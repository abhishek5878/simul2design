"""SynthesisPipeline — high-level orchestrator.

Wires ingest → automap (rules) → automap (LLM) into a single async entry point.
Returns a `SynthesisResult` with the auto-mapped matrix, automap-trace, and a
list of cells still needing human review.

Phase 3c (cascade automation: weigh-segments / synthesize / adversary /
estimate-conversion / generate-spec) is not yet shipped; spec_markdown and
report_html will be None until those skills are ported from .claude/skills/
to standalone Anthropic-API-calling Python modules.
"""

from __future__ import annotations
import asyncio
import os
from typing import Any, Optional

from simul2design import __version__
from simul2design.ingest import build_matrix, build_source_md
from simul2design.automap_rules import automap as run_automap_rules
from simul2design.automap_llm import (
    DEFAULT_MODEL as DEFAULT_LLM_MODEL,
    run_llm_fallback,
)
from simul2design.synthesize import (
    weigh_segments,
    apply_wilson_to_segments,
    run_synthesize,
    run_adversary,
    run_generate_spec,
)
from simul2design.schemas import (
    CellRef,
    ComparisonData,
    SynthesisResult,
    TokenUsage,
)


class SynthesisPipeline:
    """End-to-end synthesis pipeline.

    Sprint A scope (today): ingest → automap-rules → automap-llm.
    Sprint B scope (Phase 3c): + weigh-segments → synthesize → adversary →
    estimate-conversion → generate-spec → render-report.

    Example:
        pipeline = SynthesisPipeline()
        result = await pipeline.run(comparison_data, client_slug="univest")
        print(result.element_matrix)
        print(result.cells_needing_review)
    """

    def __init__(
        self,
        *,
        anthropic_client=None,
        automap_model: str = DEFAULT_LLM_MODEL,
        skip_llm_fallback: bool = False,
        include_low_default_in_llm_pass: bool = False,
        max_llm_cells: Optional[int] = None,
        run_weigh_segments: bool = True,
        run_wilson_baseline: bool = True,
        wilson_baseline_variant: str = "V4",
        run_full_cascade: bool = False,
        synthesize_model: str = "claude-opus-4-7",
        adversary_model: str = "claude-opus-4-7",
        spec_model: str = "claude-sonnet-4-6",
        conservatism_mode: str = "balanced",
    ):
        """
        Args:
            anthropic_client: Pre-built Anthropic SDK client. If None, one is
                constructed from ANTHROPIC_API_KEY at first LLM-pass time.
            automap_model: Model id for the LLM fallback (default: Sonnet 4.6).
            skip_llm_fallback: If True, run rules-only — no API calls. Useful
                for environments without an API key, or for cost-zero previews.
            include_low_default_in_llm_pass: If True, the LLM also re-evaluates
                cells the rules filled with sensible defaults. Costs more but
                catches edge cases.
            max_llm_cells: Cap on LLM API calls. None = no limit.
            run_weigh_segments: If True (default), run the cascade's first
                deterministic step after auto-mapping. Output lands at
                `result.weighted_scores`. No LLM calls.
            run_wilson_baseline: If True (default), compute per-segment Wilson
                95% CI on the baseline variant. Output lands at
                `result.conversion_estimates['baseline_wilson']`. No LLM calls.
            wilson_baseline_variant: Variant id used as the Wilson baseline
                (default 'V4' — the best-observed variant in Univest's case).
            run_full_cascade: If True, run synthesize → adversary → generate-spec
                after the auto-mapper + deterministic steps. Each costs an LLM
                call (~$0.05-0.15 each). Default False — for cost-sensitive runs
                or when downstream artifacts will be produced separately.
            synthesize_model: Model id for the synthesize step (default Opus 4.7).
            adversary_model: Model id for the adversary step (default Opus 4.7).
            spec_model: Model id for the generate-spec step (default Sonnet 4.6).
            conservatism_mode: 'balanced' (default), 'conservative', or
                'exploratory'. Passed to synthesize.
        """
        self._anthropic_client = anthropic_client
        self.automap_model = automap_model
        self.skip_llm_fallback = skip_llm_fallback
        self.include_low_default_in_llm_pass = include_low_default_in_llm_pass
        self.max_llm_cells = max_llm_cells
        self.run_weigh_segments = run_weigh_segments
        self.run_wilson_baseline = run_wilson_baseline
        self.wilson_baseline_variant = wilson_baseline_variant
        self.run_full_cascade = run_full_cascade
        self.synthesize_model = synthesize_model
        self.adversary_model = adversary_model
        self.spec_model = spec_model
        self.conservatism_mode = conservatism_mode

    def _ensure_client(self):
        if self._anthropic_client is not None:
            return self._anthropic_client
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError(
                "ANTHROPIC_API_KEY env var not set and no anthropic_client provided. "
                "Pass skip_llm_fallback=True to run without LLM, or supply a client."
            )
        import anthropic
        self._anthropic_client = anthropic.Anthropic()
        return self._anthropic_client

    async def run(
        self,
        comparison_data: ComparisonData | dict[str, Any],
        client_slug: str,
    ) -> SynthesisResult:
        """Run the full pipeline (Sprint A coverage). Returns a SynthesisResult.

        Args:
            comparison_data: Apriori ComparisonData. Pydantic model OR raw dict.
            client_slug: Per-client identifier (e.g. "univest"). Used in the
                output matrix and source.md.
        """
        return await asyncio.to_thread(self._run_sync, comparison_data, client_slug)

    def _run_sync(
        self,
        comparison_data: ComparisonData | dict[str, Any],
        client_slug: str,
    ) -> SynthesisResult:
        comp = (comparison_data.model_dump()
                if isinstance(comparison_data, ComparisonData)
                else dict(comparison_data))

        # Stage 1: ingest
        matrix = build_matrix(comp, client_slug)
        source_md = build_source_md(comp, client_slug)

        # Stage 2: rules-based automap
        matrix, trace = run_automap_rules(matrix, comp)

        # Stage 3: LLM fallback (optional)
        usage = TokenUsage()
        cost = 0.0
        if not self.skip_llm_fallback:
            client = self._ensure_client()
            matrix, trace, summary = run_llm_fallback(
                matrix, trace, comp,
                anthropic_client=client,
                model=self.automap_model,
                include_low_default=self.include_low_default_in_llm_pass,
                max_cells=self.max_llm_cells,
                verbose=False,
            )
            usage.input_tokens = summary["tokens_input"]
            usage.output_tokens = summary["tokens_output"]
            usage.cache_read_tokens = summary["tokens_cache_read"]
            usage.cache_write_tokens = summary["tokens_cache_write"]
            cost = summary["estimated_cost_usd"]

        # Build cells_needing_review
        cells_needing_review = []
        for vid, dims in trace.get("per_variant", {}).items():
            for dim, info in dims.items():
                if info.get("confidence") in ("needs_review", "low_default"):
                    cells_needing_review.append(CellRef(
                        variant_id=vid,
                        dimension=dim,
                        confidence=info["confidence"],
                        current_value=info.get("value"),
                    ))

        # Stage 4: cascade — deterministic steps (no LLM)
        weighted_scores = None
        conversion_estimates = None
        if self.run_weigh_segments:
            weighted_scores = weigh_segments(matrix)
        if self.run_wilson_baseline:
            try:
                wilson_per_segment = apply_wilson_to_segments(
                    matrix, baseline_variant_id=self.wilson_baseline_variant)
                conversion_estimates = {
                    "method": "wilson_95_baseline_only",
                    "wilson_z": 1.96,
                    "baseline_variant": self.wilson_baseline_variant,
                    "per_segment_baseline": wilson_per_segment,
                    "_note": ("Wilson 95% CIs on baseline variant only. "
                              "Mechanism-derived deltas + coupling discount come from "
                              "synthesize + adversary (run_full_cascade=True)."),
                }
            except ValueError:
                conversion_estimates = None

        # Stage 5: full LLM cascade (optional — synthesize + adversary + generate-spec)
        synthesized_variant = None
        adversary_review = None
        spec_markdown = None
        if self.run_full_cascade:
            client = self._ensure_client()
            ws_for_cascade = weighted_scores or weigh_segments(matrix)

            # 5a. synthesize — Opus 4.7 picks V(N+1) values + per-segment predictions
            synthesized_variant, sv_usage, sv_err = run_synthesize(
                matrix, ws_for_cascade,
                anthropic_client=client, model=self.synthesize_model,
                conservatism_mode=self.conservatism_mode,
            )
            if sv_usage:
                self._merge_usage(usage, sv_usage)
                cost += self._estimate_cost_for_call(sv_usage, self.synthesize_model)

            # 5b. adversary — Opus 4.7 challenges the V(N+1)
            if not sv_err and synthesized_variant.get("elements"):
                adversary_review, adv_usage, adv_err = run_adversary(
                    matrix, ws_for_cascade, synthesized_variant,
                    anthropic_client=client, model=self.adversary_model,
                )
                if adv_usage:
                    self._merge_usage(usage, adv_usage)
                    cost += self._estimate_cost_for_call(adv_usage, self.adversary_model)
            else:
                adversary_review = {"_skipped": "synthesize failed; adversary skipped"}

            # 5c. generate-spec — Sonnet 4.6 produces the buildable markdown
            if not sv_err and adversary_review and "_skipped" not in adversary_review:
                spec_markdown, gs_usage, gs_err = run_generate_spec(
                    matrix, ws_for_cascade, synthesized_variant, adversary_review,
                    conversion_estimates=conversion_estimates,
                    anthropic_client=client, model=self.spec_model,
                    baseline_variant_id=self.wilson_baseline_variant,
                )
                if gs_usage:
                    self._merge_usage(usage, gs_usage)
                    cost += self._estimate_cost_for_call(gs_usage, self.spec_model)

        return SynthesisResult(
            client_slug=client_slug,
            pipeline_version=__version__,
            element_matrix=matrix,
            automap_trace=trace,
            source_markdown=source_md,
            cells_needing_review=cells_needing_review,
            ready_for_synthesis=(len([c for c in cells_needing_review
                                      if c.confidence == "needs_review"]) == 0),
            estimated_cost_usd=round(cost, 4),
            token_usage=usage,
            weighted_scores=weighted_scores,
            conversion_estimates=conversion_estimates,
            synthesized_variant=synthesized_variant,
            adversary_review=adversary_review,
            spec_markdown=spec_markdown,
        )

    @staticmethod
    def _merge_usage(usage: TokenUsage, llm_usage: dict) -> None:
        usage.input_tokens += llm_usage.get("input_tokens", 0)
        usage.output_tokens += llm_usage.get("output_tokens", 0)
        usage.cache_read_tokens += llm_usage.get("cache_read_input_tokens", 0)
        usage.cache_write_tokens += llm_usage.get("cache_creation_input_tokens", 0)

    @staticmethod
    def _estimate_cost_for_call(llm_usage: dict, model: str) -> float:
        from simul2design.automap_llm import PRICING
        p = PRICING.get(model)
        if not p:
            return 0.0
        in_t = llm_usage.get("input_tokens", 0) / 1_000_000
        out_t = llm_usage.get("output_tokens", 0) / 1_000_000
        cw_t = llm_usage.get("cache_creation_input_tokens", 0) / 1_000_000
        cr_t = llm_usage.get("cache_read_input_tokens", 0) / 1_000_000
        return in_t * p["input"] + out_t * p["output"] + cw_t * p["cache_write_5m"] + cr_t * p["cache_read"]

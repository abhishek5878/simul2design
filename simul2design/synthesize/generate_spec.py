"""generate-spec — final buildable v5-spec.md document.

⚠️ NOT YET IMPLEMENTED — this is a Sprint B follow-up.

Why deferred: spec generation is the most templated of the cascade steps,
but each component (ClosedTradeCard, RefundSlaLine, etc.) needs:
- A name + field list
- A copy block (verbatim)
- A data contract (API endpoint, fallback, staleness)
- Acceptance criteria
- Associated kill-condition events from the instrumentation block

Most of this is templating from the synthesized_variant + adversary outputs,
but the per-component spec generation needs LLM (Sonnet 4.6 is enough).

# Design plan

When implemented:

    def run_generate_spec(
        synthesized_variant: dict,
        adversary_review: dict,
        conversion_estimates: dict,
        matrix: dict,
        *,
        anthropic_client,
        model: str = "claude-sonnet-4-6",
    ) -> dict:  # {"spec_markdown": str, "components": [...]}

# Implementation phases

## Phase 1 — deterministic spec skeleton (no LLM)
- Sections 0-9 from .claude/skills/generate-spec/SKILL.md template
- Pull headline numbers from conversion_estimates
- Pull diff table from synthesized_variant.elements
- Pull per-segment rows from synthesized_variant.per_segment_predictions
- Pull operational_preconditions from adversary_review.objections where
  severity == "operational_precondition"
- Pull instrumentation events from synthesized_variant + adversary kill_conditions

## Phase 2 — LLM call per component (Sonnet 4.6, prompt-cached)
- For each new component in synthesized_variant (e.g., ClosedTradeCard):
  - Prompt: "Generate the §2.X component spec for <component>. Inputs: <matrix
    citation> + <synthesize_variant element> + <adversary objections targeting
    this element>. Output: {name, fields, copy_verbatim, data_contract,
    acceptance_criteria, instrumentation_events}."
- One call per component is OK at Sonnet pricing. Cache the system prompt
  (taxonomy + spec-template instructions).

## Phase 3 — assemble + render
- Substitute LLM-generated component blocks into the deterministic skeleton
- Generate copy book (§3) from extracted verbatim strings
- Validate: every kill_condition references a real instrumentation event
- Render to markdown string

# What runs without it

Today, the spec is hand-written / hand-curated per client. data/univest/v5-spec.md
is the canonical example. When this module ships, SynthesisPipeline.run() will
populate result.spec_markdown automatically.
"""

from __future__ import annotations


def run_generate_spec(*args, **kwargs) -> dict:
    raise NotImplementedError(
        "simul2design.synthesize.generate_spec.run_generate_spec() is not yet implemented "
        "(Sprint B follow-up). Use the .claude/skills/generate-spec/ SKILL.md as a "
        "Claude Code reasoning pass, or open an issue to prioritize the port."
    )

"""synthesize — picks V(N+1) element values + per-segment predictions.

⚠️ NOT YET IMPLEMENTED — this is a Sprint B follow-up.

Why deferred: the synthesize skill is reasoning-heavy (12 element values
each picked with cited evidence + cross-dimension consistency rules from the
overlay + per-segment lift estimation with confidence intervals). Most of
the structure is deterministic (apply weighted_scores recommendation per
dim, apply consistency rules), but the tiebreaks + the per-segment lift
narratives need LLM judgment.

# Design plan

When implemented, the function signature will be:

    def run_synthesize(
        matrix: dict,
        weighted_scores: dict,
        *,
        anthropic_client,
        model: str = "claude-opus-4-7",
        conservatism_mode: str = "balanced",  # | "conservative" | "exploratory"
        audience_override: dict[str, float] | None = None,
        overlay_taxonomy_md: str | None = None,
    ) -> dict:  # synthesized_variant.json shape

# Implementation phases

## Phase 1 — deterministic prep
- Load weighted_scores.dimensions; for each dim, take .recommended.value as draft
- Apply conservatism_mode (downgrade untested→observed for conservative;
  prefer untested-with-mechanism for exploratory)
- Apply audience_override (recompute weighted scores per dim with new weights;
  if recommended flips, adopt the audience-adjusted choice)
- Apply cross-dim consistency rules from overlay (mutual_exclusion, required_pair,
  shared_banner, etc.) — these are mostly deterministic given a structured
  representation of the overlay

## Phase 2 — LLM call (Opus 4.7)
- Build prompt: matrix + weighted_scores + draft picks + per-dim alternatives
- Ask LLM to: (a) confirm or revise per-dim picks with reasoning, (b) produce
  per-segment predicted conversion ranges, (c) attach citations to every choice
- Use structured output (json_schema) to enforce the synthesized_variant schema
- Adaptive thinking enabled

## Phase 3 — emit + validate
- Validate output schema (every dim has a value + citation; every segment has
  a prediction range)
- Untested-stack count > 4 → emit warning flag
- Confidence_grade roll-up (per SKILL.md decision tree)

# Inputs needed but not yet wired

- Overlay parsing: client overlays at .claude/rules/element-taxonomy-<client>.md
  contain the contradiction + consistency rules. Need a parser that extracts
  these into a structured representation. Options:
  (a) Convention-based markdown parsing (fragile)
  (b) Have clients ship overlays as YAML alongside the .md (cleaner)
  (c) Pre-process via LLM call to convert .md → structured rules (one-time
       per client at ingest time)
  Probably (b) is the right answer — INTEGRATION.md should call this out.

# What runs without it

For now, the SynthesisPipeline returns weighted_scores.json + skips synthesize.
The .claude/skills/synthesize SKILL.md continues to drive a Claude Code reasoning
pass for hand-run synthesis. When this file is implemented, SynthesisPipeline.run()
will optionally invoke it after weigh_segments and before estimate_conversion.
"""

from __future__ import annotations


def run_synthesize(*args, **kwargs) -> dict:
    raise NotImplementedError(
        "simul2design.synthesize.synthesize.run_synthesize() is not yet implemented "
        "(Sprint B follow-up). Use the .claude/skills/synthesize/ SKILL.md as a "
        "Claude Code reasoning pass, or open an issue to prioritize the port."
    )

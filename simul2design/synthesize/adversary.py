"""adversary — falsifiable challenges to the synthesized variant.

⚠️ NOT YET IMPLEMENTED — this is a Sprint B follow-up.

Why deferred: the adversary agent is the most reasoning-heavy step. It's
intentionally adversarial — generating falsifiable predictions against
each element choice, surfacing operational/contextual failure modes the
synthesizer can't see, flagging coupled-mechanism risks. This requires
genuine Opus-class reasoning, not a templated prompt.

# Design plan

When implemented, the function signature will be:

    def run_adversary(
        matrix: dict,
        weighted_scores: dict,
        synthesized_variant: dict,
        *,
        anthropic_client,
        model: str = "claude-opus-4-7",
    ) -> dict:  # adversary_review.json shape

# Implementation phases

## Phase 1 — structural blind-review (no LLM)
- Compute hard structural objections deterministically:
  - Cells with confidence < 'medium' → flag as low-evidence
  - Untested-stack count > 4 → coupled-mechanism risk
  - Per-segment predictions outside Wilson 95% baseline CI → over-reaching
- These become "starter" objections passed to the LLM.

## Phase 2 — LLM challenge round (Opus 4.7, adaptive thinking)
- Prompt structure:
  - System: "You are an adversary. Your job is to find every reason the
    synthesized V(N+1) might fail, especially failure modes outside the
    matrix the synthesizer can't see."
  - User: matrix + weighted_scores + synthesized_variant + structural objections
  - Ask for: list of objections, each with severity (blocker | should-fix |
    operational_precondition | watch | instrument), targets[], falsifiable
    kill_condition, suggested_revision
- Use structured output for the objection schema
- Adaptive thinking enabled — adversarial reasoning benefits from it

## Phase 3 — coupling analysis (LLM, focused prompt)
- Specific call: "Which mechanisms in V(N+1) target the same segment via
  shared substrate? Compute per-segment coupling discount."
- Output feeds estimate-conversion's coupling adjustment

## Phase 4 — emit + cross-check
- adversary_review.json with summary block
- If any blocker: synthesize must re-run with revisions

# Anti-bias considerations (from .claude/agents/adversary/AGENT.md)

- The adversary should NOT have read IDEA.md / client-narrative docs.
  Structural separation: adversary's prompt context contains ONLY the
  matrix + synthesized_variant, NOT IDEA.md or weighted_scores narrative.
- Falsifiable predictions only — no "this might fail" without a specific
  observable that would prove it.
- Out-of-matrix reach is required: every objection should ideally name an
  operational/legal/UX failure mode invisible to the synthesizer.
"""

from __future__ import annotations


def run_adversary(*args, **kwargs) -> dict:
    raise NotImplementedError(
        "simul2design.synthesize.adversary.run_adversary() is not yet implemented "
        "(Sprint B follow-up). Use the .claude/agents/adversary/ AGENT.md as a "
        "Claude Code subagent, or open an issue to prioritize the port."
    )

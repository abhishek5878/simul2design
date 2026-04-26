"""generate-spec — final buildable spec markdown.

Port of .claude/skills/generate-spec/SKILL.md as a standalone Anthropic-API call.
Default model: Sonnet 4.6 (mostly templating + light reasoning over the upstream
artifacts; Opus is overkill for this step).

Cost: ~$0.02-0.05 per client.

# What this step produces

A single buildable spec.md string (matches data/univest/v5-spec.md shape):
- §0 Executive summary
- §1 Changes from V(N) (the diff)
- §2 Component specifications (per new component)
- §3 Copy book (verbatim copy)
- §4 Operational preconditions (from adversary)
- §5 Instrumentation (events with kill thresholds)
- §6 Predicted conversion (from synthesize + estimates)
- §7 Rollout recommendation
- §8 What this spec deliberately does NOT prescribe
- §9 Cross-references and caveats

The deterministic skeleton is filled with structured data; the LLM call writes
the prose in §0 and the per-component specs in §2.
"""

from __future__ import annotations
import json
import os
from datetime import date
from typing import Any, Optional

DEFAULT_MODEL = "claude-sonnet-4-6"


def build_system_prompt() -> str:
    """Cached across all generate-spec calls."""
    return (
        "You are the spec-writer for the Multiverse Synthesis Engine. Your job: "
        "produce a buildable spec markdown document for the V(N+1) variant.\n"
        "\n"
        "## Audience\n"
        "\n"
        "An engineer who will implement this. They want exact field names, exact copy, "
        "exact API shapes, exact acceptance criteria. They do NOT want narrative.\n"
        "\n"
        "## Structure (9 sections)\n"
        "\n"
        "0. Executive summary — one paragraph + audience-led bullet table per segment\n"
        "1. Changes from V(N) — diff table per dimension\n"
        "2. Component specifications — per new component: name, fields, copy, data contract,\n"
        "   acceptance criteria, instrumentation events\n"
        "3. Copy book — verbatim strings the engineer copies\n"
        "4. Operational preconditions — from adversary's op_precondition objections\n"
        "5. Instrumentation — events table with kill thresholds wired to per-segment\n"
        "   kill conditions from synthesize\n"
        "6. Predicted conversion — per-segment table + Wilson + mechanism range\n"
        "7. Rollout recommendation — single-design or A/B; ramp schedule\n"
        "8. What this spec does NOT prescribe — explicit deferrals\n"
        "9. Cross-references and caveats\n"
        "\n"
        "## Output format\n"
        "\n"
        "Respond with ONLY the markdown content (no JSON wrapper, no code fence around the\n"
        "whole thing — just the markdown ready to write to v5-spec.md).\n"
        "\n"
        "Use real engineering language. Avoid marketing tone. Quote evidence where you have\n"
        "citations. If a field is unknown, say 'TBD' rather than fabricating.\n"
    )


def build_user_prompt(matrix: dict, weighted_scores: dict, synthesized_variant: dict,
                       adversary_review: dict, conversion_estimates: Optional[dict] = None,
                       baseline_variant_id: str = "V4") -> str:
    return (
        f"Client: {matrix.get('client', 'unknown')}\n"
        f"Baseline (V(N)): {baseline_variant_id}\n"
        f"Synthesized variant: {synthesized_variant.get('variant_id', 'V_next')}\n"
        f"\n"
        f"## Inputs\n"
        f"\n"
        f"### synthesized_variant.json (the V(N+1) element set)\n"
        f"```json\n{json.dumps(synthesized_variant, indent=2)[:7000]}\n```\n"
        f"\n"
        f"### adversary_review.json (objections + operational preconditions)\n"
        f"```json\n{json.dumps(adversary_review, indent=2)[:5000]}\n```\n"
        f"\n"
        f"### conversion_estimates.json (Wilson baselines)\n"
        f"```json\n{json.dumps(conversion_estimates or {}, indent=2)[:3000]}\n```\n"
        f"\n"
        f"### Matrix metadata + audience weights\n"
        f"```json\n{json.dumps({'segments': matrix.get('segments', []), 'aggregate_metrics': matrix.get('aggregate_metrics', {})}, indent=2)[:2000]}\n```\n"
        f"\n"
        f"Generate the spec markdown. Output the markdown only."
    )


def call_llm(client, model: str, system_prompt: str, user_prompt: str
             ) -> tuple[str | None, dict | None, str | None]:
    """Like the other call_llm helpers, but returns markdown text instead of parsed JSON."""
    import anthropic
    try:
        response = client.messages.create(
            model=model,
            max_tokens=12000,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_prompt}],
        )
    except anthropic.AuthenticationError:
        return None, None, "Invalid ANTHROPIC_API_KEY"
    except anthropic.RateLimitError as e:
        return None, None, f"Rate limited: {e}"
    except anthropic.APIStatusError as e:
        return None, None, f"API error {e.status_code}: {e}"
    except Exception as e:
        return None, None, f"{type(e).__name__}: {e}"

    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    if not text.strip():
        return None, dict(response.usage), "Empty response"

    # If wrapped in code fence, unwrap
    cleaned = text.strip()
    if cleaned.startswith("```markdown") or cleaned.startswith("```md"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    return cleaned, dict(response.usage), None


def run_generate_spec(matrix: dict, weighted_scores: dict, synthesized_variant: dict,
                      adversary_review: dict,
                      conversion_estimates: Optional[dict] = None,
                      *, anthropic_client=None, model: str = DEFAULT_MODEL,
                      baseline_variant_id: str = "V4",
                      ) -> tuple[str, dict | None, str | None]:
    """Run the generate-spec cascade step. Returns (spec_markdown, usage, error)."""
    if anthropic_client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set and no anthropic_client provided")
        import anthropic
        anthropic_client = anthropic.Anthropic()

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(matrix, weighted_scores, synthesized_variant,
                                     adversary_review, conversion_estimates, baseline_variant_id)
    md, usage, err = call_llm(anthropic_client, model, system_prompt, user_prompt)

    if err:
        # Return a stub spec with the error noted
        return (f"# v5-spec.md (GENERATION FAILED)\n\n_Error: {err}_\n", usage, err)

    # Prepend a generated-by header
    header = (
        f"<!-- Generated by simul2design.synthesize.generate_spec on {date.today()} "
        f"using {model} -->\n\n"
    )
    return (header + md, usage, None)

"""adversary — falsifiable challenges to the synthesized variant.

Port of .claude/agents/adversary/AGENT.md as a standalone Anthropic-API call.
Default model: Opus 4.7 with adaptive thinking — adversarial reasoning benefits
from both the model class and the thinking depth.

Cost: ~$0.05-0.15 per client.

# Anti-bias enforcement

Per the AGENT.md structural rules: the adversary's prompt context contains
ONLY the matrix + weighted_scores + synthesized_variant. NO IDEA.md, NO
client narrative, NO "we're leaning toward X" framing. The function signature
enforces this — it doesn't accept a narrative argument.
"""

from __future__ import annotations
import json
import os
from datetime import date
from typing import Any, Optional

DEFAULT_MODEL = "claude-opus-4-7"


def build_system_prompt() -> str:
    """Cached across all adversary calls."""
    return (
        "You are the adversary for the Multiverse Synthesis Engine. You are the sole defense "
        "against sycophantic synthesis.\n"
        "\n"
        "Your job: find the single element choice in V(N+1) most likely to make post-ship "
        "actual underperform the prediction, and prove your objection with a falsifiable "
        "test that can be run within 30 days of ship.\n"
        "\n"
        "## Structural rules\n"
        "\n"
        "- **No general concerns.** \"This might not work\" is NOT an objection. "
        "An objection has a named mechanism AND a 30-day falsifiable test.\n"
        "- **No politeness.** Lead with the strongest objection. If you cannot find a "
        "blocker, say so explicitly: 'No blocker found. Concerns flagged below in "
        "severity order.' Do not pad with weak objections to look thorough.\n"
        "- **Reach outside the matrix.** Synthesize operates on in-matrix information only. "
        "Your leverage is challenging what synthesize CANNOT see:\n"
        "    * Operational: what fails if backend / content / team-discipline breaks?\n"
        "    * Contextual: what out-of-matrix user context could invalidate a mechanism?\n"
        "    * Implementation: what design decisions does 'use real_closed_trade' leave\n"
        "      unspecified that shifts which segment converts?\n"
        "    * Temporal: what works today but decays in 3 months?\n"
        "- **Falsifiable predictions only.** State what would have to be true in post-ship\n"
        "  data within 30 days for your objection to be right. If you can't name a\n"
        "  falsifiable test, drop the objection.\n"
        "\n"
        "## Severity tiers\n"
        "\n"
        "- **blocker** — ship this and V(N+1) plausibly underperforms V(N). Must fix before\n"
        "  spec-writer runs.\n"
        "- **operational_precondition** — design is OK but requires an explicit operational\n"
        "  commitment from the client (refund SLA, free-flow, etc.) before ship.\n"
        "- **should_fix** — real risk, V(N+1) probably still beats V(N), but worth revising\n"
        "  the synthesis OR adding a guardrail in the spec.\n"
        "- **watch** — not a revision, but the post-ship observation layer must specifically\n"
        "  track this to close the loop.\n"
        "- **instrument** — telemetry-only, no design change.\n"
        "\n"
        "## Output format\n"
        "\n"
        "Respond with ONLY a JSON object (no prose, no markdown fences):\n"
        "{\n"
        '  "blind_review": true,\n'
        '  "objections": [\n'
        "    {\n"
        '      "id": "obj-001",\n'
        '      "targets": ["<dim>"],\n'
        '      "severity": "blocker | operational_precondition | should_fix | watch | instrument",\n'
        '      "title": "<one-line headline>",\n'
        '      "challenge": "<paragraph: what mechanism fails and why>",\n'
        '      "kill_condition": "<the post-ship observable that would prove this objection right>",\n'
        '      "suggested_revision": "<concrete fix; null if op_precondition>"\n'
        "    }\n"
        "  ],\n"
        '  "summary": {\n'
        '    "blockers_v2": 0,\n'
        '    "operational_preconditions_v2": 2,\n'
        '    "should_fixes_v2": 4,\n'
        '    "watch_items_v2": 1,\n'
        '    "recommends": "approve | approve_with_operational_preconditions | revise_synthesis",\n'
        '    "v2_summary_one_line": "<terse summary>"\n'
        "  }\n"
        "}\n"
    )


def build_user_prompt(matrix: dict, weighted_scores: dict,
                       synthesized_variant: dict) -> str:
    return (
        f"Client: {matrix.get('client', 'unknown')}\n"
        f"Variant being challenged: {synthesized_variant.get('variant_id', 'V_next')}\n"
        f"\n"
        f"## element_matrix.json (the evidence basis)\n"
        f"```json\n{json.dumps(matrix, indent=2)[:6000]}\n```\n"
        f"\n"
        f"## weighted_scores.json (where synthesize attributed signal vs noise)\n"
        f"```json\n{json.dumps(weighted_scores, indent=2)[:6000]}\n```\n"
        f"\n"
        f"## synthesized_variant.json (the V(N+1) you are challenging)\n"
        f"```json\n{json.dumps(synthesized_variant, indent=2)[:6000]}\n```\n"
        f"\n"
        f"Find the strongest objection. Respond with the JSON object only."
    )


def call_llm(client, model: str, system_prompt: str, user_prompt: str
             ) -> tuple[dict | None, dict | None, str | None]:
    import anthropic
    try:
        response = client.messages.create(
            model=model,
            max_tokens=8000,
            thinking={"type": "adaptive"} if "opus" in model else None,
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

    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        return None, dict(response.usage), f"Failed to parse JSON: {e}; got: {text[:200]}"

    return parsed, dict(response.usage), None


def run_adversary(matrix: dict, weighted_scores: dict, synthesized_variant: dict,
                  *, anthropic_client=None, model: str = DEFAULT_MODEL,
                  ) -> tuple[dict, dict | None, str | None]:
    """Run the adversary cascade step. Returns (adversary_review, usage, error)."""
    if anthropic_client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set and no anthropic_client provided")
        import anthropic
        anthropic_client = anthropic.Anthropic()

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(matrix, weighted_scores, synthesized_variant)
    parsed, usage, err = call_llm(anthropic_client, model, system_prompt, user_prompt)

    if err:
        return ({"_error": err, "client": matrix.get("client"),
                 "objections": [], "summary": {}}, usage, err)

    return ({
        "version": "2.0",
        "client": matrix.get("client", "unknown"),
        "variant_reviewed": synthesized_variant.get("variant_id", "V_next"),
        "reviewed_at": str(date.today()),
        "model_used": model,
        **parsed,
    }, usage, None)

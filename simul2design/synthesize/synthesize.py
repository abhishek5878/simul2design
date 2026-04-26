"""synthesize — picks V(N+1) element values + per-segment predictions.

Port of .claude/skills/synthesize/SKILL.md as a standalone Anthropic-API call.

For each taxonomy dimension, picks the value the engine recommends for the
next variant (V(N+1)). Attaches a citation per choice. Estimates per-segment
conversion (point + range). Computes a confidence_grade.

Default model: Opus 4.7 with adaptive thinking. Sonnet 4.6 also supported
for cost-sensitive runs (lower quality on tiebreaks but cheaper).

Cost: ~$0.05-0.15 per client (~5-10K tokens in/out, with prompt caching
on the system message).

# Inputs deliberately EXCLUDED from the prompt

Per .claude/skills/synthesize and the project's adversarial framing rules:
the synthesize prompt does NOT include IDEA.md or any "the client wants X"
narrative. The synthesis is right or wrong on its evidence basis, not
stakeholder preference.
"""

from __future__ import annotations
import json
import os
from datetime import date
from typing import Any, Optional

DEFAULT_MODEL = "claude-opus-4-7"


def build_system_prompt() -> str:
    """Cached across all synthesize calls. Keep stable to maximize cache hits."""
    return (
        "You are the synthesizer for the Multiverse Synthesis Engine. Your job: pick "
        "the optimal V(N+1) element set from the per-dimension weighted scores produced "
        "by the engine's deterministic weigh-segments step.\n"
        "\n"
        "## Rules\n"
        "\n"
        "- For each dimension, choose ONE value. Default to weighted_scores.dimensions[<dim>].recommended.value.\n"
        "- Override the default only when: (a) cross-dimension consistency forces it, (b) audience-override\n"
        "  flips the score, or (c) the recommendation is null and you must pick a sensible default.\n"
        "- Every choice gets a citation block referencing the evidence (clean_contrast, friction_direct,\n"
        "  variant_only, or untested with overlay_mechanism).\n"
        "- For untested values, set untested=true and include the expected_mechanism.\n"
        "- Per-segment predictions: estimate V(N+1) conversion per segment using:\n"
        "    baseline = best-observed segment conversion across tested variants\n"
        "    + clean_contrast deltas from chosen values (segment-weighted)\n"
        "    + friction-resolution lifts (qualitative, widen interval)\n"
        "    + untested mechanism lifts (biased interval, must include 0)\n"
        "  Express as {predicted_point, predicted_range: [low, high]} per segment.\n"
        "- Roll up to weighted_overall using audience_weights.\n"
        "- confidence_grade rule:\n"
        "    high   = ≥6 dims have high-evidence values AND ≤2 untested\n"
        "    medium = 3-5 dims high-evidence, ≤4 untested\n"
        "    low    = <3 high-evidence OR >4 untested\n"
        "\n"
        "## Anti-bias\n"
        "\n"
        "- Do NOT pick a value because the user or input narrative implies it. Pick on evidence.\n"
        "- If a dimension's recommended.value is null (non-informative), pick the most-adopted\n"
        "  value across post-Control variants. Use citation type 'default_by_adoption_rate'\n"
        "  with confidence='low'. Don't reach for untested values to fill informational gaps.\n"
        "\n"
        "## Output format\n"
        "\n"
        "Respond with ONLY a JSON object (no prose, no markdown fences) matching this schema:\n"
        "{\n"
        '  "elements": {\n'
        '    "<dim>": {\n'
        '      "value": "<chosen value>",\n'
        '      "citation": {"type": "<type>", "ref": "<ref>", "verbatim_quote": "<quote>"},\n'
        '      "confidence": "high|medium|low",\n'
        '      "untested": false,\n'
        '      "expected_mechanism": null,\n'
        '      "rationale_one_line": "<one sentence>"\n'
        "    }\n"
        "  },\n"
        '  "per_segment_predicted": {\n'
        '    "<segment_id>": {\n'
        '      "baseline_variant": "V4",\n'
        '      "baseline_conversion": 0.25,\n'
        '      "predicted_point": 0.35,\n'
        '      "predicted_range": [0.30, 0.40],\n'
        '      "drivers": [{"lever": "<dim>", "expected_pts": 5, "evidence": "<short>"}],\n'
        '      "kill_condition": "<observable that would invalidate this prediction>"\n'
        "    },\n"
        '    "weighted_overall": {\n'
        '      "predicted_point": 0.51,\n'
        '      "predicted_range": [0.45, 0.56],\n'
        '      "computation": "<one-line arithmetic>"\n'
        "    }\n"
        "  },\n"
        '  "untested_stack_count": 1,\n'
        '  "confidence_grade_overall": "medium-high",\n'
        '  "confidence_rationale": "<one line>"\n'
        "}\n"
    )


def build_user_prompt(matrix: dict, weighted_scores: dict,
                       conservatism_mode: str = "balanced",
                       audience_override: Optional[dict[str, float]] = None) -> str:
    audience = audience_override or {seg["id"]: seg["weight"] for seg in matrix.get("segments", [])}
    return (
        f"Client: {matrix.get('client', 'unknown')}\n"
        f"Conservatism mode: {conservatism_mode}\n"
        f"Audience weights to use: {json.dumps(audience)}\n"
        f"\n"
        f"## element_matrix.json\n"
        f"```json\n{json.dumps(matrix, indent=2)[:8000]}\n```\n"
        f"\n"
        f"## weighted_scores.json (deterministic Phase 1 output)\n"
        f"```json\n{json.dumps(weighted_scores, indent=2)[:8000]}\n```\n"
        f"\n"
        f"Pick V(N+1). Respond with the JSON object only."
    )


def call_llm(client, model: str, system_prompt: str, user_prompt: str
             ) -> tuple[dict | None, dict | None, str | None]:
    """Make one Messages API call. Returns (parsed_json, usage, error)."""
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


def run_synthesize(matrix: dict, weighted_scores: dict,
                   *, anthropic_client=None, model: str = DEFAULT_MODEL,
                   conservatism_mode: str = "balanced",
                   audience_override: Optional[dict[str, float]] = None,
                   ) -> tuple[dict, dict | None, str | None]:
    """Run the synthesize cascade step. Returns (synthesized_variant, usage, error).

    On error, synthesized_variant is a minimal dict with `_error` field set.
    """
    if anthropic_client is None:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY not set and no anthropic_client provided")
        import anthropic
        anthropic_client = anthropic.Anthropic()

    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(matrix, weighted_scores, conservatism_mode, audience_override)
    parsed, usage, err = call_llm(anthropic_client, model, system_prompt, user_prompt)

    if err:
        return ({"_error": err, "client": matrix.get("client"),
                 "elements": {}, "per_segment_predicted": {}}, usage, err)

    # Wrap LLM output in standard envelope
    audience = audience_override or {seg["id"]: seg["weight"] for seg in matrix.get("segments", [])}
    return ({
        "version": "2.0",
        "client": matrix.get("client", "unknown"),
        "variant_id": "V_next",
        "generated_at": str(date.today()),
        "model_used": model,
        "conservatism_mode": conservatism_mode,
        "audience_weights_used": audience,
        "audience_source": "user_override" if audience_override else "matrix_default",
        **parsed,
    }, usage, None)

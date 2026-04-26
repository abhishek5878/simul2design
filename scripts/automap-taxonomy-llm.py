#!/usr/bin/env python3
"""
automap-taxonomy-llm.py — LLM fallback for taxonomy cells the rule-based mapper missed.

Phase 3b of the plug-in roadmap (see INTEGRATION.md §5). Reads the matrix +
automap-trace produced by Phase 3a (`automap-taxonomy.py`); for every cell
flagged `low_default` or `needs_review`, calls Claude Sonnet 4.6 to propose a
value with reasoning. High/medium-confidence LLM picks update the matrix and
get tagged `auto_mapped_llm` in the trace; low-confidence picks (or null) are
left untouched for the human review pass.

Cost & caching: the full taxonomy enum is sent as a cached system message
(prompt caching, 5-minute TTL). For a typical client (~14 cells) the run
costs roughly $0.05 on Sonnet 4.6.

Requires:
- `anthropic` Python SDK installed (see requirements.txt)
- ANTHROPIC_API_KEY environment variable
- Phase 3a outputs at data/<client>/{element_matrix,automap-trace}.json

Usage:
    scripts/automap-taxonomy-llm.py <client>
    scripts/automap-taxonomy-llm.py <client> --dry-run            # preview prompts; no API calls
    scripts/automap-taxonomy-llm.py <client> --include-low-default # also re-map cells already filled by Phase 3a defaults
    scripts/automap-taxonomy-llm.py <client> --max-cells 5         # cost cap: stop after N API calls
    scripts/automap-taxonomy-llm.py <client> --model claude-opus-4-7  # use a different model
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEEDS_REVIEW = "__needs_review__"
DEFAULT_MODEL = "claude-sonnet-4-6"
TAXONOMY_BASE_FILE = ROOT / ".claude" / "rules" / "element-taxonomy-base.md"

# Sonnet 4.6 pricing per million tokens (cached at module load — see live-sources for updates)
PRICING = {
    "claude-sonnet-4-6": {"input": 3.00, "output": 15.00, "cache_write_5m": 3.75, "cache_read": 0.30},
    "claude-opus-4-7":   {"input": 5.00, "output": 25.00, "cache_write_5m": 6.25, "cache_read": 0.50},
    "claude-opus-4-6":   {"input": 5.00, "output": 25.00, "cache_write_5m": 6.25, "cache_read": 0.50},
    "claude-haiku-4-5":  {"input": 1.00, "output":  5.00, "cache_write_5m": 1.25, "cache_read": 0.10},
}

# The 11 enum dimensions from element-taxonomy-base.md plus the freeform cta_primary_label.
# Allowed-values map is built by parsing the taxonomy file at runtime.
ENUM_DIMENSIONS = [
    "layout", "modal_interrupt", "branding", "price_visibility",
    "cta_style", "cta_stack", "urgency_mechanism",
    "refund_or_guarantee_copy", "trust_signal", "evidence_detail",
]
FREEFORM_DIMENSIONS = ["cta_primary_label"]


# ─── taxonomy loading ───────────────────────────────────────────────────────

def load_taxonomy_text() -> str:
    """Read the full base taxonomy markdown for use in the system prompt."""
    if not TAXONOMY_BASE_FILE.is_file():
        print(f"Error: {TAXONOMY_BASE_FILE} not found", file=sys.stderr)
        sys.exit(1)
    return TAXONOMY_BASE_FILE.read_text()


def parse_allowed_values(taxonomy_md: str) -> dict[str, list[str]]:
    """Extract per-dimension allowed values from the base taxonomy markdown.

    Looks for lines like '- `value_name` — description' under each '### N. `dim`' heading.
    """
    import re
    allowed: dict[str, list[str]] = {}
    current_dim = None
    for line in taxonomy_md.splitlines():
        m = re.match(r"^###\s+\d+\.\s*`(\w+)`", line)
        if m:
            current_dim = m.group(1)
            allowed.setdefault(current_dim, [])
            continue
        if current_dim:
            m = re.match(r"^-\s+`([\w_]+)`", line)
            if m:
                allowed[current_dim].append(m.group(1))
    return allowed


# ─── prompt building ────────────────────────────────────────────────────────

def build_system_prompt(taxonomy_md: str) -> str:
    return (
        "You are a taxonomy classifier for the Multiverse Synthesis Engine. "
        "Your job: given natural-language descriptions of an A/B test variant's "
        "activation screen, map it to the correct enum value for a single "
        "taxonomy dimension.\n"
        "\n"
        "Below is the full base taxonomy you must classify against. Read it carefully.\n"
        "\n"
        "============================================================\n"
        f"{taxonomy_md}\n"
        "============================================================\n"
        "\n"
        "OUTPUT FORMAT — respond with ONLY a JSON object (no prose, no markdown fences):\n"
        "{\n"
        '  "value": "<exact enum value from the dimension\'s allowed set, OR null if undeterminable>",\n'
        '  "reasoning": "<one sentence quoting the evidence in the variant text that drove your choice>",\n'
        '  "confidence": "high" | "medium" | "low"\n'
        "}\n"
        "\n"
        "Rules:\n"
        "- Use ONLY values from the dimension's allowed set above. If the variant suggests a value "
        "not in the set, pick the closest match and note the approximation in reasoning.\n"
        "- For cta_primary_label (freeform): return the exact button-label string from the variant text, "
        "preserving capitalization. Reject brand strings ('India's Trusted Advisory'), banner copy, "
        "and section headers — only return the actual CTA button label.\n"
        "- 'high' confidence = the variant text explicitly states or strongly implies this value.\n"
        "- 'medium' = derivable from context but with some judgment.\n"
        "- 'low' = guess based on weak signal; the human review pass should override.\n"
        "- Return value=null if the variant text genuinely doesn't speak to this dimension.\n"
        "- The Phase 3a rule-based mapper's prior verdict is provided as context — feel free to "
        "agree with it, override it, or disagree (be explicit about why in reasoning)."
    )


def build_user_prompt(variant_id: str, dimension: str, allowed_values: list[str],
                      variant_context: str, prior_verdict: dict) -> str:
    allowed_str = ", ".join(allowed_values) if allowed_values else "(freeform string)"
    prior = (f"value={prior_verdict.get('value')!r}, "
             f"confidence={prior_verdict.get('confidence')!r}, "
             f"matched_pattern={prior_verdict.get('matched_pattern')!r}")
    return (
        f"Variant: {variant_id}\n"
        f"Dimension: {dimension}\n"
        f"Allowed values: {allowed_str}\n"
        "\n"
        f"Phase 3a rule-based verdict: {prior}\n"
        "\n"
        "Variant text corpus (variant description + Apriori screen-comparison summaries):\n"
        "----- BEGIN -----\n"
        f"{variant_context}\n"
        "----- END -----\n"
        "\n"
        f"What is the best value for `{dimension}`? Respond with the JSON object only."
    )


def collect_variant_text(matrix: dict, apriori: dict, our_variant_id: str) -> str:
    """Same logic as automap-taxonomy.py.collect_text but inlined to avoid cross-import."""
    apriori_id = next((v["apriori_id"] for v in matrix["variants"]
                       if v["id"] == our_variant_id), None)
    if not apriori_id:
        return ""
    parts = []
    for v in apriori.get("variants", []):
        if v["id"] == apriori_id:
            parts.append(f"VARIANT_DESCRIPTION: {v.get('description', '')}")
    for sc in apriori.get("screen_comparison", []):
        s = sc.get("summaries", {}).get(apriori_id, "")
        if s:
            parts.append(f"SCREEN '{sc.get('screen_name', '?')}': {s}")
    for fp in apriori.get("friction_provenance", []):
        if fp.get("presence", {}).get(apriori_id) == "present":
            parts.append(f"FRICTION_PRESENT: {fp.get('friction', '')}")
    for bucket in ("persistent", "introduced"):
        for theme in apriori.get("theme_movement", {}).get(bucket, []):
            if apriori_id in theme.get("present_in", []):
                parts.append(f"THEME ({bucket}): {theme.get('name', '')} — {theme.get('description', '')[:200]}")
    return "\n".join(parts)


# ─── LLM call ───────────────────────────────────────────────────────────────

def call_llm(client, model: str, system_prompt: str, user_prompt: str
             ) -> tuple[dict | None, dict | None, str | None]:
    """Make one Anthropic Messages API call. Returns (parsed_json, usage_dict, error_msg)."""
    import anthropic
    try:
        response = client.messages.create(
            model=model,
            max_tokens=512,
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
    except Exception as e:  # network errors etc.
        return None, None, f"{type(e).__name__}: {e}"

    text = "".join(b.text for b in response.content if getattr(b, "type", None) == "text")
    if not text.strip():
        return None, dict(response.usage), "Empty response"

    # Strip markdown code fences if the model added them despite instructions
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


def estimate_cost(usage: dict, model: str) -> float:
    """Cost in USD for one API call."""
    p = PRICING.get(model)
    if not p:
        return 0.0
    in_t = usage.get("input_tokens", 0) / 1_000_000
    out_t = usage.get("output_tokens", 0) / 1_000_000
    cw_t = usage.get("cache_creation_input_tokens", 0) / 1_000_000
    cr_t = usage.get("cache_read_input_tokens", 0) / 1_000_000
    return in_t * p["input"] + out_t * p["output"] + cw_t * p["cache_write_5m"] + cr_t * p["cache_read"]


# ─── main ───────────────────────────────────────────────────────────────────

def select_cells_to_map(trace: dict, include_low_default: bool) -> list[tuple[str, str, dict]]:
    """Return [(variant_id, dimension, prior_verdict), ...] for cells the LLM should attempt."""
    target_confidences = {"needs_review"}
    if include_low_default:
        target_confidences.add("low_default")
    cells = []
    for vid, dims in trace.get("per_variant", {}).items():
        for dim, info in dims.items():
            if info.get("confidence") in target_confidences:
                cells.append((vid, dim, info))
    return cells


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 3b LLM fallback for taxonomy cells.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("client", help="Client slug")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="Model id (default: %(default)s)")
    ap.add_argument("--include-low-default", action="store_true",
                    help="Also re-evaluate cells Phase 3a filled with low-confidence defaults")
    ap.add_argument("--max-cells", type=int, default=None,
                    help="Cost cap: stop after N API calls (default: no limit)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print prompts without calling the API; no auth required")
    ap.add_argument("-o", "--output-dir", default=None,
                    help="Output dir override (default: data/<client>/)")
    args = ap.parse_args()

    data_dir = Path(args.output_dir) if args.output_dir else (ROOT / "data" / args.client)
    matrix_path = data_dir / "element_matrix.json"
    trace_path = data_dir / "automap-trace.json"
    apriori_path = data_dir / "apriori_input.json"

    for p in (matrix_path, trace_path, apriori_path):
        if not p.is_file():
            print(f"Error: {p} not found. Run ingest-apriori.py + automap-taxonomy.py first.",
                  file=sys.stderr)
            return 1

    matrix = json.loads(matrix_path.read_text())
    trace = json.loads(trace_path.read_text())
    apriori = json.loads(apriori_path.read_text())

    cells = select_cells_to_map(trace, args.include_low_default)
    if args.max_cells is not None:
        cells = cells[: args.max_cells]

    if not cells:
        print("No cells to map. (Try --include-low-default to re-evaluate Phase 3a defaults.)")
        return 0

    print(f"LLM-mapping {len(cells)} cell(s) using {args.model}...")
    print(f"  --include-low-default: {args.include_low_default}")
    print(f"  --dry-run: {args.dry_run}")
    print()

    taxonomy_md = load_taxonomy_text()
    allowed = parse_allowed_values(taxonomy_md)
    system_prompt = build_system_prompt(taxonomy_md)

    if not args.dry_run:
        if not os.environ.get("ANTHROPIC_API_KEY"):
            print("Error: ANTHROPIC_API_KEY env var not set. (Use --dry-run to preview without auth.)",
                  file=sys.stderr)
            return 2
        try:
            import anthropic
        except ImportError:
            print("Error: 'anthropic' SDK not installed. Run: pip install -r requirements.txt",
                  file=sys.stderr)
            return 2
        client = anthropic.Anthropic()
    else:
        client = None

    auto_by_id = {v["id"]: v for v in matrix["variants"]}
    total_cost = 0.0
    total_input = total_output = total_cache_w = total_cache_r = 0
    successes = failures = nulls = 0
    for i, (vid, dim, prior) in enumerate(cells, 1):
        variant_text = collect_variant_text(matrix, apriori, vid)
        allowed_vals = allowed.get(dim, []) if dim in ENUM_DIMENSIONS else []
        user_prompt = build_user_prompt(vid, dim, allowed_vals, variant_text, prior)

        print(f"[{i}/{len(cells)}] {vid}.{dim}  (was: {prior.get('value')!r})")

        if args.dry_run:
            print(f"  (would call LLM with prompt of {len(user_prompt)} chars)")
            continue

        parsed, usage, err = call_llm(client, args.model, system_prompt, user_prompt)
        if err:
            print(f"  ✗ {err}")
            failures += 1
            time.sleep(0.2)
            continue

        if usage:
            total_input += usage.get("input_tokens", 0)
            total_output += usage.get("output_tokens", 0)
            total_cache_w += usage.get("cache_creation_input_tokens", 0)
            total_cache_r += usage.get("cache_read_input_tokens", 0)
            total_cost += estimate_cost(usage, args.model)

        value = parsed.get("value") if parsed else None
        confidence = (parsed or {}).get("confidence", "low")
        reasoning = (parsed or {}).get("reasoning", "")

        # Update only when LLM has high or medium confidence
        if value is not None and confidence in ("high", "medium"):
            auto_by_id[vid]["elements"][dim] = value
            trace["per_variant"][vid][dim] = {
                "value": value,
                "confidence": "auto_mapped_llm",
                "matched_pattern": None,
                "llm_confidence": confidence,
                "llm_reasoning": reasoning,
                "llm_model": args.model,
            }
            print(f"  ✓ {value!r}  ({confidence}) — {reasoning[:120]}")
            successes += 1
        else:
            print(f"  · LLM did not improve on Phase 3a (value={value!r}, conf={confidence})")
            nulls += 1

    # Update trace summary
    trace.setdefault("_llm_pass", {})
    trace["_llm_pass"].update({
        "run_at": str(date.today()),
        "model": args.model,
        "cells_attempted": len(cells),
        "successes_high_or_medium": successes,
        "failures_or_null": failures + nulls,
        "tokens_input": total_input,
        "tokens_output": total_output,
        "tokens_cache_write": total_cache_w,
        "tokens_cache_read": total_cache_r,
        "estimated_cost_usd": round(total_cost, 4),
    })
    if not args.dry_run:
        matrix.setdefault("extraction_confidence", {})
        matrix["extraction_confidence"]["_llm_pass"] = trace["_llm_pass"]
        matrix_path.write_text(json.dumps(matrix, indent=2))
        trace_path.write_text(json.dumps(trace, indent=2))

    print()
    print(f"Summary: {successes}/{len(cells)} cells improved by LLM "
          f"({failures + nulls} unchanged or failed)")
    if not args.dry_run:
        print(f"Tokens: input={total_input}, output={total_output}, "
              f"cache_write={total_cache_w}, cache_read={total_cache_r}")
        print(f"Estimated cost: ${total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

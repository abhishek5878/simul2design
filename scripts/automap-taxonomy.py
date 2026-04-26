#!/usr/bin/env python3
"""
automap-taxonomy.py — rule-based taxonomy auto-mapper for the synthesis engine.

Phase 3a of the plug-in roadmap (see INTEGRATION.md §5). Reads a client's
starter element_matrix.json (with __needs_review__ taxonomy values) plus the
apriori_input.json (Apriori's natural-language ComparisonData), and applies
keyword/regex pattern rules to fill in as many taxonomy cells as possible.

What gets auto-mapped:
- 11 enum dimensions: layout, modal_interrupt, branding, price_visibility,
  cta_style, cta_stack, urgency_mechanism, refund_or_guarantee_copy,
  trust_signal, evidence_detail (per .claude/rules/element-taxonomy-base.md)
- 1 freeform: cta_primary_label (verbatim quote extraction)

Per-cell confidence:
- 'high'  — explicit pattern match in the variant's text corpus
- 'low_default' — no pattern matched, fell back to a sensible default (e.g.
                 cta_stack=single, urgency=none, refund=absent, branding=none)
- 'needs_review' — no pattern, no defensible default; sentinel preserved

Phase 3b (LLM fallback for cells where rules return needs_review or low_default)
is deferred — see tasks/improvements.md.

Usage:
    scripts/automap-taxonomy.py <client>            # update data/<client>/element_matrix.json in place
    scripts/automap-taxonomy.py <client> --dry-run  # report what would change, write nothing
    scripts/automap-taxonomy.py <client> -o <dir>   # output to alternate dir (e.g. /tmp/test/)
"""

from __future__ import annotations
import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

NEEDS_REVIEW = "__needs_review__"

# ─── pattern rules ──────────────────────────────────────────────────────────
# Each dimension maps to a list of (value, regex_patterns) tuples checked in
# order. First-matching wins. Entries with patterns=[] are defaults applied
# when nothing matches (low_default confidence).
#
# Patterns are case-insensitive, applied to the concatenated lowercased text
# corpus for the variant (description + screen summaries + friction-presence).

RULES: dict[str, list[tuple[str, list[str]]]] = {
    "layout": [
        ("full_screen_dark", [r"dark theme", r"dark background", r"dark[- ]navy",
                              r"navy theme", r"\bdark[- ]themed?\b"]),
        ("bottom_modal", [r"bottom[- ]modal", r"\bmodal popup\b", r"\bbottom modal\b",
                          r"\bpopup over\b", r"\bbottom-modal popup\b"]),
        ("inline", [r"\binline\b", r"embedded in"]),
        ("side_panel", [r"side panel", r"slide-in", r"\bdrawer\b"]),
        # full_screen is the default for any variant where modal was resolved
        ("full_screen", [r"full[- ]screen", r"full screen",
                         r"dedicated (activation|landing) screen",
                         r"INFER_FULL_SCREEN"]),
    ],
    "modal_interrupt": [
        # "no" first — INFER_NO_MODAL added by collect_text when modal-friction is resolved
        ("no", [r"INFER_NO_MODAL", r"full[- ]screen", r"full screen",
                r"dedicated (surface|screen)", r"no modal", r"no popup"]),
        ("yes", [r"\bbottom modal\b", r"\bbottom-modal\b", r"\bmodal popup\b",
                 r"\bpopup over\b"]),
    ],
    "branding": [
        ("crown_header", [r"\bcrown\b", r"crown header", r"crown logo", r"crown lockup",
                          r"\bcrown branding\b"]),
        ("logo_only", [r"logo only", r"just the logo", r"\blogo[- ]only\b"]),
        ("none", []),  # default
    ],
    "price_visibility": [
        # Most specific FIRST: framing banner takes precedence over plain visible
        ("visible_with_framing", [r"INFER_PRICE_WITH_FRAMING",
                                   r"refund banner", r"\bguarantee\b.*banner",
                                   r"₹\s*1\s*\+\s*refund", r"\+\s*refund banner",
                                   r"\bbanner\b.*refund", r"refund.*\bbanner\b",
                                   r"banner.*₹\s*1"]),
        # Opaque only when explicit "no price" / "no ₹ anywhere" — not "no concrete past wins"
        ("opaque", [r"no\s+₹\s*1\s+(anywhere|on screen|visible)",
                    r"price\s+(hidden|absent|opaque)",
                    r"no price\s+(anywhere|on screen|shown)",
                    r"₹.*\bnowhere\b", r"INFER_PRICE_OPAQUE"]),
        # Visible price (default for "₹1 sticky CTA" / "₹1 button")
        ("visible_primary", [r"₹\s*1\s*sticky", r"₹\s*1\s*button", r"₹\s*1\s*cta",
                             r"price visible", r"explicit ₹\s*1", r"₹\s*1\s*trial",
                             r"INFER_PRICE_VISIBLE"]),
    ],
    "cta_style": [
        ("high_contrast_green", [r"green CTA", r"green button", r"bright green",
                                  r"high[- ]contrast green", r"\bgreen sticky\b"]),
        ("muted_premium", [r"dark teal", r"\bmuted\s+(dark|premium)\b", r"premium tone",
                           r"muted[- ]premium", r"premium[- ]toned"]),
        ("low_contrast_subordinate", [r"low[- ]contrast", r"visually subordinate",
                                       r"subordinate to", r"low contrast"]),
        ("high_contrast_warm", [r"red CTA", r"orange CTA", r"\bwarm CTA\b",
                                r"red button", r"orange button"]),
        ("high_contrast_cool", [r"blue CTA", r"teal CTA", r"\bcool CTA\b"]),
        ("text_link", [r"text link", r"underlined text", r"text[- ]only CTA"]),
        ("neutral_default", []),  # default
    ],
    "cta_stack": [
        ("dual_outline_plus_sticky", [r"dual CTA", r"dual cta", r"two CTAs",
                                       r"outline\s*\+\s*sticky", r"outline plus sticky",
                                       r"dual[- ]CTA stack"]),
        ("dual_side_by_side", [r"side[- ]by[- ]side", r"two equal", r"two equally"]),
        ("primary_plus_secondary_link", [r"primary\s*\+\s*secondary", r"primary plus secondary",
                                          r"with text link"]),
        ("single", []),  # default
    ],
    "urgency_mechanism": [
        # countdown_timer needs strong positive signal — and INFER_HAS_COUNTDOWN if
        # the countdown_timer friction was introduced by V1 and persists in V2-V4.
        ("countdown_timer", [r"countdown timer", r"\d+:\d+\s*(left|remaining)",
                              r"'\d+:\d+\s*Left'", r"\bcount[- ]?down\b",
                              r"INFER_HAS_COUNTDOWN"]),
        ("scarcity_count", [r"only \d+ (seats?|spots?|left)", r"\d+\s*spots? remaining",
                             r"limited spots", r"X left"]),
        ("social_proof_realtime", [r"viewing now", r"people viewing", r"real[- ]time"]),
        ("deadline_text", [r"\bdeadline\b", r"ends on", r"closes on", r"offer ends"]),
        ("none", []),  # default
    ],
    "refund_or_guarantee_copy": [
        ("explicit_sla", [r"refund in \d+\s*(s|sec|seconds|min)", r"refund within \d+",
                          r"refund.*to source", r"\bsla\b"]),
        ("money_back_guarantee", [r"money[- ]back guarantee", r"\d+[- ]day money back",
                                  r"money back"]),
        ("no_questions_asked", [r"no questions asked", r"no questions"]),
        ("implicit_refund", [r"INFER_HAS_REFUND_COPY",
                             r"\binstant refund\b", r"refund clause",
                             r"cancel anytime", r"cancel any time"]),
        ("absent", []),  # default
    ],
    "trust_signal": [
        # INFER_REGULATORY_PLUS_EVIDENCE fires when both regulator AND any of
        # (aggregate metrics, named wins, third-party logos) appear in the variant text.
        ("regulatory_plus_evidence", [r"INFER_REGULATORY_PLUS_EVIDENCE"]),
        ("regulatory", [r"\bsebi\b", r"\bfca\b", r"\bsec\b", r"regulator", r"\brbi\b",
                        r"inh\d+", r"reg\.\s*inh"]),
        ("evidence_mode", [r"\d+\.?\d*%\s*(accuracy|profitable)",
                           r"\d+\s*\+\s*(trades|profitable|users|ideas)",
                           r"named past wins", r"recent wins carousel", r"track record"]),
        ("third_party_endorsement", [r"google for startups", r"economic times",
                                     r"press logos?", r"\bet\b logo", r"as seen on"]),
        ("implicit", []),  # default
    ],
    "evidence_detail": [
        # Most specific first.
        ("real_outcome_disclosure", [r"entry.*exit.*days held", r"entry.*exit.*gain",
                                      r"closed trade with (entry|exit)",
                                      r"days held.*rupee gain"]),
        # aggregate_plus_named: explicit signal from collect_text when both signals exist
        # AND not negated for this variant
        ("aggregate_plus_named", [r"INFER_AGGREGATE_PLUS_NAMED"]),
        # named_past_outcome: requires INFER_HAS_NAMED_WINS (set when stocks appear in
        # this variant's screen_comparison + variant description, NOT comparative text)
        ("named_past_outcome", [r"INFER_HAS_NAMED_WINS"]),
        # aggregate_metric: explicit aggregate %s / counts in THIS variant's text
        ("aggregate_metric", [r"\d+%\s*\+?\s*accuracy", r"\d+\s*\+\s*trades?",
                              r"\d+\s*\+\s*profitable", r"\d+%\+\s*accuracy",
                              r"\baggregate metrics?\b", r"\d+\s*-?\s*column metrics"]),
        ("user_testimonial", [r"\btestimonial\b", r"user review", r"\d+[- ]star rating",
                              r"\bstar rating\b"]),
        ("third_party_logos", [r"google logo", r"press logos?", r"\bET\b logo"]),
        ("none", []),  # default
    ],
}

# Quoted-string pattern for cta_primary_label. Match strings like "Start Trial Now",
# 'Activate for ₹1', 'Unlock FREE trade'. Keep first matching string per variant.
CTA_LABEL_PATTERN = re.compile(r"['\"]([A-Z][^'\"]{2,60})['\"]")


# ─── helpers ────────────────────────────────────────────────────────────────

def collect_text(matrix: dict, apriori: dict, our_variant_id: str) -> str:
    """Concatenate all relevant text for a variant — used as the rule corpus.

    Includes per-variant positive signals only:
      1. Variant description (short, prescriptive) — 2x weight
      2. screen_comparison.summaries[this_variant] (long, descriptive)
      3. friction_provenance where this variant is present
      4. theme_movement.persistent/introduced where this variant is present
    PLUS derived INFER_* signals built from friction_provenance.resolved_by
    and theme_movement structure (e.g. INFER_NO_MODAL when the modal-interrupt
    friction is resolved by this variant).

    Notably DROPPED:
      - friction.resolved_by entries (those are NEGATIVE signals — friction no longer present)
      - theme_movement.resolved buckets (same reason)
    These exclusions prevent false-positive matches (e.g. "modal interrupts"
    appearing as RESOLVED text and matching modal_interrupt=yes).
    """
    apriori_id = next((v["apriori_id"] for v in matrix["variants"]
                       if v["id"] == our_variant_id), None)
    if not apriori_id:
        return ""

    parts = []
    # 1. Variant description — 2x weight
    for v in apriori.get("variants", []):
        if v["id"] == apriori_id:
            parts.append(v.get("description", ""))
            parts.append(v.get("description", ""))

    # 2. Screen-comparison summaries (this variant only)
    for sc in apriori.get("screen_comparison", []):
        s = sc.get("summaries", {}).get(apriori_id, "")
        if s:
            parts.append(s)

    # 3. Friction-present (positive only). NOT resolved_by (those are antitheses).
    for fp in apriori.get("friction_provenance", []):
        if fp.get("presence", {}).get(apriori_id) == "present":
            parts.append(f"FRICTION_PRESENT: {fp.get('friction', '')}")

    # 4. Theme persistent/introduced where this variant is present
    for bucket in ("persistent", "introduced"):
        for theme in apriori.get("theme_movement", {}).get(bucket, []):
            if apriori_id in theme.get("present_in", []):
                parts.append(f"THEME: {theme.get('name', '')} {theme.get('description', '')[:200]}")

    # 5. Derived INFER_* signals from friction antitheses + theme structure
    parts.append(_derive_inferences(apriori, apriori_id))

    return "\n".join(parts)


def _derive_inferences(apriori: dict, apriori_id: str) -> str:
    """Derive antithesis/structural signals from friction_provenance + theme_movement.

    These INFER_* tokens are matched verbatim by the rules (see RULES dict).
    """
    inferences = []
    # Friction antitheses: if X friction is RESOLVED for this variant, the antithesis is true.
    for fp in apriori.get("friction_provenance", []):
        fid = (fp.get("id") or "").lower()
        ftext = (fp.get("friction") or "").lower()
        if apriori_id not in fp.get("resolved_by", []):
            continue
        # Modal-interrupt friction resolved → no modal, full screen
        if "modal" in ftext or "popup" in ftext or "interrupt" in ftext:
            inferences += ["INFER_NO_MODAL", "INFER_FULL_SCREEN"]
        # Price-opacity friction resolved → price visible (but not necessarily framed)
        if "price opacity" in ftext or "no ₹1 visible" in ftext or "price hidden" in ftext:
            inferences.append("INFER_PRICE_VISIBLE")
    # Friction PRESENT signals: countdown timer / blurred card / etc.
    for fp in apriori.get("friction_provenance", []):
        if fp.get("presence", {}).get(apriori_id) != "present":
            continue
        ftext = (fp.get("friction") or "").lower()
        if "countdown" in ftext or "timer" in ftext:
            inferences.append("INFER_HAS_COUNTDOWN")
    # Theme PRESENT signals: countdown timer in persistent/introduced
    for bucket in ("persistent", "introduced"):
        for theme in apriori.get("theme_movement", {}).get(bucket, []):
            if apriori_id not in theme.get("present_in", []):
                continue
            tname = (theme.get("name") or "").lower()
            if "countdown" in tname or "timer" in tname:
                inferences.append("INFER_HAS_COUNTDOWN")
    # Aggregate vs named: scan THIS variant's screen_comparison for both signals
    var_text = ""
    for sc in apriori.get("screen_comparison", []):
        var_text += " " + sc.get("summaries", {}).get(apriori_id, "")
    for v in apriori.get("variants", []):
        if v["id"] == apriori_id:
            var_text += " " + v.get("description", "")
    var_text_lower = var_text.lower()
    # has_aggregate accepts either order: "85%+ accuracy" OR "accuracy 84.7%"
    has_aggregate = bool(re.search(
        r"\d+\.?\d*%\s*\+?\s*(accuracy|profitable|trades)|"
        r"(accuracy|profitable|trades)\s+\d+\.?\d*%|"
        r"\d+\s*\+\s*(trades|profitable|users|ideas)|"
        r"column metrics",
        var_text_lower))
    # Named-stocks signal — must NOT be in negation context
    has_named = False
    for stock in ("tmpv", "zomato", "reliance", "named recent wins", "stock by name"):
        for m in re.finditer(re.escape(stock), var_text_lower):
            window_start = max(0, m.start() - 80)
            window = var_text_lower[window_start:m.start()]
            negation_terms = ("no ", "absent", "stripped", "missing", "without",
                              "removed", "dropped", "no concrete", "no past wins",
                              "no named", "replaced.*with abstract")
            if not any(re.search(neg, window) for neg in negation_terms):
                has_named = True
                break
        if has_named:
            break
    if has_aggregate and has_named:
        inferences.append("INFER_AGGREGATE_PLUS_NAMED")
    elif has_named:
        inferences.append("INFER_HAS_NAMED_WINS")
    # Refund SLA / banner inference — also infers refund_or_guarantee_copy
    if re.search(r"refund.*banner|banner.*refund|activate @ ₹\s*1.*refund|refund clause|instant refund", var_text_lower):
        inferences.append("INFER_PRICE_WITH_FRAMING")
        inferences.append("INFER_HAS_REFUND_COPY")
    if re.search(r"cancel anytime|cancel any time", var_text_lower):
        inferences.append("INFER_HAS_REFUND_COPY")
    # Combined trust_signal: regulatory + ANY of (aggregate, named, third-party)
    has_regulator = bool(re.search(r"\bsebi\b|\bfca\b|\bsec\b|\brbi\b|inh\d+|reg\.\s*inh", var_text_lower))
    # third_party: detect Google / ET / press / awards explicitly OR as short brand mentions
    # adjacent to "badge" / "logo" / "trust" (catches abbreviations like "SEBI / Google / ET")
    has_third_party = bool(re.search(
        r"google for startups|economic times|press logos?|as seen on|"
        r"awarded.*by|\baccelerator\b|"
        r"\b(google|et)\s*(/\s*\w+\s*)?(badge|logo|trust|awarded|accelerator)|"
        r"trust badges?",
        var_text_lower))
    if has_regulator and (has_aggregate or has_named or has_third_party):
        inferences.append("INFER_REGULATORY_PLUS_EVIDENCE")
    return " ".join(set(inferences))


def map_cell(text: str, dim: str, rules: list[tuple[str, list[str]]]
             ) -> tuple[str | None, str, str | None]:
    """Apply rules for one dimension. Returns (value, confidence, matching_pattern)."""
    text_lower = text.lower()
    for value, patterns in rules:
        if not patterns:
            continue  # Default — handled separately below
        for p in patterns:
            try:
                if re.search(p, text_lower, re.IGNORECASE):
                    return value, "high", p
            except re.error:
                continue
    # No patterns matched — try default (entry with empty patterns)
    default = next((v for v, ps in rules if not ps), None)
    if default is not None:
        return default, "low_default", None
    return None, "needs_review", None


def extract_cta_label(text: str) -> str | None:
    """Extract the first plausible CTA button label.

    Heuristics:
    - Capitalized quoted string, 3-60 chars
    - Prefer strings starting with imperative verbs (Start, Activate, Unlock, etc.)
    - Reject brand strings ("India's Trusted Advisory"), section headers
      ("Recent Wins"), and descriptive phrases ("dual CTA stack").
    - Reject persona quotes (longer prose).
    """
    REJECT_SUBSTRINGS = (
        "trusted advisory", "live trades", "recent wins", "dual cta",
        "outline +", "outline plus sticky", "past performance", "mostly recent",
        "magic link", "stock/f&o ideas",  # explanation phrase, not a button
        "& get ", "& receive", "instant refund",  # banner copy, not button
        "/", " or ",  # phrases with separators are usually descriptions
    )
    PREFER_PREFIXES = (
        "start", "activate", "unlock", "see ", "claim", "get ", "try ",
        "open ", "send ", "join", "buy ",
    )
    candidates = CTA_LABEL_PATTERN.findall(text)
    # First pass: imperatives with strong CTA prefix
    for c in candidates:
        cl = c.lower()
        if any(r in cl for r in REJECT_SUBSTRINGS):
            continue
        if "'" in c or len(c.split()) > 8:
            continue
        if any(cl.startswith(p) for p in PREFER_PREFIXES):
            return c
    # Second pass: short capitalized strings that don't start with brand-like terms
    for c in candidates:
        cl = c.lower()
        if any(r in cl for r in REJECT_SUBSTRINGS):
            continue
        if "'" in c:  # possessive ("India's") — usually brand
            continue
        if len(c.split()) > 6:
            continue
        # Skip strings ending with possessive-ish adjectives
        if cl.endswith(" advisory") or cl.endswith(" carousel") or cl.endswith(" header"):
            continue
        return c
    return None


def automap(matrix: dict, apriori: dict) -> tuple[dict, dict]:
    """Apply auto-mapping. Returns (updated_matrix, trace_dict)."""
    trace = {
        "_method": "rule_based_v1",
        "_run_at": str(date.today()),
        "_summary": {"high": 0, "low_default": 0, "needs_review": 0, "total": 0},
        "per_variant": {},
    }

    for v in matrix["variants"]:
        text = collect_text(matrix, apriori, v["id"])
        v_trace = {}

        for dim, rules in RULES.items():
            value, confidence, matched_pattern = map_cell(text, dim, rules)
            if value is not None:
                v["elements"][dim] = value
            v_trace[dim] = {
                "value": value if value else NEEDS_REVIEW,
                "confidence": confidence,
                "matched_pattern": matched_pattern,
            }
            trace["_summary"][confidence] += 1
            trace["_summary"]["total"] += 1

        # cta_primary_label — freeform, separate logic
        label = extract_cta_label(text)
        if label:
            v["elements"]["cta_primary_label"] = label
            v_trace["cta_primary_label"] = {
                "value": label, "confidence": "high",
                "matched_pattern": "first quoted-string capitalized 3-60 chars",
            }
            trace["_summary"]["high"] += 1
        else:
            v_trace["cta_primary_label"] = {
                "value": NEEDS_REVIEW, "confidence": "needs_review",
                "matched_pattern": None,
            }
            trace["_summary"]["needs_review"] += 1
        trace["_summary"]["total"] += 1

        trace["per_variant"][v["id"]] = v_trace

    return matrix, trace


# ─── CLI ────────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser(
        description="Rule-based taxonomy auto-mapper. Phase 3a of the plug-in roadmap.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("client", help="Client slug")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    ap.add_argument("-o", "--output-dir", default=None,
                    help="Output dir override (default: data/<client>/)")
    args = ap.parse_args()

    data_dir = Path(args.output_dir) if args.output_dir else (ROOT / "data" / args.client)
    matrix_path = data_dir / "element_matrix.json"
    apriori_path = data_dir / "apriori_input.json"

    if not matrix_path.is_file():
        print(f"Error: {matrix_path} not found. Run ingest-apriori.py first.",
              file=sys.stderr)
        return 1
    if not apriori_path.is_file():
        print(f"Error: {apriori_path} not found. Run ingest-apriori.py first.",
              file=sys.stderr)
        return 1

    matrix = json.loads(matrix_path.read_text())
    apriori = json.loads(apriori_path.read_text())

    matrix, trace = automap(matrix, apriori)

    summary = trace["_summary"]
    total = summary["total"]
    high = summary["high"]
    default = summary["low_default"]
    needs = summary["needs_review"]
    high_pct = round(100 * high / total, 1) if total else 0
    default_pct = round(100 * default / total, 1) if total else 0
    needs_pct = round(100 * needs / total, 1) if total else 0

    print(f"Auto-mapped {high + default}/{total} cells "
          f"(high: {high} = {high_pct}%, low_default: {default} = {default_pct}%, "
          f"needs_review: {needs} = {needs_pct}%)")
    print()

    if needs:
        print("Cells still needing review:")
        for vid, dims in trace["per_variant"].items():
            for dim, info in dims.items():
                if info["confidence"] == "needs_review":
                    print(f"  {vid}.{dim}")
        print()

    if args.dry_run:
        print("(dry-run mode — no files written)")
        return 0

    # Update extraction_confidence to reflect automap status
    matrix.setdefault("extraction_confidence", {})
    matrix["extraction_confidence"]["_automap_run_at"] = str(date.today())
    matrix["extraction_confidence"]["_automap_summary"] = summary
    matrix["extraction_confidence"]["_method"] = "rule_based_v1 + ingest-apriori"

    matrix_path.write_text(json.dumps(matrix, indent=2))
    (data_dir / "automap-trace.json").write_text(json.dumps(trace, indent=2))

    print(f"Wrote:")
    print(f"  ✓  {matrix_path.relative_to(ROOT) if not args.output_dir else matrix_path}")
    print(f"  ✓  {(data_dir / 'automap-trace.json').relative_to(ROOT) if not args.output_dir else (data_dir / 'automap-trace.json')}")
    print()
    print("Next: review the matrix; high-confidence cells should be correct, "
          "low_default cells are best-guesses, needs_review cells require manual mapping.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

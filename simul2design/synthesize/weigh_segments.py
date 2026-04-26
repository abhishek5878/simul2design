"""weigh-segments — pure-Python port of .claude/skills/weigh-segments/SKILL.md.

Reads element_matrix.json + (optional) overlay text. Emits weighted_scores.json
with per-(dimension, value) evidence classification + weighted score.

NO LLM CALLS. Fully deterministic.

Five evidence tiers (per SKILL.md):
- clean_contrast: dim is the sole-diff in a clean_element_contrasts entry
- friction_direct: friction_points has an entry naming this value
- confounded: value is in matrix.confounds[]
- untested: value is in taxonomy but not observed in any variant
- variant_only: value observed but only alongside other-dim changes

Output schema follows the SKILL.md spec exactly.

Limitations of this port (to be addressed in follow-ups):
- Client-overlay contradictions (e.g., '.claude/rules/element-taxonomy-univest.md'
  → "green CTA + Trust Seeker = -10pts") are NOT yet applied. Pass them
  explicitly via the `overlay_contradictions` argument if known.
- "expected_mechanism" notes for untested values are NOT yet pulled from the
  overlay markdown. Pass via `untested_mechanism_notes` if known.
"""

from __future__ import annotations
import re
from typing import Any

from simul2design.taxonomy import (
    ENUM_DIMENSIONS,
    FREEFORM_DIMENSIONS,
    parse_allowed_values,
)


def _parse_contrast_variant_ids(contrast_label: str) -> tuple[str, str] | None:
    """Parse 'V2 -> V3' or 'V2->V3' or 'Control -> V1' to (from_id, to_id)."""
    m = re.match(r"^\s*(\S+)\s*->\s*(\S+)\s*$", contrast_label)
    if not m:
        return None
    return m.group(1).strip(), m.group(2).strip()


def _compute_clean_contrast_for_value(
    matrix: dict, contrast: dict, dim: str, value: str
) -> dict:
    """Compute per-segment delta + weighted score for a clean-contrast value.

    Returns:
        {
          "per_segment_impact": {seg_id: {"delta_pts": float, "basis": str}},
          "weighted_score_pts": float,
          "contrast_label": str,  # e.g. "V2->V3"
        }
    """
    parsed = _parse_contrast_variant_ids(contrast["contrast"])
    if not parsed:
        return {"per_segment_impact": {}, "weighted_score_pts": None, "contrast_label": contrast["contrast"]}
    from_id, to_id = parsed

    variants_by_id = {v["id"]: v for v in matrix["variants"]}
    if from_id not in variants_by_id or to_id not in variants_by_id:
        return {"per_segment_impact": {}, "weighted_score_pts": None, "contrast_label": contrast["contrast"]}
    from_v = variants_by_id[from_id]
    to_v = variants_by_id[to_id]

    # Determine the polarity: are we asking about the value at the "to" or "from" side?
    diff = contrast.get("diff", {}).get(dim, [])
    if len(diff) != 2:
        return {"per_segment_impact": {}, "weighted_score_pts": None, "contrast_label": contrast["contrast"]}
    from_val, to_val = diff[0], diff[1]
    if value == to_val:
        sign = 1.0  # adopting `value` (the to-side) gives this delta
    elif value == from_val:
        sign = -1.0
    else:
        return {"per_segment_impact": {}, "weighted_score_pts": None, "contrast_label": contrast["contrast"]}

    per_segment: dict[str, dict[str, Any]] = {}
    weighted = 0.0
    for seg in matrix["segments"]:
        sid = seg["id"]
        from_conv = from_v["conversion_by_segment"].get(sid)
        to_conv = to_v["conversion_by_segment"].get(sid)
        if from_conv is None or to_conv is None:
            continue
        delta_pts = sign * (to_conv - from_conv) * 100
        per_segment[sid] = {
            "delta_pts": round(delta_pts, 2),
            "basis": f"clean_contrast:{from_id}->{to_id}",
        }
        weighted += seg["weight"] * delta_pts
    return {
        "per_segment_impact": per_segment,
        "weighted_score_pts": round(weighted, 2),
        "contrast_label": f"{from_id}->{to_id}",
    }


def _value_is_clean_contrast(matrix: dict, dim: str, value: str) -> dict | None:
    """Find the clean_contrast for this (dim, value), if any.

    A clean contrast is a clean_element_contrasts entry where:
    - The diff has exactly one key (this dimension)
    - This dimension's diff includes `value` as one of the two sides
    """
    for contrast in matrix.get("clean_element_contrasts", []):
        diff = contrast.get("diff", {})
        if len(diff) != 1:
            continue
        if dim not in diff:
            continue
        if value in diff[dim]:
            return contrast
    return None


def _value_in_friction(matrix: dict, dim: str, value: str) -> list[dict]:
    """Return friction_points entries that mention this value (best-effort string match).

    Friction summaries reference values in prose ('blurred trade card alienates...'),
    so this matches by substring. Best-effort — false positives possible.
    """
    matches = []
    val_kw = value.lower().replace("_", " ")
    for fp in matrix.get("friction_points", []):
        summary = (fp.get("summary") or "").lower()
        if val_kw in summary:
            matches.append(fp)
    return matches


def _value_in_confounds(matrix: dict, dim: str, value: str) -> list[dict]:
    """Return confound entries that name this (dim, value)."""
    target = f"{dim}={value}"
    matches = []
    for cf in matrix.get("confounds", []):
        elements = cf.get("elements", [])
        if target in elements:
            matches.append(cf)
    return matches


def _value_observed_in_variants(matrix: dict, dim: str, value: str) -> list[str]:
    """Return list of variant ids where this (dim, value) appears."""
    return [v["id"] for v in matrix.get("variants", [])
            if v.get("elements", {}).get(dim) == value]


def _classify_value(matrix: dict, dim: str, value: str) -> tuple[str, dict]:
    """Pick the highest-confidence evidence type that fits.

    Returns (evidence_type, metadata_dict) where metadata varies by type.
    """
    contrast = _value_is_clean_contrast(matrix, dim, value)
    if contrast is not None:
        return ("clean_contrast", {"contrast": contrast})

    confound_matches = _value_in_confounds(matrix, dim, value)
    if confound_matches:
        return ("confounded", {"confounds": confound_matches})

    friction_matches = _value_in_friction(matrix, dim, value)
    if friction_matches:
        return ("friction_direct", {"friction": friction_matches})

    observed_in = _value_observed_in_variants(matrix, dim, value)
    if not observed_in:
        return ("untested", {})

    # Observed but no clean contrast and no confound listing → variant_only
    return ("variant_only", {"variants": observed_in})


def _compute_dimension_value(matrix: dict, dim: str, value: str) -> dict:
    """Build the full output entry for one (dim, value) pair."""
    evidence_type, meta = _classify_value(matrix, dim, value)
    observed_in = _value_observed_in_variants(matrix, dim, value)

    entry = {
        "evidence_type": evidence_type,
        "observed_in_variants": observed_in,
        "per_segment_impact": {},
        "weighted_score_pts": None,
        "contradictions_applied": [],
        "adjusted_score_pts": None,
        "confidence": "none",
        "flags": [],
    }

    if evidence_type == "clean_contrast":
        result = _compute_clean_contrast_for_value(matrix, meta["contrast"], dim, value)
        entry["per_segment_impact"] = result["per_segment_impact"]
        entry["weighted_score_pts"] = result["weighted_score_pts"]
        entry["adjusted_score_pts"] = result["weighted_score_pts"]
        entry["contrast_label"] = result["contrast_label"]
        # Confidence per SKILL.md: high requires clean contrast AND any per-segment delta ≥ ~8pts
        max_abs_delta = max(
            (abs(s["delta_pts"]) for s in result["per_segment_impact"].values()),
            default=0,
        )
        entry["confidence"] = "high" if max_abs_delta >= 8 else "medium"

    elif evidence_type == "friction_direct":
        # Pull flag rate + segment pattern from the first matching friction point
        fp = meta["friction"][0]
        count = fp.get("count", 0)
        of_total = fp.get("of_total", 50)
        flag_rate = round(count / of_total, 3) if of_total else 0
        entry["friction_evidence"] = {
            "friction_id": fp.get("id"),
            "summary": fp.get("summary"),
            "flag_count": count,
            "of_total": of_total,
            "flag_rate": flag_rate,
            "segment_pattern": fp.get("segment_pattern"),
            "directional_signal": "negative",
        }
        # Per SKILL.md: cross-segment ≥50% = decisive negative; ≥30% = medium; else low
        if fp.get("segment_pattern") == "cross_segment" and flag_rate >= 0.5:
            entry["confidence"] = "medium"
        elif flag_rate >= 0.3:
            entry["confidence"] = "medium"
        else:
            entry["confidence"] = "low"

    elif evidence_type == "confounded":
        entry["signal_from"] = {
            "variants": observed_in,
            "confounds": [c.get("note", "") for c in meta["confounds"]],
        }
        entry["confidence"] = "none"

    elif evidence_type == "variant_only":
        entry["signal_from"] = {"variants": observed_in}
        entry["confidence"] = "low"

    elif evidence_type == "untested":
        entry["expected_mechanism"] = None  # Filled by overlay if available
        entry["confidence"] = "none"

    return entry


def _rank_dimension(values_dict: dict) -> dict:
    """Rank values by adjusted_score_pts; identify recommended; tag dimension informativeness."""
    rankable = [(name, e) for name, e in values_dict.items()
                if e.get("adjusted_score_pts") is not None]
    if not rankable:
        return {
            "recommended": {"value": None, "rationale": "no rankable evidence for this dimension",
                             "confidence": "none"},
            "dimension_informativeness": "non_informative",
        }
    rankable.sort(key=lambda kv: kv[1]["adjusted_score_pts"], reverse=True)
    top_name, top_entry = rankable[0]
    runner_diff = (top_entry["adjusted_score_pts"]
                    - rankable[1][1]["adjusted_score_pts"]) if len(rankable) > 1 else None
    is_tie = runner_diff is not None and abs(runner_diff) < 5
    return {
        "recommended": {
            "value": top_name,
            "rationale": (f"Highest adjusted_score_pts: {top_entry['adjusted_score_pts']}"
                          + (f" (tie within 5pt of runner-up)" if is_tie else "")),
            "confidence": top_entry.get("confidence", "low"),
        },
        "dimension_informativeness": "rankable",
    }


# ─── public API ─────────────────────────────────────────────────────────────

def weigh_segments(matrix: dict, *,
                    overlay_taxonomy_md: str | None = None) -> dict:
    """Run weigh-segments on a matrix. Returns the weighted_scores dict.

    Args:
        matrix: parsed element_matrix.json
        overlay_taxonomy_md: optional client overlay markdown text. If omitted,
            only base taxonomy values are scanned. Overlay-driven contradictions
            are NOT yet applied (TODO — see module docstring).

    Returns:
        dict matching the SKILL.md output schema.
    """
    # Build the universe of (dim, value) pairs to score
    base_allowed = parse_allowed_values()
    overlay_allowed = parse_allowed_values(overlay_taxonomy_md) if overlay_taxonomy_md else {}
    all_dims: dict[str, set[str]] = {}
    for dim, vals in base_allowed.items():
        all_dims.setdefault(dim, set()).update(vals)
    for dim, vals in overlay_allowed.items():
        all_dims.setdefault(dim, set()).update(vals)
    # Also include any value observed in variants but missing from the taxonomy
    # (this catches client-overlay-only values not declared in either taxonomy file)
    for v in matrix.get("variants", []):
        for dim, val in v.get("elements", {}).items():
            if isinstance(val, str) and val and dim in all_dims:
                all_dims[dim].add(val)

    audience_weights = {seg["id"]: seg["weight"] for seg in matrix.get("segments", [])}

    out_dimensions: dict[str, Any] = {}
    summary_counts = {"rankable": 0, "non_informative": 0, "untested_only": 0,
                       "confounded": 0, "friction_only": 0, "clean_contrast": 0}
    tier_counts = {"clean_contrast": 0, "friction_direct": 0, "confounded": 0,
                    "variant_only": 0, "untested": 0}

    for dim in sorted(all_dims.keys()):
        if dim not in ENUM_DIMENSIONS:
            continue  # Skip freeform dims (cta_primary_label) — handled by synthesize
        values_out: dict[str, Any] = {}
        for value in sorted(all_dims[dim]):
            entry = _compute_dimension_value(matrix, dim, value)
            values_out[value] = entry
            tier_counts[entry["evidence_type"]] = tier_counts.get(entry["evidence_type"], 0) + 1
        ranked = _rank_dimension(values_out)
        out_dimensions[dim] = {
            "values": values_out,
            "recommended": ranked["recommended"],
            "dimension_informativeness": ranked["dimension_informativeness"],
        }
        if ranked["dimension_informativeness"] == "rankable":
            summary_counts["rankable"] += 1
        else:
            summary_counts["non_informative"] += 1

    return {
        "version": "1.0",
        "client": matrix.get("client", "unknown"),
        "source_matrix": matrix.get("source", {}).get("source_file", ""),
        "audience_weights": audience_weights,
        "method": "weigh_segments_python_v1 (deterministic; LLM-free)",
        "dimensions": out_dimensions,
        "dimension_summary": {
            "rankable_dimensions": summary_counts["rankable"],
            "non_informative_dimensions": summary_counts["non_informative"],
            "evidence_tier_distribution": tier_counts,
            "note": "Evidence-tier distribution is a dataset-informativeness KPI.",
        },
        "flags": [
            "Overlay contradictions not yet applied (TODO — see weigh_segments.py docstring).",
            "Untested 'expected_mechanism' notes not yet pulled from overlay markdown.",
        ],
    }

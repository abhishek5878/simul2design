"""AbReport (apriori_simulation_engine) → ComparisonData adapter.

The engine emits `AbReport` (defined in their repo at
`src/api/models/ab_report.py`); this module converts it to a dict that
`simul2design.schemas.ComparisonData.model_validate(...)` accepts.

The adapter is intentionally dict-in / dict-out so this package never
imports from the engine. Pass `report = AbReport.model_dump()` from the
engine side; receive a dict you can hand straight to
`SynthesisPipeline.run(...)` or to `ComparisonData(**...)`.

Per-segment per-variant completion rates resolve through three sources, in
priority order, per segment+variant cell:

  1. measured_subsample — counts of `outcome == "convert"` from
     `deep_dive.personas[].variant_{a,b}.outcome` and
     `monologue_diff[].decision_{a,b}` (de-duped by persona_id), divided
     by the observed count for that segment+variant. Real conversion rate
     on a sub-sample of the segment.
  2. preference_proxy — falls back to a binary 100/0 derived from
     `persona_split[].preferred_variant` when source 1 yields zero observed
     personas for a segment.
  3. absent — both null when neither source has data
     (preference_variant == "neither" AND observed_n == 0).

The per-cell source is recorded in `_extraction_confidence.cells[<segment>][<variant>]`
and the aggregate guidance is in `_extraction_confidence._adapter_note`.
Downstream `weigh_segments` and Wilson interval estimators see real
sub-sample rates when available; the preference proxy is the floor.
"""

from __future__ import annotations

import hashlib
from typing import Any

ADAPTER_VERSION = "1.1.0"
SOURCE_NAME = "apriori_simulation_engine.ab_report"

CONVERT_OUTCOMES = {"convert"}

ADAPTER_NOTE = (
    "completion_rate values in segment_verdicts[].metrics_by_variant[*] are "
    "resolved per-cell with three tiers: (1) MEASURED_SUBSAMPLE — real "
    "conversion rate computed from per-persona outcomes in "
    "AbReport.deep_dive.personas[].variant_{a,b}.outcome and "
    "AbReport.monologue_diff[].decision_{a,b} (de-duped by persona_id), "
    "with the cell's observed_n in the same dict; (2) PREFERENCE_PROXY — "
    "binary 100/0 from persona_split[].preferred_variant, used when no "
    "per-persona outcomes are present for that segment; (3) ABSENT — both "
    "null when preferred_variant=='neither' and observed_n==0. Treat "
    "preference_proxy cells as direction-only; measured_subsample cells "
    "carry the observed_n so Wilson intervals downstream widen "
    "appropriately on small samples."
)


def _coerce_variant_tag(tag: Any) -> str | None:
    """Map AbReport's 'A'/'B' tags to lowercase 'a'/'b' for ingest. 'neither'/'both' → None."""
    if not isinstance(tag, str):
        return None
    t = tag.strip().lower()
    if t == "a":
        return "a"
    if t == "b":
        return "b"
    return None


def _segment_id(segment_name: str) -> str:
    return segment_name.strip().lower().replace(" ", "_").replace("-", "_")


def _stable_id(*parts: str) -> str:
    """Deterministic short id for friction items / themes that lack an id in AbReport."""
    h = hashlib.sha1("||".join(parts).encode("utf-8")).hexdigest()
    return f"af_{h[:10]}"


def _collect_segment_outcomes(report: dict) -> dict[str, dict[str, list[str]]]:
    """Return per-segment per-variant outcome lists.

    Walks `deep_dive.personas[]` first (richest data), then
    `monologue_diff[]`, de-duplicating by persona_id so the same persona
    doesn't double-count if they appear in both. Personas without a known
    persona_id fall back to `(segment, name)` for de-dup.

    Returns:
        {segment_name: {"a": [outcome_str, ...], "b": [outcome_str, ...]}}
        Outcome strings are AbReport's DecisionOutcome literals
        ("convert" / "hesitate" / "abandon") plus any unrecognized values
        passed through verbatim. Empty lists when no outcomes are observed.
    """
    out: dict[str, dict[str, list[str]]] = {}
    seen: set[tuple[str, str]] = set()  # (segment, persona_key)

    def _record(segment: str, key: str, outcome_a: str, outcome_b: str) -> None:
        if not segment:
            return
        dedup_key = (segment, key)
        if dedup_key in seen:
            return
        seen.add(dedup_key)
        bucket = out.setdefault(segment, {"a": [], "b": []})
        if outcome_a:
            bucket["a"].append(outcome_a)
        if outcome_b:
            bucket["b"].append(outcome_b)

    deep = (report.get("deep_dive") or {}).get("personas") or []
    for p in deep:
        seg = p.get("segment") or ""
        pid = p.get("id") or p.get("name") or ""
        oa = (p.get("variant_a") or {}).get("outcome") or ""
        ob = (p.get("variant_b") or {}).get("outcome") or ""
        _record(seg, str(pid), str(oa), str(ob))

    for md in report.get("monologue_diff") or []:
        seg = md.get("segment") or ""
        pid = md.get("persona_id") or md.get("persona_name") or ""
        oa = md.get("decision_a") or ""
        ob = md.get("decision_b") or ""
        _record(seg, str(pid), str(oa), str(ob))

    return out


def _completion_rate(outcomes: list[str]) -> float | None:
    """Conversion rate from a list of outcome strings, percent. None on empty."""
    if not outcomes:
        return None
    converted = sum(1 for o in outcomes if o in CONVERT_OUTCOMES)
    return round(100.0 * converted / len(outcomes), 1)


def _build_metadata(report: dict) -> dict[str, Any]:
    meta = report.get("meta", {})
    return {
        "simulation_id": meta.get("simulation_id", "unknown"),
        "simulation_name": meta.get("study_name") or meta.get("screen_label") or "unnamed_study",
        "client": meta.get("client", ""),
        "screen_label": meta.get("screen_label", ""),
        "persona_count": int(meta.get("persona_count", 0)),
        "runs_per_persona": int(meta.get("runs_per_persona", 1)),
        "generated_at": meta.get("generated_at", ""),
        "_source": SOURCE_NAME,
        "_adapter_version": ADAPTER_VERSION,
    }


def _build_variants(report: dict) -> list[dict[str, Any]]:
    """AbReport always has exactly two variants (A and B) — emit them in that order.

    `is_control=True` is assigned to `a` by A/B convention; AbReport itself does
    not designate a control. If callers know better, they can override post-adapter.
    """
    return [
        {
            "id": "a",
            "label": "Variant A",
            "is_control": True,
            "description": "AbReport variant A (control by convention; AbReport does not designate a control).",
        },
        {
            "id": "b",
            "label": "Variant B",
            "is_control": False,
            "description": "AbReport variant B (treatment by convention).",
        },
    ]


def _build_metrics(report: dict, observed: dict[str, dict[str, list[str]]]) -> dict[str, Any]:
    """Aggregate per-variant metrics across all segments.

    Prefers measured per-persona outcomes (pooled across segments) and falls
    back to preference-share when no outcomes are observed. AbReport carries
    no SUS / SEQ / sentiment fields — those are emitted as null so downstream
    `map_aggregate_metrics` doesn't choke on missing keys.
    """
    pooled_a = [o for seg in observed.values() for o in seg.get("a", [])]
    pooled_b = [o for seg in observed.values() for o in seg.get("b", [])]
    measured_a = _completion_rate(pooled_a)
    measured_b = _completion_rate(pooled_b)

    if measured_a is not None and measured_b is not None:
        a_rate, b_rate, source = measured_a, measured_b, "measured_subsample"
    else:
        persona_split = report.get("persona_split") or []
        total = sum(int(ps.get("persona_count", 0)) for ps in persona_split) or 1
        a_pref = sum(
            int(ps.get("persona_count", 0))
            for ps in persona_split
            if _coerce_variant_tag(ps.get("preferred_variant")) == "a"
        )
        b_pref = sum(
            int(ps.get("persona_count", 0))
            for ps in persona_split
            if _coerce_variant_tag(ps.get("preferred_variant")) == "b"
        )
        a_rate = round(100.0 * a_pref / total, 1)
        b_rate = round(100.0 * b_pref / total, 1)
        source = "preference_proxy"

    return {
        "a": {
            "completion_rate": a_rate,
            "completion_rate_source": source,
            "observed_n": len(pooled_a),
            "sus": None,
            "seq": None,
            "avg_sentiment": None,
            "friction_count": len((report.get("friction_provenance") or {}).get("variant_a") or []),
        },
        "b": {
            "completion_rate": b_rate,
            "completion_rate_source": source,
            "observed_n": len(pooled_b),
            "sus": None,
            "seq": None,
            "avg_sentiment": None,
            "friction_count": len((report.get("friction_provenance") or {}).get("variant_b") or []),
        },
    }


def _segment_metrics_cell(
    measured_outcomes: list[str], preferred: bool | None
) -> tuple[dict[str, Any], str]:
    """Return (cell_dict, source_label) for one segment+variant cell.

    `preferred` is True if this variant is the segment's preferred one,
    False if the OTHER variant is preferred, None if 'neither'.
    """
    measured = _completion_rate(measured_outcomes)
    if measured is not None:
        return (
            {
                "completion_rate": measured,
                "observed_n": len(measured_outcomes),
                "completion_rate_source": "measured_subsample",
                "sus": None,
                "seq": None,
            },
            "measured_subsample",
        )
    if preferred is True:
        return (
            {
                "completion_rate": 100.0,
                "observed_n": 0,
                "completion_rate_source": "preference_proxy",
                "sus": None,
                "seq": None,
            },
            "preference_proxy",
        )
    if preferred is False:
        return (
            {
                "completion_rate": 0.0,
                "observed_n": 0,
                "completion_rate_source": "preference_proxy",
                "sus": None,
                "seq": None,
            },
            "preference_proxy",
        )
    return (
        {
            "completion_rate": None,
            "observed_n": 0,
            "completion_rate_source": "absent",
            "sus": None,
            "seq": None,
        },
        "absent",
    )


def _build_segment_verdicts(
    report: dict, observed: dict[str, dict[str, list[str]]]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, str]]]:
    """One ComparisonData segment_verdict per AbReport persona_split entry.

    Returns (segment_verdicts, per_cell_sources). `per_cell_sources` maps
    `{segment_name: {a: source_label, b: source_label}}` for
    `_extraction_confidence`.
    """
    out: list[dict[str, Any]] = []
    sources: dict[str, dict[str, str]] = {}
    for ps in report.get("persona_split") or []:
        seg_name = ps.get("segment", "unknown")
        winner = _coerce_variant_tag(ps.get("preferred_variant"))
        seg_obs = observed.get(seg_name, {"a": [], "b": []})

        a_cell, a_src = _segment_metrics_cell(
            seg_obs.get("a", []),
            preferred=(winner == "a") if winner else None,
        )
        b_cell, b_src = _segment_metrics_cell(
            seg_obs.get("b", []),
            preferred=(winner == "b") if winner else None,
        )

        out.append({
            "segment_name": seg_name,
            "persona_count": int(ps.get("persona_count", 0)),
            "winner": winner,
            "metrics_by_variant": {"a": a_cell, "b": b_cell},
            "interpretation": ps.get("interpretation", ""),
            "reactions": ps.get("reactions", {}),
        })
        sources[seg_name] = {"a": a_src, "b": b_src}
    return out, sources


def _build_friction_provenance(report: dict) -> list[dict[str, Any]]:
    """Flatten AbReport's per-side friction lists into ComparisonData's
    presence-shaped list."""
    fp = report.get("friction_provenance") or {}
    out: list[dict[str, Any]] = []

    for item in fp.get("variant_a") or []:
        note = item.get("note", "")
        out.append({
            "id": _stable_id("a", item.get("type", ""), note),
            "friction": note,
            "type": item.get("type", "unknown"),
            "severity": item.get("severity", "medium"),
            "screen": "unknown",
            "status": "present_in_a",
            "presence": {"a": "present", "b": "absent"},
            "persona_count": int(item.get("persona_count", 0)),
            "resolved_by": [],
            "introduced_by": ["a"],
        })

    for item in fp.get("variant_b") or []:
        note = item.get("note", "")
        out.append({
            "id": _stable_id("b", item.get("type", ""), note),
            "friction": note,
            "type": item.get("type", "unknown"),
            "severity": item.get("severity", "medium"),
            "screen": "unknown",
            "status": "present_in_b",
            "presence": {"a": "absent", "b": "present"},
            "persona_count": int(item.get("persona_count", 0)),
            "resolved_by": [],
            "introduced_by": ["b"],
        })

    return out


def _build_theme_movement(report: dict) -> dict[str, Any]:
    """Convert monologue_diff[] to theme_movement.persistent[] entries.

    Each MonologueDiff becomes one persistent theme carrying the persona's
    A and B monologues as monologue_evidence.monologues. This preserves the
    citation-extraction path used by `simul2design.ingest.map_citations`.
    """
    persistent = []
    for md in report.get("monologue_diff") or []:
        inflection = md.get("inflection", "")
        persona_name = md.get("persona_name", "unknown_persona")
        persistent.append({
            "id": _stable_id("theme", md.get("persona_id", ""), inflection),
            "name": (inflection[:80] + "…") if len(inflection) > 80 else inflection or "monologue contrast",
            "description": inflection or "AbReport monologue contrast",
            "persona_count": 1,
            "monologue_evidence": {
                "persona_name": persona_name,
                "segment": md.get("segment", "unknown"),
                "monologues": {
                    "a": md.get("variant_a_monologue", ""),
                    "b": md.get("variant_b_monologue", ""),
                },
                "decision": {
                    "a": md.get("decision_a", ""),
                    "b": md.get("decision_b", ""),
                },
            },
        })
    return {"persistent": persistent, "resolved": [], "introduced": []}


def _build_screen_comparison(report: dict) -> list[dict[str, Any]]:
    """Convert annotated_screens.screens[] into ComparisonData.screen_comparison.

    `summaries.{a,b}` is a concatenation of the screen's per-side element
    summaries, which is what the auto-mapper reads to derive taxonomy values.
    """
    screens = (report.get("annotated_screens") or {}).get("screens") or []
    out: list[dict[str, Any]] = []
    for s in screens:
        va = s.get("variant_a", {}) or {}
        vb = s.get("variant_b", {}) or {}
        out.append({
            "screen_name": s.get("screen_label", f"screen_{s.get('index', 0)}"),
            "screen_index": int(s.get("index", 0)),
            "divergence": "unknown",
            "divergence_score": 0,
            "summaries": {
                "a": " | ".join(
                    f"{e.get('label', '')}: {e.get('summary', '')}".strip(": ")
                    for e in (va.get("elements") or [])
                ),
                "b": " | ".join(
                    f"{e.get('label', '')}: {e.get('summary', '')}".strip(": ")
                    for e in (vb.get("elements") or [])
                ),
            },
            "elements": {
                "a": va.get("elements") or [],
                "b": vb.get("elements") or [],
            },
        })
    return out


def _build_persona_journeys(report: dict) -> list[dict[str, Any]]:
    """Convert deep_dive.personas[] into ComparisonData.persona_journeys."""
    deep = (report.get("deep_dive") or {}).get("personas") or []
    out: list[dict[str, Any]] = []
    for p in deep:
        leaning = _coerce_variant_tag((p.get("overall_reflection") or {}).get("leaning")) or ""
        narrative_bits: list[str] = []
        if p.get("behavior_summary"):
            narrative_bits.append(p["behavior_summary"])
        ovr = (p.get("overall_reflection") or {}).get("text", "")
        if ovr:
            narrative_bits.append(ovr)
        out.append({
            "id": p.get("id", _stable_id("persona", p.get("name", ""))),
            "name": p.get("name", "unknown"),
            "archetype": p.get("archetype", ""),
            "segment": p.get("segment", ""),
            "occupation": p.get("occupation", ""),
            "age": p.get("age"),
            "city": p.get("city", ""),
            "income_band": p.get("income_band", ""),
            "tags": p.get("tags") or [],
            "preferred_variant": leaning,
            "narrative": "\n\n".join(narrative_bits),
            "variant_a": p.get("variant_a", {}),
            "variant_b": p.get("variant_b", {}),
        })
    return out


def _build_variant_screenshots(report: dict) -> dict[str, list[str]]:
    """Collect per-variant image_paths from every annotated screen pair."""
    screens = (report.get("annotated_screens") or {}).get("screens") or []
    a_paths: list[str] = []
    b_paths: list[str] = []
    for s in screens:
        a_path = (s.get("variant_a") or {}).get("image_path")
        b_path = (s.get("variant_b") or {}).get("image_path")
        if a_path:
            a_paths.append(a_path)
        if b_path:
            b_paths.append(b_path)
    return {"a": a_paths, "b": b_paths}


def _build_recommendations(report: dict) -> list[dict[str, Any]]:
    """Convert ship_list[] into ComparisonData.recommendations[]."""
    out: list[dict[str, Any]] = []
    for item in report.get("ship_list") or []:
        out.append({
            "id": item.get("id", _stable_id("ship", item.get("feature", ""))),
            "priority": item.get("confidence", "medium"),
            "rice_score": None,
            "recommendation": item.get("bullet") or item.get("feature", ""),
            "rationale": item.get("rationale", ""),
            "action": item.get("action", "keep"),
            "source_variant": _coerce_variant_tag(item.get("source_variant")) or item.get("source_variant", ""),
            "feature": item.get("feature", ""),
            "markdown": item.get("markdown", ""),
        })
    return out


def _build_risks(report: dict) -> list[str]:
    """Extract risks from ship_list items with action='kill'."""
    risks: list[str] = []
    for item in report.get("ship_list") or []:
        if item.get("action") == "kill":
            bullet = item.get("bullet") or item.get("feature", "")
            if bullet:
                risks.append(f"[{item.get('source_variant', '?')}] {bullet}")
    return risks


def _build_verdict(report: dict) -> dict[str, Any] | None:
    v = report.get("verdict")
    if not v:
        return None
    return {"sentence": v.get("sentence", ""), "confidence": v.get("confidence", "")}


def from_ab_report(report: dict, *, client_slug: str | None = None) -> dict[str, Any]:
    """Convert an AbReport dict (e.g. `AbReport.model_dump()`) to a
    ComparisonData-compatible dict.

    Args:
        report: AbReport payload (dict-shaped).
        client_slug: Optional client slug to stamp into metadata.client if
            AbReport.meta.client is empty.

    Returns:
        A dict that `simul2design.schemas.ComparisonData.model_validate(dict)`
        accepts.
    """
    if not isinstance(report, dict):
        raise TypeError(f"from_ab_report() expects a dict, got {type(report).__name__}")
    if "meta" not in report or "annotated_screens" not in report:
        raise ValueError(
            "Input does not look like an AbReport: missing 'meta' and/or "
            "'annotated_screens'. Pass AbReport.model_dump()."
        )

    metadata = _build_metadata(report)
    if client_slug and not metadata.get("client"):
        metadata["client"] = client_slug

    observed = _collect_segment_outcomes(report)
    segment_verdicts, per_cell_sources = _build_segment_verdicts(report, observed)
    metrics = _build_metrics(report, observed)

    comp: dict[str, Any] = {
        "metadata": metadata,
        "variants": _build_variants(report),
        "metrics": metrics,
        "segment_verdicts": segment_verdicts,
        "friction_provenance": _build_friction_provenance(report),
        "variant_screenshots": _build_variant_screenshots(report),
        "theme_movement": _build_theme_movement(report),
        "screen_comparison": _build_screen_comparison(report),
        "persona_journeys": _build_persona_journeys(report),
        "recommendations": _build_recommendations(report),
        "recommended_next_test": None,
        "risks_to_monitor": _build_risks(report),
        "verdict": _build_verdict(report),
    }

    aggregate_source = metrics["a"]["completion_rate_source"]
    comp["_extraction_confidence"] = {
        "_source": SOURCE_NAME,
        "_adapter_version": ADAPTER_VERSION,
        "_adapter_note": ADAPTER_NOTE,
        "metrics.completion_rate": aggregate_source,
        "metrics.sus": "absent_in_source",
        "metrics.seq": "absent_in_source",
        "metrics.avg_sentiment": "absent_in_source",
        "segment_verdicts.metrics_by_variant.completion_rate.cells": per_cell_sources,
        "screen_comparison.divergence_score": "absent_in_source",
        "recommended_next_test": "absent_in_source",
    }

    return comp

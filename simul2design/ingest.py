"""Apriori ComparisonData → element_matrix.json scaffold.

Direct-mappable fields are auto-populated:
- segments (id slugified from name; weight = persona_count / n_total)
- variants[].id (Apriori 'a/b/c' → our 'V1/V2/V3')
- variants[].conversion_by_segment (from segment_verdicts.metrics_by_variant)
- friction_points (re-shaped from friction_provenance + theme_movement persona counts)
- citations (extracted from theme_movement.monologue_evidence)
- aggregate_metrics (sus → sus_score, completion_rate normalized to fraction)
- apriori_recommended_next_test (surfaced as matrix metadata)

Taxonomy fields stay flagged `__needs_review__` for the auto-mapper.
"""

from __future__ import annotations
import argparse
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

NEEDS_REVIEW = "__needs_review__"

# Default mapping from Apriori variant letter codes to our V-numbered IDs.
# Apriori convention: 'control' is baseline; 'a', 'b', 'c', ... are A/B test arms in order.
DEFAULT_VARIANT_LABEL_MAP = {
    "control": "Control",
    "a": "V1", "b": "V2", "c": "V3", "d": "V4", "e": "V5", "f": "V6",
    "g": "V7", "h": "V8", "i": "V9", "j": "V10",
}


# ─── helpers (also re-exported by scripts/ingest-apriori.py) ────────────────

def slugify(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def variant_label(apriori_id: str, label_override: str | None = None) -> str:
    if label_override:
        return label_override
    return DEFAULT_VARIANT_LABEL_MAP.get(apriori_id.lower(), apriori_id.upper())


# ─── core mappers ───────────────────────────────────────────────────────────

def map_segments(comp: dict) -> list[dict]:
    segs = []
    n_total = sum(sv["persona_count"] for sv in comp.get("segment_verdicts", []))
    if n_total == 0:
        n_total = comp.get("metadata", {}).get("persona_count", 0)
    for sv in comp.get("segment_verdicts", []):
        n = sv["persona_count"]
        weight = round(n / n_total, 4) if n_total else 0
        segs.append({
            "id": slugify(sv["segment_name"]),
            "name": sv["segment_name"],
            "n": n,
            "weight": weight,
        })
    return segs


def map_variants(comp: dict) -> tuple[list[dict], dict]:
    id_map = {}
    variants = []
    apriori_variants = comp.get("variants", [])
    seg_id_for_apriori_seg = {sv["segment_name"]: slugify(sv["segment_name"])
                              for sv in comp.get("segment_verdicts", [])}

    for v in apriori_variants:
        ap_id = v["id"]
        our_id = variant_label(ap_id)
        id_map[ap_id] = our_id

        conv_by_seg: dict[str, float | None] = {}
        for sv in comp.get("segment_verdicts", []):
            seg_id = seg_id_for_apriori_seg[sv["segment_name"]]
            metrics = sv.get("metrics_by_variant", {}).get(ap_id, {})
            cr = metrics.get("completion_rate")
            conv_by_seg[seg_id] = (cr / 100.0) if cr is not None else None

        elements = {dim: NEEDS_REVIEW for dim in (
            "layout", "modal_interrupt", "branding", "price_visibility",
            "cta_primary_label", "cta_style", "cta_stack", "urgency_mechanism",
            "refund_or_guarantee_copy", "trust_signal", "evidence_detail",
        )}

        variants.append({
            "id": our_id,
            "apriori_id": ap_id,
            "label_apriori": v.get("label", ""),
            "is_control": v.get("is_control", False),
            "description_from_apriori": v.get("description", ""),
            "elements": elements,
            "conversion_by_segment": conv_by_seg,
        })
    return variants, id_map


def map_friction(comp: dict, id_map: dict) -> list[dict]:
    fps = []
    for fp in comp.get("friction_provenance", []):
        presence = fp.get("presence", {})
        present_variants = [id_map.get(ap_id, ap_id)
                            for ap_id, s in presence.items() if s == "present"]
        fps.append({
            "id": fp.get("id"),
            "summary": fp.get("friction"),
            "screen": fp.get("screen", "unknown"),
            "status": fp.get("status", "unknown"),
            "variants": present_variants,
            "resolved_by": [id_map.get(x, x) for x in fp.get("resolved_by", [])],
            "introduced_by": [id_map.get(x, x) for x in fp.get("introduced_by", [])],
            "presence": {id_map.get(k, k): v for k, v in presence.items()},
        })

    tm = comp.get("theme_movement", {})
    theme_idx_by_id = {}
    for bucket in ("persistent", "resolved", "introduced"):
        for theme in tm.get(bucket, []):
            theme_idx_by_id[theme.get("id")] = theme

    for fp in fps:
        for theme in theme_idx_by_id.values():
            if theme.get("name", "").split(" — ")[0].lower() in (fp["summary"] or "").lower():
                fp["persona_count"] = theme.get("persona_count")
                fp["theme_id"] = theme.get("id")
                break
    return fps


def map_citations(comp: dict, id_map: dict) -> list[dict]:
    cits = []
    tm = comp.get("theme_movement", {})
    for bucket in ("persistent", "resolved", "introduced"):
        for theme in tm.get(bucket, []):
            ev = theme.get("monologue_evidence")
            if not ev or not ev.get("monologues"):
                continue
            persona_name = ev.get("persona_name", "unknown")
            seg_id = slugify(persona_name)
            for ap_vid, quote in (ev.get("monologues") or {}).items():
                cits.append({
                    "segment": seg_id,
                    "variant": id_map.get(ap_vid, ap_vid),
                    "quote": quote,
                    "context": f"{theme.get('name', '?')} ({bucket})",
                    "theme_id": theme.get("id"),
                })
    return cits


def map_aggregate_metrics(comp: dict, id_map: dict) -> dict:
    src = comp.get("metrics", {})
    out: dict[str, dict[str, Any]] = {}
    for ap_vid, m in src.items():
        ours = id_map.get(ap_vid, ap_vid)
        for key in ("sus", "seq", "completion_rate", "avg_sentiment", "friction_count"):
            out.setdefault(key if key != "sus" else "sus_score", {})[ours] = m.get(key)
    if "completion_rate" in out:
        out["completion_rate"] = {k: (v / 100.0 if isinstance(v, (int, float)) and v > 1 else v)
                                  for k, v in out["completion_rate"].items()}
    return out


def map_apriori_next_test(comp: dict) -> dict | None:
    nt = comp.get("recommended_next_test")
    if not nt:
        return None
    return {
        "name": nt.get("name"),
        "hypothesis": nt.get("hypothesis"),
        "predicted_conversion": nt.get("predicted_conversion"),
        "predicted_lift": nt.get("predicted_lift"),
        "_note": "Apriori's V(N+1) hypothesis. Our synthesize skill produces an independent V(N+1) — "
                 "compare and contrast in the final spec.",
    }


# ─── public entry points ────────────────────────────────────────────────────

def build_matrix(comp: dict, client: str, source_path: str = "") -> dict:
    """Build the starter element_matrix.json dict from a ComparisonData dict."""
    segments = map_segments(comp)
    variants, id_map = map_variants(comp)
    friction_points = map_friction(comp, id_map)
    citations = map_citations(comp, id_map)
    aggregate_metrics = map_aggregate_metrics(comp, id_map)
    next_test = map_apriori_next_test(comp)

    return {
        "version": "2.0",
        "client": client,
        "source": {
            "extraction_method": "apriori_comparison_json_adapter_v1",
            "extracted_at": str(date.today()),
            "source_file": source_path,
            "apriori_simulation_id": comp.get("metadata", {}).get("simulation_id"),
            "apriori_simulation_name": comp.get("metadata", {}).get("simulation_name"),
        },
        "taxonomy_base": ".claude/rules/element-taxonomy-base.md",
        "taxonomy_overlay": f".claude/rules/element-taxonomy-{client}.md",
        "n_total": comp.get("metadata", {}).get("persona_count", sum(s["n"] for s in segments)),
        "simulator_provenance": "unknown (apriori.work — underlying LLM not disclosed; flag per "
                                "estimate-conversion methodology)",
        "segments": segments,
        "variants": variants,
        "friction_points": friction_points,
        "citations": citations,
        "aggregate_metrics": aggregate_metrics,
        "apriori_recommended_next_test": next_test,
        "confounds": [],
        "clean_element_contrasts": [],
        "extraction_confidence": {
            "_adapter_note": (
                "Built by simul2design.ingest. Direct-mappable fields fully populated. "
                "Taxonomy fields (variants[].elements.*) are flagged '__needs_review__' — "
                "auto-mapper or human pass required before downstream skills run."
            ),
            "open": [
                "all variants[].elements.* — taxonomy values need to be derived from "
                "comp.screen_comparison.summaries + variant screenshots",
                "confounds[] — requires reasoning over the populated taxonomy",
                "clean_element_contrasts[] — requires diff computation once taxonomy is filled",
            ],
        },
        "flags": [
            f"All taxonomy element values are flagged {NEEDS_REVIEW}; downstream skills must not "
            "consume the matrix until taxonomy is populated.",
            "Simulator LLM is undisclosed by apriori.work; simulator_provenance=unknown downgrades "
            "overall confidence one tier per estimate-conversion methodology.",
        ],
    }


def build_source_md(comp: dict, client: str) -> str:
    """Format a human-readable source.md from the Apriori narrative fields."""
    md = comp.get("metadata", {})
    sim_id = md.get("simulation_id", "unknown")
    sim_name = md.get("simulation_name", "Untitled simulation")
    n = md.get("persona_count", "?")

    lines = [
        f"# Apriori simulation — {client}",
        "",
        f"**Source:** apriori.work (ingested via simul2design)",
        f"**Apriori simulation_id:** {sim_id}",
        f"**Apriori simulation_name:** {sim_name}",
        f"**Extracted:** {date.today()}",
        f"**N:** {n} synthetic personas",
        f"**Variants tested:** {len(comp.get('variants', []))}",
        "",
        "This file is the immutable source of truth. Generated from Apriori's ComparisonData object.",
        "",
        "---",
        "",
        "## 1. Variants",
        "",
    ]

    for v in comp.get("variants", []):
        ap_id = v["id"]
        our_id = variant_label(ap_id)
        lines.append(f"### {our_id} ({v.get('label', '')})")
        lines.append(f"- Apriori id: `{ap_id}`")
        lines.append(f"- Description: {v.get('description', '_(none)_')}")
        lines.append("")

    lines.extend(["---", "", "## 2. Audience segments", "", "| Segment | n | % of total |",
                  "|---|---|---|"])
    n_total = md.get("persona_count", sum(sv["persona_count"] for sv in comp.get("segment_verdicts", [])))
    for sv in comp.get("segment_verdicts", []):
        sn = sv["persona_count"]
        pct = round(sn / n_total * 100) if n_total else 0
        lines.append(f"| {sv['segment_name']} | {sn} | {pct}% |")
    lines.append("")

    lines.extend(["---", "", "## 3. Conversion rates (segment × variant)", ""])
    if comp.get("segment_verdicts"):
        v_ids = [variant_label(v["id"]) for v in comp.get("variants", [])]
        ap_v_ids = [v["id"] for v in comp.get("variants", [])]
        lines.append("| Segment | " + " | ".join(v_ids) + " | Winner |")
        lines.append("|---|" + "---|" * (len(v_ids) + 1))
        for sv in comp.get("segment_verdicts", []):
            row_vals = []
            for ap_id in ap_v_ids:
                cr = sv.get("metrics_by_variant", {}).get(ap_id, {}).get("completion_rate")
                row_vals.append(f"{cr}%" if cr is not None else "—")
            winner_ap = sv.get("winner")
            winner = variant_label(winner_ap) if winner_ap else "?"
            lines.append(f"| {sv['segment_name']} | " + " | ".join(row_vals) + f" | {winner} |")
    lines.append("")

    lines.extend(["---", "", "## 4. Friction points", "",
                  "Apriori's friction_provenance, re-shaped:", ""])
    for fp in comp.get("friction_provenance", []):
        st = fp.get("status", "?")
        present_in = [ap_id for ap_id, p in (fp.get("presence") or {}).items() if p == "present"]
        present_str = ", ".join(variant_label(x) for x in present_in)
        lines.append(f"- **[{st}]** {fp.get('friction', '?')} — present in: {present_str or 'none'}"
                     f" ({fp.get('screen', '?')})")
    lines.append("")

    lines.extend(["---", "", "## 5. Theme movement (Apriori's theme analysis)", ""])
    tm = comp.get("theme_movement", {})
    for bucket_name, bucket_label in (("persistent", "Persistent"),
                                       ("resolved", "Resolved"),
                                       ("introduced", "Introduced")):
        themes = tm.get(bucket_name, [])
        if not themes:
            continue
        lines.append(f"### {bucket_label}")
        for t in themes:
            lines.append(f"- **{t.get('name', '?')}** — {t.get('description', '?')[:300]}"
                         + (f" (n={t.get('persona_count')})" if t.get('persona_count') else ""))
        lines.append("")

    lines.extend(["---", "", "## 6. Per-screen comparison (Apriori's natural-language summaries)", ""])
    for sc in comp.get("screen_comparison", []):
        lines.append(f"### {sc.get('screen_name', '?')} (divergence: {sc.get('divergence', '?')}, "
                     f"score: {sc.get('divergence_score', '?')})")
        for ap_id, summary in (sc.get("summaries") or {}).items():
            lines.append(f"- **{variant_label(ap_id)}:** {summary[:400]}")
        lines.append("")

    lines.extend(["---", "", "## 7. Persona journeys", ""])
    for pj in comp.get("persona_journeys", []):
        lines.append(f"### {pj.get('name', '?')} ({pj.get('archetype', '?')}, "
                     f"prefers {variant_label(pj.get('preferred_variant', '?'))})")
        lines.append(pj.get("narrative", "")[:500])
        lines.append("")

    lines.extend(["---", "", "## 8. Apriori's recommendations", ""])
    for r in comp.get("recommendations", []):
        lines.append(f"- **[{r.get('priority', '?')} | RICE {r.get('rice_score', '?')}]** "
                     f"{r.get('recommendation', '?')}")
        rat = r.get("rationale", "")
        if rat:
            lines.append(f"  - _Rationale:_ {rat[:300]}")
    lines.append("")

    nt = comp.get("recommended_next_test")
    if nt:
        lines.extend(["---", "", "## 9. Apriori's recommended next test", "",
                     f"**{nt.get('name', '?')}**", "",
                     f"- Hypothesis: {nt.get('hypothesis', '?')}",
                     f"- Predicted conversion: {nt.get('predicted_conversion', '?')}",
                     f"- Predicted lift: {nt.get('predicted_lift', '?')}",
                     f"- Estimated effort: {nt.get('estimated_effort', '?')}",
                     "",
                     "Our synthesize skill will produce an independent V(N+1) and the final spec "
                     "will compare both.",
                     ""])

    lines.extend(["---", "", "## 10. Risks Apriori flagged", ""])
    for risk in comp.get("risks_to_monitor", []):
        lines.append(f"- {risk}")
    lines.append("")

    return "\n".join(lines)


def fetch_screenshots(comp: dict, base_url: str, out_dir: Path,
                       dry_run: bool = False) -> list[str]:
    """Download variant_screenshots URLs to out_dir/. Returns list of saved paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    vs = comp.get("variant_screenshots") or {}
    for ap_id, urls in vs.items():
        if isinstance(urls, str):
            urls = [urls]
        for idx, url in enumerate(urls):
            full = url if url.startswith("http") else f"{base_url.rstrip('/')}{url}"
            stem = variant_label(ap_id).lower()
            suffix = f"-{idx + 1}" if len(urls) > 1 else ""
            dest = out_dir / f"{stem}{suffix}.png"
            if dry_run:
                saved.append(f"(would fetch) {full} → {dest}")
                continue
            try:
                with urllib.request.urlopen(full, timeout=15) as resp:
                    dest.write_bytes(resp.read())
                saved.append(str(dest))
            except Exception as e:
                saved.append(f"(failed) {full} — {e!r}")
    return saved


# ─── CLI entry point (also called by scripts/ingest-apriori.py) ──────────────

def _cli_main() -> int:
    """CLI entry — invoked by both `simul2design-ingest` and scripts/ingest-apriori.py."""
    ap = argparse.ArgumentParser(
        description="Ingest Apriori ComparisonData JSON into the synthesis engine pipeline.",
    )
    ap.add_argument("client", help="Client slug (e.g., 'univest')")
    ap.add_argument("--from-comparison-json", required=True,
                    help="Path to ComparisonData JSON exported from Apriori")
    ap.add_argument("--apriori-base-url", default="https://apriori.work",
                    help="Base URL for fetching variant screenshots")
    ap.add_argument("--no-fetch-screenshots", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("-o", "--output-dir", default=None)
    args = ap.parse_args()

    src = Path(args.from_comparison_json)
    if not src.is_file():
        print(f"Error: {src} not found", file=sys.stderr)
        return 1

    try:
        comp = json.loads(src.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: {src} is not valid JSON: {e}", file=sys.stderr)
        return 1

    required = ["metadata", "variants", "metrics", "segment_verdicts",
                "friction_provenance", "variant_screenshots"]
    missing = [k for k in required if k not in comp]
    if missing:
        print(f"Error: ComparisonData missing required fields: {missing}", file=sys.stderr)
        return 1

    out_root = Path(args.output_dir) if args.output_dir else (Path.cwd() / "data" / args.client)
    print(f"Ingesting Apriori ComparisonData for client '{args.client}'")
    print(f"  Input:  {src}")
    print(f"  Output: {out_root}/")
    print(f"  Variants: {len(comp.get('variants', []))} | "
          f"Segments: {len(comp.get('segment_verdicts', []))} | "
          f"Friction points: {len(comp.get('friction_provenance', []))}")
    print()
    if args.dry_run:
        print("(dry-run mode — no files written)")

    matrix = build_matrix(comp, args.client,
                          source_path=str(out_root / "source.md"))

    if not args.dry_run:
        out_root.mkdir(parents=True, exist_ok=True)
        (out_root / "apriori_input.json").write_text(json.dumps(comp, indent=2))
        (out_root / "element_matrix.json").write_text(json.dumps(matrix, indent=2))
        (out_root / "source.md").write_text(build_source_md(comp, args.client))

    saved = []
    if not args.no_fetch_screenshots:
        saved = fetch_screenshots(comp, args.apriori_base_url,
                                   out_root / "source-screenshots", args.dry_run)

    print("Wrote:")
    for f in ("apriori_input.json", "source.md", "element_matrix.json"):
        marker = "(would write)" if args.dry_run else "✓"
        print(f"  {marker}  {out_root / f}")
    if saved:
        print("Screenshots:")
        for s in saved:
            print(f"  · {s}")
    print()
    print("Next steps:")
    print(f"  1. Review element_matrix.json — fill in the {NEEDS_REVIEW} taxonomy fields.")
    print(f"  2. Edit .claude/rules/element-taxonomy-{args.client}.md (client overlay).")
    print(f"  3. Run scripts/sim-flow.py status {args.client} to confirm pipeline state.")
    print(f"  4. Run weigh-segments → synthesize → adversary → estimate-conversion → generate-spec.")
    print(f"  5. scripts/render-report.py {args.client} for the customer-facing HTML report.")
    return 0

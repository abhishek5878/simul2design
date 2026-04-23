#!/usr/bin/env python3
"""
sim-flow — the pipeline equivalent of SETUP.md's session-start ritual.

Run one command, get one screen: where the pipeline is for this client, what's
blocked, what to do next. No state file to desync — introspects the filesystem.

Usage:
    scripts/sim-flow.py status <client-slug>

Exit codes:
    0 — ran successfully, pipeline green (all stages done or acceptably pending)
    1 — input error (unknown client, missing data/ folder)
    2 — pipeline has blockers (adversary flagged, validation fails, etc.)

Design:
- State is derived from files in data/<client>/, never stored separately.
- Every check runs in < 2 seconds.
- Output ends with ONE next-action suggestion (mirrors session-start "pick one phase").
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

# The seven canonical pipeline stages, in order. Each has a "detect" rule that
# inspects the filesystem to tell if it's complete, and an "artifact" path.
STAGES = [
    {
        "name": "parse-simulation",
        "artifact": "element_matrix.json",
        "description": "Ingest simulation → normalized matrix",
    },
    {
        "name": "weigh-segments",
        "artifact": "weighted_scores.json",
        "description": "Classify evidence tier per (dimension, value)",
    },
    {
        "name": "synthesize",
        "artifact": "synthesized_variant.json",
        "description": "Pick V(N+1) element set with citations",
    },
    {
        "name": "adversary",
        "artifact": "adversary_review.json",
        "description": "Structured objections; blind review",
    },
    {
        "name": "estimate-conversion",
        "artifact": "conversion_estimates.json",
        "description": "Wilson CIs + coupled-mechanism discount",
    },
    {
        "name": "generate-spec",
        "artifact": "v5-spec.md",  # generic: looking for any v*-spec.md
        "description": "Buildable spec — engineer deliverable",
        "artifact_glob": "v*-spec.md",
    },
    {
        "name": "visual-design",
        "artifact": "design/",
        "description": "HTML + PNG mockups of the variant",
        "is_dir": True,
    },
]

# ANSI colors (fall back to plain if not a tty)
def color(s: str, code: str) -> str:
    if sys.stdout.isatty():
        return f"\033[{code}m{s}\033[0m"
    return s


GREEN = lambda s: color(s, "32")
YELLOW = lambda s: color(s, "33")
RED = lambda s: color(s, "31")
DIM = lambda s: color(s, "2")
BOLD = lambda s: color(s, "1")


def detect_stage(data_dir: Path, stage: dict) -> tuple[bool, Path | None]:
    """Return (is_complete, artifact_path_or_None)."""
    if stage.get("is_dir"):
        p = data_dir / stage["artifact"]
        if p.is_dir() and any(p.iterdir()):
            return True, p
        return False, None
    if "artifact_glob" in stage:
        matches = sorted(data_dir.glob(stage["artifact_glob"]))
        if matches:
            return True, matches[-1]  # latest version
        return False, None
    p = data_dir / stage["artifact"]
    return p.exists(), p if p.exists() else None


def summarize_adversary(adv: dict) -> str:
    """One-line severity summary for adversary_review.json."""
    s = adv.get("summary", {})
    bl, sf, io = s.get("blockers", 0), s.get("should_fix", 0), s.get("instrument_only", 0)
    rec = s.get("recommendation", "unknown")
    bits = []
    if bl:
        bits.append(RED(f"{bl} blocker{'s' if bl != 1 else ''}"))
    if sf:
        bits.append(YELLOW(f"{sf} should-fix"))
    if io:
        bits.append(DIM(f"{io} instrument"))
    if not bits:
        bits.append(GREEN("clean"))
    return f"{' · '.join(bits)} · recommends: {rec}"


def summarize_synthesis(synth: dict) -> str:
    pred = synth.get("weighted_overall_prediction", {})
    p = pred.get("predicted", {})
    if p:
        low = p.get("low", 0) * 100
        point = p.get("point", 0) * 100
        high = p.get("high", 0) * 100
        conf = pred.get("confidence_grade", "?")
        return f"predicted {point:.1f}% (range {low:.1f}–{high:.1f}%) · confidence: {conf}"
    return "parsed but no weighted_overall_prediction"


def summarize_estimates(est: dict) -> str:
    w = est.get("weighted_overall_estimate", {})
    rev = w.get("estimator_revised_interval", None)
    point = w.get("estimator_revised_point", None)
    if rev and point is not None:
        return f"Wilson-revised {point*100:.1f}% (band {rev[0]*100:.1f}–{rev[1]*100:.1f}%)"
    return "parsed but no revised interval"


def summarize_matrix(m: dict) -> str:
    n_variants = len(m.get("variants", []))
    n_segments = len(m.get("segments", []))
    n_friction = len(m.get("friction_points", []))
    n_flags = len(m.get("flags", []))
    parts = [f"{n_variants} variants", f"{n_segments} segments"]
    if n_friction:
        parts.append(f"{n_friction} friction points")
    if n_flags:
        parts.append(YELLOW(f"{n_flags} flag{'s' if n_flags != 1 else ''}"))
    return " · ".join(parts)


def summarize_weighted(w: dict) -> str:
    s = w.get("dimension_summary", {})
    full = s.get("fully_rankable_with_pts", 0)
    direc = s.get("directionally_rankable_no_pts", 0)
    weak = s.get("weakly_rankable", 0)
    non_inf = s.get("non_informative", 0)
    total = full + direc + weak + non_inf
    return f"{full}/{total} fully rankable · {direc} directional · {weak} weak · {non_inf} non-informative"


def summarize_design(design_dir: Path) -> str:
    pngs = sorted(design_dir.glob("*.png"))
    if not pngs:
        return "no PNGs rendered"
    return f"{len(pngs)} mockup{'s' if len(pngs) != 1 else ''}: {', '.join(p.stem for p in pngs)}"


def validate_math(data_dir: Path) -> list[str]:
    """Quick sanity: synthesize's weighted_overall reproduces from per_segment_prediction."""
    synth_path = data_dir / "synthesized_variant.json"
    if not synth_path.exists():
        return []
    try:
        synth = json.loads(synth_path.read_text())
    except json.JSONDecodeError:
        return [f"{synth_path} is not valid JSON"]
    w = synth.get("audience_weights_used", {})
    preds = synth.get("per_segment_prediction", {})
    stated = synth.get("weighted_overall_prediction", {}).get("predicted", {})
    issues = []
    for tier in ("low", "point", "high"):
        if tier not in stated:
            continue
        try:
            computed = sum(preds[sid]["predicted_conversion"][tier] * w[sid] for sid in w)
        except (KeyError, TypeError):
            continue
        if abs(computed - stated[tier]) > 0.002:
            issues.append(
                f"weighted_overall.{tier}: computed {computed:.3f} vs stated {stated[tier]:.3f}"
            )
    return issues


def print_comparison_summary(cmp: dict) -> None:
    """One-screen comparison of predicted vs actual per segment + weighted overall."""
    overall = cmp.get("weighted_overall", {})
    predicted_point = overall.get("predicted_point")
    actual = overall.get("actual")
    in_band = overall.get("actual_within_predicted_band")
    delta_pts = overall.get("delta_pts")

    if predicted_point is not None and actual is not None:
        band = overall.get("predicted_interval") or []
        band_str = f" (band {band[0]*100:.1f}%–{band[1]*100:.1f}%)" if band else ""
        marker = GREEN("✓") if in_band else RED("✗")
        print(f"  [{marker}] weighted overall: predicted {predicted_point*100:.1f}%{band_str}, actual {actual*100:.1f}% · delta {delta_pts:+.1f}pt")

    per_seg = cmp.get("per_segment", {})
    if per_seg:
        for sid, row in per_seg.items():
            p = row.get("predicted_point")
            a = row.get("actual")
            in_band_s = row.get("actual_within_predicted_band")
            if p is None or a is None:
                continue
            m = GREEN("✓") if in_band_s else YELLOW("!")
            dp = (a - p) * 100
            print(f"       {m} {sid}: predicted {p*100:.1f}% / actual {a*100:.1f}% ({dp:+.1f}pt)")

    calibration_signal = cmp.get("calibration_signal", {})
    if calibration_signal:
        bias = calibration_signal.get("weighted_point_bias_pts")
        if bias is not None:
            direction = "over-predicted" if bias > 0 else "under-predicted"
            print(DIM(f"       · calibration signal: synthesize {direction} by {abs(bias):.1f}pt on weighted overall"))


def suggest_next(data_dir: Path, stage_states: list[dict]) -> str:
    """One-line suggestion: what to do next."""
    # First incomplete stage
    next_incomplete = next((s for s in stage_states if not s["complete"]), None)

    # Post-ship evaluator not scaffolded?
    evaluator = data_dir / "evaluator"
    has_actuals = (evaluator / "actual.json").exists() if evaluator.is_dir() else False

    # Adversary recommendation
    adv_path = data_dir / "adversary_review.json"
    adv_rec = None
    if adv_path.exists():
        try:
            adv = json.loads(adv_path.read_text())
            adv_rec = adv.get("summary", {}).get("recommendation")
        except json.JSONDecodeError:
            pass

    if next_incomplete:
        return (
            f"Run the `{next_incomplete['name']}` skill next. "
            f"Input: previous stage's artifact. "
            f"Output: {next_incomplete['artifact']}."
        )

    # All stages complete. Next action depends on adversary + actuals state.
    if adv_rec == "revise_synthesis":
        return (
            "Adversary requires a synthesize revision pass. Re-run synthesize with blockers "
            "addressed, then re-run adversary. Expected to converge in one iteration."
        )
    if adv_rec == "revise_with_conditions":
        return (
            "Adversary approved with operational conditions. The spec encodes them as "
            "Operational Preconditions. Next: client sign-off on preconditions → ship → "
            "record actuals via `sim-flow record-actuals` (not yet implemented)."
        )
    if not has_actuals:
        return (
            "Pipeline is design-complete. Next: either (a) ship and record post-ship "
            "actuals to data/<client>/evaluator/actual.json, or (b) onboard a second "
            "client to validate genericity."
        )
    return "Pipeline + actuals complete. Next: weekly self-edit ritual (see .claude/self-edit/weekly-ritual.md)."


def cmd_status(client: str) -> int:
    data_dir = ROOT / "data" / client
    if not data_dir.is_dir():
        print(f"Error: data/{client}/ does not exist", file=sys.stderr)
        print(f"       To start a new client, create data/{client}/source.md first.", file=sys.stderr)
        return 1

    print(BOLD(f"=== sim-flow: {client} ==="))
    print()

    # Source file
    sources = sorted(data_dir.glob("source*.md"))
    if sources:
        latest = sources[-1]
        size_kb = latest.stat().st_size // 1024
        print(f"Source:  {GREEN('✓')} {latest.relative_to(ROOT)} ({size_kb}KB)")
        if len(sources) > 1:
            print(DIM(f"         · {len(sources)} source versions (immutable once written)"))
    else:
        print(f"Source:  {RED('✗')} no source*.md in {data_dir}")
        print()
        print(f"Next: drop the simulation source at {data_dir}/source.md or use `scripts/refetch-source.sh`.")
        return 2
    print()

    # Stage status
    print(BOLD("Pipeline:"))
    stage_states = []
    for stage in STAGES:
        complete, path = detect_stage(data_dir, stage)
        marker = GREEN("✓") if complete else DIM("·")
        rel = str(path.relative_to(ROOT)) if path else f"(no {stage['artifact']})"
        summary = ""

        # Enrich with parsed content where useful
        if complete and path and path.is_file() and path.suffix == ".json":
            try:
                d = json.loads(path.read_text())
                if stage["name"] == "parse-simulation":
                    summary = " · " + summarize_matrix(d)
                elif stage["name"] == "weigh-segments":
                    summary = " · " + summarize_weighted(d)
                elif stage["name"] == "synthesize":
                    summary = " · " + summarize_synthesis(d)
                elif stage["name"] == "adversary":
                    summary = " · " + summarize_adversary(d)
                elif stage["name"] == "estimate-conversion":
                    summary = " · " + summarize_estimates(d)
            except json.JSONDecodeError:
                summary = " · " + RED("[JSON parse error]")
        elif complete and stage["name"] == "visual-design":
            summary = " · " + summarize_design(path)

        print(f"  [{marker}] {stage['name']:20s} {DIM(rel)}{summary}")
        stage_states.append({"name": stage["name"], "complete": complete, "path": path})
    print()

    # Post-ship evaluator (the immutable one)
    evaluator = data_dir / "evaluator"
    actual_path = evaluator / "actual.json"
    predicted_path = evaluator / "predicted.json"
    comparison_path = evaluator / "comparison.json"

    if actual_path.exists():
        print(BOLD("Post-ship evaluator:"))
        if not predicted_path.exists():
            print(f"  {RED('✗')} actual.json exists but predicted.json missing — re-run record-actuals")
        elif not comparison_path.exists():
            print(f"  {YELLOW('!')} actuals recorded, comparison not yet computed — re-run record-actuals")
        else:
            try:
                cmp = json.loads(comparison_path.read_text())
                print_comparison_summary(cmp)
            except json.JSONDecodeError:
                print(f"  {RED('✗')} comparison.json is not valid JSON")
        print()
    else:
        print(DIM(f"Post-ship:  [·] no {evaluator.relative_to(ROOT)}/actual.json yet — ship + record via `sim-flow record-actuals <client> <file>`"))
        print()

    # Blockers from adversary
    adv_path = data_dir / "adversary_review.json"
    if adv_path.exists():
        try:
            adv = json.loads(adv_path.read_text())
            blockers = [o for o in adv.get("objections", []) if o.get("severity") == "blocker"]
            if blockers:
                print(BOLD(RED(f"Blockers ({len(blockers)}):")))
                for b in blockers:
                    targets = b.get("targets", "?")
                    if isinstance(targets, list):
                        targets = ", ".join(targets)
                    obj_id = b.get("id", "?")
                    summary = (b.get("suggested_revision") or "").split(".")[0][:100]
                    print(f"  {RED('!')} {obj_id} [{targets}]: {summary}")
                print()
        except json.JSONDecodeError:
            pass

    # Flags from matrix
    matrix_path = data_dir / "element_matrix.json"
    if matrix_path.exists():
        try:
            m = json.loads(matrix_path.read_text())
            flags = m.get("flags", [])
            if flags:
                print(BOLD(YELLOW(f"Matrix flags ({len(flags)}):")))
                for f in flags[:3]:  # cap at 3
                    snippet = f[:110] + ("…" if len(f) > 110 else "")
                    print(f"  {YELLOW('!')} {snippet}")
                if len(flags) > 3:
                    print(DIM(f"  … and {len(flags)-3} more (see {matrix_path.relative_to(ROOT)})"))
                print()
        except json.JSONDecodeError:
            pass

    # Validation
    issues = validate_math(data_dir)
    if issues:
        print(BOLD(RED("Validation:")))
        for i in issues:
            print(f"  {RED('✗')} {i}")
        print()
    else:
        if (data_dir / "synthesized_variant.json").exists():
            print(f"Validation: {GREEN('✓')} weighted-overall math reproduces from per-segment predictions")
            print()

    # The session-start ritual's "pick one phase" equivalent
    print(BOLD("Next action:"))
    print(f"  → {suggest_next(data_dir, stage_states)}")
    print()

    # Exit code
    all_complete = all(s["complete"] for s in stage_states)
    has_blockers = bool(adv_path.exists() and json.loads(adv_path.read_text()).get("summary", {}).get("blockers", 0))
    if issues:
        return 2
    return 0 if all_complete and not has_blockers else (2 if has_blockers else 0)


def cmd_record_actuals(client: str, actuals_file: str) -> int:
    """
    Record post-ship actuals for a client. Freezes predictions at ship time into an
    immutable snapshot (predicted.json), stores the reported actuals (actual.json),
    and computes the delta (comparison.json). This is the evaluator loop's entry
    point — predicted never changes after first recording.

    Expected actuals file format (minimal JSON):
    {
      "variant": "V5",
      "weighted_overall_actual": 0.47,
      "per_segment_actual": {
        "skeptical_investor": 0.28,
        "curious_beginner":   0.39,
        ...
      },
      "cohort_size": 2500,
      "observed_over": "first 2000 activations",
      "notes": "optional"
    }
    """
    data_dir = ROOT / "data" / client
    if not data_dir.is_dir():
        print(f"Error: data/{client}/ does not exist", file=sys.stderr)
        return 1

    estimates_path = data_dir / "conversion_estimates.json"
    if not estimates_path.exists():
        print(f"Error: {estimates_path} does not exist — cannot freeze predictions", file=sys.stderr)
        print("       Run the full pipeline through estimate-conversion first.", file=sys.stderr)
        return 1

    actuals_path = Path(actuals_file)
    if not actuals_path.exists():
        print(f"Error: {actuals_file} does not exist", file=sys.stderr)
        return 1

    try:
        actuals = json.loads(actuals_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: {actuals_file} is not valid JSON: {e}", file=sys.stderr)
        return 1

    evaluator = data_dir / "evaluator"
    evaluator.mkdir(exist_ok=True)
    predicted_path = evaluator / "predicted.json"
    actual_out = evaluator / "actual.json"
    comparison_out = evaluator / "comparison.json"

    # Immutable predicted snapshot: freeze at first record. Never overwrite.
    estimates = json.loads(estimates_path.read_text())
    if predicted_path.exists():
        # Load the existing snapshot — it is the source of truth for what we predicted
        # when this client shipped. estimate-conversion may have been re-run since;
        # predicted.json does NOT update.
        frozen = json.loads(predicted_path.read_text())
        if "_frozen_at" not in frozen:
            print(f"Warning: {predicted_path} exists but has no _frozen_at marker. Treating as frozen.", file=sys.stderr)
    else:
        import datetime
        frozen = {
            "_frozen_at": datetime.datetime.now().astimezone().isoformat(),
            "_source_at_freeze": str(estimates_path.relative_to(ROOT)),
            "_note": "Immutable snapshot of estimate-conversion output at ship time. NEVER edit. The predicted-vs-actual delta is the evaluator loop's only input.",
            **estimates,
        }
        predicted_path.write_text(json.dumps(frozen, indent=2))
        print(f"Froze predictions → {predicted_path.relative_to(ROOT)}")

    # Actuals: record as-is but add metadata.
    import datetime
    actual_record = {
        "_recorded_at": datetime.datetime.now().astimezone().isoformat(),
        "_source_file": str(actuals_path),
        **actuals,
    }
    actual_out.write_text(json.dumps(actual_record, indent=2))
    print(f"Recorded actuals → {actual_out.relative_to(ROOT)}")

    # Comparison: derive delta per segment + weighted overall.
    comparison = compute_comparison(frozen, actuals)
    comparison_out.write_text(json.dumps(comparison, indent=2))
    print(f"Computed comparison → {comparison_out.relative_to(ROOT)}")
    print()
    print(BOLD("Summary:"))
    print_comparison_summary(comparison)
    print()
    print("Now run `sim-flow status %s` to see the full picture." % client)
    return 0


def compute_comparison(frozen_predicted: dict, actuals: dict) -> dict:
    """Compute per-segment and weighted-overall delta: actual - predicted."""
    per_segment = {}
    pred_per_seg = frozen_predicted.get("per_segment_estimate", {})
    act_per_seg = actuals.get("per_segment_actual", {})

    for sid, p in pred_per_seg.items():
        point = p.get("estimator_revised_point") or p.get("synthesize_predicted_point")
        interval = p.get("estimator_revised_interval") or p.get("synthesize_predicted_interval")
        actual = act_per_seg.get(sid)
        if point is None or actual is None or interval is None:
            continue
        in_band = interval[0] <= actual <= interval[1]
        per_segment[sid] = {
            "predicted_point": point,
            "predicted_interval": interval,
            "actual": actual,
            "delta_pts": round((actual - point) * 100, 2),
            "actual_within_predicted_band": in_band,
        }

    overall_pred = frozen_predicted.get("weighted_overall_estimate", {})
    overall_point = overall_pred.get("estimator_revised_point")
    overall_interval = overall_pred.get("estimator_revised_interval")
    actual_overall = actuals.get("weighted_overall_actual")

    weighted_overall = {}
    if overall_point is not None and actual_overall is not None and overall_interval is not None:
        weighted_overall = {
            "predicted_point": overall_point,
            "predicted_interval": overall_interval,
            "actual": actual_overall,
            "delta_pts": round((actual_overall - overall_point) * 100, 2),
            "actual_within_predicted_band": overall_interval[0] <= actual_overall <= overall_interval[1],
        }

    calibration_signal = {}
    if weighted_overall:
        calibration_signal["weighted_point_bias_pts"] = round(
            (weighted_overall["predicted_point"] - weighted_overall["actual"]) * 100, 2
        )
    if per_segment:
        biases = [(p["predicted_point"] - p["actual"]) * 100 for p in per_segment.values()]
        calibration_signal["mean_segment_bias_pts"] = round(sum(biases) / len(biases), 2)
        in_band_count = sum(1 for p in per_segment.values() if p["actual_within_predicted_band"])
        calibration_signal["segments_within_band"] = f"{in_band_count}/{len(per_segment)}"

    import datetime
    return {
        "_computed_at": datetime.datetime.now().astimezone().isoformat(),
        "_note": "Derived from evaluator/predicted.json + evaluator/actual.json. Can be recomputed; do not hand-edit.",
        "per_segment": per_segment,
        "weighted_overall": weighted_overall,
        "calibration_signal": calibration_signal,
    }


def cmd_list() -> int:
    """List every client folder under data/."""
    data_root = ROOT / "data"
    if not data_root.is_dir():
        print("No data/ directory yet.")
        return 1
    clients = sorted(d.name for d in data_root.iterdir() if d.is_dir())
    if not clients:
        print("No clients yet. Create data/<slug>/source.md to start one.")
        return 0
    print(BOLD("Clients:"))
    for c in clients:
        print(f"  · {c}")
    print()
    print(DIM("Run `sim-flow status <slug>` for any client's pipeline state."))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="sim-flow — session-start-style dashboard for the synthesis pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Takes inspiration from SETUP.md's session-start ritual:\n"
            "  state-aware, narrowly-scoped, plan-before-execute, iterate once.\n\n"
            "Examples:\n"
            "  scripts/sim-flow.py list\n"
            "  scripts/sim-flow.py status univest"
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    st = sub.add_parser("status", help="show pipeline state for one client")
    st.add_argument("client", help="client slug (e.g., univest)")
    sub.add_parser("list", help="list all known clients")
    ra = sub.add_parser("record-actuals", help="record post-ship actuals for a client (freezes predictions + computes delta)")
    ra.add_argument("client", help="client slug")
    ra.add_argument("actuals_file", help="path to JSON file with actuals — see --help-schema")

    args = parser.parse_args()
    if args.cmd == "status":
        return cmd_status(args.client)
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "record-actuals":
        return cmd_record_actuals(args.client, args.actuals_file)
    return 2


if __name__ == "__main__":
    sys.exit(main())

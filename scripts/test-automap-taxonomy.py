#!/usr/bin/env python3
"""
test-automap-taxonomy.py — test suite for scripts/automap-taxonomy.py.

Runs unit tests on rule helpers, integration tests on the synthetic + real-univest
fixtures, and validates that automap output achieves ≥70% match against the
hand-built v2 univest matrix.

Usage:
    scripts/test-automap-taxonomy.py
"""

from __future__ import annotations
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "scripts" / "ingest-apriori.py"
AUTOMAP = ROOT / "scripts" / "automap-taxonomy.py"
FIXTURE_SIMPLE = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-example.json"
FIXTURE_UNIVEST = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
HANDBUILT_UNIVEST = ROOT / "data" / "univest" / "element_matrix.json"

TMP_BASE = Path("/tmp/test-automap")

# Coverage threshold targets — these encode the realistic rule-based ceiling.
# If the threshold is missed, regression has occurred OR the rules have improved
# (in which case bump the threshold up).
MIN_OVERALL_MATCH_PCT = 70.0
MIN_HIGH_CONF_MATCH_PCT = 80.0
MIN_AUTOMAP_COVERAGE_PCT = 95.0  # cells filled in (high or low_default)

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


def import_automap():
    spec = importlib.util.spec_from_file_location("automap_taxonomy", AUTOMAP)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_tmp_dir(name: str) -> Path:
    p = TMP_BASE / name
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


def ingest(fixture: Path, out_dir: Path) -> int:
    result = subprocess.run(
        [sys.executable, str(ADAPTER), "x",
         "--from-comparison-json", str(fixture),
         "--no-fetch-screenshots", "-o", str(out_dir)],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode


def run_automap(out_dir: Path) -> tuple[int, str, str]:
    result = subprocess.run(
        [sys.executable, str(AUTOMAP), "x", "-o", str(out_dir)],
        capture_output=True, text=True, timeout=20,
    )
    return result.returncode, result.stdout, result.stderr


# ─── unit tests ─────────────────────────────────────────────────────────────

def test_helper_extract_cta_label_imperative():
    """extract_cta_label prefers imperative-prefixed labels."""
    mod = import_automap()
    assert mod.extract_cta_label("'Start Trial Now' button") == "Start Trial Now"
    assert mod.extract_cta_label("the 'Activate for ₹1' CTA") == "Activate for ₹1"
    assert mod.extract_cta_label("see 'Unlock FREE trade →' as the outline button") == "Unlock FREE trade →"


def test_helper_extract_cta_label_rejects_brand():
    """extract_cta_label rejects brand strings like 'India's Trusted Advisory'."""
    mod = import_automap()
    text = "shows 'India's Trusted Advisory' header above 'Start Trial Now' button"
    label = mod.extract_cta_label(text)
    assert label == "Start Trial Now", f"got: {label!r}"


def test_helper_extract_cta_label_rejects_banner():
    """extract_cta_label rejects banner-copy with '&' / '/'."""
    mod = import_automap()
    text = "'Activate @ ₹1 & get instant refund' banner above 'Unlock FREE trade' button"
    label = mod.extract_cta_label(text)
    assert label == "Unlock FREE trade", f"got: {label!r}"


def test_helper_map_cell_high_confidence():
    """map_cell returns high confidence when a pattern matches."""
    mod = import_automap()
    rules = [("a", [r"foo"]), ("b", [r"bar"]), ("c", [])]
    assert mod.map_cell("there is foo here", "x", rules) == ("a", "high", r"foo")


def test_helper_map_cell_low_default():
    """map_cell falls back to low_default when no patterns match."""
    mod = import_automap()
    rules = [("a", [r"foo"]), ("b", [r"bar"]), ("none", [])]  # default 'none'
    assert mod.map_cell("nothing here", "x", rules) == ("none", "low_default", None)


def test_helper_map_cell_needs_review():
    """map_cell returns needs_review when no match and no default."""
    mod = import_automap()
    rules = [("a", [r"foo"]), ("b", [r"bar"])]  # no default
    val, conf, _ = mod.map_cell("nothing here", "x", rules)
    assert val is None and conf == "needs_review"


def test_helper_derive_inferences_modal_resolved():
    """_derive_inferences emits INFER_NO_MODAL + INFER_FULL_SCREEN when modal friction is resolved."""
    mod = import_automap()
    apriori = {
        "friction_provenance": [{
            "id": "f1", "friction": "Modal interrupts before value preview",
            "resolved_by": ["a"], "presence": {"a": "absent"}
        }],
        "screen_comparison": [], "variants": [], "theme_movement": {},
    }
    out = mod._derive_inferences(apriori, "a")
    assert "INFER_NO_MODAL" in out
    assert "INFER_FULL_SCREEN" in out


def test_helper_derive_inferences_named_with_negation():
    """_derive_inferences does NOT set INFER_HAS_NAMED_WINS when stocks appear in negation context."""
    mod = import_automap()
    apriori = {
        "friction_provenance": [], "theme_movement": {},
        "variants": [{"id": "b", "description": "no concrete past wins"}],
        "screen_comparison": [{"summaries": {"b": "stripped TMPV/ZOMATO from V1's carousel; no named wins"}}],
    }
    out = mod._derive_inferences(apriori, "b")
    assert "INFER_HAS_NAMED_WINS" not in out, f"named wins set despite negation; got: {out}"


def test_helper_derive_inferences_aggregate_plus_named():
    """_derive_inferences sets INFER_AGGREGATE_PLUS_NAMED when both aggregate AND named present."""
    mod = import_automap()
    apriori = {
        "friction_provenance": [], "theme_movement": {},
        "variants": [{"id": "a", "description": "Recent Wins carousel + 84.7% accuracy"}],
        "screen_comparison": [{"summaries": {
            "a": "84.7% all-time accuracy. ZOMATO +₹23,435 in 3 days carousel."
        }}],
    }
    out = mod._derive_inferences(apriori, "a")
    assert "INFER_AGGREGATE_PLUS_NAMED" in out


# ─── integration tests ──────────────────────────────────────────────────────

def test_simple_fixture_full_run():
    """End-to-end automap on synthetic 'fixturo' fixture writes valid output."""
    out_dir = make_tmp_dir("simple")
    rc = ingest(FIXTURE_SIMPLE, out_dir)
    assert rc == 0
    rc, stdout, stderr = run_automap(out_dir)
    assert rc == 0, f"stderr: {stderr}"
    assert "Auto-mapped" in stdout
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    assert len(matrix["variants"]) == 3
    # Verify some cells are non-sentinel
    n_filled = sum(1 for v in matrix["variants"] for val in v["elements"].values()
                   if val != "__needs_review__")
    assert n_filled > 0, "no cells were auto-mapped"


def test_simple_fixture_writes_trace():
    """automap writes automap-trace.json with per-cell confidence."""
    out_dir = make_tmp_dir("simple-trace")
    ingest(FIXTURE_SIMPLE, out_dir)
    run_automap(out_dir)
    trace_path = out_dir / "automap-trace.json"
    assert trace_path.is_file()
    trace = json.loads(trace_path.read_text())
    assert "_summary" in trace
    assert "per_variant" in trace
    assert set(trace["_summary"].keys()) == {"high", "low_default", "needs_review", "total"}


def test_dry_run_writes_nothing():
    """--dry-run reports without writing files."""
    out_dir = make_tmp_dir("dry-run")
    ingest(FIXTURE_SIMPLE, out_dir)
    matrix_before = (out_dir / "element_matrix.json").read_text()

    result = subprocess.run(
        [sys.executable, str(AUTOMAP), "x", "-o", str(out_dir), "--dry-run"],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 0
    assert "(dry-run mode" in result.stdout

    matrix_after = (out_dir / "element_matrix.json").read_text()
    assert matrix_before == matrix_after, "dry-run modified the matrix"
    assert not (out_dir / "automap-trace.json").exists()


def test_missing_inputs_errors():
    """Adapter exits 1 if matrix or apriori_input.json missing."""
    out_dir = make_tmp_dir("missing-inputs")
    result = subprocess.run(
        [sys.executable, str(AUTOMAP), "nonexistent", "-o", str(out_dir)],
        capture_output=True, text=True, timeout=20,
    )
    assert result.returncode == 1


# ─── real-data validation tests ─────────────────────────────────────────────

def test_univest_full_run():
    """End-to-end automap on real univest fixture exits 0."""
    out_dir = make_tmp_dir("univest")
    rc = ingest(FIXTURE_UNIVEST, out_dir)
    assert rc == 0
    rc, stdout, _ = run_automap(out_dir)
    assert rc == 0
    assert "Auto-mapped" in stdout


def test_univest_coverage_threshold():
    """Automap fills in ≥95% of cells (high or low_default) on univest fixture."""
    out_dir = make_tmp_dir("univest-cov")
    ingest(FIXTURE_UNIVEST, out_dir)
    run_automap(out_dir)
    trace = json.loads((out_dir / "automap-trace.json").read_text())
    s = trace["_summary"]
    filled = s["high"] + s["low_default"]
    pct = 100 * filled / s["total"]
    assert pct >= MIN_AUTOMAP_COVERAGE_PCT, (
        f"coverage {pct:.1f}% below threshold {MIN_AUTOMAP_COVERAGE_PCT}% "
        f"(high={s['high']}, low_default={s['low_default']}, needs_review={s['needs_review']})"
    )


def test_univest_match_against_handbuilt():
    """Automap output matches ≥70% of cells against hand-built v2 univest matrix."""
    if not HANDBUILT_UNIVEST.exists():
        return  # Skip if hand-built not yet committed
    out_dir = make_tmp_dir("univest-match")
    ingest(FIXTURE_UNIVEST, out_dir)
    run_automap(out_dir)
    auto = json.loads((out_dir / "element_matrix.json").read_text())
    hand = json.loads(HANDBUILT_UNIVEST.read_text())

    dims = ["layout", "modal_interrupt", "branding", "price_visibility",
            "cta_primary_label", "cta_style", "cta_stack", "urgency_mechanism",
            "refund_or_guarantee_copy", "trust_signal", "evidence_detail"]
    auto_by_id = {v["id"]: v["elements"] for v in auto["variants"]}
    hand_by_id = {v["id"]: v["elements"] for v in hand["variants"]}

    total = match = 0
    for vid in ["Control", "V1", "V2", "V3", "V4"]:
        a, h = auto_by_id[vid], hand_by_id[vid]
        for dim in dims:
            av, hv = a.get(dim), h.get(dim)
            # Case-insensitive + arrow-tolerant comparison for cta_primary_label
            if dim == "cta_primary_label" and isinstance(av, str) and isinstance(hv, str):
                is_match = av.lower().rstrip(" →").strip() == hv.lower().rstrip(" →").strip()
            else:
                is_match = av == hv
            if is_match:
                match += 1
            total += 1

    pct = 100 * match / total
    assert pct >= MIN_OVERALL_MATCH_PCT, (
        f"match rate {pct:.1f}% below threshold {MIN_OVERALL_MATCH_PCT}% "
        f"({match}/{total} cells)"
    )


def test_univest_high_confidence_match_threshold():
    """High-confidence (non-default) auto-mapped cells match ≥80% against hand-built."""
    if not HANDBUILT_UNIVEST.exists():
        return
    out_dir = make_tmp_dir("univest-conf")
    ingest(FIXTURE_UNIVEST, out_dir)
    run_automap(out_dir)
    auto = json.loads((out_dir / "element_matrix.json").read_text())
    hand = json.loads(HANDBUILT_UNIVEST.read_text())
    trace = json.loads((out_dir / "automap-trace.json").read_text())

    dims = ["layout", "modal_interrupt", "branding", "price_visibility",
            "cta_primary_label", "cta_style", "cta_stack", "urgency_mechanism",
            "refund_or_guarantee_copy", "trust_signal", "evidence_detail"]
    auto_by_id = {v["id"]: v["elements"] for v in auto["variants"]}
    hand_by_id = {v["id"]: v["elements"] for v in hand["variants"]}

    total_high = match_high = 0
    for vid in ["Control", "V1", "V2", "V3", "V4"]:
        a, h = auto_by_id[vid], hand_by_id[vid]
        for dim in dims:
            conf = trace["per_variant"].get(vid, {}).get(dim, {}).get("confidence")
            if conf != "high":
                continue
            av, hv = a.get(dim), h.get(dim)
            if dim == "cta_primary_label" and isinstance(av, str) and isinstance(hv, str):
                is_match = av.lower().rstrip(" →").strip() == hv.lower().rstrip(" →").strip()
            else:
                is_match = av == hv
            total_high += 1
            if is_match:
                match_high += 1

    pct = 100 * match_high / total_high if total_high else 0
    assert pct >= MIN_HIGH_CONF_MATCH_PCT, (
        f"high-confidence match {pct:.1f}% below threshold {MIN_HIGH_CONF_MATCH_PCT}% "
        f"({match_high}/{total_high})"
    )


def test_univest_segments_unchanged_by_automap():
    """Automap doesn't touch segments / conversion_by_segment / friction_points (only elements)."""
    out_dir = make_tmp_dir("univest-untouched")
    ingest(FIXTURE_UNIVEST, out_dir)
    matrix_before = json.loads((out_dir / "element_matrix.json").read_text())
    run_automap(out_dir)
    matrix_after = json.loads((out_dir / "element_matrix.json").read_text())

    assert matrix_after["segments"] == matrix_before["segments"]
    for v_after, v_before in zip(matrix_after["variants"], matrix_before["variants"]):
        assert v_after["conversion_by_segment"] == v_before["conversion_by_segment"]
    assert matrix_after["friction_points"] == matrix_before["friction_points"]
    assert matrix_after["aggregate_metrics"] == matrix_before["aggregate_metrics"]


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    # Unit (8)
    test_helper_extract_cta_label_imperative,
    test_helper_extract_cta_label_rejects_brand,
    test_helper_extract_cta_label_rejects_banner,
    test_helper_map_cell_high_confidence,
    test_helper_map_cell_low_default,
    test_helper_map_cell_needs_review,
    test_helper_derive_inferences_modal_resolved,
    test_helper_derive_inferences_named_with_negation,
    test_helper_derive_inferences_aggregate_plus_named,
    # Integration (4)
    test_simple_fixture_full_run,
    test_simple_fixture_writes_trace,
    test_dry_run_writes_nothing,
    test_missing_inputs_errors,
    # Real-data (5)
    test_univest_full_run,
    test_univest_coverage_threshold,
    test_univest_match_against_handbuilt,
    test_univest_high_confidence_match_threshold,
    test_univest_segments_unchanged_by_automap,
]


def main() -> int:
    if not AUTOMAP.is_file() or not ADAPTER.is_file():
        print("Error: AUTOMAP or ADAPTER script missing", file=sys.stderr)
        return 1

    print(f"Running {len(TESTS)} tests against {AUTOMAP.name}...\n")
    passed, failed = [], []
    for t in TESTS:
        name = t.__name__
        try:
            t()
            passed.append(name)
            print(f"  {GREEN}✓{RESET} {name}")
        except AssertionError as e:
            failed.append((name, str(e)))
            print(f"  {RED}✗{RESET} {name}{DIM} — {e}{RESET}")
        except Exception as e:
            failed.append((name, f"{type(e).__name__}: {e}"))
            print(f"  {RED}✗{RESET} {name}{DIM} — {type(e).__name__}: {e}{RESET}")

    if TMP_BASE.exists():
        shutil.rmtree(TMP_BASE)

    print()
    print(f"{GREEN}Passed:{RESET} {len(passed)}/{len(TESTS)}")
    if failed:
        print(f"{RED}Failed:{RESET} {len(failed)}")
        return 1
    print(f"{GREEN}All tests passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
test-ingest-apriori.py — test suite for scripts/ingest-apriori.py.

Runs unit, integration, edge-case, and real-data validation tests.
Exits 0 if all pass, 1 if any fail.

Usage:
    scripts/test-ingest-apriori.py            # run all tests
    scripts/test-ingest-apriori.py -v         # verbose (print test bodies on fail)
"""

from __future__ import annotations
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ADAPTER = ROOT / "scripts" / "ingest-apriori.py"
FIXTURE_SIMPLE = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-example.json"
FIXTURE_UNIVEST = ROOT / "scripts" / "test-fixtures" / "apriori-comparison-univest.json"
HANDBUILT_UNIVEST_MATRIX = ROOT / "data" / "univest" / "element_matrix.json"

TMP_BASE = Path("/tmp/test-ingest-apriori")

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"

VERBOSE = "-v" in sys.argv


# ─── helpers ────────────────────────────────────────────────────────────────

def run_adapter(args: list[str], expect_exit: int = 0) -> tuple[int, str, str]:
    """Run the adapter as a subprocess. Returns (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(ADAPTER), *args],
        capture_output=True, text=True, timeout=30,
    )
    return result.returncode, result.stdout, result.stderr


def import_adapter():
    """Import ingest-apriori as a module to test individual functions."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("ingest_apriori", ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def make_tmp_dir(name: str) -> Path:
    p = TMP_BASE / name
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)
    return p


# ─── tests ──────────────────────────────────────────────────────────────────

def test_simple_dry_run():
    """Adapter dry-run on simple fixture exits 0 and writes nothing."""
    out_dir = make_tmp_dir("simple-dry")
    rc, stdout, stderr = run_adapter([
        "fixturo",
        "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots",
        "--dry-run",
        "-o", str(out_dir),
    ])
    assert rc == 0, f"exit code: {rc}, stderr: {stderr}"
    assert "(dry-run mode" in stdout, "dry-run banner missing"
    # No files written in dry-run
    assert list(out_dir.iterdir()) == [], f"dry-run wrote files: {list(out_dir.iterdir())}"


def test_simple_real_run():
    """Adapter real-run on simple fixture writes 3 expected files + valid JSON."""
    out_dir = make_tmp_dir("simple-real")
    rc, stdout, stderr = run_adapter([
        "fixturo",
        "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots",
        "-o", str(out_dir),
    ])
    assert rc == 0, f"exit code: {rc}, stderr: {stderr}"
    for f in ("apriori_input.json", "source.md", "element_matrix.json"):
        assert (out_dir / f).is_file(), f"{f} missing"
    # JSON validity
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    assert matrix["client"] == "fixturo"
    assert matrix["n_total"] == 30
    assert len(matrix["segments"]) == 3
    assert len(matrix["variants"]) == 3
    # Apriori ids → our ids
    var_ids = [v["id"] for v in matrix["variants"]]
    assert var_ids == ["Control", "V1", "V2"], f"variant ids: {var_ids}"


def test_segment_weights_sum_to_one():
    """Adapter computes segment weights that sum to ~1.0."""
    out_dir = make_tmp_dir("weights")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    total_weight = sum(s["weight"] for s in matrix["segments"])
    # Weights are rounded to 4 decimals, may not sum to exactly 1.0
    assert abs(total_weight - 1.0) < 0.001, f"weights sum: {total_weight}"


def test_aggregate_metrics_normalization():
    """completion_rate as integer (e.g. 28) is normalized to fraction (0.28); sus → sus_score."""
    out_dir = make_tmp_dir("agg-norm")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    am = matrix["aggregate_metrics"]
    # sus → sus_score remap
    assert "sus_score" in am, f"aggregate_metrics keys: {list(am.keys())}"
    assert "sus" not in am, "sus key should be remapped to sus_score"
    # completion_rate normalized to fractions
    assert am["completion_rate"]["Control"] == 0.28, f"Control cr: {am['completion_rate']['Control']}"
    assert am["completion_rate"]["V2"] == 0.48
    # sus values preserved as-is
    assert am["sus_score"]["Control"] == 62.0


def test_apriori_next_test_surfaced():
    """recommended_next_test is included in matrix metadata."""
    out_dir = make_tmp_dir("next-test")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    nt = matrix.get("apriori_recommended_next_test")
    assert nt is not None, "apriori_recommended_next_test missing"
    assert "passkey" in nt["name"].lower(), f"unexpected next_test name: {nt['name']}"


def test_taxonomy_flagged_needs_review():
    """All 12 taxonomy element values per variant are flagged __needs_review__."""
    out_dir = make_tmp_dir("taxonomy-flag")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    expected_dims = {"layout", "modal_interrupt", "branding", "price_visibility",
                     "cta_primary_label", "cta_style", "cta_stack", "urgency_mechanism",
                     "refund_or_guarantee_copy", "trust_signal", "evidence_detail"}
    for v in matrix["variants"]:
        elems = v["elements"]
        assert set(elems.keys()) == expected_dims, f"missing dims: {expected_dims - set(elems.keys())}"
        for dim, val in elems.items():
            assert val == "__needs_review__", f"variant {v['id']}.{dim} = {val!r} (expected sentinel)"


def test_citations_extracted():
    """Citations are extracted from theme_movement.monologue_evidence."""
    out_dir = make_tmp_dir("citations")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    cits = matrix["citations"]
    assert len(cits) >= 4, f"expected at least 4 citations from fixture monologues, got {len(cits)}"
    # Validate shape of one citation
    c = cits[0]
    for key in ("segment", "variant", "quote", "context"):
        assert key in c, f"citation missing {key}"


def test_friction_reshaping():
    """friction_provenance correctly reshaped + persona_count fuzzy-matched from theme_movement."""
    out_dir = make_tmp_dir("friction")
    rc, _, stderr = run_adapter([
        "fixturo", "--from-comparison-json", str(FIXTURE_SIMPLE),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    fps = matrix["friction_points"]
    assert len(fps) == 3, f"expected 3 friction points, got {len(fps)}"
    # Statuses preserved
    statuses = {f["status"] for f in fps}
    assert "resolved" in statuses
    assert "introduced" in statuses
    # Apriori variant ids in 'presence' should be remapped to ours
    fp_password = next(f for f in fps if "password" in f["summary"].lower())
    assert "Control" in fp_password["presence"]
    assert "V2" in fp_password["presence"]


def test_invalid_json_input():
    """Adapter exits non-zero on malformed JSON input."""
    bad_file = make_tmp_dir("invalid") / "bad.json"
    bad_file.write_text("{ this is not json")
    rc, _, stderr = run_adapter([
        "x", "--from-comparison-json", str(bad_file),
        "--no-fetch-screenshots", "-o", str(bad_file.parent),
    ])
    assert rc == 1, f"expected exit 1, got {rc}"
    assert "not valid JSON" in stderr, f"missing error message; stderr: {stderr}"


def test_missing_file():
    """Adapter exits non-zero if --from-comparison-json file doesn't exist."""
    rc, _, stderr = run_adapter([
        "x", "--from-comparison-json", "/tmp/does-not-exist.json",
        "--no-fetch-screenshots",
    ])
    assert rc == 1
    assert "not found" in stderr


def test_missing_required_fields():
    """Adapter exits non-zero if ComparisonData missing any required field."""
    out_dir = make_tmp_dir("missing-fields")
    bad_file = out_dir / "minimal.json"
    # Drop variant_screenshots
    full = json.loads(FIXTURE_SIMPLE.read_text())
    del full["variant_screenshots"]
    bad_file.write_text(json.dumps(full))
    rc, _, stderr = run_adapter([
        "x", "--from-comparison-json", str(bad_file),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 1, f"expected exit 1, got {rc}"
    assert "missing required fields" in stderr
    assert "variant_screenshots" in stderr


def test_helper_slugify():
    """slugify('Skeptical Investor') == 'skeptical_investor'."""
    mod = import_adapter()
    assert mod.slugify("Skeptical Investor") == "skeptical_investor"
    assert mod.slugify("Time-Pressed Founder") == "time_pressed_founder"
    assert mod.slugify("UPPERCASE") == "uppercase"
    assert mod.slugify("  with spaces  ") == "with_spaces"
    assert mod.slugify("special!@#chars") == "special_chars"


def test_helper_variant_label():
    """variant_label maps Apriori ids to our format."""
    mod = import_adapter()
    assert mod.variant_label("control") == "Control"
    assert mod.variant_label("a") == "V1"
    assert mod.variant_label("b") == "V2"
    assert mod.variant_label("d") == "V4"
    # Unknown id falls back to .upper()
    assert mod.variant_label("xyz") == "XYZ"


# ─── real-data tests (require univest fixture) ──────────────────────────────

def test_univest_real_run():
    """Adapter handles realistic univest input (5 variants × 4 segments × 50 personas)."""
    out_dir = make_tmp_dir("univest")
    rc, stdout, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, f"exit {rc}, stderr: {stderr}"
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    assert matrix["n_total"] == 50
    assert len(matrix["variants"]) == 5
    assert len(matrix["segments"]) == 4
    # Variant id mapping for 5 variants
    assert [v["id"] for v in matrix["variants"]] == ["Control", "V1", "V2", "V3", "V4"]


def test_univest_matches_handbuilt_segments():
    """Adapter-produced segments match our hand-built v2 univest matrix."""
    if not HANDBUILT_UNIVEST_MATRIX.exists():
        return  # Skip if no hand-built matrix yet
    out_dir = make_tmp_dir("univest-cmp-segs")
    rc, _, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    adapter_m = json.loads((out_dir / "element_matrix.json").read_text())
    handbuilt_m = json.loads(HANDBUILT_UNIVEST_MATRIX.read_text())
    ad = {s["id"]: (s["n"], s["weight"]) for s in adapter_m["segments"]}
    hb = {s["id"]: (s["n"], s["weight"]) for s in handbuilt_m["segments"]}
    assert ad == hb, f"adapter={ad}, handbuilt={hb}"


def test_univest_matches_handbuilt_conversion_data():
    """Adapter-produced conversion_by_segment matches hand-built v2 within 0.005."""
    if not HANDBUILT_UNIVEST_MATRIX.exists():
        return
    out_dir = make_tmp_dir("univest-cmp-conv")
    rc, _, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    adapter_m = json.loads((out_dir / "element_matrix.json").read_text())
    handbuilt_m = json.loads(HANDBUILT_UNIVEST_MATRIX.read_text())
    for ad_v, hb_v in zip(adapter_m["variants"], handbuilt_m["variants"]):
        for seg_id, hb_val in hb_v["conversion_by_segment"].items():
            ad_val = ad_v["conversion_by_segment"].get(seg_id)
            assert abs(ad_val - hb_val) < 0.005, (
                f"{ad_v['id']}.{seg_id}: adapter={ad_val} handbuilt={hb_val}"
            )


def test_univest_matches_handbuilt_aggregate_metrics():
    """Adapter-produced aggregate completion_rate matches hand-built exactly."""
    if not HANDBUILT_UNIVEST_MATRIX.exists():
        return
    out_dir = make_tmp_dir("univest-cmp-agg")
    rc, _, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    adapter_m = json.loads((out_dir / "element_matrix.json").read_text())
    handbuilt_m = json.loads(HANDBUILT_UNIVEST_MATRIX.read_text())
    ad_cr = adapter_m["aggregate_metrics"]["completion_rate"]
    hb_cr = handbuilt_m["aggregate_metrics"]["completion_rate"]
    assert ad_cr == hb_cr, f"adapter={ad_cr}, handbuilt={hb_cr}"


def test_univest_source_md_well_formed():
    """source.md has all 10 expected sections from real univest input."""
    out_dir = make_tmp_dir("univest-source-md")
    rc, _, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    md = (out_dir / "source.md").read_text()
    expected_sections = ["## 1. Variants", "## 2. Audience segments", "## 3. Conversion rates",
                         "## 4. Friction points", "## 5. Theme movement",
                         "## 6. Per-screen comparison", "## 7. Persona journeys",
                         "## 8. Apriori's recommendations",
                         "## 9. Apriori's recommended next test",
                         "## 10. Risks Apriori flagged"]
    for section in expected_sections:
        assert section in md, f"source.md missing section: {section}"
    # Real content checks
    assert "TMPV" in md or "ZOMATO" in md, "expected stock names absent"
    assert "Skeptical Investor" in md
    assert "44%" in md, "V4 completion_rate missing"


def test_univest_apriori_next_test_v5_proposal():
    """Apriori's V5 proposal ('Real Closed Trade') is surfaced in matrix metadata."""
    out_dir = make_tmp_dir("univest-v5")
    rc, _, stderr = run_adapter([
        "univest-test", "--from-comparison-json", str(FIXTURE_UNIVEST),
        "--no-fetch-screenshots", "-o", str(out_dir),
    ])
    assert rc == 0, stderr
    matrix = json.loads((out_dir / "element_matrix.json").read_text())
    nt = matrix.get("apriori_recommended_next_test")
    assert nt is not None
    assert "Real Closed Trade" in nt["name"], f"unexpected: {nt}"
    assert "48-52%" in nt["predicted_conversion"]


# ─── runner ─────────────────────────────────────────────────────────────────

TESTS = [
    # Unit
    test_helper_slugify,
    test_helper_variant_label,
    # Integration — simple
    test_simple_dry_run,
    test_simple_real_run,
    test_segment_weights_sum_to_one,
    test_aggregate_metrics_normalization,
    test_apriori_next_test_surfaced,
    test_taxonomy_flagged_needs_review,
    test_citations_extracted,
    test_friction_reshaping,
    # Edge cases
    test_invalid_json_input,
    test_missing_file,
    test_missing_required_fields,
    # Real-data
    test_univest_real_run,
    test_univest_matches_handbuilt_segments,
    test_univest_matches_handbuilt_conversion_data,
    test_univest_matches_handbuilt_aggregate_metrics,
    test_univest_source_md_well_formed,
    test_univest_apriori_next_test_v5_proposal,
]


def main() -> int:
    if not ADAPTER.is_file():
        print(f"Error: {ADAPTER} not found", file=sys.stderr)
        return 1
    if not FIXTURE_SIMPLE.is_file():
        print(f"Error: {FIXTURE_SIMPLE} not found", file=sys.stderr)
        return 1

    print(f"Running {len(TESTS)} tests against {ADAPTER.name}...\n")
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

    # Cleanup tmp
    if TMP_BASE.exists():
        shutil.rmtree(TMP_BASE)

    print()
    print(f"{GREEN}Passed:{RESET} {len(passed)}/{len(TESTS)}")
    if failed:
        print(f"{RED}Failed:{RESET} {len(failed)}")
        if VERBOSE:
            for name, msg in failed:
                print(f"  {RED}{name}:{RESET} {msg}")
        return 1
    print(f"{GREEN}All tests passed.{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

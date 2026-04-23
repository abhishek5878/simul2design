#!/usr/bin/env python3
"""
Automate confound detection for a client's element_matrix.json.

A confound is a pair of (dimension, value) elements that co-occur across all
variants they appear in — meaning no variant has one without the other.
Without isolated variation, downstream skills cannot attribute conversion
impact to either element independently.

Usage:
    scripts/detect-confounds.py data/<client>/element_matrix.json

Emits a JSON report to stdout listing detected confounds, each with:
    - the co-occurring (dimension=value) pairs
    - the variants involved
    - a severity signal (full confound vs partial break)

Exit code:
    0 — ran successfully (confounds may or may not be present — see output)
    1 — input file missing or malformed
    2 — no confounds found (still exit 0 but useful for scripting)

Non-destructive: does NOT modify the matrix. Output is for the human + the
synthesize skill to cross-check the matrix's hand-written confounds[] block.
"""

import json
import sys
from itertools import combinations
from pathlib import Path


def load_matrix(path: Path) -> dict:
    if not path.exists():
        print(f"Error: {path} does not exist", file=sys.stderr)
        sys.exit(1)
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: {path} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def collect_variant_elements(matrix: dict) -> dict:
    """{variant_id: set of 'dim=value' strings}"""
    out = {}
    for v in matrix.get("variants", []):
        vid = v["id"]
        elements = v.get("elements", {})
        # Ignore sub-attribute keys (starting with _ or containing _detail_format etc.)
        # and only take primary dimension=value pairs.
        pairs = set()
        for dim, val in elements.items():
            if dim.startswith("_"):
                continue
            if isinstance(val, str):
                pairs.add(f"{dim}={val}")
        out[vid] = pairs
    return out


def find_confounds(variant_elements: dict) -> list:
    """
    For every pair of element values (A, B) that appear together in any variant,
    check whether they co-occur across ALL variants where either appears. That's a confound.
    """
    # Collect where each element appears.
    element_variants = {}  # 'dim=value' -> set of variant ids
    for vid, elems in variant_elements.items():
        for e in elems:
            element_variants.setdefault(e, set()).add(vid)

    confounds = []
    seen_pairs = set()

    # For each variant, enumerate pairs of elements within it.
    for vid, elems in variant_elements.items():
        for a, b in combinations(sorted(elems), 2):
            if (a, b) in seen_pairs:
                continue
            seen_pairs.add((a, b))

            va, vb = element_variants[a], element_variants[b]

            # "Confounded" means: everywhere A appears, B also appears (A subset of B),
            # OR B subset of A, OR they have identical variant sets.
            # Union minus intersection is the number of variants that "break" the pairing.
            union = va | vb
            intersection = va & vb
            differential = union - intersection  # variants where one appears but not the other

            # Meaningful confound: at least 2 variants share the pair AND zero breaks it.
            if len(intersection) >= 2 and len(differential) == 0:
                severity = "full"
            # Partial: shared in >=2 variants but broken in >=1
            elif len(intersection) >= 2 and len(differential) >= 1:
                # Only interesting if the break doesn't fully dissociate them.
                # Skip if the pair is obviously not confounded (e.g., appears together in one variant but not 80% of time).
                if len(intersection) / len(union) >= 0.67:
                    severity = "partial"
                else:
                    continue
            else:
                continue

            confounds.append({
                "pair": [a, b],
                "co_occur_in_variants": sorted(intersection),
                "only_one_in_variants": sorted(differential),
                "severity": severity,
                "note": (
                    f"{a} and {b} appear together in {len(intersection)} variant(s); "
                    f"neither appears alone" if severity == "full"
                    else f"co-occur in {len(intersection)} of {len(union)} variants; partial break"
                )
            })

    return confounds


def compare_to_matrix_confounds(detected: list, matrix: dict) -> dict:
    """Cross-check against the matrix's hand-written confounds[] block."""
    hand_written = matrix.get("confounds", [])
    hand_pairs = set()
    for h in hand_written:
        # Normalize to sorted tuple of "dim=value" strings
        if "elements" in h:
            hand_pairs.add(tuple(sorted(h["elements"])))

    auto_pairs = set(tuple(sorted(c["pair"])) for c in detected if c["severity"] == "full")

    return {
        "hand_written_count": len(hand_written),
        "auto_detected_full_count": len(auto_pairs),
        "auto_only": sorted(list(auto_pairs - hand_pairs)),
        "hand_only": sorted(list(hand_pairs - auto_pairs)),
        "both": sorted(list(auto_pairs & hand_pairs)),
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: detect-confounds.py <path-to-element_matrix.json>", file=sys.stderr)
        return 1

    matrix_path = Path(sys.argv[1])
    matrix = load_matrix(matrix_path)

    variant_elements = collect_variant_elements(matrix)
    confounds = find_confounds(variant_elements)
    cross_check = compare_to_matrix_confounds(confounds, matrix)

    report = {
        "matrix_file": str(matrix_path),
        "client": matrix.get("client"),
        "variants_analyzed": list(variant_elements.keys()),
        "detected_confounds": confounds,
        "cross_check_vs_matrix": cross_check,
        "summary": {
            "full_confounds_detected": sum(1 for c in confounds if c["severity"] == "full"),
            "partial_confounds_detected": sum(1 for c in confounds if c["severity"] == "partial"),
            "auto_detection_matches_hand_written": len(cross_check["auto_only"]) == 0 and len(cross_check["hand_only"]) == 0,
        }
    }

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

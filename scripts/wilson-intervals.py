#!/usr/bin/env python3
"""
Wilson 95% binomial confidence-interval helper.

Two modes:

1. Single-segment mode — compute Wilson CI for one (p, n) observation:
     scripts/wilson-intervals.py --p 0.25 --n 12

2. Matrix mode — for every (variant, segment) pair in element_matrix.json,
   emit the Wilson CI on the observed conversion:
     scripts/wilson-intervals.py data/<client>/element_matrix.json

Exit code 0 on success.
"""

import argparse
import json
import math
import sys
from pathlib import Path


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple:
    """Wilson score 95% CI for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0.0 <= p <= 1.0:
        raise ValueError("p must be in [0, 1]")
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z / denom) * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return (max(0.0, center - half), min(1.0, center + half))


def single_mode(p: float, n: int) -> dict:
    low, high = wilson_ci(p, n)
    return {
        "p": p,
        "n": n,
        "z": 1.96,
        "ci_low": round(low, 4),
        "ci_high": round(high, 4),
        "interval_width_pts": round((high - low) * 100, 2),
    }


def matrix_mode(path: Path) -> dict:
    if not path.exists():
        print("Error: %s does not exist" % path, file=sys.stderr)
        sys.exit(1)
    matrix = json.loads(path.read_text())
    segments = {s["id"]: s for s in matrix.get("segments", [])}
    out = {
        "matrix_file": str(path),
        "client": matrix.get("client"),
        "z": 1.96,
        "per_variant_segment": {},
    }
    for v in matrix.get("variants", []):
        vid = v["id"]
        out["per_variant_segment"][vid] = {}
        for sid, seg in segments.items():
            p = v.get("conversion_by_segment", {}).get(sid)
            n = seg.get("n")
            if p is None or n is None:
                continue
            low, high = wilson_ci(p, n)
            out["per_variant_segment"][vid][sid] = {
                "observed": p,
                "n": n,
                "ci_low": round(low, 4),
                "ci_high": round(high, 4),
                "interval_width_pts": round((high - low) * 100, 2),
            }
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Wilson 95% binomial CI helper.")
    parser.add_argument("matrix", nargs="?", help="Path to element_matrix.json (matrix mode)")
    parser.add_argument("--p", type=float, help="Observed proportion (single-segment mode)")
    parser.add_argument("--n", type=int, help="Sample size (single-segment mode)")
    args = parser.parse_args()

    if args.p is not None and args.n is not None:
        result = single_mode(args.p, args.n)
    elif args.matrix:
        result = matrix_mode(Path(args.matrix))
    else:
        parser.print_help(sys.stderr)
        return 2

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

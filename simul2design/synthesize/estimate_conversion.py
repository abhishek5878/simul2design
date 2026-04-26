"""estimate-conversion — pure-Python port of the Wilson interval math.

The full skill (.claude/skills/estimate-conversion/SKILL.md) does both:
1. Wilson 95% CI on per-segment baselines + predictions  ← this file
2. Coupling discount adjustment per adversary's coupled-mechanism notes  ← TODO LLM

This module ships the deterministic part. Coupling discount + hard-segment
widening + simulator-provenance flagging are skeletoned for the LLM cascade
in synthesize.py / adversary.py.

Wilson formula (Sonnet 4.5+ docs):
    z = 1.96  (95% CI)
    center = (p̂ + z²/(2n)) / (1 + z²/n)
    half_width = (z / (1 + z²/n)) × sqrt( p̂(1-p̂)/n + z²/(4n²) )
    [lower, upper] = [center - half_width, center + half_width]
"""

from __future__ import annotations
import math


WILSON_Z_95 = 1.96


def wilson_95_interval(p: float, n: int) -> tuple[float, float]:
    """Wilson 95% binomial confidence interval.

    Args:
        p: Observed proportion (0.0 to 1.0).
        n: Sample size.

    Returns:
        (lower, upper) clipped to [0, 1].

    Wilson is preferred over Normal approximation at small n (<30) because
    Normal can return intervals outside [0, 1].
    """
    if n <= 0:
        return (0.0, 0.0)
    z = WILSON_Z_95
    z2 = z * z
    denom = 1 + z2 / n
    center = (p + z2 / (2 * n)) / denom
    half_width = (z / denom) * math.sqrt(p * (1 - p) / n + z2 / (4 * n * n))
    return (max(0.0, center - half_width), min(1.0, center + half_width))


def apply_wilson_to_segments(matrix: dict, baseline_variant_id: str = "V4") -> dict:
    """Compute Wilson 95% CI per segment, on the baseline variant's observed conversion.

    Returns:
        {
          "<segment_id>": {
            "n": int,
            "baseline_variant": str,
            "baseline_conversion": float,
            "baseline_wilson_95_ci": [low, high],
          },
          ...
        }

    Used by synthesize/adversary to layer mechanism-derived deltas on top.
    """
    variants_by_id = {v["id"]: v for v in matrix.get("variants", [])}
    baseline = variants_by_id.get(baseline_variant_id)
    if baseline is None:
        raise ValueError(f"baseline variant '{baseline_variant_id}' not in matrix")

    out = {}
    for seg in matrix.get("segments", []):
        sid = seg["id"]
        n = seg.get("n", 0)
        p = baseline["conversion_by_segment"].get(sid)
        if p is None or n == 0:
            continue
        low, high = wilson_95_interval(p, n)
        out[sid] = {
            "n": n,
            "baseline_variant": baseline_variant_id,
            "baseline_conversion": p,
            "baseline_wilson_95_ci": [round(low, 3), round(high, 3)],
        }
    return out

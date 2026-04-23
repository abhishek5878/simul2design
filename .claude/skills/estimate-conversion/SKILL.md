---
name: estimate-conversion
description: Trigger after synthesize has produced per-segment predictions AND adversary has flagged any coupled-mechanism or interval-widening concerns. Applies Wilson binomial confidence intervals on per-segment predictions using segment n from the matrix; applies mechanism-coupling adjustments where adversary flagged them; emits refined intervals that the spec-writer and the post-ship evaluator consume. Client-agnostic.
---

# estimate-conversion skill

**Client-agnostic.** Reads n from the matrix, prediction intervals from synthesize, mechanism-coupling notes from adversary. No hardcoded client or segment.

## When to use

- `synthesized_variant.json` exists AND `adversary_review.json` either exists or the user has explicitly skipped adversary (say why).
- Per-segment predictions need to be hardened before spec-writer puts them in a client deliverable.
- Post-ship actuals arrived and the predicted-vs-actual delta needs to be recorded against the original predictions.

## When NOT to use

- No synthesis yet → run synthesize first.
- The ask is "how confident are you" without a specific V(N+1) element set to grade → use confidence_grade from synthesize directly.

## Inputs

1. `data/<client>/synthesized_variant.json` — per-segment predictions (point + preliminary intervals) + untested stack.
2. `data/<client>/element_matrix.json` — segment n (required for Wilson interval).
3. `data/<client>/adversary_review.json` (optional) — coupling concerns that warrant interval widening beyond pure small-sample uncertainty.
4. `data/<client>/weighted_scores.json` — evidence type per (dimension, value) for compounding uncertainty accounting.

## Methodology

### Wilson binomial confidence intervals

For each per-segment prediction `p̂` on segment size `n`:

```
Wilson 95% CI:
  z = 1.96
  center = (p̂ + z²/(2n)) / (1 + z²/n)
  half_width = (z / (1 + z²/n)) × sqrt( p̂(1-p̂)/n + z²/(4n²) )
  [lower, upper] = [center - half_width, center + half_width]
```

For Univest-style n=10-15 per segment, Wilson is preferred over Normal approximation because Normal gives impossible intervals (< 0 or > 1) at the tails.

### Compounding uncertainty adjustment

Starting from the Wilson interval on the baseline (the tested variant's observed conversion), apply adjustments:

1. **Clean-contrast-derived deltas**: the point delta is evidence-backed, but the delta's own uncertainty (~Wilson on the original V(N) side of the contrast) compounds. Combine via interval arithmetic: if baseline is [b_low, b_high] and delta is [d_low, d_high], the predicted interval is [b_low + d_low, b_high + d_high].
2. **Friction-resolution-derived lifts**: these have no pts magnitude. Express as [0, observed_segment_conversion_ceiling] — widest legitimate range — unless a clean contrast corroborates.
3. **Untested-mechanism-derived lifts**: the overlay's `expected_mechanism` gives a direction + rough magnitude. Apply as a BIASED interval: [0.5 × expected_magnitude, expected_magnitude] on the positive side; ALWAYS include 0 on the negative side. The interval must allow the mechanism to fail entirely.
4. **Coupled mechanisms** (per adversary): if K mechanisms target the same segment AND share a common substrate (per adversary's analysis), the independent-combination assumption is wrong. Multiply the non-linearity discount by 0.7 for each additional coupled mechanism. Example: 3 coupled mechanisms → discount 0.5 × 0.7² = 0.245 vs independent 0.7³ = 0.343.
5. **Small-sample ceiling**: an interval whose upper bound exceeds `1.2 × max(baseline, Wilson_upper)` is likely over-reaching; cap at that value with a flag.

### Output per segment

Each segment gets:

- `baseline_wilson_95_ci`: [low, high] on the tested-variant's observed conversion
- `predicted_wilson_95_ci`: [low, high] on V(N+1) including the adjustments above
- `prediction_decomposition`: what drove the lower bound, what drives the upper bound — named mechanisms, each with a direction ("positive", "negative", "zero-if-failed")
- `kill_condition`: the specific observable whose post-ship value would reject the prediction (IDEA.md: "the specific failure condition that would collapse this prediction")

## Workflow

1. Read synthesize's predictions, matrix segment n, adversary's coupling notes.
2. For each segment, compute baseline Wilson CI on the tested-variant observed conversion.
3. For each driver in synthesize's `per_segment_prediction.drivers`, classify into: clean_contrast_backed / friction_resolution / untested_mechanism.
4. Apply the compounding method above.
5. Apply coupling discount where adversary flagged it.
6. Emit `data/<client>/conversion_estimates.json`.
7. Update `synthesized_variant.json` to reference the refined intervals (or leave synthesize output immutable as the "before-estimator" record — preferred: immutable synthesize output + estimator output as the next-layer truth).
8. Update `tasks/progress.md` with the revised weighted-overall and the Skeptical-specific impact of coupled-mechanism discount.

## Output schema

```jsonc
{
  "version": "1.0",
  "client": "<client-slug>",
  "variant_estimated": "V5",
  "estimated_at": "YYYY-MM-DD",
  "source_synthesis": "data/<client>/synthesized_variant.json",
  "source_adversary": "data/<client>/adversary_review.json",

  "method": "wilson_95_with_coupling_adjustment",
  "wilson_z": 1.96,
  "coupling_discount_applied": { "<segment_id>": 0.35 },

  "per_segment_estimate": {
    "<segment_id>": {
      "n": 12,
      "baseline_variant": "V4",
      "baseline_conversion": 0.25,
      "baseline_wilson_95_ci": [0.07, 0.55],
      "synthesize_predicted_point": 0.35,
      "synthesize_predicted_interval": [0.30, 0.40],
      "estimator_revised_interval": [0.19, 0.41],
      "estimator_revised_point": 0.31,
      "revision_reason": "<one line: Wilson baseline widens low; coupled mechanisms shrink upper>",
      "kill_conditions": ["<observable and threshold that invalidates this>"]
    }
  },

  "weighted_overall_estimate": {
    "synthesize_point": 0.493,
    "synthesize_interval": [0.455, 0.530],
    "estimator_revised_point": 0.47,
    "estimator_revised_interval": [0.42, 0.52],
    "revision_note": "Wilson widens baselines; adversary's coupled-mechanism discount on Skeptical (3 untested mechanisms targeting same segment with shared honesty-substrate) drops Skeptical upper from 40% to 37% and lower from 30% to 27%. Weighted-overall impact: low drops ~3pt, upper drops ~1pt."
  },

  "flags": []
}
```

## Success criteria

- Every segment in the matrix has an `estimator_revised_interval`.
- Every interval is inside [0, 1] (Wilson guarantees this; the coupling adjustments must also).
- Every segment has at least one named `kill_condition` — the post-ship observable whose value would collapse the prediction.
- Weighted-overall revised interval is computed from per-segment, not re-fitted.
- The revision diff (synthesize → estimator) is explicit and named, so a reviewer can see what the estimator changed and why.

## Common pitfalls

- **Normal approximation instead of Wilson.** At n=10, Normal gives intervals that breach [0, 1]. Always Wilson.
- **Ignoring the adversary's coupling notes.** If adversary flagged coupled mechanisms, you MUST apply the coupling discount — don't treat it as advisory.
- **Refitting weighted-overall.** Do per-segment first, then weight. Never the reverse.
- **Claiming post-ship didn't happen within the interval** — unless post-ship actually arrived. The estimator predicts; it doesn't validate. Validation is a separate skill that runs when actuals come back.

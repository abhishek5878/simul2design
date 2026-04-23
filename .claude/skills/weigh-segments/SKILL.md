---
name: weigh-segments
description: Trigger after parse-simulation has produced a matrix for a client. Reads `data/<client>/element_matrix.json` + the client taxonomy overlay, and emits `data/<client>/weighted_scores.json` — per-(dimension, value) weighted score with evidence-type classification, segment-weight-adjusted impact, and contradiction penalties. Client-agnostic. Input to `synthesize`.
---

# weigh-segments skill

**Client-agnostic.** Reads the client slug, segments, and weights from the matrix itself. Never hardcodes client or segment names.

## When to use

- A matrix exists at `data/<client>/element_matrix.json` and you need to rank per-dimension values for the synthesizer.
- Audience weights changed and the scores need recomputation.
- The taxonomy overlay's contradictions changed.

## When NOT to use

- No matrix yet → run `parse-simulation` first.
- The ask is "which variant won" — that's just max over `conversion_by_segment` × weights, not a synthesis problem.
- The ask is "build V(N+1)" — that's `synthesize`, which consumes this skill's output.

## Evidence types (classify every (dimension, value) as exactly one)

1. **`clean_contrast`** — the matrix's `clean_element_contrasts[]` has a contrast where only this dimension differs. Highest confidence: per-segment delta is directly attributable.
2. **`friction_direct`** — a `friction_points[]` entry names this value explicitly AND identifies a specific segment pattern. Medium confidence: attributable negative for the named segment, not a positive signal elsewhere.
3. **`confounded`** — the value is observed but only alongside co-varying values listed in `confounds[]`. No single-value attribution allowed. Weighted score is `null` with evidence tier `confounded`.
4. **`untested`** — the value is in the taxonomy (base or overlay) but does not appear in any variant's `elements`. Weighted score is `null` with an `expected_mechanism` field from the overlay's "proposed-but-untested" notes.
5. **`variant_only`** — the value appears in exactly one variant's observations, but that variant's conversion delta vs Control is confounded by other dimensions changing. Partial signal: use variant-level conversion as a weak informative signal only; do NOT attribute to this value alone.

## Workflow

1. Read `data/<client>/element_matrix.json`. Extract: segments[], variants[], friction_points[], clean_element_contrasts[], confounds[], flags[], extraction_confidence{}.
2. Read `.claude/rules/element-taxonomy-base.md` and `.claude/rules/element-taxonomy-<client>.md`. Extract: the allowed values for every dimension, the client-specific contradiction rules, the proposed-but-untested notes.
3. For each dimension (base + overlay):
   3a. Enumerate every value observed in any variant's `elements` block.
   3b. For each observed value: classify evidence type per the rules above.
   3c. Enumerate every value in the taxonomy that is NOT in the variants → classify as `untested`.
4. For each (dimension, value) marked `clean_contrast`:
   4a. Find the contrast in `clean_element_contrasts[]` where this dimension is the sole diff.
   4b. Pull per-segment deltas from the contrast's observation (store as `delta_pts` — positive means adopting this value vs the other side of the contrast raises conversion for that segment).
   4c. Compute `weighted_score = Σ_segments (segment.weight × delta_pts)`.
5. For each (dimension, value) marked `friction_direct`:
   5a. Pull friction count + affected segment from the matrix. Compute the flag rate: `friction_count / segment_n` (or `/ n_total` if cross-segment).
   5b. **Do NOT convert flag rate to conversion-pts directly** — they're different units (flag rate = what fraction noticed/objected; pts = how much conversion changed). A high flag rate is strong *directional* evidence but does not establish the magnitude of conversion impact without a corroborating contrast.
   5c. If a corroborating clean_contrast also exists for this value (same affected segment), use the contrast's delta_pts; the friction is corroboration. Emit `evidence_type: clean_contrast` with a `corroborating_friction` note.
   5d. If only friction exists: emit `weighted_score_pts: null`, `confidence: medium` (if flag rate ≥ 30%) or `low` (if < 30%), with a `directional_signal: negative` field for the affected segment and a structured `friction_evidence` block. The synthesizer treats this as "avoid for this audience if the segment is in the mix" without a pts magnitude.
   5e. Cross-segment friction affecting ≥ 50% of users (like `price_opacity` 39/50 = 78%) is treated as decisive directional negative even without a contrast. Confidence: medium-high.
6. For each (dimension, value) marked `confounded` or `variant_only`: emit score as `null`, evidence tier set accordingly, and include a `signal_from` field pointing at the variant(s) + the confound entry that prevents attribution.
7. For each (dimension, value) marked `untested`: emit `expected_mechanism` from the overlay's proposed-but-untested notes. Score is `null`.
8. **Apply client-overlay contradictions — with double-counting check.** For each overlay contradiction of the form `(element_value, segment) → negative`:
   8a. If the value's evidence type is `clean_contrast` and that contrast already observed the affected segment: the penalty is already reflected in per_segment_impact. Record the contradiction as a label (`contradictions_applied` with `already_in_contrast: true`) but apply NO additional pts penalty.
   8b. If the value's evidence type is `friction_direct` with the same segment as the contradiction: same — already counted, no double-apply.
   8c. If the value is `untested` and the contradiction's mechanism is expected to transfer: carry as `expected_contradiction` in the output, with no pts penalty (score is null anyway).
   8d. Only apply as a score penalty when the contradiction adds information the contrast/friction didn't already capture (rare in practice — flag if this happens, it may indicate the contradiction is redundant).
9. **Rank within each dimension.** Sort observed values by adjusted weighted score. Mark one as `recommended`. If the top score is within noise-band (<5pts difference) of the runner-up, flag as `tie`. Always include a "for <segment>-heavy audience, prefer X" suggestion if any value is segment-specifically optimal.
10. Emit `data/<client>/weighted_scores.json`.
11. Spot-check: the hand-computed clean contrast (e.g., V2→V3 for Univest's `cta_style`) must reproduce. If it doesn't, stop — the pipeline is broken.
12. Update `tasks/progress.md` with evidence-tier distribution (how many dimensions got `clean_contrast` vs `confounded` vs `untested`) — this is a KPI of dataset informativeness.

## Decision tree

- If a dimension has 0 observed values of evidence type `clean_contrast` or `friction_direct`: emit `recommended: null` + `reason: "no rankable evidence for this dimension from current dataset"`. Do NOT guess. `synthesize` will need to either skip this dimension or reach for `untested` values with wider confidence intervals.
- If the same value appears in multiple `clean_contrast` entries: weight-average the per-segment deltas (the matrix shouldn't contain conflicting clean contrasts, but if it does, take the mean and log a flag).
- If a contradiction from the overlay applies to a `clean_contrast` value: apply it. If it applies to an `untested` value: carry it forward as an `expected_contradiction` note so `synthesize` sees it.
- If all observed values of a dimension are `confounded`: the dimension is effectively non-informative from this dataset. Flag for `improvements.md` — "need more variants to disambiguate <dimension>."

## Output schema

```jsonc
{
  "version": "1.0",
  "client": "<client-slug>",
  "source_matrix": "data/<client>/element_matrix.json",
  "taxonomy_base": ".claude/rules/element-taxonomy-base.md",
  "taxonomy_overlay": ".claude/rules/element-taxonomy-<client>.md",
  "audience_weights": { "<segment_id>": 0.24 },
  "dimensions": {
    "<dimension_name>": {
      "values": {
        "<value>": {
          "evidence_type": "clean_contrast | friction_direct | confounded | variant_only | untested",
          "observed_in_variants": ["V3", "V4"],
          "per_segment_impact": {
            "<segment_id>": { "delta_pts": 9.0, "basis": "clean_contrast:V2->V3" }
          },
          "weighted_score_pts": 6.42,
          "contradictions_applied": [
            { "with": "segment:trust_seeker", "penalty_pts": 2.0, "source": "overlay:cta_style=high_contrast_green+trust_seeker" }
          ],
          "adjusted_score_pts": 4.42,
          "confidence": "high | medium | low | none",
          "expected_mechanism": "<from overlay, only if untested>",
          "flags": []
        }
      },
      "recommended": {
        "value": "high_contrast_green",
        "alternative_for_audience_skew": {
          "trust_seeker_heavy": "muted_premium (untested) — preserves Bargain lift, removes Trust penalty"
        },
        "rationale": "<one line>",
        "confidence": "high | medium | low"
      },
      "dimension_informativeness": "rankable | non_informative"
    }
  },
  "dimension_summary": {
    "rankable_dimensions": 1,
    "confounded_dimensions": 7,
    "untested_only_dimensions": 0,
    "note": "Evidence-tier distribution is a dataset-informativeness KPI."
  },
  "flags": []
}
```

## Success criteria

- Every (dimension, value) pair in the taxonomy (base + overlay) appears exactly once in the output, with an evidence type.
- The clean V2→V3 `cta_style` computation in the output matches a hand computation.
- No value of evidence type `confounded` or `untested` emits a non-null `weighted_score_pts`. Null is honest; fabrication is not.
- The output is self-describing: a synthesizer (or a human reader) can tell, from the JSON alone, which values are evidence-backed and which are expectation-only.
- No client-specific names appear in this SKILL.md (other than illustrative anti-examples).

## Common pitfalls

- **Weighting everything.** Tempting to emit a score for every value to make the output look complete. Don't. Null-with-evidence-tier is the correct output for `confounded` and `untested`.
- **Mixing positive evidence with friction penalties.** Friction is a per-segment penalty; clean-contrast deltas are per-segment impacts. They're different units. Friction becomes a negative delta for the affected segment only; it shouldn't blanket-penalize the value.
- **Ignoring the contradictions block in overlay.** If the overlay says "green + Trust Seeker is −10pts," you must apply it explicitly. The synthesizer doesn't reparse the overlay.
- **Baking in segment count.** Don't assume 4 segments. Don't iterate over known names. Always read from the matrix.
- **Claiming high confidence on small samples.** n=10-15 per segment: a 1-2pt delta is inside the noise. Confidence tier `high` requires both a clean contrast AND a per-segment delta ≥ ~8pts.

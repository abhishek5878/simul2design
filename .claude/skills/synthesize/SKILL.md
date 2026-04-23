---
name: synthesize
description: Trigger after weigh-segments has produced a ranked set of per-dimension recommendations for a client. Picks the V(N+1) element set, enforces cross-dimension consistency from the client overlay, attaches citations to every choice, and flags the untested stack. Client-agnostic. Output feeds the adversary agent (Day 5) before spec-writer.
---

# synthesize skill

**Client-agnostic.** Reads client slug, weighted scores, overlay, and matrix from paths derived from the slug. No hardcoded client / segment / value names.

## When to use

- `data/<client>/weighted_scores.json` exists and is current.
- The user asks to produce V(N+1), the optimal untested combination, or "what should we ship next."
- Audience weights changed enough that recomputation is warranted (the output depends on segment weights via weigh-segments).

## When NOT to use

- `weighted_scores.json` is missing or stale → run `weigh-segments` first.
- The ask is "which tested variant should we pick" — that's variant-max, not synthesis.
- The ask is "what does the evidence show" — that's weigh-segments (the reasoning artifact). Synthesize is the decision artifact.

## Inputs

1. **Client slug** (inferred from `weighted_scores.client` field).
2. **Audience override** (optional) — if the client's real audience differs from the simulated one. Default: use `audience_weights` from weighted_scores.
3. **Conservatism mode** (optional) — default `balanced`. Alternatives: `conservative` (prefer observed-high over untested even when untested has higher expected value) or `exploratory` (reach more aggressively for untested-mechanism candidates).

## Workflow

1. Load `data/<client>/weighted_scores.json`, `.claude/rules/element-taxonomy-base.md`, `.claude/rules/element-taxonomy-<client>.md`, `data/<client>/element_matrix.json` (for citation text).
2. **Per-dimension draft pick.** For each dimension, start from `weighted_scores.dimensions.<dim>.recommended.value`.
3. **Apply conservatism mode.** If `conservative` and the recommendation is an untested value: downgrade to the highest-evidence observed value from the same dimension. If `exploratory` and an untested value has a named positive mechanism: prefer it over observed but lower-upside values.
4. **Apply audience override.** If the user specified different audience weights, check each dimension: does the swap of weights flip the recommended value? (Computable from per_segment_impact on clean_contrast values; qualitative for others.) If yes, note the flip and adopt the audience-adjusted choice.
5. **Apply cross-dimension consistency.** Read the overlay's "Contradictions" and any structural consistency rules. Enforce:
   - **Mutual-exclusion rules**: if rule says `A and B cannot coexist`, resolve by picking the higher-evidence of the two.
   - **Required-pair rules**: if rule says `A requires B`, and A is picked, force B to the paired value.
   - **Same-element-different-names rules** (e.g., `visible_with_framing` + `implicit_refund` being one banner): keep them in sync; never emit combinations that imply a banner copy exists without the banner.
6. **Attach citations.** For every chosen value, emit a `citation` block pointing at the evidence basis:
   - If `clean_contrast`: `{type: "clean_contrast", ref: "<contrast label>", per_segment_delta: {...}}` + preserve the contrast observation sentence verbatim.
   - If `friction_direct`: `{type: "friction_point", id: "<friction_point.id from matrix>", flag_rate, segment_pattern}` + preserve the friction summary sentence.
   - If `untested`: `{type: "overlay_mechanism", ref: "<overlay section>", expected_mechanism: "<verbatim from overlay>"}` — mark as `"untested": true`.
   - If `universal_adoption` (all post-Control variants adopted it): `{type: "universal_adoption", variants: [...]}`.
7. **Count the untested stack.** How many chosen values are `"untested": true`? If > 4, emit a warning flag. Consider narrowing unless exploratory mode explicitly asks for the stack.
8. **Preliminary per-segment prediction.** For each segment, estimate V(N+1) conversion. Use:
   - Baseline = best-observed segment conversion across tested variants.
   - Add: documented pts lift from clean_contrast choices (applied with segment weighting).
   - Add: directional positive lift from friction-resolutions (name the magnitude as "undetermined, expect +0 to +X based on friction prevalence"; keep it as an interval).
   - For untested values: add the overlay's expected-mechanism direction as a qualitative adjustment, with a widened interval.
   - Roll up to weighted overall.
9. **Emit `data/<client>/synthesized_variant.json`** + a companion `synthesized_variant.md` human-readable summary.
10. **Update `tasks/progress.md`** with the V(N+1) headline, untested-stack count, and predicted weighted-overall interval.
11. **Hand off to adversary.** Do NOT write the spec yet. IDEA.md rule: synthesize and spec-writer are separate, with adversary in between.

## Decision tree

- If `weighted_scores.dimensions.<dim>.recommended.value` is `null` (non-informative dimension): pick the most-adopted value from observations (e.g., 4/5 variants used it). Emit citation type `default_by_adoption_rate` + confidence `low`. Do NOT guess at untested values for non-informative dimensions — the synthesis can't add signal where none exists.
- If two dimensions have mutually-exclusive recommended values per the overlay: resolve by comparing confidence tiers. If tied: prefer the dimension whose recommendation has a pts magnitude over the dimension that has only directional evidence. Log the resolution.
- If a dimension's recommended value is untested AND another dimension's observed value (lower-upside) has a stronger mechanism argument for the same segment: prefer the observed value. Untested should be chosen when the mechanism is strong and the observed best is a known liability (e.g., green penalizing Trust), not as a tiebreaker.

## Confidence roll-up

Emit a single V(N+1) `confidence_grade`:
- **High**: ≥ 6 dimensions have observed-high evidence AND ≤ 2 dimensions resolve to untested values.
- **Medium**: 3-5 dimensions observed-high, ≤ 4 untested.
- **Low**: < 3 observed-high OR > 4 untested.
- Attach a one-line diagnosis in every case: "Confidence is <grade> because <N> observed-high / <M> directional / <K> untested."

## Output schema

```jsonc
{
  "version": "1.0",
  "client": "<client-slug>",
  "variant_id": "V5",
  "generated_at": "YYYY-MM-DD",
  "conservatism_mode": "balanced | conservative | exploratory",
  "audience_weights_used": { "<segment_id>": 0.24 },
  "audience_source": "simulation_default | user_override",

  "elements": {
    "<dimension>": {
      "value": "<chosen value>",
      "citation": {
        "type": "clean_contrast | friction_point | overlay_mechanism | universal_adoption | default_by_adoption_rate",
        "ref": "<matrix id or overlay section>",
        "verbatim_quote": "<if applicable — friction summary, contrast observation, or overlay mechanism sentence>"
      },
      "confidence": "high | medium | low",
      "untested": false,
      "replaces": "<the V(N) value for same dimension>",
      "rationale_one_line": "<why this over observed alternatives>"
    }
  },

  "cross_dimension_consistency": {
    "applied_rules": [
      { "rule": "<rule from overlay>", "resolution": "<how synthesize handled it>" }
    ],
    "conflicts_surfaced_and_resolved": [],
    "remaining_inconsistencies": []
  },

  "untested_stack": {
    "count": 0,
    "dimensions_with_untested": [],
    "warning": "<only if count > 4>"
  },

  "per_segment_prediction": {
    "<segment_id>": {
      "baseline_from_best_tested_variant": "<variant_id>",
      "baseline_conversion": 0.25,
      "expected_delta_pts": { "low": 3, "point": 8, "high": 12 },
      "predicted_conversion": { "low": 0.28, "point": 0.33, "high": 0.37 },
      "drivers": ["<list of element choices driving the lift>"],
      "failure_conditions": ["<named failure mode that would collapse this prediction>"]
    }
  },

  "weighted_overall_prediction": {
    "baseline": 0.44,
    "baseline_source": "V4 actual",
    "predicted": { "low": 0.47, "point": 0.51, "high": 0.55 },
    "confidence_grade": "high | medium | low",
    "confidence_diagnosis": "<one line>"
  },

  "flags": []
}
```

## Success criteria

- Every dimension in the taxonomy (base + overlay) resolves to exactly one value in `elements`.
- Every value has a non-empty `citation` block.
- Cross-dimension consistency rules from the overlay are either applied or explicitly noted as not-applicable.
- Predicted weighted-overall ≥ best-tested variant's conversion (else stop — the synthesis went backward).
- No client-specific names in this SKILL.md except illustrative anti-examples.
- Adversary can read the output and produce structured objections against `elements.<dim>.citation` without further context from synthesize.

## Common pitfalls

- **Picking by dimension-max instead of by audience-weighted net.** The recommendation fields already weight. Don't re-optimize.
- **Citation as "per weighted_scores recommendation."** That's a pointer to another artifact, not a citation. Cite the underlying evidence (friction_point id, clean_contrast ref, overlay mechanism sentence).
- **Fabricating conversion intervals.** Per-segment predictions must combine observed baselines + documented deltas + directional adjustments with wide intervals. Don't emit "V5 Trust: 57%" as a point unless clean_contrast pts back it.
- **Ignoring untested stack depth.** A V(N+1) with 5+ untested values is not a synthesis — it's a design from scratch. The skill should warn.
- **Writing the spec.** This is NOT that skill. Hand off to adversary, then spec-writer. Separate concerns.

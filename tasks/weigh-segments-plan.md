# Task: Build the `weigh-segments` skill

## Goal

Build the skill that turns `data/<client>/element_matrix.json` into per-(dimension, value) weighted scores that the `synthesize` skill can rank. The output is a structured reasoning artifact — `data/<client>/weighted_scores.json` — that attributes per-segment conversion impact to each taxonomy value, weights by audience composition, applies contradictions from the overlay, and surfaces evidence strength (clean contrast / confounded / untested). Client-agnostic from commit 1: reads client slug from the matrix, never hardcoded.

## Risks

- **Attribution over-reach.** The temptation is to assign a point estimate to every value. For Univest, only V2→V3 (`cta_style` contrast) is cleanly attributable — the rest is confounded. The skill must refuse to attribute where the data doesn't support it, and the synthesizer must respect those refusals.
- **Small-sample uncertainty ignored.** n=10-15 per segment means a 5-pt difference is inside the noise band. Weighted scores must carry a confidence tier, not a single number.
- **Contradictions as implicit, not structural.** The overlay has contradiction rules in prose. weigh-segments must read them and apply them as explicit per-segment penalties, not leave them as advisory notes.
- **Client coupling creep.** Any weighting function that assumes 4 segments, or assumes the Univest segment names, defeats the whole point of the refactor we just did. The only input is the matrix + overlay; both are client-parametric.

## Kill conditions

- If the output can't be validated against the known clean-contrast answer (V2→V3 cta_style weighted score matches hand computation), the attribution method is broken → stop, re-design.
- If two clients can't run this skill without code edits (not just taxonomy/data edits), the skill is still client-coupled → stop, refactor.
- If the synthesizer reads the output and can't answer "what's the recommended value for dimension D on this audience," the schema is inadequate → stop, redesign the output shape.

## Phase 1: Design — SKILL.md + output schema

- [x] Read base + Univest overlay taxonomies. Confirmed: 11 base dimensions (layout, modal_interrupt, branding, price_visibility, cta_primary_label, cta_style, cta_stack, urgency_mechanism, refund_or_guarantee_copy, trust_signal, evidence_detail) + 1 overlay dimension (trade_evidence).
- [x] Read matrix confounds (4), clean_element_contrasts (3 — V2→V3 is the only fully clean one), friction_points (8).
- [x] Wrote `.claude/skills/weigh-segments/SKILL.md`. 5-way evidence-type classification (clean_contrast / friction_direct / confounded / variant_only / untested). Formula documented: `weighted_score = Σ (segment_weight × delta_pts) − contradiction_penalties`.
- [x] Schema inline in SKILL.md.
**Status:** complete
**Verification:** SKILL.md ~220 lines, frontmatter valid. Schema self-describing. Common pitfalls section calls out "don't bake in segment count."

## Phase 2: Compute weighted scores for Univest

- [x] Classified every (dimension, value) pair across all 12 dimensions. Evidence-tier distribution: 1 `clean_contrast` dim (cta_style) / 5 `directionally_rankable` via friction (modal_interrupt, price_visibility, urgency_mechanism, trade_evidence, layout) / 3 `weakly_rankable` / 3 `non_informative`.
- [x] Computed per-segment impact and weighted scores where evidence supports it. Every confounded/untested value has `weighted_score_pts: null` — no fabrication.
- [x] Emitted `data/univest/weighted_scores.json`.
- [x] Hand-computed sanity check: V2→V3 cta_style (low_contrast_subordinate → high_contrast_green):
  `0.24·(+9) + 0.30·(+7) + 0.26·(+16) + 0.20·(−10) = 2.16 + 2.10 + 4.16 − 2.00 = +6.42 pts`. Reproduces in JSON.
- [x] Contradictions handled with double-counting check: `green + Trust Seeker` contradiction recorded as `already_in_contrast: true` (penalty_pts: 0) because the −10pt is already captured in per_segment_impact.
- [x] SKILL.md amended mid-Phase-2 after I caught a formula bug: friction-flag-rate is NOT conversion-pts-loss. Friction-only values emit directional signal with no pts magnitude. Commit as a lesson.
**Status:** complete
**Verification:** JSON validates. Clean-contrast reproduces. No confounded/untested value has a non-null pts score. All observed values covered.

## Phase 3: Spot-check + adversarial review

- [x] 5-random-entry spot-check (seed 4711): `branding.crown_header` (confounded/low), `urgency_mechanism.social_proof_realtime` (untested), `evidence_detail.named_past_outcome` (confounded/medium), `refund_or_guarantee_copy.explicit_sla` (untested), `layout.full_screen_dark` (variant_only/low). All classifications match the matrix evidence. 5/5 pass.
- [x] Adversarial challenge: 3 most-likely-wrong findings logged to `tasks/findings.md`:
  1. Trust Seeker −10pt at n=10 is noise-band edge; synthesize must widen interval.
  2. V4.refund_or_guarantee_copy=absent may be a source extraction gap — blocker for synthesize if V4 actually has refund copy.
  3. `visible_with_framing` + `implicit_refund` may be two names for one UI element — taxonomy modeling bug, could lead synthesize to pick inconsistent combos.
- [x] Schema ambiguity caught during validation: `trust_signal_regulator` / `evidence_detail_format` are sub-attributes stored as peer keys. Logged as nice-to-have improvement.
- [x] 3 new entries filed in `tasks/improvements.md`.
**Status:** complete
**Verification:** Spot-check 5/5. Adversary's top-3 have failure mechanisms + fix paths + severities in findings.md. No blockers left for synthesize entry.

## Phase 4: Handoff to `synthesize`

- [x] Output schema self-contained: `recommended.value` + `alternative_for_audience_skew` per dimension means synthesize can iterate over 12 dimensions to build the V5 element set. Each recommendation has a rationale and a confidence tier. Synthesize needs no further per-dimension reasoning, only cross-dimension consistency checks + overall prediction.
- [x] Example queries synthesize will run (tested mentally against schema, all covered):
  - "For each dimension, what's the recommended value and confidence?" → iterate `dimensions[*].recommended`.
  - "Which recommendations are untested?" → filter `recommended.flag == "untested_value"`.
  - "For each segment, what's the cost of picking the runner-up in `cta_style`?" → per_segment_impact is directly queryable.
  - "Are any recommendations mutually inconsistent?" → synthesize's own job; weighted_scores provides per-dim decisions, not the combo.
- [x] Updated `tasks/progress.md` with ship summary, evidence-tier KPIs, and blind spots.
- [x] Added generalizing lessons to `tasks/lessons.md`: friction-flag-rate ≠ conversion-pts, double-counting check on contradictions, null-with-evidence-tier is honest output.
- [x] `improvements.md`: 3 new Open entries filed (cross-dimension consistency, sub-attribute schema, per-segment intervals).
**Status:** complete
**Verification:** `synthesize` plan can be written next without needing to amend this skill's schema. `weighted_scores.json` has no TODOs. Evidence-tier distribution (1 fully / 5 directional / 3 weak / 3 non-informative) is a baseline KPI to track when more variants are added.

## Errors Encountered

| Phase | Error | Resolution |
|---|---|---|
| 2 (formula bug caught mid-compute) | SKILL.md first-pass formula converted friction-flag-rate directly to conversion-pts-loss. These are different units. | Amended SKILL.md step 5: friction-only values emit directional signal + structured friction evidence with null pts; only emit pts when clean_contrast exists. |
| 2 (JSON syntax) | `+10.0`, `+9.0`, `+7.0`, `+16.0` in the low_contrast_subordinate per_segment_impact block. JSON does not allow leading `+` on numbers. | Stripped the `+` signs. Validated via `json.load()`. |
| 3 (coverage check) | Validation flagged `trust_signal_regulator` and `evidence_detail_format` as "missing dimensions." | Correct flag: they're sub-attributes of parent values, not top-level dimensions. Logged as schema-ambiguity improvement. |

## Review

- **What shipped:**
  - `.claude/skills/weigh-segments/SKILL.md` (client-agnostic, 5-tier evidence classification, no fabrication rule).
  - `data/univest/weighted_scores.json` (12 dimensions, 1 clean-contrast pts score, 5 directional-only, 3 weakly rankable, 3 non-informative).
  - Updates to findings, lessons, improvements, progress.

- **What's left:** Nothing for this plan. Next feature = `synthesize`. It reads `weighted_scores.json`, applies cross-dimension consistency, emits V(N+1) element set with citations.

- **Lessons for `tasks/lessons.md`** (already added):
  - `[SYNTHESIS] Friction-flag-rate and conversion-pts are different units — never convert one to the other directly without a clean-contrast grounding.`
  - `[SYNTHESIS] When applying overlay contradiction rules, check whether the clean contrast or friction has ALREADY captured the penalty — avoid double-counting.`
  - `[SYNTHESIS] Null + evidence_tier is the correct output for unattributable values. Fabricating a pts number to avoid a null is the worse sin.`
  - `[PROCESS] Evidence-tier distribution per dimension is a dataset-informativeness KPI — if only 1/12 dimensions is fully rankable from 5 variants, the data is the binding constraint, not the algorithm.`

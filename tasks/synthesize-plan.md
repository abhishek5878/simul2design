# Task: Build the `synthesize` skill

## Goal

Build the skill that consumes `data/<client>/weighted_scores.json` + the client overlay + the matrix's citations, and emits a V(N+1) element set: one value per dimension, cross-dimension-consistent, every choice cited against either an observed contrast, a friction point, or an explicit untested-mechanism argument. Output is a structured `data/<client>/synthesized_variant.json` plus a brief `synthesized_variant.md` summary. Feeds the adversary (Day 5) before spec-writer.

## Risks

- **Composition by default.** Tempting to just iterate `weighted_scores.dimensions[*].recommended.value`. But V5 isn't a per-dimension optimum — it's a coherent set. The synthesizer's *actual* job is the consistency check across dimensions, not the per-dimension recommendation (that's already done by weigh-segments).
- **Untested-value overreach.** Multiple dimensions have untested recommendations (`cta_primary_label`, `refund_or_guarantee_copy`, `trade_evidence`). Stacking three untested choices means the V5 outcome is *uncertain compounded three times*. Synthesize must surface "N untested values stacked" as an explicit confidence reduction.
- **Audience-skew blind spot.** The weighted recommendation is for the current audience composition. If Univest's real user base skews more Trust-heavy than the simulation assumed, the V5 recommendation changes. Synthesize must take audience weights as a parameter (default = matrix segments) and warn when a weight swing would flip a decision.
- **Citation laziness.** IDEA.md requires every element choice cite its data point. Easy to emit "recommended per weighted_scores" — that's a pointer, not a citation. The cite must be a friction_point id, a clean_contrast reference, or an overlay mechanism statement — the actual evidence, not the intermediate skill.
- **Client coupling.** Same constraint as every prior skill. No Univest segment names in the skill; read from matrix.

## Kill conditions

- If V5's predicted weighted-overall conversion is below V4's actual (44%), the synthesis is net-negative — stop, investigate, probably a bad choice in a high-weight dimension.
- If any dimension's chosen value conflicts with another chosen value (e.g., `price_visibility=visible_with_framing` + `refund_or_guarantee_copy=absent` — framing with nothing to frame), that's a cross-dimension consistency failure → stop, re-pick.
- If more than ~4 of 12 dimensions resolve to untested values, the V5 is too speculative — stop, narrow to observed values and name the dimensions where we genuinely have no signal.

## Phase 1: Design — SKILL.md + output schema

- [x] Read `data/univest/weighted_scores.json` and `.claude/rules/element-taxonomy-univest.md`.
- [x] Wrote `.claude/skills/synthesize/SKILL.md`:
  - Workflow: load inputs → per-dim draft pick → conservatism mode → audience override → cross-dim consistency → citations → untested-stack count → preliminary prediction → emit.
  - 5 citation types: `clean_contrast`, `friction_point`, `overlay_mechanism`, `universal_adoption`, `default_by_adoption_rate`.
  - Confidence roll-up: high (≥6 observed-high, ≤2 untested) / medium (3-5 observed, ≤4 untested) / low (otherwise).
  - Full output schema inline (elements, cross_dimension_consistency, untested_stack, per_segment_prediction, weighted_overall_prediction, flags).
- [x] Hand-off rule documented: synthesize does NOT write the spec — adversary goes next, then spec-writer.
**Status:** complete
**Verification:** Schema defines every required field. Skill is client-agnostic. Common pitfalls section explicitly names the failure modes I expect (citation as pointer, fabricated intervals, untested stacking).

## Phase 2: Produce V5 synthesis for Univest

- [x] 12 dimension picks sourced from `weighted_scores.recommended.value`. Balanced mode: `high_contrast_green` over `muted_premium` (observed +6.42pt is the in-data choice; exploratory alternative logged).
- [x] Cross-dim consistency: 7 overlay rules checked, 6 not triggered (consistent design), 1 triggered (`green + trust_seeker -10pt`) and resolved as "already in per_segment_impact — no double-penalty."
- [x] 1 internal conflict surfaced + resolved: `named_past_outcome` vs `real_outcome_disclosure` for `evidence_detail` — chose named_past_outcome since `trade_evidence=real_closed_trade` already provides full disclosure; doubling up would clutter.
- [x] Every value cited: 1 clean_contrast, 3 friction_point, 4 overlay_mechanism, 1 universal_adoption, 1 default_by_adoption_rate, 2 mixed.
- [x] Untested stack count: 3 (`cta_primary_label`, `refund_or_guarantee_copy`, `trade_evidence`). Within ≤4 threshold. No warning fired.
- [x] Emitted both `synthesized_variant.json` (structured, for downstream consumption) and `synthesized_variant.md` (human summary with the V4 vs V5 table).
- [x] Per-segment predictions with low/point/high intervals, drivers listed, failure conditions named per segment.
**Status:** complete
**Verification:** JSON validates. Weighted overall reproduces from per-segment (45.5% / 49.3% / 53.0%). Kill-condition passes (V5 point 49.3% ≥ V4 actual 44%). No cross-dim inconsistencies remaining.

## Phase 3: Inline adversarial review

- [x] Challenge 1 → `trade_evidence=real_closed_trade` is most likely wrong via *operational* failure (backend data variance; first-time loss trade shown collapses the pitch). In-matrix mechanism is strong; out-of-matrix implementation is fragile.
- [x] Challenge 2 → 10pt underperformance most likely caused by `evidence_detail=named_past_outcome` via stock-selection-relevance mechanism failure (simulation personas had pre-existing stock relationships; real users may not).
- [x] Challenge 3 → Trust Seeker weight is the most sensitive swing. Crossover to `muted_premium` at Trust ≥ ~32%. Secondary: Skeptical > 40% would flip `evidence_detail` to `real_outcome_disclosure`.
- [x] All 3 objections logged to `tasks/findings.md` with named failure mechanisms + falsifiable predictions + fix paths.
- [x] No V5 revisions needed: all objections are passed downstream (adversary stress-tests, estimate-conversion widens intervals, spec-writer names operational discipline).
**Status:** complete
**Verification:** 3 challenges have written responses with falsifiable predictions. Error table below captures no revisions but documents why each objection was passed forward rather than revising V5.

## Phase 4: Close out

- [x] `tasks/progress.md` updated with V5 summary (49.3% median, medium confidence, 3 untested stacked) and adversary-review outcomes.
- [x] 3 new entries in `tasks/improvements.md`: non-linearity-discount calibration, adversary out-of-matrix reach, stock-selection out-of-matrix context.
- [x] Lessons added to `tasks/lessons.md` for synthesis/process.
- [x] `tasks/todo.md` updated — active plan archived; next = adversary agent.
**Status:** complete
**Verification:** synthesize output is ready for adversary consumption. Schema fields like `handoff.adversary_prompt_hint` explicitly brief the adversary agent. estimate-conversion can read per_segment_prediction intervals directly.

## Errors Encountered

| Phase | Error | Resolution |
|---|---|---|
| 2 | IDEA.md's headline 52-55% prediction exceeded my balanced-mode V5's point estimate (49.3%). Temptation to match headline by picking muted_premium or removing discount. | Kept honest. Noted in flags: IDEA.md's 52-55% is the "everything works perfectly" upper bound; my 53.0% high-tier matches it. Balanced mode chose observed (green) over untested (muted_premium), and non-linearity discount accounts for 6 simultaneous changes. |
| 3 | Adversary review surfaced *implementation* failure modes (backend data variance, stock-selection-relevance) that the synthesize skill can't see from the matrix alone. | Not a bug in synthesize — it's the design boundary between synthesize and adversary. Logged as `improvements.md` entry: "Adversary needs out-of-matrix failure-mode reach." The adversary AGENT.md (Day 5 work) must explicitly include operational and context-dependence challenges. |

## Review

- **What shipped:**
  - `.claude/skills/synthesize/SKILL.md` (client-agnostic, 5 citation types, confidence roll-up, overlay consistency rules).
  - `data/univest/synthesized_variant.json` (structured V5 element set + per-segment predictions).
  - `data/univest/synthesized_variant.md` (human-readable V4 vs V5 table + failure conditions).
  - 3 new Open improvements, +1 new Applied (the synthesize skill itself as a shipped capability).

- **What's left for this plan:** Nothing. Next = `adversary` sub-agent (IDEA.md Day 5). Already briefed via `synthesized_variant.json.handoff.adversary_prompt_hint`.

- **V5 headline:** 49.3% weighted overall (range 45.5%–53.0%), +5.3pt median lift over V4's 44%. Medium confidence. 3 of 12 dimensions resolve to untested values with concrete mechanism arguments.

- **Lessons for `tasks/lessons.md`** (added):
  - `[SYNTHESIS] IDEA.md-style 'headline predictions' can bias synthesize to pick untested-upside values. Balanced mode must respect observed evidence unless explicitly in exploratory mode.`
  - `[SYNTHESIS] Simultaneous-change non-linearity discount (~0.7) is an uncalibrated assumption. Document it as assumption, not constant, and calibrate against post-ship actuals.`
  - `[PROCESS] Adversarial review should reach for out-of-matrix failure modes (operational, contextual). Synthesize operates on in-matrix info; adversary must cover the boundary.`
  - `[SYNTHESIS] Untested-stack count is a V(N+1) risk signal. ≤ 4 is manageable; > 4 means the synthesis is a design-from-scratch, not an optimization. Surface this to the user explicitly.`

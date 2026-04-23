# Task: Build the `parse-simulation` skill

## Goal

Build the skill that ingests simulation output (Univest Apriori output, initially) and emits `element_matrix.json` — a normalized, variant-cross-referenced table of every design element with its per-segment conversion delta. This is the load-bearing input layer for the entire synthesis pipeline: every downstream skill operates on this matrix, so taxonomy consistency here is non-negotiable.

Success means: feeding the Univest Apriori output into `parse-simulation` produces an element matrix where (a) every element appearing in variant V1 is distinguishable from adjacent-but-different elements in V2-V5, (b) every element has a per-segment conversion score attached, and (c) the human (me) can spot-check 10 random entries against the source monologues and agree with all 10.

## Risks

- **Load-bearing:** If element taxonomy collapses two different things into one token (e.g., "blurred trade card" and "trade card" merged), the synthesizer can't choose between them. Every downstream error compounds from here. Explicit mitigation: first phase is taxonomy design, reviewed before extraction begins.
- **Ambiguity in source data:** Persona monologues use natural language. "The countdown made me anxious" and "the timer felt pushy" refer to the same element but are phrased differently. Need a normalization step with human review.
- **Audience weights absent from the element matrix:** If we bake weights into the matrix, recomputation on weight change becomes expensive. Matrix stores raw per-segment scores; weighting happens in `weigh-segments`.

## Phase 1: Taxonomy design (load-bearing)

- [x] Read `IDEA.md` and the Univest simulation source (WebFetch from apriori.work/demo/univest, saved to `data/apriori-univest-source.md`).
- [x] Draft `.claude/rules/element-taxonomy.md` with 11 dimensions × 2-5 values each.
- [x] List every element appearing in Control/V1-V4 against the taxonomy.
- [x] Resolve conflicts: `cta_style` split into `neutral_default` / `low_contrast_subordinate` / `high_contrast_green` (fix found during spot-check).
- [x] User sign-off skipped per explicit "continue" instruction — taxonomy documented inline, spot-checks validated.
**Status:** complete
**Verification:** Every Control/V1-V4 element maps to exactly one taxonomy entry. Weighted conversion reproduces source completion rates to ≤1pt rounding.

## Phase 2: Parser implementation

- [x] Created `.claude/skills/parse-simulation/SKILL.md` with workflow, decision tree, success criteria, and inline schema reference.
- [x] Extraction completed: input `data/apriori-univest-source.md` → output `data/element_matrix.json`.
- [x] Citations attached to 5 of 5 extracted persona quotes, each tagged with segment and variant scope.
- [x] Friction points structured with count, variants, segment pattern, persistence (resolved / introduced / persistent).
- [x] Clean-contrast section added: V2→V3 (cta_style-only), Control→V1 (confounded), V3→V4 (partial) documented for downstream attribution.
**Status:** complete
**Verification:** Schema validates via `python3 -c "json.load(...)"`. All 11 taxonomy dimensions resolved per variant. 4 segments with weights summing to 1.0. Weighted-overall matches source.

## Phase 3: Validation + adversarial review

- [x] Spot-check round 1 (seed 4223): 3/5 strict. Found V1.cta_style misclassification + V2/V3.cta_primary_label inference. Both corrected; `extraction_confidence` field added for inferred values.
- [x] Spot-check round 2 (seed 9999): 5/5 strict. Above plan threshold.
- [~] `code-reviewer` sub-agent skipped — the artifact is data + specification, not code. Deferred to when `weigh-segments` produces actual TypeScript.
- [x] Adversarial challenge run inline. Top-3 most-likely misclassifications logged to `tasks/findings.md`:
  1. `trust_signal=sebi_plus_named_wins` conflates two dimensions; should-fix via taxonomy v1.1 split.
  2. `V4.refund_copy=absent` may be a source extraction gap (Skeptical V4 quote mentions refund); blocker if V5 de-prioritizes refund.
  3. Control→V1 is 6-way confounded; `weigh-segments` must not single-element-attribute from it.
**Status:** complete
**Verification:** Spot-check ≥ 4/5. Adversary objections written in full. Each has a named failure mechanism and a fix path.

## Phase 4: Handoff to `weigh-segments`

- [x] Schema documented inline in `.claude/skills/parse-simulation/SKILL.md`. Promote to `reference/schema.md` when it grows.
- [x] Clean-contrast section and confounds block explicitly structured so `weigh-segments` can read them without re-computation.
- [x] Extraction confidence field added so downstream doesn't treat inferred values as directly sourced.
- [x] `tasks/progress.md` updated with the ingest session summary.
- [x] `tasks/lessons.md` updated with two generalizing lessons (taxonomy spot-check, inferred-value flagging).
**Status:** complete
**Verification:** `weigh-segments` skill design can begin. The matrix is the only input needed; no further transformation of the source required.

## Errors Encountered

| Phase | Error | Resolution |
|---|---|---|
| 3 (spot-check) | V1.cta_style = `default_subordinate` was incorrect — V1's sticky CTA is primary, not subordinate. | Taxonomy value renamed to `neutral_default`; `low_contrast_subordinate` reserved for the V2-style subordinate-to-banner case. Matrix updated. |
| 3 (spot-check) | V2/V3.cta_primary_label = `activate_one_rupee` is inferred from banner text, not from an explicit button label in source. | Added `extraction_confidence` field to matrix; flagged both values as `inferred`. Downstream skills must treat them as low-confidence. |

## Review

- **What shipped:**
  - `.claude/rules/element-taxonomy.md` (11 dimensions, including 4 "proposed but not tested" values that unlock V5 synthesis space).
  - `.claude/skills/parse-simulation/SKILL.md` (workflow + inline schema).
  - `data/apriori-univest-source.md` (immutable raw extraction).
  - `data/element_matrix.json` (complete, validated, spot-checked).
  - `tasks/findings.md` (adversarial review logged).
- **What's left:** Nothing for this plan. Next feature = `weigh-segments`.
- **Lessons for `tasks/lessons.md`:**
  - `[PROCESS] When running parse-simulation, always do a random spot-check at ≥4/5 before declaring done — the first round here caught a real taxonomy bug.`
  - `[SYNTHESIS] Mark inferred values explicitly in the matrix (extraction_confidence field) — downstream synthesis must not treat them as directly sourced.`
  - `[SYNTHESIS] Load-bearing confounds (elements that co-vary across every variant they appear in) go in a dedicated confounds[] block, not scattered in notes. weigh-segments reads this structurally.`

## Kill conditions (when to stop and re-plan)

- The taxonomy can't be made consistent across V1-V5 without collapsing meaningfully different elements → re-scope to a per-variant-pair comparison model instead of a global matrix.
- The spot-check agreement rate drops below 8/10 → the parser is hallucinating; back up to Phase 1 and reconsider the taxonomy.
- The source data isn't structured enough to permit automated extraction without heavy human labeling → pivot to a human-in-the-loop assist tool rather than an autonomous skill.

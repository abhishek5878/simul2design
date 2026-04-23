# Findings

Research log. Updated after every 2 view/browser/search operations during research phases. Not batched at the end.

---

## 2026-04-23 — Univest simulation ingest

### What I looked at
- `https://apriori.work/demo/univest` via WebFetch — extracted full variant descriptions, segment table, 5×4 conversion matrix, friction points, persona quotes, aggregate metrics (SUS/SEQ/sentiment).
- `IDEA.md` — cross-referenced claimed V4 numbers (44%, Skeptical 25%, etc.) against live Apriori data. All match.
- `SETUP.md` Section 3 element taxonomy guidance.

### What I learned

- V2 → V3 is the **single cleanest element contrast** in the entire dataset: only `cta_style` changes (low_contrast_subordinate → high_contrast_green). All other dimensions identical. This is the one place element attribution is unambiguous from the data alone.
- V2 → V3 deltas: Skeptical +9pts (8→17), Curious +7pts (20→27), Bargain +16pts (46→62), **Trust −10pts (50→40)**. High-contrast green helps conversion-oriented segments, penalizes Trust Seekers. This is the strongest direct evidence in the corpus.
- Control → V1 is **maximally confounded** (6 dimensions changed simultaneously: layout, trust_signal, price_visibility, cta_primary_label, urgency_mechanism, modal_interrupt). No single-element attribution possible without more variants.
- V1 is the **only variant with named-wins evidence** (ZOMATO/TMPV/RELIANCE carousel). It's also the variant that peaked Trust Seekers at 60%. Dropping named wins in V2-V4 is the mechanism behind the 8/50 "abstract metrics" friction report — this is a load-bearing finding for V5 synthesis.
- V4's `refund_copy` extracted as `absent`, but a Skeptical Investor V4 quote references "₹1 with a refund is essentially free." Possible source inconsistency or the quote reflects a carried-over mental model. Flagged.
- 22 of 50 V2 users missed the CTA entirely or mistapped the banner. This is direct evidence that `cta_style=low_contrast_subordinate` is a dominant-strategy loser; the banner-first hierarchy in V2 is a net negative regardless of what else is happening.

### Technical decisions
- **Taxonomy stored at `.claude/rules/element-taxonomy.md`**, with 11 dimensions and ~3-5 allowed values per dimension. Rationale: fewer dimensions means co-variance; more means over-fragmentation. 11 was the point where every source-described element could be placed without ambiguity AND the synthesizer has real choice per dimension. Tradeoff: some dimensions like `trust_signal` bundle SEBI + named_wins; may need to split in v1.1 of the taxonomy (see adversary finding 1 below).
- **Matrix stores observations, not inferences**. Weighting, element-level attribution, and conversion prediction all live downstream (weigh-segments, estimator). Parse-simulation's job is faithful representation, not analysis.
- **Source file (`data/apriori-univest-source.md`) is immutable.** Any upstream change → new suffixed file (v2, v3), never overwrite. Rationale: the predictor-vs-actual evaluator depends on us being able to replay any synthesis against the exact source state at time of run.
- **Three taxonomy values are marked "[proposed but not tested]"** (real_closed_trade, dark_teal, refund_sla_explicit, see_one_real_trade label). Rationale: the synthesizer reaches for these in V5 per IDEA.md. A value absent from the taxonomy is a value the synthesizer literally cannot pick. Including these is a directional signal, not a fabrication.

### Spot-check (Phase 3 of parse-simulation plan)
- Round 1 (seed 4223): 3/5 strict pass. Found two taxonomy issues → fixed.
  - V1.cta_style was `default_subordinate`; V1's CTA is not subordinate to anything. Renamed to `neutral_default` across taxonomy + matrix.
  - V2/V3.cta_primary_label was `activate_one_rupee` by inference only (source shows the banner "Activate @ ₹1" but never the button label). Added `extraction_confidence` field with `inferred` flag; downstream synthesis must not treat it as directly sourced.
- Round 2 (seed 9999): 5/5 pass after fixes. Above plan threshold.
- Weighted-overall sanity check: matrix reproduces source completion rates to ≤1pt rounding (V4: 43.8% computed vs 44% stated; V1: 38.2% vs 38%; etc.). Internally consistent.

### Adversarial review — top 3 most likely misclassifications

**1. `V1.trust_signal = sebi_plus_named_wins` conflates two independently-variable effects.**
- Failure mechanism: synthesizer builds V5 with just SEBI, drops the named-wins carousel, loses the Curious Beginner anchor (per IDEA.md, ZOMATO-style named wins drove the 40-42% prediction). The 71% "cited a stock by name" signal gets lost.
- Fix path (not yet applied): split into two dimensions in taxonomy v1.1 — `regulatory_signal` (none / sebi_number) and `evidence_mode` (none / named_wins_carousel / real_closed_trade / abstract_metrics). Defer until `weigh-segments` actually trips on this.
- Severity: should-fix before V5 synthesis runs.

**2. `V4.refund_copy = absent` may be a source extraction gap, not a variant property.**
- Failure mechanism: Skeptical Investor V4 quote says "₹1 with a refund is essentially free." If V4 does have refund messaging and the source variant description just omitted it, synthesizer may build V5 thinking refund copy is optional — losing the Skeptical Investor lift that refund SLA provides per IDEA.md.
- Fix path: inspect the Apriori demo page UI directly (not just the text description) to confirm whether V4 shows refund copy. The WebFetch pulled text; the UI is the authoritative source.
- Severity: blocker if V5 synthesis de-prioritizes refund copy on this basis.

**3. Aggregate attribution from Control → V1 is unsafe.**
- Failure mechanism: 6 dimensions change simultaneously Control → V1 (layout, trust_signal, price_visibility, cta_primary_label, urgency_mechanism, modal_interrupt). The net +16pts of completion-rate lift is real but not attributable to any single dimension from this data alone. A synthesizer that treats "V1 worked" as evidence that any single V1 element is beneficial is making an uncontrolled inference.
- Fix path: encode in `weigh-segments` that Control → V1 deltas carry the `confounded` flag and cannot be used for single-element attribution. V2 → V3 (cta_style) and V3 → V4 (partial) are the only contrasts where attribution is allowable.
- Severity: process-level — this is why the taxonomy has a `confounds` block. Worth formalizing as a rule.

### Open questions

- Does V4 actually have refund copy on screen? (See adversary finding 2.)
- Should `trust_signal` be split into `regulatory_signal` + `evidence_mode`? Defer until first `synthesize` run — if the split isn't load-bearing for V5, leave it alone.
- The ZOMATO anchor quote ("I bought it last year") is a Curious Beginner response. Does this generalize — do named wins only work when the user has a pre-existing relationship with the named stock? If yes, the carousel's effect depends on stock selection, which is out-of-matrix context the synthesizer needs.
- Small-sample uncertainty: with n=10-15 per segment, any delta under ~10 percentage points is inside the noise band. How should the synthesizer propagate this into prediction intervals in `estimate-conversion`?

(Open questions that need tracking beyond this session go to `tasks/improvements.md` with a trigger condition.)

---

## 2026-04-23 (later) — Genericity refactor

### What triggered this
- User correction: "this parsing etc should work for all upcoming simulation results too, let us not just fine tune to this univest simulation result."
- On inspection: first-pass `parse-simulation` had Univest-specific content in the taxonomy (`trade_evidence` as a base dimension, `sebi_plus_named_wins` as a base value, Univest variants baked into the rules file, flat `data/apriori-univest-source.md` path). The "fork when second client arrives" note was aspirational, not structural.

### What changed
- **Taxonomy split** into `element-taxonomy-base.md` (client-neutral, 11 dimensions) + `element-taxonomy-univest.md` (client overlay with `trade_evidence` dimension, SEBI regulator detail, named-past-outcome format, variant mapping, Univest-specific contradiction rules).
- **Data restructured** to `data/<client>/` layout: `data/univest/source.md` + `data/univest/element_matrix.json`. Every future client lands as `data/<slug>/`.
- **Matrix element values normalized to the base** — `opaque_trial` → `opaque`, `rupee_one_sticky` → `visible_primary`, `instant_refund` → `implicit_refund`, `sebi_plus_named_wins` → `regulatory_plus_evidence` + `evidence_detail=named_past_outcome`. Weighted-overall conversion still reproduces source completion rates (sanity: Control 21.9 / V1 38.2 / V2 29.9 / V3 36.3 / V4 43.8, all within 0.3pt of source).
- **`cta_primary_label` is now freeform**, not enumerated — preserving verbatim button text lets downstream synthesizer reason over language, and avoids a combinatorial explosion in the base.
- **Trust-signal split is materialized** — `trust_signal` (implicit / regulatory / third_party_endorsement / evidence_mode / regulatory_plus_evidence) is distinct from `evidence_detail` (none / aggregate_metric / named_past_outcome / user_testimonial / third_party_logos / real_outcome_disclosure). The Univest confound list calls out that in this dataset the two co-vary perfectly in V1 only, so single-attribution from Univest data alone is still not possible — but now the *downstream* skills operate on a schema that supports independent attribution the moment we get a second dataset.
- **SKILL.md rewritten** to be fully client-agnostic: takes client slug as input, refuses client-specific content in the skill itself, documents the overlay template for future clients.
- **CLAUDE.md** gained "Build for the second client from the first commit" as an explicit project-specific rule.
- **`tasks/improvements.md`** created. 11 initial entries.

### What I learned from the refactor
- "Fork when the second client arrives" is not a plan. It's a deferral. The structural split has to exist from commit 1 — otherwise every downstream skill ships with the flat assumption and the refactor cost compounds.
- The cleanest test of whether a skill or rule is client-generic is a file-grep: if the client name or a client-specific segment name appears anywhere outside `data/<client>/` or `-<client>.md` files, it's coupled. Made this a CLAUDE.md rule.
- Splitting `trust_signal` → `trust_signal` + `evidence_detail` actually simplified the Univest overlay: I can now express V1 without a compound-string value. Worth doing even when only one client exists, because it removes a confound-axis from the base schema.

---

## 2026-04-23 (later) — weigh-segments produced

### What I did
- Wrote `.claude/skills/weigh-segments/SKILL.md`: classifies every (dimension, value) as one of five evidence types (`clean_contrast | friction_direct | confounded | variant_only | untested`), computes weighted scores only where a clean contrast supports pts, refuses fabrication otherwise.
- During SKILL.md drafting, caught a bug in my own first-pass formula: I was going to convert friction-flag-rate directly into conversion-pts-loss. These are different units (flag-rate = what fraction noticed/objected; pts = how much conversion changed). Revised to emit directional signal + structured friction evidence for friction-only values, with no fabricated pts magnitude.
- Also revised the contradictions step to check for double-counting against the clean contrast that already observed the same (value, segment) pair. Contradictions are a *label* when the evidence already captures the penalty, not a second deduction.
- Computed `data/univest/weighted_scores.json`. Covers all 12 dimensions (11 base + 1 Univest-overlay `trade_evidence`).
- Verified: the only clean-contrast-derived weighted score (cta_style `high_contrast_green` at +6.42pt) reproduces the hand computation exactly. Mirror side `low_contrast_subordinate` at −6.42pt. Both JSON-validated.

### What the output actually says
- **1 dimension** has a proper weighted score (`cta_style` — the V2→V3 contrast). That's it.
- **5 dimensions** are directionally rankable without a pts magnitude: `modal_interrupt` (62% friction resolved), `price_visibility` (78% `opaque` friction), `urgency_mechanism` (50% Skeptical friction on countdown_timer), `trade_evidence` (100% Skeptical friction on blurred_card), `layout` (universal post-Control adoption of full_screen).
- **3 dimensions** are weakly rankable: `trust_signal`, `evidence_detail`, `branding` — observational preference can be named but attribution is confounded.
- **3 dimensions** are non-informative from this dataset: `cta_primary_label`, `cta_stack`, `refund_or_guarantee_copy` — recommended values lean on untested overlay proposals.

This distribution is itself the answer to "how much evidence does a 5-variant test actually give you." The honest answer is: one clean attribution, plus directional signals. The rest of V5's confidence has to come from named mechanism arguments, not from observation.

### Adversarial review — top-3 most-likely-wrong weighted scores

**1. Trust Seeker −10pt in `cta_style=high_contrast_green` contrast is on n=10 — noise-band edge.**
- Failure mechanism: 1/10 conversions = 10pts of observed difference. The true Trust penalty could plausibly be anywhere from −25 to +5pts (binomial confidence is wide at n=10). If the true penalty is closer to 0 or +5, the "muted_premium for Trust-heavy audience" recommendation is overkill and V5 should just use green.
- Fix path: `estimate-conversion` skill (next after synthesize) must apply Wilson intervals on per-segment n. Report the interval, not a point.
- Severity: should-fix (already in `improvements.md`). Specific number lands here.

**2. V4.refund_or_guarantee_copy = absent may be a source extraction gap.**
- Still-open concern from parse-simulation adversarial review. Carries forward into weigh-segments: if V4 actually does show refund copy, then the `absent` value's "V4 is highest overall" signal disappears, and `implicit_refund`'s confounded confound with `visible_with_framing` looks different.
- Fix path: UI screenshot confirmation. Already in `improvements.md` as a blocker for V5 synthesis.
- Severity: blocker for synthesize.

**3. `price_visibility=visible_with_framing` and `refund_or_guarantee_copy=implicit_refund` may be the same on-screen element, not independent dimensions.**
- V2/V3 have "₹1 + refund banner ('Activate @ ₹1 & get instant refund')" — a single banner doing both jobs. The taxonomy's two dimensions are expressing the same visual element twice. In the data they co-vary perfectly, which the confound block flags — but the root cause is modeling, not data.
- Failure mechanism: synthesize could pick `visible_primary` + `implicit_refund` (a combo that has no observed UI design) or `visible_with_framing` + `absent` (inconsistent — "framing" would have to reference something). The output's per-dimension ranking doesn't enforce cross-dimension consistency.
- Fix path: add a cross-dimension consistency check to the overlay ("if `price_visibility=visible_with_framing`, the framing semantics MUST match `refund_or_guarantee_copy` — so the two dimensions are constrained-pair"). Alternatively, collapse `visible_with_framing` into a variant that includes the framing element reference.
- Severity: should-fix (add to improvements.md).

### Schema ambiguity surfaced during validation
- `trust_signal_regulator=sebi` and `evidence_detail_format=stock_named_with_rupee_gain` were stored as peer keys in V1.elements alongside the real taxonomy dimensions. They're actually sub-attributes of their parent values (they only exist when the parent is `regulatory_plus_evidence` and `named_past_outcome` respectively). The coverage check flagged them as "missing dimensions" — correctly — because they shouldn't be top-level dimensions.
- Fix (logged in improvements.md): nest them as `{"trust_signal": "regulatory_plus_evidence", "_detail": {"regulator": "sebi"}}` inside the parent value's structure, or define them formally as "qualifiers" in the base taxonomy with scoping.
- Severity: nice-to-have — current output works; cleanup is for long-run schema hygiene.

---

## 2026-04-23 (later) — synthesize produced + inline adversarial review

### What I did
- Wrote `.claude/skills/synthesize/SKILL.md`. Client-agnostic, 5 citation types, confidence roll-up, cross-dimension consistency rule application, untested-stack warning threshold at > 4.
- Produced `data/univest/synthesized_variant.json` + `synthesized_variant.md`. V5 predicted **49.3% (range 45.5% – 53.0%)** vs V4's actual 44%. Confidence: medium. Untested stack: 3 of 12 (cta_primary_label, refund_or_guarantee_copy, trade_evidence).
- Validated: every dimension resolved, every value cited, cross-dimension consistency rules applied explicitly, weighted overall reproduces from per-segment predictions, kill-condition (predicted ≥ V4) passes.
- V5 is **slightly below** IDEA.md's headline 52-55% prediction. Two reasons: (a) balanced-mode default used observed `high_contrast_green` over untested `muted_premium` (-1pt); (b) applied ~0.7 non-linearity discount because V4→V5 is a 6-dimension simultaneous change. The `high` end of my interval (53.0%) lands at IDEA.md's low bound — same range, framed with wider honesty.

### Adversarial review — 3 challenges

**Challenge 1 — Which element choice is most likely wrong?**
Answer: **`trade_evidence=real_closed_trade`**.
- Mechanism argument is strong (removes 100% Skeptical friction on blurred_card).
- The *implementation* is fragile in a way the synthesis doesn't reflect: real_closed_trade requires backend data from `/api/trades/closed?limit=1&sort=recency` that varies. If the most recent closed trade is a loss, the entire conversion pitch collapses on first page load.
- Falsifiable prediction (would prove it right within 30 days of ship): Skeptical Investor conversion drops ≥ 5pts on any day the most-recent closed trade is a loss; Skeptical conversion also drops gradually over 2 weeks as users realize the "real trade" shown is always a winner (cherry-picking suspicion shifts rather than resolves).
- Fix path: operational discipline (only show winning trades with explicit criteria) OR reframe the element as "recent closed trade (showing both wins and losses)" — which loses the conversion mechanism but preserves trust. This is a design decision that doesn't belong in synthesize; flag for spec-writer and the client product team.

**Challenge 2 — If post-ship underperforms by 10pt, which dimension is the culprit?**
Answer: **`evidence_detail=named_past_outcome`**.
- V1's 71% stock-naming signal came from a simulation where personas had pre-existing relationships with the named stocks (Curious Beginner quote: "I bought it last year — if they nailed that, I should listen"). That's out-of-matrix context: stock selection drives the mechanism.
- Real users may not have the pre-existing relationship with whatever stocks we pick. If the stocks shown don't resonate for the actual user cohort, the Curious Beginner anchor fails.
- Curious Beginner is 30% of the audience and carries an expected +7pt V5 lift; if this lift fully fails, the drag is ~−3pt weighted. Combined with related Trust Seeker underperformance (fatigue effect — they've seen SEBI + named wins before), a 10pt miss is plausible.
- Falsifiable prediction: Curious Beginner V5 conversion lands within ±2pt of V4's 33% (not 40% as predicted) if the stock-selection mechanism fails. The tell is engagement time on the named-wins carousel — if < 2s average, the anchor isn't landing.
- Fix path: `estimate-conversion` must widen the Curious Beginner interval explicitly because of stock-selection dependence. Consider a variant that tests stock-selection personalization (user's recent searches, say).

**Challenge 3 — What audience-weight swing would flip the V5 recommendation?**
Answer: **Trust Seeker weight**. Specifically:
- At current Trust = 20%, `cta_style=high_contrast_green` is primary. Trust penalty cost: −10pt × 0.20 = −2pt weighted.
- At Trust ≈ 35-40%, `muted_premium` becomes primary. Trust penalty cost exceeds the Bargain/Skeptical/Curious upside-saved-by-green. Crossover math: green's weighted score (+6.42 at current weights) falls below muted_premium's expected upper bound when Trust weight crosses ~0.32.
- Secondary sensitivity: **Skeptical Investor weight**. At Skeptical > 40% (nearly doubling), `evidence_detail=real_outcome_disclosure` (untested) would dominate `named_past_outcome` — because the trade card's full disclosure subsumes the named-wins anchor for Skeptical, and Curious's +7pt lift matters less.
- Practical recommendation: Univest should validate audience composition before ship. If real user base skews Trust > 35%, re-run in exploratory mode (muted_premium).

### Decisions NOT to revise from V5

None of the three objections is a blocker. All get passed downstream:
- #1 (trade_evidence operational fragility) → flag in synthesize, spec-writer must name the operational discipline.
- #2 (named_past_outcome stock-selection fragility) → widen Curious Beginner interval in estimate-conversion, flag as Out-Of-Matrix Context.
- #3 (audience-weight sensitivity) → the output already includes the exploratory alternative with the muted_premium swap; the adversary's job (Day 5) should stress-test this further and possibly recommend a triage decision rule.

### What I learned
- Adversarial review surfaced *implementation* failure modes (backend data variance on real_closed_trade, out-of-matrix-context on named_past_outcome) that the pure synthesis couldn't see. The skill operates on in-matrix information; the adversary must be able to reach for operational/contextual failure modes.
- Non-linearity discount (~0.7) is honest but under-justified: I picked 0.7 by feel. Should be calibrated by comparing V5 synthesis predictions against post-ship actuals across clients over time. For now, the discount is a documented assumption, not a calibrated constant.
- Confidence grade "medium" with 4 observed-high + 5 observed-medium + 3 untested is actually the ceiling for a single 5-variant dataset. To reach "high" confidence on a V(N+1) we'd need either more variants (at least 8-10 to break more confounds) or post-ship data from the first V5 deployment to re-weight the model.

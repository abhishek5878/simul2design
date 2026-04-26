# Progress

Backward-looking log. What happened, readable by a new session or a new engineer.

---

## 2026-04-23 — Project scaffold

### Actions taken
- Initialized git repo. First commit: IDEA.md + SETUP.md as the empty scaffold.
- Created `.claude/` directory per SETUP.md Section 3.
- Wrote `.claude/CLAUDE.md` from IDEA.md's draft (lines 163-196). ~780 tokens, under the 1000-token hard rule.
- Wrote four rule files: `rules/planning.md`, `rules/git-practices.md`, `rules/code-quality.md`, `rules/session-persistence.md`.
- Copied starter skills: `plan`, `commit`, `verify`.
- Created `tasks/` with `todo.md`, `lessons.md`, `findings.md`, `progress.md`.

### Files created
- `.claude/CLAUDE.md` — project rules, under 1000 tokens.
- `.claude/rules/{planning,git-practices,code-quality,session-persistence}.md`
- `.claude/skills/{plan,commit,verify}/SKILL.md`
- `tasks/{todo,lessons,findings,progress}.md`

### Issues encountered
- None in the scaffold pass.

### Status
Scaffold phase complete through SETUP.md step 5. Continuing with hooks (6), sub-agents (7), first task_plan (8), and layers 9-13.

---

## 2026-04-23 — All 13 setup steps complete

### Actions taken
- Wrote 6 starter hooks (post-edit-format, post-edit-typecheck, pre-tool-use-plan, post-tool-use-progress, stop-verify, suggest-compact) + 2 observability hooks (log-tool-call, log-user-correction). Wired all in `.claude/settings.json`.
- Set up `planner` and `code-reviewer` sub-agents in `.claude/agents/<name>/AGENT.md` per SETUP.md Section 3 spec.
- Wrote first plan: `tasks/parse-simulation-plan.md` — the load-bearing element-taxonomy work.
- Drafted `.claude/rules/cross-model-verification.md` (blanks for user to pick second model).
- Scaffolded research layer: `.claude/research/autoresearch-prompt.md` + `run-autoresearch.sh` cron runner.
- Scaffolded observation layer: `.claude/observability/` with logging hooks and README of jq queries.
- Scaffolded self-edit loop: `.claude/self-edit/weekly-ritual.md`.
- Wrote `README.md` pointing to SETUP.md as the reading order for anyone (human or agent) entering the repo.
- Wrote `.gitignore` to exclude observability logs from git.

### Files created (this session total: 30)
- `.claude/`: CLAUDE.md, settings.json, 5 rule files, 3 skills, 2 agents, 8 hooks, research/, observability/, self-edit/
- `tasks/`: todo.md, lessons.md, findings.md, progress.md, parse-simulation-plan.md
- Root: README.md, .gitignore

### Issues encountered
- `.claude/settings.json` gets reset to a minimal form each time Claude Code prompts for a new permission. Hooks block was rewritten at end-of-session. Pattern to watch for future work.
- Initial agents were placed as `.claude/agents/<name>.md` (Claude Code's native discovery format) rather than SETUP.md's `.claude/agents/<name>/AGENT.md`. User flagged. Fix: (a) moved content to `<name>/AGENT.md`, (b) added symlinks `<name>.md -> <name>/AGENT.md` so both SETUP.md spec and native Task-tool discovery are satisfied with one source of truth.

### Status
Scaffold phase **complete**. Ready to start Phase 1 of `parse-simulation-plan.md` (element taxonomy design) once the Univest Apriori source data is in the repo.

---

## 2026-04-23 — parse-simulation: all 4 phases complete (Univest ingest)

### Actions taken
- WebFetched `https://apriori.work/demo/univest`; extracted variant descriptions, 5×4 conversion matrix, friction points, persona quotes, aggregate metrics.
- Saved raw data to `data/apriori-univest-source.md` (immutable per skill rule).
- **Phase 1** — Drafted `.claude/rules/element-taxonomy.md` with 11 dimensions. Included 4 "proposed but not tested" values (real_closed_trade, see_one_real_trade, dark_teal, refund_sla_explicit) because V5 synthesis will reach for them.
- **Phase 2** — Wrote `.claude/skills/parse-simulation/SKILL.md` with workflow, decision tree, inline schema. Produced `data/element_matrix.json`: 5 variants × 11 dimensions, 4 segments with weights, 8 friction points with persistence flags, 5 citations, aggregate metrics block, 3 documented confounds, 3 clean-contrast inferences (V2→V3 is the only fully clean one).
- **Phase 3** — Spot-check round 1 (3/5) caught two bugs: V1.cta_style mislabeled, V2/V3.cta_primary_label inferred not extracted. Fixed taxonomy + matrix; added `extraction_confidence` field. Round 2 (5/5) passed. Logged top-3 adversarial objections to findings.md with failure mechanisms + fix paths.
- **Phase 4** — Updated parse-simulation-plan.md Review section. Added 4 lessons to lessons.md. Matrix is ready for `weigh-segments`.

### Files created / modified
- `data/apriori-univest-source.md` — immutable raw source.
- `data/element_matrix.json` — complete matrix, validated, reproduces source completion rates to ≤1pt.
- `.claude/rules/element-taxonomy.md` — 11-dimension taxonomy, variant mapping table, extraction confidence guidance.
- `.claude/skills/parse-simulation/SKILL.md` — workflow + schema.
- `tasks/parse-simulation-plan.md` — all phases marked complete, Errors + Review filled.
- `tasks/findings.md` — Univest-ingest section with adversarial review.
- `tasks/lessons.md` — 4 new lessons (PROCESS + SYNTHESIS categories).

### Issues encountered
- Source description for V4 omits refund_copy, but a V4 Skeptical Investor quote references "₹1 with a refund." Either source gap or carried-over mental model. Flagged in matrix.flags, not resolved; blocker for V5 synthesis if it matters.
- Trust Seeker quote attributed to "n=48" in source while segment size is n=10. Treated as aggregate; logged in flags.
- `trust_signal` dimension bundles SEBI-reg + named-wins-evidence; these varied independently across the dataset but the taxonomy collapsed them. Adversarial review flagged as should-fix in taxonomy v1.1; deferring until weigh-segments actually trips on it.

### Status
`parse-simulation` feature **shipped**. Matrix is ready for `weigh-segments` consumption. Updated `tasks/todo.md` to point to `tasks/weigh-segments-plan.md` as the next active plan (to be written when user kicks off Day 3 per IDEA.md week plan).

---

## 2026-04-23 (later) — Genericity refactor

### Actions taken
- Split `.claude/rules/element-taxonomy.md` into `element-taxonomy-base.md` (client-neutral, 11 dimensions) + `element-taxonomy-univest.md` (overlay with `trade_evidence` dimension, SEBI regulator detail, Univest variant mapping, Univest-specific contradiction rules). Deleted the monolithic file.
- Moved `data/apriori-univest-source.md` → `data/univest/source.md`; `data/element_matrix.json` → `data/univest/element_matrix.json`. Established `data/<client>/` as the per-client convention.
- Updated matrix element values to match the new base schema (e.g., `opaque_trial` → `opaque`, `sebi_plus_named_wins` → `regulatory_plus_evidence` + `evidence_detail=named_past_outcome`). Weighted-overall conversion still reproduces source to ≤0.3pt across all 5 variants — schema refactor was value-preserving.
- Rewrote `.claude/skills/parse-simulation/SKILL.md` to be fully client-agnostic. Added a client-overlay template, explicit inputs (client slug, source, domain hint), and a "Common pitfalls" section that calls out "baking client segments into the skill."
- Added to `.claude/CLAUDE.md`: "Build for the second client from the first commit" as a project-specific rule with explicit path conventions.
- Created `tasks/improvements.md` — forward-looking improvement backlog distinct from reactive lessons. 11 initial entries, severity-tagged.
- Added 4 new lessons to `tasks/lessons.md` (source immutability at new path, build-for-second-client, taxonomy-split trigger, improvements-log convention).
- Logged the full genericity-refactor session to `tasks/findings.md` with what changed and what I learned.

### Files modified / created
- `.claude/rules/element-taxonomy-base.md` (new, 11 dimensions, client-neutral)
- `.claude/rules/element-taxonomy-univest.md` (new, client overlay)
- `.claude/rules/element-taxonomy.md` (deleted — replaced by the split)
- `.claude/skills/parse-simulation/SKILL.md` (rewritten, client-agnostic)
- `.claude/CLAUDE.md` (added build-for-second-client rule)
- `data/univest/source.md` (moved from `data/apriori-univest-source.md`)
- `data/univest/element_matrix.json` (moved + element values normalized to base schema)
- `tasks/improvements.md` (new)
- `tasks/lessons.md` (+4 lessons)
- `tasks/findings.md` (genericity-refactor session log)

### Issues encountered
- `cta_primary_label` enumeration in first-pass taxonomy was doomed — would explode combinatorially across clients. Switched to freeform string, preserving verbatim button text. Matrix values now show the actual text ("Activate for ₹1" instead of `activate_one_rupee`).
- Splitting `trust_signal` → `trust_signal` + `evidence_detail` materializes a split that improvements.md had flagged as should-fix. Decided to do it now rather than defer — cheaper to split once during a refactor than to propagate the conflation downstream. Applied improvement landed; improvements.md entry for this should move to "Applied."

### Status
Refactor complete. Matrix validates. `data/<client>/` pattern established. SKILL.md is client-agnostic and has an overlay template ready for the second client. Ready for `weigh-segments` to be built on top — and `weigh-segments` must also be client-agnostic from the start (it reads from `data/<client>/element_matrix.json` and the client overlay, never hardcodes).

---

## 2026-04-23 (later) — weigh-segments shipped

### Actions taken
- Wrote `tasks/weigh-segments-plan.md`. 4 phases.
- Phase 1: Wrote `.claude/skills/weigh-segments/SKILL.md`. Client-agnostic. 5-tier evidence classification (clean_contrast / friction_direct / confounded / variant_only / untested). Formula: `weighted_score = Σ (segment_weight × delta_pts) − contradiction_penalties (only when not already in contrast)`.
- Phase 2: Computed `data/univest/weighted_scores.json`. Mid-computation, caught a formula bug in my own SKILL.md: friction-flag-rate isn't conversion-pts. Amended SKILL.md step 5 to emit null-pts + directional-signal for friction-only values. Amended step 8 to check for double-counting before applying contradiction penalties.
- Phase 3: JSON-validated. Clean-contrast reproduces hand computation: cta_style high_contrast_green = +6.42pt, low_contrast_subordinate = −6.42pt. 5-random-entry spot-check (seed 4711) passed 5/5. Adversarial review surfaced 3 most-likely-wrong concerns.
- Phase 4: Updated findings, lessons (4 new), improvements (3 new Open entries), plan Review.

### Files created / modified
- `.claude/skills/weigh-segments/SKILL.md` (new, ~220 lines, client-agnostic)
- `data/univest/weighted_scores.json` (new)
- `tasks/weigh-segments-plan.md` (new, all 4 phases complete, Errors + Review filled)
- `tasks/lessons.md` (+4 synthesis/process lessons)
- `tasks/improvements.md` (+3 Open entries: cross-dimension consistency, sub-attribute schema, per-segment intervals)
- `tasks/findings.md` (weigh-segments session with adversarial review and schema ambiguity notes)
- `tasks/todo.md` (active plan pointer updated)

### Evidence-tier KPI (first measurement for Univest)
| Tier | Count | Dimensions |
|---|---|---|
| Fully rankable (clean-contrast pts) | 1 | cta_style |
| Directionally rankable (friction or universal adoption) | 5 | modal_interrupt, price_visibility, urgency_mechanism, trade_evidence, layout |
| Weakly rankable (observational signal, confounded) | 3 | trust_signal, evidence_detail, branding |
| Non-informative from data | 3 | cta_primary_label, cta_stack, refund_or_guarantee_copy |
| **Total** | **12** | — |

1/12 dimensions produced a clean-contrast pts score from 5 variants. The 5-variant A/B test gives one clean attribution plus directional signals; 3 dimensions' V5 recommendations lean on overlay-proposed untested values.

### Issues encountered
- Formula bug in SKILL.md caught during Phase 2. Fixed in place. Lesson about unit-confusion added.
- JSON `+N.N` numbers (leading `+` sign) are invalid. Stripped. Validation caught it cleanly.
- Validation coverage check flagged `trust_signal_regulator` / `evidence_detail_format` as "missing dimensions" — correctly, because they're sub-attributes not dimensions. Schema ambiguity logged in improvements.md.

### Status
`weigh-segments` feature **shipped**. `data/univest/weighted_scores.json` is the input to `synthesize`. Next per IDEA.md Day 4: build `synthesize` — applies cross-dimension consistency to pick the V5 element set, threads citations from the matrix through each choice, hands off to adversary for challenge. Must be client-agnostic from commit 1 (same pattern as prior skills).

---

## 2026-04-23 (later) — synthesize shipped, V5 produced for Univest

### Actions taken
- Wrote `tasks/synthesize-plan.md` (4 phases, 3 kill conditions).
- Phase 1: Wrote `.claude/skills/synthesize/SKILL.md`. Client-agnostic. 5 citation types (clean_contrast / friction_point / overlay_mechanism / universal_adoption / default_by_adoption_rate). Confidence roll-up rule. Untested-stack threshold at > 4. Explicit separation from spec-writer (adversary goes in between per IDEA.md doctrine).
- Phase 2: Produced `data/univest/synthesized_variant.json` + `.md`. 12 dimensions resolved; every choice cited; cross-dim consistency rules applied (7 checked, 1 triggered-and-reflected, 1 internal conflict resolved). Per-segment predictions with intervals and named failure conditions per segment.
- Phase 3: Inline adversarial review. 3 challenges answered with named failure mechanisms, falsifiable predictions, fix paths. Surfaced that `trade_evidence=real_closed_trade` has operational fragility and `evidence_detail=named_past_outcome` has stock-selection dependence — both out-of-matrix concerns.
- Phase 4: Updated findings, lessons (+4), improvements (+3 Open), plan Review.

### Files created / modified
- `.claude/skills/synthesize/SKILL.md` (new, client-agnostic)
- `data/univest/synthesized_variant.json` (new)
- `data/univest/synthesized_variant.md` (new, human summary)
- `tasks/synthesize-plan.md` (new, all phases complete, Errors + Review filled)
- `tasks/lessons.md` (+4 synthesis/process lessons)
- `tasks/improvements.md` (+3 Open: non-linearity calibration, adversary out-of-matrix reach, stock-selection out-of-matrix)
- `tasks/findings.md` (synthesize session + adversarial review)
- `tasks/todo.md` (active plan archived; next = adversary agent)

### V5 headline

| Metric | Value |
|---|---|
| Predicted weighted-overall | **49.3% (range 45.5% – 53.0%)** |
| V4 actual | 44% |
| Median lift | +5.3pt |
| Confidence | **medium** (4 observed-high + 5 observed-medium + 3 untested) |
| Untested stack | 3 of 12 dimensions (cta_primary_label, refund_or_guarantee_copy, trade_evidence) |
| Exploratory alternative | muted_premium cta_style → 50.3% median (+1pt over primary); stacks a 4th untested |

### V5 element changes vs V4 (6 dimensions differ)
- `cta_primary_label`: "Unlock FREE trade" → "See 1 real trade, free" (untested — honest framing)
- `cta_stack`: dual_outline_plus_sticky → single (removes 33% mismatch-notice)
- `refund_or_guarantee_copy`: absent → explicit_sla (untested — "Refund in 60s to source. No questions.")
- `trust_signal`: implicit → regulatory_plus_evidence (SEBI number + named wins restored from V1)
- `evidence_detail`: none → named_past_outcome (stock-named-with-rupee-gain format)
- `trade_evidence`: blurred_card → real_closed_trade (untested — removes 100% Skeptical friction)

### Issues encountered
- V5 median (49.3%) is below IDEA.md's headline 52-55%. Reason: balanced mode picked observed `high_contrast_green` over untested `muted_premium` (-1pt) and applied 0.7 non-linearity discount for 6 simultaneous changes (-2-3pt vs sum). My 53.0% high-tier matches IDEA.md's 52-55% low bound.
- Adversarial review found operational/contextual failure modes outside the matrix. Not revisions to V5 but improvements filed against the adversary agent (Day 5) and estimate-conversion.

### Status
`synthesize` feature **shipped**. `data/univest/synthesized_variant.json` is handoff-ready for the adversary agent. Per IDEA.md Day 5, next work = build the adversary sub-agent to stress-test the V5 with structural challenges (falsifiable objections, out-of-matrix failure modes, operational fragility). The adversary output feeds back into synthesize (revision pass), then to estimate-conversion (Wilson intervals), then spec-writer (buildable document).

---

## 2026-04-23 (end of day) — V5 buildable design shipped end-to-end

### Actions taken (this session, in order)
1. **Adversary sub-agent built.** `.claude/agents/adversary/AGENT.md` with structural anti-bias rules (blind-review, client-preference bias check), out-of-matrix reach protocol, falsifiable-prediction requirement, schema for `adversary_review.json`.
2. **Ran adversary on V5.** Produced `data/univest/adversary_review.json`. 3 blockers (cta_primary_label "free" language + flow, refund SLA operational reality, real_closed_trade source rules), 5 should-fixes, 2 instrument-only. Acknowledged partial confirmation bias (I had read IDEA.md during parse-simulation). Surfaced coupled-mechanism risk for Skeptical Investor that synthesize's 0.7 discount missed.
3. **estimate-conversion skill built.** `.claude/skills/estimate-conversion/SKILL.md` with Wilson 95% CI formula, coupled-mechanism discount methodology, kill-condition requirement per segment.
4. **Applied estimator to V5.** `data/univest/conversion_estimates.json`. Weighted overall: synthesize's [45.5, 49.3, 53.0] → estimator's [22.3, 48.6, 52.0]. Point preserved (-0.7pt); low tier correctly widened to reflect n=10-15 per-segment baseline uncertainty.
5. **generate-spec skill built.** `.claude/skills/generate-spec/SKILL.md` with 9-section buildable-spec structure.
6. **Produced V5 buildable design.** `data/univest/v5-spec.md`. 5 new components (ClosedTradeCard, RefundSlaLine, RegulatoryBadge, PastWinsCarousel, ActivationCTA) with full specs (fields, copy verbatim, data contracts, acceptance criteria). 4 Operational Preconditions (hard ship gates). 10 instrumentation events tied to kill-conditions. Per-payment-method refund SLA (revises adversary blocker 2 from fiction to operational reality). Cherry-picking mitigation link required in trade card (revises blocker 3).
7. **Quick-win improvements applied.**
   - `scripts/refetch-source.sh` — source versioning helper (refuses to overwrite; auto-increments `-vN`).
   - Cross-dimension consistency rules added to `element-taxonomy-univest.md` (shared-banner pair, trust-evidence pair, label-matches-flow).
   - 5 Open improvements moved to Applied.

### Files created / modified (this session)
- `.claude/agents/adversary/AGENT.md` + symlink
- `.claude/skills/estimate-conversion/SKILL.md`
- `.claude/skills/generate-spec/SKILL.md`
- `data/univest/adversary_review.json`
- `data/univest/conversion_estimates.json`
- `data/univest/v5-spec.md` — **THE DELIVERABLE**
- `scripts/refetch-source.sh`
- `.claude/rules/element-taxonomy-univest.md` (+ cross-dim consistency section)
- `tasks/improvements.md` (5 Open → Applied; 3 Open remain)
- `tasks/progress.md` (this entry)

### The V5 headline
- **Predicted weighted-overall conversion: 48.6%** (Wilson 95% band 22.3% – 52.0%). V4 actual: 44%. Point lift: +4.6pt.
- **Confidence: medium.** Binding constraint is n=10-15 per segment in the source simulation. A future V6 simulation should target n ≥ 30 per segment.
- **6 element changes V4 → V5:** cta_primary_label, cta_stack, refund_or_guarantee_copy, trust_signal, evidence_detail, trade_evidence.
- **3 untested values stacked** (all targeting Skeptical via shared honesty-substrate). Coupled-mechanism discount applied.
- **3 Operational Preconditions must be met before ship.** If any fails, V5 is descoped to V5-narrow (keep only PastWinsCarousel + RegulatoryBadge).

### What the system has built (the four-layer snapshot)
| Layer | Artifact | Status |
|---|---|---|
| **Build** | parse-simulation, weigh-segments, synthesize, estimate-conversion, generate-spec (skills); planner, code-reviewer, adversary (sub-agents); 8 hooks; 6 rule files | ✅ shipped |
| **Research** | autoresearch prompt + cron runner in `.claude/research/` | ⚠ unused (no cron scheduled) |
| **Observation** | log-tool-call, log-user-correction hooks writing to `.claude/observability/*.jsonl` | ✅ wired, collecting data |
| **Self-edit** | `.claude/self-edit/weekly-ritual.md` | ⚠ scheduled for 2026-04-30 first run |

### What's been delivered for Univest
| Artifact | Purpose | Path |
|---|---|---|
| Source | Raw Apriori data | `data/univest/source.md` |
| Element matrix | Normalized variant × dimension data | `data/univest/element_matrix.json` |
| Weighted scores | Per-dimension recommendations with evidence tiers | `data/univest/weighted_scores.json` |
| Synthesized variant | V5 element choices + predictions | `data/univest/synthesized_variant.{json,md}` |
| Adversary review | Structured objections | `data/univest/adversary_review.json` |
| Conversion estimates | Wilson intervals + kill-conditions | `data/univest/conversion_estimates.json` |
| **V5 Buildable Spec** | **Engineer deliverable** | **`data/univest/v5-spec.md`** |

### Status
V5 for Univest is **design-complete**. An engineer can read `data/univest/v5-spec.md` and produce an implementation plan without further context (subject to Univest's codebase conventions overlaying the semantic component names). Three Operational Preconditions must be signed off by Product/Ops/Legal before ship. V5 ship is blocked on Univest-internal commitments, not on the synthesis pipeline.

Next work per IDEA.md week 8: post-ship actuals feed back into `tasks/lessons.md`; the predicted-vs-actual delta calibrates the non-linearity discount factor and the coupled-mechanism assumption. Until then, the system idles on Univest; the test of genericity is a second client.

---

## 2026-04-23 (final) — V5 visual design + scripts + GitHub push

### Actions taken
- Built three HTML mockups under `data/univest/design/`: V4-before (blurred card + 84.7% abstract claim + dual-CTA mismatch), V5a-green (high_contrast_green CTA, full new layout), V5b-muted-premium (dark-teal CTA alternative per adversary obj-005).
- Rendered each to retina-quality PNG (375×812 iPhone viewport, 2x) via Chrome headless. **The "V5.png" deliverable the user asked for** lives at `data/univest/design/v5a-green.png` and `v5b-muted-premium.png`.
- Built `scripts/detect-confounds.py` — auto-detects element confounds via co-occurrence analysis. Smoke-tested against Univest matrix: found 9 full + 10 partial confounds; cross-check against hand-written list showed 8 auto-only (spurious default-coincidences) and 3 hand-only (3+-way clusters the naive detector missed). Refinement logged as nice-to-have improvement.
- Built `scripts/wilson-intervals.py` — Wilson 95% CI helper in single + matrix modes. Reproduces the interval widths used in `conversion_estimates.json`.
- Updated `tasks/improvements.md` with 2 new Applied entries (visual design + scripts, confound-detector noise refinement).
- **Three commits** split cleanly: (1) scaffold per SETUP.md, (2) pipeline skills + adversary, (3) Univest end-to-end deliverable.
- **Pushed to GitHub:** `https://github.com/abhishek5878/simul2design` — all 4 commits now on `origin/main`.

### Files added (this session)
- `data/univest/design/v4-before.html` + `.png` (56KB)
- `data/univest/design/v5a-green.html` + `.png` (154KB retina)
- `data/univest/design/v5b-muted-premium.html` + `.png` (154KB retina)
- `scripts/detect-confounds.py`
- `scripts/wilson-intervals.py`
- GitHub remote wired + all commits pushed

### Status — end of session
**Univest proof-of-concept: design-complete, committed, pushed.** Public at github.com/abhishek5878/simul2design. V5 visual design is the headline artifact; the buildable spec is the engineer-facing deliverable; the full pipeline reasoning (matrix → weighted scores → synthesis → adversary → Wilson estimates → spec → visual mockup) is auditable through the committed JSON/Markdown artifacts.

Remaining Open improvements (4): non-linearity discount calibration (needs post-ship actuals), cross-segment user modeling (needs real user analytics), stock-selection out-of-matrix context (needs real user data), research/observation layers unused (needs user to schedule cron + observe). All require external data/commitment outside this session's scope.

---

## 2026-04-23 (later, 2nd ritual session) — sim-flow + evaluator loop

### Actions taken
- **Session-start ritual applied:** 60s read of lessons / active plan / progress / live `sim-flow status`. Picked ONE phase: build the session-start-style pipeline dashboard. Drafted plan, critiqued once, narrowed v1 from 4 commands to 1 (just `status`).
- Built `scripts/sim-flow.py` (commit `82d0d55`). One-screen dashboard per client: 7 stage markers with inline summaries, post-ship evaluator state, adversary blockers, matrix flags, validation check, next-action recommendation. Reads filesystem directly — no state manifest to desync. Exit codes: 0 clean / 1 input error / 2 has blockers.
- **Second session-start ritual** (same day): state read, picked ONE phase — close the immutable evaluator loop that `sim-flow status` pointed at as missing.
- Added `record-actuals <client> <actuals.json>` verb (commit `cb6d1f0`). Three-file evaluator separation:
  - `evaluator/predicted.json` — frozen snapshot, never overwrites after first record, `_frozen_at` timestamp baked in.
  - `evaluator/actual.json` — raw post-ship truth, user-supplied.
  - `evaluator/comparison.json` — derived delta + calibration signal (weighted point bias pts, segments-within-band count). Can be recomputed; never hand-edited.
- Tested end-to-end on Univest with synthetic `/tmp/` fixtures (realistic: predicted 48.6% → actual 47.0%, within Wilson band, all segments ✓, calibration signal "over-predicted by 1.6pt"). Cleaned synthetic data before commit.
- Adversarial self-review against SETUP.md Appendix A — 8 honest critiques of the system + V5, including "confirmation-bias machine," "Wilson-widened low tier is correct arithmetic on a bad assumption," and "boring notebook captures 85% in 4 hours." Delivered inline to the user; offered to save but they didn't ask.

### Files modified / added
- `scripts/sim-flow.py` (+427 lines across two commits — dashboard + record-actuals)
- `README.md` (+Pipeline status section + +record-actuals doc)
- `tasks/lessons.md` (+4 lessons: status-probe-not-state-file, exit-codes-as-CI, immutable-evaluator-3-files, test-destructive-on-throwaway)
- No client artifacts modified — evaluator test run was to `/tmp/`, cleaned before commit

### Commits this session
- `82d0d55` — sim-flow.py: session-start-style pipeline dashboard
- `cb6d1f0` — sim-flow: add record-actuals verb and immutable-evaluator loop

### What the pipeline now has that it didn't 4 hours ago
- A `<2s` state probe for "where are we on client X"
- CI-compatible exit codes (0 clean / 2 blockers)
- A mechanical immutable-evaluator record that freezes predictions at ship time
- Calibration signal that directly drives the non-linearity-discount calibration improvement when real actuals arrive
- 7 new lessons covering pipeline-operation discipline

### Status — end of session
Pipeline observability + evaluator loop complete. Univest remains ship-blocked on internal sign-off of the 3 Operational Preconditions; now `sim-flow record-actuals univest <actuals>` is the one-command close-the-loop when they do ship.

---

## 2026-04-24 — Related-work paper citations + simulator-LLM provenance

### Actions taken
- Verified three Jan/Feb-2026 arxiv papers in dialogue with the engine: Lost in Simulation (Seshadri et al., 2601.17087), PersonaCite (Truss, 2601.22288), Persona Generators (Paglieri et al., 2602.03545). All IDs confirmed via WebFetch against arxiv.
- Wrote `tasks/related-work.md` — methodology adoption notes per paper. PersonaCite flagged as inspirational-not-authoritative because single-author HCI; the other two are institutionally credible.
- Adopted Lost in Simulation methodology in `.claude/skills/estimate-conversion/SKILL.md`: added `simulator_provenance` as a required input/output field; documented hard-segment widening as a flagged-not-auto-applied recommendation; added a pitfall on ignoring simulator-LLM provenance.
- Added Caveat 4 to `data/univest/v5-spec.md` §9 citing the paper as the structural justification for the wide low-tier interval and the kill-switch architecture.
- Filed three Open improvements derived from the papers: VoC grounding audit, persona diversity audit skill, and the deferred PersonaCite-driven schema change.

### Files modified
- `.claude/skills/estimate-conversion/SKILL.md` — provenance requirement + hard-segment widening section + pitfall
- `data/univest/v5-spec.md` — Caveat 4 with citation
- `tasks/improvements.md` — 3 new Open entries
- `tasks/related-work.md` — new doc

### Commit
- `530eef2` — Adopt simulator provenance + cite related-work in estimator and spec

### Status — end of session
Three citable paper sources now wired into the engine. The PersonaCite-driven schema refactor for parse-simulation is deferred (medium-low source confidence; defer until a stronger source surfaces or a client provides VoC data that motivates it).

---

## 2026-04-24 (later) — Sharpen V5 spec to decisive single-design

### Actions taken
- User direction: "give me the winning variant... with proper factual and other reasoning." Reframed away from A/B hedging. Apriori supplies the variants + simulation; OUR synthesis call is the value-add.
- Verified V5 design call against the source page's own modification recommendation (rendered the apriori demo via Chrome headless). Found source page recommends keeping V4's dual-CTA functionally separated; we had chosen single-CTA. Surfaced this as a real fork.
- Per user's "B" choice: preserved dual-CTA structure but made labels coherent (resolves V4's 33%-noticed mismatch by fixing copy, not by removing structure).
- Sharpened `data/univest/v5-spec.md` §0 (executive summary) to lead with per-segment audience reasoning + cited evidence, instead of element-centric technical brief.
- Sharpened §1.6 + §7: dropped V5a/V5b A/B framing. Single-design ramp at green CTA; muted_premium becomes a sequenced post-ship contingency, triggered only if Trust Seeker drops ≥5pt over 2 weeks.
- Recast `synthesized_variant.md` "Exploratory alternative" as "Post-ship contingency."
- Re-rendered `data/univest/design/v5a-green.png` from current HTML to ensure pixel artifact matches the now-decisive spec.

### Files modified
- `data/univest/v5-spec.md` — exec summary rewrite + drop A/B framing
- `data/univest/synthesized_variant.md` — contingency reframing
- `data/univest/design/v5a-green.png` — re-render

### Commit
- `c8701ba` — Sharpen V5 spec to decisive single-design with audience reasoning

### Status — end of session
V5 spec is now the decisive answer. No options at launch. One sequenced contingency. Audience-led narrative.

---

## 2026-04-24 (later, 3rd session) — Matrix v2: screenshot re-extraction + cascade through pipeline

### Actions taken
- User flagged "we should be sure on the facts on the other variants, say if they were offering 3 free trials we should use that not 1." Treated as red-flag for cascading extraction errors, not a single-fact verify.
- Pulled all 5 variant screenshots from `apriori.work/screens/univest/{1.1,2,3,4,5}.png`. Saved to `data/univest/source-screenshots/{control,v1,v2,v3,v4}.png` as immutable artifacts. Read each visually.
- **Discovered 11 extraction errors** in matrix v1. Source-page prose was prescriptive (highlighting variant-distinguishing features), not descriptive. v1 missed: trial offer count = "3 FREE Trades" not 1; V4's countdown timer; V4's refund banner; V4's crown branding; V4's dark theme; V4's SEBI badge + aggregate metrics; V1's "914 wins · 62 losses" transparency disclosure (the structural defense against cherry-picking).
- Wrote `data/univest/source-v2.md` as new immutable extraction (per source-immutability rule; source.md preserved for audit trail).
- Updated `data/univest/element_matrix.json` to v2 schema. Added `simulator_provenance`, `trial_offer_count`, `wins_losses_disclosure` dimensions. Added v1→v2 audit trail block.
- Cascaded full pipeline against the corrected matrix: `weighted_scores.json` (v2), `synthesized_variant.{json,md}` (v2), `adversary_review.json` (v2), `conversion_estimates.json` (v2), `v5-spec.md` (v2), `data/univest/design/v5a-green.{html,png}` (v2 — dark theme + dual CTA + 3 trades + wins/losses disclosure + real ZOMATO closed trade).
- Updated `tasks/lessons.md` (+3 lessons): source-prose-vs-screenshot extraction discipline; user fact-challenge as red-flag for cascade; introduction/concretization/removal classification of untested-stack.
- Moved improvements.md "Confirm V4.refund_copy via UI screenshot" from Open → Applied with the v2 cascade entry.

### Files modified / created
- `data/univest/source-screenshots/` — new, 5 immutable PNGs
- `data/univest/source-v2.md` — new, screenshot-validated extraction
- `data/univest/element_matrix.json` — v2 (rewritten with corrections + new dimensions)
- `data/univest/weighted_scores.json` — v2
- `data/univest/synthesized_variant.{json,md}` — v2
- `data/univest/adversary_review.json` — v2 (3 blockers → 0 + 2 op preconditions)
- `data/univest/conversion_estimates.json` — v2
- `data/univest/v5-spec.md` — v2 (rewritten Section 1 diff + new components for wins/losses + carousel)
- `data/univest/design/v5a-green.{html,png}` — v2 (dark theme, dual CTA, full content)
- `tasks/lessons.md` (+3 lessons)
- `tasks/improvements.md` (1 Open → Applied with full cascade write-up)

### Headline impact
- Predicted weighted-overall: **50.6%** (mechanism range 44–56%, Wilson envelope 22–74%) vs V4's 44%. Median lift +7pt (was +4.6pt in v1).
- Untested stack: **3 → 1**. Most "untested introductions" were V4 concretizations we missed.
- Adversary blockers: **3 → 0** + 2 operational preconditions (refund SLA per payment method, "free" flow delivers 3 trades pre-payment).
- CTA copy: "See 1 real trade, free" → **"See 3 real trades, free"** (matches actual offer).

### Issues encountered
- sim-flow.py status reports `0/0 fully rankable` and `parsed but no weighted_overall_prediction` — the script's v1 schema-key paths don't match v2 outputs. Cosmetic (pipeline artifacts validate fine), but visible on every status check. Filed as known follow-up in commit message; addressed in next session.

### Commit
- `a7f55c1` — Matrix v2: screenshot re-extraction + corrected V5 cascade

### Status — end of session
Three commits (530eef2, c8701ba, a7f55c1) pushed to origin/main. Univest V5 v2 is the corrected, decisive deliverable. Session-end ritual itself was skipped this day; progress.md and handoff updated retroactively in the 2026-04-26 catch-up session.

---

## 2026-04-26 — Catch-up: session persistence + sim-flow v2 schema

### Actions taken
- Session-start ritual revealed yesterday's session-end was skipped: progress.md, todo.md, and the latest handoff were stale (still pointing at 2026-04-23 state). Caught up retroactively with three backward-looking entries above.
- Wrote `tasks/handoff-2026-04-26.md` as the new latest handoff. Supersedes `tasks/handoff-2026-04-23-late.md`. Documents the v2 cascade + 12 Open improvements + the sim-flow regression.
- Updated `tasks/todo.md` to point at the new handoff and reflect "v2 cascade complete" state.
- Fixed `scripts/sim-flow.py` to read v2 schema keys: `summarize_synthesis`, `summarize_estimates`, `summarize_weighted`, `summarize_adversary`, `validate_math` all gained v2-aware fallbacks. Added new "Operational preconditions" section so v2's 2 ship-gates surface visibly (they aren't `severity=blocker` in the v2 schema but they function as ship gates).
- Verified: `sim-flow status univest` now shows clean v2 stats (`1/12 fully rankable`, `predicted 50.6% (range 44–56%)`, `0 blockers · 2 op preconditions · 4 should-fix · 1 watch`).

### Files modified
- `tasks/progress.md` — three retroactive entries + this entry
- `tasks/handoff-2026-04-26.md` — new
- `tasks/todo.md` — pointer + state update
- `scripts/sim-flow.py` — v2-aware schema fallbacks across 5 functions

### Status — end of session
Process debt closed. Pipeline observability is honest again. Univest still ship-blocked on Univest-internal commitments (2 op preconditions). Three deferred work-streams remain: post-ship actuals capture, second client engagement, weekly self-edit ritual (scheduled 2026-04-30 — 4 days away).

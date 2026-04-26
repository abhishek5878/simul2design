# Improvements

Forward-looking backlog. Separate from `lessons.md` (reactive — corrections the user gave) and `findings.md` (research — what I learned).

An improvement lands here when I notice something is weak but don't need to fix it *right now*. Review at every session start. Promote to `todo.md` when the cost of leaving it unfixed exceeds the cost of fixing it.

## Format

```
### <short title>
- **Why it matters:** <one sentence>
- **Trigger to fix:** <what event makes this urgent>
- **Fix path:** <one line, concrete>
- **Severity:** blocker | should-fix | nice-to-have
- **Filed:** YYYY-MM-DD
```

---

## Open

### ~~Phase 3b: LLM fallback for the ~25% of taxonomy cells rules can't auto-map~~ → see Applied (2026-04-27)

### Audit Univest VoC grounding sources
- **Why it matters:** The 5 Univest segments ("Skeptical Investor," "Curious Beginner," etc.) are abstract archetypes, not voice-of-customer-grounded personas. Per Truss 2026 (PersonaCite, arxiv:2601.22288 — see `tasks/related-work.md` §2), persona behaviors that can't cite a real source are unverifiable. If real Univest VoC artifacts (app-store reviews, churn-survey responses, support tickets) exist, anchoring the 5 segments to them would tighten V5 confidence intervals retroactively.
- **Trigger to fix:** Before V5 ships AND Univest can hand over real user-research data; or before a second client engagement, whichever comes first.
- **Fix path:** Ask Univest for (a) recent app-store reviews tagged by sentiment, (b) any churn-survey or cancellation-reason data, (c) support tickets categorized by issue type. For each segment, attach 2-5 verbatim quotes from real users that justify the segment's stated behaviors. File at `data/univest/voc/<segment_id>.md`.
- **Severity:** should-fix
- **Filed:** 2026-04-24

### Persona diversity audit skill (run before parse-simulation on a new client)
- **Why it matters:** A synthesis is only as good as the simulation's persona coverage. Per Paglieri et al. 2026 (Persona Generators, arxiv:2602.03545 — see `tasks/related-work.md` §3), persona sets benefit from explicit diversity audits — measuring trait variance, opinion diversity, and coverage of the client's actual customer base. Without this, the synthesis output has no defensible "diversity floor" — a confidence cap below which no synthesis can drop regardless of how clean the variant data looks.
- **Trigger to fix:** Second client engagement. Univest's n=10-per-segment binding constraint is already documented; new clients will hit the same issue more or less severely.
- **Fix path:** New skill `audit-persona-diversity`. Inputs: simulation persona definitions + client's actual customer-segmentation data (if available). Outputs: per-segment trait-variance score, opinion-diversity score, coverage-vs-real-customer-base ratio, and a diversity floor that downstream skills must respect.
- **Severity:** nice-to-have
- **Filed:** 2026-04-24

### parse-simulation should accept VoC grounding artifacts (PersonaCite-derived schema change)
- **Why it matters:** Today `parse-simulation` ingests variant performance only. Per PersonaCite (Truss 2026, arxiv:2601.22288 — see `tasks/related-work.md` §2), persona definitions that ground in real Voice-of-Customer artifacts produce more verifiable outputs. Schema change: each persona gains a `voc_evidence: [{source_type, source_id, quote}]` field. A persona with empty `voc_evidence` is allowed but flagged as "abstract" in downstream confidence scoring.
- **Trigger to fix:** Second client engagement OR if Univest provides real user-research data per the "Audit Univest VoC grounding sources" entry above.
- **Fix path:** (a) extend `parse-simulation` SKILL.md schema with `voc_evidence`; (b) add `data/<client>/voc/` folder convention; (c) add a propagation rule — if `voc_evidence` is empty, downstream `weigh-segments` and `synthesize` must apply a confidence-tier downgrade.
- **Severity:** should-fix (deferred — source paper is single-author HCI, methodology inspirational rather than authoritative; defer structural refactor until either a stronger source surfaces or a client provides data that motivates it)
- **Filed:** 2026-04-24

### ~~Confirm V4.refund_copy via UI screenshot~~ → see Applied (2026-04-24)

### Confound auto-detector is naive (over-detects default+default coincidences)
- **Why it matters:** `scripts/detect-confounds.py` catches 9 full confounds in Univest's matrix where the hand-written list has 3. 8 of the auto-detected are spurious — "branding=none ↔ refund=absent" just means both are the default values that happen to coincide in 3 variants. Meaningful confounds (3+-way clusters with partial breaks) are missed.
- **Trigger to fix:** Second client (will expose the over-detection as noise).
- **Fix path:** (a) exclude "default/null" values from confound detection unless they co-vary in a non-trivial way; (b) detect 3+-way clusters explicitly; (c) score confounds by how much they interfere with downstream attribution — a confound only matters if the elements have different predicted per-segment impacts.
- **Severity:** nice-to-have (script is useful as a first pass; the hand-written list in the matrix remains the authority)
- **Filed:** 2026-04-23 (confound detector smoke test)

### Cross-segment users are not modeled
- **Why it matters:** Simulation assigns each persona to exactly one segment. Real users span segments (e.g., 35yo F&O trader who is also price-sensitive). The synthesis has no rule for hybrid users. Per IDEA.md problem 8.
- **Trigger to fix:** When a client's actual user base analytics are available and segmentation is clearly multi-label.
- **Fix path:** Allow a persona/user to have a primary segment + secondary flags. Weigh against the primary; flag edge cases in spec output.
- **Severity:** nice-to-have (not blocking V5; becomes blocking when segment model moves from synthetic to real-data)
- **Filed:** 2026-04-23

### Inferred values are easy to miss
- **Why it matters:** `extraction_confidence.{variant}.{dim} = "inferred"` is buried in the matrix. A synthesizer reading `V2.cta_primary_label = activate_one_rupee` doesn't see the inferred flag unless it looks for it specifically.
- **Trigger to fix:** First time `synthesize` uses an inferred value as load-bearing evidence.
- **Fix path:** Either (a) make inferred values explicit in the element value — e.g., `activate_one_rupee (inferred)` — or (b) require `synthesize` skill to check `extraction_confidence` before using any value; block decisions that depend on inferred values without user confirmation.
- **Severity:** should-fix
- **Filed:** 2026-04-23

### code-reviewer agent not yet exercised
- **Why it matters:** Parse-simulation produced data + markdown, not code. code-reviewer was skipped. When `weigh-segments` becomes TypeScript we need the review loop to actually run.
- **Trigger to fix:** First TypeScript file created for any skill.
- **Fix path:** Invoke code-reviewer as a sub-agent on every new .ts file before the commit skill runs.
- **Severity:** should-fix
- **Filed:** 2026-04-23

### "Proposed but not tested" taxonomy values need synthesizer guardrails
- **Why it matters:** `dark_teal`, `real_closed_trade`, `refund_sla_explicit`, `see_one_real_trade` are in the taxonomy so the synthesizer can reach for them. But they have no observed performance data — zero evidence base. A naive synthesizer might pick them uncritically.
- **Trigger to fix:** First `synthesize` run.
- **Fix path:** Synthesize skill must: (a) detect proposed-but-untested values; (b) require the spec to explicitly note "untested in dataset" in the rationale; (c) automatically put the prediction into a wider confidence interval for any segment where the untested value is load-bearing.
- **Severity:** should-fix
- **Filed:** 2026-04-23

### Sub-attribute storage is schema-ambiguous
- **Why it matters:** `trust_signal_regulator=sebi` and `evidence_detail_format=stock_named_with_rupee_gain` are currently peer keys in `variant.elements` alongside real dimensions. They're actually qualifiers on their parent values. Validation coverage checks flag them as "missing dimensions" — correctly — because they shouldn't be top-level.
- **Trigger to fix:** When a second dimension needs a sub-attribute (likely happens with second client), OR when a downstream skill gets confused about which keys are independent dimensions.
- **Fix path:** Either nest — `{"trust_signal": "regulatory_plus_evidence", "_detail": {"regulator": "sebi"}}` — or formalize a "qualifier" registry in base taxonomy listing `(parent_dim, parent_value) → [allowed_qualifiers]`.
- **Severity:** nice-to-have (current output works; this is schema hygiene)
- **Filed:** 2026-04-23 (weigh-segments validation)

### Non-linearity discount factor is assumed (0.7), not calibrated
- **Why it matters:** When V(N+1) involves K simultaneous dimension changes, mechanism-sum predictions compound non-linearly. I used a 0.7 discount factor by feel. If the true factor is 0.5, V5 is over-predicted by several pts; if 0.9, under-predicted.
- **Trigger to fix:** Second client engagement (first cross-client data point), OR post-ship actuals from Univest V5.
- **Fix path:** Log (simultaneous_change_count, predicted_point, actual_point) tuples across clients. Fit the discount factor against actuals. Replace the constant in synthesize SKILL.md with a data-backed function.
- **Severity:** should-fix (long-run calibration — blocks honest "confidence" grading)
- **Filed:** 2026-04-23 (synthesize phase 3)

### Stock selection is out-of-matrix context that breaks named_past_outcome mechanism
- **Why it matters:** V1's 71% stock-naming signal assumed persona pre-existing relationships with the named stocks. Real users may not have that relationship with whichever stocks V5 picks. Curious Beginner's +7pt lift depends on stock-selection resonance.
- **Trigger to fix:** Before V5 ships to production.
- **Fix path:** Either (a) personalize the carousel stocks to user's recent searches/holdings (out-of-scope for activation screen), OR (b) pick stocks with broad name recognition (index ETFs, top-10-by-search in user's region), OR (c) treat stock-selection as a separate test that's upstream of V5.
- **Severity:** should-fix (bleeds into estimate-conversion which must widen Curious Beginner interval)
- **Filed:** 2026-04-23 (synthesize adversarial review)

### Research layer and observation hooks are wired but unused
- **Why it matters:** Autoresearch prompt exists but no cron scheduled. Observability hooks write logs but nobody's reading them yet. These layers will decay if they're never exercised.
- **Trigger to fix:** End of first week of real work (2026-04-30).
- **Fix path:** Run the autoresearch script manually once; confirm output shape. Pull the week's tool-call log; skim for failure patterns. Close the loop on 2026-04-30.
- **Severity:** nice-to-have
- **Filed:** 2026-04-23

---

## Applied (moved here when shipped)

### 2026-04-27 — Phase 3b: LLM fallback for taxonomy cells (Sonnet 4.6)
- Closes the Open entry filed 2026-04-26. Builds `scripts/automap-taxonomy-llm.py`: for each cell where Phase 3a returned `needs_review` (or `low_default` with `--include-low-default`), calls Claude Sonnet 4.6 (configurable via `--model`) with the variant text + dimension enum + Phase 3a verdict; updates the matrix and tags trace as `auto_mapped_llm` for high/medium-confidence picks.
- Prompt caching on the system message (full taxonomy enum, ~2KB) — first call writes cache (1.25× cost), subsequent calls read at 0.1×. Cost ~$0.05 per typical client (~14 cells × ~$0.003 each).
- Cost guards: `--max-cells N` cap, `--dry-run` for prompt preview without API calls (no auth required).
- Error handling: typed exceptions for `AuthenticationError` / `RateLimitError` / `APIStatusError`; SDK auto-retries 5xx; markdown-fence stripping on responses; JSON parse failures surfaced.
- Added `requirements.txt` (anthropic ≥0.85.0). Documented `ANTHROPIC_API_KEY` requirement in INTEGRATION.md.
- Tested by 15-test suite using `unittest.mock` to patch `anthropic.Anthropic` — runs without an API key. Covers: taxonomy parsing, prompt building, cell selection (needs_review-only by default; +low_default with flag), LLM call shape (cache_control on system), response parsing (incl. markdown-fence stripping + invalid JSON), auth-error handling, full mocked end-to-end run, low-confidence preserves matrix, --max-cells caps iterations.
- After Phase 3b: rules fill ~75%, LLM closes most of the remaining 25%, only 1–3 cells per typical client need human review. **Onboarding time ~15–20 min** (down from ~45–60 min after Phase 3a alone, ~1.5–2 hours after Phase 2 alone, ~4–6 hours pre-Phase-2).
- Unblocks Phase 4 (webhook on apriori_landing PRs → engine triggers automatically).

### 2026-04-24 — Matrix v2: full screenshot-validated re-extraction (cascade through pipeline)
- Discovered via user fact-challenge ("if 3 trials, use 3") that v1 matrix had multiple extraction errors. Source page prose ≠ actual variant UI. Pulled all 5 variant screenshots from `/screens/univest/{1.1,2,3,4,5}.png`, saved to `data/univest/source-screenshots/` as immutable artifacts.
- 11 corrections across Control/V1/V2/V3/V4 (trial offer count, trust signals, refund copy, urgency, branding, layout, CTA labels). Wrote `data/univest/source-v2.md` as new immutable extraction. Updated `element_matrix.json` to v2 schema (added `simulator_provenance`, `trial_offer_count`, `wins_losses_disclosure` dimensions; added v1→v2 audit trail).
- Cascaded through full pipeline: weighted_scores.json (v2), synthesized_variant.{json,md} (v2), adversary_review.json (v2 — 3 blockers → 0 blockers + 2 op preconditions), conversion_estimates.json (v2), v5-spec.md (v2), v5a-green.{html,png} (v2 — dark theme + dual CTA + 3 trades + wins/losses).
- Net effect on V5: same ~7pt median lift (50.6% vs 48.6%), but smaller untested stack (1 vs 3) and more defensible because most "untested elements" turned out to be V4 concretizations.
- Resolves improvements.md "Confirm V4.refund_copy via UI screenshot" Open entry.
- 3 new lessons logged.

### 2026-04-23 (later) — Adversary sub-agent built and exercised
- `.claude/agents/adversary/AGENT.md` created with structural anti-bias rules (blind-review requirement, client-preference bias check) and falsifiable-prediction requirement on every objection.
- Ran against V5: 3 blockers (cta_primary_label "free" language, refund SLA operational reality, real_closed_trade source rules), 5 should-fixes, 2 instrument-only. Coupled-mechanism risk surfaced that synthesize's 0.7 discount missed.
- Resolves improvements.md "Adversary out-of-matrix reach" Open entry.

### 2026-04-23 (later) — estimate-conversion skill + Wilson intervals
- `.claude/skills/estimate-conversion/SKILL.md` — Wilson 95% CI formula documented, coupled-mechanism discount methodology, kill-condition requirement per segment.
- Applied to V5: `data/univest/conversion_estimates.json`. Revised weighted overall from synthesize's [45.5, 49.3, 53.0] to [22.3, 48.6, 52.0] — point preserved, low tier correctly widened to reflect small-sample uncertainty.
- Resolves improvements.md "Per-segment small-sample intervals not yet computed" Open entry and "Propagate small-sample uncertainty into predictions" earlier Open entry.

### 2026-04-23 (later) — generate-spec skill + V5 buildable design
- `.claude/skills/generate-spec/SKILL.md` — 9-section buildable-spec structure with component specs (name, fields, copy, data contract, acceptance criteria), operational preconditions as first-class checklist, instrumentation tied to kill-conditions.
- Produced `data/univest/v5-spec.md`: buildable V5 design with 5 new components (ClosedTradeCard, RefundSlaLine, RegulatoryBadge, PastWinsCarousel, ActivationCTA), per-payment-method refund SLA (revises adversary blocker 2's concern), cherry-picking mitigation via "Browse all recent trades (mixed outcomes)" link, 10 instrumentation events tied to kill-conditions.

### 2026-04-23 (end of day) — V5 visual design + helper scripts
- `data/univest/design/v5a-green.html` + `v5a-green.png` — V5 primary (high_contrast_green CTA) rendered at 375×812 iPhone viewport, 2x retina.
- `data/univest/design/v5b-muted-premium.html` + `v5b-muted-premium.png` — V5 exploratory alternative (dark-teal CTA) per adversary obj-005.
- `data/univest/design/v4-before.html` + `v4-before.png` — V4 "before" mockup showing blurred trade card + "84.7% historical accuracy" abstract claim + dual-CTA mismatch — the three frictions V5 removes.
- Chrome headless rendering pipeline established for future mockups.
- `scripts/detect-confounds.py` — auto-detects full + partial element confounds from a matrix. Exposed that 8 of 9 auto-detected "full confounds" are spurious default-coincidences; refinement logged.
- `scripts/wilson-intervals.py` — Wilson 95% CI helper in single-value + full-matrix modes. Reproduces the interval widths used in conversion_estimates.json.

### 2026-04-23 (later) — Source versioning helper + cross-dimension consistency rules
- `scripts/refetch-source.sh` — refuses to overwrite existing source files; auto-increments `-v2`, `-v3` suffixes. Writes header with fetch date + source URL.
- Resolves improvements.md "Source-file versioning isn't enforced" Open entry.
- Added cross-dimension consistency section to `.claude/rules/element-taxonomy-univest.md`: shared-banner pair rule, trust-evidence pair rule, trade/evidence-detail non-overlap, label-matches-flow operational rule, SEBI disclaimer requirement.
- Resolves improvements.md "`visible_with_framing` and `implicit_refund` may be the same UI element" Open entry.

### 2026-04-23 — Split `trust_signal` into `trust_signal` + `evidence_detail`
- Base taxonomy now has two independent dimensions: `trust_signal` (implicit / regulatory / third_party_endorsement / evidence_mode / regulatory_plus_evidence) and `evidence_detail` (none / aggregate_metric / named_past_outcome / user_testimonial / third_party_logos / real_outcome_disclosure).
- Univest matrix updated: V1 now shows `trust_signal=regulatory_plus_evidence` + `evidence_detail=named_past_outcome` (with `evidence_detail_format=stock_named_with_rupee_gain` in overlay).
- Applied during the genericity refactor rather than deferred — cheaper to split once in-place than to propagate the conflation into `weigh-segments`.
- Caveat: in the *Univest* dataset the two still co-vary perfectly (only V1 has either), so single-attribution remains impossible from this dataset alone. Logged in `matrix.confounds[]`. The split makes future clients able to attribute independently.

### 2026-04-23 — Build-for-second-client discipline made structural
- Split taxonomy into `element-taxonomy-base.md` + `element-taxonomy-<client>.md` overlay pattern.
- Restructured data into `data/<client>/` folder convention.
- Added CLAUDE.md rule: "Every skill, rule, and agent is client-agnostic unless its path makes the client scope explicit."
- parse-simulation SKILL.md rewritten as client-agnostic, takes client-slug input, includes overlay template.
- This was promoted from "doctrine" (a note at the bottom of the old monolithic taxonomy file) to structural enforcement (separate files, explicit paths, CLAUDE.md rule).

---

## Rejected (with reason)

_Nothing yet._

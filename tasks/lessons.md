# Lessons

## Format

Each lesson is one line in the form: `[CATEGORY] Pattern — Rule`.

Categories in use: `STYLE`, `GIT`, `SCOPE`, `TOOL`, `VERIFICATION`, `SYNTHESIS`, `PROCESS`.

## Entries

- [PROCESS] Every element choice in a deliverable must cite the simulation data point supporting it — rule: no unsupported claims in synthesis output.
- [PROCESS] Synthesizer output is not shown to spec-writer until adversary has challenged it — rule: separate synthesis from writing, always.
- [VERIFICATION] Conversion predictions require confidence level + named failure condition — rule: never give a number without both.
- [VERIFICATION] If a validation step didn't run, say so — rule: never fabricate test results or review steps.
- [SYNTHESIS] Element extraction is load-bearing — rule: if taxonomy is inconsistent across variants, fix the parser before touching synthesis.
- [PROCESS] Random spot-check at ≥4/5 is a real filter, not ceremony — rule: always run it on a new element_matrix; the first Univest ingest caught a `cta_style` miscategorization and an inferred-value mis-labeling that would have compounded downstream.
- [SYNTHESIS] Inferred values must be flagged — rule: any matrix value not directly stated in source gets `extraction_confidence: inferred`; synthesize and spec-writer must refuse to treat inferred values as load-bearing.
- [SYNTHESIS] Confounded element sets must be named structurally — rule: co-varying elements (e.g., crown_header + blurred_card + refund_copy in V2/V3) go in matrix.confounds[], not in prose notes; weigh-segments reads them to refuse single-element attribution from confounded contrasts.
- [PROCESS] Source data is immutable — rule: never edit `data/<client>/source.md` after extraction. Upstream changes create `source-v2.md`, `-v3` etc. in the same `data/<client>/` folder. The predictor-vs-actual evaluator depends on replay.
- [PROCESS] Build for the second client from the first commit — rule: no client name, client segment, or client-specific value may appear in a base skill, a base rule, or a sibling skill. Client content lives only in `data/<client>/` and `.claude/rules/element-taxonomy-<client>.md`. If a generalizing dimension emerges across clients, lift it to base with a note about which client surfaced it — don't duplicate.
- [PROCESS] Taxonomy splits are a live design decision — rule: if two sub-attributes of a dimension can observably vary independently (e.g., regulatory-signal and evidence-mode), split them. Don't wait for the synthesizer to trip on the conflation; split on the next spot-check if the evidence is already there.
- [PROCESS] Keep an explicit forward-looking improvements log (`tasks/improvements.md`) — rule: `lessons.md` is for reactive corrections the user gave; `improvements.md` is for proactive "I noticed this is weak" notes. Review improvements at session start alongside lessons. Promote to `todo.md` when the cost of not fixing exceeds the cost of fixing.
- [SYNTHESIS] Friction-flag-rate and conversion-pts are different units — rule: never convert one to the other directly. A 50% flag rate is strong directional evidence but tells you nothing about the pts magnitude without a clean-contrast grounding. weigh-segments emits friction_direct values with null pts + structured friction_evidence block.
- [SYNTHESIS] When applying overlay contradiction rules, check the clean contrast or friction hasn't already captured the penalty — rule: `contradiction_penalty` is only applied if the value's evidence basis does NOT already include the affected segment. Double-counting silently biases weighted scores downward.
- [SYNTHESIS] Null + evidence_tier is the correct output for unattributable values — rule: fabricating a pts number to avoid a null is the worse sin. A synthesizer reading null+confounded correctly widens confidence; a synthesizer reading a fabricated pts number overfits. weigh-segments, synthesize, and estimate-conversion all treat null as a first-class signal.
- [PROCESS] Evidence-tier distribution per dimension is a dataset-informativeness KPI — rule: track "rankable dimensions / total dimensions" at the end of every weigh-segments run. If only 1/12 dimensions is fully rankable from a 5-variant test, the binding constraint is data, not algorithm — and the next test should vary more dimensions in isolation. Report the KPI to the user at handoff.
- [SYNTHESIS] Headline predictions (like IDEA.md's "52-55%") can bias synthesize toward untested-upside values — rule: balanced mode respects observed evidence and the discount factor, even when the result lands below a previously-stated headline. The headline is an upper-bound assumption, not a target. If the user wants the headline, they must explicitly pick exploratory mode (which will stack more untested values and widen the interval).
- [SYNTHESIS] Simultaneous-change non-linearity discount is an assumption, not a constant — rule: document it as `non_linearity_discount: 0.7 (assumed)` inline. Calibrate against post-ship actuals over time. Never hide it inside a prediction calc; the discount must be visible to the adversary and to the user.
- [PROCESS] Adversarial review must reach for out-of-matrix failure modes — rule: synthesize operates on in-matrix information only (observed contrasts, documented frictions, overlay mechanisms). The adversary must explicitly challenge operational/implementation/context-dependence failure modes — these are invisible to synthesize by design. Bake this into the adversary AGENT.md when it's built.
- [SYNTHESIS] Untested-stack count is a V(N+1) risk signal — rule: count untested values in the V(N+1) element set at every synthesize run. ≤ 4 is manageable optimization; > 4 means design-from-scratch, not optimization. Surface this explicitly to the user and in the output.
- [SYNTHESIS] Coupled mechanisms defeat the independence assumption in non-linearity discounts — rule: if ≥ 2 untested changes target the same segment via a shared substrate (e.g., "show a real thing" honesty across cta_label + trade_evidence + refund_sla), apply a stronger discount (0.5 not 0.7) to that segment's predicted lift. Synthesize's default 0.7 assumes independence; adversary must flag couplings.
- [PROCESS] Wilson intervals, not Normal approximations, for small-n segments — rule: at n=10-15, Normal approximation CIs breach [0, 1]. Always Wilson. Expose the baseline Wilson CI alongside the mechanism-lift interval so the reader sees both sources of uncertainty.
- [PROCESS] Estimator widens the low tier honestly — rule: synthesize's "confidence intervals" reflect only mechanism uncertainty. estimate-conversion adds baseline small-sample uncertainty. The low tier should WIDEN and often go negative on lift when Wilson baseline bands are wide. This is not a bug; it's the information content of the simulation.
- [SYNTHESIS] Operational reality must override stated mechanisms — rule: if the synthesized value requires an operational promise (refund SLA, backend freshness, legal language), adversary must challenge it; spec-writer must encode it as a hard Operational Precondition. Never ship a design whose mechanism depends on ops discipline without naming that discipline as a gate.
- [PROCESS] Client-preference bias is structural, not psychological — rule: agents that read the client-narrative doc (IDEA.md, brief, etc.) cannot be the adversary. Structural separation: the adversary agent's context must NOT include the client preference. For the first client this rule was violated; logged as an improvement. Enforce from second client.
- [SPEC] Every component in a spec must have: name, fields with types + sources, copy verbatim, data contract with staleness/fallback, acceptance criteria, associated kill-condition events — rule: "use a real trade card" is not a spec. "Replace `BlurredTradeCard` with `ClosedTradeCard`, fields {stock_name, entry_price, ...}, sourced from `/api/v1/trades/closed?limit=1&sort=recency&filter=outcome:win&max_age_hours=24`" is a spec. IDEA.md problem 4 applied.
- [PROCESS] Cherry-picking detection belongs in the spec, not the synthesis — rule: any design that selects best-of-many (best trade, best review, best metric) must include a visible "browse the full set" link so the user can detect cherry-picking if they want to. Skeptical Investor trust gap is not closed by showing a win; it's closed by being willing to show the losses too.
- [PROCESS] "Proper design" means a visual artifact the reader can see, not only a markdown spec — rule: when the user says "design," default to producing BOTH the buildable markdown spec AND a renderable visual (HTML → PNG via Chrome headless, or equivalent). IDEA.md problem 4 talks about buildable specs in prose; the user's "V5.png types" clarification made it concrete. Going forward, `generate-spec` output is the spec doc; parallel artifact `design/<variant>.png` is the visual. Ship both.
- [PROCESS] Genericity (build-for-second-client) must be structural AND enforced — rule: "fork when another client arrives" is a deferral, not a plan. The taxonomy split, client overlay pattern, and `data/<client>/` convention had to exist from commit 1. When a user says "this should work for upcoming simulations too," treat it as a process-level correction that warrants structural refactoring, not just a note. Apply immediately; don't carry forward.
- [PROCESS] A pipeline needs a session-start-style status probe, not a state file — rule: derive pipeline state from filesystem introspection (what artifacts exist, what they contain), not from a separate JSON manifest that can desync. `scripts/sim-flow.py status <client>` takes <2s, reads 6 JSON files, and outputs one screen with per-stage marker + inline summary + blockers + next-action suggestion. Mirror the session-start ritual's principles: state first, narrow scope, one suggested action at end.
- [PROCESS] Exit codes are the CI interface for research pipelines — rule: `sim-flow status` returns 0 only when pipeline is clean (no blockers). Any real CI/cron check against `sim-flow status univest` will then correctly gate downstream actions on the pipeline being in a shippable state.

## How to use this file

- Read at session start (the `session-persistence` rule enforces this).
- Add a lesson after every user correction, with enough specificity that the agent can pattern-match next time.
- Consolidate weekly: merge duplicates, delete obsolete.
- When a lesson has held for 30+ sessions without violation, promote it to `CLAUDE.md` as a hard rule.

## Template for a new lesson

```
- [CATEGORY] <situation that triggered the correction> — rule: <what to do next time, concrete enough to pattern-match>.
```

Bad lesson: `[STYLE] Don't break things — rule: be careful.`
Good lesson: `[STYLE] When refactoring a skill, don't add new abstractions — rule: stay within existing SKILL.md patterns unless explicitly asked.`

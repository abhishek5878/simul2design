# IDEA.md — Multiverse Synthesis Engine

> **One line:** We don't report which variant won. We build the variant that should exist.

---

## The Problem Worth Naming Precisely

Simulation tools are excellent at producing truth. They are not designed to produce instruction.

The output of a well-run simulation is: *"Variant 4 won at 44% conversion."* The implicit takeaway is: ship Variant 4. This is correct and incomplete in equal measure.

No single tested variant is optimal for the whole audience. Variant 4 won overall but Trust Seekers peaked at Variant 1 (60%). Skeptical Investors hit 25% in V4 — the blurred trade card that kills them was never fixed in any variant. Curious Beginners want a real named stock, which every variant after V1 stripped out. The highest-converting design you could actually build — the one the data implies is sitting at roughly 52-55% overall — was never tested. It doesn't exist in any of the five universes.

The gap between "which variant performed best" and "what you should build next" is not filled by a better report. It is a different product category.

That category is called **prescriptive simulation**. This project builds it.

---

## The Core Insight

Every design element has a performance score against every segment. A variant is one combination of those elements. The space of all possible combinations — the multiverse — is enormous. Any five-variant test explores five points in it.

The synthesis problem: given performance data across N tested variants, find the untested combination that maximizes weighted conversion across the full audience composition.

This is tractable for three reasons:

1. **Element-level performance data exists.** The simulation didn't just score variants. It scored elements — the countdown timer, the blurred trade card, the dual CTA, the refund SLA, the named stock win. That data is in the persona monologues and friction maps.

2. **Audience weights are known.** Segment sizes are not assumptions. They are outputs of the simulation. Curious Beginner is 30% of the Univest audience. Skeptical Investor is 24%. Weight the element choices accordingly.

3. **Contradiction pairs are detectable.** Not every combination is valid. A countdown urgency timer and a skeptic-first design are mutually exclusive — V1 proved it. A bright green CTA and premium positioning don't coexist — V3 proved it. The constraints reduce the search space to what can actually ship.

A human analyst reads V4's result and anchors on "V4 won." Claude reads all 5 × 4 = 20 segment-variant data points in parallel, holds the contradiction map, applies the audience weights, and finds the combination that was never tested. The cognitive task that would take a strategy consultant two weeks is a well-structured agent run.

**The 1% reframe:** You are not building a better research report. You are solving a constraint satisfaction problem over a design space, and handing the solution to an engineer as a buildable spec.

---

## What We Are Building

A Claude Code project — a local agent system — that ingests simulation output and emits a prescriptive variant specification.

### Input

- Simulation results in structured form: variant descriptions, per-segment conversion rates, friction point logs, persona monologues, design element taxonomy.
- Audience composition weights.
- Optional: existing brand/design constraints (colors, tone, platform).

### Output

**1. The Synthesized Variant Spec**
Not a summary. A buildable document. Every design decision named, with the element it replaces, the segment it serves, and the conversion delta it is predicted to deliver. An engineer reads it and knows what to ship. No translation required.

**2. Segment-Level Conversion Predictions**
Predicted conversion per segment, with confidence ranges and the specific failure condition that would collapse each prediction. "Skeptical Investor: 35% (±5pts). Failure condition: trade data shown is older than 30 days or is a forward-looking projection rather than a closed trade.")

**3. The Contradiction Map**
Element pairs that conflict. Element pairs that have never been combined but have no known conflict and both have positive segment signals. The map shows what's been tried, what's been avoided, and what's unexplored.

**4. Risk Flags**
The three highest-risk assumptions embedded in the synthesis. Each flag includes: the assumption, the evidence base, the failure cost if wrong, and a one-sentence test to validate it before shipping.

**5. The Next Experiment**
A fully specified V(N+1) A/B test plan: hypothesis, success metric, segment to watch, minimum detectable effect, sample size, and the one thing that would kill the test early.

---

## The Univest Proof-of-Concept

This is not speculative. The numbers exist.

**Current state:** Variant 4 is the recommended ship. 44% overall activation. Best-in-study SUS score 73.6. Dual CTA stack with sticky ₹1 button. Known unresolved friction: blurred trade card (12/50 users immediately recognize it as a gimmick), abstract metrics vs. named wins (8/50), dual CTA label mismatch (5/50).

**The synthesized variant (call it V5):**

| Element | V4 (current best) | V5 (synthesized) | Rationale |
|---|---|---|---|
| Layout | Full-screen | Full-screen | No change — V4 right |
| Trust signal | Implicit | SEBI reg. number + "ZOMATO +₹23,435 in 3 days" | V1 peaked Trust Seekers at 60% with this. V2-V4 dropped it. Put it back. |
| Trade evidence | Blurred card | Real closed trade: entry / exit / days held / ₹ gain | 24% of audience (Skeptical Investors) call this out as a gimmick in every variant. Never resolved. This is the largest single unsolved conversion drag. |
| CTA 1 | "Unlock FREE trade" → ₹1 flow | "See 1 real trade, free" → genuinely free preview | 33% of V4 users flagged the label mismatch as mildly deceptive. Make it honest. Make it actually free. |
| CTA 2 | Sticky green "₹1 Trial" | Sticky dark-teal "Activate for ₹1" | V3 proved bright green costs Trust Seekers 10pts. Dark-teal preserves visibility and premium tone simultaneously. |
| Urgency mechanism | None (V4 removed timer) | None | V1's countdown timer alienated 41% of Skeptical Investors. Confirmed correct to omit. |
| Refund copy | "Instant refund" | "Refund in 60s to source. No questions." | Explicit SLA closes the refund-disbelief gap that costs 3-5pts with Skeptical Investors. One line of copy. |

**Predicted V5 conversion by segment:**

| Segment | V4 (current) | V5 (predicted) | Driver |
|---|---|---|---|
| Skeptical Investor (24%) | 25% | 35-38% | Real trade card removes the primary trust blocker |
| Curious Beginner (30%) | 33% | 40-42% | Named stock win restores the anchor; honest CTA reduces choice paralysis |
| Bargain Hunter (26%) | 69% | 69-71% | Already near ceiling. Real trade card has no negative effect. |
| Trust Seeker (20%) | 50% | 55-58% | SEBI number + named wins restored from V1; dark-teal CTA removes the premium-feel regression |
| **Overall (weighted)** | **44%** | **~52-55%** | |

**The 8-11 point lift comes from three specific changes. None require design invention. All are directly implied by the simulation data that already exists.**

---

## Architecture (Four Layers per SETUP.md)

### Build Layer — The Agent System

```
.claude/
├── CLAUDE.md                        # This project's rules (see Section below)
├── skills/
│   ├── parse-simulation/            # Ingest Apriori output → structured element-segment matrix
│   ├── synthesize/                  # Core skill: produce optimal variant from the matrix
│   ├── weigh-segments/              # Apply audience composition to element scores
│   ├── detect-conflicts/            # Find contradiction pairs across elements
│   ├── generate-spec/               # Write the buildable variant spec
│   ├── estimate-conversion/         # Predict conversion delta per segment with confidence
│   └── validate-synthesis/          # Adversarial challenge of every design decision
├── agents/
│   ├── synthesizer/                 # Opus. Holds the full matrix, produces the variant.
│   ├── adversary/                   # Opus. Challenges every element choice before it ships.
│   ├── estimator/                   # Sonnet. Produces the conversion predictions with ranges.
│   └── spec-writer/                 # Sonnet. Produces the final buildable document.
└── tasks/
    ├── univest-plan.md              # The active task plan for the Univest proof-of-concept
    ├── lessons.md                   # Self-improvement ledger
    ├── findings.md                  # Research log, updated every 2 operations
    └── progress.md                  # What shipped, readable by next session
```

### Research Layer

Daily digest of:
- New design pattern research relevant to Indian fintech UX (SEBI-regulated products, ₹-denominated trials, trust signals in advisory contexts).
- New simulation methodologies (synthetic persona improvements, element-level attribution techniques).
- Competitor moves in the prescriptive simulation space (currently: no direct competitor exists in this specific gap).

Output: `tasks/findings.md` updated automatically. Not a live process.

### Observation Layer

Every synthesis run logs:
- Input: number of variants parsed, number of segments, number of unique design elements extracted.
- Processing: which element choices were made, which contradiction pairs were detected, which segments drove which decisions.
- Output: predicted vs. actual conversion (filled in post-ship by the client).

When post-ship data comes back, the delta between predicted and actual is the system's accuracy score. This is the evaluator. It is immutable. The synthesis agent cannot edit it.

### Self-Edit Layer

After every client engagement:
1. Read the delta between predicted and actual conversion.
2. Identify which element choices were wrong and why.
3. Propose updates to the `synthesize` skill's decision logic.
4. Run adversarial challenge: "What is the strongest objection to this rule change?"
5. Accept or reject each individually.
6. Commit to `tasks/lessons.md`.

The system gets better at prediction with each client. The evaluator is what keeps it honest.

---

## The CLAUDE.md for This Project

```markdown
# Project context

Multiverse Synthesis Engine. Takes simulation output (from Apriori or equivalent tools) 
and produces a prescriptive variant specification: the optimal untested design derived 
by combining the highest-leverage elements from all tested variants, weighted by audience 
composition. The primary deliverable is a buildable spec an engineer can ship, not a 
research report a PM has to translate. Current proof-of-concept: Univest ₹1 trial 
activation screen. 50 synthetic personas, 5 variants tested, predicted V5 at 52-55% 
vs. V4's 44%.

## Stack
- Language: TypeScript
- Runtime: Claude Code (agentic, local)
- Primary model: Opus (synthesizer, adversary), Sonnet (estimator, spec-writer)
- Input format: JSON / markdown (Apriori output)
- Output format: Markdown spec + structured JSON predictions

## Core rules
- The synthesizer agent never sees the spec-writer's output until after the adversary has 
  challenged it. Synthesis and writing are separate steps. Never collapse them.
- Every element choice in the spec must cite the specific simulation data point that 
  supports it. No unsupported claims in a deliverable.
- Conversion predictions must include confidence level (1-10) and the named failure 
  condition that would collapse the prediction. Never give a number without both.
- The adversary agent's objections are logged in full, even if overruled. The audit 
  trail of rejected objections is as important as the accepted ones.
- Never fabricate test run results. If a validation step didn't run, say so.

## Adversarial framing (self-reminder)
When I ask "is this synthesis correct," answer with the strongest counterargument first. 
What element choice is most likely wrong, and why? What segment is most likely to 
underperform the prediction, and what is the failure mechanism?
```

---

## The 10 Hardest Problems

Ranked by how likely each one is to kill the project if not solved first.

**1. Element extraction is the load-bearing step.**
The synthesis is only as good as the element taxonomy. If "blurred trade card" and "real trade card" are not distinct elements in the parsed input, the synthesis can't choose between them. The parse-simulation skill must produce a consistent, normalized element taxonomy across all variants. This is the hardest engineering problem in the system. Solve it before anything else.

**2. Contradiction detection is underspecified.**
Some element pairs conflict (urgency timer + skeptic-first design). Others don't (dark-teal CTA + SEBI trust badge). The rules for what conflicts are not always obvious from the data alone — they require domain knowledge. Build a contradiction rule file per domain (fintech, e-commerce, SaaS, etc.) and make it human-editable. Don't try to learn it from data alone at this stage.

**3. Audience weights change. The synthesis must recompute when they do.**
If Univest's actual user base skews more Bargain Hunter than the simulation assumed, the optimal variant shifts. The synthesis must be parameterized on audience weights, not hardcoded. Build the weight input as a first-class input from day one.

**4. The deliverable must be buildable by an engineer who wasn't in the room.**
A spec that says "use a real trade card" is not buildable. A spec that says "replace `blurred_trade_card` component with `ClosedTradeCard`, fields: `stock_name`, `entry_price`, `exit_price`, `days_held`, `rupee_gain`, sourced from `/api/trades/closed?limit=1&sort=recency`" is buildable. The spec-writer agent must know the client's codebase conventions to produce this. That means the system needs a codebase context step before spec generation.

**5. Predicted vs. actual tracking is the only thing that prevents hallucination compounding.**
Without post-ship data, the system has no feedback signal. The synthesis gets confidently wrong over time. Build the feedback loop as part of the MVP. The accuracy score is not a nice-to-have. It is the product's immune system.

**6. The adversary agent will be sycophantic if prompted wrong.**
Running "what are the weaknesses of this synthesis" will produce soft objections. Running "your job is to find the single element choice most likely to be wrong and explain the failure mechanism in concrete terms" produces real adversarial output. The adversary's prompt is a product decision, not a prompt trick. Get it right.

**7. The system will be used to justify decisions that were already made.**
Every consultant knows this failure mode. The client will show you their preferred variant, ask for a synthesis, and the output will suspiciously confirm their preference — because the agent detected the framing. The adversary agent must be structurally separated from any knowledge of the client's stated preference. Blind review.

**8. Segment boundaries are fuzzy in real data.**
The simulation assigned each persona to exactly one segment. Real users don't work that way. A 35-year-old F&O trader who is also price-sensitive sits between Skeptical Investor and Bargain Hunter. The synthesis needs a handling rule for cross-segment users, even if it's simple (apply primary segment, flag the edge case).

**9. The first client is the hardest.**
Univest is not the product. Univest is the proof. The product is the system that can run this for any client in any vertical. Every decision made in the Univest engagement must be abstracted, not hard-coded. Build for the second client from the first commit.

**10. Speed of the synthesis loop is a product decision.**
A synthesis that takes 4 hours to run is a consulting deliverable. A synthesis that takes 4 minutes is a product feature. The architecture decisions made now (parallel sub-agents vs. sequential, Opus vs. Sonnet for specific steps) determine which one this becomes. Default to speed. Use Opus only where it is load-bearing.

---

## Adversarial Pre-Mortem

Before writing a line of code, answer these honestly.

**Where is this most likely to fail?**
The element extraction step. If the parse-simulation skill doesn't produce a consistent taxonomy, every downstream step is operating on inconsistent inputs. The synthesis will produce output that looks confident and is structurally wrong.

**What is the failure cost if the conversion predictions are wrong?**
High. A client ships V5 based on a predicted 52-55% conversion. Actual comes in at 38%. The prediction was confident. The system loses credibility. The failure condition that was supposed to be named (and wasn't) was the one that mattered. Every prediction must name its own kill condition. This is non-negotiable.

**What does a skeptical senior engineer say about this architecture?**
"You are running Opus twice in sequence (synthesizer → adversary) on every engagement. That's expensive and slow. Why not run them in parallel and then resolve conflicts?" Answer: because the adversary needs to see the full synthesis before challenging it. Parallel runs would produce a synthesizer that didn't know what the adversary would say and an adversary that didn't know what the synthesizer decided. The sequential cost is correct.

**What is the boring version of this that works 90% as well?**
A well-structured markdown template that a human fills in after reading the simulation report. Faster to ship, zero agent cost. The reason this is not the answer: the human will anchor on the winning variant (V4 bias) and miss the cross-segment synthesis. The value of the agent is specifically in holding all 20 data points simultaneously without anchoring. That is the job to be done.

**What does this look like if it works and nobody notices?**
The client receives a spec, engineers ship it, conversion goes up. The client attributes it to good design instincts. This is fine. The proof is in the delta. Own the outcome, not the credit.

---

## Success Definition

**Week 2:** The parse-simulation skill ingests the Univest Apriori output and produces a normalized element-segment matrix. Every element in every variant is extracted and tagged. Every segment-level conversion score is attached to every element. No human intervention required after the input is fed.

**Week 3:** The synthesizer agent produces a V5 spec for Univest. Every element choice cites a specific data point. The adversary agent has been run. Its objections are logged. The spec has been revised once based on adversary input.

**Week 4:** The V5 spec is in the hands of Univest's product team. It is buildable without additional clarification. It contains: full design decisions, predicted conversion by segment with confidence ranges and failure conditions, the contradiction map, three risk flags, and the next A/B test plan.

**Week 8:** Post-ship data from Univest. Predicted vs. actual delta recorded. Lessons logged. Synthesize skill updated.

**Month 3:** The system runs for a second client, in a different vertical, with zero Univest-specific hardcoding. The second run takes 4 minutes of compute and 20 minutes of human input (audience weights + brand constraints). The first run took 4 days.

---

## First Week: What Gets Built

**Day 1:** Set up the `.claude/` directory from SETUP.md Section 10. Write the `CLAUDE.md` above verbatim. Write `univest-plan.md` with Phase 1 as active.

**Day 2:** Build `parse-simulation`. Input: the Univest Apriori output (already consumed). Output: a JSON file — `element_matrix.json` — with every design element, its variant presence, and its per-segment conversion delta. Validate manually against the data you have already read.

**Day 3:** Build `weigh-segments`. Input: `element_matrix.json` + audience weights (Curious Beginner 30%, Bargain Hunter 26%, Skeptical Investor 24%, Trust Seeker 20%). Output: weighted score per element. The element that wins for the most audience-weight-adjusted segments is the default pick. Contradiction rules override.

**Day 4:** Build `synthesize`. Input: weighted element scores + contradiction rule file. Output: V5 design decisions in structured markdown. Run it. Read the output. Correct it by hand if wrong. Write every correction to `tasks/lessons.md`.

**Day 5:** Build `adversary`. Input: the V5 synthesis. Prompt: "You are a skeptical senior product designer. Your job is to find the element choice most likely to be wrong and explain the failure mechanism in concrete, falsifiable terms. Do not give general concerns. Give specific predictions that would prove you right." Run it against the V5 synthesis. Revise. Log the objections that were overruled.

**Weekend:** Run `generate-spec` on the revised synthesis. Produce the Univest V5 deliverable. Read it as if you are a Univest engineer who was not in the room. Is it buildable? If not, fix the spec-writer.

---

## The One Thing

If this entire IDEA.md reduces to one sentence for the build phase:

**The parse-simulation skill must be correct before any other skill is built. Every downstream output is only as good as the element taxonomy it runs on. Get the input layer right first.**

Everything else compounds from there.

---

*Written against SETUP.md. Four layers. Adversarial by default. Context is state. The loop closes on itself.*

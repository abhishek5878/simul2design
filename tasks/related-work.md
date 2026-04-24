# Related work

Papers that intersect what the synthesis engine is doing. Recorded here so future sessions don't re-find them, and so spec deliverables can cite the methodology rather than asserting it.

The bar for inclusion: the paper changes how we'd build something, not just describes a thing we already do. Each entry has (a) verified citation, (b) what the paper actually argues, (c) the concrete methodology we adopt, (d) the file/skill that changes.

---

## 1. Lost in Simulation — the calibration paper

**Citation (verified 2026-04-24 via arxiv.org):**
- Title: "Lost in Simulation: LLM-Simulated Users are Unreliable Proxies for Human Users in Agentic Evaluations"
- Authors: Preethi Seshadri, Samuel Cahyawijaya, Ayomide Odumakinde, Sameer Singh, Seraphina Goldfarb-Tarrant
- Submitted: 2026-01-23 (v1), revised 2026-01-28 (v2)
- arxiv: 2601.17087

**What it argues.** Cross-cultural user study (US, India, Kenya, Nigeria) finds three structural failure modes in LLM-simulated user evaluations:
1. Agent success rate varies up to 9 percentage points depending on which LLM plays the simulated user.
2. Simulations underestimate performance on hard tasks and overestimate on medium tasks — systematic miscalibration, not random noise.
3. Demographic calibration error compounds with age.

**Methodology we adopt.**
- Treat simulation output as a calibration-dependent input, never ground truth. The post-ship feedback loop in `data/<client>/v5-spec.md` Section 5 (kill-conditions + actuals capture) is the structural answer to (2).
- For "hard" segments (Skeptical Investor in Univest), default to wider Wilson intervals than n alone would suggest. The paper's empirical claim that simulations *underestimate* hard-task performance is a hypothesis we can falsify against Univest actuals.
- Document which simulator generated the input. If Apriori swaps its underlying LLM, recalibrate from scratch.

**What changes.**
- `.claude/skills/estimate-conversion/SKILL.md` — add a "simulator-LLM provenance" required input, and a note that hard-segment intervals widen beyond Wilson-from-n alone.
- `data/<client>/v5-spec.md` Section 5 — cite this paper as the justification for the kill-switch architecture.

**Confidence in the paper:** high. Five authors, recognizable names (Sameer Singh — UC Irvine NLP), structural empirical study with public dataset. Defensible as a citation.

---

## 2. PersonaCite — the grounding paper

**Citation (verified 2026-04-24 via arxiv.org):**
- Title: "PersonaCite: VoC-Grounded Interviewable Agentic Synthetic AI Personas for Verifiable User and Design Research"
- Author: Mario Truss (single author)
- Submitted: 2026-01-29
- arxiv: 2601.22288

**Caveat on the source.** Single-author HCI paper, no co-authors, no institution disclosed in the abstract. Treat the methodology as inspirational rather than authoritative. The *idea* (ground personas in real Voice-of-Customer artifacts) is well-established outside this paper — PersonaCite gives it a citeable name but isn't the only or strongest source.

**What it argues.** Personas should be evidence-bounded. Instead of generating personas from abstract archetypes ("Skeptical Investor"), retrieve actual VoC artifacts — reviews, support tickets, interview transcripts — and constrain persona responses to that evidence. A persona that can't cite a source for its behavior is a hallucination wearing a research-instrument costume.

**Methodology we adopt.**
- `parse-simulation` should accept (and prefer) a VoC-grounded persona definition over an abstract-archetype definition. When a client provides real customer data — app reviews, churned-user interview snippets, support-ticket categories — those are first-class inputs to the simulation, not just context.
- The persona schema gains a `voc_evidence: [{source_type, source_id, quote}]` field. A persona with empty `voc_evidence` is allowed but flagged as "abstract" in downstream confidence scoring.
- For Univest specifically: even retroactively, we should look for real Univest app-store reviews, churn survey responses, or support tickets that anchor the existing 5 segments to real user voices. Anything we find tightens the V5 confidence intervals.

**What changes.**
- `.claude/skills/parse-simulation/SKILL.md` — add VoC-grounding as an optional but preferred input. Document the schema.
- `data/<client>/` folder convention — add `voc/` subfolder for grounding artifacts.
- `tasks/improvements.md` — file a should-fix entry for "audit Univest VoC grounding sources."

**Confidence in the paper:** medium-low as a citation; high as inspiration. Cite cautiously, or cite the underlying HCI lineage instead.

---

## 3. Persona Generators — the diversity paper

**Citation (verified 2026-04-24 via arxiv.org):**
- Title: "Persona Generators: Generating Diverse Synthetic Personas at Scale"
- Authors: Davide Paglieri, Logan Cross, William A. Cunningham, Joel Z. Leibo, Alexander Sasha Vezhnevets
- Submitted: 2026-02-03
- arxiv: 2602.03545

**What it argues.** Introduces a method for *learning* a Persona Generator function — code that produces persona populations — rather than hand-crafting personas. The generator is iteratively improved using AlphaEvolve (LLMs as mutation operators on the generator's code), with a fitness function that maximizes diversity in traits, opinions, and preferences. Result: persona sets that are provably more diverse than hand-crafted alternatives, covering edge cases a human researcher would miss.

**Methodology we adopt.** (Out of immediate scope for Univest, but defines the second-client improvement.)
- A synthesis is only as good as the simulation it's derived from, and a simulation is only as diverse as its persona set. Add a *persona diversity audit* upstream of `parse-simulation` for any new client.
- The audit measures: per-segment trait variance, opinion diversity within a segment, and segment-coverage of the client's actual customer base. Output is a "diversity floor" — a confidence cap that the synthesis output cannot exceed regardless of how clean the variant data looks.
- For Univest: n=10 Trust Seekers and n=10 Skeptical Investors set a diversity floor that no amount of synthesis can break through. The V5 spec already widens those intervals; this paper formalizes *why*.

**What changes.**
- `tasks/improvements.md` — file a nice-to-have entry for "persona diversity audit skill (run before parse-simulation on a new client)."
- No immediate change to existing skills. Revisit at second-client engagement.

**Confidence in the paper:** high. Joel Z. Leibo and Alexander Sasha Vezhnevets are senior DeepMind researchers — this is institutionally credible work. Defensible as a citation.

---

## Through-line

All three converge on the same claim: **simulation is a calibration-dependent input, not ground truth.** The synthesis engine's defensibility comes from the layers it adds on top of raw simulation:

1. Cross-segment weighing (audience-composition adjusted, not raw simulation reads).
2. Adversarial challenge (out-of-matrix failure modes the simulator can't see).
3. Wilson intervals + coupled-mechanism widening (small-sample uncertainty propagated honestly).
4. Operational preconditions as first-class spec elements (e.g., refund SLA per payment method).
5. Kill-conditions + post-ship actuals capture (the feedback loop that closes the calibration gap over time).

Each of those is a methodological response to a failure mode one of these papers documents. When pitching the engine, the framing is: "raw simulation has known calibration errors (Lost in Simulation); the engine is the prescriptive + feedback layer that makes the output decision-grade."

---

## How to use this doc

- When writing a deliverable spec for a new client, copy the relevant citation block into the spec's "References" section.
- When the methodology of an existing skill changes because of one of these papers, update the skill's SKILL.md AND mark the change here ("methodology adopted on YYYY-MM-DD: <skill> changed to <new behavior> per <paper>").
- When a new paper lands that meets the inclusion bar (changes how we build something), add it as section N+1.
- Re-verify citations annually — arxiv IDs are stable but author/title metadata occasionally changes on revision.

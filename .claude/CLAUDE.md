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

## Code style

- No inline comments unless the WHY is non-obvious.
- Prefer editing existing files over creating new ones.
- Never add console.log, print statements, or debug output to committed code.
- Every element choice in a synthesis output cites the simulation data point supporting it.

## Do's and don'ts

- Check for existing implementations before adding new ones.
- Never create documentation unless explicitly requested.
- Ask before installing new dependencies.
- Never fabricate test run results, validation steps, or review processes that didn't happen.
- Never collapse synthesis and spec-writing into one step — adversary challenges synthesis first.

## Workflow orchestration

1. **Plan mode default.** For any task with 3+ steps or architectural decisions, enter plan mode. If something goes sideways, stop and re-plan.
2. **Subagent strategy.** Use subagents liberally to keep the main context clean. One task per subagent.
3. **Self-improvement loop.** After ANY correction from the user, update `tasks/lessons.md` with the pattern. Review lessons at session start.
4. **Verification before done.** Never mark a task complete without proving it works. Run tests, check logs, demonstrate correctness.
5. **Demand elegance, balanced.** For non-trivial changes, ask "is there a more elegant way?" Skip for simple fixes — don't over-engineer.
6. **Autonomous bug fixing.** Point at logs, errors, failing tests, then resolve. Don't ask for hand-holding.

## Task management

- **Plan first.** Write plan to `tasks/todo.md` (or a named `tasks/*-plan.md`) with checkable items.
- **Verify plan.** Check in with the user before starting implementation.
- **Track progress.** Mark items complete as you go.
- **Document results.** Add review section to the plan file when done.
- **Capture lessons.** Update `tasks/lessons.md` after every correction.

## Core principles

- **Simplicity first.** Every change as simple as possible. Minimal impact.
- **No laziness.** Find root causes. No temporary fixes. Senior developer standards.
- **Context is state.** Every lesson written back is a tax future-self doesn't pay.

## Project-specific rules

- The synthesizer agent never sees the spec-writer's output until after the adversary has challenged it.
- Every element choice in a deliverable cites the simulation data point that supports it.
- Conversion predictions must include confidence level (1-10) AND the named failure condition that would collapse the prediction.
- The adversary's objections are logged in full, even when overruled.
- Element extraction is load-bearing: if the element taxonomy is inconsistent across variants, every downstream step compounds the error.
- **Build for the second client from the first commit.** Every skill, rule, and agent is client-agnostic unless its path makes the client scope explicit. Client-specific content lives only in `data/<client>/` and `.claude/rules/element-taxonomy-<client>.md`. If you find yourself writing a client name (or a client's segment name, or a client's domain-specific value) inside a skill or a base rule, stop and refactor.

## Linked rules

Load on demand:
- @rules/planning.md
- @rules/git-practices.md
- @rules/code-quality.md
- @rules/session-persistence.md

## Adversarial framing (self-reminder)

When asked "is this synthesis correct," answer with the strongest counterargument first. What element choice is most likely wrong, and why? What segment is most likely to underperform, and what is the failure mechanism? Never give uniform confidence. If stuck in a long conversation on a hard decision, remind me to verify with a second model.

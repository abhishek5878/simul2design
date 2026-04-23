---
name: handoff
description: Trigger at session end when non-trivial work shipped. Produces a session-handoff doc so the next session (or engineer) picks up context without re-reading the full transcript. One of SETUP.md's session-end ritual steps.
---

# handoff skill

## When to use

- Session end, non-trivial work shipped.
- Context will be lost across a reset (autocompact, fresh conversation, different operator).
- A new engineer (human) is picking up where Claude left off.

## When NOT to use

- Trivial sessions (typo fixes, doc tweaks).
- Mid-session — handoff is for the cut point, not a status check.

## Workflow

1. Read `tasks/progress.md` tail (last ~50 lines) — what happened this session.
2. Read `tasks/todo.md` — what's next, what's parked.
3. Read `tasks/improvements.md` Open section — what's deferred.
4. Write a single handoff doc at `tasks/handoff-<YYYY-MM-DD>.md` covering:
   - **TL;DR** (2-3 sentences): what shipped, what state the project is in, what's blocked.
   - **State of the tree**: uncommitted work, unpushed commits, branches, any risky state.
   - **Active plans**: feature → plan file → phase → next action. If nothing active, say so.
   - **Deferred (improvements.md Open)**: 3-5 highest-priority items with trigger-to-fix.
   - **Known unknowns**: questions the current session surfaced that remain unanswered.
   - **If you're picking this up**: concrete first 30 minutes — what to read, what to verify before touching anything.
5. Cross-link from `tasks/todo.md` so a new session knows the handoff exists.

## Success criteria

- A new operator can read the handoff in 5 minutes and know exactly what to do next.
- No jargon that requires the prior transcript to decode.
- Every "blocked on X" has X named explicitly.
- The "first 30 minutes" section is actionable — specific files to read, specific commands to run.

## Common pitfalls

- **Narrating the session.** The handoff is forward-looking, not a diary. Just enough backward-looking to orient. `progress.md` is the diary.
- **Burying the TL;DR.** The first two sentences must answer "what shipped, what's next" without scrolling.
- **Leaving ambiguity in the active plan.** If a phase is in_progress, the handoff must say where it stopped AND what the next concrete action is. No "see session transcript."

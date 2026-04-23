---
name: verify
description: Trigger before any commit, PR, or claim that work is done. Runs the project's test, type, and lint commands in sequence and reports pass/fail with actual output.
---

# Verify skill

## When to use

- Before every commit.
- Before marking any phase as `complete` in a plan.
- Before claiming "tests pass" or "it works" to the user.
- After any non-trivial edit to check for regressions.

## When NOT to use

- Pure documentation edits (no code changed).
- Exploratory scratch work that isn't going to be committed.

## Workflow

1. Check `package.json` (or equivalent) for the test, typecheck, and lint scripts. Current project conventions:
   - Tests: `npm test` (once tests exist)
   - Typecheck: `npm run typecheck` or `npx tsc --noEmit`
   - Lint: `npm run lint` (once lint is configured)
2. Run them in sequence. Capture actual output. Do NOT summarize — include the output verbatim in your report.
3. If any step fails: report the failure with the actual error output. Do not attempt a fix unless asked.
4. If all green: report "verify: OK" with a one-line summary per step.

## Decision tree

- If `package.json` doesn't exist yet (project is pre-code): report "verify: no code to verify yet" and skip. Do NOT fabricate a passing result.
- If a script isn't defined (e.g., no `test` script): skip that step and note "no tests configured" — do not invent a command.
- If a step hangs: kill after 120s and report the timeout.

## Success criteria

- Every step ran or was explicitly skipped with a reason.
- Actual tool output is shown to the user.
- No fabrication. If a step couldn't run, say so.

## Common pitfalls

- Claiming "tests pass" without running them. Fix: always show the output.
- Running only tests and skipping types/lint. Fix: all three, every time.
- Silencing warnings to make the output green. Fix: fix the warning or explicitly suppress with justification.

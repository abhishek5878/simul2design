# Code quality

## Baseline (non-negotiable)

- TypeScript strict mode. No `any` unless justified in a comment.
- No `console.log` / `print` in committed code. Use a proper logger.
- No dead code. If it's unused, delete it.
- No backwards-compatibility shims unless there's a live consumer.

## Style

- Default to no comments. Only add one when the WHY is non-obvious (hidden constraint, subtle invariant, workaround for a specific bug).
- Don't explain WHAT the code does — well-named identifiers already do that.
- Don't reference the current task, ticket, or PR in comments. Those rot.
- Functions over 30 lines: ask if they should be split. If no, add a one-line docstring.
- Prefer composition over inheritance.

## Dependencies

- Ask before installing a new dependency.
- Prefer the standard library and what's already in `package.json`.
- No dev-dependencies masquerading as runtime deps.

## Error handling

- Validate at system boundaries (user input, external APIs). Trust internal code.
- Don't catch exceptions you can't meaningfully handle.
- Never swallow errors silently.

## Project-specific

- Every element choice emitted by a synthesis step must include a citation to the simulation data point.
- Every conversion prediction must include a confidence level and a named failure condition.
- Never fabricate a validation step. If it didn't run, say so.

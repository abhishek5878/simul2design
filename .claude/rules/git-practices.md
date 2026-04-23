# Git practices

## Commit conventions

- One commit, one concern. Never opportunistically refactor adjacent code in a bug-fix commit.
- Message format: imperative mood, ≤72 chars for subject. Body explains WHY, not what.
- Run `verify` skill before every commit. No "it should work" commits.
- Never `--amend` a published commit. Create a new commit.

## Branch safety

- Never force-push to main.
- Never skip hooks (`--no-verify`, `--no-gpg-sign`) without explicit user approval.
- Before any destructive op (reset --hard, branch -D, clean -f), confirm with user.

## What not to commit

- `.env`, credentials, API keys.
- Large binaries or datasets unless explicitly versioned.
- Anything in `tasks/` that would re-capture ephemeral session state beyond the four standard files.

## Working with the user

- Only create commits when the user asks. Unclear? Ask first.
- Never push to remote unless asked.
- Never open a PR unless asked.

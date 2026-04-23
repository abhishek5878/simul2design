#!/usr/bin/env bash
# Daily autoresearch runner. Intended for cron.
#
# Setup:
#   chmod +x .claude/research/run-autoresearch.sh
#   crontab -e
#   0 7 * * *  cd /Users/abhishekvyas/Desktop/simul_design && .claude/research/run-autoresearch.sh >> .claude/research/autoresearch.log 2>&1
#
# Runs `claude -p` with the autoresearch prompt and appends the result
# to tasks/findings.md. Requires the `claude` CLI in PATH.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

PROMPT_FILE=".claude/research/autoresearch-prompt.md"
OUTPUT_FILE="tasks/findings.md"

if ! command -v claude >/dev/null 2>&1; then
  echo "[autoresearch] claude CLI not found in PATH. Aborting." >&2
  exit 1
fi

TODAY=$(date +%Y-%m-%d)
echo "[autoresearch] Running digest for $TODAY"

claude -p "$(cat "$PROMPT_FILE")" \
  --output-format text \
  >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "[autoresearch] Done. Appended to $OUTPUT_FILE"

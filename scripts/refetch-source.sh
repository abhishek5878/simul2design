#!/usr/bin/env bash
# Safely re-fetch a client's simulation source. Never overwrites existing source files.
# Auto-increments the version suffix.
#
# Usage:
#   scripts/refetch-source.sh <client-slug> <source-url-or-path>
#
# Result:
#   - If `data/<client>/source.md` does not exist, creates it.
#   - If it exists, creates `data/<client>/source-v2.md` (or -v3, -v4, ...).
#   - Writes a header with the fetch date and the URL.
#   - Never overwrites. Never deletes.
#
# The invariant: once a `data/<client>/source*.md` file is committed, it is immutable.
# Every downstream artifact was computed against that exact state, and the
# predicted-vs-actual evaluator needs that state to survive.

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <client-slug> <source-url-or-path>" >&2
  exit 2
fi

CLIENT="$1"
SOURCE="$2"

if [[ ! "$CLIENT" =~ ^[a-z][a-z0-9-]+$ ]]; then
  echo "Client slug must be lowercase kebab-case (e.g., 'univest', 'acme-saas'). Got: $CLIENT" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATA_DIR="$ROOT/data/$CLIENT"
mkdir -p "$DATA_DIR"

# Pick the next filename.
if [ ! -e "$DATA_DIR/source.md" ]; then
  OUT="$DATA_DIR/source.md"
  VERSION=1
else
  # Find the highest existing version.
  VERSION=1
  while [ -e "$DATA_DIR/source-v$((VERSION+1)).md" ]; do
    VERSION=$((VERSION+1))
  done
  VERSION=$((VERSION+1))
  OUT="$DATA_DIR/source-v$VERSION.md"
fi

echo "[refetch-source] Writing to $OUT"

# Fetch content.
if [[ "$SOURCE" =~ ^https?:// ]]; then
  echo "[refetch-source] Fetching $SOURCE..."
  BODY=$(curl -fsSL "$SOURCE")
else
  if [ ! -f "$SOURCE" ]; then
    echo "Source path does not exist: $SOURCE" >&2
    exit 2
  fi
  BODY=$(cat "$SOURCE")
fi

# Write with header.
{
  echo "# Source for $CLIENT (version $VERSION)"
  echo ""
  echo "**Source:** $SOURCE"
  echo "**Fetched:** $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "**Immutable from this moment.** If upstream changes, re-run this script — do not edit in place."
  echo ""
  echo "---"
  echo ""
  echo "$BODY"
} > "$OUT"

echo "[refetch-source] Done. $OUT ($(wc -c < "$OUT") bytes)"
echo "[refetch-source] Remember: all downstream artifacts (element_matrix, weighted_scores, synthesized_variant, adversary_review, conversion_estimates, spec) must be regenerated against this new source if it represents a real upstream change."

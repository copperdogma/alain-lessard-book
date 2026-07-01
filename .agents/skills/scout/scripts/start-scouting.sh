#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: start-scouting.sh <topic-slug>" >&2
  echo "Example: start-scouting.sh instructor-patterns" >&2
  exit 1
fi

SLUG="$1"

# Validate slug: lowercase alphanumeric and hyphens only
if [[ ! "$SLUG" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
  echo "ERROR: Invalid slug '$SLUG'. Use lowercase letters, numbers, and hyphens only." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TODAY=$(date +%Y-%m-%d)
SCOUT_DIR="$ROOT/docs/scout"
INDEX="$ROOT/docs/scout.md"

# Bootstrap index if missing
if [[ ! -f "$INDEX" ]]; then
  cp "$SKILL_DIR/templates/scout-index.md" "$INDEX"
  echo "Created $INDEX"
fi

# Bootstrap directory if missing
mkdir -p "$SCOUT_DIR"

# Find next available number
next_num=1
if ls "$SCOUT_DIR"/scout-*.md &>/dev/null; then
  last=$(ls "$SCOUT_DIR"/scout-*.md | sed 's/.*scout-\([0-9][0-9]*\).*/\1/' | sort -n | tail -1)
  next_num=$((10#$last + 1))
fi
padded=$(printf "%03d" "$next_num")

# Create expedition file from template
OUT="$SCOUT_DIR/scout-${padded}-${SLUG}.md"
if [[ -f "$OUT" ]]; then
  echo "ERROR: $OUT already exists" >&2
  exit 1
fi

sed "s/NNN/$padded/g; s/TITLE/${SLUG}/g; s/SCOUTED_DATE/${TODAY}/g" "$SKILL_DIR/templates/scout-expedition.md" > "$OUT"

echo "$OUT"

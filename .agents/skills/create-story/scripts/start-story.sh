#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: start-story.sh <slug> [priority]" >&2
  echo "Example: start-story.sh golden-refs High" >&2
  exit 1
fi

SLUG="$1"
PRIORITY="${2:-Medium}"

# Validate slug: lowercase alphanumeric and hyphens only
if [[ ! "$SLUG" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
  echo "ERROR: Invalid slug '$SLUG'. Use lowercase letters, numbers, and hyphens only." >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STORIES_DIR="$ROOT/docs/stories"

# Bootstrap directory if missing
mkdir -p "$STORIES_DIR"

# Find next available number
next_num=1
if ls "$STORIES_DIR"/story-*.md &>/dev/null; then
  last=$(ls "$STORIES_DIR"/story-*.md | sed 's/.*story-\([0-9][0-9]*\).*/\1/' | sort -n | tail -1)
  next_num=$((10#$last + 1))
fi
padded=$(printf "%03d" "$next_num")

OUT="$STORIES_DIR/story-${padded}-${SLUG}.md"
if [[ -f "$OUT" ]]; then
  echo "ERROR: $OUT already exists" >&2
  exit 1
fi

sed "s/NNN/$padded/g; s/TITLE/${SLUG}/g; s/PRIORITY/${PRIORITY}/g" "$SKILL_DIR/templates/story.md" > "$OUT"

echo "$OUT"

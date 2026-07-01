#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../../" && pwd)"
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="$ROOT/docs/reports/codebase-improvement"
STATE_FILE="$REPORT_DIR/_state.yaml"

STAMP="$(date +%Y%m%d-%H%M)"
SCANNED_AT="$(date +"%Y-%m-%d %H:%M")"
BRANCH="$(git -C "$ROOT" branch --show-current 2>/dev/null || echo "unknown")"
HEAD_SHA="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo "unknown")"

mkdir -p "$REPORT_DIR"

if [[ ! -f "$STATE_FILE" ]]; then
  cp "$SKILL_DIR/templates/state.yaml" "$STATE_FILE"
fi

REPORT_PATH="$REPORT_DIR/$STAMP.md"
if [[ -f "$REPORT_PATH" ]]; then
  echo "ERROR: $REPORT_PATH already exists" >&2
  exit 1
fi

sed \
  -e "s/TIMESTAMP/$STAMP/g" \
  -e "s/SCANNED_AT/$SCANNED_AT/g" \
  -e "s/BRANCH/$BRANCH/g" \
  -e "s/HEAD_SHA/$HEAD_SHA/g" \
  "$SKILL_DIR/templates/report.md" > "$REPORT_PATH"

echo "$REPORT_PATH"

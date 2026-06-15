#!/usr/bin/env bash
#
# Create a new daily issue of Market Prompt and rebuild the site.
#
#   ./new-issue.sh              -> uses today's date
#   ./new-issue.sh 2026-06-07   -> uses the date you pass
#
# It copies the most recent issue as a starting template (so the styling is
# already correct), opens it in your editor to fill in, then rebuilds index.html.

set -euo pipefail
cd "$(dirname "$0")"

DATE="${1:-$(date +%F)}"                       # YYYY-MM-DD
if ! [[ "$DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "✗ Date must look like YYYY-MM-DD (got: $DATE)"; exit 1
fi

NEW="newsletters/${DATE}.html"
if [[ -e "$NEW" ]]; then
  echo "✗ $NEW already exists — edit it directly."; exit 1
fi

# Most recent dated issue = best template (current styling + structure).
TEMPLATE="$(ls newsletters/[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].html 2>/dev/null | sort | tail -1 || true)"
if [[ -z "$TEMPLATE" ]]; then
  echo "✗ No existing issue to use as a template."; exit 1
fi

cp "$TEMPLATE" "$NEW"
echo "✓ Created $NEW (from $(basename "$TEMPLATE"))"
echo "  → Edit the headlines, stories, date and issue number, then save."

# Rebuild the landing page so the new issue is listed.
python3 build.py >/dev/null
echo "✓ Rebuilt index.html"

# Open the new article (and the site) if we're on macOS.
if command -v open >/dev/null 2>&1; then
  open "$NEW"
fi

echo
echo "When you're happy, run:  python3 build.py   (to refresh the index again)"

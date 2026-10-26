#!/usr/bin/env bash
# Step 3 of the monthly routine. Run this once you are happy with the review.
# Builds the report and the web page, marks the month as seen, and publishes.
set -euo pipefail
cd "$(dirname "$0")"

STAMP="${1:-$(ls -t data/curation_[0-9]*-[0-9]*.json 2>/dev/null | head -1 | sed 's/.*curation_//;s/\.json//')}"

if [ -z "${STAMP:-}" ] || [ ! -f "data/curation_${STAMP}.json" ]; then
  echo "No review found yet."
  echo
  echo "The review step has not been done. Open this folder in Claude Code and say:"
  echo "    write this month's teaching review"
  echo "That writes data/curation_YYYY-MM.json, which this script needs."
  exit 1
fi
if [ ! -f "data/slides_${STAMP}.json" ]; then
  echo "Found data/curation_${STAMP}.json but no data/slides_${STAMP}.json."
  echo "The review is half-finished — ask Claude to write the slide text too."
  exit 1
fi

echo "Publishing the ${STAMP} review."
echo
echo "1/4  fetching author details for the APA references"
python3 -I scripts/fetch_refs.py "$STAMP"
echo
echo "2/4  building the report and the web page"
python3 -I scripts/build_report.py "$STAMP"
python3 -I scripts/build_site.py
echo
echo "3/4  marking this month's articles as seen"
python3 -I scripts/commit_seen.py "$STAMP"
echo
echo "4/4  pushing to GitHub"
git add -A
if git diff --cached --quiet; then
  echo "     nothing changed — already up to date"
else
  git commit -q -m "Teaching review: ${STAMP}"
  git push -q origin main
  echo "     pushed"
fi

echo
echo "─────────────────────────────────────────────────────────────"
echo "Done."
echo
echo "  Report:      reports/${STAMP}.md"
echo "  Public page: https://rossdavilla.github.io/teaching-review/"
echo "               (live in about a minute)"
echo
echo "The private Claude version only updates when Claude republishes it."
echo "If you want that too, say:  publish the artifact"
echo "─────────────────────────────────────────────────────────────"

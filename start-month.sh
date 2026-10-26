#!/usr/bin/env bash
# Step 1 of the monthly routine. Scans the journals for anything new.
# Afterwards, open this folder in Claude Code and say: "write this month's teaching review"
set -euo pipefail
cd "$(dirname "$0")"

echo "Scanning 21 journals for articles indexed in the last 31 days..."
echo
python3 -I scripts/fetch_articles.py "$@"

STAMP=$(ls -t data/candidates_[0-9]*-[0-9]*.json 2>/dev/null | grep -v _PSY | head -1 | sed 's/.*candidates_//;s/\.json//')
echo
echo "─────────────────────────────────────────────────────────────"
echo "Done. Found this month's candidates: data/candidates_${STAMP}.json"
echo
echo "NEXT: open this folder in Claude Code and say"
echo
echo "      write this month's teaching review"
echo
echo "Then, when you are happy with it, run:  ./finish-month.sh"
echo "─────────────────────────────────────────────────────────────"

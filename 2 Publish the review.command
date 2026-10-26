#!/usr/bin/env bash
# Double-click this AFTER Claude has written the review.
cd "$(dirname "$0")"
./finish-month.sh
echo
read -n 1 -s -r -p "Finished. Press any key to close this window."
echo

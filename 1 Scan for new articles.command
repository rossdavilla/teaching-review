#!/usr/bin/env bash
# Double-click this to scan the journals. A black window opens and shows progress.
cd "$(dirname "$0")"
./start-month.sh
echo
read -n 1 -s -r -p "Finished. Press any key to close this window."
echo

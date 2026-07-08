#!/usr/bin/env bash
# Runnable CLI quickstart. Prereqs: a running MIP backend (see backend/README.md)
# and `mip-cli` installed (`pip install -e cli` + `pip install -e sdk/python`).
#
# Usage: examples/cli/quickstart.sh [api_url]
set -euo pipefail

API_URL="${1:-http://localhost:8000}"
MIP_BIN="${MIP_BIN:-mip}"
MIP="$MIP_BIN --api-url $API_URL"

echo "== health =="
$MIP admin health

echo "== create =="
CREATED_JSON=$($MIP --json memories create \
  --namespace demo --owner user-1 --title "Q3 onboarding notes" \
  --summary "Key steps for new hires." \
  --keyword onboarding --keyword notes \
  --source manual-entry)
echo "$CREATED_JSON"
MEMORY_ID=$(echo "$CREATED_JSON" | grep -o '"memory_id": *"[^"]*"' | head -1 | sed 's/.*"\([^"]*\)"$/\1/')

echo "== list =="
$MIP memories list --namespace demo

echo "== search =="
$MIP search "onboarding" --mode hybrid

echo "== explain =="
$MIP explain "$MEMORY_ID" --query onboarding

echo "== update (creates version 2) =="
$MIP memories update "$MEMORY_ID" --if-match 1 --title "Q3 onboarding notes (revised)"

echo "== version conflict (expected MEM-4001) =="
$MIP memories update "$MEMORY_ID" --if-match 1 --title "stale update" || true

echo "== archive / restore / delete =="
$MIP memories archive "$MEMORY_ID"
$MIP memories restore "$MEMORY_ID"
$MIP --json memories delete "$MEMORY_ID"

echo "done"

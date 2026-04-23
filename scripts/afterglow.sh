#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

MODE="${1:-}"
if [[ "$MODE" == "mcp" ]]; then
  shift
  PYTHONPATH=src python3 -m afterglow.mcp_server "$@"
else
  PYTHONPATH=src python3 -m afterglow.cli "$@"
fi

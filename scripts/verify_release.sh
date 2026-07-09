#!/usr/bin/env bash
# Thin wrapper — implementation is scripts/verify_release.py
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/verify_release.py" "$@"

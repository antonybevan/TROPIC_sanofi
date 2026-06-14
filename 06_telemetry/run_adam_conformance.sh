#!/usr/bin/env bash
# run_adam_conformance.sh — turnkey ADaM conformance gate (CDISC ADaMIG v1.3-aligned).
#
# Executable, in-environment QC that implements the high-value ADaM conformance rule families
# (dataset<->define.xml consistency, ADaMIG structural rules, identifier/key integrity, controlled
# terminology). It is the interim gate used while the authoritative Pinnacle 21 Enterprise run is
# unavailable (CORE has no ADaM rules; P21 Community 4.1.0 is engine-expired). See
# 06_telemetry/p21_adam_runrecord.md.
#
# Usage:  bash 06_telemetry/run_adam_conformance.sh
# Outputs: 06_telemetry/adam_conformance_report.{csv,md} + adam_conformance_status.json
set -euo pipefail
cd "$(dirname "$0")/.."
RSCRIPT="$(command -v Rscript || echo /opt/homebrew/bin/Rscript)"

echo "[1/2] Parsing define.xml -> metadata JSON ..."
python3 06_telemetry/adam_conf_parse_define.py

echo "[2/2] Running ADaM conformance checks against 04_adam/*_prod.xpt ..."
"$RSCRIPT" 06_telemetry/adam_conf_check.R

echo "Done. See 06_telemetry/adam_conformance_report.md"

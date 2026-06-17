#!/usr/bin/env bash
# Reproducible CDISC CORE conformance run for TROPIC (SDTM + executable ADaM custom rules).
#
# CORE has executable rules for SDTM/SEND/TIG/USDM but NOT ADaM (the adamig pack is empty as of
# 2026-06). So SDTM is validated against CORE's published rules; ADaM is validated against the
# executable custom rules we author in 06_telemetry/conformance_rules/adam/ (CORE --local-rules).
#
# Requires: python3.12, a CDISC Library API key (free) for the one-time metadata cache.
#   export CDISC_LIBRARY_API_KEY=<key>     # or put it in .core_run/.env (gitignored)
#
# Usage:  bash 06_telemetry/run_core_conformance.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/.core_run"; ENGINE="$RUN/engine"; VENV="$ROOT/.core_venv"; CACHE="$ENGINE/resources/cache"
PY="$VENV/bin/python"; CORE="$ENGINE/core.py"
mkdir -p "$RUN" "$ROOT/06_telemetry/conformance"
[ -f "$RUN/.env" ] && set -a && . "$RUN/.env" && set +a || true
: "${CDISC_LIBRARY_API_KEY:?Set CDISC_LIBRARY_API_KEY (free CDISC account) or add it to .core_run/.env}"

# 1. Python 3.12 venv + CORE library
[ -d "$VENV" ] || python3.12 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip cdisc-rules-engine

# 2. CLI + bundled rule cache (repo clone at the matching tag)
if [ ! -f "$CORE" ]; then
  git clone --depth 1 --branch v0.16.0 https://github.com/cdisc-org/cdisc-rules-engine "$ENGINE"
fi
# CORE 0.16.0 CLI gate bug: StandardTypes omits 'adamig' though the engine requires it. Patch it.
grep -q 'ADAMIG = "adamig"' "$ENGINE/cdisc_rules_engine/enums/standard_types.py" || \
  sed -i '' 's/    ADAM = "adam"/    ADAM = "adam"\n    ADAMIG = "adamig"/' \
    "$ENGINE/cdisc_rules_engine/enums/standard_types.py"

# 3. One-time library metadata cache (ADaM/SDTM standard + CT) via CDISC Library
"$PY" "$CORE" update-cache -c "$CACHE" >/dev/null

# 4. SDTM: convert source sas7bdat -> v5 XPT, validate against CORE's published SDTMIG rules.
#    NOTE: source is SDTMIG 3.1.1; CORE's lowest rule set is 3.2 -> version-gap findings expected.
Rscript -e 'library(haven); d<-c("dm","ae","ex","ds","vs"); dir.create(".core_run/sdtm",showWarnings=FALSE,recursive=TRUE);
  for(x in d) write_xpt(read_sas(sprintf("01_raw_source/real_sdtm/%s.sas7bdat",x)), sprintf(".core_run/sdtm/%s.xpt",x), name=toupper(x), version=5)'
"$PY" "$CORE" validate -s sdtmig -v 3.2 -d "$RUN/sdtm" -ft xpt -ca "$CACHE" \
  -rt "$CACHE/../templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/06_telemetry/conformance/core_sdtm_report"

# 5. ADaM: validate the *_prod.xpt against our executable custom rules (CORE has no ADaM pack).
mkdir -p "$RUN/adam"; for f in "$ROOT"/04_adam/*_prod.xpt; do b=$(basename "$f" _prod.xpt); cp "$f" "$RUN/adam/$b.xpt"; done
rm -f "$RUN/adam/clinsite.xpt"   # BIMO dataset, not ADaM
"$PY" "$CORE" validate -s adamig -v 1.3 -d "$RUN/adam" -ft xpt \
  -lr "$ROOT/06_telemetry/conformance_rules/adam" -ca "$CACHE" \
  -rt "$CACHE/../templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/06_telemetry/conformance/core_adam_report"

echo "Done. Reports in 06_telemetry/conformance/ (core_sdtm_report.json, core_adam_report.json)."

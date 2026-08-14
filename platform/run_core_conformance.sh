#!/usr/bin/env bash
# Reproducible CDISC CORE conformance run for TROPIC (SDTM + executable ADaM custom rules).
#
# CORE has executable rules for SDTM/SEND/TIG/USDM but NOT ADaM (the adamig pack is empty as of
# 2026-06). So SDTM is validated against CORE's published rules; ADaM is validated against the
# executable custom rules we author in platform/conformance_rules/adam/ (CORE --local-rules).
#
# Requires: python3.12, a CDISC Library API key (free) for the one-time metadata cache.
#   export CDISC_LIBRARY_API_KEY=<key>     # or put it in .core_run/.env (gitignored)
#
# Usage:  bash platform/run_core_conformance.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/.core_run"; ENGINE="$RUN/engine"; VENV="$ROOT/.core_venv"; CACHE="$ENGINE/resources/cache"
PY="$VENV/bin/python"; CORE="$ENGINE/core.py"
CORE_VERSION="0.16.0"
# Immutable commit for the v0.16.0 source tree used by the committed conformance evidence.
CORE_COMMIT="c78b05cad21379adf52c8fad5fe1760b826d1ef3"
cd "$ROOT"
mkdir -p "$RUN" "$ROOT/platform/conformance"
chmod 700 "$RUN"
if [ -f "$RUN/.env" ]; then
  # The file is ignored by Git but still carries a live API credential at runtime.  Refuse to
  # source a group/world-readable copy; this protects local workspaces and backup tooling from a
  # secret that would otherwise be exposed before the client ever opens a network connection.
  python3 - "$RUN/.env" <<'PY'
import os
import stat
import sys

path = sys.argv[1]
mode = stat.S_IMODE(os.stat(path).st_mode)
if mode & 0o077:
    print(f"Refusing insecure credential file permissions for {path}: {mode:04o}; use 0600.",
          file=sys.stderr)
    raise SystemExit(1)
PY
  set -a
  . "$RUN/.env"
  set +a
fi
: "${CDISC_LIBRARY_API_KEY:?Set CDISC_LIBRARY_API_KEY (free CDISC account) or add it to .core_run/.env}"

# 1. Python 3.12 venv + CORE library
[ -d "$VENV" ] || python3.12 -m venv "$VENV"
"$VENV/bin/pip" install --quiet --upgrade pip "cdisc-rules-engine==$CORE_VERSION"

# 2. CLI + bundled rule cache (repo clone at the matching tag)
if [ ! -f "$CORE" ]; then
  git clone --depth 1 --branch "v$CORE_VERSION" https://github.com/cdisc-org/cdisc-rules-engine "$ENGINE"
fi
test "$(git -C "$ENGINE" rev-parse HEAD)" = "$CORE_COMMIT" || {
  echo "Refusing unverified CDISC CORE source tree; expected $CORE_COMMIT." >&2
  exit 1
}
# CORE 0.16.0 CLI gate: StandardTypes omits 'adamig' though the engine requires it. Patch it
# (portable across BSD/GNU sed via Python). Resolved upstream (PR #1733 adamig; PR #1770 the other
# ADaM products, merged 2026-06-22); this local patch is required only while the engine is pinned
# to v0.16.0.
STD_TYPES="$ENGINE/cdisc_rules_engine/enums/standard_types.py"
grep -q 'ADAMIG = "adamig"' "$STD_TYPES" || "$VENV/bin/python" - "$STD_TYPES" <<'PYEOF'
import sys
p = sys.argv[1]; s = open(p).read()
open(p, "w").write(s.replace('    ADAM = "adam"\n', '    ADAM = "adam"\n    ADAMIG = "adamig"\n', 1))
PYEOF

# 3. One-time library metadata cache (ADaM/SDTM standard + CT) via CDISC Library
"$PY" "$CORE" update-cache -c "$CACHE" >/dev/null

# 4a. SDTM baseline: convert the PRISTINE 3.1.1 source sas7bdat -> v5 XPT, validate against CORE's
#     published SDTMIG 3.2 rules. NOTE: source is SDTMIG 3.1.1; CORE's lowest rule set is 3.2 ->
#     version-gap findings expected. Pre-uplift reference run (see CORE_RUN_RECORD.md).
rm -rf "$RUN/sdtm"; mkdir -p "$RUN/sdtm"   # clean dir: validate only these std domains (avoids stale/large-supp deadlock)
Rscript -e 'library(haven); d<-c("dm","ae","ex","ds","vs");
  for(x in d) write_xpt(read_sas(sprintf("01_source_data/real_sdtm/%s.sas7bdat",x)), sprintf(".core_run/sdtm/%s.xpt",x), name=toupper(x), version=5)'
cp "$ROOT/03_metadata/define/define_sdtm.xml" "$RUN/sdtm/define.xml"
"$PY" "$CORE" validate -s sdtmig -v 3.2 -d "$RUN/sdtm" -ft xpt -dxp "$RUN/sdtm/define.xml" -ca "$CACHE" \
  -rt "$CACHE/../templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_sdtm_report"

# 4b. SDTM authoritative: uplift the pristine source to the SDTMIG 3.4 derived layer (the version the
#     package describes and ships), then validate it against CORE's published SDTMIG 3.4 rules. The
#     uplift never modifies the source. Authoritative SDTM run (see CORE_SDTM34_RUN_RECORD.md).
Rscript "$ROOT/platform/uplift_sdtm_34.R"
rm -rf "$RUN/sdtm34_std"; mkdir -p "$RUN/sdtm34_std"   # clean dir: same 5 std domains as the baseline (avoids large-supp deadlock)
for x in dm ae ex ds vs; do cp "$RUN/sdtm34/$x.xpt" "$RUN/sdtm34_std/$x.xpt"; done
cp "$ROOT/03_metadata/define/define_sdtm.xml" "$RUN/sdtm34_std/define.xml"
"$PY" "$CORE" validate -s sdtmig -v 3.4 -d "$RUN/sdtm34_std" -ft xpt -dxp "$RUN/sdtm34_std/define.xml" -ca "$CACHE" \
  -rt "$CACHE/../templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_sdtm34_report"

# 5. ADaM: validate the *_prod.xpt against our executable custom rules (CORE has no ADaM pack).
rm -rf "$RUN/adam"; mkdir -p "$RUN/adam"; for f in "$ROOT"/04_analysis_datasets/adam/*_prod.xpt; do b=$(basename "$f" _prod.xpt); cp "$f" "$RUN/adam/$b.xpt"; done
rm -f "$RUN/adam/clinsite.xpt"   # BIMO dataset, not ADaM
cp "$ROOT/03_metadata/define/define.xml" "$RUN/adam/define.xml"
"$PY" "$CORE" validate -s adamig -v 1.3 -d "$RUN/adam" -ft xpt -dxp "$RUN/adam/define.xml" \
  -lr "$ROOT/platform/conformance_rules/adam" -ca "$CACHE" \
  -rt "$CACHE/../templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_adam_report"

echo "Done. Reports in platform/conformance/ (core_sdtm34_report.json [authoritative], core_sdtm_report.json [3.2 baseline], core_adam_report.json)."

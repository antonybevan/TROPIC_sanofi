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
# Keep an inherited credential available only as a non-exported shell value until the one
# subprocess that needs it. No setup, installer, Git, or patching child process receives it.
TROPIC_INHERITED_CDISC_LIBRARY_API_KEY="${CDISC_LIBRARY_API_KEY-}"
export -n TROPIC_INHERITED_CDISC_LIBRARY_API_KEY
unset CDISC_LIBRARY_API_KEY
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RUN="$ROOT/.core_run"; ENGINE="$RUN/engine"; CACHE="$ENGINE/resources/cache"
VENV=""; PY=""; CORE="$ENGINE/core.py"
RULES_DIR="$ROOT/platform/conformance_rules/adam"
CORE_VERSION="0.16.0"
# Immutable commit for the v0.16.0 source tree used by the committed conformance evidence.
CORE_COMMIT="c78b05cad21379adf52c8fad5fe1760b826d1ef3"
cd "$ROOT"

# Execute every dependency/source/cache control from a minimal environment.
# This excludes inherited Python and dynamic-loader search state before any
# process can prepare code that will later receive the Library credential.
clean_env() {
  /usr/bin/env -i \
    "PATH=$PATH" \
    "HOME=$HOME" \
    "TMPDIR=${TMPDIR:-/tmp}" \
    "LANG=${LANG:-C}" \
    "LC_ALL=${LC_ALL-}" \
    "TZ=${TZ-}" \
    "HTTPS_PROXY=${HTTPS_PROXY-}" \
    "https_proxy=${https_proxy-}" \
    "HTTP_PROXY=${HTTP_PROXY-}" \
    "http_proxy=${http_proxy-}" \
    "NO_PROXY=${NO_PROXY-}" \
    "no_proxy=${no_proxy-}" \
    "REQUESTS_CA_BUNDLE=${REQUESTS_CA_BUNDLE-}" \
    "CURL_CA_BUNDLE=${CURL_CA_BUNDLE-}" \
    "PIP_CONFIG_FILE=/dev/null" \
    "GIT_CONFIG_GLOBAL=/dev/null" \
    "GIT_CONFIG_NOSYSTEM=1" \
    "GIT_NO_REPLACE_OBJECTS=1" \
    "GIT_OPTIONAL_LOCKS=0" \
    "$@"
}

# The wrapper reads the key from stdin, so even its own process receives only
# deterministic locale/path state. The wrapper then constructs a second,
# literal allowlist for the credential-bearing CORE child; no inherited proxy,
# custom CA, netrc, HOME, Python, or loader configuration crosses the boundary.
credential_env() {
  /usr/bin/env -i \
    "PATH=/usr/bin:/bin" \
    "LANG=C" \
    "LC_ALL=C" \
    "TZ=UTC" \
    "$@"
}

# The Python environment is rebuilt from exact hash locks for every governed
# run. Keep it in a randomized, owner-only directory and remove it on every
# exit so prior sitecustomize/modules cannot persist into a credential-bearing
# child.
cleanup_core_venv() {
  case "${VENV-}" in
    "$RUN"/core-venv.*)
      rm -rf -- "$VENV"
      ;;
  esac
}
trap cleanup_core_venv EXIT

# Verify the exact custom-rule directory through no-follow file descriptors. RULES.lock is
# sorted UTF-8 JSON using the schema tropic-core-custom-rule-lock/v1; every rule row contains a
# directory-local YAML basename and its lowercase SHA-256 digest. No other directory entry is
# accepted because CORE also interprets ungoverned .json/.yml/.yaml files as executable rules.
verify_core_rules() {
  clean_env python3 -I -S - "$ROOT" <<'PY_CORE_RULE_LOCK'
import hashlib
import json
import os
import re
import stat
import sys


def refuse(message):
    print(f"Refusing ungoverned CDISC CORE custom rules: {message}", file=sys.stderr)
    raise SystemExit(1)


if "CDISC_LIBRARY_API_KEY" in os.environ:
    refuse("rule verification must run without CDISC_LIBRARY_API_KEY")
if len(sys.argv) != 2:
    refuse("repository root argument is missing")

root = os.fsencode(os.path.abspath(sys.argv[1]))
no_follow = getattr(os, "O_NOFOLLOW", None)
directory_only = getattr(os, "O_DIRECTORY", None)
close_on_exec = getattr(os, "O_CLOEXEC", 0)
nonblocking = getattr(os, "O_NONBLOCK", 0)
if no_follow is None or directory_only is None:
    refuse("platform lacks required no-follow directory controls")

directory_flags = os.O_RDONLY | no_follow | directory_only | close_on_exec
file_flags = os.O_RDONLY | no_follow | nonblocking | close_on_exec
directory_fds = []


def read_regular(rules_fd, name):
    try:
        fd = os.open(os.fsencode(name), file_flags, dir_fd=rules_fd)
    except OSError as exc:
        refuse(f"cannot open {name!r} without following links ({exc.strerror})")
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            refuse(f"{name!r} is not a regular file")
        chunks = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(fd)
        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if identity_before != identity_after:
            refuse(f"{name!r} changed while it was being verified")
        return b"".join(chunks), after
    finally:
        os.close(fd)


try:
    try:
        current_fd = os.open(root, directory_flags)
        directory_fds.append(current_fd)
        for component in (b"platform", b"conformance_rules", b"adam"):
            current_fd = os.open(component, directory_flags, dir_fd=current_fd)
            directory_fds.append(current_fd)
    except OSError as exc:
        refuse(f"rule directory or an ancestor is not a real directory ({exc.strerror})")

    rules_fd = directory_fds[-1]
    lock_bytes, _ = read_regular(rules_fd, "RULES.lock")
    if len(lock_bytes) > 64 * 1024:
        refuse("RULES.lock exceeds the 64 KiB format limit")
    try:
        lock = json.loads(lock_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        refuse(f"RULES.lock is not valid UTF-8 JSON ({exc})")
    if not isinstance(lock, dict) or set(lock) != {"schema", "algorithm", "rules"}:
        refuse("RULES.lock has unexpected top-level fields")
    if lock["schema"] != "tropic-core-custom-rule-lock/v1":
        refuse("RULES.lock schema is not supported")
    if lock["algorithm"] != "sha256":
        refuse("RULES.lock algorithm is not sha256")
    rows = lock["rules"]
    if not isinstance(rows, list) or len(rows) != 7:
        refuse("RULES.lock must govern exactly seven rules")

    locked = {}
    ordered_names = []
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "sha256"}:
            refuse("RULES.lock contains a malformed rule row")
        name = row["path"]
        digest = row["sha256"]
        if not isinstance(name, str) or not re.fullmatch(r"TROPIC-ADAM-[0-9]{3}\.yml", name):
            refuse(f"RULES.lock contains an unsafe rule path: {name!r}")
        if name in locked:
            refuse(f"RULES.lock duplicates {name!r}")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            refuse(f"RULES.lock has an invalid SHA-256 for {name!r}")
        locked[name] = digest
        ordered_names.append(name)
    if ordered_names != sorted(ordered_names):
        refuse("RULES.lock rows are not sorted by path")

    actual_entries = set(os.listdir(rules_fd))
    expected_entries = set(locked) | {"RULES.lock"}
    missing = sorted(expected_entries - actual_entries)
    extra = sorted(actual_entries - expected_entries)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing entries: {missing!r}")
        if extra:
            details.append(f"extra entries: {extra!r}")
        refuse("; ".join(details))

    for name in ordered_names:
        content, verified_stat = read_regular(rules_fd, name)
        actual_digest = hashlib.sha256(content).hexdigest()
        if actual_digest != locked[name]:
            refuse(f"SHA-256 mismatch for {name!r}")
        try:
            current_stat = os.stat(
                os.fsencode(name), dir_fd=rules_fd, follow_symlinks=False
            )
        except OSError as exc:
            refuse(f"cannot restat {name!r} ({exc.strerror})")
        if (
            not stat.S_ISREG(current_stat.st_mode)
            or (current_stat.st_dev, current_stat.st_ino)
            != (verified_stat.st_dev, verified_stat.st_ino)
        ):
            refuse(f"{name!r} was replaced during verification")
    if set(os.listdir(rules_fd)) != expected_entries:
        refuse("rule directory changed during verification")
finally:
    for fd in reversed(directory_fds):
        os.close(fd)
PY_CORE_RULE_LOCK
}

verify_core_rules
mkdir -p "$RUN" "$ROOT/platform/conformance"
chmod 700 "$RUN"
test -d "$RUN" && test ! -L "$RUN" || {
  echo "Refusing unsafe .core_run directory." >&2
  exit 1
}
VENV="$(mktemp -d "$RUN/core-venv.XXXXXXXX")"
chmod 700 "$VENV"
PY="$VENV/bin/python"

# 1. Install local CORE dependencies before loading the Library API credential. Explicitly
# remove an inherited key from the installer environment as well, so package build/install hooks
# never receive the credential even when the caller exported it before invoking this script.
clean_env python3.12 -I -m venv "$VENV"
clean_env "$PY" -I -m pip install --quiet --require-hashes --only-binary=:all: \
    --requirement "$ROOT/requirements-core-build.lock"
clean_env "$PY" -I -m pip install --quiet --require-hashes --no-build-isolation \
    --requirement "$ROOT/requirements-core.txt"
clean_env "$PY" -I -m pip check
test "$(clean_env "$PY" -I -c \
  'import importlib.metadata as m; print(m.version("cdisc-rules-engine"))')" = "$CORE_VERSION" || {
  echo "Refusing unexpected CDISC CORE package version; expected $CORE_VERSION." >&2
  exit 1
}

# 2. CLI + bundled rule cache (repo clone at the matching tag)
if [ ! -f "$CORE" ]; then
  clean_env git clone --depth 1 --branch "v$CORE_VERSION" \
    https://github.com/cdisc-org/cdisc-rules-engine "$ENGINE"
fi
test "$(clean_env git -C "$ENGINE" rev-parse HEAD)" = "$CORE_COMMIT" || {
  echo "Refusing unverified CDISC CORE source tree; expected $CORE_COMMIT." >&2
  exit 1
}
# Remove ignored bytecode and all other non-cache extras from the disposable
# vendor checkout before the independent byte-for-byte verifier runs. -B on
# every later CORE process prevents those files from being recreated.
clean_env git -C "$ENGINE" clean -ffdx -e resources/cache/
# Verify every executable CORE source file before any credential is loaded.
# The verifier applies/accepts only the deterministic ADaM CLI compatibility
# patch (upstream PRs #1733/#1770); cache drift is checked separately below.
clean_env "$PY" -I -S "$ROOT/platform/verify_core_source.py" \
    --engine "$ENGINE" --commit "$CORE_COMMIT"

# 3. Before any credential-bearing cache refresh, fail closed on a populated
# local cache that differs from the committed authority. A genuinely missing or
# empty cache is allowed only here for the first download; the post-refresh
# check below is always strict.
clean_env "$PY" "$ROOT/platform/verify_core_cache.py" \
  --cache "$CACHE" \
  --manifest "$ROOT/platform/conformance/core_cache_manifest.json" \
  --allow-initial-empty-cache

# One-time library metadata cache (ADaM/SDTM standard + CT) via CDISC Library. Stream the
# captured inherited key to a credential-free parser; it no-follow-opens an optional exact-0600
# .env and launches update-cache directly with the selected key only in that child's environment.
printf '%s' "$TROPIC_INHERITED_CDISC_LIBRARY_API_KEY" | \
  credential_env "$PY" -I -S "$ROOT/platform/run_core_update_cache.py" \
      "$RUN/.env" "$PY" "$CORE" "$CACHE"
unset CDISC_LIBRARY_API_KEY
unset TROPIC_INHERITED_CDISC_LIBRARY_API_KEY

# Fail closed again if the downloaded Library cache differs from the reviewed,
# committed inventory. Cache refresh is a separate explicit maintainer action;
# the ordinary run never rewrites its authority.
clean_env "$PY" "$ROOT/platform/verify_core_cache.py" \
  --cache "$CACHE" \
  --manifest "$ROOT/platform/conformance/core_cache_manifest.json"

# 4a. SDTM baseline: convert the PRISTINE 3.1.1 source sas7bdat -> v5 XPT, validate against CORE's
#     published SDTMIG 3.2 rules. NOTE: source is SDTMIG 3.1.1; CORE's lowest rule set is 3.2 ->
#     version-gap findings expected. Pre-uplift reference run (see CORE_RUN_RECORD.md).
rm -rf "$RUN/sdtm"; mkdir -p "$RUN/sdtm"   # clean dir: validate only these std domains (avoids stale/large-supp deadlock)
Rscript -e 'library(haven); d<-c("dm","ae","ex","ds","vs");
  for(x in d) write_xpt(read_sas(sprintf("01_source_data/real_sdtm/%s.sas7bdat",x)), sprintf(".core_run/sdtm/%s.xpt",x), name=toupper(x), version=5)'
cp "$ROOT/03_metadata/define/define_sdtm.xml" "$RUN/sdtm/define.xml"
clean_env "$PY" -E -s -B "$CORE" validate -s sdtmig -v 3.2 -d "$RUN/sdtm" -ft xpt -dxp "$RUN/sdtm/define.xml" -ca "$CACHE" \
  -rt "$ENGINE/resources/templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_sdtm_report"

# 4b. SDTM authoritative: uplift the pristine source to the SDTMIG 3.4 derived layer (the version the
#     package describes and ships), then validate it against CORE's published SDTMIG 3.4 rules. The
#     uplift never modifies the source. Authoritative SDTM run (see CORE_SDTM34_RUN_RECORD.md).
Rscript "$ROOT/platform/uplift_sdtm_34.R"
rm -rf "$RUN/sdtm34_std"; mkdir -p "$RUN/sdtm34_std"   # clean dir: same 5 std domains as the baseline (avoids large-supp deadlock)
for x in dm ae ex ds vs; do cp "$RUN/sdtm34/$x.xpt" "$RUN/sdtm34_std/$x.xpt"; done
cp "$ROOT/03_metadata/define/define_sdtm.xml" "$RUN/sdtm34_std/define.xml"
clean_env "$PY" -E -s -B "$CORE" validate -s sdtmig -v 3.4 -d "$RUN/sdtm34_std" -ft xpt -dxp "$RUN/sdtm34_std/define.xml" -ca "$CACHE" \
  -rt "$ENGINE/resources/templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_sdtm34_report"

# 5. ADaM: recheck the governed rule files immediately before CORE reads them, then validate the
#    *_prod.xpt against our executable custom rules (CORE has no ADaM pack).
verify_core_rules
rm -rf "$RUN/adam"; mkdir -p "$RUN/adam"; for f in "$ROOT"/04_analysis_datasets/adam/*_prod.xpt; do b=$(basename "$f" _prod.xpt); cp "$f" "$RUN/adam/$b.xpt"; done
rm -f "$RUN/adam/clinsite.xpt"   # BIMO dataset, not ADaM
cp "$ROOT/03_metadata/define/define.xml" "$RUN/adam/define.xml"
clean_env "$PY" -E -s -B "$CORE" validate -s adamig -v 1.3 -d "$RUN/adam" -ft xpt -dxp "$RUN/adam/define.xml" \
  -lr "$RULES_DIR" -ca "$CACHE" \
  -rt "$ENGINE/resources/templates/report-template.xlsx" -ps 1 -of JSON \
  -o "$ROOT/platform/conformance/core_adam_report"

echo "Done. Reports in platform/conformance/ (core_sdtm34_report.json [authoritative], core_sdtm_report.json [3.2 baseline], core_adam_report.json)."

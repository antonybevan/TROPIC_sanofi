#!/usr/bin/env bash
# Authoritative Define-XML 2.1 + ARM validation of define.xml against the vendored CDISC schema.
# This is the full XSD certification (what Pinnacle 21 / CDISC CORE also enforce at the schema
# level); it runs offline with only `xmllint` (libxml2) + the bundled schema/ directory.
#
# Usage:  07_define_xml/validate_xsd.sh [path/to/define.xml]   (default: ./define.xml beside this)
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
SCHEMA="$HERE/schema/cdisc-arm-1.0/arm-extension.xsd"   # ARM-aware entry schema (redefines define-2.1)
DEFINE="${1:-$HERE/define.xml}"

if ! command -v xmllint >/dev/null 2>&1; then
  echo "xmllint (libxml2) not found — install it to run XSD validation." >&2; exit 2
fi

# "Skipping import" lines are benign libxml dedupe warnings for the ODM namespace.
out="$(xmllint --noout --schema "$SCHEMA" "$DEFINE" 2>&1 | grep -v 'Skipping import' || true)"
echo "$out"
if echo "$out" | grep -q ' validates$'; then
  echo "XSD: VALID — conforms to Define-XML 2.1 + ARM v1.0."
  exit 0
fi
echo "XSD: INVALID — see errors above." >&2
exit 1

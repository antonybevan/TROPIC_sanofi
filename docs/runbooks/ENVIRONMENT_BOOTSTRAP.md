# Environment Bootstrap and CI Replay

This runbook defines the two supported data-free setup profiles. It does not
authorize access to excluded patient data or credentials.

## Profile A — reviewer smoke (macOS or Linux)

Prerequisites are R 4.6.0, CPython 3.12.13, Git, and network access to CRAN.
Restore the R library before invoking the demo; a clone alone is not an installed
runtime.

```bash
git clone <repo-url> TROPIC
cd TROPIC

TROPIC_RENV_VERSION="$(python3.12 -c 'import json; print(json.load(open("renv.lock"))["Packages"]["renv"]["Version"])')"
TROPIC_RENV_ARCHIVE="$(mktemp -d)/renv_${TROPIC_RENV_VERSION}.tar.gz"
curl --fail --silent --show-error --location --retry 3 \
  --output "$TROPIC_RENV_ARCHIVE" \
  "https://cran.r-project.org/src/contrib/Archive/renv/renv_${TROPIC_RENV_VERSION}.tar.gz"
python3.12 - "$TROPIC_RENV_ARCHIVE" <<'PY'
import hashlib
import pathlib
import sys

expected = "f462b55ace5436b6bed18e01ac1267649fc196ad8505f55c8546704eda104bfb"
actual = hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest()
if actual != expected:
    raise SystemExit(f"renv archive SHA-256 mismatch: {actual}")
PY
R CMD INSTALL "$TROPIC_RENV_ARCHIVE"
test "$(Rscript -e 'cat(as.character(packageVersion("renv")))')" = "$TROPIC_RENV_VERSION"
Rscript -e 'renv::restore(prompt = FALSE)'
python3.12 platform/cibuild.py --demo
```

The smoke parses the R programs and challenges the reconciliation method with
synthetic fixtures. It does not run SAS, touch patient data, or qualify a release.

## Profile B — exact functional-CI replay

The Python artifact lock is intentionally scoped to **Ubuntu 24.04 x86_64 and
CPython 3.12.13**. Use that platform (a VM or container is acceptable) for lock-
equivalent replay. macOS execution may be useful engineering evidence, but it is
not the controlled Linux artifact-lock claim.

Install the same system packages used by CI:

```bash
sudo apt-get update
sudo apt-get install --no-install-recommends -y \
  fonts-liberation2 ghostscript libxml2-dev libssl-dev libcurl4-openssl-dev \
  libxml2-utils poppler-utils
```

Then restore the Python and R environments and run the functional surface:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes --only-binary=:all: \
  --requirement requirements-ci-build.lock
.venv/bin/python -m pip install --require-hashes --no-build-isolation \
  --requirement requirements-ci.txt
.venv/bin/python -m pip check

# Use the hash-verified renv bootstrap from Profile A, then:
Rscript -e 'renv::restore(prompt = FALSE)'
.venv/bin/python -m pytest -q -m "not release_qualification" tests
.venv/bin/python platform/build_delivery_controls.py --ci
.venv/bin/python platform/check_submission_readiness.py
.venv/bin/python platform/check_regulatory_source_inventory.py
.venv/bin/python platform/lint_sas.py
git diff --check
```

The authoritative job order, pinned GitHub Actions, secret scan, R lint, PDF
checks, and additional conformance commands remain in
[`../../.github/workflows/ci.yml`](../../.github/workflows/ci.yml). The dedicated
`release_qualification` job is intentionally excluded above: it requires a current
genuine full-DAG SAS run and must remain red when that evidence is absent.

## Failure handling

- Do not loosen hashes, select a different Python minor version, or add
  `continue-on-error` to make bootstrap pass.
- Treat a changed download hash as a supply-chain review event.
- Treat an unavailable package repository as an external dependency failure; use
  a reviewed mirror or retry later, and record the deviation.
- Delete disposable virtual environments normally; never delete source, evidence,
  or repository roots as part of cleanup.

# Repository professional-build audit — 2026-08-14

## Outcome

The repository now has a clearer public operating surface, executable hygiene checks, and
fail-closed security/data-boundary controls. The clinical directory numbering was retained: it is the controlled review
and evidence taxonomy documented in [`docs/REPO_SURFACE_POLICY.md`](../../docs/REPO_SURFACE_POLICY.md),
not accidental root clutter that should be flattened.

This audit is a repository-quality and security-hardening pass. It does not turn the project into a
validated GxP system, grant a software license, add patient data, or replace the genuine SAS/ODA
release seal.

## Scope and method

- Whole Git revision audited: `94b6b1a` (the pre-audit branch tip), 457 tracked files.
- Review surfaces: governance, source/data boundaries, specifications, metadata, programs,
  outputs, QC evidence, reviewer explanation, package materialization, platform orchestration,
  configuration, CI, dependencies, tests, and ignored local runtime boundaries.
- Static checks: tracked-secret filename/pattern review, Markdown link review, shell syntax,
  Python compilation, Git diff whitespace, dependency-lock review, CI/release-control review, and
  source-backed security analysis of filesystem, process, network, deserialization, and SAS-code
  boundaries.
- Runtime checks: the pinned Python CI environment, data-free and local-data R contracts, and the
  existing release verifier. No credentials or patient-level content were read or added.

## Changes made

### Repository operating surface

- Added [`CONTRIBUTING.md`](../../CONTRIBUTING.md) with branch/PR, test, data-boundary, and seal
  expectations.
- Added [`SECURITY.md`](../../SECURITY.md) with private-reporting guidance and explicit patient,
  credential, and release-boundary rules.
- Added [`docs/LICENSING.md`](../../docs/LICENSING.md) and corrected the README: the repository
  currently declares no open-source license; public visibility is not a reuse license.
- Added `.hermes.md` and `tmp/` to `.gitignore`; retained the existing intentional exclusions for
  patient data, credentials, engine installs, runtime telemetry, and generated package payloads.
- Removed machine-specific `file:///Users/...` links from active reviewer/changelog surfaces in
  favor of repository-relative links.
- Tightened local credential permissions to mode `0600` for the existing ignored `_authinfo` and
  `sascfg_personal.py` files and the ignored CORE runtime (`.core_run/`) to `0700`; the credential
  file contents were not read.
- Added `tests/test_repository_hygiene.py` to keep the above public-surface and data-boundary rules
  executable in CI, and added `tests/test_define_parser_security.py` for the Define-XML parser.

### Security hardening

- Added `validate_remote_path()` and applied it before ODA paths enter SAS source, including the
  account-home expansion and the Stage-10 / TFL renderer roots. Quotes, macro characters,
  statement terminators, empty segments, traversal, whitespace, and relative paths are rejected.
- Replaced unrestricted offline CDISC cache `pickle.load()` with a restricted unpickler that only
  permits JSON-like builtin containers/scalars. A malicious global is rejected before execution.
- Added strict manifest dataset-name validation and rejected symlink/non-regular SDTM inputs.
- Bound Stage-10 SDTM verification to the validated ODA project root; decoy SDTM directories and
  unsafe returned ODA homes are rejected before SAS submission.
- Enforced `0600` files/`0700` directories across patient-level package, Dataset-JSON, staging,
  and eCTD materialization generators.
- Replaced source-derived SUPP `IDVAR` macro interpolation with a static domain map and fail-closed
  validation in both the working and packaged SAS program.
- Pinned the local CDISC CORE package/version and verified its immutable source commit.
- Added regression tests for malicious ODA paths, malicious returned ODA homes, invalid Stage-10
  roots, malicious pickle globals, symlinked SDTM inputs, manifest traversal, permissions, and parser
  external-entity handling.

## Validation evidence

| Check | Result |
|---|---|
| `uv run --with-requirements requirements-ci.lock pytest -q` | **217 passed** |
| `platform/test_oda_broker.py` with the pinned local environment | **95 passed** |
| Shiny data-free and local production contract suites | **PASS** |
| R smoke, F-042, lab-shift, population, TFL-statistics, and figure-output suites | **PASS** |
| Python compilation, shell `bash -n`, `git diff --check` | **PASS** |
| Tracked credential/data filename audit and active Markdown links | **PASS** |
| `scripts/verify_release.py` | **40/43; seal blocked by stale source/artifact hashes after this change and the existing real-SAS seal state** |

The release-verifier failures are intentional evidence, not suppressed gates. The source tree and
release artifacts must be regenerated and resealed after the owner-approved change set; a fresh
genuine SAS/ODA run is required before the project can claim a current clinical release.

## Residual risks and handoff

1. **Release seal:** rerun the genuine SAS/ODA path, regenerate package/QC outputs, and run
   `python3 scripts/verify_release.py` until source-tree, source-hash, and artifact-hash checks
   agree. Do not reseal from the demo or cached path.
2. **Ownership/licensing:** choose and approve a license before describing the repository as
   open-source. Until then, the new licensing notice is the authoritative boundary.
3. **Clinical/data scope:** the public clone remains data-free with respect to patient-level source
   and derived datasets. The simulation operating-characteristics workstream remains exploratory,
   non-MIDD, non-confirmatory, and not a filing claim.
4. **External services:** ODA, SAS, CDISC Library credentials, and licensed source materials are
   external prerequisites. They were not exercised by this audit.

## Security review pointer

The independent repository security scan is recorded in the Codex Security workbench for scan
`59885955-dad6-4f4d-89e8-aceb41c7f99e` and completed with 8 reportable findings (3 high, 3 medium,
2 low) against the pre-audit revision. The canonical workbench record is identified
by the scan ID above; its temporary machine-local report path was intentionally not
retained as a repository link. This document records the implementation and validation handoff.

Disposition: patient-output permissions, Define-XML entity handling, SUPP-IDVAR interpolation,
ODA path/root binding, CT-cache traversal/deserialization, and manifest-name traversal are fixed
and regression-tested. Credential rotation/backup cleanup remains owner action, and end-to-end
dependency hash locking (Python/R artifacts) remains a follow-up before treating the build as
fully supply-chain hardened.

## 2026-08-24 professional-build second pass

The follow-up whole-repository review completed standard security scan
`81056d45-0e9b-4bb9-854e-efb3a93ffc38` and closed the six validated findings in
F-051–F-056. In particular, the earlier Python supply-chain follow-up is now
implemented for the CI and CORE execution surfaces: runtime and build requirements
are artifact-hash locked, build isolation is disabled, installed distributions are
checked, Dependabot covers GitHub Actions and Python, dependency review blocks new
moderate-or-higher dependency risk, and CodeQL analyzes both Python and GitHub
Actions using commit-pinned actions.

Repository conventions now also include `.editorconfig`, a PR template, current
dependency-update policy, a concise factual changelog, a consistent `renv.lock`
including the R linter toolchain, and a self-contained TFL gallery with no externally
loaded scripts, styles, or fonts. The regulatory inventory distinguishes released
requirements from drafts/review material—most notably Step 2b ICH E20 and the CDISC
Package 62 public-review material—and
the filing profile explicitly blocks regulatory shipment pending sponsor-specific
qualification, QC, rights, current validator evidence, and accountable approvals.

The release boundary was strengthened beyond the original audit: governance reseals
are authorized by a single downstream-enforced policy and immutable Git objects;
package/eCTD filesystem operations fail closed on symlinks, parent swaps, and
unreadable descendants; the ODA personal configuration is validated before execution;
CDISC credentials are scoped to the one network operation that needs them; and the
custom CORE rule set is independently hash locked. These source changes require a new
genuine-SAS full-DAG run, clean seal, clean-checkout verification, and green PR checks
before promotion. They do not alter the non-submission, non-Part-11, non-FDA-approved
product boundary.

### 2026-08-24 controlled execution update

The first fresh run against the reviewed source commit passed stages 1-16, then
exhausted the one-hour ODA connection budget after 44 encryption-key-exchange
terminations. An original-config diagnostic reproduced the failure, excluding the
new verified-copy hardening as the cause. The orchestrator labelled its fallback as
simulated, reconciliation rejected it, emitted RED `partial_dag` telemetry (18/41),
and rolled controlled clinical outputs back. No current SAS seal was built.

The work that does not depend on SAS was completed without weakening that blocker:
the 400,000-replicate simulation bundle and independent verifier pass; the draft
Module 5/eCTD tree validates 99/99 leaves; and all 62 pages across six generated PDFs
pass visual, bounds, header/footer, outline, font-embedding, and Fast-Web-View checks.
The package pass also found and fixed a macOS portability defect where the no-follow
layer correctly rejected the default `/var` temporary-directory symlink; renderer
scratch now stays under controlled ignored `tmp/pdf-render/` with mode `0700`.

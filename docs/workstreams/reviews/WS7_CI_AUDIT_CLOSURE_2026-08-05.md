# WS-7 Review Note — CI Audit Closure (2026-08-05)

**Date:** 2026-08-05
**Workstream:** WS-7 Release Engineering
**Product claim:** Path A — controlled non-submission clinical biometrics programming
demonstration. Not an FDA filing, not Part 11, not a re-analysis of trial efficacy.
**Scope:** Close the findings from the 2026-08-05 repo-pipeline audit
(`.github/workflows/ci.yml`, `scripts/verify_release.py`, `platform/cibuild.py`,
and the data-free test surface) with in-repo fixes and governance records.

## Findings closed

| ID | Severity | Fix |
|---|---|---|
| F-044 | Major | CI now runs `tests/test_pipeline_abort_scope.py`, `tests/test_define_arm_contract.py`, `tests/test_f042_sas_response_control.py` via pytest, and `tests/test_f042_provisional_pain_derivation.R` via Rscript, in a dedicated validate-job step. |
| F-045 | Major | `tests/test_f042_sas_response_control.py` now always asserts the tracked `08_submission_package/m5/...` program copy matches source, and skips only the gitignored materialized `08_submission_package/ectd/0000/m5/...` copy when absent (`pytest.mark.skipif`), so the file runs in data-free CI. |
| F-046 | Major | The CT cross-validation step runs as a hard gate when `CDISC_LIBRARY_API_KEY` is configured and otherwise prints an explicit SKIPPED line; a new `platform/ci_coverage_summary.py` step reports which conformance gates executed versus skipped so a green CI is not mistaken for full conformance. |
| F-047 | Minor (ACCEPTED) | Repo-side wiring is complete; the key already exists locally in gitignored `.core_run/.env`, but enabling the hard CT gate in CI still requires adding it as a GitHub repository secret (external action). |
| F-048 | Medium | A gitleaks v8.18.4 scan (pinned, matching `.pre-commit-config.yaml`) runs as the first check in the validate job. |
| F-049 | Medium | R is pinned to `4.6.0` (the audited release) and `requirements-ci.txt` pins the CI Python toolchain at the versions verified on 2026-08-05; a full transitive lockfile remains future work. |
| F-050 | Low | Workflow hardening: `permissions: contents: read`, `concurrency` with `cancel-in-progress`, `timeout-minutes` on both jobs, and `workflow_dispatch`. |

## Changes

- `.github/workflows/ci.yml` — triggers, permissions, concurrency, timeouts,
  gitleaks, pinned R, `requirements-ci.txt` install, data-free regression tests,
  conditional CT enforcement, conformance-coverage summary.
- `requirements-ci.txt` — new pinned top-level CI Python dependencies.
- `tests/test_f042_sas_response_control.py` — tracked-copy assertion always runs;
  materialized eCTD copy assertion skips when the copy is absent.
- `platform/ci_coverage_summary.py` — new data-free conformance coverage report.
- `06_qc_evidence/audit/findings_register.csv` — F-044..F-050 recorded.

## Verification (local, 2026-08-05)

| Check | Result |
|---|---|
| `python3 -m pytest -q tests/test_pipeline_abort_scope.py tests/test_define_arm_contract.py tests/test_f042_sas_response_control.py` | 11 passed locally (materialized eCTD copy present); on a fresh data-free CI checkout the materialized-copy test skips (10 passed, 1 skipped) |
| `RENV_CONFIG_SANDBOX_ENABLED=false Rscript tests/test_f042_provisional_pain_derivation.R` | PASS (synthetic rule-boundary coverage) |
| `python3 scripts/verify_release.py` | 31/31 PASS, exit 0 |
| Worktree | clean before edits; changes are the intended fix set |
| `ci.yml` YAML parse | OK (2 jobs: path-a-seal-verify, validate) |

## Honesty

- The workflow changes were **not** executed on a real GitHub runner from this
  environment; they require a push/PR to validate end-to-end.
- CI remains data-free by design: real XPTs, SAS/ODA, the CDISC Library key/cache,
  and the full CDISC CORE engine are not part of the runner. The coverage summary
  makes that boundary explicit rather than implied.
- The key exists locally in gitignored `.core_run/.env` (used by local CORE/CT
  runs); until the same value is configured as a GitHub repository secret, the CI
  CT gate reports SKIPPED (F-047, accepted external dependency).

## Exit

F-044..F-050 closed (F-047 accepted as an external dependency). Next action:
push the branch and confirm the validate job is green on GitHub; configure
`CDISC_LIBRARY_API_KEY` to turn the CT gate into a hard check.

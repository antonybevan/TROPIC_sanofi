# Repository Cleanup and Completion Audit — 2026-08-23

**Repository:** TROPIC controlled clinical-submission simulation

**Scope:** tracked and ignored repository surface, executable reachability,
duplicate classification, active governance/current-state accuracy, CI collection,
metadata-control fail-closed behavior, local privacy hygiene, and release evidence.

**Product boundary:** this audit improves the engineering and evidence surface. It
does not create sponsor approval, independent organizational QC, a validated Part 11
system, licensed Pinnacle 21 Enterprise clearance, a true aCRF/application identity,
or FDA filing readiness.

## Executive decision

The audit found no accidental duplicate clinical payload among the tracked exact-byte
duplicate groups. The material duplicate groups are controlled source-to-Module-5
materializations or frozen/current evidence snapshots and are intentionally retained.

The material cleanup findings were stale governance classifications, two malformed
findings-register rows, a fail-open metadata-control prerequisite, incomplete Python
test collection in CI, an obsolete SAP authority in ARS, a tracked empty listings
placeholder, three abandoned audit scripts, a dangerous ignored local code archive,
machine-local/broken links, stale run/P21/release identity claims, and local temporary
or credential-hash exposure. These were corrected without deleting patient data,
clinical results, validation runtimes, or controlled package copies.

## Prioritized disposition

| Priority | Finding | Disposition |
|---|---|---|
| P0 | `findings_register.csv` rows F-023/F-047 had excess columns and could shift remediation fields | Fixed; G00 and CI now require exact schema, row width, required fields, and unique IDs |
| P0 | Metadata report treated absent traceability/drift inputs as empty evidence | Fixed; a named manifest stage regenerates both inputs and fails closed on missing, empty, malformed, gap, or current-XPT-missing evidence |
| P0 | ARS ReportingEvent bound `TROPIC SAP v3.0` instead of current SAP v4.0 authority | Fixed in generator and artifact; regression-gated |
| P0 | Active traceability/P21/release-identity documents contradicted current evidence or Git tag state | Corrected; the candidate is explicitly unreleased and Community/Enterprise boundaries are synchronized |
| P1 | Orphan register called orchestrated CbzP/additive layers unfinished and called absent NDJSON stale | Rebuilt dynamically; current governed candidate set has zero `CONFIRMED` entries |
| P1 | CI ran a hand-maintained pytest subset, omitting math/fail-closed/DAG/staging modules | Fixed; CI collects the complete `tests/` Python directory |
| P1 | Tracked `listings/.gitkeep` contradicted the controlled no-listings policy | Removed; recurrence is regression-gated |
| P1 | Local inventory read and hashed credential files | Fixed; all exact credential names and `*.env` files are excluded before byte reads; local inventories are mode `0600` |
| P1 | ODA-downloaded patient-derived XPT/result CSV files inherited mode `0644` | Fixed; atomic promotion now restricts temporary files to `0600`, current artifacts were repaired, and CI covers both genuine-download and simulated-copy paths |
| P1 | Obsolete source-tree staging directory duplicated the governed analysis staging layer | Removed recoverably after all 11 RDS hashes matched `04_analysis_datasets/staging/`; the raw source directory was retained |
| P1 | Active links resolved only on the data-bearing developer tree | Fixed; active Markdown links must resolve to Git-tracked targets or tracked directories |
| P2 | Abandoned audit utilities and dangerous ignored archive remained available | Removed recoverably; provenance remains in Git history and this report |
| P3 | Legacy internal `cibuild.py` helper/comment names contain historical stage ordinals | Deferred; they are internal compatibility labels, not current stage authority. A future rename must preserve tests and telemetry compatibility. |

## Removed material

Tracked removals:

- `05_outputs/tfl/output/listings/.gitkeep` — empty output scaffolding falsely
  hash-bound as a controlled listing;
- `06_qc_evidence/audit/build_dataset_metadata.py` — one-off local structural
  inventory superseded by current conformance/metadata controls;
- `06_qc_evidence/audit/build_dual_language_comparison.py` — obsolete comparison
  logic superseded by governed key/value/result reconciliation;
- `06_qc_evidence/audit/build_rds_metadata.R` — broken-path historical one-off with
  no current consumer.

Recoverable local removals (moved to macOS Trash, not permanently erased):

- `tools/archive/` containing two unsafe Git rescue/push snippets and two historical
  one-time migration/remediation utilities;
- 62 temporary JPEG pages under `tmp/pdfs/figure_fix_qa.*`;
- stale ignored `dataset_metadata.csv`, `dual_language_comparison.csv`, and
  `rds_metadata.csv` audit outputs;
- the obsolete `01_source_data/real_sdtm/staging/` directory after all 11 RDS files
  were proven byte-identical to the private governed copies under
  `04_analysis_datasets/staging/`;
- Python/pytest caches and empty generated directories.

## Retained material

- Patient/source data, production ADaM XPTs, reviewer outputs, and materialized eCTD
  payloads were not deleted.
- The `.core_engine`, `.core_run`, and `.core_venv` local validation installations
  were retained. They are large (approximately 806 MB, 730 MB, and 442 MB) but are
  active, expensive-to-restore CDISC CORE capability, not repository clutter.
- `_authinfo`, `sascfg_personal.py`, `.Rprofile`, and other ignored local operator
  configuration were retained; credential files had restrictive permissions and their
  contents were not inspected.
- Current patient-derived ODA XPT/result CSV files and governed staging RDS files were
  retained and restricted to mode `0600`; their parent clinical-data directories remain
  mode `0700`.
- `platform/_oda_render_tfl.py` remains a documented manual diagnostic, never release
  evidence.
- SAP v3.0 remains as the historical predecessor used to reproduce SAP v4.0; current
  ARS and analysis authority bind only v4.0.
- CbzP reconstruction, Guyot helper/validation, XPT export, bridge parity,
  Dataset-JSON, ARS, and USDM were retained because they are active orchestrated or
  explicitly additive capabilities.

## Duplicate classification

The independent exact-byte scan at audit entry found 64 duplicate blob groups / 130
instances. Every group was an intentional controlled copy: source programs,
stylesheets, Define/specification artifacts, figures/tables, or reviewer documents
materialized into Module 5/eCTD, plus frozen/current evidence snapshots. Removing
these copies would damage the submission-style review surface and package-integrity
checks. No accidental tracked exact duplicate was approved for deletion.

## Remaining real work

The following are not abandoned programming items and were not auto-fixed:

- external qualified statistical/medical review and independent accountable approval;
- licensed Pinnacle 21 Enterprise execution and independent disposition approval;
- GitHub `CDISC_LIBRARY_API_KEY` repository-secret configuration (F-047);
- true sponsor application identifiers, annotated CRF, full two-arm authoritative IPD,
  organizational validation/Part 11 controls, and gateway evidence;
- W-ADAM-02 hard-fail policy for the source-fidelity TEAE `AESER` residual, which
  requires an approved scope decision rather than automatic imputation;
- W-ADAM-05/full deferred TFL or ARS expansion, which requires approved SAP scope.

## Verification record

Final full-DAG, test, lint, release-seal, clean-checkout, Computer Use, and CI evidence
is recorded in the closing section after the implementation commit. Until those
checks pass, this report is an implementation record rather than a promotion record.

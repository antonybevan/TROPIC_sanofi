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
| P1 | The new metadata-refresh stage executed but had no orchestrator-to-governance mapping, leaving the generated gate map at `fail` | Fixed; stage 39 maps to G03/G06 and a full-manifest regression requires all 41 stages to remain mapped |
| P1 | Tracked `listings/.gitkeep` contradicted the controlled no-listings policy | Removed; recurrence is regression-gated |
| P1 | Local inventory read and hashed credential files | Fixed; all exact credential names and `*.env` files are excluded before byte reads; local inventories are mode `0600` |
| P1 | ODA-downloaded patient-derived XPT/result CSV files inherited mode `0644` | Fixed; atomic promotion now restricts temporary files to `0600`, current artifacts were repaired, and CI covers both genuine-download and simulated-copy paths |
| P1 | Obsolete source-tree staging directory duplicated the governed analysis staging layer | Removed recoverably after all 11 RDS hashes matched `04_analysis_datasets/staging/`; the raw source directory was retained |
| P1 | Active links resolved only on the data-bearing developer tree | Fixed; active Markdown links must resolve to Git-tracked targets or tracked directories |
| P2 | The ignored detailed TFL index could be built before new ODA figures were transactionally promoted, so hashes matched but displayed companion mtimes described the prior identical-byte run | Refreshed after promotion; the release-binding stage now rebuilds the index post-output and fails closed on execution, unreadable status, or non-PASS status. Current evidence has zero missing, stale, unindexed, or semantic findings |
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

## Closing verification record

### Production execution and numerical evidence

- A genuine SAS OnDemand for Academics run completed **41/41 stages PASS** on
  2026-08-23 with SAS `9.04.01M8P022223`, `run_scope=full_dag`,
  `sas_execution_mode=oda`, and GREEN pipeline health. The health timestamp is
  `2026-08-23T17:47:35.766117+00:00`; the run-bound source-tree SHA-256 is
  `6b2e272130b0936f4f2156bf8f4352f4c3428a9c01eb772e29614c14ce970e91`.
- All seven production/validation ADaM pairs and the clinical-site pair were
  byte-distinct and passed key, value, label, order, date-precision, result, forest,
  and figure-data reconciliation. The simulation completed 400,000/400,000
  replicates with zero failures and passed independent recomputation while retaining
  `NOT_QUALIFIED` for clinical/filing use.
- ADaM conformance returned zero findings. Define-XML 2.1/ARM validation passed 522
  ADaM checks and 351 SDTM checks. Specification-to-Define and
  specification-to-data checks passed all 7 datasets / 161 variables. The pipeline
  DAG validated all 41 stages and their gate/order/parallel-boundary contracts.

### External-validator evidence boundary

- Pinnacle 21 Community 4.1.0 (`p21-client-1.0.8.jar`) was rerun against byte-identical
  standard-named copies of the seven current production XPTs using FDA engine 2508.1,
  ADaM-IG 1.3, Define-XML 2.1, and CT 2024-03-29.
- The process generated a report and completed with the retained CLI compatibility
  caveat: 7 datasets, 121,320 records, 0 rejects, 388 rules, 30 issue groups, and
  2,373 occurrences. The report SHA-256 is
  `05cf6f82c46ba958fdd659f9f60f41fa5e9fd2bf7f59eba443b83fd428d89cb5`.
- The retained local workbook is outside Git and restricted to owner-only mode
  `0600`; the temporary standard-named XPT staging directory was moved recoverably
  to Trash after hash verification.
- This is informative Community evidence with open findings. It is not licensed
  Enterprise execution, qualified disposition approval, or regulatory clearance.

### Code, conformance, and provenance regression

- Complete Python collection: **166 passed**. ODA/broker suite: **95 passed**.
- R endpoint, laboratory-shift, figure, population, dashboard data-free, and local
  production-data dashboard suites: **all passed**. R lint: **0 findings across 40
  files**. SAS static analysis: **0 errors and 0 warnings across 17 files**.
- Seven custom CDISC CORE ADaM rules passed well-formedness validation. G07 reviewer
  package lock, regulatory baseline, scoped official-source inventory, simulation
  independent check, committed GREEN-ODA evidence consistency, and the 41/41
  orchestrator-to-governance gate map all passed.
- Exact-byte duplicate review classified 64 groups / 130 instances as intentional
  package materializations or evidence snapshots. The regenerated orphan register
  contains 23 governed candidates and zero `CONFIRMED` abandoned artifacts.

### Visual and interaction verification

- All 13 final figure PNGs were inspected and passed the 2400-pixel/opacity contract.
  R/SAS numerical semantics reconciled, including 13/13 subgroup rows, 32/32 risk
  counts, 690 waterfall subjects, 60 swimmer subjects, and 730 exposure-response
  observations.
- Six reviewer PDFs (ADRG 14 pages, cSDRG 8, BDRG 5, CSR 7, simulation MAP 13, and
  simulation report 15) were rendered and visually inspected across all **62 pages**.
  No clipping, overlap, blank page, malformed glyph, missing content, or margin loss
  was observed.
- Computer Use exercised every static-gallery card repeatedly by pointer and keyboard,
  exposed and verified the modal focus fix, and exercised every dashboard tab, all six
  KM endpoints twice, Safety valid/invalid bounds, filter toggles, sidebar states, and
  Reconciliation sorting without a visible application error or disconnect.

### Seal and CI boundary

This report is part of the governed source change, so it cannot truthfully contain
its own final hash seal without circularity. The post-report change-control sequence
is: commit this bounded governance/UI evidence, rebind it to the genuine ODA evidence
commit, build the release-run manifest and candidate checklist from a clean tree,
verify the resulting commit again from a fresh checkout, and require the GitHub PR
checks. Those machine records and PR checks are the authoritative seal/CI evidence;
they do not turn the demonstration into a filing-ready or validated system.

The Codex Security deep-scan worker was not reportable in this environment because
its managed read-only filesystem permission profile could not be established. No
claim of a completed deep security scan is made. Secret scanning, dependency locks,
static source controls, fail-closed path/credential handling, and repository hygiene
tests remain in the executed CI/local control surface.

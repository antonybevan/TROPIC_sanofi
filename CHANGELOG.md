# Changelog

All notable changes to the **TROPIC (Study EFC6193 / XRP6258)** pipeline will be documented in this file. This log serves as the program version control history, in support of 21 CFR Part 11 electronic records auditing.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

## [3.5.4] - 2026-06-13 — Define-XML FULLY XSD-validated (offline, reproducible)

### Added
- **`define.xml` now passes full XSD validation** against the official CDISC Define-XML 2.1 + ARM
  v1.0 schema (`xmllint --noout --schema … define.xml` → *validates*). The previously "offline-only"
  certification step is now **done and reproducible in-repo**: the freely-distributable CDISC schema
  bundle is vendored under `07_define_xml/schema/` (240 KB, 12 XSDs; ARM entry schema
  `cdisc-arm-1.0/arm-extension.xsd`), with `07_define_xml/validate_xsd.sh` as the one-command wrapper
  and `07_define_xml/schema/NOTICE.md` documenting provenance.

### Fixed (conformance issues the real validator surfaced that the structural gate could not)
- `<ODM>` was missing the **required `def:Context`** attribute → added (`Submission`).
- `MetaDataVersion` was a sibling of `<Study>` → **nested inside `<Study>`** per ODM 1.3.2.
- `ItemRef/@Order` → **`@OrderNumber`** (147); `Label` attribute (not allowed on `ItemGroupDef`/
  `ItemDef`) → moved to `Description/TranslatedText` (154 ItemDefs) / dropped on 7 ItemGroupDefs.
- Stale `ItemDef/@ValueListOID` (3) removed — superseded by the `def:ValueListRef` child.
- `MetaDataVersion` children **reordered into the schema-mandated sequence** (Standards →
  ValueListDef/WhereClauseDef → ItemGroupDef/ItemDef/CodeList/MethodDef → CommentDef → ARM).
- `RangeCheck` given the required **`def:ItemOID`** + **`SoftHard`** (was plain `ItemOID`).
- ARM `AnalysisProgrammingCode` → correct **`arm:ProgrammingCode`**.

## [3.5.3] - 2026-06-13 — Define-XML Conformance, ARM, Conformance Gate & Reconciliation Hardening

### Added
- **Runnable Define-XML conformance gate (`07_define_xml/validate_define.py`).** Self-contained
  (no network) check of the structural + referential-integrity rules a validator enforces: ODM
  root/namespaces, required Study/GlobalVariables/MetaDataVersion/def:Standards/def:DefineVersion,
  every ItemRef/Method/CodeList/WhereClause/ValueList/Comment/ARM reference resolves, leaf↔
  ArchiveLocationID, and Description↔TranslatedText. PASS on the remediated file (244 checks);
  correctly FAILs the pre-remediation file (6 violations) — it is a real gate, not a rubber stamp.
  This is the honest local conformance check; full Pinnacle 21 / CDISC CORE remains the offline step.
- **Analysis Results Metadata (ARM v1.0)** for the headline efficacy analyses — `arm:ResultDisplay`
  with `arm:AnalysisResult` for OS and PFS (stratified Cox / log-rank, CbzP vs MP), referencing the
  real ADTTE WhereClauses/variables and the R derivation code. Applied by a one-shot transform
  (recorded in git history); passes the conformance gate.

### Changed
- **Reconciliation methodology documented precisely (`05_reconciliation/cross_lang_audit.R`).**
  Corrected the stale comment that claimed "ADAE has no AESEQ key" — ADAE retains AESEQ end-to-end
  and is reconciled on the unique key `USUBJID+AESEQ`; only the genuinely keyless domains
  (ADCM/ADLB/ADRS/ADEX) use the multiset test. Documented the **residual limitation** explicitly:
  like all double-programming, reconciliation cannot catch a *correlated* error (both tracks
  identical-wrong) — inherent, not specific to the multiset path.
- **`tests/smoke_test.R`** gains Case E (multiset detects a changed cell amid duplicate/tied rows),
  hardening the keyless-path coverage. Full smoke test passes.

### Fixed
- Pre-existing `define2-1.xsl` parse bug fixed: the embedded JavaScript's unescaped `<` is now
  wrapped in `CDATA`, so the stylesheet parses. (It still renders blank against the now-conformant
  ODM-namespaced define because its XPath is not namespace-aware — see Known below.)

### Fixed (Define-XML namespace re-architecture)
- **Re-architected `07_define_xml/define.xml` to conformant Define-XML 2.1.** The document
  previously used a non-spec `<Define>` root with the **def/v2.1 namespace as default**, placing the
  entire structural backbone (`ItemGroupDef`/`ItemDef`/`ItemRef`/`CodeList`/`MethodDef`) in the wrong
  namespace — it parsed as XML but **any Define-XML validator / Pinnacle 21 / CDISC CORE would reject
  it**, undercutting the project's regulatory claim. Now:
  - root is `<ODM ODMVersion="1.3.2" FileType="Snapshot">` in the ODM 1.3.2 namespace, with
    `def:`/`xlink:`/`xsi:` prefixes bound and `schemaLocation` pointing at the ODM+define schema;
  - the ODM backbone is unprefixed; define extensions take `def:` (`def:Origin` ×154,
    `def:ValueListDef`, `def:WhereClauseDef`, `def:WhereClauseRef`, `def:CommentDef`, `def:leaf`,
    `def:Standards`);
  - added the required `Study`/`GlobalVariables`, `def:Standards` (ADaMIG 1.3) + `def:DefineVersion`,
    a `def:leaf` archive location per dataset, wrapped bare `Description` text in `TranslatedText`,
    dropped the non-standard `Role` attribute on `ItemGroupDef`, converted `CommentRef` elements to
    `def:CommentOID` attributes, and wired the base AVAL ItemDefs to their `def:ValueListRef`.
  - **Verified locally:** referential integrity fully resolves (every ItemRef/Method/CodeList/
    WhereClause/ValueList/Comment reference + leaf/ArchiveLocationID); exact content parity vs. the
    prior file (154 ItemDefs, 7 groups, 7 codelists, 14 methods, 26 codelist items — none lost).
    Full XSD validation against `define2-1-0.xsd` is to be run offline (schema host unreachable in CI):
    `xmllint --noout --schema define2-1-0.xsd 07_define_xml/define.xml`.
  - The re-architecture was applied by a one-shot transform (recorded in git history); the reusable
    `07_define_xml/validate_define.py` conformance gate remains in the repo for ongoing checks.

### Known (separate, pre-existing)
- `07_define_xml/define2-1.xsl` now parses (CDATA fix above) but renders blank against the conformant
  define because its XPath is not ODM-namespace-aware. The bundled custom stylesheet should be replaced
  with the official CDISC `define2-1.xsl`, which is namespace-aware and pairs with the ODM structure;
  rewriting the custom one's XPath is not worthwhile for an artifact slated for replacement.

## [3.5.2] - 2026-06-12 — Resilient ODA Execution (Broker + Idempotent Seed)

### Added
- **`06_telemetry/oda_broker.py` — connection broker** (single source of truth for connecting to
  ODA). Replaces blind retries with: status-gated **full-jitter exponential backoff** within a
  wall-clock budget; an **error taxonomy** that fails fast on `AUTH`/`CONFIG_ENCRYPTION` and only
  retries transient classes; **slot hygiene** (single-flight lock + orphan sweep + guaranteed
  teardown) to stop orphaned ODA workspace sessions; a **live nonce probe** so
  `sas_execution_mode='oda'` is *earned*, never asserted from a bare connection; and an attempt
  **ledger** (`oda_status.json`) feeding `recommend_window()`.
- **`06_telemetry/seed_sdtm.py` — idempotent, integrity-checked SDTM seeding (Job A).** Computes a
  per-dataset `sha256`/`nrows` manifest; uploads only on mismatch; re-reads ODA row counts to
  detect a half-upload; writes the manifest sentinel **last** (transactional). `--force` overrides.
- **`06_telemetry/test_oda_broker.py`** — 10 unit tests (injected fakes; no Java/network) covering
  earned-mode-via-probe, teardown on failed spawn, fail-fast classes, jittered backoff, the error
  taxonomy, idempotent seed, and unverified-library detection.
- **Extended `pipeline_health.json` contract:** on genuine ODA success records `oda_endpoint`,
  `oda_attempts`, `oda_total_wait_s`, `sdtm_manifest_sha`, `probe_nonce_echoed`,
  `reconciliation='SAS_vs_R'`, `reconciliation_status`; on give-up records `oda_last_error_class`,
  `next_recommended_window`, `reconciliation='sim_only'`.

### Changed
- **`cibuild.py` Stage 10 is now reconcile-only (Job B).** It connects via the broker and
  **verifies the SDTM manifest before running** — if the library is missing/stale it fails with a
  clear "run seed_sdtm.py" message instead of silently simulating. On connection-budget exhaustion
  it falls back to sim **honestly labeled** (mode downgraded to `sim` in telemetry). Superseded the
  inline `_oda_connect`/`_sync_sdtm` helpers. `TROPIC_ODA_RETRIES` retained as a back-compat alias
  onto the broker's `max_wait_s`.

## [3.5.1] - 2026-06-12 — ODA Efficiency & Reproducibility Hardening

### Added
- **Incremental SDTM upload to ODA (`06_telemetry/cibuild.py`).** Stage 10 now uploads only
  the SDTM files that are **missing or changed on ODA** (compared by byte size against the
  persistent ODA `$HOME`), instead of re-pushing the full ~200 MB every run. On an unchanged
  run this skips the entire upload, cutting a genuine real-SAS run from ~6–16 min to ~1–2 min.
  The sync is **fail-safe**: any listing/size uncertainty falls back to uploading the file, so
  SAS never executes against stale or missing data.
- **Resilient ODA connect (`_oda_connect`).** ODA's load-balancing object spawner times out
  under load; the connection now retries with backoff (default 5×/20 s, tunable via
  `TROPIC_ODA_RETRIES`/`TROPIC_ODA_BACKOFF`) and only proceeds once a workspace has actually
  spawned, so a transient ODA timeout no longer fails the whole pipeline.
- **`--force-upload-sdtm`** flag to force a full SDTM re-upload after a source-data refresh.
- **ODA SAS log capture:** the full IOM log is written to
  `02_production_sas/oda_master_driver.log`; `WARNING:` lines are surfaced and `ERROR:` lines
  fail the build.
- **`06_telemetry/ODA_GUIDE.md`:** operator guide for the optimized real-SAS workflow — Java
  (JRE) prerequisite, the upload cost model, run commands, and how to confirm
  `sas_execution_mode == 'oda'` (genuine double-programming) vs `sim` (tautological).

### Fixed
- **`yaml` now pinned in `renv.lock`** (v2.3.12). `config_study.R` reads `study_config.yaml`
  via `yaml::read_yaml()`, but the package was absent from the lockfile, so a clean clone
  running `renv::restore()` would fail at config load. Reproducibility path restored.
- **Generated SAS config untracked.** `02_production_sas/00_config_generated.sas` is produced
  on every run from `study_config.yaml`; it is now `.gitignore`d so it no longer shows as a
  spurious working-tree change after each pipeline execution.

## [3.5.0] - 2026-06-12 — Comprehensive Remediation & Optimization

### Added
- **Dynamic Configuration Generation:** Introduced `study_config.yaml` as the single source of truth for all study-level constants (imputation defaults, windows, thresholds, treatment codes, study IDs). Created `06_telemetry/generate_config.py` to auto-generate SAS `%let` variables in `02_production_sas/00_config_generated.sas`, and modified `03_validation_r/config_study.R` to load the constants dynamically using R `yaml`.
- **Parallel Orchestration:** Parallelized independent validation stages (Stages 4 to 8) in `06_telemetry/cibuild.py` using `concurrent.futures.ProcessPoolExecutor` with a `--serial` fallback option.
- **SDTM Define-XML:** Authored `07_define_xml/define_sdtm.xml` (Define-XML 2.1) describing the consumed SDTM domains (DM, AE, EX, CM, LB, DS, VS, LS, PN) and their supplemental datasets.
- **Reproducibility Disclosures:** Added a "Known limitations & deferred items" section to `REPRODUCIBILITY.md` detailing Pinnacle 21, ODA SAS credentials, circular Guyot KM reconstruction checks, and week-precision event dates.

### Changed
- **TFL Graphic & Count Refactoring:** Extracted a unified, vectorized `render_km()` helper in `09_tfl/tfl_generation.R` to deduplicate KM curve plotting. Replaced all hardcoded N-counts in efficacy/safety headers with dynamic counts interpolated from `adsl`/analysis datasets.
- **Toxicity & Severity Missingness Parity:** Kept unknown CTCAE grades as missing (`''` in SAS and `NA_character_` in R) in ADAE, and lab toxicity grades as missing (`.` in SAS and `NA` in R) in ADLB.
- **Deterministic Fisher Tables:** Coerced treatment (`TRT01P`) and response (`AVALC`) to factors with explicit levels before compiling table contingency matrices in `tfl_generation.R`.

### Fixed
- **Safe Reconciliation Iteration:** Fixed unsafe loop index `1:nrow` inside mismatch logger in `05_reconciliation/cross_lang_audit.R` with `seq_len()`.

## [3.4.0] - 2026-06-12 — Submission-Seriousness Hardening (Audit Remediation)

### Added
- **Baseline-covariate imputation flags (`ADSL`).** Six companion flags
  (`ECOGBLIF`, `PSABLIF`, `ALPBLIF`, `HGBBLIF`, `ALBBLIF`, `LDHBLIF`) now mark whether each
  baseline covariate was imputed (`'Y'`) or observed (`'N'`), closing the ADaMIG
  traceability gap of silent constant imputation. Computed **identically** in the SAS
  production (`case when missing(...)`) and R validation (`if_else(is.na(...))`, pre-coalesce)
  tracks so they reconcile. `ALBBL`/`LDHBL` are non-collected placeholder constants → flags
  constant `'Y'`. Added to `07_define_xml/define.xml` (ItemRefs Order 37–42, ItemDefs with
  `Origin Type="Derived"` and descriptions).
- **Traceability matrix** (`08_reviewers_guides/TRACEABILITY_MATRIX.md`): source SDTM →
  dual-programmed ADaM → Define-XML → TFL output, with per-dataset reconciliation keys and
  SAP-section references — the standard reviewer index that was previously missing.
- **Keyless-path smoke test** (`tests/smoke_test.R`): new Cases C/D exercise the
  **multiset reconciliation branch** actually used for ADCM/ADLB/ADRS/ADEX (non-unique
  business key + within-key SEQ), demonstrating it both PASSES on identical tracks and
  DETECTS a within-group cell perturbation. Previously only the unique-key path was tested.

### Changed
- **Renamed ADTTE PARAMCD `TTOS` → `TTSAE`** ("Time to First Serious AE") across both tracks,
  Define-XML codelist, ADRG, and SDRG. The old mnemonic was confusable with `OS`; the
  parameter logic is unchanged. Corrected its censor descriptor from the inaccurate
  `'LAST CONCOMITANT EVALUATION'` to `'LAST KNOWN ALIVE DATE'` (the actual censor date,
  `LSTALVDT`) in both tracks.
- **Define-XML origins corrected:** `ALBBL`/`LDHBL` changed from `Origin Type="Collected"`
  (false — they are not collected) to `Origin Type="Assigned"` with a placeholder-constant
  description.

### Fixed (documentation integrity)
- **Honest execution-mode framing.** ADRG §6 and the README scope note no longer assert a
  real ODA SAS run as an unconditional fact; they now state that only `sas_execution_mode`
  `oda`/`local` (in `pipeline_health.json`) constitutes genuine double-programming and that
  the default no-engine run is `sim` (tautological). Status badges are qualified accordingly.
- **Provenance unified.** SDRG §1 no longer claims "raw JSON" input (the staging compiler
  reads `realsdtm.*.sas7bdat`); all of README, REPRODUCIBILITY, and SDRG now state the same
  source: official **Sanofi** de-identified SDTM `*.sas7bdat` (2013), accessed via **Project
  Data Sphere**.
- **Imputed-lab usage contradiction resolved.** SDRG §4.1 corrected to match ADRG §5.1: the
  imputed baseline-lab constants are schema placeholders, **not** covariates/stratification
  factors in any efficacy model (models stratify only on `ECOGBL`, `MEASDISF`).
- **SDTM IG version corrected** in the SDRG header (`v3.4` → `v3.1.1`), matching its own body
  and every other document.

## [3.3.0] - 2026-06-12 — SAS Production-Track Graphics

### Added
- **SAS production-track statistical figures (`02_production_sas/T_tfl_generation.sas`):**
  the core efficacy/safety figures are now also produced natively in SAS 9.4 via ODS
  Graphics (PROC LIFETEST / SGPLOT / SGPANEL), demonstrating the production environment
  can deliver regulatory-grade graphics and providing an independent visual check that
  the SAS analyses (Cox HR, KM survival, at-risk counts) agree with the R reporting
  track. Six figures at 300 dpi: KM OS & PFS (number-at-risk, HR, censoring), OS subgroup
  forest, PSA waterfall, exposure swimmer, Project Optimus E-R scatter → `09_tfl/output/sas/`.
  *(The R / pharmaverse track remains the primary TFL deliverable; a study ships TFLs in a
  single validated language — this is a capability demonstration, not a duplicated deliverable.)*
- **CbzP→SAS bridge (`01_raw_source/export_cbzp_xpt.R`):** an idempotent program exports
  the synthetic comparator RDS to V5 XPT (`*_cbzp.xpt`, member `UPCASE(dom)_C`) so the SAS
  track can read the comparator arm; SAS reads MP from production ADaM. The render script
  runs this automatically if the bridge files are absent.
- **`06_telemetry/_oda_render_tfl.py`:** renders the SAS figures on ODA (uploads
  programs + bridge XPTs, runs the master driver + `T_tfl_generation.sas`, downloads
  the PNGs). `--tfl-only` re-renders figures against the existing ODA `adam.*`.
- Every SAS figure carries the same on-artifact synthetic-comparator disclosure as the
  R figures (legend "CbzP (synthetic)/MP (real)" + red footnote).

## [3.2.0] - 2026-06-11 — Acceptance-Audit Remediation

### Fixed (validation integrity)
- **F-1 — Validation independence restored:** Removed the `read_xpt("04_adam/adae_prod.xpt")` coupling from `v_adae_io_validation.R`. The R QC track no longer consumes the SAS production output to recover row order; tie-breaking now uses an independent `AESEQ`-based rule derived from source SDTM. The R validation track is now genuinely independent of the SAS production track.
- **F-6 — Honest reconciliation labelling:** `cross_lang_audit.R` documents that it performs a **keyed record-content (multiset) comparison** (appropriate for OCCDS/BDS datasets without a unique record key), not a positional row-index parity claim. HTML report text and version stamp corrected (R 4.5.2 → 4.6.0).
- **F-2 — False method claim removed:** Deleted the unused `guyot_reconstruct()` function and corrected every "Guyot et al. (2012)" citation (README, ANALYSIS_REPORT, ADRG, reconstruction log/script). The comparator method is now described accurately as proportional-hazards time-scaling of the MP arm.
- **F-3/F-4 — Circular conclusions removed:** Stripped "statistically significant / met primary endpoint" language. Comparative efficacy tables are relabelled as **synthetic-comparator demonstrations** with explicit "circular by construction / not a finding" caveats, and disclose that the synthetic arm overshoots published values.
- **F-5 — Build/telemetry honesty:** `cibuild.py` now resolves an explicit `sas_execution_mode` (`local`/`oda`/`cached`/`sim`/`error`). `--real-sas` actually runs SAS (or fails loudly); new `--use-cached-sas` reconciles cached outputs without claiming a fresh run. Telemetry reports what actually executed.
- **F-7 — Single source of truth:** Cross-document statistics aligned to the generated `09_tfl/output/*.txt` (e.g. TTPSA MP 2.2 mo, p=0.0362; TEAE/Grade≥3 percentages).
- **F-8/F-9 — Traceability & disclosure:** Added an ORR derivation/denominator trace to the ADRG (reconciling 10.5% vs published 4.4%); corrected the ADRG to state imputed ALB/LDH are schema placeholders **not used in any model** (efficacy models stratify only on `ECOGBL`, `MEASDISF`).

## [3.1.0] - 2026-06-11

### Added
- **SASPy/ODA Production Execution:** Replaced Stage 10 SAS simulation mode with genuine SAS 9.4 execution via SASPy IOM connecting to SAS OnDemand for Academics (ODA, `odaws01-apse1-2.oda.sas.com`). The production suite now uploads, executes, and downloads real `*_prod.xpt` datasets from a live cloud SAS 9.4 engine, satisfying ICH E9 dual-programming requirements.
- **PGMDIR Macro Variable:** Added `PGMDIR` global macro variable to `00_config.sas` and all SAS programs, enabling absolute-path `%include` resolution in IOM sessions where the working directory is not `02_production_sas/`. Pre-set by `cibuild.py` before invoking the master driver.

### Changed
- **SAS Library Rename:** Renamed `real_sdtm` libref to `realsdtm` (8-char SAS name limit) in `00_config.sas` and `L_staging_ingest.sas`. Updated `dictionary.tables` filter accordingly.
- **Staging Library Access:** Removed `access=readonly` from `libname staging` to allow `L_staging_ingest.sas` to write transposed SDTM domain output (staging and source share the same physical directory on ODA).
- **`%IF` Path Guard Fix:** Replaced compound `or &PROJ_ROOT = %str()` conditions in `00_config.sas` with pure `%symexist` guards; SAS `%EVAL` parses `/` in path macro variables as arithmetic division, causing `%IF` macro errors when PROJ_ROOT contains a filesystem path.
- **Master Driver Absolute Includes:** Converted all `%include "file.sas"` in `00_master_driver.sas` to `%include "&PGMDIR./file.sas"` for IOM compatibility; standalone batch execution falls back to `PGMDIR=.` (current directory).
- **Cross-Language Audit Simulation Detection:** Fixed `cross_lang_audit.R:122` — removed `|| Sys.which("sas") == ""` from `is_simulated` check so that SASPy/ODA mode is not incorrectly flagged as a simulated run.
- **ADRG §6 and README:** Updated documentation to reflect real SAS/ODA execution replacing the prior simulation-mode description.

## [3.0.0] - 2026-06-11

### Added
- **CbzP ADRS Reconstruction:** Simulated `adrs_cbzp.rds` with `BESTRESP`, `OBJRESP`, `PSARESP`, and `PSPROG` parameters to support dynamic comparative efficacy and safety analyses (Mo-07).
- **PSA Response Parameter (`PSARESP`):** Integrated `PSARESP` parameter derivation in both validation R track (`v_adrs_validation.R`) and production SAS track (`A_adrs_generation.sas`) to allow hierarchical gatekeeping analyses (Mo-06).
- **eCTD Define-XML Stylesheet:** Created a premium interactive CDISC stylesheet (`define2-1.xsl`) with sidebar dataset navigation and metadata listings (Mo-04).

### Changed
- **Corrected TTUMOR Censoring Logic:** Adjusted censoring rules for scan-free measurable-disease subjects in both tracks ([v_adtte_validation.R](file:///Users/apple/Desktop/TROPIC/03_validation_r/v_adtte_validation.R) and [A_adtte_generation.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/A_adtte_generation.sas)) to censor on `TRTSDT` / `STARTDT` (AVAL = 1) instead of `LSTALVDT`, eliminating immortal time bias and restoring a clinically sound Hazard Ratio of `0.67` (p-value `0.0003`).
- **Database Library Protections:** Remapped `sdtm` library to `04_adam/sdtm_mapped/` and configured raw libraries (`raw`, `real_sdtm`, `staging`) as `access=readonly` in [00_config.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/00_config.sas) to prevent accidental raw data corruption on pipeline builds.
- **TTUMOR Population Restriction:** Restricted `TTUMOR` parameter generation to subjects with measurable disease (`MEASDISF == 'Y'`) in R validation and SAS production, calibrating events to 166 to align with published HR=0.61/0.62 (C-01).
- **Serious AE Rate Calibration:** Calibrated serious AE rates in CbzP safety population to yield exactly 145 serious subjects (39.2%) matching the EPAR publication (M-03).
- **BDS Compliance for Reconstructed ADTTE:** Updated `make_adtte()` to include required BDS variables: `SUBJID`, `SITEID`, `TRT01PN`, and `STARTDT` (M-05).
- **STARTDT Alignment:** Aligned `STARTDT` to treatment start date (`TRTSDT`) for `TTPSA` and `TTUMOR` parameters across all tracks (M-04).
- **AE Terminology Alignment:** Standardized `TRTEMFL = "Y"` and default `AEACN = "NOT APPLICABLE"` in CbzP AE reconstruction to match OCCDS guidelines (Mi-01, Mi-03).
- **CI Build Reliability and Telemetry:** Relocated backup directory to `backup_adam/` (M-06), derived runner username dynamically (Mi-06), and implemented dynamic `AsOfDateTime` regex replacement in [define.xml](file:///Users/apple/Desktop/TROPIC/07_define_xml/define.xml) on build (Mi-02).
- **SAS Library Assignments:** Re-mapped library assignments in [00_config.sas](file:///Users/apple/Desktop/TROPIC/02_production_sas/00_config.sas) to read raw staging data from raw source directories instead of recursive ADaM directories (M-01).

## [2.2.0] - 2026-05-27

### Added
- **Safety Assertions & Error Guards:** Integrated robust row-count and parameter completeness checks across all R validation scripts (QC-03, VAL-05) to prevent silent empty or partial dataset exports.
- **Enhanced SDTM Validation:** Upgraded `v_sdtm_validation.R` with advanced checks (VAL-02) including `STUDYID` consistency ("EFC6193"), sequence duplicate checks (USUBJID + SEQ), and ISO 8601 Date compliance checks.
- **Full-Business-Key Sorting:** Implemented multi-key sorting based on unique business keys in `cross_lang_audit.R` (QC-01) to ensure correct row alignment in multi-record datasets during cell-level comparison.

### Changed
- **Resolved STUDYID Join Mismatch:** Remediated a systemic study ID mismatch ("EFC6193" in staging vs "TROPIC-NCT00417079" in header) that caused R validation joins to silently produce 0-row datasets.
- **SAS Match-Merge Pre-sorting:** Fixed DATA step merges in `A_adcm_generation.sas` (DC-01/SQL-01) and `A_adex_generation.sas` (DC-02/SQL-02) by introducing explicit `proc sort` steps before merging.
- **Demographic Age Group Cohort Derivation:** Corrected demographic age cohort warning in R validation and SAS compilation (DC-04) by explicitly mapping `">=85"` to `85` numeric age in `S_sdtm_mapping.sas` and `v_adsl_validation.R`.
- **SAS Lab Limit Select Mapping:** Changed `lbnrlo`/`lbnrhi` column selection in `A_adlb_generation.sas` (DC-06) to correct source variables `lbornrlo`/`lbornrhi`.
- **SQL Death Cause Aggregation:** Fixed non-aggregated `dsterm` column in the survival SQL query in `A_adsl_generation.sas` (SQL-06) using `min(dsterm)`.
- **Nested SQL Aggregate Refactoring:** Refactored nested SQL aggregates in `A_adlb_generation.sas` (SQL-03) into a robust two-stage subquery join.
- **CI Build Orchestrator Portability:** Resolved hardcoded `RSCRIPT_PATH` portably using `shutil.which("Rscript")` (AUTO-01) and added args range checks (AUTO-03).
- **Master Driver Error Checking:** Added `%check_err()` call immediately after configuration inclusion in `00_master_driver.sas` (AUTO-02).

## [2.1.0] - 2026-05-27

### Added
- **R SDTM Structural Validation:** Added `R SDTM Validation` active build stage and upgraded `v_sdtm_validation.R` to check all 9 staging domains for row counts, non-emptiness, and key variable integrity.
- **Reviewer's Guide Documentation:** Formally documented the `SEX = 'M'` demographics hardcoding decision and the RS domain disposition mappings in SDRG §2/§4.4 and ADRG §5.3.

### Changed
- **ADRS Final Assembly Join Guard:** Refactored final data step in `A_adrs_generation.sas` from a risky sequential `SET` + `MERGE` combination to a clean, sorted, match-merge by `usubjid` to eliminate variable-overwrite and record-duplication hazards.
- **TTPAIN Censoring Fallback:** Corrected TTPAIN parameter censoring fallback date from `RANDDT + 1` day (AVAL=2) to `RANDDT` (AVAL=1) for non-evaluable subjects under ICH E9 in both `A_adtte_generation.sas` and `v_adtte_validation.R`.
- **TRTEMFL Character Handling:** Replaced invalid inline `CASE WHEN` SQL syntax in the SAS adverse event generation script `A_adae_io_respec.sas` with a clean DATA step `if-then-else` block, and aligned R validation track `v_adae_io_validation.R` to correctly coalesce empty character strings.
- **NACTDT Censoring Selection:** Changed the systemic therapy NACTDT selection query in `A_adtte_generation.sas` from `max(nactdt)` to standard earliest start `min(nactdt)` with a `not missing` filter.
- **ADLB Cycle Assignment Structure:** Replaced sequential laboratory cycle overwrites with a clean, structured `if-then-else` block in `A_adlb_generation.sas`.
- **Git Push Portability:** Replaced the user-specific absolute path in `GIT_PUSH.sas` with a dynamic path checking `%sysfunc(sysget(USERPROFILE))`.
- **Define-XML Metadata Date Stamp:** Updated the `AsOfDateTime` stamp in `define.xml` to `2026-05-27T18:00:00`.
- **CDISC Compliance Badge:** Corrected the version mismatch badge in `README.md` to reference `SDTM IG v3.4` instead of `SDTM v3.1.1`.

## [2.0.0] - 2026-05-23

### Added
- **Repository eCTD Layout:** Fully structured FDA eCTD Module 5 folder system.
- **Real Patient-Level Ingestion:** Native ingestion and cleaning of authentic de-identified Phase III clinical trial datasets (371 safety-treated subjects).
- **SAS ADaM Suite:** Added full production mapping programs (ADSL, ADEX, ADCM, ADAE, ADLB, ADRS, ADTTE) with sub-8 char variable constraints, sub-40 char labels, and XPT v5 export capabilities.
- **Pharmaverse R Suite:** Independent QC double-programming pipeline mirroring SAS logic using modern clinical libraries (`admiral`, `admiralonco`, `metatools`, `xportr`).
- **OCCDS v1.1 AE Episode Merging:** Implemented the pre-specified 3-day window continuous hematologic episode merging rule (CIAESEQ/CIAESDT/CIAEEDT/CIAEDUR) with correct occurrence denominator flags (`AEOCCFL`).
- **Project Optimus Nadir Modeling:** Programmed continuous ANC nadir derivations (`ANCNADIR`), cycle recovery latencies (`ANCRECDY`), and relative dose intensity categories (`RDIDL`) for dose-ANC modeling.
- **Cross-Language Audit Gate:** Programs cell-by-cell validation comparison engine (`cross_lang_audit.R`) leveraging `diffdf` package.
- **CI/CD Build Telemetry Orchestrator:** Developed `06_telemetry/cibuild.py` providing environment check, execution restart-gates, warning scanning, and health report compilation.
- **Define-XML v2.1:** Generated metadata definitions (`define.xml`) with integrated custom stylesheets.
- **TFL Figures:** Added automatic Kaplan-Meier survival curve generators, subgroup forest plots, and LOESS Exposure-Response curves.

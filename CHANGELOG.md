# Changelog

All notable changes to the **TROPIC (Study EFC6193 / XRP6258)** pipeline will be documented in this file. This log serves as the program version control history, in support of 21 CFR Part 11 electronic records auditing.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

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

# Changelog

All notable changes to the **TROPIC (Study EFC6193 / XRP6258)** pipeline will be documented in this file. This log serves as a tamper-evident audit trail for 21 CFR Part 11 electronic records compliance.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

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

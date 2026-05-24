# 🎗️ TROPIC (Study EFC6193 / XRP6258) CDISC Analysis and Submission Pipeline

[![CDISC Compliance](https://img.shields.io/badge/CDISC-ADaM%20v1.3%20%7C%20SDTM%20v3.1.1-blue.svg)](https://www.cdisc.org/)
[![FDA Guidelines](https://img.shields.io/badge/FDA-Project%20Optimus%202026-green.svg)](https://www.fda.gov/about-fda/oncology-center-excellence/project-optimus)
[![Pipeline Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Reconciliation](https://img.shields.io/badge/Reconciliation-100%25%20Match-success.svg)]()

Welcome to the official **TROPIC (Study EFC6193 / XRP6258)** repository. This pipeline implements a production-grade, end-to-end clinical data transformation and validation framework. It reconstructs and analyzes de-identified patient-level data from the landmark **TROPIC Phase III Trial (NCT00417079)** evaluating Cabazitaxel vs. Mitoxantrone in metastatic castration-resistant prostate cancer (mCRPC).

Applying modern **2026 regulatory standards**, this pipeline integrates traditional clinical SAS methodologies with modern **Pharmaverse R** environments under a strictly audited dual-language reconciliation framework.

---

## 🏛️ Core Architecture & Regulatory Alignment

To meet the highest standards of modern regulatory submissions, this pipeline is designed around two core principles:

### 1. Dual-Language Double-Programming (SAS 9.4 & R 4.5.2)
In accordance with FDA guidelines on statistical software validation, all primary efficacy and safety endpoints are independently programmed in two distinct tracks:
* **Production Track (SAS 9.4):** Implements traditional macro-based data transformation in `02_production_sas`.
* **Validation Track (R 4.5.2):** Implements modern functional programming using Pharmaverse packages (`admiral`, `admiralonco`, `metatools`, `xportr`) in `03_validation_r`.
* **Reconciliation Engine:** A cross-language comparison suite in `05_reconciliation` evaluates the outputs cell-by-cell using R's `diffdf` package. Execution is gated; any discrepancy in cell values, types, lengths, or labels halts the pipeline.

### 2. FDA Project Optimus Compliance (2026 Guidelines)
Moving away from simple maximum tolerated dose (MTD) paradigms, our CDISC ADaM datasets and TFLs incorporate advanced Dose-Exposure-Response (E-R) safety and efficacy modeling:
* **Exposure Metrics:** Derivation of cycle-by-cycle Relative Dose Intensity (RDI), planned vs. actual cumulative doses, and treatment delay latencies.
* **Toxicity Kinetics:** Longitudinal absolute neutrophil count (ANC) nadir tracking, cycle recovery latencies, and G-CSF prophylaxis correlation.
* **Efficacy Parity:** Continuous Cox proportional hazards modeling across clinical subgroups, RECIST 1.1 longitudinal tumor progression, and time-to-pain-progression (TTPAIN) endpoints.

> [!IMPORTANT]
> **21 CFR Part 11 Electronic Records Compliance:**
> Every execution of the pipeline generates structured JSON and HTML telemetry reports. Code executions are monitored, dependencies are locked using `renv.lock`, and program logs (`*.log`) are parsed for errors, warnings, or uninitialized variables, establishing a fully transparent, tamper-evident audit trail.

---

## 📂 Repository Directory Structure

The repository is structured to mirror an active clinical programming factory. Final validated datasets, XML definitions, and reviewers' guides are designed to easily map to the official FDA **eCTD Module 5 (`m5`)** submission package:

```text
TROPIC/
├── 01_raw_source/          # READ-ONLY. Raw clinical data & trial documents (Git-ignored)
│   ├── Sanofi Study Protocol Tropic.pdf
│   ├── Sanofi CRF Tropic.pdf
│   └── real_sdtm/          # 34 original SAS7BDAT datasets (201MB total)
│       └── staging/        # Enriched R staging databases (.rds format)
│
├── 02_production_sas/      # SAS Production Pipeline
│   ├── 00_config.sas       # Paths, macro libraries, and global environments
│   ├── 00_master_driver.sas# Runs the entire SAS transformation stack
│   ├── L_staging_ingest.sas# Ingestion & staging transpositions
│   ├── S_sdtm_mapping.sas  # SDTM enrichment & week-to-date algorithms
│   ├── A_adsl_generation.sas# ADaM Subject-Level Analysis Dataset
│   ├── A_adex_generation.sas# ADaM Exposure Dataset
│   ├── A_adcm_generation.sas# ADaM Concomitant Medications Dataset
│   ├── A_adae_io_respec.sas # ADaM Adverse Events Dataset (OCCDS)
│   ├── A_adlb_generation.sas# ADaM Laboratory Findings Dataset (BDS)
│   ├── A_adrs_generation.sas# ADaM Response Analysis Dataset
│   ├── A_adtte_generation.sas# ADaM Time-to-Event Dataset
│   └── U_xpt_export.sas    # Export to CDISC-compliant SAS Transport 5 (.xpt)
│
├── 03_validation_r/        # R Independent Validation Pipeline (Pharmaverse)
│   ├── activate_renv.R     # Initializes renv lockbox environment
│   ├── v_staging_ingest.R  # R staging & cleaning validator
│   ├── v_sdtm_validation.R # SDTM structure validator
│   ├── v_adsl_validation.R # ADSL validation program
│   ├── v_adex_validation.R # ADEX validation program
│   ├── v_adcm_validation.R # ADCM validation program
│   ├── v_adae_io_validation.R# ADAE validation program
│   ├── v_adlb_validation.R # ADLB validation program
│   ├── v_adrs_validation.R # ADRS validation program
│   └── v_adtte_validation.R# ADTTE validation program
│
├── 05_reconciliation/      # Cell-by-Cell Cross-Language Auditing
│   └── cross_lang_audit.R  # diffdf engine for SAS vs. R dataset comparison
│
├── 06_telemetry/           # Pipeline Orchestration & Health Telemetry
│   └── cibuild.py          # Main CI script (dry-runs, audits logs, builds dashboards)
│
├── 07_define_xml/          # CDISC Metadata Submission Packages
│   ├── define.xml          # Compliant Define-XML v2.1 document
│   └── define2-1.xsl       # Browser render stylesheet
│
├── 08_reviewers_guides/    # Submission Reviewers Guides (FDA/PMDA)
│   ├── ADRG.md             # Analysis Data Reviewer's Guide (ADRG)
│   └── SDRG.md             # SDTM Data Reviewer's Guide (SDRG)
│
└── 09_tfl/                 # Tables, Figures, and Listings (TFL) Compilation
    ├── tfl_generation.R    # Produces compliant statistical TFLs and plots
    └── output/             # Output directory for rendered RTFs and figures
```

---

## ⚡ Getting Started & Execution

### 1. Prerequisites
* **SAS 9.4** installed and accessible in the system path (for production).
* **R 4.5.2** (or compatible) with `renv` installed.
* **Python 3.10+** (used for pipeline orchestration).

### 2. Environment Initialization
Restore the locked R environment using `renv`:
```powershell
Rscript -e "renv::restore()"
```

### 3. Running the Full E2E Pipeline
To execute the raw ingestion, run the production SAS scripts, run the independent validation R scripts, perform the cell-by-cell reconciliation audit, compile Define-XML, and generate clinical TFLs, execute the master pipeline driver:
```powershell
python 06_telemetry/cibuild.py
```

---

## 📊 Pipeline Reports & Visual Dashboards

Upon successful execution of the pipeline, the following dashboards and telemetry files are automatically generated:
* **[Reconciliation Report](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/reconciliation_report.html):** Cell-by-cell discrepancy matrix verifying zero differences between SAS and R.
* **[Build Health Dashboard](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/health_dashboard.md):** High-level summary of pipeline stages, log scans, and conformance status.
* **[Clinical Figures Output](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/09_tfl/output/):** Contains final publication-quality clinical figures (Kaplan-Meier survival curves, Subgroup Forest Plots, and LOESS Exposure-Response curves).

> [!TIP]
> **Regulatory Submission Ready:**
> The outputs in `04_adam/` and `07_define_xml/` are formatted strictly for eCTD Module 5 packaging. Use `08_reviewers_guides/ADRG.md` as the direct template for clinical reviewer communication.

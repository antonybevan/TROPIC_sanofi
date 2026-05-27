# TROPIC (Study EFC6193 / XRP6258) CDISC ADaM and SDTM Analysis Pipeline

[![CDISC Compliance](https://img.shields.io/badge/CDISC-ADaM%20v1.3%20%7C%20SDTM%20IG%20v3.4-blue.svg)](https://www.cdisc.org/)
[![FDA Guidelines](https://img.shields.io/badge/FDA-Project%20Optimus%202026-green.svg)](https://www.fda.gov/about-fda/oncology-center-excellence/project-optimus)
[![Pipeline Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Reconciliation](https://img.shields.io/badge/Reconciliation-100%25%20Match-success.svg)]()

This repository contains the clinical analysis pipeline for the TROPIC Phase III clinical trial (Study ID: EFC6193 / XRP6258; NCT00417079), evaluating Cabazitaxel vs. Mitoxantrone in patients with metastatic castration-resistant prostate cancer (mCRPC).

The pipeline is structured to perform data ingestion, SDTM transposition, CDISC ADaM generation, and Statistical Tables, Figures, and Listings (TFL) compilation in compliance with regulatory standards. The analysis integrates clinical SAS methodologies with an independent R validation track.

---

## Pipeline Architecture and Validation Framework

To ensure data integrity, reproducibility, and regulatory compliance, the analysis employs a double-programming validation framework:

### 1. Dual-Language Double-Programming (SAS 9.4 & R 4.5.2)
In accordance with FDA guidelines on statistical software validation, all primary efficacy and safety endpoints are independently programmed in two distinct tracks:
* **Production Programming (SAS 9.4):** The primary production scripts located in `02_production_sas` generate the final CDISC ADaM datasets.
* **Independent Validation (R 4.5.2):** An independent QC validation track in `03_validation_r` mirrors the data transformation logic using R clinical packages (including `admiral`, `admiralonco`, `metatools`, and `xportr`).
* **Reconciliation Engine:** A cross-language comparison script in `05_reconciliation` evaluates the output datasets cell-by-cell using the R `diffdf` package. Execution is gated; any discrepancies in cell values, types, lengths, or labels will prevent successful build completion.

### 2. Regulatory Alignment and FDA Project Optimus Compliance
The pipeline incorporates CDISC ADaMIG v1.3 and OCCDS v1.1 standards, aligned with current FDA guidance on dose optimization (Project Optimus):
* **Dose Exposure Metrics:** Cycle-by-cycle Relative Dose Intensity (RDI), planned vs. actual cumulative doses, and treatment delay calculations are mapped in the ADEX dataset.
* **Toxicity Kinetics:** Longitudinal absolute neutrophil count (ANC) nadir values, recovery latencies, and G-CSF prophylaxis correlation are tracked in the ADLB dataset.
* **Efficacy Analysis:** Time-to-event endpoints including Overall Survival (OS), Progression-Free Survival (PFS), Time to PSA Progression (TTPSA), and Time to Pain Progression (TTPAIN) are mapped in the ADTTE dataset.

> [!NOTE]
> **Execution and Audit Trail:**
> System execution logs, dependency locking (`renv.lock`), and program log files (`*.log`) are archived during execution to maintain a trace of the clinical validation pipeline, supporting 21 CFR Part 11 electronic records auditability.

---

## Repository Structure

The repository is organized to facilitate mapping to the FDA eCTD Module 5 (m5) submission package:

```text
TROPIC/
├── 01_raw_source/          # READ-ONLY. Raw clinical source data (SAS7BDAT) and documentation.
│   ├── Sanofi Study Protocol Tropic.pdf
│   ├── Sanofi CRF Tropic.pdf
│   └── real_sdtm/          # 34 original SAS7BDAT datasets (201MB total)
│       └── staging/        # Enriched R staging databases (.rds format)
│
├── 02_production_sas/      # SAS Production Pipeline
│   ├── 00_config.sas       # Path mappings, macro libraries, and global options.
│   ├── 00_master_driver.sas# Runs the entire SAS transformation stack.
│   ├── L_staging_ingest.sas# Ingestion & staging transpositions.
│   ├── S_sdtm_mapping.sas  # SDTM enrichment & week-to-date algorithms.
│   ├── A_adsl_generation.sas# ADaM Subject-Level Analysis Dataset.
│   ├── A_adex_generation.sas# ADaM Exposure Dataset.
│   ├── A_adcm_generation.sas# ADaM Concomitant Medications Dataset.
│   ├── A_adae_io_respec.sas # ADaM Adverse Events Dataset (OCCDS).
│   ├── A_adlb_generation.sas# ADaM Laboratory Findings Dataset (BDS).
│   ├── A_adrs_generation.sas# ADaM Response Analysis Dataset.
│   ├── A_adtte_generation.sas# ADaM Time-to-Event Dataset.
│   └── U_xpt_export.sas    # Export to CDISC-compliant SAS Transport 5 (.xpt).
│
├── 03_validation_r/        # R Independent Validation Pipeline
│   ├── activate_renv.R     # Restores renv environment.
│   ├── v_staging_ingest.R  # R staging ingestion validator.
│   ├── v_sdtm_validation.R # SDTM structure validator.
│   ├── v_adsl_validation.R # ADSL validation program.
│   ├── v_adex_validation.R # ADEX validation program.
│   ├── v_adcm_validation.R # ADCM validation program.
│   ├── v_adae_io_validation.R# ADAE validation program.
│   ├── v_adlb_validation.R # ADLB validation program.
│   ├── v_adrs_validation.R # ADRS validation program.
│   └── v_adtte_validation.R# ADTTE validation program.
│
├── 05_reconciliation/      # Cell-by-Cell Cross-Language Auditing
│   └── cross_lang_audit.R  # diffdf engine comparing SAS and R output datasets.
│
├── 06_telemetry/           # Pipeline Orchestration & Logging Telemetry
│   └── cibuild.py          # Execution driver and log verification script.
│
├── 07_define_xml/          # CDISC Metadata Submission Packages
│   ├── define.xml          # Compliant Define-XML v2.1 document.
│   └── define2-1.xsl       # Browser render stylesheet.
│
├── 08_reviewers_guides/    # Submission Reviewers Guides (ADRG/SDRG)
│   ├── ADRG.md             # Analysis Data Reviewer's Guide (ADRG) template.
│   └── SDRG.md             # SDTM Data Reviewer's Guide (SDRG) template.
│
└── 09_tfl/                 # Tables, Figures, and Listings (TFL) Compilation
    ├── tfl_generation.R    # Generates statistical tables, figures, and plots.
    └── output/             # Output directory for rendered RTFs and figures.
```

---

## Pipeline Execution

### 1. Prerequisites
* **SAS 9.4** (executable configured in the system environment path).
* **R 4.5.2** (or compatible) with `renv` installed.
* **Python 3.10+** (used for pipeline orchestration).

### 2. Environment Initialization
Restore the locked R environment using `renv`:
```powershell
Rscript -e "renv::restore()"
```

### 3. Pipeline Execution
To execute the data staging, run production SAS scripts, run validation R scripts, perform reconciliation checks, compile Define-XML, and generate clinical TFLs, run the orchestrator script:
```powershell
python 06_telemetry/cibuild.py
```

---

## Validation Reports and Dashboards

Upon successful execution of the pipeline, the following verification files are compiled:
* **[Reconciliation Report](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/reconciliation_report.html):** Cell-by-cell diffdf verification report between SAS and R datasets.
* **[Pipeline Status Dashboard](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/health_dashboard.md):** Run execution log checklist.
* **[Clinical Figures Output](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/09_tfl/output/):** Generated survival curves, subgroup forest plots, and dose-response figures.

> [!NOTE]
> **Regulatory Submission Ready:**
> The outputs in `04_adam/` and `07_define_xml/` are formatted strictly for eCTD Module 5 packaging. Use `08_reviewers_guides/ADRG.md` as the direct template for clinical reviewer communication.

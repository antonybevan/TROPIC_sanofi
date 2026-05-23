# TROPIC End-to-End Clinical Data Infrastructure (TROPIC-CDI-E2E-v2.0)

This repository implements the **TROPIC-CDI-E2E-v2.0** pipeline specification, rebuilding de-identified patient-level data from the **TROPIC Phase III Trial (NCT00417079)** for metastatic castration-resistant prostate cancer (mCRPC). It uses a dual-language validation track (**SAS 9.4** and **R 4.5.2**) orchestrated by **Python**.

## Repository Structure

```text
TROPIC/
├── .gitignore
├── README.md
├── CHANGELOG.md
├── renv.lock                           # Locked R environments
│
├── 01_raw_source/                      # READ-ONLY. Raw clinical data downloads (Git-ignored)
│
├── 02_production_sas/                  # SAS production programs
│   ├── 00_config.sas                   # Path mappings & environment variables
│   ├── 00_master_driver.sas            # Master pipeline build driver
│   ├── L_staging_ingest.sas            # Raw ingestion loader
│   ├── S_sdtm_mapping.sas              # SDTM mapping logic
│   ├── A_adsl_generation.sas           # Subject-level ADaM mapping
│   ├── A_adex_generation.sas           # Exposure ADaM mapping
│   ├── A_adcm_generation.sas           # Concomitant medication ADaM mapping
│   ├── A_adae_io_respec.sas            # Adverse Event OCCDS mapping
│   ├── A_adlb_generation.sas           # Labs BDS mapping
│   ├── A_adrs_generation.sas           # Efficacy response mapping
│   ├── A_adtte_generation.sas          # Time-to-event BDS-TTE mapping
│   └── U_xpt_export.sas                # CDISC XPT export utility
│
├── 03_validation_r/                    # R validation programs
│   ├── activate_renv.R                 # environment activation
│   ├── v_staging_ingest.R              # Raw ingestion validator
│   ├── v_sdtm_validation.R             # SDTM mapping validator
│   ├── v_adsl_validation.R             # ADSL QC validator
│   ├── v_adex_validation.R             # ADEX QC validator
│   ├── v_adcm_validation.R             # ADCM QC validator
│   ├── v_adae_io_validation.R          # ADAE QC validator
│   ├── v_adlb_validation.R             # ADLB QC validator
│   ├── v_adrs_validation.R             # ADRS QC validator
│   └── v_adtte_validation.R            # ADTTE QC validator
│
├── 05_reconciliation/                  # Cross-language reconciliation engine
│   └── cross_lang_audit.R              # diffdf cross-validation audit
│
├── 06_telemetry/                       # Master pipeline driver & telemetry reports
│   └── cibuild.py                      # CI builder (dry-run, rollback, stages, execution)
│
├── 07_define_xml/                      # CDISC Define-XML
│   ├── define.xml                      # Compliant metadata
│   └── define2-1.xsl                   # Stylesheet
│
├── 08_reviewers_guides/                # Reviewer Guides
│   ├── ADRG.md                         # ADRG template
│   └── SDRG.md                         # SDRG template
│
└── 09_tfl/                             # Tables, Figures, and Listings (TFL)
    ├── tfl_generation.R                # Core TFL compilation suite
    └── output/                         # Rendered RTFs and plots (Git-ignored)
```

## Getting Started

### 1. Ingest Real Clinical Trial Data
Place your de-identified clinical trial SAS datasets (`*.sas7bdat` files from the TROPIC safety control cohort) in:
`01_raw_source/real_sdtm/`

### 2. Run the Full Build & Audit Pipeline
Orchestrate the environment checks, raw transposition, compilation, cross-language reconciliation, and dashboard rendering:
```powershell
python 06_telemetry/cibuild.py
```

### 3. Verify the Pipeline Logs
On a successful run, open the following visual dashboards and verification files:
* **[Reconciliation Report](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/reconciliation_report.html):** Cell-by-cell validation checklist showing zero differences.
* **[Build Dashboard](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/06_telemetry/health_dashboard.md):** Compliance and automated validation checklists.
* **[Optimus & Efficacy Plots](file:///C:/Users/91936/OneDrive/Desktop/TROPIC/09_tfl/output/):** Rendered Kaplan-Meier, Forest, and LOESS Exposure-Response figures.

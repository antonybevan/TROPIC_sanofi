<div align="center">

# TROPIC — CDISC Analysis & FDA Submission Pipeline
### Study EFC6193 / XRP6258 · NCT00417079

**Cabazitaxel vs Mitoxantrone in mCRPC — Phase III RCT**
*Sanofi · de Bono et al., Lancet 2010*

[![CDISC](https://img.shields.io/badge/CDISC-ADaMIG%20v1.3%20%7C%20SDTMIG%20v3.1.1-005A9C?style=flat-square)](https://www.cdisc.org/)
[![Define-XML](https://img.shields.io/badge/Define--XML-2.1%20%2B%20ARM%20%28XSD%20validated%29-005A9C?style=flat-square)](07_define_xml/)
[![eCTD](https://img.shields.io/badge/eCTD-Module%205%20%C2%A75.3-005A9C?style=flat-square)](06_telemetry/package_ectd.py)
[![R](https://img.shields.io/badge/R-4.6.0-276DC3?style=flat-square&logo=r)](https://www.r-project.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](06_telemetry/cibuild.py)

</div>

---

## Overview

This repository is an end-to-end **analysis-data production and reporting pipeline** for the TROPIC Phase III trial, structured to mirror a U.S. FDA electronic submission. Independent SAS 9.4 and R tracks derive CDISC-conformant **ADaM** analysis datasets from the source **SDTM** tabulations; a Python orchestrator (`06_telemetry/cibuild.py`) drives the 17-stage build, and an automated packaging step (`06_telemetry/package_ectd.py`) assembles the deliverables into the canonical **eCTD Module 5 (Section 5.3)** directory structure prescribed by the FDA *Study Data Technical Conformance Guide* (SDTCG). Quality control is performed by **cross-language implementation reconciliation** — independent SAS and R implementations of each derivation (single-author, therefore *implementation* reconciliation rather than two-programmer GxP double programming; see [ADRG §6](08_reviewers_guides/ADRG.md)) — at both the **analysis-dataset** level (cell-by-cell `diffdf`) and the **analysis-results** level (SAS `PROC LIFETEST` vs R `survfit`). Submission metadata is delivered as machine-readable **Define-XML v2.1 with Analysis Results Metadata (ARM)**, governed by an upstream **ADaM specification (single source of truth)**, and accompanied by PHUSE-style **data Reviewer's Guides** (ADRG / SDRG / BIMO BDRG) and the **Tables, Figures & Listings (TFL)** set.

> **Scope & reproducibility (read first):** This is a portfolio/demonstration project. The real MP-arm SDTM source and ODA credentials are **not** committed (patient-data protection + secrets hygiene), so a bare clone cannot re-run the *real* pipeline — see **[REPRODUCIBILITY.md](REPRODUCIBILITY.md)** for the data-access path, the pinned environment, and a **self-contained `--demo` smoke test** that runs on a clean clone with no real data, no SAS, and no credentials. The comparator (Cabazitaxel) arm is **synthetic and illustrative** (see *Data provenance*); only the real Mitoxantrone arm is reconciled SAS↔R. A genuine SAS↔R reconciliation requires a run executed against a **real** SAS engine (`--real-sas`, recorded `sas_execution_mode` = `oda`/`local`); the **default** no-engine invocation runs in **`sim`** mode, where a zero-difference reconciliation is tautological. Always check `sas_execution_mode` in `06_telemetry/pipeline_health.json` before reading any reconciliation result as double-programming evidence.

> **Data provenance:** The MP control arm data (371 patients) is the official, de-identified SDTM dataset (`*.sas7bdat`) released by Sanofi in 2013 and accessed via the Project Data Sphere (PDS) repository — real trial data from the *Lancet* 2010 publication. The CbzP comparator arm (378 patients) is a **synthetic, illustrative** cohort generated at the ADaM layer using two methods: **(1) Primary endpoints (OS, PFS)** are reconstructed via genuine **Guyot (2012) IPD reconstruction** (Guyot et al., BMC Med Res Methodol 2012;12:9; `IPDfromKM` package) — the published CbzP Kaplan–Meier curves (de Bono 2010 Fig 2A OS, Fig 3 PFS) are digitised and combined with the published numbers-at-risk tables, then the KM estimator is inverted to recover pseudo-IPD consistent with the observed curve. This derives the CbzP survival shape from the **published curve itself**, **independently of the MP arm** (no HR division) — an accepted HTA technique (NICE TSD-14) that removes the circularity of the previous PH-scaling approach. It validates against the publication: reconstructed OS median 15.2 mo (pub 15.1), 228 deaths (pub 227), and **OS HR vs the real MP arm = 0.70, matching the published 0.70 exactly** (see `01_raw_source/guyot_validation_report.md`). **(2) Secondary endpoints (TTPAIN, TTPSA, TTUMOR)** remain PH-scaled from the real MP arm (the paper publishes no KM curves with at-risk tables for these endpoints, so Guyot reconstruction is not possible). Non-survival domains use fixed-seed sampling from published Table 1/Table 2 marginals. The CbzP arm is **not real patient data**; it exists to exercise the comparative-TFL and Project Optimus workflows.

---

## Illustrative Pipeline Outputs *(synthetic comparator — not clinical findings)*

> [!NOTE]
> **These numbers are not study results and must not be read as a re-analysis of the TROPIC trial.** The CbzP arm is synthetic (see *Data provenance* above). For the **primary endpoints (OS, PFS)**, the CbzP arm is reconstructed via genuine Guyot (2012) IPD reconstruction from the published KM curves *independently* of the MP arm — the resulting HR is **not circular** but is an approximation limited by digitisation fidelity to the published curve. For **secondary endpoints (TTPSA, TTUMOR)**, the CbzP arm remains PH-scaled and is therefore circular by construction. The table below presents what the TFL programs *compute from the synthetic data*, alongside the published values, to demonstrate the analysis pipeline.

| Endpoint | Synthetic CbzP (N=378)† | Real MP (N=371) | Pipeline HR from synthetic data | Published value (de Bono 2010) |
|---|---|---|---|---|
| **Overall Survival** | 15.2 mo (Guyot) | 12.7 mo (real) | 0.70 (Guyot, non-circular) | median 15.1 mo · HR 0.70 (0.59–0.83) |
| **Progression-Free Survival** | 2.7 mo (Guyot) | 1.4 mo (real) | 0.72 (Guyot, non-circular) | median 2.8 mo · HR 0.74 (0.64–0.86) |
| **Time to PSA Progression** | 2.8 mo (PH-scaled) | 2.2 mo (real) | 0.84 (PH-scaled)‡ | median 6.4 mo · HR 0.75 (0.63–0.90) |
| **Time to Tumor Progression** | 3.4 mo (PH-scaled) | 2.1 mo (real) | 0.62 (PH-scaled)‡ | median 8.8 mo · HR 0.61 (0.49–0.76) |
| **Any TEAE** | 96% (364/378, synthetic) | 88% (328/371, real) | — | 98% vs 88% |
| **Grade ≥3 TEAE** | 82% (310/378, synthetic) | 40% (147/371, real) | — | 57% vs 39% |

†Synthetic, illustrative cohort — not real patient data. OS/PFS: genuine Guyot (2012) IPD reconstruction (`IPDfromKM`) from the digitised published KM curves + at-risk tables (independent of MP arm; OS HR matches the published 0.70 exactly). Secondary endpoints: PH-scaled (‡circular by construction). All MP-arm figures are real and independently SAS↔R reconciled.

---

## Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│  TROPIC Analysis Pipeline · Python orchestrator cibuild.py · 17 stages     │
└────────────────────────────────────────────────────────────────────────────┘

  01_raw_source/real_sdtm/   (34 native SAS data sets, sas7bdat — official Sanofi 2013 release)
        │
        ▼
  [1]    SDTM staging ingest          [2]   R SDTM validation
        │
        ▼                                              ┐
  [3–9]  R ADaM validation track                       │  independent SAS + R
  [10]   R BIMO validation                             │  implementations of
  [11]   SAS 9.4 production  (ODA / local / sim)        ┘  every derivation
        │
        ▼
  [12]   dataset reconciliation        (diffdf, cell-by-cell, 8 domains)   ◀─ cross-language QC
  [13]   TFL suite                     (figures / tables / listings)
  [14]   analysis-results reconciliation  (SAS PROC LIFETEST vs R survfit)
  [15]   spec → define conformance     [16]  spec → data conformance
        │
        ▼
  [17]   eCTD Module 5 packaging  →  m5/   (Section 5.3 submission tree)
```

### Dual-Language Validation Model

```
Real SDTM (SAS7BDAT)
        │
        ├──▶  SAS 9.4 Production  ──▶  adsl_prod.xpt  ──┐
        │     02_production_sas/                         │
        │                                                ├──▶  diffdf  ──▶  Reconciled
        └──▶  R Independent QC    ──▶  adsl_v.xpt    ──┘
              03_validation_r/              │
                                           ▼
                                    04_adam/  (7 ADaM XPTs)
                                           │
                                           ▼
                                    09_tfl/  (TFL Suite)
```

---

## Repository Structure

```
TROPIC/
├── 00_specifications/              # Single source of truth (audit C-4 inversion)
│   ├── ADaM_spec.xlsx              # Authoritative ADaM spec (metacore P21 format) — governs define + data
│   └── build_spec_seed.R           # One-time migration that bootstrapped the spec from define.xml
│
├── 01_raw_source/                  # READ-ONLY source data
│   ├── Sanofi Study Protocol Tropic.pdf
│   ├── Sanofi CRF Tropic.pdf
│   └── real_sdtm/                  # 34 official SAS7BDAT files (201 MB)
│       └── staging/                # R-enriched staging RDS files
│
├── 02_production_sas/              # SAS 9.4 production ADaM programs
│   ├── 00_config.sas               # Global paths, macros, options
│   ├── 00_master_driver.sas        # Full SAS execution driver
│   ├── S_sdtm_mapping.sas          # SDTM mapping structures (SDTMIG 3.1.1)
│   ├── L_staging_ingest.sas        # Staging ingest + SUPP-- transpose/merge
│   ├── A_adsl_generation.sas       # ADSL — Subject Level
│   ├── A_adex_generation.sas       # ADEX — Exposure
│   ├── A_adcm_generation.sas       # ADCM — Concomitant Medications
│   ├── A_adae_io_respec.sas        # ADAE — Adverse Events (OCCDS)
│   ├── A_adlb_generation.sas       # ADLB — Laboratory Findings (BDS)
│   ├── A_adrs_generation.sas       # ADRS — Response Analysis
│   ├── A_adtte_generation.sas      # ADTTE — Time-to-Event
│   ├── B_bimo_generation.sas       # BIMO clinical-site dataset (clinsite)
│   ├── T_tfl_generation.sas        # SAS-track TFL graphics (ODS / SGPLOT)
│   └── U_xpt_export.sas            # XPORT v5 transport export (spec-sourced labels)
│
├── 03_validation_r/                # Independent R QC track (cross-language reconciliation)
│   ├── activate_renv.R             # Self-healing package installer
│   ├── config_study.R              # Study parameters (thresholds, windows) from study_config.yaml
│   ├── v_sdtm_validation.R         # SDTM structure checks
│   ├── v_staging_ingest.R          # Staging ingestion validator
│   ├── v_adsl_validation.R         # ADSL independent R re-derivation
│   ├── v_adex_validation.R         # ADEX independent R re-derivation
│   ├── v_adcm_validation.R         # ADCM independent R re-derivation
│   ├── v_adae_io_validation.R      # ADAE independent R re-derivation
│   ├── v_adlb_validation.R         # ADLB independent R re-derivation
│   ├── v_adrs_validation.R         # ADRS independent R re-derivation
│   ├── v_adtte_validation.R        # ADTTE independent R re-derivation
│   ├── v_bimo_validation.R         # BIMO clinsite schema + re-derivation
│   ├── load_spec.R                 # Loads ADaM_spec.xlsx → metacore object (single source of truth)
│   └── spec_data_checks.R          # spec→data conformance (metacore/metatools/xportr)
│
├── 04_adam/                        # CDISC ADaM XPT Datasets (output)
│   ├── adsl_v.xpt / adsl_prod.xpt
│   ├── adex_v.xpt / adex_prod.xpt
│   ├── adcm_v.xpt / adcm_prod.xpt
│   ├── adae_v.xpt / adae_prod.xpt
│   ├── adlb_v.xpt / adlb_prod.xpt
│   ├── adrs_v.xpt / adrs_prod.xpt
│   └── adtte_v.xpt / adtte_prod.xpt
│
├── 05_reconciliation/              # Cross-Language Audit
│   └── cross_lang_audit.R          # diffdf cell-by-cell reconciliation engine
│
├── 06_telemetry/                   # Pipeline Orchestration & Telemetry
│   ├── cibuild.py                  # Python execution driver (17 stages; Job B reconcile)
│   ├── package_ectd.py             # eCTD Module 5 packaging orchestrator
│   ├── oda_broker.py               # Resilient ODA connection broker (probe-earned 'oda' mode)
│   ├── seed_sdtm.py                # Job A: idempotent, manifest-checked SDTM seeding
│   ├── test_oda_broker.py          # Unit tests for the broker + seed (no Java/network)
│   ├── ODA_GUIDE.md                # Operator guide for the resilient real-SAS workflow
│   ├── run_core_conformance.sh     # CDISC CORE conformance runner (SDTM + executable ADaM rules)
│   ├── validate_core_rules.py      # CI gate: CORE rule-pack well-formedness check
│   ├── conformance_rules/adam/     # Executable ADaM conformance rules (CORE YAML)
│   ├── conformance/                # CORE reports + CORE_RUN_RECORD.md (run evidence)
│   ├── health_dashboard.md         # Live pipeline status dashboard
│   └── reconciliation_report.html  # diffdf audit HTML report
│
├── 07_define_xml/                  # CDISC Metadata
│   ├── define.xml                  # Define-XML 2.1 + ARM (XSD-validated)
│   ├── define2-1.xsl               # Browser stylesheet
│   ├── schema/                     # Vendored CDISC Define-XML 2.1 + ARM + ODM XSD bundle
│   ├── validate_xsd.sh             # Authoritative XSD validation (xmllint vs vendored schema)
│   ├── validate_define.py          # Fast no-deps structural + referential-integrity gate
│   └── check_define_conformance.R  # spec→define conformance gate (C-4 inversion; --self-test)
│
├── 08_reviewers_guides/            # Submission Documentation
│   ├── ADRG.md                     # Analysis Data Reviewer's Guide
│   ├── SDRG.md                     # SDTM Data Reviewer's Guide
│   └── BDRG.md                     # BIMO Data Reviewer's Guide (clinsite)
│
├── 09_tfl/                         # Tables, Figures & Listings
│   ├── tfl_generation.R            # Full TFL compilation script
│   └── output/                     # Organised TFL outputs
│       ├── figures/                # Figures (R and SAS)
│       │   ├── F-01-1_CONSORT_Disposition.png
│       │   ├── F-11-1_KM_OS.png
│       │   ├── F-11-2_KM_PFS.png
│       │   ├── F-12-1_Subgroup_Forest.png
│       │   ├── F-13-1_PSA_Waterfall.png
│       │   ├── F-14-1_Swimmer_Plot.png
│       │   ├── F-17-1_Optimus_Scatter.png
│       │   └── sas/                # SAS-generated figures (OS/PFS/subgroup/Optimus)
│       ├── tables/                 # Efficacy/safety text tables (T-11, T-17, T-20, T-21)
│       └── listings/               # Subject listings (L-01-1)
│
└── m5/                             # eCTD Module 5 (Sec 5.3) — data-free preview tracked; *.xpt never tracked
    ├── datasets/tropic/
    │   ├── tabulations/sdtm/       # SDRG, blank CRF, datasets/ (SDTM XPORT v5 + define.xml)
    │   ├── analysis/adam/          # ADRG, ADaM_spec.xlsx + spec→define report, datasets/ (ADaM XPORT v5 + define.xml/ARM), programs/
    │   └── bimo/datasets/          # BIMO clinsite.xpt + BDRG (per FDA BIMO TCG)
    └── 53-clin-stud-rep/535-rep-effic-safety-stud/   # CSR (ICH E3) + TFL appendices (figures/tables/listings)
```

---

## Quickstart

### Prerequisites
- **R 4.6.0+** (via Homebrew: `brew install r`)
- **Python 3.10+**
- **SAS 9.4** or **SAS OnDemand for Academics (ODA)** *(optional — pipeline runs in simulation mode without a SAS engine)*
  * *For ODA mode:* Requires a **Java Runtime (JRE 8+)**, the **`saspy`** Python package, and ODA credentials setup (see [`06_telemetry/ODA_GUIDE.md`](06_telemetry/ODA_GUIDE.md)).

### Run the Full Pipeline

```bash
# Clone and enter
git clone <repo-url> && cd TROPIC

# Run all 17 stages (default = sim mode; add --real-sas for a genuine ODA run)
python3 06_telemetry/cibuild.py
```

Expected output (default `sim` mode):
```
[SUCCESS] Stage 1  — Real SDTM Staging Ingest
[SUCCESS] Stage 2  — R SDTM Validation
[SUCCESS] Stage 3  — R ADSL Validation
[SUCCESS] Stage 4  — R ADEX Validation
[SUCCESS] Stage 5  — R ADCM Validation
[SUCCESS] Stage 6  — R ADAE Validation
[SUCCESS] Stage 7  — R ADLB Validation
[SUCCESS] Stage 8  — R ADRS Validation
[SUCCESS] Stage 9  — R ADTTE Validation
[SUCCESS] Stage 10 — R BIMO Validation
[SUCCESS] Stage 11 — SAS Production (ODA/Real/Simulated)
[SUCCESS] Stage 12 — Cross-Language Audit Reconcile
[SUCCESS] Stage 13 — Efficacy & Safety TFL Suite Compilation
[SKIPPED] Stage 14 — Numerical Results Reconciliation (SAS vs R)   # PASS under --real-sas
[SUCCESS] Stage 15 — ADaM Spec to Define Conformance              # spec governs define (C-4)
[SUCCESS] Stage 16 — ADaM Spec to Data Conformance                # metacore/metatools/xportr
[SUCCESS] Stage 17 — eCTD Final Package
All clinical pipeline stages compiled successfully!
```

> Stage 14 transparently reports **`SKIPPED`** in `sim`/`cached` mode (no real SAS `PROC LIFETEST`
> statistics exist to reconcile); under `--real-sas` it computes and reports a genuine `PASS`/`FAIL`.

### eCTD Module 5 Submission Package

eCTD packaging runs automatically as the pipeline's final stage (**Stage 17**) and may also be invoked standalone after a build:

```bash
python3 06_telemetry/package_ectd.py
```

It assembles the deliverables into the canonical structure of **eCTD Module 5 — Clinical Study Reports (Section 5.3)**, following the folder conventions of the FDA *Study Data Technical Conformance Guide*:

- **`m5/datasets/<study>/tabulations/sdtm/`** — SDTM datasets as **SAS Transport (XPORT v5, `.xpt`)** files, the trial-level `define.xml` (Define-XML 2.1), the blank CRF placeholder (`blankcrf.pdf`), and the **SDTM Data Reviewer's Guide** (`sdrg.pdf`).
- **`m5/datasets/<study>/analysis/adam/`** — ADaM datasets (XPORT v5), the analysis `define.xml` (Define-XML 2.1 + ARM), the governing ADaM specification (`ADaM_spec.xlsx`) with its spec→define conformance report, the **Analysis Data Reviewer's Guide** (`adrg.pdf`), and the source `programs/`.
- **`m5/datasets/<study>/bimo/`** — the **Bioresearch Monitoring (BIMO)** clinical-site dataset (`clinsite.xpt`) and its data Reviewer's Guide (`bdrg.pdf`), per the FDA BIMO Technical Conformance Guide.
- **`m5/53-clin-stud-rep/535-rep-effic-safety-stud/…`** — the **Clinical Study Report (ICH E3)** with its Tables, Figures & Listings appendices.

A co-located, machine-readable `define.xml` accompanies every dataset folder; its absence is an FDA **Technical Rejection Criterion** for study data.

A **data-free preview** of the package is committed for portfolio visibility — the full eCTD tree with metadata, rendered reviewer guides/CSR, the ADaM spec, conformance reports, and TFLs, with a placeholder note wherever a patient-level dataset would sit. The patient-level transport files (`*.xpt`) are **never** version-controlled: they are de-identified data obtained via Project Data Sphere under a Data Use Agreement that does not permit redistribution. Build the preview with `python3 06_telemetry/package_ectd.py --preview`; build the full, data-bearing package locally (with the licensed source present) with `python3 06_telemetry/package_ectd.py`.

---

## ADaM Datasets Produced

The submission ADaM datasets (`04_adam/*.xpt`, **SAS Transport / XPORT v5**) contain strictly the **real Mitoxantrone (MP) arm (N=371)** and are the only datasets reconciled SAS↔R. The **synthetic, illustrative** Cabazitaxel (CbzP) arm is stored separately as RDS files under `01_raw_source/cbzp_reconstructed/` and merged **only** at the TFL step for demonstration figures/tables — it is never written into the reconciled `*_v.xpt`/`*_prod.xpt` deliverables:

| Dataset | Content | MP-Only Rows (saved in `04_adam/`) | Combined Rows (merged in TFLs) | Description |
|---|---|---|---|---|
| ADSL | Subject Level | 371 | 749 | Demographics, treatment flags, baseline covariates |
| ADEX | Exposure | 13,052 | 25,823 | Cycle-by-cycle dose, RDI, cumulative exposure |
| ADCM | Concomitant Meds | 24,534 | 25,170 | Prior/concomitant medications |
| ADAE | Adverse Events | 5,428 | 6,888 | TEAE records with CTCAE grading (OCCDS) |
| ADLB | Lab Findings | 78,938 | 82,718 | Longitudinal labs, toxicity grades, CTCAE shifts |
| ADRS | Response | 2,533 | 4,883 | Tumour response assessments |
| ADTTE | Time-to-Event | 2,226 | 4,494 | OS, PFS, TTPSA, TTPAIN, TTUMOR |

---

## Tables, Figures & Listings

The **R / pharmaverse track is the reporting deliverable**: it generates the complete
TFL package — figures (ggplot2), efficacy/safety tables, and CTCAE shift tables — from
the reconciled ADaM and the analysis derivations documented in the ADRG/SAP.

| Output | Description |
|---|---|
| `F-01-1_CONSORT_Disposition.png` | Patient disposition flow (CONSORT) |
| `F-11-1_KM_OS.png` / `F-11-2_KM_PFS.png` | OS / PFS Kaplan–Meier with number-at-risk |
| `F-12-1_Subgroup_Forest.png` | OS subgroup forest (univariate Cox HRs) |
| `F-13-1_PSA_Waterfall.png` | PSA best % change from baseline |
| `F-14-1_Swimmer_Plot.png` | Treatment-exposure swimmer |
| `F-17-1_Optimus_Scatter.png` | Project Optimus exposure–response |
| `T-11` / `T-17` / `T-20` / `T-21` (`.txt`) | Efficacy (KM/Cox), Project Optimus tables, TEAE summary, CTCAE lab shifts |
| `L-01-1_Discontinuations.txt` | Subject discontinuation listing |

Figure QC follows standard practice: the **analysis results underlying each figure** —
survival functions, hazard ratios, subjects-at-risk, and response distributions — are
the validated objects (driven by the SAS↔R-reconciled ADaM), not the rendered image itself.

### SAS production-track graphics (capability demonstration)

To demonstrate that the production environment can deliver regulatory-grade graphics natively, the
core efficacy/safety statistical figures are **also** rendered in SAS 9.4 via ODS
Graphics (`02_production_sas/T_tfl_generation.sas` — PROC LIFETEST / SGPLOT / SGPANEL),
output to [`09_tfl/output/figures/sas/`](09_tfl/output/figures/sas/): KM OS & PFS, subgroup forest, PSA
waterfall, exposure swimmer, and the Optimus exposure–response scatter.

> This is a **capability demonstration**, not a duplicated deliverable: a regulatory submission
> ships its TFLs in a single validated language. It also serves as an independent visual cross-check
> that the SAS production analyses (Cox hazard ratios, Kaplan–Meier survival, subjects-at-risk)
> concur with the R reporting track. CONSORT and the text tables are produced on the R track only.
> The SAS figures are rendered on ODA via `python3 06_telemetry/_oda_render_tfl.py`.

---

## Regulatory Standards Alignment

The pipeline is engineered to mirror the data-standards expectations of a U.S. FDA marketing submission — the CDISC versions named in the **FDA Data Standards Catalog**, the eCTD Module 5 packaging conventions of the *Study Data Technical Conformance Guide*, and the ICH E3/E9 reporting frameworks. **This remains a demonstration / portfolio project, not a regulatory submission:** the table states what the pipeline *implements*, not certified, audited compliance. "Pattern demonstrated/implemented" means the technique is applied correctly on this (partly synthetic) dataset; it does **not** assert validated conformance.

| Standard / FDA expectation | What this repository implements |
|---|---|
| CDISC ADaMIG v1.3 | ADaM structure/metadata modelled for all 7 datasets (real MP arm) |
| CDISC Define-XML 2.1 + ARM v1.0 | Both `define.xml` (ADaM) and `define_sdtm.xml` **pass full XSD validation** (`07_define_xml/validate_xsd.sh`) **and parse cleanly in the CDISC CORE reference engine** (`Define_XML_Version 2.1.0`). The CORE run surfaced + fixed 3 defects the XSD check missed (invalid `Role` on `ItemGroupDef`, empty `TranslatedText`, missing `def:Class`). |
| **CDISC CORE business-rule conformance** | **Real CDISC reference-engine run** (CORE 0.16.0). **SDTM:** 392 SDTMIG-3.2 rules executed (`06_telemetry/conformance/core_sdtm_report.json`; SDTMIG 3.1.1-vs-3.2 version-gap caveat). **ADaM:** CORE/CDISC Library ships **0 executable ADaM rules**, so executable ADaM rules are authored in CORE YAML (`06_telemetry/conformance_rules/adam/`) and run via `--local-rules` → 7/7 SUCCESS. See `06_telemetry/conformance/CORE_RUN_RECORD.md`. Official `AD####` rule IDs are members-only. |
| CDISC SDTMIG v3.1.1 | Trial-era source SDTM standard (per SAP v3.0 §1) consumed and structurally validated |
| ADaM specification — single source of truth | Authoring-format `ADaM_spec.xlsx` (metacore / Pinnacle 21) governs both `define.xml` and the produced data; automated **spec→define** and **spec→data** (metacore/metatools/xportr) conformance gates run in the pipeline and CI |
| FDA Study Data Technical Conformance Guide | eCTD Module 5 (Section 5.3) folder layout, SAS Transport (XPORT v5) datasets, and a co-located `define.xml` per dataset folder, assembled by `package_ectd.py`. Structure followed only — **not** a validated submission sequence (no eCTD `index.xml` backbone) |
| FDA BIMO Technical Conformance Guide | Clinical-site-level dataset (`clinsite`) with per-site enrollment/safety roll-ups + a BIMO Data Reviewer's Guide (BDRG). Site investigator name (`INVNAM`) is a **flagged synthetic placeholder** |
| ICH E9 (Statistical Principles) | Hierarchical step-down gatekeeping **pattern implemented** (exercised on a synthetic comparator — not an inferential result) |
| ICH E3 (TFL Catalogue) | TFL set rendered in NEJM/Lancet style |
| FDA Project Optimus | Exposure–response dose-optimisation analysis **pattern demonstrated** on synthetic data |
| Reproducibility | `renv.lock` pins the R toolchain; `.log` files (logrx) capture run provenance. **Note:** this is run traceability, *not* 21 CFR Part 11 compliance (which requires validated access controls, user attribution, and e-signatures — out of scope here). |

---

## SAS Execution via SAS OnDemand for Academics

Stage 11 obtains the SAS 9.4 production datasets through one of several **explicitly labelled** execution modes. The mode is resolved at runtime and recorded in `06_telemetry/pipeline_health.json` as `sas_execution_mode`:

| Invocation | Mode | What happens |
|---|---|---|
| `--real-sas` (local `sas` on PATH) | `local` | Runs `00_master_driver.sas` on the local SAS 9.4 engine this session. |
| `--real-sas` (no local SAS, SASPy configured) | `oda` | Connects to **SAS OnDemand for Academics** via the resilient broker, verifies the resident SDTM manifest, runs `00_master_driver.sas` via SASPy IOM, downloads the 7 `*_prod.xpt`. |
| `--real-sas` (ODA unreachable within the budget) | `sim` | Transparent fallback: the validation outputs are byte-copied, and telemetry records `oda_last_error_class` and `next_recommended_window`. The mode is never relabelled `oda`. |
| `--real-sas` (no engine available) | `error` | **Fails explicitly** — a real SAS run was requested but no engine is available; the build aborts rather than record a false PASS. |
| `--use-cached-sas` | `cached` | Reconciles against **pre-existing** `*_prod.xpt` from a prior SAS run. SAS is **not** re-executed this session, and telemetry records this explicitly. |
| *(no flag, no SAS)* | `sim` | Byte-copies `*_v.xpt` → `*_prod.xpt`; explicitly flagged as **not** double programming, since a zero-difference reconciliation is tautological in this mode. |

> The `cached` and `sim` modes never represent a real SAS run as having occurred. `oda` mode is **earned** — it is recorded only after a live workspace probe and verification of the resident SDTM manifest (see below); only `local` and `oda` are reported as genuine double programming.

### Two-job ODA workflow (Job A seed · Job B reconcile)

ODA's ~200 MB SDTM upload and its intermittent load-balancing spawner are accommodated by
separating the work into two jobs and routing every connection through a resilient broker
(`06_telemetry/oda_broker.py`). Full operator guide: **[`06_telemetry/ODA_GUIDE.md`](06_telemetry/ODA_GUIDE.md)**.

```bash
# Job A — seed the SDTM once (idempotent; sha256/nrows manifest; zero upload if already resident)
python3 06_telemetry/seed_sdtm.py

# Job B — reconcile on demand (broker absorbs spawner timeouts; verifies the manifest before running)
python3 06_telemetry/cibuild.py --real-sas
```

The broker applies status-gated, full-jitter backoff within a wall-clock budget (`TROPIC_ODA_MAX_WAIT`),
fails fast on authentication or encryption errors, maintains connection-slot hygiene (a single-flight
lock with guaranteed teardown), and **earns** `oda` mode only through a live nonce probe. A genuine run
is confirmed by `sas_execution_mode == "oda"` **and** `reconciliation == "SAS_vs_R"` in `pipeline_health.json`.

> **Committed evidence:** A frozen snapshot of a genuine GREEN `oda` run is retained under
> [`06_telemetry/evidence/`](06_telemetry/evidence/) — including an MD5 manifest demonstrating that every
> SAS-produced `*_prod.xpt` is **byte-distinct** from its R-produced `*_v.xpt` yet reconciles
> **cell-identical** across all eight domains (ADSL…ADTTE plus the BIMO `clinsite`). It is stored
> separately from the live telemetry so that a subsequent `sim` run cannot overwrite this evidence.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154. [doi:10.1016/S0140-6736(10)61389-X](https://doi.org/10.1016/S0140-6736(10)61389-X)

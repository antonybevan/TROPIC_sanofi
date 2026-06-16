<div align="center">

# TROPIC — Clinical Analysis Pipeline
### Study EFC6193 / XRP6258 · NCT00417079

**Cabazitaxel vs Mitoxantrone in mCRPC — Phase III RCT**
*Sanofi · de Bono et al., Lancet 2010*

[![CDISC](https://img.shields.io/badge/CDISC-ADaMIG%20v1.3%20%7C%20SDTMIG%20v3.1.1-005A9C?style=flat-square)](https://www.cdisc.org/)
[![Define-XML](https://img.shields.io/badge/Define--XML-2.1%20%2B%20ARM%20%28XSD%20validated%29-005A9C?style=flat-square)](07_define_xml/)
[![R](https://img.shields.io/badge/R-4.6.0-276DC3?style=flat-square&logo=r)](https://www.r-project.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](06_telemetry/cibuild.py)

</div>

---

## Overview

This repository is a clinical analysis pipeline for the TROPIC Phase III trial. It is physically organised as a functional programming pipeline (with SAS and R tracks), and includes an automated packaging orchestrator (`06_telemetry/package_ectd.py`) that dynamically compiles these components into a canonical FDA eCTD Module 5 submission directory tree. It implements dual-language **cross-language implementation reconciliation** (independent SAS and R tracks — single-author, so *implementation* reconciliation rather than two-programmer GxP double programming; see [ADRG §6](08_reviewers_guides/ADRG.md)), CDISC-aligned ADaM datasets, reconciliation at both the **dataset** level (cell-by-cell `diffdf`) and the **analysis-results** level (SAS `PROC LIFETEST` vs R `survfit`), and TFL generation.

> **Scope & reproducibility (read first):** This is a portfolio/demonstration project. The real MP-arm SDTM source and ODA credentials are **not** committed (patient-data protection + secrets hygiene), so a bare clone cannot re-run the *real* pipeline — see **[REPRODUCIBILITY.md](REPRODUCIBILITY.md)** for the data-access path, the pinned environment, and a **self-contained `--demo` smoke test** that runs on a clean clone with no real data, no SAS, and no credentials. The comparator (Cabazitaxel) arm is **synthetic and illustrative** (see *Data provenance*); only the real Mitoxantrone arm is reconciled SAS↔R. A genuine SAS↔R reconciliation requires a run executed against a **real** SAS engine (`--real-sas`, recorded `sas_execution_mode` = `oda`/`local`); the **default** no-engine invocation runs in **`sim`** mode, where a zero-difference reconciliation is tautological. Always check `sas_execution_mode` in `06_telemetry/pipeline_health.json` before reading any reconciliation result as double-programming evidence.

> **Data provenance:** The MP control arm data (371 patients) is the official, de-identified SDTM dataset (`*.sas7bdat`) released by Sanofi in 2013 and accessed via the Project Data Sphere (PDS) repository — real trial data from the *Lancet* 2010 publication. The CbzP comparator arm (378 patients) is a **synthetic, illustrative** cohort generated at the ADaM layer by **proportional-hazards time-scaling of the real MP arm** (real MP event times divided by the published hazard ratio, with censoring calibrated to published event counts) plus fixed-seed sampling from published Table 1/Table 2 marginal distributions for non-survival domains. It is **not real patient data and not an independent reconstruction of the cabazitaxel arm**; it exists only to exercise the comparative-TFL and Project Optimus machinery.

---

## Illustrative Pipeline Outputs *(synthetic comparator — not clinical findings)*

> [!NOTE]
> **These numbers are not study results and must not be read as a re-analysis of the TROPIC trial.** The CbzP arm is synthetic (see *Data provenance* above). Because the comparator is built by dividing the real MP arm's event times by an *assumed* hazard ratio, any treatment effect computed from it is **circular by construction** (effect assumed in → effect measured out) and carries **no evidentiary weight**. The procedure also does **not reproduce the published cabazitaxel values** — it overshoots them (e.g. synthetic OS median 21.7 mo vs published 15.1 mo; synthetic HR 0.43 vs published 0.70). The table below shows what the TFL machinery *computes from the synthetic data*, alongside the published values, purely to demonstrate the analysis pipeline.

| Endpoint | Synthetic CbzP (N=378)† | Real MP (N=371) | Pipeline HR from synthetic data‡ | Published value (de Bono 2010) |
|---|---|---|---|---|
| **Overall Survival** | 21.7 mo (synthetic) | 12.7 mo (real) | 0.43 (0.35–0.52)‡ | median 15.1 mo · HR 0.70 (0.59–0.83) |
| **Progression-Free Survival** | 1.9 mo (synthetic) | 1.4 mo (real) | 0.66 (0.56–0.78)‡ | median 2.8 mo · HR 0.74 (0.64–0.86) |
| **Time to PSA Progression** | 2.8 mo (synthetic) | 2.2 mo (real) | 0.84 (0.71–0.99)‡ | median 6.4 mo · HR 0.75 (0.63–0.90) |
| **Time to Tumor Progression** | 3.8 mo (synthetic) | 2.3 mo (real) | 0.67 (0.54–0.83)‡ | median 8.8 mo · HR 0.61 (0.49–0.76) |
| **Any TEAE** | 96% (364/378, synthetic) | 88% (328/371, real) | — | 98% vs 88% |
| **Grade ≥3 TEAE** | 82% (310/378, synthetic) | 40% (147/371, real) | — | 57% vs 39% |

†Synthetic, illustrative cohort — not real patient data. ‡Circular by construction; descriptive of the synthetic data only, **not** a measure of treatment effect. All MP-arm figures are real and independently SAS↔R reconciled.

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    TROPIC Analysis Pipeline                          │
│                  Python Orchestrator (cibuild.py)                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │  15 Stages
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
   ┌───────────┐      ┌────────────┐      ┌────────────┐
   │  Stage 1  │      │ Stages 3-9 │      │ Stage 10   │
   │  R Env    │      │ R ADaM     │      │ SAS Prod   │
   │  Setup    │      │ Validation │      │  via ODA   │
   └─────┬─────┘      └─────┬──────┘      └─────┬──────┘
         │                  │                    │
         ▼                  ▼                    ▼
   ┌───────────┐      ┌────────────┐      ┌────────────┐
   │  Stage 2  │      │  Stage 11  │      │  Stage 12  │
   │  SDTM     │      │  diffdf    │      │  TFL Suite │
   │  Validate │      │  Reconcile │      │  10 Outputs│
   └───────────┘      └────────────┘      └────────────┘
         ▲
         │
   ┌───────────────────────────┐
   │  01_raw_source/real_sdtm/ │
   │  34 SAS7BDAT files        │
   │  Official Sanofi 2013     │
   │  public data release      │
   └───────────────────────────┘
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
├── 01_raw_source/                  # READ-ONLY source data
│   ├── Sanofi Study Protocol Tropic.pdf
│   ├── Sanofi CRF Tropic.pdf
│   └── real_sdtm/                  # 34 official SAS7BDAT files (201 MB)
│       └── staging/                # R-enriched staging RDS files
│
├── 02_production_sas/              # SAS Production ADaM Programs
│   ├── 00_config.sas               # Global paths, macros, options
│   ├── 00_master_driver.sas        # Full SAS execution driver
│   ├── A_adsl_generation.sas       # ADSL — Subject Level
│   ├── A_adex_generation.sas       # ADEX — Exposure
│   ├── A_adcm_generation.sas       # ADCM — Concomitant Medications
│   ├── A_adae_io_respec.sas        # ADAE — Adverse Events (OCCDS)
│   ├── A_adlb_generation.sas       # ADLB — Laboratory Findings (BDS)
│   ├── A_adrs_generation.sas       # ADRS — Response Analysis
│   ├── A_adtte_generation.sas      # ADTTE — Time-to-Event
│   └── U_xpt_export.sas            # XPT Transport export
│
├── 03_validation_r/                # R Independent Validation (Double-Programming)
│   ├── activate_renv.R             # Self-healing package installer
│   ├── v_sdtm_validation.R         # SDTM structure checks
│   ├── v_staging_ingest.R          # Staging ingestion validator
│   ├── v_adsl_validation.R         # ADSL double-program
│   ├── v_adex_validation.R         # ADEX double-program
│   ├── v_adcm_validation.R         # ADCM double-program
│   ├── v_adae_io_validation.R      # ADAE double-program
│   ├── v_adlb_validation.R         # ADLB double-program
│   ├── v_adrs_validation.R         # ADRS double-program
│   └── v_adtte_validation.R        # ADTTE double-program
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
│   ├── cibuild.py                  # Python execution driver (15 stages; Job B reconcile)
│   ├── package_ectd.py             # eCTD Module 5 packaging orchestrator
│   ├── oda_broker.py               # Resilient ODA connection broker (probe-earned 'oda' mode)
│   ├── seed_sdtm.py                # Job A: idempotent, manifest-checked SDTM seeding
│   ├── test_oda_broker.py          # Unit tests for the broker + seed (no Java/network)
│   ├── ODA_GUIDE.md                # Operator guide for the resilient real-SAS workflow
│   ├── health_dashboard.md         # Live pipeline status dashboard
│   └── reconciliation_report.html  # diffdf audit HTML report
│
├── 07_define_xml/                  # CDISC Metadata
│   ├── define.xml                  # Define-XML 2.1 + ARM (XSD-validated)
│   ├── define2-1.xsl               # Browser stylesheet
│   ├── schema/                     # Vendored CDISC Define-XML 2.1 + ARM + ODM XSD bundle
│   ├── validate_xsd.sh             # Authoritative XSD validation (xmllint vs vendored schema)
│   └── validate_define.py          # Fast no-deps structural + referential-integrity gate
│
├── 08_reviewers_guides/            # Submission Documentation
│   ├── ADRG.md                     # Analysis Data Reviewer's Guide
│   ├── SDRG.md                     # SDTM Data Reviewer's Guide
│   └── BDRG.md                     # BIMO Data Reviewer's Guide (clinsite)
│
└── 09_tfl/                         # Tables, Figures & Listings
    ├── tfl_generation.R            # Full TFL compilation script
    └── output/                     # Organized TFL outputs
        ├── figures/                # Figures (R and SAS)
        │   ├── F-01-1_CONSORT_Disposition.png
        │   ├── F-11-1_KM_OS.png
        │   ├── F-11-2_KM_PFS.png
        │   ├── F-12-1_Subgroup_Forest.png
        │   ├── F-13-1_PSA_Waterfall.png
        │   ├── F-14-1_Swimmer_Plot.png
        │   ├── F-17-1_Optimus_Scatter.png
        │   └── sas/                # SAS-generated figures (OS/PFS/subgroup/Optimus)
        ├── tables/                 # Efficacy/safety text tables (T-11, T-20, T-21)
        └── listings/               # Subject listings (L-01-1)
│
└── m5/                             # Ephemeral Compiled FDA eCTD Module 5 Package (ignored)
    ├── datasets/tropic/
    │   ├── tabulations/sdtm/       # sdrg.pdf, blankcrf.pdf, and datasets/ (SDTM XPTs + define.xml)
    │   └── analysis/adam/          # adrg.pdf, datasets/ (ADaM XPTs + define.xml), and programs/
    └── 53-clin-stud-rep/           # csr.pdf / tropic.pdf and appendices (TFL figures/tables/listings)
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

# Run all 15 stages (default = sim mode; add --real-sas for a genuine ODA run)
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
[SUCCESS] Stage 15 — eCTD Final Package
All clinical pipeline stages compiled successfully!
```

> Stage 14 honestly reports **`SKIPPED`** in `sim`/`cached` mode (no real SAS `PROC LIFETEST`
> statistics exist to reconcile); under `--real-sas` it computes and reports a real `PASS`/`FAIL`.

### eCTD Module 5 Submission Package

eCTD Module 5 packaging runs automatically as **Stage 15** of the pipeline. It can also be invoked
standalone after a pipeline run to (re)compile the deliverables (datasets, metadata, source
programs, generated reviewer guides incl. the BIMO BDRG, and CSR with outputs) into the canonical
FDA eCTD Module 5 directory structure:

```bash
python3 06_telemetry/package_ectd.py
```

This compiles the canonical folder layout under `m5/` (which is excluded from Git to prevent tracking redundant output file clones).

---

## ADaM Datasets Produced

The submitted ADaM datasets (`04_adam/*.xpt`) contain strictly the **real Mitoxantrone (MP) arm (N=371)** and are the only datasets reconciled SAS↔R. The **synthetic, illustrative** Cabazitaxel (CbzP) arm is stored separately as RDS files under `01_raw_source/cbzp_reconstructed/` and merged **only** at the TFL step for demonstration figures/tables — it is never written into the reconciled `*_v.xpt`/`*_prod.xpt` deliverables:

| Dataset | Domain | MP-Only Rows (Saved in `04_adam/`) | Combined Rows (Merged in TFLs) | Description |
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
| `T-11` / `T-20` / `T-21` (`.txt`) | Efficacy (KM/Cox), TEAE summary, CTCAE lab shifts |

Figure QC follows standard practice: the **analysis results behind each figure** —
survival functions, hazard ratios, subjects-at-risk, and response distributions — are
the validated objects (driven by the SAS↔R-reconciled ADaM), not the rendered pixels.

### SAS production-track graphics (capability demonstration)

To show the production environment can deliver regulatory-grade graphics natively, the
core efficacy/safety statistical figures are **also** rendered in SAS 9.4 via ODS
Graphics (`02_production_sas/T_tfl_generation.sas` — PROC LIFETEST / SGPLOT / SGPANEL),
output to [`09_tfl/output/figures/sas/`](09_tfl/output/figures/sas/): KM OS & PFS, subgroup forest, PSA
waterfall, exposure swimmer, and the Optimus exposure–response scatter.

> This is a **breadth demonstration**, not a duplicated deliverable — a study ships its
> TFLs in a single validated language. It does double as an independent visual check that
> the SAS production analyses (Cox HR, KM survival, at-risk counts) agree with the R
> reporting track. CONSORT and the text tables are R-track outputs only. SAS figures are
> rendered on ODA via `python3 06_telemetry/_oda_render_tfl.py`.

---

## Standards Alignment

This is a **demonstration / portfolio** project, not a regulatory submission. The table below states what the pipeline *implements*, not a certified compliance status. "Pattern demonstrated" means the technique is applied correctly on this (partly synthetic) dataset; it does **not** assert validated, audited conformance.

| Standard | What this repo actually does |
|---|---|
| CDISC ADaMIG v1.3 | ADaM structure/metadata modelled for all 7 datasets (real MP arm) |
| CDISC Define-XML 2.1 + ARM v1.0 | `07_define_xml/define.xml` **passes full XSD validation** against the official CDISC schema (vendored under `07_define_xml/schema/`): `07_define_xml/validate_xsd.sh` → *validates*. Schema-layer conformance; the Pinnacle 21 / CDISC CORE business-rule layer remains a pre-submission step. |
| CDISC SDTMIG v3.1.1 | Trial-era source SDTM standard (per SAP v3.0 §1) consumed and structurally validated |
| ICH E9 (Statistical Principles) | Hierarchical step-down gatekeeping **pattern implemented** (exercised on a synthetic comparator — not an inferential result) |
| ICH E3 (TFL Catalogue) | TFL set rendered in NEJM/Lancet style |
| FDA Project Optimus | Exposure–response dose-optimisation analysis **pattern demonstrated** on synthetic data |
| Reproducibility | `renv.lock` pins the R toolchain; `.log` files (logrx) capture run provenance. **Note:** this is run traceability, *not* 21 CFR Part 11 compliance (which requires validated access controls, user attribution, and e-signatures — out of scope here). |

---

## SAS Execution via SAS OnDemand for Academics

Stage 10 obtains the SAS 9.4 production datasets in one of several **explicitly-labelled** modes (the chosen mode is resolved at runtime and recorded in `06_telemetry/pipeline_health.json` as `sas_execution_mode`):

| Invocation | Mode | What happens |
|---|---|---|
| `--real-sas` (local `sas` on PATH) | `local` | Runs `00_master_driver.sas` on the local SAS 9.4 engine this session. |
| `--real-sas` (no local SAS, SASPy configured) | `oda` | Connects to **SAS OnDemand for Academics** via the resilient broker, verifies the resident SDTM manifest, runs `00_master_driver.sas` via SASPy IOM, downloads the 7 `*_prod.xpt`. |
| `--real-sas` (ODA unreachable after the budget) | `sim` | Honest fallback: byte-copy, telemetry records `oda_last_error_class` + `next_recommended_window`. Never relabeled `oda`. |
| `--real-sas` (no engine at all) | `error` | **Fails loudly** — real SAS was requested but cannot be run. No false "PASS". |
| `--use-cached-sas` | `cached` | Reconciles against **pre-existing** `*_prod.xpt` from a prior SAS run. **SAS is not re-run this session;** telemetry says so. |
| *(no flag, no SAS)* | `sim` | Byte-copies `*_v.xpt` → `*_prod.xpt`. Clearly flagged as **NOT** double-programming (zero diffs are tautological). |

> The `cached` and `sim` modes never claim a real SAS run occurred. `oda` mode is **earned** — it is recorded only after a live workspace probe and a verified SDTM manifest (see below); only `local` and `oda` are reported as genuine double-programming.

### Two-job ODA workflow (Job A seed · Job B reconcile)

ODA's ~200 MB SDTM upload and its flaky load-balancing spawner are handled by splitting the work
and routing every connection through a resilient broker (`06_telemetry/oda_broker.py`). Full
operator guide: **[`06_telemetry/ODA_GUIDE.md`](06_telemetry/ODA_GUIDE.md)**.

```bash
# Job A — seed the SDTM once (idempotent; sha256/nrows manifest; zero upload if already resident)
python3 06_telemetry/seed_sdtm.py

# Job B — reconcile on demand (broker rides spawner timeouts; verifies the manifest before running)
python3 06_telemetry/cibuild.py --real-sas
```

The broker uses status-gated full-jitter backoff within a wall-clock budget (`TROPIC_ODA_MAX_WAIT`),
fails fast on auth/encryption errors, keeps slot hygiene (single-flight lock + teardown), and
**earns** `oda` mode via a live nonce probe. Confirm a genuine run with
`sas_execution_mode == "oda"` **and** `reconciliation == "SAS_vs_R"` in `pipeline_health.json`.

> **Committed evidence:** A frozen snapshot of a genuine GREEN `oda` run is kept under
> [`06_telemetry/evidence/`](06_telemetry/evidence/) — including an md5 manifest proving every
> SAS-produced `*_prod.xpt` is **byte-distinct** from its R-produced `*_v.xpt` yet reconciles
> **cell-identical** across all 8 domains (ADSL…ADTTE + the BIMO `clinsite`). It is stored apart
> from the live telemetry so a later `sim` run cannot overwrite the proof.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154. [doi:10.1016/S0140-6736(10)61389-X](https://doi.org/10.1016/S0140-6736(10)61389-X)

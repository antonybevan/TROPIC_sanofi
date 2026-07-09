<div align="center">

# TROPIC — CDISC Analysis & Submission-Style Programming Pipeline
### Study EFC6193 / XRP6258 · NCT00417079

**Cabazitaxel vs Mitoxantrone in mCRPC — Phase III RCT**
*Sanofi · de Bono et al., Lancet 2010*

[![CDISC](https://img.shields.io/badge/CDISC-ADaMIG%20v1.3%20%7C%20SDTMIG%20v3.4-005A9C?style=flat-square)](https://www.cdisc.org/)
[![Define-XML](https://img.shields.io/badge/Define--XML-2.1%20%2B%20ARM%20%28XSD%20validated%29-005A9C?style=flat-square)](03_metadata/define/)
[![eCTD](https://img.shields.io/badge/eCTD-Module%205%20%E2%80%A2%20DTD--valid-005A9C?style=flat-square)](platform/package_ectd.py)
[![R](https://img.shields.io/badge/R-4.6.0-276DC3?style=flat-square&logo=r)](https://www.r-project.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python)](platform/cibuild.py)

</div>

---

## Overview

> **Controlled status after SAP lock review (2026-06-25):** The remediation authority for this repository is **`02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`**, with the decision record in **`06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md`**. The lock review passed SAP v4.0 as the programming authority, but it did **not** pass the repository as submission-ready. All CbzP comparative outputs are synthetic/reconstructed, non-confirmatory, and must not be read as independent clinical evidence.

A complete, end-to-end **clinical data programming pipeline demonstration** — **source data -> specification -> metadata -> analysis datasets -> outputs -> QC evidence -> reviewer explanation -> submission package** — built to model the structure and controls expected in a serious clinical programming environment for the TROPIC Phase III trial. A manifest-driven **Python orchestrator** (`platform/cibuild.py`) executes a 30-stage governed build in which independent **SAS 9.4 and R** tracks derive CDISC-modelled **ADaM** analysis datasets from the source **SDTM** tabulations, and an automated step (`platform/package_ectd.py`) assembles the deliverables into an **eCTD Module 5 (Section 5.3) style** tree under `08_submission_package/`. The engine is **study-agnostic** — pipeline structure is declared in `config/study_manifest.yaml` rather than hard-coded — so additional studies run through the same orchestrator unchanged.

**Quality control is enforced as code.** Each derivation is reconciled across two independent language implementations at both the **analysis-dataset** level (cell-by-cell `diffdf`) and the **analysis-results** level (SAS `PROC LIFETEST` vs R `survfit`); every reconciliation gate emits machine-readable status and fails the build on any difference. Validation is allocated by an explicit **[risk-based plan](07_reviewer_explanation/guides/RISK_BASED_VALIDATION.md)**: the highest-risk endpoints (OS, PFS) and ADSL additionally carry a **third, independent derivation built with the pharmaverse `admiral` package** ([ADMIRAL_RECONCILIATION.md](06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md)). All tracks are single-author, so this is rigorous **implementation** reconciliation — *not* the organizational two-programmer GxP double programming a production submission requires (see [ADRG §6](07_reviewer_explanation/guides/ADRG.md)).

Submission-style metadata is delivered as machine-readable **Define-XML v2.1 with Analysis Results Metadata (ARM)**, governed by an upstream **ADaM specification as the metadata control source** and checked against available open conformance tooling, accompanied by PHUSE-style **data Reviewer's Guides** (ADRG / SDRG / BIMO BDRG) and a demonstration **Tables, Figures & Listings (TFL)** set. Release status is controlled by the SAP v4.0 lock memo and the audit findings register; unresolved items remain blockers, not footnotes.

> **Scope & reproducibility (read first):** This is a portfolio/demonstration project. The real MP-arm SDTM source and ODA credentials are **not** committed (patient-data protection + secrets hygiene), so a bare clone cannot re-run the *real* pipeline — see **[00_governance/REPRODUCIBILITY.md](00_governance/REPRODUCIBILITY.md)** for the data-access path, the pinned environment, and a **self-contained `--demo` smoke test** that runs on a clean clone with no real data, no SAS, and no credentials. The comparator (Cabazitaxel) arm is **synthetic and illustrative** (see *Data provenance*); only the real Mitoxantrone arm is reconciled SAS↔R. A genuine SAS↔R reconciliation requires a run executed against a **real** SAS engine (`--real-sas`, recorded `sas_execution_mode` = `oda`/`local`); the **default** no-engine invocation runs in **`sim`** mode, where a zero-difference reconciliation is tautological. Always check `sas_execution_mode` in `platform/pipeline_health.json` before reading any reconciliation result as double-programming evidence. The flag is guard-enforced: telemetry records `oda`/`local` only when every `*_prod.xpt` is byte-distinct from its R `*_v.xpt` pair (`provenance_guard.passed` in the same file), so a simulated byte-copy cannot be recorded as a real SAS run.

> **Data provenance:** The MP control arm data (371 patients) is the official, de-identified SDTM dataset (`*.sas7bdat`) released by Sanofi in 2013 and accessed via the Project Data Sphere (PDS) repository — real trial data from the *Lancet* 2010 publication. The CbzP comparator arm (378 patients) is a **synthetic, illustrative** cohort generated at the ADaM layer using two methods: **(1) Primary endpoints (OS, PFS)** are reconstructed via genuine **Guyot (2012) IPD reconstruction** (Guyot et al., BMC Med Res Methodol 2012;12:9; `IPDfromKM` package) — the published CbzP Kaplan–Meier curves (de Bono 2010 Fig 2A OS, Fig 3 PFS) are digitised and combined with the published numbers-at-risk tables, then the KM estimator is inverted to recover pseudo-IPD consistent with the observed curve. This derives the CbzP survival shape from the **published curve itself**, **independently of the MP arm** (no HR division) — an accepted HTA technique (NICE TSD-14) that removes the circularity of the previous PH-scaling approach. It validates against the publication: reconstructed OS median 15.2 mo (pub 15.1), 228 deaths (pub 227), and **OS HR vs the real MP arm = 0.70, matching the published 0.70 exactly** (see `01_source_data/guyot_validation_report.md`). **(2) Secondary endpoints (TTPAIN, TTPSA, TTUMOR)** remain PH-scaled from the real MP arm (the paper publishes no KM curves with at-risk tables for these endpoints, so Guyot reconstruction is not possible). Non-survival domains use fixed-seed sampling from published Table 1/Table 2 marginals. The CbzP arm is **not real patient data**; it exists to exercise the comparative-TFL and Project Optimus workflows.

---

## Illustrative Pipeline Outputs *(synthetic comparator — not clinical findings)*

> [!NOTE]
> **These numbers are not study results and must not be read as a re-analysis of the TROPIC trial.** The CbzP arm is synthetic (see *Data provenance* above). For the **primary endpoints (OS, PFS)**, the CbzP arm is reconstructed via genuine Guyot (2012) IPD reconstruction from the published KM curves *independently* of the MP arm — the resulting HR is **not circular** but is an approximation limited by digitisation fidelity to the published curve. For the **secondary endpoints shown below (TTPSA, TTUMOR)**, the CbzP arm remains PH-scaled and is therefore circular by construction. The table below presents what the TFL programs *compute from the synthetic data*, alongside the published values, to demonstrate the analysis pipeline.

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

> **Architecture note:** the current 30-stage pipeline follows the evidence chain
> `source data -> specification -> metadata -> analysis dataset -> output -> QC evidence -> reviewer explanation`.
> See [docs/PIPELINE_ARCHITECTURE_REDESIGN.md](docs/PIPELINE_ARCHITECTURE_REDESIGN.md)
> for the source-backed redesign and migration map; [config/evidence_layers.yaml](config/evidence_layers.yaml)
> defines the repository's physical evidence-layer contract.
> The cross-functional delivery model is defined in
> [docs/BIOMETRICS_DELIVERY_OPERATING_MODEL.md](docs/BIOMETRICS_DELIVERY_OPERATING_MODEL.md)
> and enforced structurally by [config/delivery_workstreams.yaml](config/delivery_workstreams.yaml);
> department workflows and the modern risk-based validation stance are grounded in
> [docs/REGULATORY_WORKFLOW_RESEARCH.md](docs/REGULATORY_WORKFLOW_RESEARCH.md);
> the generated status view is [docs/DELIVERY_EVIDENCE_DASHBOARD.md](docs/DELIVERY_EVIDENCE_DASHBOARD.md).
> The source-intake gate now has an aggregate, patient-safe profile at
> [docs/SOURCE_PROFILING_REPORT.md](docs/SOURCE_PROFILING_REPORT.md).
> TFL output control is indexed at [docs/TFL_OUTPUT_INDEX.md](docs/TFL_OUTPUT_INDEX.md).
> Metadata governance is summarized at [docs/METADATA_CONTROL_REPORT.md](docs/METADATA_CONTROL_REPORT.md).
> ADaM predecessor lineage and sponsor-defined CT dispositions are governed by
> [config/metadata_lineage.yaml](config/metadata_lineage.yaml) and checked with
> `python3 platform/apply_metadata_lineage.py --check`.
> CTQ and estimand traceability is governed by [config/ctq_traceability.yaml](config/ctq_traceability.yaml)
> and summarized at [docs/CTQ_TRACEABILITY_REPORT.md](docs/CTQ_TRACEABILITY_REPORT.md).
> Risk-based validation is machine-checked through [config/validation_strategy.yaml](config/validation_strategy.yaml)
> and [docs/VALIDATION_STRATEGY_CONTROL_REPORT.md](docs/VALIDATION_STRATEGY_CONTROL_REPORT.md).
> Release-candidate readiness is checked at [docs/RELEASE_CANDIDATE_CHECKLIST.md](docs/RELEASE_CANDIDATE_CHECKLIST.md).
> Runtime stages are mapped to delivery gates at [docs/ORCHESTRATOR_GATE_MAP.md](docs/ORCHESTRATOR_GATE_MAP.md).
> The complete architecture-control suite runs locally and in CI with
> `python3 platform/build_delivery_controls.py`.

```
┌────────────────────────────────────────────────────────────────────────────┐
│  TROPIC Analysis Pipeline · Python orchestrator cibuild.py · 30 stages     │
└────────────────────────────────────────────────────────────────────────────┘

  01_source_data/real_sdtm/   (34 native SAS data sets, sas7bdat — official Sanofi 2013 release)
        │
        ▼
  [1]    ADaM spec label/order artifacts
  [2-3]  SDTM staging ingest + R SDTM validation
        │
        ▼                                              ┐
  [4-11] R ADaM/BIMO validation track                  │  independent SAS + R
  [12]   SAS 9.4 production  (ODA / local / sim)        ┘  implementations of
                                                       every derivation
        │
        ▼
  [13]    dataset reconciliation       (diffdf, cell-by-cell, 8 domains)
  [14-16] admiral third-engine core    (ADSL + OS/PFS + reconciliation)
  [17-20] comparator bridge, TFLs, results reconciliation, forest HR reconciliation
  [21-22] spec -> define conformance + spec -> data conformance
        │
        ▼
  [23-25] Dataset-JSON (v1.1), ARS (v1.0), USDM (v3.0)
        │
        ▼
  [26-28] Module 5 package + eCTD backbone/STF + materialized sequence
  [29-30] log cleanliness + release-run manifest binding
```

### Dual-Language Validation Model

```
Real SDTM (SAS7BDAT)
        │
        ├──▶  SAS 9.4 Production  ──▶  adsl_prod.xpt  ──┐
        │     04_analysis_datasets/programs/sas/                         │
        │                                                ├──▶  diffdf  ──▶  Reconciled
        └──▶  R Independent QC    ──▶  adsl_v.xpt    ──┘
              04_analysis_datasets/programs/r/              │
                                           ▼
                                    04_analysis_datasets/adam/  (7 ADaM XPTs)
                                           │
                                           ▼
                                    05_outputs/tfl/  (TFL Suite)
```

> **Third track for the highest-risk endpoints.** Under the [risk-based validation plan](07_reviewer_explanation/guides/RISK_BASED_VALIDATION.md), ADSL and the primary efficacy endpoints (OS, PFS) are *additionally* re-derived with the pharmaverse **`admiral`** package and reconciled cell-for-cell (zero cell-level differences) against the SAS production track — see [`06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md`](06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md). Validation depth scales with risk: three engines on the critical endpoints, two on supporting datasets, automated conformance on metadata.

---

## Repository Structure

```
TROPIC/
|-- 00_governance/                  # Reproducibility, data access, operating boundaries
|-- 01_source_data/                 # Read-only source intake and source-side reconstruction utilities
|-- 02_specifications/              # SAP and analysis authority
|-- 03_metadata/                    # ADaM spec, Define-XML, schemas, USDM
|-- 04_analysis_datasets/           # SAS/R programs, ADaM XPT outputs, Dataset-JSON exports
|-- 05_outputs/                     # TFLs, ARS, reporting outputs
|-- 06_qc_evidence/                 # Reconciliation, conformance, audit registers, run records
|-- 07_reviewer_explanation/        # ADRG, SDRG, BDRG, SDSP, traceability, review tools
|-- 08_submission_package/          # Module 5 package tree and eCTD sequence 0000
|-- config/                         # Manifest, study parameters, evidence/workstream controls
|-- platform/                       # Orchestrator, build gates, package builders, status emitters
|-- docs/                           # Operating-model dashboards, workstream packs, runbooks
|-- studies/                        # Multi-study proof area
`-- tests/                          # R smoke/regression tests
```

---

## Quickstart

### Prerequisites
- **R 4.6.0+** (via Homebrew: `brew install r`)
- **Python 3.10+**
- **SAS 9.4** or **SAS OnDemand for Academics (ODA)** *(optional — pipeline runs in simulation mode without a SAS engine)*
  * *For ODA mode:* Requires a **Java Runtime (JRE 8+)**, the **`saspy`** Python package, and ODA credentials setup (see [`docs/runbooks/ODA_GUIDE.md`](docs/runbooks/ODA_GUIDE.md)).

### Run the Full Pipeline

```bash
# Clone and enter
git clone https://github.com/antonybevan/TROPIC_sanofi.git TROPIC && cd TROPIC

# Run all 30 manifest-governed stages (default = sim mode; add --real-sas for a genuine ODA run)
python3 platform/cibuild.py
```

Expected result:
```
All clinical pipeline stages compiled successfully.
pipeline_health.json records the run scope, SAS mode, provenance guard, and all 30 stages.
```

> The numerical results reconciliation stage transparently reports **`SKIPPED`** in `sim`/`cached` mode (no real SAS `PROC LIFETEST`
> statistics exist to reconcile); under `--real-sas` it computes and reports a genuine `PASS`/`FAIL`.

> **Multi-study.** The engine is study-agnostic — pipeline *structure* lives in `config/study_manifest.yaml`,
> not in code. A second study runs through the **same** engine via
> `python3 platform/cibuild.py --study DEMO02` (see [`studies/README.md`](studies/README.md)).

### eCTD Module 5 Submission Package

eCTD packaging runs automatically as **Stage 26** (with the eCTD backbone + STF and sequence materialization following as Stages 27-28) and may also be invoked standalone after a build:

```bash
python3 platform/package_ectd.py
```

It assembles the deliverables into an **eCTD Module 5 — Clinical Study Reports (Section 5.3)** style structure, following the folder conventions of the FDA *Study Data Technical Conformance Guide*. As of the SAP v4.0 lock review, this package is still remediation-controlled rather than submission-release-controlled: stale-sequence purge, SDTM 3.4 package-source enforcement, and CRF provenance are explicit gates.

- **`08_submission_package/m5/datasets/<study>/tabulations/sdtm/`** — SDTM datasets as **SAS Transport (XPORT v5, `.xpt`)** files, the trial-level `define.xml` (Define-XML 2.1), the source CRF copy (`blankcrf.pdf` when available; not an annotated CRF unless separately supplied), and the **SDTM Data Reviewer's Guide** (`sdrg.pdf`).
- **`08_submission_package/m5/datasets/<study>/analysis/adam/`** — ADaM datasets (XPORT v5), the analysis `define.xml` (Define-XML 2.1 + ARM), the governing ADaM specification (`ADaM_spec.xlsx`) with its spec-to-define conformance report, the **Analysis Data Reviewer's Guide** (`adrg.pdf`), and the source `programs/`.
- **`08_submission_package/m5/datasets/<study>/bimo/`** — the **Bioresearch Monitoring (BIMO)** clinical-site dataset (`clinsite.xpt`) and its data Reviewer's Guide (`bdrg.pdf`), per the FDA BIMO Technical Conformance Guide.
- **`08_submission_package/m5/53-clin-stud-rep/535-rep-effic-safety-stud/...`** — the **Clinical Study Report (ICH E3)** with its Tables, Figures & Listings appendices.

A co-located, machine-readable `define.xml` accompanies every dataset folder; its absence is an FDA **Technical Rejection Criterion** for study data.

A **data-free preview** of the package is committed for portfolio visibility — the full eCTD tree with metadata, rendered reviewer guides/CSR, the ADaM spec, conformance reports, and TFLs, with a placeholder note wherever a patient-level dataset would sit. The patient-level transport files (`*.xpt`) are **never** version-controlled: they are de-identified data obtained via Project Data Sphere under a Data Use Agreement that does not permit redistribution. Build the preview with `python3 platform/package_ectd.py --preview`; build the full, data-bearing package locally (with the licensed source present) with `python3 platform/package_ectd.py`.

---

## ADaM Datasets Produced

The submission ADaM datasets (`04_analysis_datasets/adam/*.xpt`, **SAS Transport / XPORT v5**) contain strictly the **real Mitoxantrone (MP) arm (N=371)** and are the only datasets reconciled SAS↔R. The **synthetic, illustrative** Cabazitaxel (CbzP) arm is stored separately as RDS files under `01_source_data/cbzp_reconstructed/` and merged **only** at the TFL step for demonstration figures/tables — it is never written into the reconciled `*_v.xpt`/`*_prod.xpt` deliverables:

| Dataset | Content | MP-Only Rows (saved in `04_analysis_datasets/adam/`) | Combined Rows (merged in TFLs) | Description |
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
| `F-01-1_CONSORT_Disposition.png` | Analysis-population and mortality overview (legacy filename; not a CONSORT flowchart) |
| `F-11-1_KM_OS.png` / `F-11-2_KM_PFS.png` | OS / PFS Kaplan–Meier with number-at-risk |
| `F-12-1_Subgroup_Forest.png` | OS subgroup forest (univariate Cox HRs) |
| `F-13-1_PSA_Waterfall.png` | PSA best % change from baseline |
| `F-14-1_Swimmer_Plot.png` | Treatment-exposure swimmer |
| `F-17-1_Optimus_Scatter.png` | Project Optimus exposure–response |
| `T-11` / `T-17` / `T-20` / `T-21` (`.txt`) | Efficacy (KM/Cox), Project Optimus tables, TEAE summary, CTCAE lab shifts |
| Listings | No listing is currently released. The prior discontinuation placeholder was removed because it had no production program or source lineage. |

Figure QC validates both layers. `tests/test_figure_outputs.R` gates file presence, the
2400×1650 canvas contract, minimum size, and opaque backgrounds. The exact SAS
figure-driving exports are reconciled to R by
`06_qc_evidence/reconciliation/figure_data_reconcile.R`: KM HR/CIs and all displayed risk counts,
waterfall subject/value/category records, swimmer subjects/durations/death markers, and
exposure-response observations. `forest_reconcile.R` separately checks all 13 forest HR/CIs.

### SAS production-track graphics (capability demonstration)

To demonstrate that the production environment can deliver regulatory-grade graphics natively, the
core efficacy/safety statistical figures are **also** rendered in SAS 9.4 via ODS
Graphics (`04_analysis_datasets/programs/sas/T_tfl_generation.sas` — PROC LIFETEST / SGPLOT / SGPANEL),
output to [`05_outputs/tfl/output/figures/sas/`](05_outputs/tfl/output/figures/sas/): KM OS & PFS, subgroup forest, PSA
waterfall, exposure swimmer, and the Optimus exposure–response scatter.

> This is a **capability demonstration**, not a duplicated deliverable: a regulatory submission
> normally ships one validated TFL set. The SAS figures are a supplementary native rendering;
> their figure-driving records and displayed statistics are numerically reconciled to the R track,
> but the graphics engines are not expected to produce pixel-identical typography. A genuine
> independent SAS-vs-R comparison holds for the real MP arm only — its ADaM is derived separately
> in SAS (`00_master_driver.sas`) and R (admiral) from the common SDTM and reconciled **numerically**
> in `06_qc_evidence/reconciliation/`. The synthetic CbzP arm is reconstructed once (R, Guyot) and rendered on
> both tracks from that same source (the SAS bridge XPT is a format conversion of the R `.rds`, gated
> cell-for-cell by `check_cbzp_bridge.R`), so for that arm the figures show rendering fidelity, not an
> independent derivation. The analysis-population overview (legacy `CONSORT` filename) and the
> text tables are produced on the R track only.
> The SAS figures are rendered on ODA via `python3 platform/_oda_render_tfl.py`.

---

## Regulatory Standards Alignment

The pipeline is engineered to mirror data-standards expectations used in regulated clinical programming — the CDISC versions named in the **FDA Data Standards Catalog**, the eCTD Module 5 packaging conventions of the *Study Data Technical Conformance Guide*, and the ICH E3/E9 reporting frameworks. **This remains a demonstration / portfolio project, not a regulatory submission:** the table states what the pipeline is designed to implement or has locally checked, not certified, audited compliance. "Pattern demonstrated/implemented" means the technique is applied on this partly synthetic dataset; it does **not** assert validated conformance.

| Standard / FDA expectation | What this repository implements |
|---|---|
| CDISC ADaMIG v1.3 | ADaM structure/metadata modelled for all 7 datasets (real MP arm) |
| CDISC Define-XML 2.1 + ARM v1.0 | Both `define.xml` (ADaM) and `define_sdtm.xml` **pass full XSD validation** (`03_metadata/define/validate_xsd.sh`) **and parse cleanly in the CDISC CORE reference engine** (`Define_XML_Version 2.1.0`). The CORE run surfaced + fixed 3 defects the XSD check missed (invalid `Role` on `ItemGroupDef`, empty `TranslatedText`, missing `def:Class`). |
| **CDISC CORE business-rule conformance** | **Real CDISC reference-engine run** (CORE 0.16.0). **SDTM:** CORE-validated at **SDTMIG 3.4** (CT 2026-03-27) — targeted structural rules cleared, residual findings classified (`platform/conformance/CORE_SDTM34_RUN_RECORD.md`); the earlier 3.1.1-source-against-3.2 baseline run is retained at `core_sdtm_report.json`. **ADaM:** CORE/CDISC Library ships **0 executable ADaM rules**, so executable ADaM rules are authored in CORE YAML (`platform/conformance_rules/adam/`) and run via `--local-rules` → 7/7 SUCCESS. See `platform/conformance/CORE_RUN_RECORD.md`. Official `AD####` rule IDs are members-only. A gate-consistency fix surfaced while authoring these rules was contributed upstream and **merged** into the engine ([cdisc-rules-engine PR #1770](https://github.com/cdisc-org/cdisc-rules-engine/pull/1770), 2026-06-22). |
| CDISC SDTMIG v3.4 (uplifted from v3.1.1 source) | PDS source SDTM is trial-era v3.1.1 (below the FDA support floor); a derived **v3.4** layer (EPOCH, Trial Design, AGE/AGEU, AESOC, week-vars->SUPP) is what `define_sdtm.xml` describes and what is packaged in `08_submission_package/m5/.../tabulations/sdtm/`. Pristine source (`01_source_data/real_sdtm/`) is never modified; uplift via `platform/uplift_sdtm_34.R` (data) + `03_metadata/define/uplift_define_34.py` (define). See SDRG §5 |
| ADaM specification — metadata control source | Authoring-format `ADaM_spec.xlsx` (metacore / Pinnacle 21) governs metadata alignment between `define.xml` and produced data; SAP v4.0 governs analysis intent. Automated **spec→define** and **spec→data** (metacore/metatools/xportr) conformance gates run in the pipeline and CI |
| CDISC machine-readable layers — Dataset-JSON / ARS / USDM | **Dataset-JSON v1.1** emitted alongside XPT for all 42 datasets (`04_analysis_datasets/datasetjson/`; schema-valid, lossless round-trip); **Analysis Results Standard v1.0** ReportingEvent + ARD (`05_outputs/ars/`; real MP-arm KM results); **USDM v3.0** machine-readable study definition (`03_metadata/usdm/`; built through the `usdm_model` classes). Wired into the pipeline as stages 23–25 (`config/study_manifest.yaml`), each gated by its own exit code; `build_usdm` additionally runs as a data-free **CI** gate, while the data-dependent Dataset-JSON/ARS generators are enforced in the full pipeline run. Standalone reproduction is documented in `docs/runbooks/OFFLINE_LAYER_RUNBOOK.md` |
| FDA Study Data Technical Conformance Guide | eCTD Module 5 (Section 5.3) folder layout, SAS Transport (XPORT v5) datasets, and a co-located `define.xml` per dataset folder, assembled by `package_ectd.py`. A **DTD-valid eCTD sequence backbone** (`index.xml` + STF + US regional metadata) is materialised under `08_submission_package/ectd/0000/` (`materialize_ectd.py`); application identifiers are `EXAMPLE` placeholders, so it demonstrates the sequence structure rather than a real submission |
| FDA BIMO Technical Conformance Guide | Clinical-site-level dataset (`clinsite`) with per-site enrollment/safety roll-ups + a BIMO Data Reviewer's Guide (BDRG). Site investigator name (`INVNAM`) is a **flagged synthetic placeholder** |
| ICH E9 (Statistical Principles) | Hierarchical step-down gatekeeping **pattern implemented** (exercised on a synthetic comparator — not an inferential result) |
| ICH E3 (TFL Catalogue) | TFL set rendered in NEJM/Lancet style |
| FDA Project Optimus | Exposure–response dose-optimisation analysis **pattern demonstrated** on synthetic data |
| Reproducibility | `renv.lock` pins the R toolchain; `.log` files (logrx) capture run provenance. **Note:** this is run traceability, *not* 21 CFR Part 11 compliance (which requires validated access controls, user attribution, and e-signatures — out of scope here). |

---

## SAS Execution via SAS OnDemand for Academics

Stage 11 obtains the SAS 9.4 production datasets through one of several **explicitly labelled** execution modes. The mode is resolved at runtime and recorded in `platform/pipeline_health.json` as `sas_execution_mode`:

| Invocation | Mode | What happens |
|---|---|---|
| `--real-sas` (local `sas` on PATH) | `local` | Runs `00_master_driver.sas` on the local SAS 9.4 engine this session. |
| `--real-sas` (no local SAS, SASPy configured) | `oda` | Connects to **SAS OnDemand for Academics** via the resilient broker, verifies the resident SDTM manifest, runs `00_master_driver.sas` via SASPy IOM, downloads the 7 `*_prod.xpt`. |
| `--real-sas` (ODA unreachable within the budget) | `sim` | Transparent fallback: the validation outputs are byte-copied, and telemetry records `oda_last_error_class` and `next_recommended_window`. The mode is never relabelled `oda`. |
| `--real-sas` (no engine available) | `error` | **Fails explicitly** — a real SAS run was requested but no engine is available; the build aborts rather than record a false PASS. |
| `--use-cached-sas` | `cached` | Reconciles against **pre-existing** `*_prod.xpt` from a prior SAS run. SAS is **not** re-executed this session, and telemetry records this explicitly. |
| *(no flag, no SAS)* | `sim` | Byte-copies `*_v.xpt` → `*_prod.xpt`; explicitly flagged as **not** double programming, since a zero-difference reconciliation is tautological in this mode. |

> The `cached` and `sim` modes never represent a real SAS run as having occurred. `oda` mode is **earned** — it is recorded only after a live workspace probe and verification of the resident SDTM manifest (see below); only `local` and `oda` are reported as genuine double programming.
>
> **Provenance guard.** An `oda`/`local` run is finalized GREEN only when every `*_prod.xpt` is byte-distinct from its R validation `*_v.xpt` — the on-disk signature of independent double programming — **and** the SDTM manifest SHA recorded for the run matches the current SDTM source, so the production data is bound to the same verified input the R track validated against. If any production file is byte-identical to (or missing relative to) its pair, or the manifest SHA is missing or mismatched, the health record is set to **RED** with a `provenance_guard` block detailing the failed check; a restamped snapshot, a simulated byte-copy, or a swapped SDTM source therefore cannot be recorded as a real SAS run.

### Two-job ODA workflow (Job A seed · Job B reconcile)

ODA's ~200 MB SDTM upload and its intermittent load-balancing spawner are accommodated by
separating the work into two jobs and routing every connection through a resilient broker
(`platform/oda_broker.py`). Full operator guide: **[`docs/runbooks/ODA_GUIDE.md`](docs/runbooks/ODA_GUIDE.md)**.

```bash
# Job A — seed the SDTM once (idempotent; sha256/nrows manifest; zero upload if already resident)
python3 platform/seed_sdtm.py

# Job B — reconcile on demand (broker absorbs spawner timeouts; verifies the manifest before running)
python3 platform/cibuild.py --real-sas
```

The broker applies status-gated, full-jitter backoff within a wall-clock budget (`TROPIC_ODA_MAX_WAIT`),
fails fast on authentication or encryption errors, maintains connection-slot hygiene (a single-flight
lock with guaranteed teardown), and **earns** `oda` mode only through a live nonce probe. A genuine run
is confirmed by `sas_execution_mode == "oda"` **and** `reconciliation == "SAS_vs_R"` in `pipeline_health.json`.

> **Committed evidence:** A frozen snapshot of a genuine GREEN `oda` run is retained under
> [`platform/evidence/`](platform/evidence/) — including an MD5 manifest demonstrating that every
> SAS-produced `*_prod.xpt` is **byte-distinct** from its R-produced `*_v.xpt` yet reconciles
> **cell-identical** across all eight domains (ADSL…ADTTE plus the BIMO `clinsite`). It is stored
> separately from the live telemetry so that a subsequent `sim` run cannot overwrite this evidence.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154. [doi:10.1016/S0140-6736(10)61389-X](https://doi.org/10.1016/S0140-6736(10)61389-X)

### Audit & review records

- `06_qc_evidence/audit/run_records/REPO_AUDIT_2026-06-21.md` — submission-readiness repository audit (standards currency, pipeline DAG, reconciliation matrix, full orphan sweep).
- `06_qc_evidence/audit/run_records/FDA_REVIEWER_AUDIT_2026-06-20.md` — independent FDA-reviewer conformance audit (filing-risk perspective).
- `06_qc_evidence/audit/run_records/ADDITIVE_INTEGRATION_SCAN_2026-06-20.md` — emerging-standards additive-integration scan (ARS / USDM / Dataset-JSON / eCTD).
- Reviewer guides: `07_reviewer_explanation/guides/{ADRG, SDRG, BDRG, SDSP, TRACEABILITY_MATRIX}.md`.

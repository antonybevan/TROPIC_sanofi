<div align="center">

# TROPIC — Controlled Clinical Biometrics Demonstration

### Study EFC6193 / XRP6258 · NCT00417079
**Cabazitaxel vs Mitoxantrone in mCRPC — Phase III RCT**
*Sanofi · de Bono et al., Lancet 2010*

[![Claim](https://img.shields.io/badge/Product-Path%20A%20controlled%20demo-important?style=flat-square)](docs/PRODUCT_CLAIM.md)
[![CDISC](https://img.shields.io/badge/CDISC-ADaMIG%20v1.3%20%7C%20SDTMIG%20v3.4-005A9C?style=flat-square)](https://www.cdisc.org/)
[![Define-XML](https://img.shields.io/badge/Define--XML-2.1%20%2B%20ARM-005A9C?style=flat-square)](03_metadata/define/)
[![eCTD](https://img.shields.io/badge/eCTD-Module%205%20style-005A9C?style=flat-square)](08_submission_package/m5/)
[![Release](https://img.shields.io/badge/Seal-v0.2.2--portfolio-success?style=flat-square)](docs/RELEASE_NOTE_v0.2.2-portfolio.md)

</div>

---

## What this is (read before anything else)

**TROPIC is a controlled, non-submission clinical biometrics programming demonstration** — not an FDA filing, not Part 11, not a re-analysis of trial efficacy.

| Allowed | Forbidden |
|---|---|
| SDTM → ADaM → TFL → Define → eCTD-style package | “Submission-ready / NDA complete” |
| Dual-language SAS 9.4 / R recon on **real MP arm** | “GxP org double programming complete” |
| Risk-tiered admiral third engine (ADSL, OS, PFS) | “Independent clinical confirmation of CbzP benefit” |
| Hash-sealed demo release-candidate under Path A | “Part 11 compliant” |

**Binding claim:** [`docs/PRODUCT_CLAIM.md`](docs/PRODUCT_CLAIM.md)
**Current release narrative:** [`docs/RELEASE_NOTE_v0.2.2-portfolio.md`](docs/RELEASE_NOTE_v0.2.2-portfolio.md)
**What GitHub is allowed to contain:** [`docs/REPO_SURFACE_POLICY.md`](docs/REPO_SURFACE_POLICY.md)
**10-minute interviewer walk:** [`docs/INTERVIEWER_GUIDE.md`](docs/INTERVIEWER_GUIDE.md)

> `v0.1.0-demo-rc.1` remains an immutable historical Path A tag record. The
> current portfolio release is `v0.2.2-portfolio`, with its connected-evidence
> disposition recorded in [`SECTION_05_PORTFOLIO_FINALIZATION_AUDIT_2026-08-04.md`](06_qc_evidence/audit/section_reviews/SECTION_05_PORTFOLIO_FINALIZATION_AUDIT_2026-08-04.md).

> **Portfolio surface:** this repo tracks the **review package face**, **spine programs**, **config**, and a **minimal seal pack** — not patient data, not secrets, not regenerable factory status piles. That is standard practice, not incompleteness.

---

## Open first (30 seconds)

There are **two surfaces**. Industry does not present a Git monorepo as “the submission.” A reviewer opens the package; an engineer opens the factory.

| # | Open this | Why |
|---:|---|---|
| 1 | [`docs/INTERVIEWER_GUIDE.md`](docs/INTERVIEWER_GUIDE.md) | What we want interviewers to see |
| 2 | [`docs/PRODUCT_CLAIM.md`](docs/PRODUCT_CLAIM.md) | What you may assert — Path A only |
| 3 | [`08_submission_package/README.md`](08_submission_package/README.md) → [`m5/`](08_submission_package/m5/) | **Review surface** (Module 5 style) |
| 4 | [`07_reviewer_explanation/guides/`](07_reviewer_explanation/guides/) | ADRG · SDRG · BDRG · SDSP |
| 5 | [`docs/RELEASE_NOTE_v0.2.2-portfolio.md`](docs/RELEASE_NOTE_v0.2.2-portfolio.md) | Current portfolio seal and review anchors |
| 6 | `python3 scripts/verify_release.py` | Re-check machine grades (no SAS needed) |
| 7 | `python3 platform/cibuild.py --demo` | Bare-clone smoke (no patient data) |

**Navigation index:** [`docs/INDEX.md`](docs/INDEX.md) — Reviewer · Engineer · QC
**Repo surface policy:** [`docs/REPO_SURFACE_POLICY.md`](docs/REPO_SURFACE_POLICY.md) — what is / isn’t in git
**Script map:** [`docs/SCRIPT_MAP.md`](docs/SCRIPT_MAP.md) · **Factory triage:** [`platform/README.md`](platform/README.md)

### Interview line (use this)

> There are two views. The **submission-style package** is under `08_submission_package/m5/` — that is what a reviewer would navigate. The rest of the repo is the **controlled factory**: dual-language ADaM, admiral, gates, and seals. Patient data are not in git. Comparative CbzP is synthetic and disclosed. This is Path A — a controlled demonstration, not a filing.

---

## Dual surface map

```text
┌─────────────────────────────────────────────────────────────────┐
│  SURFACE A — REVIEW PACKAGE (demo this first)                   │
│  08_submission_package/m5/                                      │
│    datasets/tropic/tabulations/sdtm/   XPT + define + SDRG      │
│    datasets/tropic/analysis/adam/      XPT + define + ADRG + pgms│
│    datasets/tropic/bimo/               clinsite + BDRG          │
│    53-clin-stud-rep/.../               CSR / figures / tables   │
└─────────────────────────────────────────────────────────────────┘
                              ▲ produced & sealed by
┌─────────────────────────────────────────────────────────────────┐
│  SURFACE B — CONTROLLED FACTORY (engineers / QC)                │
│  00…07 evidence chain · config/ · platform/ · scripts/ · tests/ │
│  programs live under 04_analysis_datasets/programs/{sas,r}/     │
│  QC warehouse under 06_qc_evidence/                             │
└─────────────────────────────────────────────────────────────────┘
```

| If you are… | Start here | Do not start here |
|---|---|---|
| **Mock FDA / portfolio reviewer** | `08_submission_package/m5/` + guides | `platform/` status JSON |
| **Statistical programmer** | `04_analysis_datasets/programs/` + SAP v4.0 | Random regenerated `docs/*_REPORT.md` |
| **Platform / pipeline engineer** | `config/study_manifest.yaml` + `platform/cibuild.py` | Treating root as eCTD |
| **QC / validation** | `06_qc_evidence/` + findings board | Claiming green JSON = filing |

---

## Repository structure (evidence chain + factory)

The numbered folders are an **internal evidence-chain model** (source → package).
The **FDA-shaped tree** lives *inside* `08_submission_package/` only.

```text
TROPIC/
│
│  ── LAYER 0  Claim & entry ──────────────────────────────────
├── README.md                         ← you are here
├── docs/PRODUCT_CLAIM.md             ← binding Path A claim
├── docs/INDEX.md                     ← Reviewer / Engineer / QC tours
├── docs/RELEASE_NOTE_v0.2.2-portfolio.md
│
│  ── LAYER 1  Review surface ─────────────────────────────────
├── 08_submission_package/            ← THE deliverable face
│   ├── README.md                     ← package tour
│   ├── m5/                           ← Module 5 style tree
│   └── ectd/0000/                    ← sequence + backbone demo
├── 07_reviewer_explanation/guides/   ← ADRG · SDRG · BDRG · SDSP
│
│  ── LAYER 2  Analysis truth ─────────────────────────────────
├── 00_governance/                    # reproducibility boundary
├── 01_source_data/                   # intake (real SDTM not redistributed)
├── 02_specifications/sap/            # SAP v4.0 programming authority
├── 03_metadata/                      # ADaM spec · Define-XML · USDM
├── 04_analysis_datasets/             # programs + ADaM XPT + Dataset-JSON
├── 05_outputs/                       # TFLs · ARS
│
│  ── LAYER 3  Factory ────────────────────────────────────────
├── config/                           # manifest · catalog · controls
├── platform/                         # orchestrator · packagers · seals
├── scripts/verify_release.py         # release re-check
├── tests/                            # R smoke / figure gates
├── studies/                          # multi-study engine proof (DEMO02)
│
│  ── LAYER 4  QC warehouse ───────────────────────────────────
├── 06_qc_evidence/                   # recon · gates · findings · run records
└── docs/                             # operating model + generated control reports
```

**Authority stack (conflicts):** PRODUCT_CLAIM → SAP v4.0 → lock memo → TFL catalog → study config/manifest → machine seals → ADRG/SDRG (must not exceed claim).

---

## Scope & data provenance (non-negotiable)

| Arm | N | Nature | Where used |
|---|---:|---|---|
| **MP (control)** | 371 | Real de-identified SDTM (Sanofi 2013 / Project Data Sphere) | Reconciled ADaM (`*_prod.xpt` / `*_v.xpt`); **not committed to git** |
| **CbzP (comparator)** | 378 | **Synthetic / reconstructed** (Guyot OS/PFS; PH secondary) | TFL merge only — never in reconciled package ADaM |

- **Programming authority:** `02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx` (lock memo: package is **not** submission-passed).
- **Bare clone:** real MP SDTM and ODA credentials are not in git — see [`00_governance/REPRODUCIBILITY.md`](00_governance/REPRODUCIBILITY.md). Use `--demo` for a data-free smoke path.
- **SAS mode honesty:** check `sas_execution_mode` in `platform/pipeline_health.json`. Default (no engine) is `sim` — zero-diff recon is **tautological**. Genuine dual-language evidence requires `oda` / `local` with provenance guard PASS.

Full Guyot validation notes: [`01_source_data/guyot_validation_report.md`](01_source_data/guyot_validation_report.md).

---

## Quickstart

### Prerequisites
- **R 4.6.0+** · **Python 3.10+**
- **SAS 9.4** or **SAS OnDemand for Academics** *(optional — default is simulation mode)*
  ODA setup: [`docs/runbooks/ODA_GUIDE.md`](docs/runbooks/ODA_GUIDE.md)

### Run / verify

```bash
git clone https://github.com/antonybevan/TROPIC_sanofi.git TROPIC && cd TROPIC

# What interviewers can do immediately (no patient data, no SAS)
python3 scripts/verify_release.py          # re-check committed Path A seals
python3 platform/cibuild.py --demo         # smoke: syntax + recon methodology

# Full governed DAG (requires local SDTM; default = sim SAS unless --real-sas)
python3 platform/cibuild.py
python3 platform/cibuild.py --real-sas     # genuine ODA/local when configured

# Assemble and validate the complete eCTD-style sequence (after a local build)
python3 platform/package_ectd.py
python3 platform/build_ectd_backbone.py
python3 platform/materialize_ectd.py       # includes complete G08 surface validation
```

See [`00_governance/REPRODUCIBILITY.md`](00_governance/REPRODUCIBILITY.md) and [`docs/REPO_SURFACE_POLICY.md`](docs/REPO_SURFACE_POLICY.md).

Multi-study proof: `python3 platform/cibuild.py --study DEMO02` — see [`studies/README.md`](studies/README.md).

---

## Pipeline (factory summary)

Manifest-driven **37-stage DAG** (`config/study_manifest.yaml` · `platform/cibuild.py`):

```text
01 real SDTM (local, not in git)
  → staging + R validation
  → synthetic comparator reconstruction + intrinsic/compatibility validation + XPT export
  → independent SAS production + R validation ADaM
  → cell-level recon (diffdf) + results recon
  → admiral third engine (ADSL, OS, PFS)
  → TFLs (catalog-controlled) + figure data recon
  → Define / spec conformance
  → Dataset-JSON · ARS · USDM (additive layers)
  → Module 5 package + eCTD backbone
  → log cleanliness + release-run hash seal
```

**Dual-language model:** SAS `*_prod.xpt` ↔ R `*_v.xpt` on real MP only.
**Third track (risk-based):** admiral for ADSL + OS/PFS — see [`06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md`](06_qc_evidence/reconciliation/ADMIRAL_RECONCILIATION.md).
**Single-author tracks** = implementation independence, **not** organizational GxP double programming.

Architecture redesign map: [`docs/PIPELINE_ARCHITECTURE_REDESIGN.md`](docs/PIPELINE_ARCHITECTURE_REDESIGN.md)
Operating model: [`docs/BIOMETRICS_DELIVERY_OPERATING_MODEL.md`](docs/BIOMETRICS_DELIVERY_OPERATING_MODEL.md)

---

## What the package contains

### ADaM (reconciled MP arm only)

| Dataset | Role |
|---|---|
| ADSL | Subject-level analysis population |
| ADEX / ADCM | Exposure · concomitant meds |
| ADAE / ADLB | Safety programming (TEAE, labs/shifts) |
| ADRS / ADTTE | Response · TTE (OS, PFS, secondaries) |

Paths: development `04_analysis_datasets/adam/` · package `08_submission_package/m5/datasets/tropic/analysis/adam/datasets/`.

### TFL (catalog-controlled)

In-scope IDs live in [`config/tfl_output_catalog.yaml`](config/tfl_output_catalog.yaml).
Gallery / outputs: [`05_outputs/tfl/`](05_outputs/tfl/) · package CSR appendices under `m5/53-clin-stud-rep/…`.

Representative figures: KM OS/PFS · forest · waterfall · swimmer · Optimus ER.
Tables: T-11 efficacy · T-17 Optimus · T-20 AE summary · T-21 lab shifts.

### Reviewer guides

| Guide | Location |
|---|---|
| ADRG | `07_reviewer_explanation/guides/ADRG.md` (+ PDF in package) |
| SDRG | `…/SDRG.md` (+ `sdrg.pdf` co-located with SDTM) |
| BDRG | `…/BDRG.md` (+ `bdrg.pdf` with BIMO) |
| SDSP / Traceability | same guides folder |

### Standards alignment (demonstration scope)

CDISC ADaMIG 1.3 · SDTMIG 3.4 uplift · Define-XML 2.1 + ARM · FDA sdTCG Module 5 layout · BIMO clinsite pattern · Dataset-JSON / ARS / USDM additive layers.
**Pattern demonstrated ≠ certified commercial validator clearance.** Details: historical section content retained in package README and ADRG.

---

## SAS execution modes (honesty table)

| Invocation | Mode | Evidence value |
|---|---|---|
| `--real-sas` + local SAS | `local` | Genuine dual-language |
| `--real-sas` + ODA | `oda` | Genuine dual-language (if provenance guard PASS) |
| `--use-cached-sas` | `cached` | Prior prod XPT only — not a new SAS run |
| default / no engine | `sim` | **Not** double programming |

Recorded in `platform/pipeline_health.json`. Frozen GREEN ODA snapshot: [`platform/evidence/`](platform/evidence/).
Operator runbook: [`docs/runbooks/ODA_GUIDE.md`](docs/runbooks/ODA_GUIDE.md).

---

## Workstreams (how the work is organized)

Not a single script pile. Delivery is operated as departments:

| WS | Focus |
|---|---|
| WS-0 | Governance & product claim (G00) |
| WS-1 / WS-2 | Source intake · standards / metadata |
| WS-3 | Analysis programming (SAS / R / admiral) |
| WS-5 | QC, recon, findings disposition |
| WS-6 | Reviewer writing (ADRG/SDRG/BDRG) |
| Release | Seals, RC checklist, tag train |

Board: [`docs/WORKSTREAM_EXECUTION_BOARD.md`](docs/WORKSTREAM_EXECUTION_BOARD.md) · packs: [`docs/workstreams/`](docs/workstreams/).

---

## Reference

de Bono JS, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer…** *Lancet.* 2010;376(9747):1147–1154. [doi:10.1016/S0140-6736(10)61389-X](https://doi.org/10.1016/S0140-6736(10)61389-X)

### Audit & seal records
- Findings disposition: [`06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`](06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md)
- SAP lock memo: [`06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md`](06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md)
- Historical run records: `06_qc_evidence/audit/run_records/`
- Presentation research (why dual surface): [`docs/SUBMISSION_REPO_PRESENTATION_RESEARCH.md`](docs/SUBMISSION_REPO_PRESENTATION_RESEARCH.md)

# Submission-Style Package — Review Surface

**Study:** TROPIC (EFC6193 / NCT00417079)  
**Product claim:** Path A controlled **non-submission** demonstration — see [`docs/PRODUCT_CLAIM.md`](../docs/PRODUCT_CLAIM.md)  
**This folder is Surface A** — what a mock reviewer opens.  
**The factory that builds and seals it** is the rest of the repository (Surface B).

---

## What this is

An **eCTD Module 5–style** clinical study data package assembled for portfolio / training demonstration:

| Included | Meaning |
|---|---|
| SDTM + define + SDRG co-located | Tabulations review path |
| ADaM + define + ADRG + programs | Analysis review path |
| BIMO clinsite + BDRG | Site-level review path (demo) |
| CSR-style figures / tables | TFL appendices under 5.3 |
| eCTD sequence backbone under `ectd/0000/` | Structure demo (`EXAMPLE` app IDs) |

| Not claimed | Why |
|---|---|
| Real FDA sequence / application numbers | Placeholders only |
| Full two-arm real IPD package | MP real; CbzP synthetic (TFLs only) |
| Annotated CRF as sponsor aCRF | Source CRF copy when present — not aCRF unless supplied |
| Part 11 validated system | Hash seals ≠ validated e-signature system |
| Commercial Pinnacle 21 full clearance | Not asserted under Path A |

**Current sealed portfolio release:** [`docs/RELEASE_NOTE_v0.2.2-portfolio.md`](../docs/RELEASE_NOTE_v0.2.2-portfolio.md) · tag `v0.2.2-portfolio`
The earlier `v0.1.0-demo-rc.1`, `v0.2.0-portfolio`, and `v0.2.1-portfolio` notes remain immutable historical release records.

---

## Open order (FDA-mode walk)

Walk the package like a reviewer — not like a GitHub tourist.

### 1. Study data root

```text
m5/datasets/tropic/
```

### 2. Tabulations (SDTM)

```text
m5/datasets/tropic/tabulations/sdtm/
├── datasets/          # *.xpt + define.xml (+ stylesheet)
├── sdrg.pdf           # Study Data Reviewer's Guide (SDTM)
└── blankcrf.pdf       # CRF copy when available
```

**Also read (markdown source of truth for narrative):**  
[`07_reviewer_explanation/guides/SDRG.md`](../07_reviewer_explanation/guides/SDRG.md)

### 3. Analysis (ADaM)

```text
m5/datasets/tropic/analysis/adam/
├── datasets/          # adsl…adtte *.xpt + define.xml (+ stylesheet)
├── programs/          # SAS production + R validation + admiral
├── adrg.pdf           # Analysis Data Reviewer's Guide
└── ADaM_spec.xlsx     # metadata control source
```

**Also read:**  
[`07_reviewer_explanation/guides/ADRG.md`](../07_reviewer_explanation/guides/ADRG.md)

### 4. BIMO (if reviewing site-level)

```text
m5/datasets/tropic/bimo/datasets/
├── clinsite.xpt
└── bdrg.pdf
```

**Also read:**  
[`07_reviewer_explanation/guides/BDRG.md`](../07_reviewer_explanation/guides/BDRG.md)

### 5. Clinical study report appendices (TFLs)

```text
m5/53-clin-stud-rep/535-rep-effic-safety-stud/mcrpc/5351-stud-rep-contr/tropic/
├── csr.pdf
├── figures/           # KM, forest, waterfall, swimmer, Optimus (+ sas/ capability renders)
└── tables/            # T-11, T-17, T-20, T-21
```

Controlled TFL universe (in-scope vs deferred):  
[`config/tfl_output_catalog.yaml`](../config/tfl_output_catalog.yaml)

### 6. Materialized eCTD sequence

```text
ectd/0000/
├── index.xml          # backbone
├── m1/us/             # US regional (EXAMPLE placeholders)
├── m5/                # mirrored study content
└── util/
    ├── dtd/           # checksum-pinned official DTDs
    └── style/         # checksum-pinned official ICH/FDA stylesheets
```

Run record: [`ectd/RUN_RECORD.md`](ectd/RUN_RECORD.md)

---

## Co-location rules (why this layout)

Per FDA Study Data Technical Conformance Guide practice for clinical study data:

| Artifact | Co-located with |
|---|---|
| SDTM XPT | `define.xml`, SDRG, blank CRF under tabulations/sdtm |
| ADaM XPT | `define.xml`, ADRG, programs under analysis/adam |
| BIMO | clinsite + BDRG |
| TFLs | CSR section 5.3 tree — not scattered at repo root |

**Professional signal:** a stranger can open `m5/datasets/tropic/` and understand the study **without** reading `platform/`.

---

## Data honesty inside this package

| Content | Status |
|---|---|
| MP-arm ADaM XPT | Real-arm derived; dual-language recon under genuine SAS when seal says `oda`/`local` |
| SDTM XPT in package | Uplifted / packaged study data layer for demo (source intake separate; **redistribution rights apply**) |
| CbzP comparative TFLs | Built with **synthetic/reconstructed** comparator — non-confirmatory |
| Application / sequence IDs | `EXAMPLE` placeholders |

If package contents and PRODUCT_CLAIM disagree, **PRODUCT_CLAIM wins**.

---

## How this package is built (factory pointer)

Do **not** hand-edit package trees as source of truth.

| Step | Command / path |
|---|---|
| Full DAG | `python3 platform/cibuild.py` (optionally `--real-sas`) |
| Package only | `python3 platform/package_ectd.py` |
| Backbone + sequence | `python3 platform/build_ectd_backbone.py` then `python3 platform/materialize_ectd.py` |
| Complete G08 validation | `python3 platform/validate_ectd_sequence.py` (also runs inside materialization) |
| Preview (data-light) | `python3 platform/package_ectd.py --preview` |
| Verify seals | `python3 scripts/verify_release.py` |
| Orchestrator | `platform/cibuild.py` · manifest `config/study_manifest.yaml` |
| Packager | `platform/package_ectd.py` · backbone `platform/materialize_ectd.py` |

Development programs (source):  
`04_analysis_datasets/programs/{sas,r}/`  
Package copies programs into `m5/.../analysis/adam/programs/` for the review surface.

---

## What is *not* in this folder (by design)

| Lives elsewhere | Why |
|---|---|
| `platform/*.json` status objects | Factory telemetry — not reviewer content |
| Workstream boards / YAML controls | Engineering control plane |
| Findings register / orphan scans | QC warehouse (`06_qc_evidence/`) |
| Shiny app / DEMO02 multi-study proof | Labs / engine proof — not Module 5 |
| Generated delivery dashboards | Operating reports under `docs/` |

Mixing those into `m5/` would contaminate the review surface. They stay in the factory.

---

## Residual risks (read before over-claiming)

- [`docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](../docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md)
- [`06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md`](../06_qc_evidence/audit/FINDINGS_DISPOSITION_BOARD.md)
- [`06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md`](../06_qc_evidence/audit/SAP_LOCK_REVIEW_MEMO.md)

---

## Back to repo face

- Root orientation: [`README.md`](../README.md)  
- Three tours: [`docs/INDEX.md`](../docs/INDEX.md)  
- Presentation research: [`docs/SUBMISSION_REPO_PRESENTATION_RESEARCH.md`](../docs/SUBMISSION_REPO_PRESENTATION_RESEARCH.md)

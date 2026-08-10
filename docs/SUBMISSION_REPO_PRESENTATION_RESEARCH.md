# How Serious Submission Repos Are Presented  
## Research note + honest diagnosis of TROPIC noise

**Date:** 2026-07-09  
**Audience:** You (portfolio / career) · future reviewers · future self  
**Product claim in force:** Path A controlled non-submission demo (`docs/PRODUCT_CLAIM.md`)  
**Sources:** FDA Study Data Technical Conformance Guide (sdTCG); eCTD Module 5 study-data layout; R Consortium Submissions Pilots; PHUSE industry practice; sponsor-style biometrics program trees.

---

## 0. Direct answer

**Why the repo looks like noise**

We mixed **three different products** in one tree and labeled all of them “the project”:

1. **Development / platform factory** (orchestrator, gates, YAML control plane, CI, multi-study engine)  
2. **QC evidence warehouse** (hundreds of status JSONs, CSVs, regenerated reports, orphan registers)  
3. **Submission-style deliverable package** (what an FDA reviewer actually opens: SDTM/ADaM XPT, define, ADRG/SDRG, programs, TFLs, eCTD Module 5)

Industry does **not** present those as one flat “look at my repo.”  
Serious presentation is a **dual surface**:

| Surface | Audience | What they open |
|---|---|---|
| **A. Submission package** | FDA / mock reviewer | `m5/` (or eCTD sequence) — datasets, define, guides, programs, CSR appendices |
| **B. Development repository** | Programmers / platform engineers | source, specs, build system, tests, evidence logs |

TROPIC currently puts A and B (and the evidence warehouse) in the same root, with **78 files under `platform/`**, **200+ JSON status objects**, and **many regenerated markdown reports** competing with the few files a reviewer cares about. The *architecture intent* is good; the *presentation surface* is not.

---

## 1. What FDA actually wants to *see* (submission surface)

FDA’s **Study Data Technical Conformance Guide (sdTCG)** is about **how study data are organized for review in eCTD**, not about how a company stores Git history.

### 1.1 Module 5 study-data tree (clinical)

For a clinical study, the reviewable package is essentially:

```text
m5/
└── datasets/
    └── <study>/
        ├── tabulations/
        │   └── sdtm/
        │       ├── *.xpt              # SDTM transport
        │       ├── define.xml         # + stylesheet
        │       ├── define.pdf         # optional but common
        │       ├── csdrg.pdf          # clinical SDRG (Study Data Reviewer’s Guide)
        │       └── blankcrf.pdf       # annotated blank CRF (aCRF)
        └── analysis/
            └── adam/
                ├── datasets/
                │   ├── *.xpt          # ADaM transport
                │   ├── define.xml
                │   ├── define.pdf
                │   └── adrg.pdf       # Analysis Data Reviewer’s Guide
                └── programs/          # ADaM (+ often analysis) programs
└── 53-clin-stud-rep/…                 # CSR and TFL appendices (figures/tables/listings)
```

**What is *not* in the reviewer’s primary path**

- Orchestrator Python  
- 40 status JSON files  
- Workstream YAML boards  
- Orphan registers  
- CI configs  
- Shiny apps  
- Multi-study engine stubs  

Those may exist in a **sponsor development repo**, but they are **not** how you “present a submission.”

### 1.2 Naming and co-location rules that signal professionalism

From sdTCG practice (clinical):

| Artifact | Expectation |
|---|---|
| SDTM + define + cSDRG | Co-located under tabulations/sdtm |
| ADaM + define + ADRG | Co-located under analysis/adam |
| Programs | Under analysis/adam/programs (and/or analysis programs as allowed) |
| TFLs | With CSR appendices, not dumped as random PNGs at repo root |
| Define | Machine-readable define.xml **with** human review path (PDF/HTML) |
| File names | Stable, conventional (`csdrg.pdf`, `adrg.pdf`, dataset short names) |

**Professional signal:** a stranger can open `m5/datasets/<study>/` and understand the study without reading your orchestrator.

### 1.3 What “submission repo” means in industry slang

People say “submission repo” for two different things:

| Meaning | Correct presentation |
|---|---|
| **Filing package** | eCTD sequence / Module 5 tree only (or a zip that *is* that tree) |
| **Development repo that *produces* a filing package** | Clear split: `src/` or programs + specs + tests **vs** `deliverables/` or `m5/` |

TROPIC is meaning #2. Presenting it as if the whole GitHub clone *is* the filing package is why it feels noisy.

---

## 2. How modern pharma presents *development* repos (R Consortium / PHUSE)

### 2.1 R Consortium Submissions Pilots (public gold standard for “how we show work”)

Public pilots (Pilot 1–5 pattern) typically use **two surfaces**:

1. **Development repository**  
   - Code that *builds* ADaM/TLFs  
   - `renv.lock` / environment  
   - ADRG content as Rmd/source sometimes  
   - README focused on **how to reproduce**  
   - Tests / CI  

2. **Submission package tree (`m5/`)**  
   - What was (or could be) sent through the eCTD portal  
   - XPT + define + programs + guides  

Pilot 3-style structure (publicly documented) puts the **reviewer-facing** content under:

```text
m5/datasets/<study>/tabulations/sdtm/   # xpt + define + blankcrf
m5/datasets/<study>/analysis/adam/
    datasets/   # xpt + define + adrg
    programs/   # .r / .sas + lockfile
```

**Not** under a 78-file `platform/` dump at the same cognitive level as `adsl.xpt`.

### 2.2 PHUSE / industry Git practice

PHUSE materials on Git for statistical programming emphasize:

- Version control of **code and controlled docs**, not patient data  
- Branching for development  
- Clear separation of **source code** vs **generated outputs**  
- Avoid treating the entire evidence warehouse as “the product”

Generated QC JSONs belong in **artifacts / CI outputs / run records**, not as the primary story in README.

### 2.3 Sponsor internal trees (typical, not public)

A serious sponsor study area often looks more like:

```text
study/
  documents/     # protocol, SAP, shells (controlled)
  sdtm/          # or tabulations
  adam/
  tfl/
  programs/
    sdtm/
    adam/
    tfl/
  qc/            # independent programs + logs (restricted)
  deliverables/  # what goes to eCTD / transfer
  utilities/     # shared macros (optional)
```

Notice:

- **Few top-level folders**  
- **No** “00_governance through 08_submission” **plus** `platform` **plus** `docs` **plus** `config` **plus** 20 regenerated reports all shouting at once  
- QC logs live under **qc/**, not next to README as peer “products”

---

## 3. Diagnosis: where TROPIC creates noise (honest)

### 3.1 Inventory (current tree signals)

Approximate file counts (excluding `.git` / `renv`):

| Area | ~Files | Presentation problem |
|---|---:|---|
| `08_submission_package/` | ~188 | OK if this is the *star*; currently competes with everything else |
| `04_analysis_datasets/` | ~159 | Mix of programs + build outputs + Dataset-JSON |
| `platform/` | ~112 / ~78 listed | Feels like “the whole company CI dump” at repo root |
| Status/report JSON | **200+** | Warehouse, not portfolio face |
| `docs/` | ~24 | Many *generated* control reports look like hand-authored narrative |

### 3.2 Noise types

| Noise type | Examples in TROPIC | Industry fix |
|---|---|---|
| **Generated evidence at root of attention** | `*_status.json`, dozens of `docs/*_REPORT.md` regenerated every run | Put under `artifacts/` or `06_qc_evidence/runs/` and **gitignore** volatile copies; keep only *templates* + *last sealed run* |
| **Platform sprawl** | Orchestrator + 15 report builders + conformance + ODA broker in one flat `platform/` | `platform/{orchestrator,qc,packaging,conformance}/` **or** hide platform behind one entrypoint doc |
| **Dual numbering schemes** | Evidence-chain `00_`…`08_` *and* historical program names *and* eCTD paths | One **presentation map** in README: “Open these 5 paths first” |
| **Control plane oversharing** | YAML for every control + board + strategy all in `config/` | Fine for engineers; **not** first slide for reviewers |
| **Truth vs presentation** | DEMO02, Shiny, USDM, ARS, Dataset-JSON all visible | Label **exploratory** or move to `labs/` / `optional/` |
| **Docs that are really build outputs** | Delivery dashboard, gate maps, TFL index markdown | Generate into `artifacts/reports/`; link from one index |

### 3.3 What is *not* noise (protect these)

These are **career-grade** if easy to find:

1. README with **Path A claim** + how to open the package  
2. `08_submission_package/m5/` (or clear pointer)  
3. Production + validation programs (SAS/R)  
4. ADRG / SDRG / BDRG  
5. ADaM spec + define  
6. One release note / one product claim  
7. How to verify (`scripts/verify_release.py`)  

Everything else is **supporting factory**.

---

## 4. The dual-surface presentation model (what you should adopt)

### 4.1 Face of the repository (first 30 seconds)

A serious presentation root looks like this **conceptually**:

```text
README.md                 # 1 screen: claim, open these paths, how to verify
PRODUCT_CLAIM.md          # or docs/PRODUCT_CLAIM.md — linked first
SUBMISSION_PACKAGE/       # or 08_submission_package/ — THE deliverable
  m5/                     # FDA-shaped
  README.md               # how this package is built / limitations
PROGRAMS/                 # or clearly under analysis datasets
  sas/ r/
docs/
  RELEASE_NOTE_*.md       # one sealed narrative
  guides/                 # ADRG SDRG BDRG only (or symlink)
platform/                 # “build system — engineers only”
config/                   # “control plane — engineers only”
qc/ or 06_qc_evidence/    # “run evidence — QC only”
```

**Rule:** If a folder is not needed to understand the study package, it must not look equal to `m5/` in the README.

### 4.2 Submission package face (what you demo to “FDA mode”)

Open **only**:

```text
08_submission_package/m5/datasets/<study>/
  tabulations/sdtm/     # define + xpt (+ sdrg, blankcrf)
  analysis/adam/        # define + xpt + adrg + programs
  bimo/                 # if claimed
08_submission_package/m5/53-clin-stud-rep/.../figures|tables
```

Say:  
“This is the review surface. The rest of the Git repo is the factory that produces and seals it.”

### 4.3 Development face (what you demo to “engineering mode”)

```text
config/study_manifest.yaml   # DAG truth
platform/cibuild.py          # entrypoint
scripts/verify_release.py    # seal recheck
04_analysis_datasets/programs/
tests/
```

Say:  
“This is how the factory is controlled.”

### 4.4 QC face (what you demo to “validation mode”)

```text
06_qc_evidence/
  reconciliation/
  gates/
  audit/findings_register.csv
docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md
```

Say:  
“This is how we challenge and disposition.”

**Never** mix the three faces in one breath without labeling them.

---

## 5. Industry-aligned README “above the fold” (template)

Serious repos lead with **≤15 lines** of orientation:

```markdown
# TROPIC — Controlled biometrics demonstration (Path A)

**Not a regulatory filing.** Real MP SDTM (not in git) + synthetic CbzP for TFLs only.

## Open first
1. Product claim → docs/PRODUCT_CLAIM.md
2. Submission-style package → 08_submission_package/m5/
3. Reviewer guides → 07_reviewer_explanation/guides/
4. Current release seal → docs/RELEASE_NOTE_v0.2.2-portfolio.md
5. Verify machine grades → python3 scripts/verify_release.py

## Factory (engineers)
- config/ · platform/ · 04_analysis_datasets/programs/

## QC evidence
- 06_qc_evidence/ · docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md
```

If README still reads like a 400-line architecture blog, **presentation failed** even if engineering is strong.

---

## 6. What “clean presentation” is *not*

| Temptation | Why it fails |
|---|---|
| More numbered folders | Adds cognitive load without reviewer value |
| More status JSON in `m5/` | Contaminates submission surface (you already removed QC JSON from Module 5 — correct) |
| One giant WORKSTREAM + PLATFORM + EVIDENCE at equal weight | Looks like a startup monorepo, not a study package |
| Regenerating 15 markdown reports into `docs/` as peers of ADRG | Blurs controlled docs vs build logs |
| Claiming “this GitHub tree *is* the eCTD” | False; eCTD is a sequence with DTD/STF rules |

---

## 7. Recommended presentation architecture for TROPIC (Path A)

### 7.1 Keep (evidence-chain is fine *if* README demotes factory)

The `00_governance` … `08_submission_package` chain is a valid **internal evidence model**.  
It is **not** the FDA tree. FDA tree lives **inside** `08_submission_package/`.

### 7.2 Presentation layers (target mental model)

```text
LAYER 0 — Claim & entry
  README.md
  docs/PRODUCT_CLAIM.md
  docs/RELEASE_NOTE_*.md

LAYER 1 — Review surface (submission-style)
  08_submission_package/m5/
  07_reviewer_explanation/guides/{ADRG,SDRG,BDRG}.md

LAYER 2 — Analysis truth
  04_analysis_datasets/programs/{sas,r}/
  04_analysis_datasets/adam/          # or only via package if you want stricter
  03_metadata/{adam,define}/
  05_outputs/tfl/

LAYER 3 — Factory
  config/
  platform/     # ideally subfoldered later
  scripts/

LAYER 4 — QC warehouse
  06_qc_evidence/
  (generated reports → 06_qc_evidence/reports/ or gitignored artifacts/)
```

### 7.3 Immediate de-noise actions (high ROI, no science rewrite)

| Priority | Action | Effect |
|---:|---|---|
| 1 | Rewrite README “Open first” to Layers 0–1 only | Instant professionalism |
| 2 | Add `08_submission_package/README.md` that *is* the package tour | FDA-mode demo |
| 3 | Move or generate control reports only under `06_qc_evidence/reports/` | ADRG not crowded by dashboards |
| 4 | Split `platform/` into `platform/orchestrator`, `platform/packaging`, `platform/qc_tools` | Reduces “78 files of equal noise” |
| 5 | Gitignore volatile status JSON except sealed snapshots under `platform/evidence/` or `06_qc_evidence/seals/` | Clean diffs, clean clone story |
| 6 | One `docs/INDEX.md` with three tours: Reviewer / Engineer / QC | Stops dump-scrolling |

### 7.4 What to say in interviews when they open GitHub

> “There are two views. The **submission-style package** is under `08_submission_package/m5/`—that’s what a reviewer would navigate. The rest is the **controlled factory**: dual-language ADaM, admiral, gates, and seals. Patient data aren’t in git. Comparative CbzP is synthetic and disclosed. This is Path A—a controlled demonstration, not a filing.”

That sentence alone is worth more than another YAML file.

---

## 8. Comparison table: noisy monorepo vs professional dual surface

| Dimension | Noisy (current risk) | Professional presentation |
|---|---|---|
| First click | Random status JSON / long README | Package tree or claim doc |
| Reviewer path | Buried under platform + docs reports | `m5/datasets/...` obvious |
| Engineer path | Mixed with package | `config/` + `platform/cibuild.py` |
| QC path | Scattered status files | One evidence root + residual memo |
| Generated artifacts | Committed as peers of ADRG | Sealed snapshot or gitignored |
| Exploratory tech | USDM/ARS/Shiny at same level as ADSL | `labs/` or labeled optional |
| Success metric | “Many green JSON” | “Can explain package in 5 minutes without lying” |

---

## 9. Research conclusions (actionable)

1. **FDA presentation ≠ Git architecture.** FDA cares about Module 5 co-location of data + define + guides + programs.  
2. **Industry public gold standard** (R Consortium pilots) separates **dev repo** from **`m5/` package**.  
3. **TROPIC’s evidence-chain folders are a good internal model** but must be **narratively demoted** relative to `08_submission_package/`.  
4. **Noise is mostly presentation and generated evidence**, not lack of substance.  
5. **Next work should be presentation hygiene**, not more control YAML—unless a control is broken.  
6. **Career risk** is inverse to clarity: a clean `m5/` + honest claim beats a brilliant but noisy monorepo.

---

## 10. Recommended next engineering (presentation-first)

Do these in order; stop when the 30-second test passes (“stranger finds package + claim without help”):

1. **README above-the-fold rewrite** (Layer 0). — **DONE 2026-07-09** (root `README.md` dual-surface + Open first).  
2. **`08_submission_package/README.md`** package tour + Path A limitations. — **DONE 2026-07-09**.  
3. **`docs/INDEX.md`** with Reviewer / Engineer / QC tours. — **DONE 2026-07-09**.  
4. **Park generated reports** under `06_qc_evidence/reports/` (or stop committing non-seal reports). — pending (do not migrate folders until 30s test is accepted).  
5. **Subfolder `platform/`** by responsibility (orchestrator / packaging / reports). — pending (factory hygiene only after face is stable).  
6. Only then: full ODA re-run if package face is stable.

**30-second test (self-check):** stranger opens root README → finds PRODUCT_CLAIM → finds `08_submission_package/m5/` → finds three tours in `docs/INDEX.md` without help.

---

## 11. References (primary)

- FDA, *Study Data Technical Conformance Guide* (current published version via FDA Study Data standards pages) — Module 5 organization, define co-location, reviewer guides.  
- FDA eCTD technical guidance / Module 5 study data folder conventions.  
- R Consortium Submissions Working Group pilots (public `m5/` + development repo pattern).  
- PHUSE papers on eCTD Module 5 study data placement and Git for statistical programming.  
- CDISC ADaM / Define-XML roles: machine metadata + human ADRG (complementary, not interchangeable).

---

## 12. Bottom line

**You do not present a submission by showing `platform/`.**  
You present a submission by showing **`m5/`** (data, define, guides, programs) and only then, if asked, the **factory that sealed it**.

The repo feels noisy because the factory and the warehouse are currently as loud as the package.  
Fix presentation hierarchy—not by abandoning the architecture, but by **making the package the face and the factory the engine room**.

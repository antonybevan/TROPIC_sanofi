# Bioresearch Monitoring (BIMO) Data Reviewer's Guide (BDRG)

| Field | Value |
|---|---|
| **Document** | BIMO Data Reviewer's Guide (BDRG) |
| **Study** | TROPIC / EFC6193 / XRP6258 · NCT00417079 |
| **Cohort in clinsite** | Real Mitoxantrone (MP) de-identified arm only (N=371 subjects → site roll-up) |
| **Standard** | FDA *Bioresearch Monitoring Technical Conformance Guide* (clinsite pattern; Appendix 3 **subset**) |
| **Document version** | 1.3 (audit closure / portfolio release) |
| **Effective** | 2026-08-05 |
| **Supersedes** | BDRG v1.2 from the `v0.2.0-portfolio` release (which superseded the `v0.1.0-demo-rc.1` baseline) |
| **Product claim** | Controlled clinical-submission simulation; not a regulatory submission |

---

## 0. What this package is / is not (read first)

| This package **is** | This package **is not** |
|---|---|
| Site-level roll-up (`clinsite`) for **BIMO-style** review practice | Full BIMO TCG Appendix-3 ~39-variable production clinsite |
| Dual-language (SAS/R) recon of the delivered clinsite subset under genuine SAS when seals say `oda`/`local` | Organizational GxP double programming |
| Honest omissions where PDS has no PI/CTMS/DV data | Real investigator identity / financial disclosure / full DV counts |
| Controlled simulation deliverable under `m5/.../bimo/` | FDA filing BIMO package |

**Binding claim:** [`docs/PRODUCT_CLAIM.md`](../../docs/PRODUCT_CLAIM.md)
**Residuals:** [`docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md`](../../docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md)
**Current controlled release:** tag `v0.3.0-clinical-simulation` · [`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`](../../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md) · `python3 scripts/verify_release.py`
**Package path:** [`08_submission_package/m5/datasets/tropic/bimo/`](../../08_submission_package/m5/datasets/tropic/bimo/)
**Related guides:** [`ADRG.md`](ADRG.md) · [`SDRG.md`](SDRG.md) · [`TRACEABILITY_MATRIX.md`](TRACEABILITY_MATRIX.md)

---

## 1. Purpose

The summary-level clinical-site dataset (`clinsite`) supports the FDA Office of Scientific
Investigations (OSI) / BIMO **review pattern**. It aggregates subject-level enrollment,
disposition, and safety experience **to the study-site level** so reviewers can prioritise
sites for inspection. It is **not** an ADaM analysis dataset and is **not** in the ADaM
`define.xml`; per BIMO TCG practice it is delivered with its own guide (this BDRG) under
`08_submission_package/m5/datasets/tropic/bimo/`.

Structure follows PHUSE *BIMO Data Reviewer's Guide Completion Guidelines* as far as this
source honestly allows.

---

## 2. Honest scope vs full BIMO TCG `clinsite`

> [!IMPORTANT]
> Full BIMO TCG Appendix-3 specifies **~39 site-level variables** (investigator identity/
> address/contact, country, screen/randomized/treated/completed/discontinued counts,
> protocol-deviation counts, primary-endpoint contribution, financial-disclosure flags, etc.).
> This portfolio implements the **subset honestly derivable** from the public, de-identified
> TROPIC release (Project Data Sphere). It does **not** fabricate variables the source cannot
> support. **Illustrative BIMO subset**, not a submission-complete clinsite.

| Omitted BIMO TCG content | Why not populated |
|---|---|
| Investigator name / address / phone / email | PDS has **no** PI identity. `INVNAM` is a labelled **synthetic placeholder** (`PI_<siteid>`), never a real investigator. |
| `COUNTRY` / site geography | Not in de-identified release. |
| Important / significant protocol deviations | No SDTM `DV` domain in public release. |
| Screened / completed / discontinued counts | Disposition reasons not separable into screen-fail vs completion in this release. |
| Financial disclosure | Not applicable to public secondary-use data. |

A production BIMO package would populate Appendix-3 from sponsor CTMS/operational data. The
**transferable skill** here is subject → site roll-up joined to populations and safety, with
dual-language recon.

---

## 3. Variables delivered (`clinsite`)

**One row per study site** (69 sites in the current MP-only build).

| Variable | Label | Derivation |
|---|---|---|
| `STUDYID` | Study Identifier | ADSL `STUDYID` |
| `SITEID` | Study Site Identifier | ADSL `SITEID` (group key) |
| `INVNAM` | Principal Investigator (**SYNTHETIC** placeholder) | `"PI_" \|\| SITEID` — see §2 |
| `N_RAND` | Number of Subjects Randomized | `COUNT(DISTINCT USUBJID)` per site |
| `N_SAF` | Number of Subjects Treated (Safety) | `SAFFL='Y'` per site |
| `N_ITT` | Number of Subjects in ITT | `ITTFL='Y'` per site |
| `N_PPROT` | Number of Subjects in Per-Protocol | `PPROTFL='Y'` per site |
| `N_DEATH` | Number of Subjects Who Died | `DTHFL='Y'` per site |
| `N_SAE` | Subjects with a Serious AE | distinct `USUBJID` with ADAE `AESER='Y'`, via ADSL site |
| `N_TEAE` | Subjects with a TEAE | distinct `USUBJID` with ADAE `TRTEMFL='Y'`, via ADSL site |

### 3.1 Population note (ICH E9 + controlled source)

Randomized, Safety, ITT, and Per-Protocol are **distinct analysis-set concepts**. ITT is
reported as `N_ITT` and is **never** relabelled “Efficacy Population.”

In this de-identified MP-only release, population flags on ADSL are **source-inherited and
non-discriminating** (all 371 subjects `ITTFL = SAFFL = PPROTFL = 'Y'` — see ADRG §5.4).
Therefore `N_RAND` / `N_SAF` / `N_ITT` / `N_PPROT` **coincide per site**. Inspection signal
lives in the safety roll-ups (`N_DEATH`, `N_SAE`, `N_TEAE`), which vary by site.

**Programs:**

| Track | Program | Output (local build) |
|---|---|---|
| Production (SAS) | `04_analysis_datasets/programs/sas/B_bimo_generation.sas` | `clinsite_prod.xpt` |
| Validation (R) | `04_analysis_datasets/programs/r/v_bimo_validation.R` | `clinsite_v.xpt` |
| Package copy | assembled by `package_ectd.py` | `m5/.../bimo/datasets/clinsite.xpt` (local; not in git) |

---

## 4. Dual-language reconciliation evidence

`clinsite` is produced on both tracks and reconciled on keys `(STUDYID, SITEID)` by
`06_qc_evidence/reconciliation/cross_lang_audit.R` (one of eight recon domains).

| Claim | Honesty |
|---|---|
| Independent SAS vs R **implementations** | Yes (different language/structure) |
| Organizational two-programmer GxP | **No** — single author (PRODUCT_CLAIM non-claim) |
| Meaningful zero-diff under `sim` mode | **No** — tautological byte-copy |
| Meaningful recon under `oda` / `local` | Yes — check `platform/pipeline_health.json` |

Seals / residual memo: [`WS5_KNOWN_DIFFERENCES_MEMO.md`](../../docs/workstreams/WS5_KNOWN_DIFFERENCES_MEMO.md).

---

## 5. Delivery location (review face)

```text
08_submission_package/m5/datasets/tropic/bimo/datasets/
  clinsite.xpt    # local full package only (patient-derived — not in git)
  bdrg.pdf        # rendered guide when packaged
```

Markdown source of truth for narrative: this file.

---

## 6. References

- FDA, *Bioresearch Monitoring Technical Conformance Guide* (clinsite, Appendix 3).
- PHUSE, *BIMO Data Reviewer's Guide (BDRG) Completion Guidelines*.
- PHUSE SA01, *Development of a standard BIMO process to create the clinsite dataset*.
- ICH E9, *Statistical Principles for Clinical Trials* (analysis-set definitions).
- Binding claim: `docs/PRODUCT_CLAIM.md`

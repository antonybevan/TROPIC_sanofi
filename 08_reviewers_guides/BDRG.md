# Bioresearch Monitoring (BIMO) Data Reviewer's Guide (BDRG)

**Study Name:** TROPIC Re-Analysis (Study EFC6193 / XRP6258, NCT00417079)
**Compound:** Mitoxantrone (MP) control arm — real, de-identified cohort (N=371)
**Standard:** FDA *Bioresearch Monitoring Technical Conformance Guide* (clinsite, Appendix 3)
**Created:** 2026-06-16

---

## 1. Purpose

The summary-level clinical-site dataset (`clinsite`) supports the FDA Office of Scientific
Investigations (OSI) / BIMO program. It aggregates subject-level enrollment, disposition, and
safety experience **to the study-site level** so that reviewers can prioritise clinical sites for
on-site inspection. It is **not** an analysis dataset and is **not** part of the ADaM define.xml;
per the BIMO Technical Conformance Guide it is delivered with its own data-definition documentation
(this BDRG) under `m5/datasets/tropic/bimo/`.

This guide follows the structure recommended by the PHUSE *BIMO Data Reviewer's Guide Completion
Guidelines*.

## 2. Honest Scope vs. the Full BIMO TCG `clinsite` Specification

> [!IMPORTANT]
> The full BIMO TCG Appendix-3 `clinsite` structure specifies **~39 site-level variables**
> (investigator identity/address/contact, country, screen/randomized/treated/completed/discontinued
> counts, protocol-deviation counts, primary-endpoint contribution, financial-disclosure flags, etc.).
> This portfolio implements the **subset that is HONESTLY DERIVABLE** from the public, de-identified
> TROPIC release (Project Data Sphere). It deliberately does **not** fabricate variables the source
> cannot support. This is an *illustrative BIMO subset*, not a submission-complete clinsite.

**Variables intentionally NOT populated, and why:**

| Omitted BIMO TCG content | Reason it is not derivable from this source |
|---|---|
| Investigator name / address / phone / email | The de-identified PDS release carries **no** principal-investigator identity. `INVNAM` below is a clearly-labelled **synthetic placeholder** (`PI_<siteid>`), never a real investigator. |
| `COUNTRY` / site geography | Not present in the de-identified release. |
| Important / significant protocol deviations | No SDTM `DV` (protocol deviations) domain is available in the public release. |
| Screened / completed / discontinued counts | DS disposition reasons are not separable into screen-fail vs. completion vs. discontinuation in the de-identified release. |
| Financial disclosure | Not applicable to a public secondary-use dataset. |

A production BIMO package would populate the full Appendix-3 structure from the sponsor's
operational/CTMS data; the derivation **pattern** demonstrated here (subject-level → site-level
roll-up, joined across populations and safety) is the transferable skill.

## 3. Variables Delivered (`clinsite`, one row per study site; 69 sites)

| Variable | Label | Derivation |
|---|---|---|
| `STUDYID` | Study Identifier | ADSL `STUDYID` |
| `SITEID` | Study Site Identifier | ADSL `SITEID` (group key) |
| `INVNAM` | Principal Investigator (**SYNTHETIC** placeholder) | `"PI_" || SITEID` — see §2 |
| `N_RAND` | Number of Subjects Randomized | `COUNT(DISTINCT USUBJID)` per site |
| `N_SAF` | Number of Subjects Treated (Safety Population) | `SAFFL='Y'` per site |
| `N_ITT` | Number of Subjects in ITT Population | `ITTFL='Y'` per site |
| `N_PPROT` | Number of Subjects in Per-Protocol Population | `PPROTFL='Y'` per site |
| `N_DEATH` | Number of Subjects Who Died | `DTHFL='Y'` per site |
| `N_SAE` | Number of Subjects with a Serious AE | distinct `USUBJID` with ADAE `AESER='Y'`, routed to site via ADSL |
| `N_TEAE` | Number of Subjects with a TEAE | distinct `USUBJID` with ADAE `TRTEMFL='Y'`, routed to site via ADSL |

> **Population note (ICH E9):** Randomized, Safety (treated), ITT, and Per-Protocol are **distinct
> analysis sets**. ITT is reported as `N_ITT` and is **never** relabelled "Efficacy Population"
> (a prior version mislabelled the ITT count as efficacy — corrected). In this de-identified
> single-arm release all subjects are randomized, treated, ITT, and per-protocol, so those four
> counts coincide per site; the safety counts (`N_DEATH`, `N_SAE`, `N_TEAE`) vary by site and carry
> the inspection-prioritisation signal.

## 4. Dual-Programming / Reconciliation

`clinsite` is double-programmed like the ADaM domains: produced by SAS
(`02_production_sas/B_bimo_generation.sas` → `clinsite_prod.xpt`) and independently by R
(`03_validation_r/v_bimo_validation.R` → `clinsite_v.xpt`), then reconciled cell-by-cell on the
`(STUDYID, SITEID)` key by `05_reconciliation/cross_lang_audit.R`. As with all domains, a genuine
SAS↔R reconciliation requires a run executed against a real SAS engine
(`sas_execution_mode = oda/local` in `06_telemetry/pipeline_health.json`); a `sim`-mode byte-copy
reconciliation is tautological.

## 5. References

- FDA, *Bioresearch Monitoring Technical Conformance Guide* (clinsite, Appendix 3).
- PHUSE, *BIMO Data Reviewer's Guide (BDRG) Completion Guidelines*.
- PHUSE SA01, *Development of a standard BIMO process to create the clinsite dataset*.
- ICH E9, *Statistical Principles for Clinical Trials* (analysis-set definitions).

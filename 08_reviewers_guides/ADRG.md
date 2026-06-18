# Analysis Data Reviewer's Guide (ADRG)

**Study Name:** TROPIC Re-Analysis  
**Compound:** Cabazitaxel (CbzP) vs. Mitoxantrone (MP)  
**Standard:** CDISC ADaMIG v1.3 / OCCDS v1.0 (+ custom episode-merging extension)  
**Created:** 2026-05-23  

---

## 1. Study & Re-Analysis Overview
The **TROPIC Phase III Trial (NCT00417079)** evaluated the efficacy and safety of cabazitaxel (25 mg/m² IV q3w) + prednisone against mitoxantrone (12 mg/m² IV q3w) + prednisone in metastatic castration-resistant prostate cancer (mCRPC) previously treated with docetaxel. 

In the **published** trial, cabazitaxel carried a profound safety burden: ~82% Grade 3/4 neutropenia and ~8% febrile neutropenia (de Bono et al., Lancet 2010). *(Note: the synthetic CbzP arm in this repository realises ~86.5% (321/371) Grade 3/4 ANC nadir per the generated lab data — see `09_tfl/output/tables/T-21-Lab_Shift_Tables.txt`; it approximates, but does not exactly reproduce, the published rate.)*

This **demonstration** rebuilds a synthetic comparator to retrospectively exercise modeling of the relationship between relative dose intensity (RDI), G-CSF prophylaxis, and absolute neutrophil count (ANC) nadir. This characterization supports the **FDA Project Optimus dose-optimization framework** by analyzing recovery kinetics and safety margins.

---

## 2. Key Derivations & Episode Merging
### Myeloid/Neutropenic Episode Merging (ADAE)
Under the published CDISC OCCDS v1.0 structure, separate adverse event records (e.g. repeated reports of neutropenia) artificially inflate the event count denominator. We therefore apply a **pre-specified custom 3-day continuous episode-merging extension** (this merging rule is a TROPIC analysis convention — it is *not* part of the published OCCDS v1.0; no CDISC "OCCDS v1.1" standard exists):
1. Within a patient and Customized Query 02 (`CQ02NAM = 'HEMATOLOGIC irAE'`), neutropenic events with a start date within 3 days of the previous event's end date are merged.
2. The continuous start (`CIAESDT`), end (`CIAEEDT`), and duration (`CIAEDUR`) are calculated across the merged sequence.
3. The occurrence flag `AEOCCFL` is set to `'Y'` only for the first record in the merged sequence, establishing an accurate, non-inflated safety denominator.

---

## 3. Project Optimus Modeling Parameters (ADLB)
To support dose-toxicity modeling, two continuous parameters were derived per cycle:
* **`ANCNADIR` (PARAMCD: ANCNADIR):** The absolute minimum ANC value recorded during the primary nadir window (Day 4 to Day 24).
* **`ANCRECDY` (PARAMCD: ANCRECDY):** The number of days from the nadir date to the first post-nadir assessment where ANC >= 1.5 x10³/μL, defining the patient-specific recovery latency.
* **Exposure Linkage:** RDI and continuous nadir bounds are linked at the subject-cycle level to construct fitted LOESS exposure-response curves (`F-17-1`).

---

## 4. Efficacy Censoring Rules (ADTTE)
For Progression-Free Survival (PFS), progression is defined as radiological progression (RECIST v1.0 — the trial-era standard per SAP v3.0 §5.3 and de Bono 2010), PSA progression (PCWG2-era criteria), bone scan progression, or death.
* **Censoring Hierarchy:**
  1. If a patient starts a new systemic anti-cancer therapy (`NACTDT`) prior to a documented PFS event, the time-to-event is censored at **`NACTDT - 1 day`** (`CNSDTDSC = 'NEW ANTI-CANCER THERAPY START'`).
  2. If no event or NACT occurs, the time-to-event is censored at the last evaluable tumor assessment or last known alive date.

* **Other Time-to-Event Parameters Censoring Rules (VAL-06):**
  * **Overall Survival (OS) (PARAMCD: OS):** Start date is `RANDDT`. Event is death (`DTHFL = 'Y'`). Censored at last known alive date (`LSTALVDT`).
  * **Time to First Serious AE (TTSAE) (PARAMCD: TTSAE):** Start date is `TRTSDT`. Event is first treatment-emergent Serious AE. Censored at last known alive date (`LSTALVDT`, `CNSDTDSC = 'LAST KNOWN ALIVE DATE'`). *(Renamed from the prior `TTOS` mnemonic, which was confusable with `OS`; the parameter is unchanged.)*
  * **Time to PSA Progression (TTPSA) (PARAMCD: TTPSA):** Start date is `TRTSDT`. Event is PSA progression (`PARAMCD = 'PSPROG' & AVAL = 1.0`). Censored at last PSA assessment date or last known alive date.
  * **Time to Tumor Progression (TTUMOR) (PARAMCD: TTUMOR):** Start date is `TRTSDT`. Event is the first radiographic PD across the enriched ADRS — integrated RECIST v1.0 `OVRLRESP = 'PD'` (now incorporating new-lesion and non-target progression, §4A) **or** confirmed PCWG3 bone progression (`BSGRESP = 'PROGRESSION'`). Censored at last tumor assessment date (`last_tumor_dt`) or last known alive date. The consumer logic in `A_adtte_generation.sas` (`work.pd_dates`) was already written to take the earliest of `OVRLRESP='PD'`, `BSGRESP='PROGRESSION'`, `PSPROG='Y'`; the ADRS enrichment now supplies the previously-missing `BSGRESP` and the richer `OVRLRESP`. **Note: Restrictive analysis population is the measurable disease subpopulation (MEASDISF = 'Y'); SAP v3.0 §3.4 cites 204 MP / 201 CbzP measurable at baseline. The real MP arm yields N=203 here; the synthetic CbzP arm carries N=179 by reconstruction.**

### 4.1 Time-to-Event Analysis Conventions (audit MO-4 / MO-5)
* **Duration convention.** `AVAL = (event/censor date − time origin) + 1` day, so an event on the origin date contributes 1 day (not 0); applied uniformly across all parameters.
* **Time origin per parameter is explicit and deliberate.** OS and PFS are anchored at randomization (`RANDDT`, ITT); TTSAE, TTPSA and TTUMOR are anchored at first dose (`TRTSDT`, safety). Efficacy ITT endpoints run from randomization, safety/treatment endpoints from exposure; the origin is recorded on every record via `STARTDT`.
* **Negative durations are surfaced, not silently masked (audit MO-4).** A small number of source records carry an event/censor date marginally before the time origin — an artefact of the week-precision source dates (±3.5 days; SDRG §2). They are floored to 1 day so the record stays in the risk set, **and** both tracks emit an explicit warning (SAS `putlog`, R `warning()`) identifying the subject so the anomaly is investigable rather than hidden.

---

## 4A. Response Endpoint Derivations (ADRS) — Traceability (audit F-8)

To pre-empt reviewer challenge on the response rates, the exact derivation of the response endpoints (as implemented in the SAS/R ADRS track and consumed by `tfl_generation.R`) is:

* **Overall Response (`PARAMCD = OVRLRESP`) — integrated RECIST v1.0 timepoint response.** The per-visit overall response is the standard RECIST integration of **three** components, all sourced from `ls`: (1) **target** lesions (sum-of-diameters vs nadir/baseline, thresholds `RECIST_PD_PCT/PR_PCT/PD_ABS`); (2) **non-target** lesion status (`LSCAT='NON-TARGET'`, worst-per-visit collapse of `LSSTRESC`); (3) **new lesions** (`LSTESTCD='NEWLES'`). Override rules: **any new lesion ⇒ PD**; **non-target unequivocal PD ⇒ PD** (even with target CR/PR); target CR with a non-CR non-target ⇒ PR. The derivation is *defensive* — when non-target / new-lesion rows are absent for a subject-visit it reproduces the prior target-only result. The label remains "Overall Response per RECIST v1.0": new-lesion and non-target integration are part of RECIST 1.0; this is a **correctness fix**, not a version change. (Earlier revisions derived `OVRLRESP` from target SOD only and discarded the new-lesion and non-target signal that is present in the source.)
* **Objective Response Rate (ORR, `PARAMCD = OBJRESP`):** Responder = a **confirmed** CR or PR per RECIST v1.0 (`AVALC = 'Y'`). Confirmation (audit M-2) requires a subsequent CR/PR at least `RECIST_CONFIRM_DAYS` (28) days after the first (CR confirmed by CR; PR confirmed by CR or PR), evaluated on the lesion-derived RECIST timepoints that both the SAS and R tracks compute identically. **Denominator = ITT population restricted to patients with measurable disease at baseline** (`MEASDISF == 'Y'`), per SAP v3.0 §3.4 / §5.3 and the publication (de Bono 2010). The real MP arm yields **13/203 = 6.4%** on the measurable subpopulation.
  * **Reconciliation to the publication:** The published MP ORR was **4.4%**. With confirmation enforced and overall response now integrated across target + non-target + new lesions (§4A), the pipeline yields **6.4%** on the measurable-disease denominator and **3.7%** (13/351) on the response-evaluable denominator (T-11-8b) — both close to the published rate. The prior best-of-any-assessment logic, with no confirmation, overstated this roughly four-fold (18.2%); enforcing the RECIST confirmation rule removed that overstatement. The small residual reflects lesion-sum-derived RECIST vs investigator adjudication and the ±3.5-day source date precision, not a calculation error.
* **PSA Response (`PARAMCD = PSARESP`):** Responder = ≥50% confirmed decline in PSA from baseline (PCWG3) (`AVALC = 'Y'`); denominator = subjects with a baseline and ≥1 post-baseline PSA. MP arm: **69/371 = 18.6%**.
* **Bone Scan Progression (`PARAMCD = BSGRESP`) — PCWG3 2+2 rule (methodological demonstration).** Bone is the dominant mCRPC metastatic site and is largely non-measurable by RECIST, so progression is tracked separately from new bone lesions (`LSTESTCD='NEWLES' & LSLOC='BONE'`, scintigraphy). A first post-baseline scan with `≥ BONE_PROG_MIN_NEW` (2) new bone lesions is **PDu** (`AVALC='PROGRESSION UNCONFIRMED'`); it is **confirmed** (`AVALC='PROGRESSION'`, the only state that feeds TTUMOR) when a later scan adds `≥ BONE_PROG_CONFIRM_NEW` (2) further new bone lesions, with the PD date backdated to the PDu scan; otherwise `AVALC='NO PROGRESSION'`. This rule (Scher 2016, PCWG3) post-dates the 2010 trial and is **not in the trial-era SAP** — it is a clearly-labelled methodological demonstration, consistent with how `PSPROG` already applies PCWG3 here. On the real MP arm the strict 2+2 is **stringent relative to the source granularity**: **5 subjects reach PDu, 0 are confirmed** — reported honestly rather than tuning the thresholds to manufacture events.

All response counts/percentages are emitted by `09_tfl/tfl_generation.R` to `09_tfl/output/tables/T-11-Efficacy_Tables.txt` (single source of truth).

---

## 5. Missing Data Handling (ADaMIG v1.3 §4.4 Compliance)

### 5.1 Baseline Laboratory Covariates — Schema Placeholders (not used in any model)
Several baseline laboratory variables are carried on ADSL to satisfy the ADaM schema, but some are not present in the public SDTM release. Where a value was unavailable, a published population-median constant is stored:

| Variable | Stored Value | Units | Source patient-level data available? |
|----------|--------------|-------|--------------------------------------|
| `PSABL` | 110.0 | ng/mL | Yes (real, per subject) — constant used only as fallback |
| `ALPBL` | 140.0 | U/L | Yes (real, per subject) — constant used only as fallback |
| `HGBBL` | 11.5 | g/dL | Yes (real, per subject) — constant used only as fallback |
| `ALBBL` | 38.0 | g/L | **No** — single constant for all subjects (placeholder) |
| `LDHBL` | 220.0 | U/L | **No** — single constant for all subjects (placeholder) |

> [!IMPORTANT]
> **Correction (audit F-9):** These imputed/constant covariates are **not used as covariates or stratification factors in any efficacy model.** The primary and secondary Cox / log-rank analyses stratify **only on `ECOGBL` and `MEASDISF`** (see `09_tfl/tfl_generation.R`, `compute_tte_stats()` → `strata(ECOGBL, MEASDISF)`). Albumin (`ALBBL`) and LDH (`LDHBL`) were never collected in the public MP SDTM release; a single constant column conveys no subject-level information and a degenerate (constant) covariate would in any case contribute nothing to a model. They are retained purely as schema placeholders and should be read as "not available," not as analysis inputs.

**Imputation method and flags (audit F-5).** The method is a single **published population-median constant** per variable (values in `study_config.yaml`); it is *not* model-based or multiple imputation, and is applied only where the per-subject value is absent. Every imputed/placeholder baseline carries a companion **imputation flag** — `ECOGBLIF`, `PSABLIF`, `ALPBLIF`, `HGBBLIF`, `ALBBLIF`, `LDHBLIF` (= `'Y'` when imputed) — computed identically in SAS (`case when missing(...)`) and R (`is.na(...)` pre-coalesce), so a reviewer can isolate every imputed cell. `ALBBL`/`LDHBL` (a single constant for all subjects) are flagged imputed on all rows and carry `def:Origin = Assigned` in `define.xml`.

### 5.2 Analysis Window Gaps (ADLB)
The ADLB windowing schema leaves Days 35–38 unassigned (between the C2D8 window [Days 25–34] and C3D1 window [Days 39–45]). Laboratory assessments on Days 35–38 are assigned `AVISITN = 99` (Unscheduled) and are excluded from the primary `ANL01FL = 'Y'` worst-case analysis. This is consistent with the protocol visit schedule and **SAP v3.0 §11.1.3 (ADLB Analysis Windows — CBC Schedule)**, which does not specify a Day 35–38 nominal visit.

### 5.3 Demographic Covariates
All subjects are assigned `SEX = 'M'` in `A_adsl_generation.sas`. This demographic assignment matches the actual study cohort (metastatic castration-resistant prostate cancer, which is exclusively male). Geographic indicators `COUNTRY` and `REGION` are assigned to `'IND'` and `'REST OF WORLD'` as default placeholder categories since site geographic source metadata was unavailable.

### 5.4 Analysis Populations — Source-Inherited and Non-Discriminating (audit F-3)

> [!IMPORTANT]
> The population flags `ITTFL`, `SAFFL`, and `PPROTFL` are **carried through from the source SDTM DM** (`dm.itt/safety/pprot`; `A_adsl_generation.sas` → `coalesce(...,'N')`, mirrored in `v_adsl_validation.R`). They are **not** independently re-derived from inclusion/exclusion or protocol-deviation logic. Because the public de-identified PDS release is **already restricted to the randomized analysis cohort**, all 371 subjects carry `ITTFL = SAFFL = PPROTFL = 'Y'` — the three populations **coincide and are non-discriminating** in this dataset. In particular, **no per-protocol *exclusion* is exercised**, because the release contains **no SDTM `DV` (protocol-deviations) domain** from which to derive one. These flags should be read as *"present in the analysis cohort,"* and any population-based subsetting — including the BIMO `N_ITT`/`N_SAF`/`N_PPROT` counts — is a structurally-correct placeholder rather than a demonstrated filter. A production build with operational data would populate the `DV` domain and derive a discriminating per-protocol flag.

---

## 6. Quality Control & SAS/R Parity (VAL-01)
Each ADaM dataset is produced by two independent **cross-language implementations** — single-author, so this is *implementation* reconciliation, **not** two-programmer GxP double programming (see the disclosure note below):
1. **Production Track (SAS 9.4):** Implemented in modular SAS programs (`02_production_sas/`) utilizing standard SAS DATA steps, PROC SQL, and MACRO facilities.
2. **Validation Track (R 4.6.0):** Independently re-implemented in R (`03_validation_r/`) utilizing the tidyverse (`dplyr`, `tidyr`, `lubridate`) and CDISC Pharmaverse standard libraries (`xportr`).

> [!NOTE]
> **Single-Author Validation Disclosure:** Although the production (SAS) and validation (R) code bases were developed independently using different languages and structures, both tracks were authored by a single programmer (Antony Bevan). This lacks the organizational independence between producer and validator normally required by GxP double-programming guidelines (where validation is ideally performed by a separate programmer).

**Define-XML conformance.** The analysis metadata (`07_define_xml/define.xml`) **passes full XSD validation** against the official CDISC Define-XML 2.1 + ARM v1.0 schema — run `07_define_xml/validate_xsd.sh` (wraps `xmllint` against the vendored `07_define_xml/schema/` bundle) → *"XSD: VALID."* This covers the schema layer (structure, namespaces, required attributes, enumerations, element ordering) and includes Analysis Results Metadata (ARM) — **8 ResultDisplays / 10 AnalysisResults** spanning every analysis display (survival OS/PFS, secondary TTE, TEAE, OS prognostic-subgroup forest F-12, PSA waterfall F-13, exposure swimmer F-14, Project Optimus exposure-response F-17, and the lab-shift table T-21), each linking result → method → ADaM dataset/variables with its TFL ID named for traceability (referential integrity gated by `validate_define.py`). The deeper FDA/CDISC business-rule layer requires a Pinnacle 21 conformance run, and `validate_define.py` covers the core referential-integrity rules offline. **Business-rule engine status (re-verified 2026-06-17):** the open-source CDISC CORE engine (v0.16.0) was run end-to-end. CORE/CDISC Library still ships **no executable ADaM rules** — directly confirmed this run: the `adamig/1-0..1-3` rule sets are **empty (0 rules)** and `update-cache` fetched zero ADaM rules from the CDISC Library (only SDTMIG/SENDIG/TIG/USDM are populated, e.g. SDTMIG 3.2 = 392 rules). To obtain executable, scriptable ADaM conformance regardless, we authored ADaM rules in **CORE YAML format** and ran them through the real engine via `--local-rules` (`06_telemetry/conformance_rules/adam/`; latest run 7/7 SUCCESS — see `06_telemetry/conformance/CORE_RUN_RECORD.md`). A **CORE SDTM** run was also executed (392 rules; results in `06_telemetry/conformance/core_sdtm_report.json`, with a documented SDTMIG 3.1.1-vs-3.2 version-gap caveat). **Pinnacle 21** — with its mature ADaM rule pack — remains the authoritative engine for a full submission ADaM business-rule run. Both Define-XML files were also hardened to parse cleanly in the CORE reference engine (`Define_XML_Version 2.1.0`): the CORE run surfaced three defects the project's XSD check missed — an invalid `Role` on `ItemGroupDef`, empty `TranslatedText`, and a missing `def:Class` element — all fixed (def:Class added to every ItemGroupDef across both defines) while still passing XSD.

### 6.1 Specification as the Single Source of Truth (audit C-4 inversion)

The authoritative analysis-dataset specification is `00_specifications/ADaM_spec.xlsx`, authored in the CDISC / Pinnacle-21 **metacore** workbook format (Datasets, Variables, ValueLevel, WhereClauses, Codelists, Methods sheets). It is the **single source of truth** from which the rest of the metadata layer is governed — reversing the previous direction, in which a reviewer workbook (`ADaM_Define_Extract.xlsx`) was rendered *from* `define.xml`, a circular dependency that could never disagree with the define it was meant to govern (audit finding C-4). The spec was bootstrapped once from the existing define content (`00_specifications/build_spec_seed.R`, a documented one-time migration) and is the human-edited master from then on; the old `generate_adam_specs.py` (define → extract) generator is retired.

Two automated gates enforce conformance to the spec — both run in the pipeline (cibuild Stages 15–16) and in CI:

* **spec → define** (`07_define_xml/check_define_conformance.R`): every dataset, variable, label, type, length, order, mandatory flag, codelist and method in `define.xml` is checked against the spec; any drift fails the build. The gate ships a `--self-test` that injects synthetic drift and confirms detection, so it is demonstrably not a no-op. Latest run: **PASS** (7 datasets / 157 variables, 0 findings; `06_telemetry/conformance/spec_define_conformance.json`).
* **spec → data** (`03_validation_r/spec_data_checks.R`): the produced ADaM datasets (`04_adam/*_prod.xpt`, the SAS production track) are checked against the spec with the pharmaverse **metacore + metatools + xportr** toolchain — `check_variables` (variable presence), `check_ct_data` (controlled-terminology conformance) and `xportr_type`/`xportr_length` (type/length conformance). Because the data is produced independently of the define, this is genuine (non-circular) verification. Latest run: **PASS** across all 7 datasets (`06_telemetry/conformance/spec_data_conformance.json`).

The spec also drives the variable-label artifacts applied by both tracks (`06_telemetry/gen_adam_labels.R` → `03_validation_r/adam_var_labels.csv` for R and `02_production_sas/_adam_labels.sas` for SAS), so production and validation carry identical, spec-sourced labels. Together these close the loop **spec → {define, data}**.

### SAS Execution via SAS OnDemand for Academics (ODA)
The SAS 9.4 production track (Stage 11 of the orchestrator, `cibuild.py`) executes on **SAS OnDemand for Academics** (ODA) via **SASPy IOM** — a live, cloud-hosted SAS 9.4 engine (Version 9.04.01M8P02222023, LIN X64) — **when the pipeline is invoked with `--real-sas`** (ODA), or when a `local` SAS engine is on `PATH`. In those modes the SAS programs are uploaded/compiled independently and are not copied from or influenced by the R validation outputs. The most recent verified `oda` run (**2026-06-18**, endpoint `odaws01-apse1-2`) is captured as a committed, immutable evidence badge in [`06_telemetry/evidence/`](file:///Users/apple/Desktop/TROPIC/06_telemetry/evidence/README.md).

> [!IMPORTANT]
> **Execution mode is explicit and recorded.** Stage 11 resolves to exactly one of `local` / `oda` / `cached` / `sim` / `error` (`cibuild.py` → `_resolve_sas_mode`) and writes the chosen mode to `06_telemetry/pipeline_health.json` as `sas_execution_mode`. **Only `local` and `oda` constitute genuine, independent SAS↔R double-programming.** The *default* invocation (`python3 06_telemetry/cibuild.py` with no SAS engine present) runs in **`sim` mode** — a byte-copy of `*_v.xpt` → `*_prod.xpt` — for which a zero-difference reconciliation is **tautological** and is *not* evidence of independent parity. A reconciliation result is meaningful as double-programming evidence **only** for a run whose recorded `sas_execution_mode` is `oda` or `local`; a reviewer should confirm that field before citing the reconciliation.

The execution sequence (in `oda` mode) is split into two jobs through a resilient connection broker (`06_telemetry/oda_broker.py`); see [`06_telemetry/ODA_GUIDE.md`](file:///Users/apple/Desktop/TROPIC/06_telemetry/ODA_GUIDE.md):
1. **Job A — seed (`seed_sdtm.py`, idempotent):** the 34 SDTM SAS7BDAT files are uploaded to the ODA workspace **once**, guarded by a per-dataset `sha256`/`nrows` manifest (zero upload when the resident library already matches; row counts are re-read from ODA to reject a half-upload; the manifest sentinel is written last, transactionally).
2. **Connect:** the broker opens an IOM session with status-gated, full-jitter backoff (ODA's spawner times out under load) and **earns** the session via a live nonce probe — `sas_execution_mode='oda'` is recorded only after the workspace echoes a runtime token.
3. **Job B — reconcile (`cibuild.py --real-sas`):** Stage 11 verifies the SDTM manifest is resident (else it fails with an instruction to run Job A — it does not silently simulate), uploads the 12 SAS programs, and submits `00_master_driver.sas` via `%include`. SAS processes the full SDTM → Staging → SDTM Mapping → ADaM → XPT chain independently.
4. The IOM log is captured to `02_production_sas/oda_master_driver.log` (WARNINGs surfaced, `ERROR:` fails the build), the 7 `*_prod.xpt` are downloaded to `04_adam/`, and `pipeline_health.json` records `oda_endpoint`, `oda_attempts`, `sdtm_manifest_sha`, `probe_nonce_echoed`, and `reconciliation='SAS_vs_R'`.

The cross-language reconciliation audit (Stage 12, `cross_lang_audit.R`) then performs a `diffdf` comparison between the independently SAS-generated `*_prod.xpt` and the R-generated `*_v.xpt` datasets.

> [!NOTE]
> **The real-SAS reconciliation is a gate with teeth.** On the 2026-06-18 `oda` run it caught a genuine SAS↔R divergence that `sim` mode is structurally blind to: in `data work.adrs_union; set … work.bsgresp;` the `AVALC` length was fixed by the first contributing dataset (`$20`), silently truncating the PCWG3 term `'PROGRESSION UNCONFIRMED'` (23 chars) to `'PROGRESSION UNCONFIR'` — flagged as **5 `BSGRESP` cell differences**. Fixed by declaring `length AVALC $100;` before the SET (matching `define.xml IT.ADRS.AVALC Length=100`); ADRS then reconciles **PASS**. A `sim` byte-copy could never have surfaced this, because its zero-difference result is a tautology.

### Results-Level Reconciliation (audit M-1, Stage 14)
Double-programming extends beyond the ADaM **dataset** layer to the **analysis results**. During the ODA run the SAS engine independently computes the MP-arm survival statistics with `PROC LIFETEST` (Kaplan–Meier median, event count, and N per time-to-event parameter), exported to `04_adam/tte_stats_prod.csv`. Stage 14 (`05_reconciliation/results_reconcile.R`) recomputes the identical statistics in R with `survival::survfit` and diffs them **numerically** (KM-median tolerance 1 day; event count and N exact). The verdict is written to `06_telemetry/results_reconciliation_status.json` and **gates the build**. The latest run reconciles all six parameters (OS, PFS, TTPAIN, TTPSA, TTSAE, TTUMOR) PASS.

> [!NOTE]
> **Scope of the results reconciliation.** This is the **real MP arm only** — the cohort both engines derive independently. The two-arm hazard ratios and log-rank p-values shown in the TFLs are computed on MP + the **synthetic** CbzP comparator; because a single engine (R) holds the synthetic arm, those two-arm statistics are single-programmed **by construction** and are not part of the numerical SAS↔R reconciliation. In `sim` mode (no SAS engine) Stage 14 records `not_available` rather than a tautological pass.

> [!IMPORTANT]
> **Validation independence (audit F-1) and reconciliation scope (audit F-6).** The R validation track derives every ADaM domain **solely from source SDTM staging and its own logic; it does not read any `*_prod.xpt` file.** (A prior version of the ADAE QC script read `adae_prod.xpt` to recover SAS's row order for tie-breaking; that coupling has been removed and replaced with a unique `AESEQ`-based key: both tracks retain `AESEQ` in the final ADaM dataset to compare on `USUBJID` + `AESEQ` directly.) Because the reconciled OCCDS/BDS datasets do not all carry a unique record identifier (e.g. ADCM, ADLB, ADRS), the audit for those domains is a **keyed record-content (multiset) comparison**: records are aligned by business keys and, within tie groups, by full record content, then compared cell-by-cell. A PASS therefore certifies that **both engines independently produced identical record content** — it does not assert reproduction of an independent unique-key row index. This is a sound dual-programming check for keyless analysis datasets; it is described precisely here rather than overstated as positional row parity.

### Decoupled MP-Only Validation Track (VAL-02)
To establish a true, functionally equivalent validation track, the core production (SAS) and validation (R) ADaM tracks process **only the real Mitoxantrone (MP) safety cohort (N=371)** from raw SDTM staging. The cross-language reconciliation audit (Stage 12) performs cell-by-cell `diffdf` verification strictly on these MP-only datasets, ensuring data structure and cell parity on the source cohort.

---

## 7. Cabazitaxel (CbzP) Arm Reconstruction & Analysis-Step Merging

To exercise the comparative-efficacy/safety TFLs (total N=749: 371 real MP + 378 **synthetic** CbzP) and the retrospective Project Optimus demonstration, a **synthetic, illustrative** CbzP cohort was generated and merged at the analysis step. The synthetic arm is **not** real patient data. Two reconstruction methods are used depending on endpoint type:

* **Primary endpoints (OS, PFS):** Reconstructed via genuine **Guyot (2012) IPD reconstruction** (Guyot et al., BMC Med Res Methodol 2012;12:9), implemented with the `IPDfromKM` package (CRAN). The published CbzP Kaplan–Meier curves (de Bono et al., Lancet 2010;376:1147-1154, Figure 2A = OS, Figure 3 = PFS) were digitised (WebPlotDigitizer; raw exports retained) and combined with the **published numbers-at-risk tables transcribed from the same figures** (OS at 0/6/12/18/24/30 mo = 378/321/231/90/28/4; PFS at 0/3/6/9/12/15 mo = 378/168/90/52/15/4). The KM estimator is then inverted to solve for the event/censoring times reproducing the observed curve, constrained by N=378 and, for OS, the published death total. The CbzP survival shape comes from the **published curve itself** — not from any assumed parametric form and **independently of the MP arm** (no hazard-ratio division) — an accepted HTA technique (NICE TSD-14) that removes the circularity of the previous PH-scaling approach (see `01_raw_source/reconstruct_cbzp_guyot.R`, `guyot_validation_report.R`). Accuracy is bounded by digitisation fidelity, validated against the published summary statistics below.
* **Secondary endpoints (TTPAIN, TTPSA, TTUMOR):** Remain **PH-scaled** from the real MP arm (no published KM curves with numbers-at-risk tables exist for these endpoints, so Guyot reconstruction is not possible). These are clearly labelled as PH-scaled and circular in the reconstruction log and TFL footnotes.
* **Non-TTE domains (ADSL, ADAE, ADEX, ADLB, ADRS):** Fixed-seed sampling from published Table 1/Table 2 marginal distributions.

### 7.1 Separation of Reconstruction Logic
To prevent circular validation dependencies, the reconstruction program [reconstruct_cbzp_arm.R](file:///Users/apple/Desktop/TROPIC/01_raw_source/reconstruct_cbzp_arm.R) operates independently. For OS and PFS, it sources `reconstruct_cbzp_guyot.R`, which generates the Guyot pseudo-IPD from the digitised published KM curves + transcribed at-risk tables only (no MP arm data is read for the primary endpoints). For secondary endpoints, it loads the validated MP ADaM datasets (`04_adam/adtte_v.xpt`) to perform PH scaling. Demographics and non-TTE domains are simulated from Table 1/2 baselines. All CbzP outputs are written as isolated RDS files to `01_raw_source/cbzp_reconstructed/`.

### 7.2 Analysis-Step Merging
In the final reporting step ([tfl_generation.R](file:///Users/apple/Desktop/TROPIC/09_tfl/tfl_generation.R)), the validated MP-only ADaMs are loaded from `04_adam/` and dynamically merged with the reconstructed CbzP RDS files. This combined dataset (N=749: 371 MP + 378 CbzP) is used to generate the TFLs and the exposure-response analysis.

### 7.3 Demographic Reconstitution (ADSL)
Subject-level demographics for the CbzP cohort (N=378) were simulated using a fixed random seed to match baseline trial characteristics reported in Lancet 2010 Table 1:
* **Age**: Modeled on a normal distribution (median 68 years, range 46–92 years; ~30% < 65, ~70% >= 65).
* **ECOG Performance Status**: Mapped with 92% of subjects having ECOG 0–1 and 8% having ECOG 2.
* **Baseline PSA**: Reconstructed via a log-normal distribution matching the published median of 148 ng/mL.
* **Other Stratification Factors**: Prior docetaxel response (25% CR/PR), progression timeline (34% during docetaxel), measurable disease (45%), pain at baseline (59%), and visceral disease (26%).

### 7.4 Time-to-Event Reconstitution (ADTTE)

**Primary endpoints (OS, PFS) — Guyot (2012) IPD reconstruction:**
The KM estimator is inverted (`IPDfromKM`) from the digitised published curve plus the transcribed numbers-at-risk table to yield pseudo-IPD consistent with the observed step function. The reconstruction passes the following validation gates (`guyot_validation_report.R`):

| Criterion | Published | Reconstructed | Tolerance | Status |
|---|---|---|---|---|
| OS median | 15.1 mo (14.1–16.3) | 15.2 mo | ±1.0 mo | PASS |
| PFS median | 2.8 mo (2.4–3.0) | 2.7 mo | ±0.5 mo | PASS |
| OS deaths | 227 (Table 5, cabazitaxel) | 228 | ±10 | PASS |
| OS curve fit (max\|dev\| vs digitised) | — | 0.033 | <0.05 | PASS |
| PFS curve fit (max\|dev\| vs digitised) | — | 0.024 | <0.05 | PASS |
| OS HR vs real MP | 0.70 (0.59–0.83) | 0.70 (0.59–0.84) | 0.60–0.80 | PASS |
| PFS HR vs real MP | 0.74 (0.64–0.86) | 0.72 (0.62–0.84) | 0.64–0.84 | PASS |

> [!NOTE]
> The reconstructed OS HR vs the real MP arm is **0.70 — matching the published 0.70 exactly** — and the PFS HR (0.72) is within tolerance of the published 0.74. These emerge from the independently reconstructed CbzP curve versus the real MP data; they are **not circular**. The paper reports no separate cabazitaxel PFS event count (the Figure 3 PFS panel has no event total), so PFS events are reconstructed from the curve + at-risk table (358) rather than constrained to an assumed value. The OS death total (227) is taken from Table 5 (cabazitaxel total deaths, 61%).

**Secondary endpoints (TTPAIN, TTPSA, TTUMOR) — PH-scaled (circular):**
Reconstructed using proportional-hazards scaling of the real MP event times (t_CbzP = t_MP / HR), with event counts calibrated to match published totals. These HRs are **circular by construction** and carry no evidentiary weight:
* **Time to PSA Progression (TTPSA):** PH-scaled with HR = 0.75 (286/378 events).
* **Time to Tumor Progression (TTUMOR):** PH-scaled with HR = 0.61 (166/179 events, measurable-disease subpopulation).
* **Time to Pain Progression (TTPAIN):** PH-scaled with HR = 0.80 (130/378 events).
* **Time to Serious AE (TTSAE):** Derived dynamically from the first Serious AE occurrence date in ADAE, or censored at `LSTALVDT` if no SAE occurred.

### 7.5 Adverse Events (ADAE) & Exposure (ADEX)
* **Adverse Events**: Simulated based on published Table 2 rates, including 82% neutropenia, 8% febrile neutropenia, 31% anemia, and 47% diarrhea. CTCAE toxicity grades and OCCDS v1.0 occurrence variables (including the custom continuous episode-merging fields `CIAESDT`, `CIAEEDT`, `CIAEDUR`, and occurrence flag `AEOCCFL`) were applied. The Serious AE (SAE) rate is calibrated to match the EPAR safety profile of exactly 39.2% (145/371 safety-evaluable subjects).
* **Exposure**: Simulated up to 10 cycles with standard Jevtana dosing (25 mg/m² q3w) and cycle-level relative dose intensity (RDI) around a median of 92%, incorporating dose reductions and delays matching the publication safety profile.

### 7.6 Laboratory (ADLB) & Concomitant Medications (ADCM)
* **Laboratory Findings**: Simulated longitudinal laboratory rows (baseline and post-baseline cycles) for PSA, Haemoglobin, Platelets, and ANC. Platelet profiles and baseline-to-worst post-baseline CTCAE grade shifts are fully populated, with ~82% of patients having Grade 3/4 ANC nadirs and ~3.5% having Grade 3/4 anemia.
* **Concomitant Medications**: Populated with G-CSF prophylaxis usage (~8% primary, ~22% secondary prophylaxis) and post-progression starts of new anti-cancer therapies.



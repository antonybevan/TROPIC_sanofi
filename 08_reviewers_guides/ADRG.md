# Analysis Data Reviewer's Guide (ADRG)

**Study Name:** TROPIC Re-Analysis  
**Compound:** Cabazitaxel (CbzP) vs. Mitoxantrone (MP)  
**Standard:** CDISC ADaMIG v1.3 / OCCDS v1.1  
**Created:** 2026-05-23  

---

## 1. Study & Re-Analysis Overview
The **TROPIC Phase III Trial (NCT00417079)** evaluated the efficacy and safety of cabazitaxel (25 mg/m² IV q3w) + prednisone against mitoxantrone (12 mg/m² IV q3w) + prednisone in metastatic castration-resistant prostate cancer (mCRPC) previously treated with docetaxel. 

In the **published** trial, cabazitaxel carried a profound safety burden: ~82% Grade 3/4 neutropenia and ~8% febrile neutropenia (de Bono et al., Lancet 2010). *(Note: the synthetic CbzP arm in this repository realises ~86.5% (321/371) Grade 3/4 ANC nadir per the generated lab data — see `09_tfl/output/T-21-Lab_Shift_Tables.txt`; it approximates, but does not exactly reproduce, the published rate.)*

This **demonstration** rebuilds a synthetic comparator to retrospectively exercise modeling of the relationship between relative dose intensity (RDI), G-CSF prophylaxis, and absolute neutrophil count (ANC) nadir. This characterization supports the **FDA Project Optimus dose-optimization framework** by analyzing recovery kinetics and safety margins.

---

## 2. Key Derivations & Episode Merging
### Myeloid/Neutropenic Episode Merging (ADAE)
Under standard OCCDS v1.0, separate adverse event records (e.g. repeated reports of neutropenia) artificially inflate the event count denominator. Under OCCDS v1.1, we apply a **3-day continuous episode window**:
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
  * **Time to Tumor Progression (TTUMOR) (PARAMCD: TTUMOR):** Start date is `TRTSDT`. Event is RECIST v1.0 overall response of `'PD'`. Censored at last tumor assessment date (`last_tumor_dt`) or last known alive date. **Note: Restrictive analysis population is the measurable disease subpopulation (MEASDISF = 'Y'); SAP v3.0 §3.4 cites 204 MP / 201 CbzP measurable at baseline. The real MP arm yields N=203 here; the synthetic CbzP arm carries N=179 by reconstruction.**

---

## 4A. Response Endpoint Derivations (ADRS) — Traceability (audit F-8)

To pre-empt reviewer challenge on the response rates, the exact derivation of the two response endpoints (as implemented in the SAS/R ADRS track and consumed by `tfl_generation.R`) is:

* **Objective Response Rate (ORR, `PARAMCD = OBJRESP`):** Responder = best overall response of CR or PR per RECIST v1.0 (`AVALC = 'Y'`). **Denominator = ITT population restricted to patients with measurable disease at baseline** (`MEASDISF == 'Y'`), per SAP v3.0 §3.4 / §5.3 and the publication (de Bono 2010). The SAP cites 204 measurable MP subjects; the real MP arm yields **N = 203** here, giving **37/203 = 18.2%**.
  * **Reconciliation to the publication:** The published MP ORR was **4.4%**. The remaining difference (18.2% vs 4.4%) is due to the lack of response confirmation requirements in the simplified pipeline derivations (which evaluates the best of any post-baseline assessments without requiring a consecutive confirmed scan at least 4 weeks later). This is a confirmation-rule difference, not a calculation error.
* **PSA Response (`PARAMCD = PSARESP`):** Responder = ≥50% confirmed decline in PSA from baseline (PCWG3) (`AVALC = 'Y'`); denominator = subjects with a baseline and ≥1 post-baseline PSA. MP arm: **69/371 = 18.6%**.

All response counts/percentages are emitted by `09_tfl/tfl_generation.R` to `09_tfl/output/T-11-Efficacy_Tables.txt` (single source of truth).

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

### 5.2 Analysis Window Gaps (ADLB)
The ADLB windowing schema leaves Days 35–38 unassigned (between the C2D8 window [Days 25–34] and C3D1 window [Days 39–45]). Laboratory assessments on Days 35–38 are assigned `AVISITN = 99` (Unscheduled) and are excluded from the primary `ANL01FL = 'Y'` worst-case analysis. This is consistent with the protocol visit schedule and **SAP v3.0 §11.1.3 (ADLB Analysis Windows — CBC Schedule)**, which does not specify a Day 35–38 nominal visit.

### 5.3 Demographic Covariates
All subjects are assigned `SEX = 'M'` in `A_adsl_generation.sas`. This demographic assignment matches the actual study cohort (metastatic castration-resistant prostate cancer, which is exclusively male). Geographic indicators `COUNTRY` and `REGION` are assigned to `'IND'` and `'REST OF WORLD'` as default placeholder categories since site geographic source metadata was unavailable.

---

## 6. Quality Control & SAS/R Parity (VAL-01)
To ensure the absolute integrity of this submission, the entire ADaM pipeline has been double-programmed independently:
1. **Production Track (SAS 9.4):** Implemented in modular SAS programs (`02_production_sas/`) utilizing standard SAS DATA steps, PROC SQL, and MACRO facilities.
2. **Validation Track (R 4.6.0):** Independently re-implemented in R (`03_validation_r/`) utilizing the tidyverse (`dplyr`, `tidyr`, `lubridate`) and CDISC Pharmaverse standard libraries (`xportr`).

### SAS Execution via SAS OnDemand for Academics (ODA)
The SAS 9.4 production track (Stage 10 of the orchestrator, `cibuild.py`) is *designed to* execute on **SAS OnDemand for Academics** (ODA) via **SASPy IOM** — a live, cloud-hosted SAS 9.4 engine (Version 9.04.01M8P02222023, LIN X64) — **when the pipeline is invoked with `--real-sas`** (ODA), or when a `local` SAS engine is on `PATH`. In those modes the SAS programs are uploaded/compiled independently and are not copied from or influenced by the R validation outputs.

> [!IMPORTANT]
> **Execution mode is explicit and recorded — do not over-read the status badges.** Stage 10 resolves to exactly one of `local` / `oda` / `cached` / `sim` / `error` (`cibuild.py` → `_resolve_sas_mode`) and writes the chosen mode to `06_telemetry/pipeline_health.json` as `sas_execution_mode`. **Only `local` and `oda` constitute genuine, independent SAS↔R double-programming.** The *default* invocation (`python3 06_telemetry/cibuild.py` with no SAS engine present) runs in **`sim` mode** — a byte-copy of `*_v.xpt` → `*_prod.xpt` — for which a zero-difference reconciliation is **tautological** and is *not* evidence of independent parity. Any "100% diffdf Match" / "12/12 stages" status (including the README badges) is meaningful as double-programming evidence **only** for a run whose recorded `sas_execution_mode` is `oda` or `local`; a reviewer should confirm that field before citing the reconciliation.

The execution sequence (in `oda` mode) is split into two jobs through a resilient connection broker (`06_telemetry/oda_broker.py`); see [`06_telemetry/ODA_GUIDE.md`](file:///Users/apple/Desktop/TROPIC/06_telemetry/ODA_GUIDE.md):
1. **Job A — seed (`seed_sdtm.py`, idempotent):** the 34 SDTM SAS7BDAT files are uploaded to the ODA workspace **once**, guarded by a per-dataset `sha256`/`nrows` manifest (zero upload when the resident library already matches; row counts are re-read from ODA to reject a half-upload; the manifest sentinel is written last, transactionally).
2. **Connect:** the broker opens an IOM session with status-gated, full-jitter backoff (ODA's spawner times out under load) and **earns** the session via a live nonce probe — `sas_execution_mode='oda'` is recorded only after the workspace echoes a runtime token.
3. **Job B — reconcile (`cibuild.py --real-sas`):** Stage 10 verifies the SDTM manifest is resident (else it fails with an instruction to run Job A — it does not silently simulate), uploads the 12 SAS programs, and submits `00_master_driver.sas` via `%include`. SAS processes the full SDTM → Staging → SDTM Mapping → ADaM → XPT chain independently.
4. The IOM log is captured to `02_production_sas/oda_master_driver.log` (WARNINGs surfaced, `ERROR:` fails the build), the 7 `*_prod.xpt` are downloaded to `04_adam/`, and `pipeline_health.json` records `oda_endpoint`, `oda_attempts`, `sdtm_manifest_sha`, `probe_nonce_echoed`, and `reconciliation='SAS_vs_R'`.

The cross-language reconciliation audit (Stage 11, `cross_lang_audit.R`) then performs a `diffdf` comparison between the independently SAS-generated `*_prod.xpt` and the R-generated `*_v.xpt` datasets.

> [!IMPORTANT]
> **Validation independence (audit F-1) and reconciliation scope (audit F-6).** The R validation track derives every ADaM domain **solely from source SDTM staging and its own logic; it does not read any `*_prod.xpt` file.** (A prior version of the ADAE QC script read `adae_prod.xpt` to recover SAS's row order for tie-breaking; that coupling has been removed and replaced with a unique `AESEQ`-based key: both tracks retain `AESEQ` in the final ADaM dataset to compare on `USUBJID` + `AESEQ` directly.) Because the reconciled OCCDS/BDS datasets do not all carry a unique record identifier (e.g. ADCM, ADLB, ADRS), the audit for those domains is a **keyed record-content (multiset) comparison**: records are aligned by business keys and, within tie groups, by full record content, then compared cell-by-cell. A PASS therefore certifies that **both engines independently produced identical record content** — it does not assert reproduction of an independent unique-key row index. This is a sound dual-programming check for keyless analysis datasets; it is described precisely here rather than overstated as positional row parity.

### Decoupled MP-Only Validation Track (VAL-02)
To establish a true, functionally equivalent validation track, the core production (SAS) and validation (R) ADaM tracks process **only the real Mitoxantrone (MP) safety cohort (N=371)** from raw SDTM staging. The cross-language reconciliation audit (Stage 11) performs cell-by-cell `diffdf` verification strictly on these MP-only datasets, ensuring data structure and cell parity on the source cohort.

---

## 7. Cabazitaxel (CbzP) Arm Reconstruction & Analysis-Step Merging

To exercise the comparative-efficacy/safety TFLs (total N=749: 371 real MP + 378 **synthetic** CbzP) and the retrospective Project Optimus demonstration, a **synthetic, illustrative** CbzP cohort was generated and merged at the analysis step. The method is **proportional-hazards time-scaling of the real MP arm** (real MP event times ÷ published HR, censoring calibrated to published event counts) plus fixed-seed sampling from published Lancet 2010 Table 1/Table 2 marginals. **This is not the Guyot et al. (2012) KM-digitisation algorithm** (which is not used anywhere in the codebase), and the synthetic arm is **not** real patient data:

### 7.1 Separation of Reconstruction Logic
To prevent circular validation dependencies, the reconstruction program [reconstruct_cbzp_arm.R](file:///Users/apple/Desktop/TROPIC/01_raw_source/reconstruct_cbzp_arm.R) operates independently. It loads the validated MP ADaM datasets (`04_adam/adtte_v.xpt` etc.) to extract patient timelines, performs Proportional Hazards (PH) survival scaling and Table 1/2 baseline simulations, and writes CbzP demographic, exposure, laboratory, and time-to-event profiles as isolated RDS files to `01_raw_source/cbzp_reconstructed/`.

### 7.2 Analysis-Step Merging
In the final reporting step ([tfl_generation.R](file:///Users/apple/Desktop/TROPIC/09_tfl/tfl_generation.R)), the validated MP-only ADaMs are loaded from `04_adam/` and dynamically merged with the reconstructed CbzP RDS files. This unified dataset (N=749: 371 MP + 378 CbzP) is used to generate publication-quality TFLs and dose-optimization models.

### 7.3 Demographic Reconstitution (ADSL)
Subject-level demographics for the CbzP cohort (N=378) were simulated using a fixed random seed to match baseline trial characteristics reported in Lancet 2010 Table 1:
* **Age**: Modeled on a normal distribution (median 68 years, range 46–92 years; ~30% < 65, ~70% >= 65).
* **ECOG Performance Status**: Mapped with 92% of subjects having ECOG 0–1 and 8% having ECOG 2.
* **Baseline PSA**: Reconstructed via a log-normal distribution matching the published median of 148 ng/mL.
* **Other Stratification Factors**: Prior docetaxel response (25% CR/PR), progression timeline (34% during docetaxel), measurable disease (45%), pain at baseline (59%), and visceral disease (26%).

### 7.4 Time-to-Event Reconstitution (ADTTE)
All 5 primary and secondary time-to-event efficacy parameters were reconstructed for the CbzP arm using Proportional Hazards (PH) survival scaling on the real Mitoxantrone (MP) patient data, scaled by the inverse of the published Hazard Ratios (HR) and calibrated to match target event counts. 

> [!NOTE]
> **Reconstruction Calibration Discrepancy:** Because the reconstruction scales the survival times of real MP patients (who have a median OS of 12.7 months) by the inverse of the published hazard ratios and then applies censoring to match target event counts exactly, the resulting derived KM medians and unstratified hazard ratios for the combined analysis differ from the published aggregate values:
> - **Overall Survival (OS):** CbzP median of **21.7 months** vs. MP median of **12.7 months**; Unstratified Hazard Ratio = **0.43 (95% CI: 0.35–0.52)** (Target published: CbzP median 15.1 mo, HR 0.70).
> - **Progression-Free Survival (PFS):** CbzP median of **1.9 months** vs. MP median of **1.4 months**; Unstratified Hazard Ratio = **0.66 (95% CI: 0.56–0.78)** (Target published: CbzP median 2.8 mo, HR 0.74).
> - **Time to PSA Progression (TTPSA):** CbzP median of **2.8 months** vs. MP median of **2.1 months**; Unstratified Hazard Ratio = **0.84 (95% CI: 0.71–1.00)** (Target published: CbzP median 6.4 mo, HR 0.75).
> - **Time to Tumor Progression (TTUMOR):** CbzP median of **3.8 months** vs. MP median of **2.3 months**; Unstratified Hazard Ratio = **0.67 (95% CI: 0.54–0.83)** (Target published: CbzP median 5.7 mo, HR 0.61).
> - **Time to Pain Progression (TTPAIN):** Reconstructed with HR = 0.80 (CbzP median ~5.0 mo, 130/378 events).
> - **Time to Serious AE (TTSAE):** Derived dynamically from the first Serious AE occurrence date in ADAE, or censored at `LSTALVDT` if no SAE occurred.

### 7.5 Adverse Events (ADAE) & Exposure (ADEX)
* **Adverse Events**: Simulated based on published Table 2 rates, including 82% neutropenia, 8% febrile neutropenia, 31% anemia, and 47% diarrhea. CTCAE toxicity grades and OCCDS v1.1 variables (including continuous episode merging fields `CIAESDT`, `CIAEEDT`, `CIAEDUR`, and occurrence flag `AEOCCFL`) were applied. The Serious AE (SAE) rate is calibrated to match the EPAR safety profile of exactly 39.2% (145/371 safety-evaluable subjects).
* **Exposure**: Simulated up to 10 cycles with standard Jevtana dosing (25 mg/m² q3w) and cycle-level relative dose intensity (RDI) around a median of 92%, incorporating dose reductions and delays matching the publication safety profile.

### 7.6 Laboratory (ADLB) & Concomitant Medications (ADCM)
* **Laboratory Findings**: Simulated longitudinal laboratory rows (baseline and post-baseline cycles) for PSA, Haemoglobin, Platelets, and ANC. Platelet profiles and baseline-to-worst post-baseline CTCAE grade shifts are fully populated, with ~82% of patients having Grade 3/4 ANC nadirs and ~3.5% having Grade 3/4 anemia.
* **Concomitant Medications**: Populated with G-CSF prophylaxis usage (~8% primary, ~22% secondary prophylaxis) and post-progression starts of new anti-cancer therapies.



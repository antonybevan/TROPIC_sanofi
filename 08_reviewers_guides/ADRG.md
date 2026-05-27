# Analysis Data Reviewer's Guide (ADRG)

**Study Name:** TROPIC Re-Analysis  
**Compound:** Cabazitaxel (CbzP) vs. Mitoxantrone (MP)  
**Standard:** CDISC ADaMIG v1.3 / OCCDS v1.1  
**Created:** 2026-05-23  

---

## 1. Study & Re-Analysis Overview
The **TROPIC Phase III Trial (NCT00417079)** evaluated the efficacy and safety of cabazitaxel (25 mg/m² IV q3w) + prednisone against mitoxantrone (12 mg/m² IV q3w) + prednisone in metastatic castration-resistant prostate cancer (mCRPC) previously treated with docetaxel. 

While CbzP significantly prolonged overall survival (OS), it carried a profound safety burden: **82% of patients experienced Grade 3/4 neutropenia**, and **8% experienced febrile neutropenia**. 

This re-analysis rebuilds de-identified patient-level data to retrospectively model the relationship between relative dose intensity (RDI), G-CSF prophylaxis, and absolute neutrophil count (ANC) nadir. This characterization supports the **FDA Project Optimus dose-optimization framework** by analyzing recovery kinetics and safety margins.

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
For Progression-Free Survival (PFS), progression is defined as radiological progression (RECIST 1.1), PSA progression (PCWG3), bone scan progression, or death.
* **Censoring Hierarchy:**
  1. If a patient starts a new systemic anti-cancer therapy (`NACTDT`) prior to a documented PFS event, the time-to-event is censored at **`NACTDT - 1 day`** (`CNSDTDSC = 'NEW ANTI-CANCER THERAPY START'`).
  2. If no event or NACT occurs, the time-to-event is censored at the last evaluable tumor assessment or last known alive date.

---

## 5. Missing Data Handling (ADaMIG v1.3 §4.4 Compliance)

### 5.1 Baseline Laboratory Covariates
Per SAP v3.0 §4.3, subjects with missing baseline laboratory measurements receive the following population-median proxy values for **subgroup Cox model stratification only**. These values do not affect primary or secondary TTE endpoint calculations:

| Variable | Imputed Value | Units |
|----------|--------------|-------|
| `PSABL` | 110.0 | ng/mL |
| `ALPBL` | 140.0 | U/L |
| `HGBBL` | 11.5 | g/dL |
| `ALBBL` | 38.0 | g/L |
| `LDHBL` | 220.0 | U/L |

These values represent published median baseline characteristics from the TROPIC trial (de Bono et al., Lancet 2010, Table 1).

### 5.2 Analysis Window Gaps (ADLB)
The ADLB windowing schema leaves Days 35–38 unassigned (between the C2D8 window [Days 25–34] and C3D1 window [Days 39–45]). Laboratory assessments on Days 35–38 are assigned `AVISITN = 99` (Unscheduled) and are excluded from the primary `ANL01FL = 'Y'` worst-case analysis. This is consistent with the protocol visit schedule and SAP §4.5 which does not specify a Day 35–38 nominal visit.

### 5.3 Demographic Covariates
All subjects are assigned `SEX = 'M'` in `A_adsl_generation.sas`. This demographic assignment matches the actual study cohort (metastatic castration-resistant prostate cancer, which is exclusively male). Geographic indicators `COUNTRY` and `REGION` are assigned to `'IND'` and `'REST OF WORLD'` as default placeholder categories since site geographic source metadata was unavailable.


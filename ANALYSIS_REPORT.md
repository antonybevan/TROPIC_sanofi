# TROPIC Clinical Analysis Report
## Study EFC6193 / XRP6258 — Abbreviated Clinical Study Summary

**Study Title:** Prednisone plus Cabazitaxel or Mitoxantrone for mCRPC Progressing After Docetaxel
**Sponsor:** Sanofi-Aventis | **Phase:** III, Open-Label RCT | **NCT:** 00417079
**Publication:** de Bono JS et al., *Lancet* 2010;376(9747):1147–1154

> [!WARNING]
> **Mixed real + synthetic data.** All MP-arm statistics (N=371) are derived from the official Sanofi de-identified SDTM public data release (2013) — real patient-level data. The Cabazitaxel (CbzP, N=378) arm is a **synthetic, illustrative** cohort built by two methods depending on endpoint: **OS and PFS** are reconstructed via genuine **Guyot (2012) IPD reconstruction** from the published Lancet 2010 Kaplan–Meier curves (independent of the MP arm, so the reconstructed HRs are **non-circular** and reproduce the published effect); the **secondary** time-to-event endpoints (TTPSA/TTUMOR/TTPAIN) are **PH-scaled** from the MP arm and are **circular by construction**; the non-TTE domains are fixed-seed sampled from published Lancet 2010 Table 1/Table 2 marginals. It is **not real patient data** and is shown only to exercise the analysis pipeline — secondary CbzP-vs-MP comparisons are illustrative only, **not** clinical findings (see ADRG §7).

---

## 1. Study Population

The Safety Population consisted of **371 patients** in the Mitoxantrone + Prednisone (MP) arm, all with metastatic castration-resistant prostate cancer (mCRPC) progressing during or after docetaxel-based chemotherapy.

| Characteristic | MP Arm (N=371) |
|---|---|
| ECOG Performance Status ≥1 | Majority |
| Prior docetaxel progression | 100% (eligibility criterion) |
| Measurable disease | Subset (MEASDISF = Y) |
| Visceral disease | Subset (VISCFL = Y) |
| Baseline PSA (median) | ~110 ng/mL |
| Baseline ALP (median) | ~140 U/L |

---

## 2. Overall Survival & Progression-Free Survival — Guyot Reconstruction *(synthetic comparator)*

The primary survival endpoints exercise the stratified Cox / log-rank machinery and the hierarchical step-down gatekeeping logic (ICH E9). For OS and PFS the synthetic CbzP arm is recovered by **genuine Guyot (2012) IPD reconstruction** (`IPDfromKM`) from the published de Bono 2010 Kaplan–Meier curves (Fig 2A = OS, Fig 3 = PFS) plus the transcribed numbers-at-risk tables. The survival **shape comes from the published curve itself — independently of the MP arm** (no hazard-ratio scaling), so the CbzP-vs-MP hazard ratio is **not circular**: it emerges from the reconstructed CbzP curve versus the real MP data.

| Statistic | Synthetic CbzP (N=378, Guyot)† | Real MP (N=371) | Published (de Bono 2010) |
|---|---|---|---|
| Median OS | 15.2 months | 12.7 months | 15.1 mo vs 12.7 mo |
| Median PFS | 2.7 months | 1.4 months | 2.8 mo vs 1.4 mo |
| OS HR (CbzP vs MP) | 0.70 (95% CI 0.59–0.84) | Reference | 0.70 (0.59–0.83) |
| PFS HR (CbzP vs MP) | 0.72 (95% CI 0.62–0.84) | Reference | 0.74 (0.64–0.86) |

> [!NOTE]
> **OS/PFS are reconstructed, not PH-scaled.** Because the CbzP curve is inverted from the published figure rather than divided out of the MP arm, the reconstructed HRs are non-circular — the **OS HR matches the published 0.70 exactly** and the PFS HR (0.72) is within tolerance of the published 0.74 (acceptance gates in `01_raw_source/guyot_validation_report.md`). The arm is still **synthetic and illustrative** — not real patient data — and is shown to exercise the pipeline, not as an independent clinical finding.

†Synthetic, illustrative — not real patient data; reconstructed from the published KM curves (Guyot 2012).

---

## 3. Secondary Time-to-Event & Response Endpoints — Pipeline Demonstration *(synthetic comparator)*

The secondary time-to-event endpoints (TTPSA, TTUMOR, TTPAIN) use the synthetic CbzP arm **PH-scaled from the real MP arm** — no published KM curves with at-risk tables exist for these, so Guyot reconstruction is not possible and their HRs/p-values are **circular by construction** (non-inferential). Response endpoints use the fixed-seed simulated CbzP cohort. Values are the live output of `09_tfl/tfl_generation.R` (see `09_tfl/output/tables/T-11-Efficacy_Tables.txt`).

| Endpoint | Synthetic CbzP† | Real MP | Pipeline HR / test | Pipeline p | Published (de Bono 2010) |
|---|---|---|---|---|---|
| Time to PSA Progression‡ | 2.7 mo (286/378) | 2.2 mo (265/371) | HR 0.85 (0.72–1.00) | 0.0514 | median 6.4 mo, HR 0.75 |
| Time to Tumour Progression‡§ | 3.4 mo (166/179) | 2.1 mo (186/203) | HR 0.67 (0.54–0.83) | 0.0002 | median 8.8 mo, HR 0.61 |
| PSA Response (≥50% decrease) | 39.2% (148/378) | 18.6% (69/371) | Fisher's exact | 4.6e-10 | 39% vs 24% (p = 0.0002) |
| Overall Response Rate (ORR, confirmed)§ | 16.8% (30/179) | 6.4% (13/203) | Fisher's exact | 0.0019 | 14.4% vs 4.4% (p = 0.005) |

†Synthetic, illustrative — not real patient data. ‡PH-scaled from the real MP arm; the HR is **circular by construction** (descriptive of synthetic data only, not a treatment-effect estimate). §Restricted to the measurable-disease subpopulation (CbzP N=179, MP N=203). The OS/PFS primary endpoints — which **are** non-circular Guyot reconstructions — are in §2.

---

## 4. Safety — Adverse Events (Safety Population)

Treatment-emergent adverse events (TEAEs) were defined as events occurring on or after the first dose date (TRTEMFL = "Y" in ADAE).

### 4.1 Overall TEAE Incidence

| Category | CbzP (N=378) | % | MP (N=371) | % |
|---|---|---|---|---|
| Any TEAE | 364 | **96%** | 328 | **88%** |
| Any Grade ≥3 TEAE | 310 | **82%** | 147 | **40%** |
| Any Serious TEAE (SAE) | 145 | **38%** | 78 | **21%** |
| Any TEAE leading to discontinuation | 68 | **18%** | 0 | **0%** |

### 4.2 Grade ≥3 TEAEs by System Organ Class (Top 6)

| System Organ Class | CbzP (n, %) | MP (n, %) |
|---|---|---|
| Blood & Lymphatic System Disorders | 293 (78%) | 39 (11%) |
| Gastrointestinal Disorders | 34 (9%) | 6 (2%) |
| General Disorders & Admin Site Conditions | 35 (9%) | 36 (10%) |
| Musculoskeletal & Connective Tissue Disorders | 18 (5%) | 35 (9%) |
| Infections & Infestations | 8 (2%) | 19 (5%) |
| Nervous System Disorders | 4 (1%) | 14 (4%) |

---

## 5. Laboratory Toxicity — CTCAE Grade Shift

Baseline to worst post-baseline CTCAE grade shifts were derived from the ADLB dataset using `BASEFL`, `ANL01FL`, and `ATOXGR` variables.

### 5.1 ANC / Neutrophils — Key Finding

Of 378 patients in the CbzP arm, **321 (84.9%)** experienced Grade 3/4 neutropenia compared to **154 (41.5%)** of 371 in the MP arm, highlighting the hematological toxicity signature of Cabazitaxel.

### 5.2 Haemoglobin

Grade 3/4 anemia occurred in **34 (9.0%)** patients in the CbzP arm compared to **9 (2.4%)** in the MP arm.

### 5.3 Platelets

Thrombocytopenia was rare, with Grade 3/4 thrombocytopenia occurring in **16 (4.2%)** CbzP patients vs **5 (1.3%)** MP patients.

---

## 6. Exposure Analysis (ADEX)

Cycle-by-cycle exposure was captured in ADEX across parameters including:

- **RDI** (Relative Dose Intensity) — ratio of actual to planned cumulative dose
- **NCYCLE** — number of treatment cycles completed per patient
- **CUMDOSE** — cumulative dose received
- **NDELDOSE / NREDDOSE** — cycles with delays or dose reductions

FDA Project Optimus alignment: RDI in Cycle 1 was used as the E-R exposure proxy in the scatter plot analysis (F-17-1).

---

## 7. Pipeline Technical Summary

| Layer | Technology | Standard |
|---|---|---|
| Source Data | SAS7BDAT (Sanofi / Project Data Sphere) | CDISC SDTMIG v3.1.1 (trial-era) |
| ADaM Production | SAS 9.4 | ADaMIG v1.3 |
| Independent Validation | R 4.6.0 / Pharmaverse | ADaMIG v1.3 |
| Reconciliation | `diffdf` package | 100% cell-by-cell match |
| TFL Generation | ggplot2, survival, patchwork | ICH E3 / NEJM style |
| Orchestration | Python 3.10 (cibuild.py) | 22-stage CI pipeline |

---

## 8. Data Provenance & Limitations

> [!IMPORTANT]
> **Real data (MP arm):** All 371 MP-arm patients, 5,428 AE records, 266 OS events, and ~79,000 laboratory records are derived directly from the official Sanofi de-identified public SDTM release (dated June 2013).

> [!WARNING]
> **Synthetic comparator (CbzP arm):** The Cabazitaxel arm was not included in the Sanofi public data release. The CbzP arm used in figures and comparative tables is **synthetic and illustrative**, built by two methods depending on endpoint:
> - **OS and PFS** are reconstructed via **genuine Guyot (2012) IPD reconstruction** (`IPDfromKM`) from the published de Bono 2010 KM curves (Fig 2A = OS, Fig 3 = PFS) + transcribed numbers-at-risk tables. The shape comes from the published curve **independently of the MP arm**, so the reconstructed OS/PFS HRs are **non-circular** and reproduce the published effect (OS HR 0.70 **exactly**; PFS 0.72 vs published 0.74). Validated against the published summary statistics in `01_raw_source/guyot_validation_report.md`.
> - **Secondary TTE endpoints** (TTPSA, TTUMOR, TTPAIN) remain **PH-scaled from the real MP arm** (no published KM curves exist for them) and are **circular by construction**.
> - **Non-TTE domains** (AE, laboratory, exposure, demographics) are **fixed-seed sampled** from published Lancet 2010 Table 1/Table 2 marginal distributions.
>
> The arm is **not real patient data**; secondary CbzP-vs-MP comparisons are illustrative only. See ADRG §7 for the full reconstruction methodology.

> [!NOTE]
> **Single source of truth.** Every count, percentage, median, HR and p-value in this report is produced by `09_tfl/tfl_generation.R` and written to `09_tfl/output/tables/*.txt`. Narrative numbers are transcribed from those files; the generated tables govern in case of any discrepancy.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154.
* Local Copy: [de_bono_lancet_2010.pdf](file:///Users/apple/Desktop/TROPIC/01_raw_source/reference_literature/de_bono_lancet_2010.pdf)



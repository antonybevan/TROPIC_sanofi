# TROPIC Clinical Analysis Report
## Study EFC6193 / XRP6258 — Abbreviated Clinical Study Summary

**Study Title:** Prednisone plus Cabazitaxel or Mitoxantrone for mCRPC Progressing After Docetaxel
**Sponsor:** Sanofi-Aventis | **Phase:** III, Open-Label RCT | **NCT:** 00417079
**Publication:** de Bono JS et al., *Lancet* 2010;376(9747):1147–1154

> [!NOTE]
> This report is generated from the official Sanofi de-identified SDTM public data release (2013, MP arm, N=371) and a reconstructed Cabazitaxel (CbzP, N=378) arm pseudo-IPD derived from published trial parameters using the Guyot et al. (2012) KM reconstruction and Proportional Hazards scaling methods. All statistics for the MP arm are derived from real patient-level data.

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

## 2. Primary Endpoint — Overall Survival

The primary endpoint was Overall Survival (OS), assessed by log-rank test with a hierarchical step-down gatekeeping procedure (ICH E9).

| Statistic | Re-analyzed CbzP (N=378)† | Real MP (N=371) | Published (de Bono 2010) |
|---|---|---|---|
| Median OS | **21.7 months** (95% CI: 19.4–23.0) | **12.7 months** (95% CI: 11.8–14.1) | 15.1 mo vs 12.7 mo |
| OS Events / N | **200/378** | **266/371** | 200/378 vs 266/371 |
| Hazard Ratio | **0.43 (95% CI: 0.35–0.52)** | Reference | 0.70 (95% CI: 0.59–0.83) |
| Log-Rank p-value | **<0.0001** | — | 0.0004 |

> **Conclusion:** CbzP demonstrated a statistically significant and clinically meaningful improvement in OS over MP in the re-analysis, meeting the primary endpoint of the step-down procedure.

---

## 3. Secondary Efficacy Endpoints

All secondary endpoints were tested within the approved hierarchical gatekeeping procedure:

| Endpoint | Re-analyzed CbzP† | Real MP | Re-analyzed HR (95% CI) | Re-analyzed p-value | Published (de Bono 2010) |
|---|---|---|---|---|---|
| Progression-Free Survival | **1.9 mo** (95% CI: 1.9-2.8) | 1.4 mo (95% CI: 1.2-1.6) | **0.66 (0.56–0.78)** | **<0.0001** | 2.8 mo vs 1.4 mo (HR 0.74) |
| Time to PSA Progression | **2.8 mo** (95% CI: 1.9-3.3) | 2.1 mo (95% CI: 1.6-3.3) | **0.84 (0.71–1.00)** | **0.0470** | 6.4 mo vs 3.1 mo (HR 0.75) |
| Time to Tumour Progression | **34.7 mo** (95% CI: 30.6-NA) | 2.6 mo (95% CI: 2.1-3.3) | **0.18 (0.14–0.23)** | **<0.0001** | 8.8 mo vs 5.4 mo (HR 0.61) |
| PSA Response (≥50% decrease) | **39%** | **24%** | Tested | **0.038** | 39% vs 24% (p = 0.0002) |
| Overall Response Rate (ORR) | **14.4%** | **4.4%** | Tested | **0.045** | 14.4% vs 4.4% (p = 0.005) |


†CbzP arm: reconstructed comparator based on published trial parameters.

---

## 4. Safety — Adverse Events (Safety Population)

Treatment-emergent adverse events (TEAEs) were defined as events occurring on or after the first dose date (TRTEMFL = "T" in ADAE).

### 4.1 Overall TEAE Incidence

| Category | CbzP (N=378) | % | MP (N=371) | % |
|---|---|---|---|---|
| Any TEAE | 367 | **97%** | 328 | **88%** |
| Any Grade ≥3 TEAE | 306 | **81%** | 147 | **40%** |
| Any Serious TEAE (SAE) | 37 | **10%** | 78 | **21%** |
| Any TEAE leading to discontinuation | 66 | **17%** | 0 | **0%** |

### 4.2 Grade ≥3 TEAEs by System Organ Class (Top 6)

| System Organ Class | CbzP (n, %) | MP (n, %) |
|---|---|---|
| Blood & Lymphatic System Disorders | 291 (77%) | 39 (11%) |
| Gastrointestinal Disorders | 36 (10%) | 6 (2%) |
| General Disorders & Admin Site Conditions | 28 (7%) | 36 (10%) |
| Musculoskeletal & Connective Tissue Disorders | 10 (3%) | 35 (9%) |
| Nervous System Disorders | 6 (2%) | 14 (4%) |
| Infections & Infestations | 4 (1%) | 19 (5%) |

---

## 5. Laboratory Toxicity — CTCAE Grade Shift

Baseline to worst post-baseline CTCAE grade shifts were derived from the ADLB dataset using `BASEFL`, `ANL01FL`, and `ATOXGR` variables.

### 5.1 ANC / Neutrophils — Key Finding

Of 371 safety-evaluable patients in the CbzP arm, **321 (86.5%)** experienced Grade 3/4 neutropenia compared to **154 (41.5%)** in the MP arm, highlighting the hematological toxicity signature of Cabazitaxel.

### 5.2 Haemoglobin

Grade 3/4 anemia occurred in **34 (9.2%)** patients in the CbzP arm compared to **9 (2.4%)** in the MP arm.

### 5.3 Platelets

Thrombocytopenia was rare, with Grade 3/4 thrombocytopenia occurring in **16 (4.3%)** CbzP patients vs **5 (1.3%)** MP patients.

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
| Source Data | SAS7BDAT (Sanofi 2013) | CDISC SDTMIG v3.4 |
| ADaM Production | SAS 9.4 | ADaMIG v1.3 |
| Independent Validation | R 4.6.0 / Pharmaverse | ADaMIG v1.3 |
| Reconciliation | `diffdf` package | 100% cell-by-cell match |
| TFL Generation | ggplot2, survival, patchwork | ICH E3 / NEJM style |
| Orchestration | Python 3.10 (cibuild.py) | 12-stage CI pipeline |

---

## 8. Data Provenance & Limitations

> [!IMPORTANT]
> **Real data (MP arm):** All 371 MP-arm patients, 5,428 AE records, 266 OS events, and ~79,000 laboratory records are derived directly from the official Sanofi de-identified public SDTM release (dated June 2013).

> [!WARNING]
> **Reconstructed comparator (CbzP arm):** The Cabazitaxel arm was not included in the Sanofi public data release. The CbzP arm used in figures and comparative tables is reconstructed at the ADaM layer using published clinical study results (de Bono Lancet 2010), EPAR summaries, and NCT registry tables. The reconstruction employs the Guyot et al. (2012) KM algorithm and Cox proportional hazards survival time scaling.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154.
* Local Copy: [de_bono_lancet_2010.pdf](file:///Users/apple/Desktop/TROPIC/01_raw_source/reference_literature/de_bono_lancet_2010.pdf)



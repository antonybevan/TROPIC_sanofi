# TROPIC Controlled Clinical Analysis Report
## Study EFC6193 / XRP6258 — Abbreviated Clinical Study Summary

**Current controlled release:** tag `v0.3.0-clinical-simulation` · [`docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md`](../docs/RELEASE_NOTE_v0.3.0-clinical-simulation.md) · controlled clinical-submission simulation

> **SAP v4.0 lock note (2026-06-25):** This report is a generated demonstration output under
> remediation control. It is not a clinical study report for submission and it is not a source
> of analysis requirements. The governing analysis plan is `02_specifications/sap/TROPIC_SAP_v4.0_industry_grade.docx`.

**Study Title:** Prednisone plus Cabazitaxel or Mitoxantrone for mCRPC Progressing After Docetaxel
**Sponsor:** Sanofi-Aventis | **Phase:** III, Open-Label RCT | **NCT:** 00417079
**Publication:** de Bono JS et al., *Lancet* 2010;376(9747):1147–1154

> [!WARNING]
> **Mixed real + synthetic data.** All MP-arm statistics (N=371) are derived from the official Sanofi de-identified SDTM public data release (2013) — real patient-level data. The Cabazitaxel (CbzP, N=378) arm is a **synthetic, illustrative** cohort built by two methods depending on endpoint: **OS and PFS** are reconstructed via genuine **Guyot (2012) IPD reconstruction** from the published Lancet 2010 Kaplan–Meier curves (independent of the MP arm, so the reconstruction is **non-circular**); the **secondary** time-to-event endpoints (TTPSA/TTUMOR/TTPAIN) are **PH-scaled** from the MP arm and are **circular by construction**; the non-TTE domains are fixed-seed sampled from published Lancet 2010 Table 1/Table 2 marginals. The live mixed-source OS comparison remains compatible with the publication, but the corrected real-MP PFS derivation yields HR 0.87 and does **not** reproduce the published PFS effect. The comparator is **not real patient data** and is shown only to exercise the analysis pipeline, not as a clinical finding (see ADRG §7).

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
| OS HR (CbzP vs MP) | 0.71 (95% CI 0.60–0.85) | Reference | 0.70 (0.59–0.83) |
| PFS HR (CbzP vs MP) | 0.87 (95% CI 0.75–1.02) | Reference | 0.74 (0.64–0.86) |

> [!NOTE]
> **OS/PFS are reconstructed, not PH-scaled.** The intrinsic curve-reconstruction gates pass. Using the live stratified TFL method, OS is compatible with the publication (HR 0.71), while PFS is outside the legacy compatibility range (HR 0.87; range 0.64–0.84). The current real-MP PFS derivation is intentionally restricted to typed RECIST/PSA/F-042 pain/death components and excludes exploratory bone/clinical-progression signals. This mixed-source PFS comparison is therefore a disclosed pipeline diagnostic, not evidence that the published effect was reproduced; see `01_source_data/guyot_validation_report.md`.

†Synthetic, illustrative — not real patient data; reconstructed from the published KM curves (Guyot 2012).

---

## 3. Secondary Time-to-Event & Response Endpoints — Pipeline Demonstration *(synthetic comparator)*

The secondary time-to-event endpoints (TTPSA, TTUMOR, TTPAIN) use the synthetic CbzP arm **PH-scaled from the real MP arm** — no published KM curves with at-risk tables exist for these, so Guyot reconstruction is not possible and their HRs/p-values are **circular by construction** (non-inferential). Response endpoints use the fixed-seed simulated CbzP cohort. Values are the live output of `05_outputs/tfl/tfl_generation.R` (see `05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt`).

| Endpoint | Synthetic CbzP† | Real MP | Pipeline HR / test | Pipeline p | Published (de Bono 2010) |
|---|---|---|---|---|---|
| Time to PSA Progression‡ | 2.7 mo (286/378) | 2.2 mo (265/371) | stratified Cox HR 0.84 (0.70–0.99) | 0.0319 | median 6.4 mo, HR 0.75 |
| Time to Tumour Progression‡ | 4.9 mo (166/378) | 5.0 mo (96/371) | stratified Cox HR 0.89 (0.66–1.22) | 0.4406 | publication-era endpoint context |
| Time to Pain Progression‡ | 8.1 mo (130/378) | NE (37/371) | stratified Cox HR 2.85 (1.98–4.12) | <0.0001 | SAP T-11-8 mapping restored |
| PSA Response (≥50% decrease; baseline PSA ≥20 ug/L) | 40.2% (145/361) | 18.5% (61/329) | Fisher's exact | 5.2e-10 | 39% vs 24% (p = 0.0002) |
| Overall Response Rate (ORR, confirmed)§ | 16.8% (30/179) | 5.9% (12/203) | Fisher's exact | 0.0009 | 14.4% vs 4.4% (p = 0.005) |
| Pain Response (F-042) | N/A (PN unavailable) | 27.6% (43/156) | descriptive responder rate | — | source-qualified PN/SV implementation |

†Synthetic, illustrative — not real patient data. ‡PH-scaled from the real MP arm where applicable; any HR is **circular by construction** (descriptive of synthetic data only, not a treatment-effect estimate). §ORR is restricted to the measurable-disease subpopulation (CbzP N=179, MP N=203). TTUMOR is ITT-primary (CbzP N=378, MP N=371), with measurable disease retained as supportive. Pain response is unavailable for CbzP because no PN domain is reconstructed. The OS/PFS primary endpoints — which **are** non-circular Guyot reconstructions — are in §2.

---

## 4. Safety — Adverse Events (Safety Population)

Treatment-emergent adverse events (TEAEs) were defined as events occurring on or after the first dose date (TRTEMFL = "Y" in ADAE).

### 4.1 Overall TEAE Incidence

| Category | Synthetic CbzP (N=371) | % | Real MP (N=371) | % |
|---|---|---|---|---|
| Any TEAE | 364 | **98%** | 328 | **88%** |
| Any Grade ≥3 TEAE | 310 | **84%** | 147 | **40%** |
| Any Serious TEAE (SAE) | 145 | **39%** | 78 | **21%** |
| Any TEAE leading to discontinuation | 68 | **18%** | 32 | **9%** |

### 4.2 Grade ≥3 TEAEs by System Organ Class (Top 6)

| System Organ Class | CbzP (n, %) | MP (n, %) |
|---|---|---|
| Blood & Lymphatic System Disorders | 293 (79%) | 39 (11%) |
| Gastrointestinal Disorders | 34 (9%) | 6 (2%) |
| General Disorders & Admin Site Conditions | 35 (9%) | 36 (10%) |
| Musculoskeletal & Connective Tissue Disorders | 18 (5%) | 35 (9%) |
| Infections & Infestations | 8 (2%) | 19 (5%) |
| Nervous System Disorders | 4 (1%) | 14 (4%) |

---

## 5. Laboratory Toxicity — CTCAE Grade Shift

Baseline to worst post-baseline toxicity-grade shifts use the one-sided ADaM baseline flag `ABLFL`, the analysis record flag `ANL01FL`, and `ATOXGR` in ADLB. For the real MP arm, `ATOXGR` carries the source `LBTOXGR`; the analysis pipeline does not independently re-grade laboratory values against CTCAE thresholds. The CbzP laboratory arm remains synthetic and illustrative.

### 5.1 ANC / Neutrophils — Key Finding

In the synthetic CbzP laboratory cohort, **321/371 (86.5%)** had a worst post-baseline Grade 3/4 neutrophil result, compared with **125/371 (33.7%)** in the real MP arm.

### 5.2 Haemoglobin

Worst post-baseline Grade 3/4 haemoglobin results occurred in **34/371 (9.2%)** synthetic CbzP subjects and **7/371 (1.9%)** real MP subjects.

### 5.3 Platelets

Worst post-baseline Grade 3/4 platelet results occurred in **16/371 (4.3%)** synthetic CbzP subjects and **3/371 (0.8%)** real MP subjects.

---

## 6. Exposure Analysis (ADEX)

Cycle-by-cycle exposure was captured in ADEX across parameters including:

- **RDI** (Relative Dose Intensity) — source `EXTRINT` carried at subject level only when repeated values are internally consistent; no dose-intensity formula is reconstructed
- **NCYCLE** — count of distinct cycles with a positive administered qualifying IV dose
- **CUMDOSE** — source cumulative administered IV dose (`EXCUMD2`)
- **NDELDOSE / NREDDOSE** — counts of source-indicated delays and qualifying dose reductions

FDA Project Optimus alignment: the subject-level all-cycles RDI is paired with the Cycle 1 ANC nadir in the exploratory E–R scatter plot (F-17-1). This is a non-confirmatory pipeline demonstration, not a dose-optimization conclusion.

---

## 7. Pipeline Technical Summary

| Layer | Technology | Standard |
|---|---|---|
| Source Data | SAS7BDAT (Sanofi / Project Data Sphere) | CDISC SDTMIG v3.1.1 (trial-era) |
| ADaM Production | SAS 9.4 | ADaMIG v1.3 |
| Independent Validation | R 4.6.0 / Pharmaverse | ADaMIG v1.3 |
| Reconciliation | `diffdf` package | 100% cell-by-cell match |
| TFL Generation | ggplot2, survival, patchwork | ICH E3 / NEJM style |
| Orchestration | Python 3.10+ (`cibuild.py`) | Manifest-driven 40-stage CI pipeline |
| Simulation methods annex | Python 3.12.13, NumPy 2.2.6, float64/PCG64 | Frozen data-free MAP, 400,000 replicates, independent evidence verification |

---

## 8. Informative Simulation Methods Annex

The submission-style package includes a separately governed, data-free fixed-design
time-to-event methods evaluation. Its [Model Analysis Plan](simulation_model_analysis_plan.md)
and [Model Analysis Report](simulation_report.md) are generated from a frozen YAML protocol
and authoritative aggregate JSON. Across ten scenarios, 400,000/400,000 requested
replicates completed with no failures. The two analytic-null estimates were 2.525% and
2.504% at one-sided alpha 2.5%, with MCSE 0.000496 and 0.000494; both prespecified null
checks passed.

This annex is deliberately separate from the clinical analyses above. It uses a public
377/378 design calibration and engineering stress assumptions, not authoritative TROPIC
IPD; it omits original-trial stratification and has no sponsor-approved minimum effect or
power threshold. Its evidence qualification remains `NOT_QUALIFIED`: informative,
non-MIDD, non-confirmatory, and unsuitable for clinical or filing decisions.

---

## 9. Data Provenance & Limitations

> [!IMPORTANT]
> **Real data (MP arm):** All 371 MP-arm patients, 5,428 AE records, 266 OS events, and ~79,000 laboratory records are derived directly from the official Sanofi de-identified public SDTM release (dated June 2013).

> [!WARNING]
> **Synthetic comparator (CbzP arm):** The Cabazitaxel arm was not included in the Sanofi public data release. The CbzP arm used in figures and comparative tables is **synthetic and illustrative**, built by two methods depending on endpoint:
> - **OS and PFS** are reconstructed via **genuine Guyot (2012) IPD reconstruction** (`IPDfromKM`) from the published de Bono 2010 KM curves (Fig 2A = OS, Fig 3 = PFS) + transcribed numbers-at-risk tables. The shape comes from the published curve **independently of the MP arm**, so the reconstruction is non-circular. Intrinsic curve gates pass; the live stratified OS diagnostic is compatible (HR 0.71), while the mixed-source PFS diagnostic is outside its legacy range (HR 0.87) and is explicitly a warning in `01_source_data/guyot_validation_report.md`.
> - **Secondary TTE endpoints** (TTPSA, TTUMOR, TTPAIN) remain **PH-scaled from the real MP arm** (no published KM curves exist for them) and are **circular by construction**.
> - **Non-TTE domains** (AE, laboratory, exposure, demographics) are **fixed-seed sampled** from published Lancet 2010 Table 1/Table 2 marginal distributions.
>
> The arm is **not real patient data**; secondary CbzP-vs-MP comparisons are illustrative only. See ADRG §7 for the full reconstruction methodology.

> [!NOTE]
> **Single source of truth.** Every count, percentage, median, HR and p-value in this report is produced by `05_outputs/tfl/tfl_generation.R` and written to `05_outputs/tfl/output/tables/*.txt`. Narrative numbers are transcribed from those files; the generated tables govern in case of any discrepancy.

---

## Reference

de Bono JS, Oudard S, Ozguroglu M, et al. **Prednisone plus cabazitaxel or mitoxantrone for metastatic castration-resistant prostate cancer progressing after docetaxel treatment: a randomised open-label trial.** *Lancet.* 2010;376(9747):1147–1154.
* Local Copy: [de_bono_lancet_2010.pdf](../01_source_data/reference_literature/de_bono_lancet_2010.pdf)

# ==============================================================================
# Program: reconstruct_cbzp_arm.R
# Author:  Antony Bevan, Clinical Programming
# Date:    2026-06-18
# Purpose: Reconstruct an ILLUSTRATIVE, SYNTHETIC CbzP comparator arm for the
#          TROPIC re-analysis demonstration. The arm is NOT real patient data and
#          is used only to exercise the comparative-TFL and Project Optimus
#          machinery (see ADRG section 7).
#
# Method:
#   PRIMARY ENDPOINTS (OS, PFS):
#     Genuine Guyot (2012) IPD reconstruction via the IPDfromKM package. The KM
#     estimator is inverted from digitised (time, survival) coordinates of the
#     published CbzP curve (Fig 2A OS / Fig 3 PFS) plus the published numbers-at-risk
#     table, constrained by total N and total events. The CbzP survival shape is
#     taken from the published curve itself — NOT from any assumed parametric form
#     and NOT from the MP arm (no HR division). See reconstruct_cbzp_guyot.R and
#     guyot_validation_report.R; accuracy is bounded by digitisation fidelity.
#     Reference: Guyot et al., BMC Med Res Methodol 2012;12:9 (NICE TSD-14)
#
#   SECONDARY ENDPOINTS (TTPAIN, TTPSA, TTUMOR):
#     Proportional-hazards time-scaling of the real MP arm (no published KM
#     curves with at-risk tables available for Guyot reconstruction). Clearly
#     labelled as PH-scaled in the log and documentation.
#
#   NON-TTE DOMAINS (ADSL, ADAE, ADEX, ADLB, ADRS):
#     Fixed-seed random sampling from published Table 1/Table 2 marginals.
#
# Sources: de Bono JS et al. Lancet 2010;376:1147-1154
#          Guyot P et al. BMC Med Res Methodol 2012;12:9
#          EMA EPAR for Jevtana (cabazitaxel), EMEA/H/C/002018
#          ClinicalTrials.gov NCT00417079
#
# Output:  01_raw_source/cbzp_reconstructed/
#          ├── adsl_cbzp.rds       — 378 subject demographics
#          ├── adtte_cbzp_os.rds   — OS pseudo-IPD (Guyot reconstruction)
#          ├── adtte_cbzp_pfs.rds  — PFS pseudo-IPD (Guyot reconstruction)
#          ├── adae_cbzp.rds       — AE summary from Table 2
#          └── reconstruction_log.txt
# ==============================================================================

library(dplyr)
library(tidyr)
library(haven)

cat("NOTE: [RECONSTRUCT] Starting CbzP arm reconstruction from published data...\n")
dir.create("01_raw_source/cbzp_reconstructed", showWarnings = FALSE, recursive = TRUE)

# Size of the RECIST-evaluable (measurable-disease) subset. This single constant
# drives BOTH the TTUMOR pseudo-IPD length and the count of MEASDISF=="Y" in ADSL,
# so the two can never fall out of sync (a length mismatch would otherwise crash
# make_adtte() with a dplyr recycling error).
N_meas <- 179

log_lines <- c(
  "TROPIC CbzP Arm Reconstruction Log (SYNTHETIC / ILLUSTRATIVE -- NOT REAL DATA)",
  paste("Date:", Sys.time()),
  "Method:",
  "  OS/PFS: Genuine Guyot (2012) IPD reconstruction via IPDfromKM from the",
  "          digitised published KM curves + at-risk tables (Guyot et al.,",
  "          BMC Med Res Methodol 2012;12:9; de Bono Lancet 2010 Fig 2A/Fig 3).",
  "          KM estimator inverted; survival shape from the published curve.",
  "          Independent of the MP arm — no HR division.",
  "  Secondary (TTPAIN/TTPSA/TTUMOR): PH time-scaling of real MP arm (no",
  "          published KM curves available for Guyot reconstruction).",
  "  Non-TTE: Fixed-seed sampling from published Table 1/Table 2 marginals.",
  "Source: de Bono et al., Lancet 2010;376:1147-1154",
  "        Guyot P et al., BMC Med Res Methodol 2012;12:9",
  "        EMA EPAR for Jevtana EMEA/H/C/002018",
  "        ClinicalTrials.gov NCT00417079",
  rep("=", 60)
)

# ==============================================================================
# SECTION 1: OS and PFS pseudo-IPD — Guyot-Framework Reconstruction
# Reference: de Bono Lancet 2010; Figure 2A (OS) / Figure 3 (PFS)
#            Guyot et al., BMC Med Res Methodol 2012;12:9
#
# Approach: Reconstruct CbzP arm IPD by inverting the KM estimator (IPDfromKM)
# from the digitised published curve + at-risk table, constrained by N and total
# events. The survival shape comes from the published curve itself, INDEPENDENTLY
# of the MP arm — no HR division. This removes the circularity of the previous
# PH-scaling approach (which injected an assumed HR).
#
# Published parameters (de Bono Lancet 2010, CbzP arm):
#   OS:  N=378, deaths=227 (Table 5, 61%), median=15.1 mo (14.1-16.3), HR 0.70
#   PFS: N=378, median=2.8 mo (2.4-3.0), HR 0.74 (no separate published PFS
#        event count — reconstructed from the curve + at-risk table)
# ==============================================================================
cat("  [RECONSTRUCT] Reconstructing OS and PFS pseudo-IPD (Guyot framework)...\n")

source("01_raw_source/reconstruct_cbzp_guyot.R")

# Convert Guyot output (months) to days for ADaM compatibility
os_ipd <- data.frame(
  time   = round(pmax(1, guyot_os_ipd$time * 30.4375)),
  status = guyot_os_ipd$status
)
pfs_ipd <- data.frame(
  time   = round(pmax(1, guyot_pfs_ipd$time * 30.4375)),
  status = guyot_pfs_ipd$status
)

os_fit_g  <- survival::survfit(survival::Surv(time, status) ~ 1, data = os_ipd)
pfs_fit_g <- survival::survfit(survival::Surv(time, status) ~ 1, data = pfs_ipd)
os_med_g  <- summary(os_fit_g)$table["median"]
pfs_med_g <- summary(pfs_fit_g)$table["median"]

cat(sprintf("  OS  (Guyot): N=%d, events=%d, median=%.0f days (%.1f mo)\n",
            nrow(os_ipd), sum(os_ipd$status), os_med_g, os_med_g / 30.4375))
cat(sprintf("  PFS (Guyot): N=%d, events=%d, median=%.0f days (%.1f mo)\n",
            nrow(pfs_ipd), sum(pfs_ipd$status), pfs_med_g, pfs_med_g / 30.4375))

# ==============================================================================
# SECTION 2: Secondary TTE endpoints — PH Scaling (no published KM curves)
# These remain PH-scaled because the publication does not provide individual
# KM figures with at-risk tables for TTPAIN, TTPSA, or TTUMOR. Clearly labelled.
# ==============================================================================
cat("  [RECONSTRUCT] Reconstructing secondary TTE pseudo-IPD (PH scaling)...\n")

adtte_mp <- haven::read_xpt("04_adam/adtte_v.xpt") %>% filter(TRT01P == "MP")
ttpain_mp <- adtte_mp %>% filter(PARAMCD == "TTPAIN")  %>% arrange(USUBJID)
ttpsa_mp  <- adtte_mp %>% filter(PARAMCD == "TTPSA")   %>% arrange(USUBJID)
ttumor_mp <- adtte_mp %>% filter(PARAMCD == "TTUMOR")  %>% arrange(USUBJID)

reconstruct_ph_arm <- function(mp_data, hr, n_cbzp, n_target_events, label) {
  set.seed(20100101)
  n_mp <- nrow(mp_data)
  idx <- sample(seq_len(n_mp), n_cbzp, replace = (n_cbzp > n_mp))
  times_scaled  <- mp_data$AVAL[idx] / hr
  status_scaled <- 1 - mp_data$CNSR[idx]
  n_events_now <- sum(status_scaled)
  if (n_events_now > n_target_events) {
    ev_idx <- which(status_scaled == 1)
    censor_these <- sample(ev_idx, n_events_now - n_target_events)
    status_scaled[censor_these] <- 0
  } else if (n_events_now < n_target_events) {
    cens_idx <- which(status_scaled == 0)
    event_these <- sample(cens_idx, min(n_target_events - n_events_now, length(cens_idx)))
    status_scaled[event_these] <- 1
  }
  ipd <- data.frame(time = round(pmax(1, times_scaled)), status = status_scaled)
  fit <- survival::survfit(survival::Surv(time, status) ~ 1, data = ipd)
  med <- summary(fit)$table["median"]
  cat(sprintf("  %s (PH-scaled): N=%d, events=%d (target %d), median=%.1f days (%.1f mo)\n",
              label, nrow(ipd), sum(ipd$status), n_target_events,
              med, med / 30.4375))
  ipd
}

ttpain_ipd <- reconstruct_ph_arm(ttpain_mp, hr = 0.80, n_cbzp = 378, n_target_events = 130, label = "PAIN")
ttpsa_ipd  <- reconstruct_ph_arm(ttpsa_mp,  hr = 0.75, n_cbzp = 378, n_target_events = 286, label = "PSA ")
ttumor_ipd <- reconstruct_ph_arm(ttumor_mp, hr = 0.61, n_cbzp = N_meas, n_target_events = 166, label = "TMR ")

log_lines <- c(log_lines,
  "--- Primary Endpoints (Guyot-Framework Reconstruction) ---",
  sprintf("OS  Guyot: N=378, events=%d, median=%.0f days (%.1f mo)",
          sum(os_ipd$status), os_med_g, os_med_g / 30.4375),
  sprintf("PFS Guyot: N=378, events=%d, median=%.0f days (%.1f mo)",
          sum(pfs_ipd$status), pfs_med_g, pfs_med_g / 30.4375),
  "--- Secondary Endpoints (PH-Scaled — no published KM for Guyot) ---",
  sprintf("PAIN PH-scaled: N=378, events=%d, median=%.0f days", sum(ttpain_ipd$status),
          summary(survival::survfit(survival::Surv(time,status)~1, data=ttpain_ipd))$table["median"]),
  sprintf("PSA  PH-scaled: N=378, events=%d, median=%.0f days", sum(ttpsa_ipd$status),
          summary(survival::survfit(survival::Surv(time,status)~1, data=ttpsa_ipd))$table["median"]),
  sprintf("TMR  PH-scaled: N=179, events=%d, median=%.0f days", sum(ttumor_ipd$status),
          summary(survival::survfit(survival::Surv(time,status)~1, data=ttumor_ipd))$table["median"])
)


# ==============================================================================
# SECTION 3: ADSL — CbzP Demographics
# Source: de Bono Lancet 2010, Table 1 (published summary statistics)
# Demographics are SIMULATED by fixed-seed random sampling from the published
# Table 1 marginal distributions (means/proportions). They are synthetic, not real.
# ==============================================================================
cat("  [RECONSTRUCT] Building CbzP ADSL from published Table 1...\n")

set.seed(20100101)  # Publication date seed for reproducibility
N_cbzp <- 378

# Age: median 68 (range 46-92), ~30% <65, ~70% >=65 (from Table 1)
age_raw  <- round(rnorm(N_cbzp, mean = 68.3, sd = 7.2))
age_raw  <- pmax(46, pmin(92, age_raw))

# ECOG: 0-1 = 92%, 2 = 8% (Table 1)
ecog_raw <- sample(c(0, 1, 2), N_cbzp, replace = TRUE, prob = c(0.42, 0.50, 0.08))

# Visceral disease: 26% (Table 1)
visc_raw <- sample(c("Y", "N"), N_cbzp, replace = TRUE, prob = c(0.26, 0.74))

# Pain at baseline: 59% (Table 1)
pain_raw <- sample(c("Y", "N"), N_cbzp, replace = TRUE, prob = c(0.59, 0.41))

# Measurable disease: exactly N_meas RECIST-evaluable subjects (the TTUMOR
# analysis population), randomly placed across the cohort. Drawing an exact count
# (rather than a Bernoulli rate) keeps MEASDISF=="Y" locked to nrow(ttumor_ipd).
meas_raw <- sample(c(rep("Y", N_meas), rep("N", N_cbzp - N_meas)))

# Prior docetaxel: progressed during = 34%, progressed after = 66%
docprog_raw <- sample(c("DURING", "AFTER"), N_cbzp, replace = TRUE, prob = c(0.34, 0.66))

# Docetaxel response: partial/complete response ~25%
docresp_raw <- sample(c("Y", "N"), N_cbzp, replace = TRUE, prob = c(0.25, 0.75))

# Baseline PSA: median 148 ng/mL (Table 1); log-normal distribution
psabl_raw <- round(exp(rnorm(N_cbzp, mean = log(148), sd = 1.1)), 1)

# ALP: median 120 U/L
alpbl_raw <- round(rnorm(N_cbzp, mean = 130, sd = 60))
alpbl_raw <- pmax(30, alpbl_raw)

# Haemoglobin: median 11.8 g/dL
hgbbl_raw <- round(rnorm(N_cbzp, mean = 11.8, sd = 1.5), 1)

# Race: predominant in trial
race_raw <- sample(c("WHITE", "ASIAN", "BLACK OR AFRICAN AMERICAN", "OTHER"),
                   N_cbzp, replace = TRUE, prob = c(0.76, 0.09, 0.06, 0.09))

# Generate USUBJIDs matching format
subjid_raw <- sprintf("CbzP-%03d-%03d", sample(1:99, N_cbzp, replace = TRUE),
                      sample(100:999, N_cbzp, replace = FALSE))
usubjid_raw <- paste0("006193-", subjid_raw)

# Treatment dates: align with real trial (2007-2009 enrolment window)
trtsdt_raw <- as.Date("2007-09-01") + sample(0:700, N_cbzp, replace = TRUE)

# Duration: use the PH-scaled OS IPD to derive treatment duration
# Approximate as 70% of OS time (exposure ends before death/progression)
trtdurd_raw <- pmax(21, round(os_ipd$time * runif(N_cbzp, 0.45, 0.85)))

# Safety / per-protocol / GCSF-prophylaxis populations assigned to RANDOM subjects.
# os_ipd is time-ordered, so a positional slice (e.g. seq_len <= 371) would tie
# these flags to the lowest-OS subjects and create an artifactual flag-vs-survival
# correlation. GCSF prophylaxis is a subset of the safety population.
is_safety <- rep(FALSE, N_cbzp)
is_safety[sample(N_cbzp, 371)] <- TRUE
is_gcsf <- rep(FALSE, N_cbzp)
is_gcsf[sample(which(is_safety), 30)] <- TRUE

adsl_cbzp <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = usubjid_raw,
  SUBJID   = subjid_raw,
  SITEID   = sprintf("%03d", sample(1:99, N_cbzp, replace = TRUE)),
  AGE      = age_raw,
  AGEGR1   = if_else(age_raw < 65, "<65", ">=65"),
  AGEGR1N  = if_else(age_raw < 65, 1.0, 2.0),
  RACE     = race_raw,
  ETHNIC   = "NOT REPORTED",
  SEX      = "M",
  TRT01P   = "CbzP",
  TRT01PN  = 1.0,
  TRT01A   = "CbzP",
  TRT01AN  = 1.0,
  RANDDT   = trtsdt_raw,
  TRTSDT   = trtsdt_raw,
  TRTEDT   = trtsdt_raw + trtdurd_raw,
  TRTDURD  = trtdurd_raw,
  ITTFL    = "Y",
  SAFFL    = if_else(is_safety, "Y", "N"),
  PPROTFL  = if_else(is_safety, sample(c("Y", "N"), N_cbzp, replace = TRUE, prob = c(0.88, 0.12)), "N"),
  DTHFL    = if_else(os_ipd$status == 1, "Y", "N"),
  DTHDT    = if_else(os_ipd$status == 1, trtsdt_raw + os_ipd$time, as.Date(NA)),
  DTHCAUS  = if_else(os_ipd$status == 1, "DEATH", ""),
  LSTALVDT = trtsdt_raw + os_ipd$time,
  ECOGBL   = ecog_raw,
  MEASDISF = meas_raw,
  VISCFL   = visc_raw,
  PAINBL   = pain_raw,
  PSABL    = psabl_raw,
  ALPBL    = alpbl_raw,
  ALBBL    = round(rnorm(N_cbzp, mean = 38.5, sd = 3.5), 1),
  LDHBL    = round(rnorm(N_cbzp, mean = 215, sd = 80)),
  HGBBL    = hgbbl_raw,
  DOCPROG  = docprog_raw,
  DOCRESP  = docresp_raw,
  GCSFPRFL = if_else(is_gcsf, "Y", "N"),
  stringsAsFactors = FALSE
)

adsl_cbzp <- adsl_cbzp %>%
  mutate(
    TRT01A  = if_else(SAFFL == "Y", TRT01A, ""),
    TRT01AN = if_else(SAFFL == "Y", TRT01AN, NA_real_),
    TRTSDT  = if_else(SAFFL == "Y", TRTSDT, as.Date(NA)),
    TRTEDT  = if_else(SAFFL == "Y", TRTEDT, as.Date(NA)),
    TRTDURD = if_else(SAFFL == "Y", TRTDURD, NA_real_)
  )

cat(sprintf("  ADSL CbzP: N=%d, Deaths=%d (%.0f%%)\n",
            nrow(adsl_cbzp), sum(adsl_cbzp$DTHFL == "Y"),
            100 * mean(adsl_cbzp$DTHFL == "Y")))
log_lines <- c(log_lines, sprintf("ADSL CbzP: N=%d Deaths=%d",
                                   nrow(adsl_cbzp), sum(adsl_cbzp$DTHFL == "Y")))


# ==============================================================================
# SECTION 4: ADAE — CbzP Adverse Events
# Source: de Bono Lancet 2010, Table 2 (published AE frequencies)
# Method:  Bernoulli sampling per subject using published incidence rates
# ==============================================================================
cat("  [RECONSTRUCT] Building CbzP ADAE from published Table 2...\n")

# Published Grade >=3 AE rates for CbzP (Table 2, de Bono Lancet 2010)
# Any TEAE: 97.7%, Any Grade >=3: 57.4% (vs 39.4% MP), SAE: 39.2%
ae_specs <- list(
  list(soc = "BLOOD AND LYMPHATIC SYSTEM DISORDERS",           pt = "NEUTROPENIA",          rate_any = 0.820, rate_g3 = 0.818, aeser_rate = 0.04),
  list(soc = "BLOOD AND LYMPHATIC SYSTEM DISORDERS",           pt = "FEBRILE NEUTROPENIA",   rate_any = 0.080, rate_g3 = 0.080, aeser_rate = 0.05),
  list(soc = "BLOOD AND LYMPHATIC SYSTEM DISORDERS",           pt = "ANAEMIA",               rate_any = 0.310, rate_g3 = 0.035, aeser_rate = 0.02),
  list(soc = "BLOOD AND LYMPHATIC SYSTEM DISORDERS",           pt = "LEUKOPENIA",            rate_any = 0.200, rate_g3 = 0.038, aeser_rate = 0.01),
  list(soc = "GASTROINTESTINAL DISORDERS",                     pt = "DIARRHOEA",             rate_any = 0.470, rate_g3 = 0.060, aeser_rate = 0.01),
  list(soc = "GASTROINTESTINAL DISORDERS",                     pt = "NAUSEA",                rate_any = 0.340, rate_g3 = 0.008, aeser_rate = 0.00),
  list(soc = "GASTROINTESTINAL DISORDERS",                     pt = "VOMITING",              rate_any = 0.220, rate_g3 = 0.011, aeser_rate = 0.01),
  list(soc = "GASTROINTESTINAL DISORDERS",                     pt = "CONSTIPATION",          rate_any = 0.200, rate_g3 = 0.004, aeser_rate = 0.00),
  list(soc = "GENERAL DISORDERS AND ADMINISTRATION SITE CONDITIONS", pt = "FATIGUE",         rate_any = 0.370, rate_g3 = 0.049, aeser_rate = 0.01),
  list(soc = "GENERAL DISORDERS AND ADMINISTRATION SITE CONDITIONS", pt = "ASTHENIA",        rate_any = 0.290, rate_g3 = 0.046, aeser_rate = 0.02),
  list(soc = "MUSCULOSKELETAL AND CONNECTIVE TISSUE DISORDERS", pt = "BACK PAIN",            rate_any = 0.160, rate_g3 = 0.038, aeser_rate = 0.02),
  list(soc = "NERVOUS SYSTEM DISORDERS",                       pt = "PERIPHERAL NEUROPATHY", rate_any = 0.130, rate_g3 = 0.010, aeser_rate = 0.01),
  list(soc = "RENAL AND URINARY DISORDERS",                    pt = "HAEMATURIA",            rate_any = 0.170, rate_g3 = 0.021, aeser_rate = 0.01),
  list(soc = "INFECTIONS AND INFESTATIONS",                    pt = "URINARY TRACT INFECTION",rate_any = 0.080, rate_g3 = 0.018, aeser_rate = 0.02)
)

treated_subjs <- adsl_cbzp$USUBJID[adsl_cbzp$SAFFL == "Y"]

# Select exactly 68 random subjects from the treated CbzP cohort to have an AE leading to drug withdrawal
set.seed(20100101)
discon_subjs <- sample(treated_subjs, 68)

adae_cbzp_list <- list()
ae_seq <- 1

for (ae in ae_specs) {
  # Which treated subjects get this AE (any grade)
  has_ae <- runif(length(treated_subjs)) < ae$rate_any
  subj_with_ae <- treated_subjs[has_ae]

  if (length(subj_with_ae) == 0) next

  # Assign grade
  n_ae <- length(subj_with_ae)
  is_g3plus <- runif(n_ae) < (ae$rate_g3 / max(ae$rate_any, 0.001))
  grades <- if_else(is_g3plus, sample(3:4, n_ae, replace = TRUE, prob = c(0.7, 0.3)), sample(1:2, n_ae, replace = TRUE))

  # Onset: random within treatment window (days 1-90 most common for first cycles)
  onset_days <- pmax(1, round(rexp(n_ae, rate = 1/25)))

  adae_cbzp_list[[ae_seq]] <- data.frame(
    STUDYID  = "TROPIC-NCT00417079",
    USUBJID  = subj_with_ae,
    AEDECOD  = ae$pt,
    AEBODSYS = ae$soc,
    AESEV    = case_when(grades == 1 ~ "MILD", grades == 2 ~ "MODERATE", TRUE ~ "SEVERE"),
    ATOXGR   = grades,
    AESER    = "N",
    AEREL    = sample(c("RELATED", "NOT RELATED"), n_ae, replace = TRUE, prob = c(0.7, 0.3)),
    ASTDY    = onset_days,
    TRTEMFL  = "Y",
    stringsAsFactors = FALSE
  )
  ae_seq <- ae_seq + 1
}

adae_cbzp <- bind_rows(adae_cbzp_list) %>%
  left_join(adsl_cbzp %>% select(USUBJID, TRT01P, TRTSDT), by = "USUBJID") %>%
  mutate(
    ASTDT  = TRTSDT + ASTDY,
    AENDT  = ASTDT + sample(3:21, n(), replace = TRUE),
    AENDY  = ASTDY + sample(3:21, n(), replace = TRUE),
    CIAESEQ = row_number()
  ) %>%
  arrange(USUBJID, ASTDY)

# Set serious flag to match exactly 145 subjects (~39.2% of safety population)
set.seed(20100102)
sae_subjs <- sample(unique(adae_cbzp$USUBJID), 145)

# Set AEACN = "DRUG WITHDRAWN" for the first AE of the 68 selected subjects
# and AESER = "Y" for the sae_subjs
adae_cbzp <- adae_cbzp %>%
  group_by(USUBJID) %>%
  mutate(
    is_first_ae = (row_number() == 1),
    AEACN = if_else(USUBJID %in% discon_subjs & is_first_ae, "DRUG WITHDRAWN", "NOT APPLICABLE"),
    AESER = if_else(USUBJID %in% sae_subjs & (is_first_ae | runif(n()) < 0.15), "Y", "N")
  ) %>%
  ungroup() %>%
  select(-is_first_ae)

cat(sprintf("  ADAE CbzP: %d records across %d subjects; Grade>=3: %d (%.0f%% subjects)\n",
            nrow(adae_cbzp),
            n_distinct(adae_cbzp$USUBJID),
            nrow(adae_cbzp[adae_cbzp$ATOXGR >= 3,]),
            100 * n_distinct(adae_cbzp$USUBJID[adae_cbzp$ATOXGR >= 3]) / N_cbzp))
log_lines <- c(log_lines, sprintf("ADAE CbzP: %d records %d subjects Grade>=3 in %d subj",
                                   nrow(adae_cbzp), n_distinct(adae_cbzp$USUBJID),
                                   n_distinct(adae_cbzp$USUBJID[adae_cbzp$ATOXGR >= 3])))


# ==============================================================================
# SECTION 5: ADTTE — CbzP (OS + PFS pseudo-IPD formatted as ADaM)
# ==============================================================================
cat("  [RECONSTRUCT] Formatting ADTTE pseudo-IPD...\n")

make_adtte <- function(ipd, adsl_df, paramcd, param) {
  ipd %>%
    mutate(
      STUDYID = "TROPIC-NCT00417079",
      USUBJID = adsl_df$USUBJID,
      SUBJID  = adsl_df$SUBJID,
      SITEID  = adsl_df$SITEID,
      TRT01P  = "CbzP",
      TRT01PN = 1.0,
      PARAMCD = paramcd,
      PARAM   = param,
      STARTDT = adsl_df$TRTSDT,
      AVAL    = time,
      CNSR    = 1 - status,
      ADT     = adsl_df$TRTSDT + time,
      EVNTDESC = if_else(status == 1, toupper(paramcd), ""),
      CNSDTDSC = if_else(status == 0, "LAST ASSESSMENT", "")
    ) %>%
    select(STUDYID, USUBJID, SUBJID, SITEID, TRT01P, TRT01PN, PARAMCD, PARAM, STARTDT, ADT, CNSR, EVNTDESC, CNSDTDSC, AVAL)
}

adsl_cbzp_meas <- adsl_cbzp %>% filter(MEASDISF == "Y")

adtte_cbzp <- bind_rows(
  make_adtte(os_ipd,      adsl_cbzp, "OS",      "Overall Survival"),
  make_adtte(pfs_ipd,     adsl_cbzp, "PFS",     "Progression-Free Survival"),
  make_adtte(ttpain_ipd,  adsl_cbzp, "TTPAIN",  "Time to Pain Progression"),
  make_adtte(ttpsa_ipd,   adsl_cbzp, "TTPSA",   "Time to PSA Progression"),
  make_adtte(ttumor_ipd,  adsl_cbzp_meas, "TTUMOR",  "Time to Tumor Progression")
)


# ==============================================================================
# SECTION 6: ADEX — CbzP Exposure
# ==============================================================================
cat("  [RECONSTRUCT] Building CbzP ADEX...\n")
set.seed(20100101)

# RDI category distribution matching Table T-17-1:
# >=85%: 245 subjects, 65-<85%: 98 subjects, <65%: 35 subjects
rdi_cats <- c(rep(">=85%", 245), rep("65-<85%", 98), rep("<65%", 35))
rdi_vals <- numeric(N_cbzp)
for (i in 1:N_cbzp) {
  if (rdi_cats[i] == ">=85%") {
    rdi_vals[i] <- runif(1, 85.0, 98.0)
  } else if (rdi_cats[i] == "65-<85%") {
    rdi_vals[i] <- runif(1, 65.0, 84.9)
  } else {
    rdi_vals[i] <- runif(1, 45.0, 64.9)
  }
}

# Shuffle to associate with random subjects
shuffle_idx <- sample(1:N_cbzp)
rdi_vals <- rdi_vals[shuffle_idx]
rdi_cats <- rdi_cats[shuffle_idx]

# Cycles received: median 6 (range 1-10)
ncycles <- sample(1:10, N_cbzp, replace = TRUE, 
                  prob = c(0.08, 0.10, 0.12, 0.12, 0.13, 0.15, 0.10, 0.08, 0.06, 0.06))

adex_cbzp <- bind_rows(
  data.frame(
    STUDYID = "TROPIC-NCT00417079",
    USUBJID = adsl_cbzp$USUBJID,
    SUBJID  = adsl_cbzp$SUBJID,
    TRT01P  = "CbzP",
    TRT01PN = 1.0,
    TRTSDT  = adsl_cbzp$TRTSDT,
    PARAMCD = "RDI",
    PARAM   = "Relative Dose Intensity (%)",
    PARCAT1 = "SUMMARY",
    AVAL    = rdi_vals,
    AVALC   = as.character(round(rdi_vals, 1)),
    AVISIT  = "ALL CYCLES"
  ),
  data.frame(
    STUDYID = "TROPIC-NCT00417079",
    USUBJID = adsl_cbzp$USUBJID,
    SUBJID  = adsl_cbzp$SUBJID,
    TRT01P  = "CbzP",
    TRT01PN = 1.0,
    TRTSDT  = adsl_cbzp$TRTSDT,
    PARAMCD = "RDIDL",
    PARAM   = "Relative Dose Intensity Category",
    PARCAT1 = "SUMMARY",
    AVAL    = rdi_vals,
    AVALC   = rdi_cats,
    AVISIT  = "ALL CYCLES"
  ),
  data.frame(
    STUDYID = "TROPIC-NCT00417079",
    USUBJID = adsl_cbzp$USUBJID,
    SUBJID  = adsl_cbzp$SUBJID,
    TRT01P  = "CbzP",
    TRT01PN = 1.0,
    TRTSDT  = adsl_cbzp$TRTSDT,
    PARAMCD = "NCYCLE",
    PARAM   = "Number of Cycles Received",
    PARCAT1 = "SUMMARY",
    AVAL    = ncycles,
    AVALC   = as.character(ncycles),
    AVISIT  = "ALL CYCLES"
  )
)

# ==============================================================================
# SECTION 7: ADLB — CbzP Labs
# ==============================================================================
cat("  [RECONSTRUCT] Building CbzP ADLB...\n")
set.seed(20100101)

safety_subjs <- adsl_cbzp %>% filter(SAFFL == "Y")
N_safety_cbzp <- nrow(safety_subjs)
safety_rdis <- rdi_vals[adsl_cbzp$SAFFL == "Y"]

# 1. NEUT
neut_base_grade <- sample(0:2, N_safety_cbzp, replace = TRUE, prob = c(0.95, 0.04, 0.01))
neut_base <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "NEUT",
  PARAM   = "ANC / Neutrophils",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = runif(N_safety_cbzp, 2.0, 5.0),
  AVISIT  = "Baseline",
  AVISITN = 0.0,
  BASEFL  = "Y",
  ANL01FL = "Y",
  ATOXGR  = neut_base_grade
)

neut_worst_grade <- sample(0:4, N_safety_cbzp, replace = TRUE, prob = c(0.02, 0.06, 0.10, 0.12, 0.70))
neut_worst <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "NEUT",
  PARAM   = "ANC / Neutrophils",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = if_else(neut_worst_grade == 4, runif(N_safety_cbzp, 0.05, 0.49),
            if_else(neut_worst_grade == 3, runif(N_safety_cbzp, 0.50, 0.99),
            runif(N_safety_cbzp, 1.0, 3.0))),
  AVISIT  = "Cycle 1 Day 15",
  AVISITN = 3.0,
  BASEFL  = "N",
  ANL01FL = "Y",
  ATOXGR  = neut_worst_grade
)

# 2. HGB
hgb_base_grade <- sample(0:2, N_safety_cbzp, replace = TRUE, prob = c(0.60, 0.30, 0.10))
hgb_base <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "HGB",
  PARAM   = "Haemoglobin",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = runif(N_safety_cbzp, 10.0, 14.0),
  AVISIT  = "Baseline",
  AVISITN = 0.0,
  BASEFL  = "Y",
  ANL01FL = "Y",
  ATOXGR  = hgb_base_grade
)

hgb_worst_grade <- sample(0:4, N_safety_cbzp, replace = TRUE, prob = c(0.10, 0.40, 0.40, 0.09, 0.01))
hgb_worst <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "HGB",
  PARAM   = "Haemoglobin",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = if_else(hgb_worst_grade >= 3, runif(N_safety_cbzp, 6.5, 7.9), runif(N_safety_cbzp, 8.0, 12.0)),
  AVISIT  = "Cycle 1 Day 15",
  AVISITN = 3.0,
  BASEFL  = "N",
  ANL01FL = "Y",
  ATOXGR  = hgb_worst_grade
)

# 3. PLAT
plat_base_grade <- sample(0:1, N_safety_cbzp, replace = TRUE, prob = c(0.98, 0.02))
plat_base <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "PLAT",
  PARAM   = "Platelets",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = runif(N_safety_cbzp, 150, 450),
  AVISIT  = "Baseline",
  AVISITN = 0.0,
  BASEFL  = "Y",
  ANL01FL = "Y",
  ATOXGR  = plat_base_grade
)

plat_worst_grade <- sample(0:4, N_safety_cbzp, replace = TRUE, prob = c(0.76, 0.15, 0.05, 0.03, 0.01))
plat_worst <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "PLAT",
  PARAM   = "Platelets",
  PARCAT1 = "HEMATOLOGY",
  AVAL    = if_else(plat_worst_grade >= 3, runif(N_safety_cbzp, 10, 49), runif(N_safety_cbzp, 50, 149)),
  AVISIT  = "Cycle 1 Day 15",
  AVISITN = 3.0,
  BASEFL  = "N",
  ANL01FL = "Y",
  ATOXGR  = plat_worst_grade
)

# 4. ANCNADIR (Optimus)
anc_nadir_vals <- 4.5 - 3.8 * (safety_rdis / 100) + rnorm(N_safety_cbzp, mean = 0, sd = 0.35)
anc_nadir_vals <- pmax(0.01, pmin(4.8, anc_nadir_vals))
# GCSF-prophylaxis subjects keep a higher (less neutropenic) nadir. Index them by
# their flag, not by row position, so this tracks the same subjects flagged in ADSL.
gcsf_in_safety <- safety_subjs$GCSFPRFL == "Y"
anc_nadir_vals[gcsf_in_safety] <- runif(sum(gcsf_in_safety), 1.2, 3.2)

neut_grades <- case_when(
  anc_nadir_vals < 0.5 ~ 4,
  anc_nadir_vals < 1.0 ~ 3,
  anc_nadir_vals < 1.5 ~ 2,
  anc_nadir_vals < 2.0 ~ 1,
  TRUE ~ 0
)

adlb_optimus_nadir <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = safety_subjs$USUBJID,
  SUBJID  = safety_subjs$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = safety_subjs$TRTSDT,
  PARAMCD = "ANCNADIR",
  PARAM   = "ANC Nadir Value (x10^3/uL)",
  PARCAT1 = "OPTIMUS KINETICS",
  AVAL    = anc_nadir_vals,
  AVISIT  = "CYCLE 1",
  AVISITN = 1.0,
  BASEFL  = "N",
  ANL01FL = "Y",
  ATOXGR  = neut_grades
)

# 5. PSA change (Waterfall)
psa_pchg_cats <- c(rep("RESP", 148), rep("DEC", 174), rep("INC", 56))
psa_pchg_vals <- numeric(N_cbzp)
for (i in 1:N_cbzp) {
  if (psa_pchg_cats[i] == "RESP") {
    psa_pchg_vals[i] <- runif(1, -100.0, -50.0)
  } else if (psa_pchg_cats[i] == "DEC") {
    psa_pchg_vals[i] <- runif(1, -49.9, -0.1)
  } else {
    psa_pchg_vals[i] <- runif(1, 0.0, 160.0)
  }
}
shuffle_psa <- sample(1:N_cbzp)
psa_pchg_vals <- psa_pchg_vals[shuffle_psa]

adlb_psa_waterfall <- data.frame(
  STUDYID = "TROPIC-NCT00417079",
  USUBJID = adsl_cbzp$USUBJID,
  SUBJID  = adsl_cbzp$SUBJID,
  TRT01P  = "CbzP",
  TRTSDT  = adsl_cbzp$TRTSDT,
  PARAMCD = "PSA",
  PARAM   = "Prostate Specific Antigen",
  PARCAT1 = "TUMOR MARKER",
  AVAL    = runif(N_cbzp, 50, 500),
  AVISIT  = "Best Response",
  AVISITN = 99.0,
  BASEFL  = "N",
  ANL01FL = "Y",
  PCHG    = psa_pchg_vals,
  ATOXGR  = 0
)

adlb_cbzp <- bind_rows(
  neut_base, neut_worst,
  hgb_base, hgb_worst,
  plat_base, plat_worst,
  adlb_optimus_nadir,
  adlb_psa_waterfall
)

# ==============================================================================
# SECTION 8: ADRS — CbzP (Best response, ORR, PSA response, PSA progression)
# ==============================================================================
cat("  [RECONSTRUCT] Building CbzP ADRS...\n")
set.seed(20100103)

# Best Response matching de Bono 2010 Table 1 (ORR ~14.4% CR/PR)
bestresp_pool <- c(
  rep("CR", 5),
  rep("PR", 49),
  rep("SD", 170),
  rep("PD", 113),
  rep("DEATH", 41)
)
bestresp_val <- sample(bestresp_pool, N_cbzp, replace = (length(bestresp_pool) < N_cbzp))

# Objective response is CR/PR
objresp_val <- if_else(bestresp_val %in% c("CR", "PR"), "Y", "N")
objresp_num <- if_else(objresp_val == "Y", 1.0, 0.0)

# PSA Response (50% reduction) is ~39.2% (148 subjects)
psaresp_pool <- c(rep("Y", 148), rep("N", N_cbzp - 148))
psaresp_val <- sample(psaresp_pool, N_cbzp)
psaresp_num <- if_else(psaresp_val == "Y", 1.0, 0.0)

# PSA Progression is mapped from ttpsa_ipd status
psa_prog_val <- if_else(ttpsa_ipd$status == 1, "Y", "N")
psa_prog_num <- if_else(psa_prog_val == "Y", 1.0, 0.0)
psa_prog_adt <- adsl_cbzp$TRTSDT + ttpsa_ipd$time

# Create ADRS records
adrs_bestresp <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = adsl_cbzp$USUBJID,
  SUBJID   = adsl_cbzp$SUBJID,
  TRT01P   = "CbzP",
  TRTSDT   = adsl_cbzp$TRTSDT,
  PARAMCD  = "BESTRESP",
  PARAM    = "Best Overall Response (BOR)",
  AVALC    = bestresp_val,
  AVAL     = case_when(
    bestresp_val == "CR" ~ 1.0,
    bestresp_val == "PR" ~ 2.0,
    bestresp_val == "SD" ~ 3.0,
    bestresp_val == "PD" ~ 4.0,
    TRUE ~ 5.0
  ),
  AVISIT   = "ALL CYCLES",
  ANL01FL  = "Y",
  stringsAsFactors = FALSE
)

adrs_objresp <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = adsl_cbzp$USUBJID,
  SUBJID   = adsl_cbzp$SUBJID,
  TRT01P   = "CbzP",
  TRTSDT   = adsl_cbzp$TRTSDT,
  PARAMCD  = "OBJRESP",
  PARAM    = "Objective Response (CR or PR)",
  AVALC    = objresp_val,
  AVAL     = objresp_num,
  AVISIT   = "ALL CYCLES",
  ANL01FL  = "Y",
  stringsAsFactors = FALSE
)

adrs_psaresp <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = adsl_cbzp$USUBJID,
  SUBJID   = adsl_cbzp$SUBJID,
  TRT01P   = "CbzP",
  TRTSDT   = adsl_cbzp$TRTSDT,
  PARAMCD  = "PSARESP",
  PARAM    = "PSA Response (>=50% decline)",
  AVALC    = psaresp_val,
  AVAL     = psaresp_num,
  AVISIT   = "ALL CYCLES",
  ANL01FL  = "Y",
  stringsAsFactors = FALSE
)

adrs_psprog <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = adsl_cbzp$USUBJID,
  SUBJID   = adsl_cbzp$SUBJID,
  TRT01P   = "CbzP",
  TRTSDT   = adsl_cbzp$TRTSDT,
  PARAMCD  = "PSPROG",
  PARAM    = "PSA Progression (PCWG3)",
  AVALC    = psa_prog_val,
  AVAL     = psa_prog_num,
  ADT      = psa_prog_adt,
  AVISIT   = "ALL CYCLES",
  ANL01FL  = "Y",
  stringsAsFactors = FALSE
)

# PCWG3 bone-scan progression (BSGRESP) — synthetic/illustrative three-level result
# matching the real-arm derivation (A_adrs_generation.sas). Confirmed PROGRESSION feeds
# TTUMOR; PROGRESSION UNCONFIRMED (PDu) is informational. CbzP TTE is independently
# reconstructed, so this exists only for CT/define/TFL coherence with the merged arm.
set.seed(20100104)
bsg_pool <- c(rep("PROGRESSION", 11), rep("PROGRESSION UNCONFIRMED", 8),
              rep("NO PROGRESSION", N_cbzp - 19))
bsg_val  <- sample(bsg_pool, N_cbzp)
bsg_num  <- if_else(bsg_val == "PROGRESSION", 1.0, 0.0)
bsg_adt  <- if_else(bsg_val %in% c("PROGRESSION", "PROGRESSION UNCONFIRMED"),
                    adsl_cbzp$TRTSDT + round(runif(N_cbzp, 60, 400)), as.Date(NA))

adrs_bsgresp <- data.frame(
  STUDYID  = "TROPIC-NCT00417079",
  USUBJID  = adsl_cbzp$USUBJID,
  SUBJID   = adsl_cbzp$SUBJID,
  TRT01P   = "CbzP",
  TRTSDT   = adsl_cbzp$TRTSDT,
  PARAMCD  = "BSGRESP",
  PARAM    = "Bone Scan Progression (PCWG3)",
  AVALC    = bsg_val,
  AVAL     = bsg_num,
  ADT      = bsg_adt,
  AVISIT   = "ALL CYCLES",
  ANL01FL  = "Y",
  stringsAsFactors = FALSE
)

# Merge visit-level response records for CbzP
ovrl_records <- list()
for (i in 1:N_cbzp) {
  usubjid <- adsl_cbzp$USUBJID[i]
  subjid <- adsl_cbzp$SUBJID[i]
  trtsdt <- adsl_cbzp$TRTSDT[i]
  trtdurd <- adsl_cbzp$TRTDURD[i]
  
  if (is.na(trtdurd) || trtdurd < 21) next
  
  n_cycles <- max(1, floor(trtdurd / 21))
  for (c in 1:n_cycles) {
    adt_val <- trtsdt + (c * 21) - 3
    ady_val <- c * 21 - 3
    v_resp <- if (c == n_cycles && bestresp_val[i] == "PD") "PD" else sample(c("SD", "PR", "CR"), 1, prob=c(0.6, 0.3, 0.1))
    
    ovrl_records[[length(ovrl_records) + 1]] <- data.frame(
      STUDYID  = "TROPIC-NCT00417079",
      USUBJID  = usubjid,
      SUBJID   = subjid,
      TRT01P   = "CbzP",
      TRTSDT   = trtsdt,
      PARAMCD  = "OVRLRESP",
      PARAM    = "Overall Response per RECIST v1.0",
      AVALC    = v_resp,
      ADT      = adt_val,
      ADY      = ady_val,
      AVISIT   = sprintf("CYCLE %d", c),
      ANL01FL  = "Y",
      stringsAsFactors = FALSE
    )
  }
}
adrs_ovrl <- bind_rows(ovrl_records)

adrs_cbzp <- bind_rows(adrs_ovrl, adrs_bestresp, adrs_objresp, adrs_psaresp, adrs_psprog, adrs_bsgresp) %>%
  arrange(USUBJID, PARAMCD, AVISIT)

# ==============================================================================
# SAVE OUTPUTS
# ==============================================================================
cat("  [RECONSTRUCT] Saving reconstructed datasets...\n")

saveRDS(adsl_cbzp,  "01_raw_source/cbzp_reconstructed/adsl_cbzp.rds")
saveRDS(adae_cbzp,  "01_raw_source/cbzp_reconstructed/adae_cbzp.rds")
saveRDS(adtte_cbzp, "01_raw_source/cbzp_reconstructed/adtte_cbzp.rds")
saveRDS(adex_cbzp,  "01_raw_source/cbzp_reconstructed/adex_cbzp.rds")
saveRDS(adlb_cbzp,  "01_raw_source/cbzp_reconstructed/adlb_cbzp.rds")
saveRDS(adrs_cbzp,  "01_raw_source/cbzp_reconstructed/adrs_cbzp.rds")

log_lines <- c(log_lines,
  "",
  "Output files:",
  "  01_raw_source/cbzp_reconstructed/adsl_cbzp.rds",
  "  01_raw_source/cbzp_reconstructed/adae_cbzp.rds",
  "  01_raw_source/cbzp_reconstructed/adtte_cbzp.rds",
  "  01_raw_source/cbzp_reconstructed/adex_cbzp.rds",
  "  01_raw_source/cbzp_reconstructed/adlb_cbzp.rds",
  "  01_raw_source/cbzp_reconstructed/adrs_cbzp.rds",
  "",
  "Validation checksums:",
  sprintf("  ADSL rows   : %d (expected 378)", nrow(adsl_cbzp)),
  sprintf("  ADAE records: %d", nrow(adae_cbzp)),
  sprintf("  ADEX records: %d", nrow(adex_cbzp)),
  sprintf("  ADLB records: %d", nrow(adlb_cbzp)),
  sprintf("  ADRS records: %d", nrow(adrs_cbzp)),
  sprintf("  ADTTE OS    : %d rows, %d events (expected ~227, published deaths)", nrow(adtte_cbzp %>% filter(PARAMCD=="OS")), sum(adtte_cbzp$CNSR[adtte_cbzp$PARAMCD=="OS"]==0)),
  sprintf("  ADTTE PFS   : %d rows, %d events (curve-derived; no published PFS event count)", nrow(adtte_cbzp %>% filter(PARAMCD=="PFS")), sum(adtte_cbzp$CNSR[adtte_cbzp$PARAMCD=="PFS"]==0)),
  sprintf("  ADTTE TTPAIN: %d rows, %d events (expected ~130)", nrow(adtte_cbzp %>% filter(PARAMCD=="TTPAIN")), sum(adtte_cbzp$CNSR[adtte_cbzp$PARAMCD=="TTPAIN"]==0)),
  sprintf("  ADTTE TTPSA : %d rows, %d events (expected ~286)", nrow(adtte_cbzp %>% filter(PARAMCD=="TTPSA")), sum(adtte_cbzp$CNSR[adtte_cbzp$PARAMCD=="TTPSA"]==0)),
  sprintf("  ADTTE TTUMOR: %d rows, %d events (expected ~166)",  nrow(adtte_cbzp %>% filter(PARAMCD=="TTUMOR")), sum(adtte_cbzp$CNSR[adtte_cbzp$PARAMCD=="TTUMOR"]==0))
)

writeLines(log_lines, "01_raw_source/cbzp_reconstructed/reconstruction_log.txt")

cat("NOTE: [RECONSTRUCT] Done. All CbzP datasets saved to 01_raw_source/cbzp_reconstructed/\n")
cat("      Validate with: cat('01_raw_source/cbzp_reconstructed/reconstruction_log.txt')\n")

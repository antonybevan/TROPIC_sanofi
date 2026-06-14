# Program: v_adlb_validation.R | Version: 3.5.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-06-12
# Standard: ADaMIG v1.3 BDS | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADLB.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("03_validation_r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADLB Validation script...\n")

# Helper function for SAS-style half-up rounding to match put(..., 8.2)
sas_round <- function(x, d) {
  posneg <- sign(x)
  z <- abs(x) * 10^d
  z <- z + 0.5 + 1e-9
  z <- floor(z)
  z <- z / 10^d
  return(z * posneg)
}

# Load real validation ADSL and staging LB
adsl <- read_xpt("04_adam/adsl_v.xpt")
lb <- readRDS("01_raw_source/real_sdtm/staging/lb.rds")

# Standardize header variables
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT)

df_lb <- lb %>%
  select(-any_of("STUDYID")) %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  mutate(
    lbdtc_clean = trimws(LBDTC),
    lbdt = if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", lbdtc_clean), ymd(lbdtc_clean, quiet = TRUE), as.Date(NA)),
    lbdy = as.numeric(lbdt - TRTSDT + 1),
    avals = as.numeric(LBSTRESN)
  ) %>%
  filter(!is.na(avals))

# Assign Windows
df_windows <- df_lb %>%
  mutate(
    PARAMCD = LBTESTCD,
    PARAM = LBTEST,
    PARAMN = case_when(
      LBTESTCD == "NEUT" ~ 1.0,
      LBTESTCD == "PSA" ~ 2.0,
      LBTESTCD == "HGB" ~ 3.0,
      TRUE ~ 4.0
    ),
    PARCAT1 = if_else(LBTESTCD == "PSA", "TUMOR MARKER", "HEMATOLOGY"),
    AVAL = avals,
    AVALC = LBORRES,
    
    AVISITN = case_when(
      is.na(lbdy) | lbdy <= W_BL_HI ~ 0.0,
      lbdy >= W_C1D1_LO  & lbdy <= W_C1D1_HI  ~ 1.0,
      lbdy >= W_C1D8_LO  & lbdy <= W_C1D8_HI  ~ 2.0,
      lbdy >= W_C1D15_LO & lbdy <= W_C1D15_HI ~ 3.0,
      lbdy >= W_C2D1_LO  & lbdy <= W_C2D1_HI  ~ 4.0,
      lbdy >= W_C2D8_LO  & lbdy <= W_C2D8_HI  ~ 5.0,
      lbdy >= W_C3D1_LO  & lbdy <= W_C3D1_HI  ~ 6.0,
      TRUE ~ 99.0
    ),
    
    AVISIT = case_when(
      AVISITN == 0.0 ~ "Baseline",
      AVISITN == 1.0 ~ "Cycle 1 Day 1 Pre-dose",
      AVISITN == 2.0 ~ "Cycle 1 Day 8",
      AVISITN == 3.0 ~ "Cycle 1 Day 15",
      AVISITN == 4.0 ~ "Cycle 2 Day 1 Pre-dose",
      AVISITN == 5.0 ~ "Cycle 2 Day 8",
      AVISITN == 6.0 ~ "Cycle 3 Day 1 Pre-dose",
      TRUE ~ "Unscheduled"
    ),
    
    AWDIST = case_when(
      AVISITN == 0.0 ~ abs(lbdy - (-1)),
      AVISITN == 1.0 ~ abs(lbdy - 1),
      AVISITN == 2.0 ~ abs(lbdy - 8),
      AVISITN == 3.0 ~ abs(lbdy - 15),
      AVISITN == 4.0 ~ abs(lbdy - 22),
      AVISITN == 5.0 ~ abs(lbdy - 29),
      AVISITN == 6.0 ~ abs(lbdy - 43),
      TRUE ~ as.numeric(NA)
    ),
    
    ATOXGR = as.numeric(LBTOXGR)
  )

# Calculate Baselines - sort by LBSEQ to break date ties stably matching SAS
df_baselines <- df_windows %>%
  filter(AVISITN == 0.0) %>%
  arrange(USUBJID, PARAMCD, is.na(lbdt), desc(lbdt), LBSEQ) %>%
  group_by(USUBJID, PARAMCD) %>%
  summarise(
    BASE = first(AVAL),
    BASEC = first(AVALC),
    BTOXGR = first(ATOXGR),
    .groups = "drop"
  )

# Merge Baselines and calculate changes
df_base_merged <- df_windows %>%
  left_join(df_baselines, by = c("USUBJID", "PARAMCD")) %>%
  mutate(
    CHG = AVAL - BASE,
    PCHG = (CHG / BASE) * 100
  )

# Determine ANL01FL and BASEFL - include LBSEQ as final tiebreaker
df_anl01 <- df_base_merged %>%
  arrange(USUBJID, PARAMCD, AVISITN, desc(is.na(AWDIST)), AWDIST, desc(ATOXGR), desc(is.na(lbdt)), lbdt, LBSEQ) %>%
  group_by(USUBJID, PARAMCD, AVISITN) %>%
  mutate(
    ANL01FL = if_else(AVISITN != 99.0 & row_number() == 1, "Y", "N"),
    BASEFL = if_else(AVISITN == 0.0, "Y", "N")
  ) %>%
  ungroup()

# Derive Project Optimus Parameters
# ANC Nadirs per cycle
df_anc_records <- df_anl01 %>%
  filter(PARAMCD == "NEUT" & lbdy > 0 & ANL01FL == "Y") %>%
  mutate(
    cycle = case_when(
      lbdy >= 39 ~ 3.0,
      lbdy >= 18 ~ 2.0,
      TRUE ~ 1.0
    )
  )

df_anc_nadir <- df_anc_records %>%
  group_by(USUBJID, cycle) %>%
  summarise(
    nadir_val = min(AVAL),
    nadir_dy = min(lbdy[AVAL == nadir_val]),
    .groups = "drop"
  )

# ANC Recovery latencies per cycle
df_anc_rec <- df_anc_records %>%
  inner_join(df_anc_nadir %>% select(USUBJID, cycle, nadir_dy), by = c("USUBJID", "cycle")) %>%
  filter(lbdy > nadir_dy & AVAL >= ANC_RECOVERY_THRESHOLD) %>%
  group_by(USUBJID, cycle) %>%
  summarise(
    rec_dy = min(lbdy),
    .groups = "drop"
  )

# Reformat Optimus records into BDS
df_optimus_nadir <- df_anc_nadir %>%
  inner_join(header, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "ANCNADIR", PARAM = "ANC Nadir Value (x10^3/uL)", PARCAT1 = "OPTIMUS KINETICS",
    ADT = as.Date(NA),
    AVAL = nadir_val, AVALC = sprintf("%.2f", sas_round(nadir_val, 2)), AVISIT = paste("CYCLE", cycle), AVISITN = cycle,
    ANL01FL = "Y", BASEFL = "N", lbdy = nadir_dy
  )

df_optimus_rec <- df_anc_rec %>%
  inner_join(df_anc_nadir %>% select(USUBJID, cycle, nadir_dy), by = c("USUBJID", "cycle")) %>%
  inner_join(header, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "ANCRECDY", PARAM = "Days from ANC Nadir to Recovery", PARCAT1 = "OPTIMUS KINETICS",
    ADT = as.Date(NA),
    AVAL = rec_dy - nadir_dy, AVALC = as.character(rec_dy - nadir_dy), AVISIT = paste("CYCLE", cycle), AVISITN = cycle,
    ANL01FL = "Y", BASEFL = "N", lbdy = rec_dy
  )

# Combine and Sort
adlb_final <- bind_rows(
  df_anl01 %>% select(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT, PARAMCD, PARAM, PARAMN, PARCAT1,
    ADT = lbdt, AVAL, AVALC, LBNRLO = LBORNRLO, LBNRHI = LBORNRHI, LBNRIND, AVISIT, AVISITN, AWDIST, ATOXGR,
    BASE, BASEC, BTOXGR, CHG, PCHG, ANL01FL, BASEFL, lbdy
  ),
  df_optimus_nadir,
  df_optimus_rec
)

# Sort and Save

adlb_final <- adlb_final %>% arrange(USUBJID, PARAMCD, AVISITN, lbdy)

# Assertions and Error Guards (QC-03)
if (nrow(adlb_final) == 0) {
  stop("ERROR: [VALIDATION] ADLB output dataset is empty!")
}
if (nrow(adlb_final %>% filter(PARAMCD == "ANCNADIR")) == 0) {
  stop("ERROR: [VALIDATION] ADLB Project Optimus nadir records are missing!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats (lbdy -> LBDY)
names(adlb_final) <- toupper(names(adlb_final))
for (.dv in names(adlb_final)) if (inherits(adlb_final[[.dv]], "Date")) attr(adlb_final[[.dv]], "format.sas") <- "DATE9."
write_xpt_v(adlb_final, "04_adam/adlb_v.xpt", domain = "ADLB")

cat("NOTE: [VALIDATION] Wrote validation ADLB: 04_adam/adlb_v.xpt\n")

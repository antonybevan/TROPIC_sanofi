# Program: v_adcm_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: ADaMIG v1.3 OCCDS v1.1 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADCM.

library(dplyr)
library(haven)
library(lubridate)

cat("NOTE: [VALIDATION] Starting ADCM Validation script...\n")

# Load real validation ADSL and staging CM
adsl <- read_xpt("04_adam/adsl_v.xpt")
cm <- readRDS("01_raw_source/real_sdtm/staging/cm.rds")

# Standardize header variables
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT)

# Ingest and clean concomitant medications
df_cm <- cm %>%
  select(-any_of("STUDYID")) %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  mutate(
    cmstdt = ymd(substring(CMSTDTC, 1, 10)),
    cmendt = ymd(substring(CMENDTC, 1, 10)),
    cmstdy = as.numeric(cmstdt - TRTSDT + 1)
  )

# Calculate NACTDT (New Anti-Cancer Therapy Start Date)
# Defined as the earliest start date of a Post-Treatment Anti-Cancer Drug Therapy
df_nact <- df_cm %>%
  filter(CMCAT == "POST TREATMENT ANTI-CANCER DRUG THERAPY" & !is.na(cmstdt)) %>%
  group_by(USUBJID) %>%
  summarise(
    nactdt = min(cmstdt, na.rm = TRUE),
    .groups = "drop"
  )

# Join NACTDT back and build ADCM
adcm <- df_cm %>%
  left_join(df_nact, by = "USUBJID") %>%
  mutate(
    GCSFFL = if_else(CMDECOD %in% c("FILGRASTIM", "PEGFILGRASTIM", "LENOGRASTIM"), "Y", "N"),
    
    # Prophylaxis: administered within 3 days of treatment start or specified as prophylaxis
    GCSFPRFL = if_else(GCSFFL == "Y" & (CMINDC == "PROPHYLAXIS" | (!is.na(cmstdy) & cmstdy >= -3 & cmstdy <= 3)), "Y", "N"),
    
    NACTFL = if_else(CMCAT == "POST TREATMENT ANTI-CANCER DRUG THERAPY", "Y", "N"),
    PREDNFL = if_else(CMDECOD %in% c("PREDNISONE", "PREDNISOLONE"), "Y", "N"),
    TRTEMFL = if_else(!is.na(cmstdt) & cmstdt >= TRTSDT, "Y", "N")
  ) %>%
  select(
    STUDYID, USUBJID, CMDECOD, CMCAT, CMINDC, CMSTDT = cmstdt, CMENDT = cmendt, 
    CMTRT, CMSTDY = cmstdy, GCSFFL, GCSFPRFL, NACTFL, NACTDT = nactdt, PREDNFL, TRTEMFL
  )

# Sort and Save
adcm <- adcm %>% arrange(USUBJID, CMSTDT, CMDECOD)
library(xportr)

# Assertions and Error Guards (QC-03)
if (nrow(adcm) == 0) {
  stop("ERROR: [VALIDATION] ADCM output dataset is empty!")
}

xportr_write(adcm, "04_adam/adcm_v.xpt", domain = "ADCM")

cat("NOTE: [VALIDATION] Wrote validation ADCM: 04_adam/adcm_v.xpt\n")

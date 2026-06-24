# Program: v_adcm_validation.R | Version: 2.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-05-23
# Standard: ADaMIG v1.3 OCCDS v1.0 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADCM.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("03_validation_r/config_study.R")

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
    cmstdtc_clean = trimws(CMSTDTC),
    cmendtc_clean = trimws(CMENDTC),
    is_full_stdt = grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", cmstdtc_clean),
    is_full_endt = grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", cmendtc_clean),
    cmstdt = if_else(is_full_stdt, ymd(cmstdtc_clean, quiet = TRUE), as.Date(NA)),
    cmendt = if_else(is_full_endt, ymd(cmendtc_clean, quiet = TRUE), as.Date(NA)),
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
    GCSFPRFL = if_else(
      GCSFFL == "Y" &
        (CMINDC == "PROPHYLAXIS" | (!is.na(cmstdy) & cmstdy >= -3 & cmstdy <= 3)),
      "Y", "N"
    ),

    NACTFL = if_else(CMCAT == "POST TREATMENT ANTI-CANCER DRUG THERAPY", "Y", "N"),
    PREDNFL = if_else(CMDECOD %in% c("PREDNISONE", "PREDNISOLONE"), "Y", "N"),
    TRTEMFL = if_else(!is.na(cmstdt) & cmstdt >= TRTSDT, "Y", "N")
  ) %>%
  select(
    STUDYID, USUBJID, CMDECOD, CMCAT, CMINDC, ASTDT = cmstdt, AENDT = cmendt,
    CMTRT, ASTDY = cmstdy, GCSFFL, GCSFPRFL, NACTFL, NACTDT = nactdt, PREDNFL, TRTEMFL
  )

# Sort and Save

# Sort and Save
adcm <- adcm %>% arrange(USUBJID, ASTDT, CMDECOD)

# Assertions and Error Guards (QC-03)
if (nrow(adcm) == 0) {
  stop("ERROR: [VALIDATION] ADCM output dataset is empty!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adcm) <- toupper(names(adcm))
for (.dv in names(adcm)) if (inherits(adcm[[.dv]], "Date")) attr(adcm[[.dv]], "format.sas") <- "DATE9."
write_xpt_v(adcm, "04_adam/adcm_v.xpt", domain = "ADCM")

cat("NOTE: [VALIDATION] Wrote validation ADCM: 04_adam/adcm_v.xpt\n")

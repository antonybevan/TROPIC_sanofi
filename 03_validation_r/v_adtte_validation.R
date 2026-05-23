# Program: v_adtte_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: ADaMIG v1.3 BDS-TTE | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADTTE.

library(jsonlite)
library(dplyr)
library(haven)
library(lubridate)

cat("NOTE: [VALIDATION] Starting ADTTE Validation script...\n")

# Load validation datasets (previously generated or subjects source)
adsl_subj <- read_xpt("04_adam/adsl_v.xpt")
adrs <- read_xpt("04_adam/adrs_v.xpt")
adcm <- read_xpt("04_adam/adcm_v.xpt")
adae <- read_xpt("04_adam/adae_v.xpt")

# Base demographics and survival hooks
df_adsl <- adsl_subj

# Calculate first PD dates
df_pd <- adrs %>%
  filter((PARAMCD == "OVRLRESP" & AVALC == "PD") |
         (PARAMCD == "BSGRESP" & AVALC == "PROGRESSION") |
         (PARAMCD == "PSPROG" & AVALC == "Y")) %>%
  group_by(USUBJID) %>%
  summarise(
    pd_dt = min(ymd(ADT)),
    .groups = "drop"
  )

# Calculate first Serious AE dates
df_sae <- adae %>%
  filter(AESER == "Y" & TRTEMFL == "Y") %>%
  group_by(USUBJID) %>%
  summarise(
    sae_dt = min(ymd(ASTDT)),
    .groups = "drop"
  )

# Calculate NACTDT dates
df_nact <- adcm %>%
  filter(!is.na(NACTDT)) %>%
  group_by(USUBJID) %>%
  summarise(
    nactdt = min(ymd(NACTDT)),
    .groups = "drop"
  )

# ------------------------------------------------------------------------------
# PARAMETER 1: OVERALL SURVIVAL
# ------------------------------------------------------------------------------
os <- df_adsl %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "OS", PARAM = "Overall Survival", STARTDT = RANDDT,
    ADT = if_else(DTHFL == "Y", DTHDT, LSTALVDT),
    CNSR = if_else(DTHFL == "Y", 0.0, 1.0),
    EVNTDESC = if_else(DTHFL == "Y", "DEATH", ""),
    CNSDTDSC = if_else(DTHFL == "Y", "", "LAST KNOWN ALIVE DATE"),
    AVAL = as.numeric(ADT - STARTDT + 1)
  )

# ------------------------------------------------------------------------------
# PARAMETER 2: TIME TO FIRST SERIOUS AE (TTOS)
# ------------------------------------------------------------------------------
ttos <- df_adsl %>%
  left_join(df_sae, by = "USUBJID") %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "TTOS", PARAM = "Time to First Serious AE", STARTDT = TRTSDT,
    ADT = if_else(!is.na(sae_dt), sae_dt, LSTALVDT),
    CNSR = if_else(!is.na(sae_dt), 0.0, 1.0),
    EVNTDESC = if_else(!is.na(sae_dt), "SERIOUS ADVERSE EVENT", ""),
    CNSDTDSC = if_else(!is.na(sae_dt), "", "LAST CONCOMITANT EVALUATION"),
    AVAL = as.numeric(ADT - STARTDT + 1)
  )

# ------------------------------------------------------------------------------
# PARAMETER 3: PROGRESSION-FREE SURVIVAL (PFS)
# ------------------------------------------------------------------------------
pfs <- df_adsl %>%
  left_join(df_pd, by = "USUBJID") %>%
  left_join(df_nact, by = "USUBJID") %>%
  rowwise() %>%
  mutate(
    STARTDT = RANDDT,
    PARAMCD = "PFS",
    PARAM = "Progression Free Survival",
    # Hierarchy checking
    pd_found = !is.na(pd_dt),
    nact_found = !is.na(nactdt),
    
    ADT = case_when(
      pd_found & (!nact_found | nactdt >= pd_dt) ~ pd_dt,
      pd_found & nact_found & nactdt < pd_dt ~ nactdt - days(1),
      !pd_found & DTHFL == "Y" & (!nact_found | nactdt >= DTHDT) ~ DTHDT,
      !pd_found & DTHFL == "Y" & nact_found & nactdt < DTHDT ~ nactdt - days(1),
      TRUE ~ if_else(nact_found, nactdt - days(1), LSTALVDT)
    ),
    
    CNSR = case_when(
      pd_found & (!nact_found | nactdt >= pd_dt) ~ 0.0,
      !pd_found & DTHFL == "Y" & (!nact_found | nactdt >= DTHDT) ~ 0.0,
      TRUE ~ 1.0
    ),
    
    EVNTDESC = case_when(
      CNSR == 0.0 & pd_found ~ "TUMOR OR PSA PROGRESSION",
      CNSR == 0.0 & !pd_found ~ "DEATH",
      TRUE ~ ""
    ),
    
    CNSDTDSC = case_when(
      CNSR == 1.0 & nact_found ~ "NEW ANTI-CANCER THERAPY START",
      CNSR == 1.0 & !nact_found & !pd_found & DTHFL != "Y" ~ "LAST EVALUABLE TUMOR ASSESSMENT",
      TRUE ~ ""
    ),
    
    AVAL = as.numeric(ADT - STARTDT + 1)
  ) %>%
  ungroup() %>%
  select(STUDYID, USUBJID, SUBJID, SITEID, TRT01P, TRT01PN, PARAMCD, PARAM, STARTDT, ADT, CNSR, EVNTDESC, CNSDTDSC, AVAL)

# Combine and save
adtte <- bind_rows(os, ttos, pfs) %>% arrange(USUBJID, PARAMCD)

# Force numeric types to double for haven compliance
adtte <- adtte %>%
  mutate(
    AVAL = as.numeric(AVAL),
    CNSR = as.numeric(CNSR)
  )

library(xportr)
xportr_write(adtte, "04_adam/adtte_v.xpt", domain = "ADTTE")
cat("NOTE: [VALIDATION] Wrote validation ADTTE: 04_adam/adtte_v.xpt\n")

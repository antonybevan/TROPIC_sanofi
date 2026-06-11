# Program: v_adtte_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: ADaMIG v1.3 BDS-TTE | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADTTE.

library(jsonlite)
library(dplyr)
library(haven)
library(lubridate)
library(tidyr)

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
    pd_dt = min(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

# Calculate first Serious AE dates
df_sae <- adae %>%
  filter(AESER == "Y" & TRTEMFL == "Y" & !is.na(ASTDT)) %>%
  group_by(USUBJID) %>%
  summarise(
    sae_dt = min(as.Date(ASTDT, origin = "1960-01-01")),
    .groups = "drop"
  )

# Calculate NACTDT dates
df_nact <- adcm %>%
  filter(!is.na(NACTDT)) %>%
  group_by(USUBJID) %>%
  summarise(
    nactdt = min(as.Date(NACTDT, origin = "1960-01-01")),
    .groups = "drop"
  )

# ------------------------------------------------------------------------------
# PARAMETER 1: OVERALL SURVIVAL
# ------------------------------------------------------------------------------
os <- df_adsl %>%
  mutate(
    STARTDT = RANDDT,
    adt_temp = if_else(DTHFL == "Y", DTHDT, LSTALVDT),
    ADT = pmax(STARTDT, adt_temp)
  ) %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "OS", PARAM = "Overall Survival", STARTDT, ADT,
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
  mutate(
    STARTDT = TRTSDT,
    adt_temp = if_else(!is.na(sae_dt), sae_dt, LSTALVDT),
    ADT = pmax(STARTDT, adt_temp)
  ) %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "TTOS", PARAM = "Time to First Serious AE", STARTDT, ADT,
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
    
    adt_temp = case_when(
      pd_found & (!nact_found | nactdt >= pd_dt) ~ pd_dt,
      pd_found & nact_found & nactdt < pd_dt ~ nactdt - days(1),
      !pd_found & DTHFL == "Y" & (!nact_found | nactdt >= DTHDT) ~ DTHDT,
      !pd_found & DTHFL == "Y" & nact_found & nactdt < DTHDT ~ nactdt - days(1),
      TRUE ~ if_else(nact_found, nactdt - days(1), LSTALVDT)
    ),
    ADT = pmax(STARTDT, adt_temp),
    
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

# ------------------------------------------------------------------------------
# PARAMETER 4: TIME TO PAIN PROGRESSION (TTPAIN)
# ------------------------------------------------------------------------------
# Load staging pain data
pn <- readRDS("01_raw_source/real_sdtm/staging/pn.rds")

# Derive treatment start date per subject
df_ex_dt <- df_adsl %>%
  select(USUBJID, TRTSDT, RANDDT, LSTALVDT)

# Baseline pain logs
pn_trt <- pn %>%
  inner_join(df_ex_dt, by = "USUBJID") %>%
  mutate(
    pndtc_clean = trimws(PNDTC),
    PNDT = if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", pndtc_clean), ymd(pndtc_clean, quiet = TRUE), as.Date(NA)),
    PNSTRESN = as.numeric(PNSTRESN)
  )

baseline_pn <- pn_trt %>% filter(PNDT <= TRTSDT)

baseline_summary <- baseline_pn %>%
  group_by(USUBJID, PNTESTCD) %>%
  summarise(base_val = median(PNSTRESN, na.rm = TRUE), .groups = "drop") %>%
  pivot_wider(id_cols = USUBJID, names_from = PNTESTCD, values_from = base_val) %>%
  rename(base_ppi = PAININT, base_an = ANSCORE)

# Cycle-level pain logs
post_pn <- pn_trt %>%
  filter(PNDT > TRTSDT) %>%
  group_by(USUBJID, VISITNUM, VISIT, PNDT, PNTESTCD) %>%
  summarise(day_val = first(PNSTRESN), .groups = "drop") %>%
  group_by(USUBJID, VISITNUM, VISIT, PNTESTCD) %>%
  summarise(cycle_val = median(day_val, na.rm = TRUE),
            cycle_date = min(PNDT, na.rm = TRUE),
            .groups = "drop")

cycle_wide <- post_pn %>%
  pivot_wider(id_cols = c(USUBJID, VISITNUM, VISIT, cycle_date), names_from = PNTESTCD, values_from = cycle_val) %>%
  rename(cycle_ppi = PAININT, cycle_an = ANSCORE) %>%
  arrange(USUBJID, VISITNUM)

cycle_comp <- cycle_wide %>%
  left_join(baseline_summary, by = "USUBJID") %>%
  mutate(
    base_ppi = coalesce(base_ppi, 0),
    base_an = coalesce(base_an, 0),
    ppi_diff = cycle_ppi - base_ppi,
    an_diff = cycle_an - base_an,
    prog_trigger = if_else((!is.na(ppi_diff) & ppi_diff >= 2) | (!is.na(an_diff) & an_diff >= 10), 1, 0)
  )

prog_subjs <- cycle_comp %>%
  group_by(USUBJID) %>%
  mutate(
    next_trigger = lead(prog_trigger),
    is_prog = if_else(prog_trigger == 1 & (next_trigger == 1 | is.na(next_trigger)), 1, 0)
  ) %>%
  filter(is_prog == 1) %>%
  group_by(USUBJID) %>%
  summarise(prog_date = min(cycle_date), .groups = "drop")

# Last pain assessment date for censoring
censor_dates <- pn_trt %>%
  group_by(USUBJID) %>%
  summarise(last_pn_dt = max(PNDT, na.rm = TRUE), .groups = "drop")

ttpain <- df_adsl %>%
  left_join(prog_subjs, by = "USUBJID") %>%
  left_join(censor_dates, by = "USUBJID") %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "TTPAIN", PARAM = "Time to Pain Progression", STARTDT = RANDDT,
    
    adt_temp = case_when(
      !is.na(prog_date) ~ prog_date,
      !is.na(last_pn_dt) ~ last_pn_dt,
      TRUE ~ RANDDT
    ),
    ADT = pmax(STARTDT, adt_temp),
    
    CNSR = if_else(!is.na(prog_date), 0.0, 1.0),
    EVNTDESC = if_else(!is.na(prog_date), "PAIN PROGRESSION", ""),
    CNSDTDSC = if_else(!is.na(prog_date), "", if_else(!is.na(last_pn_dt), "LAST PAIN ASSESSMENT DATE", "NO PAIN ASSESSMENT")),
    AVAL = as.numeric(ADT - STARTDT + 1)
  )

# ------------------------------------------------------------------------------
# PARAMETER 5: TIME TO PSA PROGRESSION (TTPSA)
# ------------------------------------------------------------------------------
library(lubridate)
adrs_val <- read_xpt("04_adam/adrs_v.xpt")

psa_prog_subjs <- adrs_val %>%
  filter(PARAMCD == "PSPROG" & AVALC == "Y") %>%
  select(USUBJID, psa_prog_dt = ADT)

# Censoring: last available PSA test date
lb_val <- readRDS("01_raw_source/real_sdtm/staging/lb.rds")
colnames(lb_val) <- toupper(colnames(lb_val))

psa_censor_dates <- lb_val %>%
  filter(LBTESTCD == "PSA" & !is.na(LBSTRESN) & !is.na(LBDTC) & LBDTC != "") %>%
  mutate(
    lbdtc_clean = trimws(LBDTC),
    LBDT = suppressWarnings(if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", lbdtc_clean), ymd(lbdtc_clean, quiet = TRUE), as.Date(NA)))
  ) %>%
  filter(!is.na(LBDT)) %>%
  group_by(USUBJID) %>%
  summarise(last_psa_dt = max(LBDT, na.rm = TRUE), .groups = "drop")

ttpsa <- df_adsl %>%
  left_join(psa_prog_subjs, by = "USUBJID") %>%
  left_join(psa_censor_dates, by = "USUBJID") %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "TTPSA", PARAM = "Time to PSA Progression", STARTDT = TRTSDT,
    
    adt_temp = case_when(
      !is.na(psa_prog_dt) ~ psa_prog_dt,
      !is.na(last_psa_dt) ~ pmin(last_psa_dt, ymd("2009-09-25")),
      TRUE ~ pmin(LSTALVDT, ymd("2009-09-25"))
    ),
    ADT = pmax(STARTDT, adt_temp),
    
    CNSR = if_else(!is.na(psa_prog_dt), 0.0, 1.0),
    EVNTDESC = if_else(!is.na(psa_prog_dt), "PSA PROGRESSION", ""),
    CNSDTDSC = if_else(!is.na(psa_prog_dt), "", if_else(!is.na(last_psa_dt), "LAST PSA ASSESSMENT", "LAST KNOWN ALIVE DATE")),
    AVAL = as.numeric(ADT - STARTDT + 1)
  )

# ------------------------------------------------------------------------------
# PARAMETER 6: TIME TO TUMOR PROGRESSION (TTUMOR)
# ------------------------------------------------------------------------------
tumor_prog_subjs <- adrs_val %>%
  filter(PARAMCD == "OVRLRESP" & AVALC == "PD") %>%
  group_by(USUBJID) %>%
  summarise(tumor_prog_dt = min(ADT), .groups = "drop")

tumor_censor_dates <- adrs_val %>%
  filter(PARAMCD == "OVRLRESP" & !is.na(ADT)) %>%
  group_by(USUBJID) %>%
  summarise(last_tumor_dt = max(ADT), .groups = "drop")

tttumor <- df_adsl %>%
  filter(MEASDISF == "Y") %>%
  left_join(tumor_prog_subjs, by = "USUBJID") %>%
  left_join(tumor_censor_dates, by = "USUBJID") %>%
  transmute(
    STUDYID = "TROPIC-NCT00417079", USUBJID, SUBJID, SITEID, TRT01P, TRT01PN,
    PARAMCD = "TTUMOR", PARAM = "Time to Tumor Progression", STARTDT = TRTSDT,
    
    adt_temp = case_when(
      !is.na(tumor_prog_dt) ~ tumor_prog_dt,
      !is.na(last_tumor_dt) ~ pmin(last_tumor_dt, ymd("2009-09-25")),
      TRUE ~ TRTSDT
    ),
    ADT = pmax(STARTDT, adt_temp),
    
    CNSR = if_else(!is.na(tumor_prog_dt), 0.0, 1.0),
    EVNTDESC = if_else(!is.na(tumor_prog_dt), "TUMOR PROGRESSION", ""),
    CNSDTDSC = if_else(!is.na(tumor_prog_dt), "", if_else(!is.na(last_tumor_dt), "LAST TUMOR ASSESSMENT", "NO POST-BASELINE ASSESSMENT")),
    AVAL = as.numeric(ADT - STARTDT + 1)
  )

# Combine and save
adtte <- bind_rows(os, ttos, pfs, ttpain, ttpsa, tttumor) %>%
  select(STUDYID, USUBJID, SUBJID, SITEID, TRT01P, TRT01PN, PARAMCD, PARAM, STARTDT, ADT, CNSR, EVNTDESC, CNSDTDSC, AVAL)

adtte <- adtte %>% arrange(USUBJID, PARAMCD)

# Force numeric types to double for haven compliance
adtte <- adtte %>%
  mutate(
    AVAL = as.numeric(AVAL),
    CNSR = as.numeric(CNSR)
  )

library(xportr)

# Assertions and Error Guards (QC-03)
if (nrow(adtte) == 0) {
  stop("ERROR: [VALIDATION] ADTTE output dataset is empty!")
}
# Assert completeness of all 6 parameters (VAL-05)
expected_params <- c("OS", "PFS", "TTPAIN", "TTPSA", "TTUMOR", "TTOS")
missing_params <- setdiff(expected_params, unique(adtte$PARAMCD))
if (length(missing_params) > 0) {
  stop(paste("ERROR: [VALIDATION] ADTTE is missing mandatory parameters:", paste(missing_params, collapse = ", ")))
}

xportr_write(adtte, "04_adam/adtte_v.xpt", domain = "ADTTE")
cat("NOTE: [VALIDATION] Wrote validation ADTTE: 04_adam/adtte_v.xpt\n")

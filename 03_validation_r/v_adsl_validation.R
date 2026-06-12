# Program: v_adsl_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: ADaMIG v1.3 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADSL.

library(dplyr)
library(haven)
library(lubridate)
library(tidyr)
library(xportr)
source("03_validation_r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADSL Validation script...\n")

# Load real staging tables
dm <- readRDS("01_raw_source/real_sdtm/staging/dm.rds")
ex <- readRDS("01_raw_source/real_sdtm/staging/ex.rds")
ds <- readRDS("01_raw_source/real_sdtm/staging/ds.rds")
vs <- readRDS("01_raw_source/real_sdtm/staging/vs.rds")
lb <- readRDS("01_raw_source/real_sdtm/staging/lb.rds")
ls <- readRDS("01_raw_source/real_sdtm/staging/ls.rds")
pn <- readRDS("01_raw_source/real_sdtm/staging/pn.rds")
cm <- readRDS("01_raw_source/real_sdtm/staging/cm.rds")

# Derive treatment start and end dates
df_ex <- ex %>%
  filter(!is.na(EXSTDTC)) %>%
  mutate(
    exstdt = ymd(if_else(!is.na(EXSTDTC) & nchar(EXSTDTC) >= 10, substring(EXSTDTC, 1, 10), NA_character_)),
    exendt = ymd(if_else(!is.na(EXENDTC) & nchar(EXENDTC) >= 10, substring(EXENDTC, 1, 10), NA_character_))
  ) %>%
  group_by(USUBJID) %>%
  summarise(
    TRTSDT = min(exstdt, na.rm = TRUE),
    TRTEDT = max(exendt, na.rm = TRUE),
    TRTDURD = as.numeric(TRTEDT - TRTSDT + 1),
    .groups = "drop"
  )

# Calculate survival details from Disposition
df_death <- ds %>%
  filter(DSDECOD %in% c("DEATH", "DEAD")) %>%
  left_join(dm %>% select(USUBJID, RFSTDTC), by = "USUBJID") %>%
  mutate(
    dth_dt = ymd(substring(RFSTDTC, 1, 10), quiet = TRUE) + (DSSTWK - 1) * 7
  ) %>%
  group_by(USUBJID) %>%
  summarise(
    DTHFL = "Y",
    DTHDT = min(dth_dt, na.rm = TRUE),
    DTHCAUS = first(DSTERM),
    .groups = "drop"
  )

df_alive <- ds %>%
  left_join(dm %>% select(USUBJID, RFSTDTC), by = "USUBJID") %>%
  mutate(
    lstalv_dt = ymd(substring(RFSTDTC, 1, 10), quiet = TRUE) + (DSSTWK - 1) * 7
  ) %>%
  group_by(USUBJID) %>%
  summarise(
    LSTALVDT = max(lstalv_dt, na.rm = TRUE),
    .groups = "drop"
  )

# 1. ECOGBL
df_ecog <- vs %>%
  filter(VSTESTCD == "ECOG" & VSBLFL == "Y") %>%
  group_by(USUBJID) %>%
  summarise(ECOGBL = first(VSSTRESN), .groups = "drop")

# 2. MEASDISF
df_meas <- ls %>%
  filter(LSCAT == "TARGET" & VISIT == "BASELINE") %>%
  group_by(USUBJID) %>%
  summarise(MEASDISF = "Y", .groups = "drop")

# 3. VISCFL
df_visc <- ls %>%
  filter(LSLOC %in% c("LIVER", "LUNGS", "KIDNEYS", "PANCREAS", "ADRENAL", "BRAIN / CNS") & VISIT == "BASELINE") %>%
  group_by(USUBJID) %>%
  summarise(VISCFL = "Y", .groups = "drop")

# 4. PAINBL
pn_trt <- pn %>%
  left_join(df_ex, by = "USUBJID") %>%
  mutate(PNDT = ymd(substring(PNDTC, 1, 10), quiet = TRUE))

baseline_pn <- pn_trt %>% filter(PNDT <= TRTSDT)

baseline_summary <- baseline_pn %>%
  group_by(USUBJID, PNTESTCD) %>%
  summarise(med_val = median(PNSTRESN, na.rm = TRUE), .groups = "drop")

ppi_meds <- baseline_summary %>% filter(PNTESTCD == "PAININT", med_val >= 2)
an_meds <- baseline_summary %>% filter(PNTESTCD == "ANSCORE", med_val >= 10)
pain_subjs <- union(ppi_meds$USUBJID, an_meds$USUBJID)

# 5. Baseline Labs
df_labs <- lb %>%
  filter(LBBLFL == "Y") %>%
  group_by(USUBJID, LBTESTCD) %>%
  summarise(val = first(LBSTRESN), .groups = "drop") %>%
  filter(LBTESTCD %in% c("PSA", "ALP", "HGB")) %>%
  pivot_wider(id_cols = USUBJID, names_from = LBTESTCD, values_from = val) %>%
  rename(PSABL = PSA, ALPBL = ALP, HGBBL = HGB)

# 6. Docetaxel Prior History
docetaxel <- cm %>%
  filter(CMDECOD == "DOCETAXEL" & CMCAT == "PRIOR TREATMENT CHEMOTHERAPY") %>%
  group_by(USUBJID) %>%
  summarise(
    DOCRESP = if_else(any(CMRLTL %in% c("COMPLETE RESPONSE", "PARTIAL RESPONSE"), na.rm = TRUE), "Y", "N"),
    DOCPROG = if_else(any(CMRSON == "DISEASE PROGRESSION" | CMRLTL == "PROGRESSIVE DISEASE", na.rm = TRUE), "DURING", "AFTER"),
    .groups = "drop"
  )

# Combine into ADSL
adsl <- dm %>%
  left_join(df_ex, by = "USUBJID") %>%
  left_join(df_death, by = "USUBJID") %>%
  left_join(df_alive, by = "USUBJID") %>%
  left_join(df_ecog, by = "USUBJID") %>%
  left_join(df_meas, by = "USUBJID") %>%
  left_join(df_visc, by = "USUBJID") %>%
  left_join(df_labs, by = "USUBJID") %>%
  left_join(docetaxel, by = "USUBJID") %>%
  mutate(
    STUDYID = .env$STUDYID,
    SITEID = substring(SUBJID, 1, 3),
    AGE = if_else(AGEGRP == ">=85", 85, suppressWarnings(as.numeric(AGEGRP))),
    AGEGR1 = if_else(AGE < .env$AGE_STRAT_CUT, "<65", ">=65"),
    AGEGR1N = if_else(AGE < .env$AGE_STRAT_CUT, 1.0, 2.0),
    ETHNIC = "NOT HISPANIC OR LATINO",
    SEX = "M",
    TRT01P = .env$TRT01P_CODE,
    TRT01PN = .env$TRT01PN_CODE,
    TRT01A = .env$TRT01P_CODE,
    TRT01AN = .env$TRT01PN_CODE,
    RANDDT = ymd(substring(RFSTDTC, 1, 10), quiet = TRUE),
    ITTFL = coalesce(ITT, "N"),
    SAFFL = coalesce(SAFETY, "N"),
    PPROTFL = coalesce(PPROT, "N"),
    DTHFL = coalesce(DTHFL, "N"),

    # Baseline clinical covariates — defaults from config_study.R §6.3
    ECOGBL = coalesce(ECOGBL, .env$ECOGBL_DEFAULT),
    MEASDISF = coalesce(MEASDISF, "N"),
    VISCFL = coalesce(VISCFL, "N"),
    PAINBL = if_else(USUBJID %in% pain_subjs, "Y", "N"),
    ALBBL = .env$ALBBL_DEFAULT,
    LDHBL = .env$LDHBL_DEFAULT,
    PSABL = coalesce(PSABL, .env$PSABL_DEFAULT),
    ALPBL = coalesce(ALPBL, .env$ALPBL_DEFAULT),
    HGBBL = coalesce(HGBBL, .env$HGBBL_DEFAULT),
    DOCPROG = coalesce(DOCPROG, "AFTER"),
    DOCRESP = coalesce(DOCRESP, "N")
  ) %>%
  select(
    STUDYID, USUBJID, SUBJID, SITEID,
    AGE, AGEGR1, AGEGR1N, RACE, ETHNIC, SEX,
    TRT01P, TRT01PN, TRT01A, TRT01AN, RANDDT, TRTSDT, TRTEDT, TRTDURD,
    ITTFL, SAFFL, PPROTFL, DTHFL, DTHDT, DTHCAUS, LSTALVDT,
    ECOGBL, MEASDISF, VISCFL, PAINBL, PSABL, ALPBL, ALBBL, LDHBL, HGBBL, DOCPROG, DOCRESP
  )

# Sort and Save
adsl <- adsl %>% arrange(USUBJID)
dir.create("04_adam", showWarnings = FALSE)

# Assertions and Error Guards (QC-03)
if (nrow(adsl) < 371) {
  stop("ERROR: [VALIDATION] ADSL output dataset is incomplete (expected N=371)!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adsl) <- toupper(names(adsl))
for (.dv in names(adsl)) if (inherits(adsl[[.dv]], "Date")) attr(adsl[[.dv]], "format.sas") <- "DATE9."
xportr_write(adsl, "04_adam/adsl_v.xpt", domain = "ADSL")

cat("NOTE: [VALIDATION] Wrote validation ADSL: 04_adam/adsl_v.xpt\n")

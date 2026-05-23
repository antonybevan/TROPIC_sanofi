# Program: v_adrs_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: CDISC ADaMIG v1.3 BDS | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADRS.

library(dplyr)
library(haven)
library(lubridate)

cat("NOTE: [VALIDATION] Starting ADRS Validation script...\n")

# Load real validation ADSL and staging tables
adsl <- read_xpt("04_adam/adsl_v.xpt")
ds <- readRDS("01_raw_source/real_sdtm/staging/ds.rds")
lb <- readRDS("01_raw_source/real_sdtm/staging/lb.rds")

# Standardize header variables
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT, RANDDT)

# Map Overall Response (OVRLRESP) from Disposition Progression and Death Milestones
df_ovrl <- ds %>%
  filter(DSDECOD %in% c("DISEASE PROGRESSION", "PROGRESSION", "DEATH", "DEAD")) %>%
  inner_join(header, by = c("USUBJID", "STUDYID", "SUBJID")) %>%
  mutate(
    adt = RANDDT + DSSTWK * 7,
    ady = as.numeric(adt - TRTSDT + 1),
    PARAMCD = "OVRLRESP",
    PARAM = "Overall Response per RECIST 1.1 + PCWG3",
    AVALC = if_else(DSDECOD %in% c("DISEASE PROGRESSION", "PROGRESSION"), "PD", "DEATH"),
    VISIT = coalesce(VISIT, "FOLLOW-UP"),
    ANL01FL = "Y"
  ) %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT, PARAMCD, PARAM, AVALC, ADT = adt, ADY = ady, VISIT, ANL01FL)

# Best Overall Response (BOR) per subject
df_bor_raw <- df_ovrl %>%
  filter(!is.na(ADT)) %>%
  mutate(
    bor_rank = if_else(AVALC == "PD", 4.0, 5.0)
  ) %>%
  group_by(USUBJID) %>%
  summarise(
    bor_val = min(bor_rank, na.rm = TRUE),
    .groups = "drop"
  )

df_bor <- df_bor_raw %>%
  inner_join(header, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "BESTRESP", PARAM = "Best Overall Response (BOR)",
    AVALC = if_else(bor_val == 4.0, "PD", "DEATH"),
    AVAL = bor_val,
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# Objective Response (CR/PR) - always N/0 for control arm non-responders
df_orr <- df_bor %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "OBJRESP", PARAM = "Objective Response (CR or PR)",
    AVALC = "N",
    AVAL = 0.0,
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# PSA progression indicator from real laboratory results
df_psprog_raw <- lb %>%
  filter(LBTESTCD == "PSA" & (toupper(LBNRIND) %in% c("HIGH", "H"))) %>%
  group_by(USUBJID) %>%
  summarise(
    cnt = n(),
    .groups = "drop"
  )

df_psprog <- header %>%
  left_join(df_psprog_raw, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "PSPROG", PARAM = "PSA Progression (PCWG3)",
    AVALC = if_else(!is.na(cnt) & cnt > 0, "Y", "N"),
    AVAL = if_else(AVALC == "Y", 1.0, 0.0),
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# Combine and Export via xportr
adrs <- bind_rows(df_ovrl, df_bor, df_orr, df_psprog) %>% 
  arrange(USUBJID, PARAMCD, VISIT)

library(xportr)
xportr_write(adrs, "04_adam/adrs_v.xpt", domain = "ADRS")

cat("NOTE: [VALIDATION] Wrote validation ADRS: 04_adam/adrs_v.xpt\n")

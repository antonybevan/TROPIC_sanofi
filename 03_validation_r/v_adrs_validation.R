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

# Load raw target lesion dataset in R
ls_data <- readRDS("01_raw_source/real_sdtm/staging/ls.rds")

# Derive visit-level target lesion SoD and responses
df_targets <- ls_data %>%
  filter(LSCAT == "TARGET" & LSTESTCD == "LENGTH" & !is.na(LSSTRESN))

df_baseline_sod <- df_targets %>%
  filter(VISIT == "BASELINE") %>%
  group_by(USUBJID) %>%
  summarise(base_sod = sum(LSSTRESN), .groups = "drop")

df_post_sod <- df_targets %>%
  filter(VISIT != "BASELINE") %>%
  group_by(USUBJID, VISITNUM, VISIT, LSDTC) %>%
  summarise(post_sod = sum(LSSTRESN), .groups = "drop") %>%
  left_join(df_baseline_sod, by = "USUBJID")

df_recist <- df_post_sod %>%
  group_by(USUBJID) %>%
  arrange(VISITNUM) %>%
  mutate(
    nadir_sod = cummin(post_sod),
    pct_chg_base = (post_sod - base_sod) / base_sod * 100,
    pct_chg_nadir = (post_sod - nadir_sod) / nadir_sod * 100,
    abs_chg_nadir = post_sod - nadir_sod,
    
    recist_resp = case_when(
      post_sod == 0 ~ "CR",
      pct_chg_nadir >= 20 & abs_chg_nadir >= 5 ~ "PD",
      pct_chg_base <= -30 ~ "PR",
      TRUE ~ "SD"
    )
  ) %>%
  ungroup() %>%
  inner_join(header, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "OVRLRESP",
    PARAM = "Overall Response per RECIST 1.1 + PCWG3",
    AVALC = recist_resp,
    ADT = ymd(substring(LSDTC, 1, 10)),
    ADY = as.numeric(ADT - TRTSDT + 1),
    VISIT,
    ANL01FL = "Y"
  )

# Disposition milestones fallback
df_disp_milestones <- ds %>%
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

# Union visit-level response records
df_ovrl <- bind_rows(df_recist, df_disp_milestones) %>%
  arrange(USUBJID, ADT, AVALC)

# Best Overall Response (BOR) per subject
# Ranking: CR (1) -> PR (2) -> SD (3) -> PD (4) -> DEATH (5)
df_bor_raw <- df_ovrl %>%
  filter(!is.na(ADT)) %>%
  mutate(
    bor_rank = case_when(
      AVALC == "CR" ~ 1.0,
      AVALC == "PR" ~ 2.0,
      AVALC == "SD" ~ 3.0,
      AVALC == "PD" ~ 4.0,
      AVALC == "DEATH" ~ 5.0,
      TRUE ~ 6.0
    )
  ) %>%
  group_by(USUBJID) %>%
  arrange(bor_rank) %>%
  slice(1) %>%
  ungroup()

df_bor <- df_bor_raw %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "BESTRESP", PARAM = "Best Overall Response (BOR)",
    AVALC,
    AVAL = bor_rank,
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# Objective Response (CR/PR)
df_orr <- df_bor %>%
  mutate(
    PARAMCD = "OBJRESP", PARAM = "Objective Response (CR or PR)",
    AVALC = if_else(AVALC %in% c("CR", "PR"), "Y", "N"),
    AVAL = if_else(AVALC == "Y", 1.0, 0.0),
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

# Program: v_adrs_validation.R | Version: 2.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-05-23
# Standard: CDISC ADaMIG v1.3 BDS | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADRS.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("03_validation_r/config_study.R")

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

# Target-lesion response only; integrated with non-target + new lesions below.
df_target <- df_post_sod %>%
  group_by(USUBJID) %>%
  arrange(VISITNUM) %>%
  mutate(
    nadir_sod = cummin(post_sod),
    pct_chg_base = (post_sod - base_sod) / base_sod * 100,
    pct_chg_nadir = if_else(nadir_sod > 0, (post_sod - nadir_sod) / nadir_sod * 100, NA_real_),
    abs_chg_nadir = post_sod - nadir_sod,

    target_resp = case_when(
      post_sod == 0 ~ "CR",
      pct_chg_nadir >= RECIST_PD_PCT & abs_chg_nadir >= RECIST_PD_ABS ~ "PD",
      pct_chg_base <= RECIST_PR_PCT ~ "PR",
      TRUE ~ "SD"
    )
  ) %>%
  ungroup()

# Non-target lesion response per visit (worst-per-visit: PD > SD > CR > NE).
# Absent for a subject/visit => integration falls back to target-only (no downgrade).
df_nontarget <- ls_data %>%
  filter(LSCAT == "NON-TARGET" & LSTESTCD == "STATUS" & VISIT != "BASELINE" &
           !is.na(LSSTRESC) & LSSTRESC != "" & LSSTRESC != "MISSING DATA") %>%
  mutate(nt_rank = case_when(
    LSSTRESC == "PROGRESSIVE DISEASE" ~ 4,
    LSSTRESC == "INCOMPLETE RESPONSE/STABLE DISEASE" ~ 3,
    LSSTRESC == "COMPLETE RESPONSE" ~ 2,
    TRUE ~ 1
  )) %>%
  group_by(USUBJID, VISIT) %>%
  summarise(nt_rank = max(nt_rank), .groups = "drop") %>%
  mutate(nt_resp = case_when(nt_rank == 4 ~ "PD", nt_rank == 3 ~ "SD",
                             nt_rank == 2 ~ "CR", TRUE ~ "NE")) %>%
  select(USUBJID, VISIT, nt_resp)

# New-lesion flag per visit (RECIST: any new lesion => PD).
df_newles <- ls_data %>%
  filter(LSTESTCD == "NEWLES" & LSSTRESC == "NEW LESION" & VISIT != "BASELINE") %>%
  distinct(USUBJID, VISIT) %>%
  mutate(newles_fl = "Y")

# Integrated RECIST v1.0 overall response (target + non-target + new lesion).
# Mirrors A_adrs_generation.sas: new lesion => PD; any PD => PD; target CR with a
# non-CR non-target => PR; else target response carries.
df_recist <- df_target %>%
  left_join(df_nontarget, by = c("USUBJID", "VISIT")) %>%
  left_join(df_newles, by = c("USUBJID", "VISIT")) %>%
  mutate(
    recist_resp = case_when(
      coalesce(newles_fl, "") == "Y" ~ "PD",
      target_resp == "PD" | coalesce(nt_resp, "") == "PD" ~ "PD",
      target_resp == "CR" & !(coalesce(nt_resp, "") %in% c("", "CR")) ~ "PR",
      TRUE ~ target_resp
    )
  ) %>%
  inner_join(header, by = "USUBJID") %>%
  mutate(
    lsdtc_clean = trimws(LSDTC),
    ADT_val = if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", lsdtc_clean), ymd(lsdtc_clean, quiet = TRUE), as.Date(NA)),
    ADY_val = as.numeric(ADT_val - TRTSDT + 1)
  ) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "OVRLRESP",
    PARAM = "Overall Response per RECIST v1.0",
    AVALC = recist_resp,
    ADT = ADT_val,
    ADY = ADY_val,
    VISIT,
    ANL01FL = "Y"
  )

df_disp_milestones <- ds %>%
  filter(DSDECOD %in% c("DISEASE PROGRESSION", "PROGRESSION", "DEATH", "DEAD")) %>%
  select(-any_of("STUDYID")) %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  mutate(
    adt = RANDDT + (DSSTWK - 1) * 7,
    ady = as.numeric(adt - TRTSDT + 1),
    PARAMCD = "OVRLRESP",
    PARAM = "Overall Response per RECIST v1.0",
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

# Objective Response (OBJRESP) — RECIST v1.0 CONFIRMED response (audit M-2).
# A responder requires a confirmatory CR/PR >= RECIST_CONFIRM_DAYS days after the
# first CR/PR (CR confirmed by CR; PR confirmed by CR or PR). Confirmation is
# evaluated on the lesion-derived RECIST timepoints (df_recist) so the R and SAS
# tracks use an identical, reconcilable basis. Unconfirmed single responses are NOT
# counted — this aligns the real-MP ORR with the published confirmed rate.
df_recist_resp <- df_recist %>%
  filter(AVALC %in% c("CR", "PR") & !is.na(ADT)) %>%
  select(USUBJID, ADT, AVALC)

df_orr_confirmed <- df_recist_resp %>%
  inner_join(df_recist_resp, by = "USUBJID", suffix = c("1", "2"),
             relationship = "many-to-many") %>%
  filter(as.numeric(ADT2 - ADT1) >= RECIST_CONFIRM_DAYS,
         !(AVALC1 == "CR" & AVALC2 == "PR")) %>%
  distinct(USUBJID) %>%
  mutate(orr_conf = "Y")

df_orr <- df_bor %>%
  left_join(df_orr_confirmed, by = "USUBJID") %>%
  mutate(
    PARAMCD = "OBJRESP", PARAM = "Objective Response (confirmed CR/PR)",
    AVALC = if_else(coalesce(orr_conf, "N") == "Y", "Y", "N"),
    AVAL = if_else(AVALC == "Y", 1.0, 0.0),
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  ) %>%
  select(-orr_conf)

# Rigorous PCWG3 PSA Progression Logic
df_lb_psa <- lb %>%
  filter(LBTESTCD == "PSA" & !is.na(LBSTRESN)) %>%
  mutate(
    lbdtc_clean = trimws(LBDTC),
    LBDT = if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", lbdtc_clean), ymd(lbdtc_clean, quiet = TRUE), as.Date(NA)),
    LBSTRESN = as.numeric(LBSTRESN)
  )

df_psa_base <- df_lb_psa %>%
  filter(LBBLFL == "Y") %>%
  select(USUBJID, PSABL = LBSTRESN, BASE_DT = LBDT)

df_psa_post <- df_lb_psa %>%
  inner_join(df_psa_base, by = "USUBJID") %>%
  filter(LBDT > BASE_DT) %>%
  select(USUBJID, LBDT, LBSTRESN, VISIT, VISITNUM)

df_psa_decline <- df_psa_post %>%
  inner_join(df_psa_base %>% select(USUBJID, PSABL), by = "USUBJID") %>%
  mutate(decline = (PSABL - LBSTRESN) / PSABL)

df_psa_resp_cand <- df_psa_decline %>%
  filter(decline >= PSA_RESP_THRESHOLD) %>%
  inner_join(df_psa_decline %>% filter(decline >= PSA_RESP_THRESHOLD),
             by = "USUBJID", suffix = c("1", "2"),
             relationship = "many-to-many") %>%
  filter(as.numeric(LBDT2 - LBDT1) >= PSA_RESP_CONFIRM)

df_psa_responders <- df_psa_resp_cand %>%
  distinct(USUBJID) %>%
  mutate(psad50 = "Y")

df_psa_all <- bind_rows(
  df_psa_base %>% rename(LBSTRESN = PSABL, LBDT = BASE_DT) %>% select(USUBJID, LBDT, LBSTRESN),
  df_psa_post %>% select(USUBJID, LBDT, LBSTRESN, VISIT, VISITNUM)
) %>%
  arrange(USUBJID, LBDT)

df_psa_nadir <- df_psa_all %>%
  group_by(USUBJID) %>%
  mutate(psanadir = cummin(LBSTRESN)) %>%
  ungroup()

df_psa_prog_check <- df_psa_nadir %>%
  filter(!is.na(VISITNUM) & VISITNUM > 0) %>%
  left_join(df_psa_responders, by = "USUBJID") %>%
  mutate(psad50 = coalesce(psad50, "N")) %>%
  mutate(
    is_trigger = if_else(
      psad50 == "Y",
      if_else(LBSTRESN >= PSA_PROG_MULT_RESP * psanadir, 1, 0),
      if_else(LBSTRESN >= PSA_PROG_MULT_NORESP * psanadir & (LBSTRESN - psanadir) >= PSA_PROG_ABS, 1, 0)
    )
  )

df_psa_prog_eval <- df_psa_prog_check %>%
  filter(is_trigger == 1)

df_psa_prog_conf <- df_psa_prog_eval %>%
  inner_join(df_psa_prog_eval, by = "USUBJID", suffix = c("1", "2"), relationship = "many-to-many") %>%
  filter(as.numeric(LBDT2 - LBDT1) >= PSA_PROG_CONFIRM) %>%
  group_by(USUBJID) %>%
  summarise(prog_date = min(LBDT1), .groups = "drop")

df_psprog <- header %>%
  left_join(df_psa_prog_conf, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "PSPROG", PARAM = "PSA Progression (PCWG3)",
    AVALC = if_else(!is.na(prog_date), "Y", "N"),
    AVAL = if_else(AVALC == "Y", 1.0, 0.0),
    ADT = prog_date,
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# PSA Response (>= 50% decline)
df_psaresp <- header %>%
  left_join(df_psa_responders, by = "USUBJID") %>%
  mutate(
    psad50 = coalesce(psad50, "N"),
    PARAMCD = "PSARESP",
    PARAM = "PSA Response (>=50% decline)",
    AVALC = psad50,
    AVAL = if_else(AVALC == "Y", 1.0, 0.0),
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  ) %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT, PARAMCD, PARAM, AVALC, AVAL, VISIT, ANL01FL)

# PCWG3 Bone-Scan Progression (BSGRESP) — 2+2 rule (Scher 2016). Methodological
# demonstration (post-2010, not in the trial-era SAP; see ADRG §4A), mirroring the SAS.
df_bone_new <- ls_data %>%
  filter(LSTESTCD == "NEWLES" & LSLOC == "BONE" & LSSTRESC == "NEW LESION" & VISIT != "BASELINE") %>%
  mutate(
    lsdtc_clean = trimws(LSDTC),
    scan_dt = if_else(grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", lsdtc_clean), ymd(lsdtc_clean, quiet = TRUE), as.Date(NA))
  ) %>%
  filter(!is.na(scan_dt)) %>%
  group_by(USUBJID, scan_dt) %>%
  summarise(n_new_bone = n(), .groups = "drop")

# PDu: first scan with >= MIN_NEW new bone lesions (unconfirmed progression).
df_bone_pdu <- df_bone_new %>%
  filter(n_new_bone >= BONE_PROG_MIN_NEW) %>%
  group_by(USUBJID) %>%
  summarise(pdu_date = min(scan_dt), .groups = "drop")

# Confirmed: a later scan adds >= CONFIRM_NEW further new bone lesions (2+2).
df_bone_conf <- df_bone_pdu %>%
  inner_join(df_bone_new %>% filter(n_new_bone >= BONE_PROG_CONFIRM_NEW),
             by = "USUBJID", relationship = "many-to-many") %>%
  filter(scan_dt > pdu_date) %>%
  distinct(USUBJID) %>%
  mutate(confirmed = "Y")

# Three-level result: confirmed PROGRESSION feeds TTUMOR; PROGRESSION UNCONFIRMED (PDu)
# is informational and does NOT count as an event.
df_bsgresp <- header %>%
  left_join(df_bone_pdu, by = "USUBJID") %>%
  left_join(df_bone_conf, by = "USUBJID") %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT,
    PARAMCD = "BSGRESP", PARAM = "Bone Scan Progression (PCWG3)",
    AVALC = case_when(
      coalesce(confirmed, "") == "Y" ~ "PROGRESSION",
      !is.na(pdu_date) ~ "PROGRESSION UNCONFIRMED",
      TRUE ~ "NO PROGRESSION"
    ),
    AVAL = if_else(coalesce(confirmed, "") == "Y", 1.0, 0.0),
    ADT = pdu_date,
    VISIT = "ALL CYCLES",
    ANL01FL = "Y"
  )

# Combine and Sort
adrs <- bind_rows(df_ovrl, df_bor, df_orr, df_psprog, df_psaresp, df_bsgresp) %>%
  rename(AVISIT = VISIT)

# Sort and Save

adrs <- adrs %>% arrange(USUBJID, PARAMCD, AVISIT)

# Assertions and Error Guards (QC-03)
if (nrow(adrs) == 0) {
  stop("ERROR: [VALIDATION] ADRS output dataset is empty!")
}
if (nrow(df_disp_milestones) == 0) {
  stop("ERROR: [VALIDATION] ADRS milestone fallback records are missing!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adrs) <- toupper(names(adrs))
for (.dv in names(adrs)) if (inherits(adrs[[.dv]], "Date")) attr(adrs[[.dv]], "format.sas") <- "DATE9."
write_xpt_v(adrs, "04_adam/adrs_v.xpt", domain = "ADRS")

cat("NOTE: [VALIDATION] Wrote validation ADRS: 04_adam/adrs_v.xpt\n")

# Program: v_adae_io_validation.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Standard: ADaMIG v1.3 OCCDS v1.1 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADAE.

library(dplyr)
library(haven)
library(lubridate)

cat("NOTE: [VALIDATION] Starting ADAE Validation script...\n")

# Load real validation ADSL and staging AE
adsl <- read_xpt("04_adam/adsl_v.xpt")
ae <- readRDS("01_raw_source/real_sdtm/staging/ae.rds")

# Standardize header variables
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRTSDT, RANDDT)

# Ingest and clean adverse events
df_ae <- ae %>%
  inner_join(header, by = c("USUBJID", "STUDYID", "SUBJID")) %>%
  mutate(
    # AE week conversion to days relative to randomization
    astdt = RANDDT + AESTWK * 7,
    aendt = if_else(!is.na(AEENWK), RANDDT + AEENWK * 7, as.Date(NA)),
    
    astdy = as.numeric(astdt - TRTSDT + 1),
    aendy = as.numeric(aendt - TRTSDT + 1),
    
    atoxgr = as.numeric(AETOXGRN),
    AESEV = case_when(
      atoxgr == 1.0 ~ "MILD",
      atoxgr == 2.0 ~ "MODERATE",
      atoxgr >= 3.0 ~ "SEVERE",
      TRUE ~ "MILD"
    ),
    CQ02NAM = if_else(AEDECOD %in% c("NEUTROPENIA", "FEBRILE NEUTROPENIA", "LEUKOPENIA"), "HEMATOLOGIC IRAE", "")
  )

# Implement Episode Merging and Denominator occurrence flagging
df_sorted <- df_ae %>%
  arrange(USUBJID, CQ02NAM, astdt, aendt)

df_episodes <- df_sorted %>%
  group_by(USUBJID, CQ02NAM) %>%
  mutate(
    prior_end = lag(aendt),
    # If gap is <= 3 days, merge = same sequence
    is_new_seq = if_else(is.na(prior_end) | CQ02NAM == "" | astdt > (prior_end + 3), 1.0, 0.0),
    ciaeseq = if_else(CQ02NAM != "", cumsum(is_new_seq), as.numeric(NA))
  ) %>%
  ungroup()

# Calculate continuous sequence details
df_seq_bounds <- df_episodes %>%
  filter(!is.na(ciaeseq)) %>%
  group_by(USUBJID, CQ02NAM, ciaeseq) %>%
  summarise(
    ciaesdt = min(astdt),
    ciaeedt = max(aendt),
    .groups = "drop"
  ) %>%
  mutate(
    ciaedur = as.numeric(ciaeedt - ciaesdt + 1) / 30.4375
  )

# Re-merge sequence bounds and apply AEOCCFL
adae_pre <- df_episodes %>%
  left_join(df_seq_bounds, by = c("USUBJID", "CQ02NAM", "ciaeseq")) %>%
  mutate(
    AEOCCFL = if_else(!is.na(ciaeseq), if_else(is_new_seq == 1.0, "Y", "N"), as.character(NA))
  )

# Standard AEDECOD level first occurrence denominator flags
adae_final <- adae_pre %>%
  arrange(USUBJID, AEDECOD, astdt) %>%
  group_by(USUBJID, AEDECOD) %>%
  mutate(
    first_ae = if_else(row_number() == 1, "Y", "N"),
    AEOCCFL = coalesce(AEOCCFL, first_ae)
  ) %>%
  ungroup() %>%
  mutate(
    TRTEMFL = coalesce(AETRTEM, if_else(!is.na(astdt) & astdt >= TRTSDT, "Y", "N")),
    ADURN = as.numeric(aendt - astdt + 1),
    ADURU = "DAYS"
  ) %>%
  select(
    STUDYID, USUBJID, AEDECOD, AEBODSYS, AEHLT, AESEV, ATOXGR = atoxgr, AESER, AEREL, 
    ASTDT = astdt, AENDT = aendt, ASTDY = astdy, AENDY = aendy, AEACN, AEOUT, 
    CQ02NAM, CIAESEQ = ciaeseq, CIAESDT = ciaesdt, CIAEEDT = ciaeedt, CIAEDUR = ciaedur, 
    AEOCCFL, TRTEMFL, ADURN, ADURU
  )

# Sort and Save
adae <- adae_final %>% arrange(USUBJID, ASTDT, AEDECOD)
library(xportr)
xportr_write(adae, "04_adam/adae_v.xpt", domain = "ADAE")

cat("NOTE: [VALIDATION] Wrote validation ADAE: 04_adam/adae_v.xpt\n")

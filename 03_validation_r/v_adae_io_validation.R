# Program: v_adae_io_validation.R | Version: 3.5.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-06-12
# Standard: ADaMIG v1.3 OCCDS v1.1 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADAE.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("03_validation_r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADAE Validation script...\n")

# Load real validation ADSL and staging AE
adsl <- read_xpt("04_adam/adsl_v.xpt")
ae <- readRDS("01_raw_source/real_sdtm/staging/ae.rds")

# VALIDATION INDEPENDENCE (audit F-1): This script derives ADAE SOLELY from the
# independent R logic below. It deliberately does NOT read the SAS production
# output (adae_prod.xpt). Deterministic row order within tie groups is resolved
# using AESEQ -- the canonical SDTM AE sequence number carried through from the
# source data -- a rule that the SAS production track and this R track can each
# apply independently. No production artifact is consumed by the QC track.

# Standardize header variables
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRT01A, TRT01AN, TRTSDT, RANDDT)

# Ingest and clean adverse events
df_ae <- ae %>%
  select(-any_of("STUDYID")) %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  mutate(
    # AE week conversion to days relative to randomization
    # Worst-case rule: if onset is week 1 (AESTWK = 1) and calculated date is prior to TRTSDT, impute to TRTSDT
    astdt = if_else(AESTWK == 1 & (RANDDT + AESTWK * 7) < TRTSDT & !is.na(TRTSDT), TRTSDT, RANDDT + AESTWK * 7),
    aendt = if_else(!is.na(AEENWK), RANDDT + AEENWK * 7, as.Date(NA)),
    
    astdy = as.numeric(astdt - TRTSDT + 1),
    aendy = as.numeric(aendt - TRTSDT + 1),
    
    atoxgr = as.numeric(AETOXGRN),
    AESEV = case_when(
      atoxgr == 1.0 ~ "MILD",
      atoxgr == 2.0 ~ "MODERATE",
      atoxgr >= 3.0 ~ "SEVERE",
      TRUE ~ NA_character_
    ),
    CQ02NAM = if_else(AEDECOD %in% c("NEUTROPENIA", "FEBRILE NEUTROPENIA", "LEUKOPENIA"), "HEMATOLOGIC EVENT", ""),
    CQ02CD = if_else(AEDECOD %in% c("NEUTROPENIA", "FEBRILE NEUTROPENIA", "LEUKOPENIA"), "CQ02", ""),
    CQ02SC = if_else(AEDECOD %in% c("NEUTROPENIA", "FEBRILE NEUTROPENIA", "LEUKOPENIA"), "SPONSOR", ""),
    aetrtem_clean = if_else(is.na(AETRTEM) | trimws(AETRTEM) == "", NA_character_, trimws(AETRTEM))
  )

# Independent deterministic tie-breaker (audit F-1):
# AESEQ (the SDTM AE sequence number) is carried through from staging and used
# as the final sort key wherever (USUBJID, dates, term) ties occur. This mirrors
# the input record order SAS preserves through its DATA steps WITHOUT reading the
# SAS production dataset, so the QC track remains genuinely independent.
df_ae <- df_ae %>% mutate(AESEQ = as.numeric(AESEQ))

# Implement Episode Merging and Denominator occurrence flagging
# Sort by usubjid CQ02NAM astdt aendt, with AESEQ as the deterministic tie-breaker
df_sorted <- df_ae %>%
  arrange(USUBJID, CQ02NAM, desc(is.na(astdt)), astdt, desc(is.na(aendt)), aendt, AESEQ)

# Episode merging using running-max of aendt (matching SAS retain-based logic).
# SAS retains _ciaeedt across rows; when aendt is missing, max(retained, .) = retained.
# R lag() would give NA for prior_end when prior aendt is missing, incorrectly
# starting a new episode. Instead, accumulate a running max of aendt.
df_episodes <- df_sorted %>%
  group_by(USUBJID, CQ02NAM) %>%
  mutate(
    row_id = row_number(),
    # For grouped AEs, compute running episode assignment iteratively
    # First pass: identify new sequence starts using running max end date
    is_new_seq = {
      n <- n()
      result <- numeric(n)
      running_end <- as.Date(NA)
      for (i in seq_len(n)) {
        if (i == 1 || CQ02NAM[i] == "") {
          result[i] <- 1.0
          running_end <- aendt[i]
        } else if (CQ02NAM[i] != "") {
          if (is.na(running_end) || astdt[i] > (running_end + EPISODE_GAP_DAYS)) {
            result[i] <- 1.0
            running_end <- aendt[i]
          } else {
            result[i] <- 0.0
            running_end <- max(running_end, aendt[i], na.rm = TRUE)
          }
        }
      }
      result
    },
    ciaeseq = if_else(CQ02NAM != "", cumsum(is_new_seq), as.numeric(NA)),
    
    # Derivation of running start date (CIAESDT)
    ciaesdt = {
      n <- n()
      res_sdt <- rep(as.Date(NA), n)
      running_start <- as.Date(NA)
      running_end <- as.Date(NA)
      for (i in seq_len(n)) {
        if (i == 1 || CQ02NAM[i] == "") {
          running_start <- astdt[i]
          running_end <- aendt[i]
        } else if (CQ02NAM[i] != "") {
          if (is.na(running_end) || astdt[i] > (running_end + EPISODE_GAP_DAYS)) {
            running_start <- astdt[i]
            running_end <- aendt[i]
          } else {
            running_end <- max(running_end, aendt[i], na.rm = TRUE)
          }
        }
        res_sdt[i] <- running_start
      }
      res_sdt
    },
    
    # Derivation of running end date (CIAEEDT)
    ciaeedt = {
      n <- n()
      res_edt <- rep(as.Date(NA), n)
      running_end <- as.Date(NA)
      for (i in seq_len(n)) {
        if (i == 1 || CQ02NAM[i] == "") {
          running_end <- aendt[i]
        } else if (CQ02NAM[i] != "") {
          if (is.na(running_end) || astdt[i] > (running_end + EPISODE_GAP_DAYS)) {
            running_end <- aendt[i]
          } else {
            running_end <- max(running_end, aendt[i], na.rm = TRUE)
          }
        }
        res_edt[i] <- running_end
      }
      res_edt
    },
    
    ciaesdt = if_else(CQ02NAM != "", ciaesdt, as.Date(NA)),
    ciaeedt = if_else(CQ02NAM != "", ciaeedt, as.Date(NA)),
    ciaedur = if_else(CQ02NAM != "", as.numeric(ciaeedt - ciaesdt + 1) / 30.4375, as.numeric(NA))
  ) %>%
  ungroup()

# Apply AEOCCFL directly using is_new_seq without left_join
adae_pre <- df_episodes %>%
  mutate(
    AEOCCFL = if_else(!is.na(ciaeseq), if_else(is_new_seq == 1.0, "Y", "N"), as.character(NA))
  )

# Standard AEDECOD level first occurrence denominator flags
# Sort matches SAS: by usubjid aedecod astdt (then assign AEOCCFL, TRTEMFL)
adae_final <- adae_pre %>%
  arrange(USUBJID, AEDECOD, desc(is.na(astdt)), astdt, desc(is.na(aendt)), aendt, AESEQ) %>%
  group_by(USUBJID, AEDECOD) %>%
  mutate(
    first_ae = if_else(row_number() == 1, "Y", "N"),
    AEOCCFL = coalesce(AEOCCFL, first_ae)
  ) %>%
  ungroup() %>%
  mutate(
    # Assign TRTEMFL in the same row context as SAS (by usubjid aedecod sort)
    TRTEMFL = if_else(!is.na(aetrtem_clean), if_else(aetrtem_clean == "T", "Y", "N"), if_else(!is.na(astdt) & astdt >= TRTSDT, "Y", "N")),
    ADURN = as.numeric(aendt - astdt + 1),
    ADURU = "DAYS"
  ) %>%
  select(
    STUDYID, USUBJID, TRTA = TRT01A, TRTAN = TRT01AN,
    AEDECOD, AEBODSYS, AEHLT, AESEV, ATOXGR = atoxgr, AESER, AEREL,
    ASTDT = astdt, AENDT = aendt, ASTDY = astdy, AENDY = aendy, AEACN, AEOUT,
    CQ02NAM, CQ02CD, CQ02SC, CIAESEQ = ciaeseq, CIAESDT = ciaesdt, CIAEEDT = ciaeedt, CIAEDUR = ciaedur,
    AEOCCFL, TRTEMFL, ADURN, ADURU, AESEQ
  )

# Sort and Save (AESEQ retained for unique-key reconciliation)
adae <- adae_final %>%
  arrange(USUBJID, ASTDT, AEDECOD, desc(is.na(AENDT)), AENDT, AESEQ)

# Assertions and Error Guards (QC-03)
if (nrow(adae) == 0) {
  stop("ERROR: [VALIDATION] ADAE output dataset is empty!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adae) <- toupper(names(adae))
for (.dv in names(adae)) if (inherits(adae[[.dv]], "Date")) attr(adae[[.dv]], "format.sas") <- "DATE9."
write_xpt_v(adae, "04_adam/adae_v.xpt", domain = "ADAE")

cat("NOTE: [VALIDATION] Wrote validation ADAE: 04_adam/adae_v.xpt\n")

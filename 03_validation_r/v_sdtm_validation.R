# Program: v_sdtm_validation.R | Version: 2.1 | Author: Antony Bevan, Clinical Programming | Date: 2026-05-27
# Description: Independent validation of SDTM mapped staging datasets.
# Validates presence, row counts, and structural completeness of core SDTM staging data.

library(dplyr)

cat("NOTE: [VALIDATION] Starting SDTM Structure Validation...\n")

staging_dir <- "01_raw_source/real_sdtm/staging"
domains <- c("dm", "ae", "ex", "cm", "lb", "ds", "vs", "ls", "pn")

validation_failed <- FALSE

for (dom in domains) {
  file_path <- file.path(staging_dir, paste0(dom, ".rds"))
  
  if (!file.exists(file_path)) {
    cat(sprintf("  [ERROR] Staging file missing for domain %s: %s\n", toupper(dom), file_path))
    validation_failed <- TRUE
    next
  }
  
  df <- readRDS(file_path)
  row_cnt <- nrow(df)
  col_cnt <- ncol(df)
  
  cat(sprintf("  [CHECK] Domain %s: %d rows, %d columns.\n", toupper(dom), row_cnt, col_cnt))
  
  if (row_cnt == 0) {
    cat(sprintf("  [ERROR] Domain %s contains 0 records.\n", toupper(dom)))
    validation_failed = TRUE
  }
  
  # 1. Validate key identifier presence
  if (!"USUBJID" %in% colnames(df)) {
    cat(sprintf("  [ERROR] Domain %s is missing mandatory key variable USUBJID.\n", toupper(dom)))
    validation_failed = TRUE
  }
  
  # 2. Validate STUDYID consistency
  if ("STUDYID" %in% colnames(df)) {
    studyids <- unique(df$STUDYID)
    if (!all(studyids == "EFC6193")) {
      cat(sprintf("  [ERROR] Domain %s has inconsistent STUDYID: %s (expected EFC6193)\n", toupper(dom), paste(studyids, collapse = ", ")))
      validation_failed = TRUE
    }
  } else {
    cat(sprintf("  [ERROR] Domain %s is missing STUDYID.\n", toupper(dom)))
    validation_failed = TRUE
  }

  # 3. Validate mandatory domain-level variables (VAL-02)
  mandatory_vars <- list(
    dm = c("ARMCD", "SEX", "RACE"),
    ae = c("AEDECOD", "AEBODSYS", "AESEQ"),
    ex = c("EXTRT", "EXDOSE", "EXSEQ"),
    cm = c("CMTRT", "CMDECOD", "CMSEQ"),
    lb = c("LBTESTCD", "LBSTRESN", "LBSEQ"),
    ds = c("DSDECOD", "DSSEQ"),
    vs = c("VSTESTCD", "VSSEQ"),
    ls = c("LSTESTCD", "LSSEQ"),
    pn = c("PNTESTCD", "PNSEQ")
  )
  
  if (dom %in% names(mandatory_vars)) {
    for (var in mandatory_vars[[dom]]) {
      if (!var %in% colnames(df)) {
        cat(sprintf("  [ERROR] Domain %s is missing mandatory variable %s.\n", toupper(dom), var))
        validation_failed = TRUE
      }
    }
  }

  # 4. Duplicate sequence key check (USUBJID + SEQ)
  seq_var <- paste0(toupper(dom), "SEQ")
  if (dom != "dm" && seq_var %in% colnames(df)) {
    dups <- df %>%
      group_by(USUBJID, .data[[seq_var]]) %>%
      filter(n() > 1) %>%
      ungroup()
    if (nrow(dups) > 0) {
      cat(sprintf("  [ERROR] Domain %s has duplicate keys on USUBJID + %s!\n", toupper(dom), seq_var))
      validation_failed = TRUE
    }
  }

  # 5. ISO 8601 Date field compliancy checks
  date_fields <- colnames(df)[grepl("DTC$", colnames(df))]
  for (fld in date_fields) {
    vals <- df[[fld]]
    vals <- vals[!is.na(vals) & vals != "" & vals != " "]
    if (length(vals) > 0) {
      # DTC variables must be character class in CDISC SDTM
      if (!is.character(vals)) {
        cat(sprintf("  [ERROR] Domain %s variable %s is not character class.\n", toupper(dom), fld))
        validation_failed = TRUE
      }
      # Warn on partial/dirty dates (which are common in raw clinical data) instead of failing
      valid_date <- grepl("^\\d{4}(-\\d{2})?(-\\d{2})?([T\\s]\\d{2}:\\d{2}(:\\d{2})?)?$", vals)
      if (!all(valid_date)) {
        bad_vals <- unique(vals[!valid_date])
        cat(sprintf("  [WARNING] Domain %s variable %s has partial/dirty date values: %s\n", toupper(dom), fld, paste(head(bad_vals), collapse = ", ")))
      }
    }
  }
}

if (validation_failed) {
  cat("ERROR: [VALIDATION] SDTM structural validation FAILED. Inspect logs.\n")
  quit(status = 1)
} else {
  cat("NOTE: [VALIDATION] Independent validation SDTM mapping validated successfully with 0 errors.\n")
}

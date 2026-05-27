# Program: v_sdtm_validation.R | Version: 2.1 | Author: Clinical Data Architect | Date: 2026-05-27
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
    validation_failed <- TRUE
  }
  
  # Validate key identifier presence
  if (!"USUBJID" %in% colnames(df)) {
    cat(sprintf("  [ERROR] Domain %s is missing mandatory key variable USUBJID.\n", toupper(dom)))
    validation_failed <- TRUE
  }
}

if (validation_failed) {
  cat("ERROR: [VALIDATION] SDTM structural validation FAILED. Inspect logs.\n")
  quit(status = 1)
} else {
  cat("NOTE: [VALIDATION] Independent validation SDTM mapping validated successfully with 0 errors.\n")
}

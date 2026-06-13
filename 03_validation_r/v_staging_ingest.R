# Program: v_staging_ingest.R | Version: 2.0 | Author: Clinical Programming | Date: 2026-05-23
# Description: Standard ingestion and supplemental transposition for real SDTM SAS datasets.

library(haven)
library(dplyr)
library(tidyr)

cat("NOTE: [INGEST] Starting Real SDTM Ingestion & Transposition...\n")

dir.create("01_raw_source/real_sdtm/staging", showWarnings = FALSE, recursive = TRUE)

transpose_supp <- function(domain_name) {
  main_path <- paste0("01_raw_source/real_sdtm/", domain_name, ".sas7bdat")
  supp_path <- paste0("01_raw_source/real_sdtm/supp", domain_name, ".sas7bdat")
  
  if (!file.exists(main_path)) {
    cat(sprintf("  [WARNING] Main domain file %s does not exist. Skipping.\n", main_path))
    return(NULL)
  }
  
  main_df <- read_sas(main_path)
  
  # Standardize all column names to uppercase
  colnames(main_df) <- toupper(colnames(main_df))
  
  if (file.exists(supp_path)) {
    supp_df <- read_sas(supp_path)
    if (nrow(supp_df) > 0) {
      colnames(supp_df) <- toupper(colnames(supp_df))
      
      # Pivot supplemental variables from long to wide format
      supp_wide <- supp_df %>%
        select(USUBJID, IDVAR, IDVARVAL, QNAM, QVAL) %>%
        filter(QNAM != "") %>%
        pivot_wider(
          id_cols = c(USUBJID, IDVAR, IDVARVAL),
          names_from = QNAM,
          values_from = QVAL,
          values_fn = first
        )
      
      # Merge based on standard domain mapping
      if (toupper(domain_name) == "DM") {
        main_df <- main_df %>% left_join(supp_wide %>% select(-IDVAR, -IDVARVAL), by = "USUBJID")
      } else {
        idvar_col <- unique(supp_df$IDVAR)
        idvar_col <- idvar_col[idvar_col != ""]
        if (length(idvar_col) == 1) {
          # Align types of join key
          supp_wide <- supp_wide %>%
            mutate(ID_JOIN = as.numeric(IDVARVAL)) %>%
            select(-IDVAR, -IDVARVAL)
          
          join_args <- c("USUBJID" = "USUBJID")
          join_args[idvar_col] <- "ID_JOIN"
          
          main_df <- main_df %>% left_join(supp_wide, by = join_args)
        } else {
          main_df <- main_df %>% left_join(supp_wide %>% select(-IDVAR, -IDVARVAL), by = "USUBJID")
        }
      }
    }
  }
  
  # Ensure all column names of output are uppercase
  colnames(main_df) <- toupper(colnames(main_df))
  
  save_path <- paste0("01_raw_source/real_sdtm/staging/", tolower(domain_name), ".rds")
  saveRDS(main_df, save_path)
  cat(sprintf("  [SUCCESS] Ingested and staging-saved: %s -> %s (Rows: %d, Cols: %d)\n", 
              toupper(domain_name), save_path, nrow(main_df), ncol(main_df)))
  return(main_df)
}

domains <- c("dm", "ae", "ex", "cm", "lb", "ds", "vs", "ls", "pn")
for (dom in domains) {
  transpose_supp(dom)
}

cat("NOTE: [INGEST] Real SDTM Staging Ingestion complete.\n")

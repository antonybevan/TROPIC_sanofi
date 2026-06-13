# Program: v_adex_validation.R | Version: 2.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-05-23
# Standard: ADaMIG v1.3 BDS | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADEX.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("03_validation_r/config_study.R")

round_half_up <- function(x, digits = 0) {
  posneg <- sign(x)
  z <- abs(x) * 10^digits
  z <- z + 0.5 + 1e-9
  z <- floor(z)
  z <- z / 10^digits
  return(z * posneg)
}

cat("NOTE: [VALIDATION] Starting ADEX Validation script...\n")

# Load real validation ADSL and staging EX
adsl <- read_xpt("04_adam/adsl_v.xpt")
ex <- readRDS("01_raw_source/real_sdtm/staging/ex.rds")

# Ensure columns are numeric and exclude staging STUDYID
ex_clean <- ex %>%
  select(-any_of("STUDYID")) %>%
  mutate(
    EXSEQ = as.numeric(EXSEQ),
    EXDOSE2 = as.numeric(EXDOSE2),
    EXCUMD2 = as.numeric(EXCUMD2),
    EXPDOSE = as.numeric(EXPDOSE),
    EXTRINT = as.numeric(EXTRINT)
  )

# Summarize Modifications per USUBJID
ex_summary <- ex_clean %>%
  group_by(USUBJID) %>%
  summarise(
    ncycle = max(EXSEQ, na.rm = TRUE),
    cumdose = max(EXCUMD2, na.rm = TRUE),
    ndeldose = sum(!is.na(EXDELAY) & EXDELAY != "", na.rm = TRUE),
    nreddose = sum(!is.na(EXDSRCM) & EXDSRCM != "", na.rm = TRUE),
    rdi = max(EXTRINT, na.rm = TRUE),
    .groups = "drop"
  ) %>%
  mutate(
    # Handle infinities/NAs from max() on missing values
    ncycle = if_else(is.infinite(ncycle) | is.na(ncycle), 0.0, ncycle),
    cumdose = if_else(is.infinite(cumdose) | is.na(cumdose), 0.0, cumdose),
    rdi = if_else(is.infinite(rdi) | is.na(rdi), 0.0, rdi)
  )

# Fetch header details from ADSL
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT)

summary_records <- header %>%
  inner_join(ex_summary, by = "USUBJID") %>%
  mutate(
    planned_dose = PLANNED_DOSE # Mitoxantrone planned dose mg/m2 — see config_study.R
  )

# Build BDS Structure (Summary records)
summary_bds <- bind_rows(
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "PLDOSE", PARAM = "Planned Dose (mg/m2)", PARCAT1 = "INDIVIDUAL",
    AVAL = planned_dose, AVALC = sprintf("%.2f", planned_dose), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "CUMDOSE", PARAM = "Cumulative Actual Dose (mg/m2)", PARCAT1 = "SUMMARY",
    AVAL = cumdose, AVALC = sprintf("%.2f", cumdose), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "NCYCLE", PARAM = "Number of Cycles Received", PARCAT1 = "SUMMARY",
    AVAL = ncycle, AVALC = as.character(ncycle), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "NDELDOSE", PARAM = "Number of Dose Delays", PARCAT1 = "SUMMARY",
    AVAL = ndeldose, AVALC = as.character(ndeldose), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "NREDDOSE", PARAM = "Number of Dose Reductions", PARCAT1 = "SUMMARY",
    AVAL = nreddose, AVALC = as.character(nreddose), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "RDI", PARAM = "Relative Dose Intensity (%)", PARCAT1 = "SUMMARY",
    AVAL = rdi, AVALC = sprintf("%.1f", round_half_up(rdi, 1)), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "RDIDL", PARAM = "Relative Dose Intensity Category", PARCAT1 = "SUMMARY",
    AVAL = rdi, 
    AVALC = if_else(rdi >= 85, ">=85%", if_else(rdi >= 65, "65-<85%", "<65%")),
    AVISIT = "ALL CYCLES"
  )
)

# Cycle-level performance dose and adjustments
cycle_bds <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "PERFDOSE", PARAM = "Actual Dose Administered (mg/m2)", PARCAT1 = "INDIVIDUAL",
    AVAL = EXDOSE2, AVALC = sprintf("%.2f", EXDOSE2), AVISIT = paste("CYCLE", EXSEQ)
  )

cycle_adj <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "ADJ", PARAM = "Dose Adjusted Flag", PARCAT1 = "INDIVIDUAL",
    AVAL = if_else(!is.na(EXDSRCM) & EXDSRCM != "", 1.0, 0.0), 
    AVALC = if_else(!is.na(EXDSRCM) & EXDSRCM != "", "Y", "N"), 
    AVISIT = paste("CYCLE", EXSEQ)
  )

cycle_adj_ae <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "ADJAE", PARAM = "Dose Adjusted due to AE Flag", PARCAT1 = "INDIVIDUAL",
    AVAL = if_else(!is.na(EXDSRCM) & EXDSRCM == "ADVERSE EVENT", 1.0, 0.0), 
    AVALC = if_else(!is.na(EXDSRCM) & EXDSRCM == "ADVERSE EVENT", "Y", "N"), 
    AVISIT = paste("CYCLE", EXSEQ)
  )

# Combine and Sort
adex <- bind_rows(summary_bds, cycle_bds, cycle_adj, cycle_adj_ae)

# Sort and Save

adex <- adex %>% arrange(USUBJID, PARAMCD, AVISIT)

# Assertions and Error Guards (QC-03)
if (nrow(adex) == 0) {
  stop("ERROR: [VALIDATION] ADEX output dataset is empty!")
}
if (nrow(adex %>% filter(PARAMCD == "PERFDOSE")) == 0) {
  stop("ERROR: [VALIDATION] ADEX cycle-level records are missing!")
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adex) <- toupper(names(adex))
for (.dv in names(adex)) if (inherits(adex[[.dv]], "Date")) attr(adex[[.dv]], "format.sas") <- "DATE9."
xportr_write(adex, "04_adam/adex_v.xpt", domain = "ADEX")
cat("NOTE: [VALIDATION] Wrote validation ADEX: 04_adam/adex_v.xpt\n")

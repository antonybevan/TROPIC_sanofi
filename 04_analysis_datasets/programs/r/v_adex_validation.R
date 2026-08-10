# Program: v_adex_validation.R | Version: 3.0.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-08-09
# Standard: ADaMIG v1.3 BDS | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADEX.
#
# Dens: subject-level BDS spine = ADSL SAFFL=="Y". Oral prednisone/
# prednisolone records are excluded from antineoplastic cycle metrics.

library(dplyr)
library(haven)
library(lubridate)
library(xportr)
source("04_analysis_datasets/programs/r/config_study.R")

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
adsl <- read_xpt("04_analysis_datasets/adam/adsl_v.xpt")
ex <- readRDS(stage_file("ex"))

# Restrict exposure metrics to the primary randomized IV antineoplastic. EXSEQ
# counts oral and IV records; VISITNUM is the treatment-cycle index.
ex_clean <- ex %>%
  select(-any_of("STUDYID")) %>%
  filter(grepl("MITOX|XRP|CABAZ", coalesce(EXTRT, ""), ignore.case = TRUE)) %>%
  mutate(
    EXSEQ = as.numeric(EXSEQ),
    VISITNUM = as.numeric(VISITNUM),
    EXDOSE2 = as.numeric(EXDOSE2),
    EXCUMD2 = as.numeric(EXCUMD2),
    EXPDOSE = as.numeric(EXPDOSE),
    EXTRINT = as.numeric(EXTRINT),
    delay_flag = !is.na(EXDELAY) & trimws(as.character(EXDELAY)) != "",
    reduction_flag = !is.na(EXDOSE2) & EXDOSE2 > 0 & !is.na(EXPDOSE) &
      EXDOSE2 < EXPDOSE * (1 - DOSE_REDUCTION_TOLERANCE)
  )

# EXTRINT is a source-derived subject RDI repeated on each IV cycle. Carry it
# only when those repetitions are internally consistent.
ex_summary <- ex_clean %>%
  group_by(USUBJID) %>%
  summarise(
    ncycle = n_distinct(VISITNUM[!is.na(EXDOSE2) & EXDOSE2 > 0]),
    planned_dose = {
      z <- EXPDOSE[VISITNUM == 1 & !is.na(EXPDOSE)]
      if (length(z)) max(z) else NA_real_
    },
    cumdose = max(EXCUMD2, na.rm = TRUE),
    ndeldose = sum(delay_flag),
    nreddose = sum(reduction_flag),
    n_rdi_values = n_distinct(EXTRINT, na.rm = TRUE),
    rdi = if_else(n_rdi_values <= 1L, max(EXTRINT, na.rm = TRUE), NA_real_),
    .groups = "drop"
  ) %>%
  mutate(
    # Handle infinities/NAs from max() on missing values
    ncycle = if_else(is.infinite(ncycle) | is.na(ncycle), 0.0, ncycle),
    cumdose = if_else(is.infinite(cumdose) | is.na(cumdose), 0.0, cumdose),
    rdi = if_else(is.infinite(rdi), NA_real_, rdi)
  )

if (any(ex_summary$n_rdi_values > 1L)) {
  stop("ERROR: [ADEX-QC] conflicting source EXTRINT values within subject")
}

# Fetch header details from ADSL
header <- adsl %>%
  select(STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT)

summary_records <- header %>%
  inner_join(ex_summary, by = "USUBJID")

# Build BDS Structure (Summary records)
summary_bds <- bind_rows(
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "PLDOSE", PARAM = "Initial Planned IV Dose (mg/m2)", PARCAT1 = "INDIVIDUAL",
    AVAL = planned_dose, AVALC = sprintf("%.2f", planned_dose), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "CUMDOSE", PARAM = "Cumulative IV Actual Dose (mg/m2)", PARCAT1 = "SUMMARY",
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
    PARAMCD = "RDI", PARAM = "Source RDI (%)", PARCAT1 = "SUMMARY",
    AVAL = rdi, AVALC = sprintf("%.1f", round_half_up(rdi, 1)), AVISIT = "ALL CYCLES"
  ),
  summary_records %>% transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "RDIDL", PARAM = "Relative Dose Intensity Category", PARCAT1 = "SUMMARY",
    AVAL = rdi,
    AVALC = case_when(
      is.na(rdi) ~ NA_character_,
      rdi >= 85 ~ ">=85%",
      rdi >= 65 ~ "65-<85%",
      TRUE ~ "<65%"
    ),
    AVISIT = "ALL CYCLES"
  )
)

# Cycle-level performance dose and adjustments
cycle_bds <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "PERFDOSE", PARAM = "IV Actual Dose Administered (mg/m2)", PARCAT1 = "INDIVIDUAL",
    AVAL = EXDOSE2,
    AVALC = if_else(is.na(EXDOSE2), NA_character_, sprintf("%.2f", EXDOSE2)),
    AVISIT = paste("CYCLE", as.integer(VISITNUM))
  )

cycle_adj <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "ADJ", PARAM = "Dose Adjusted Flag", PARCAT1 = "INDIVIDUAL",
    AVAL = if_else(delay_flag | reduction_flag | !is.na(EXDSREA), 1.0, 0.0),
    AVALC = if_else(delay_flag | reduction_flag | !is.na(EXDSREA), "Y", "N"),
    AVISIT = paste("CYCLE", as.integer(VISITNUM))
  )

cycle_adj_ae <- ex_clean %>%
  inner_join(header, by = c("USUBJID", "SUBJID")) %>%
  transmute(
    STUDYID, USUBJID, SUBJID, TRT01P, TRT01PN, TRTSDT,
    PARAMCD = "ADJAE", PARAM = "Dose Adjusted due to AE Flag", PARCAT1 = "INDIVIDUAL",
    AVAL = if_else(toupper(trimws(coalesce(EXDSREA, ""))) == "ADVERSE EVENT", 1.0, 0.0),
    AVALC = if_else(toupper(trimws(coalesce(EXDSREA, ""))) == "ADVERSE EVENT", "Y", "N"),
    AVISIT = paste("CYCLE", as.integer(VISITNUM))
  )

# Combine and Sort
adex <- bind_rows(summary_bds, cycle_bds, cycle_adj, cycle_adj_ae) %>%
  # AVISITN companion to AVISIT (audit F-09): ALL CYCLES -> 0; CYCLE n -> n
  mutate(
    .cycle_num = if_else(grepl("^CYCLE [0-9]+$", AVISIT), sub("^CYCLE ", "", AVISIT), NA_character_),
    AVISITN = if_else(AVISIT == "ALL CYCLES", 0, as.numeric(.cycle_num))
  ) %>%
  select(-.cycle_num)

# Deterministic 1:1 PARAMN over the sorted distinct PARAMCD set (audit F-09) — identical to the
# SAS track (proc sort nodupkey by PARAMCD + _n_).
pn_map <- adex %>% distinct(PARAMCD) %>% arrange(PARAMCD) %>% mutate(PARAMN = as.numeric(row_number()))
adex <- adex %>% left_join(pn_map, by = "PARAMCD")

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
write_xpt_v(adex, "04_analysis_datasets/adam/adex_v.xpt", domain = "ADEX")
cat("NOTE: [VALIDATION] Wrote validation ADEX: 04_analysis_datasets/adam/adex_v.xpt\n")

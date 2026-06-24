# Program: figure_data_reconcile.R
# Purpose: Reconcile the exact data/statistics driving every shared R/SAS figure.

suppressPackageStartupMessages({
  library(haven)
  library(dplyr)
})
source("09_tfl/tfl_stats.R")

cat("========== R <-> SAS FIGURE-DATA RECONCILIATION ==========\n")
ok <- TRUE
fail <- function(label, detail) {
  ok <<- FALSE
  cat(sprintf("  [FAIL] %-22s %s\n", label, detail))
}
pass <- function(label, detail) cat(sprintf("  [PASS] %-22s %s\n", label, detail))

required <- file.path("04_adam", c(
  "figure_km_stats_prod.csv", "figure_km_risk_prod.csv",
  "figure_waterfall_prod.csv", "figure_swimmer_prod.csv",
  "figure_er_prod.csv"
))
missing <- required[!file.exists(required)]
if (length(missing)) stop("Missing SAS figure-data exports: ", paste(missing, collapse = ", "))

adsl <- bind_rows(read_xpt("04_adam/adsl_v.xpt"),
                  readRDS("01_raw_source/cbzp_reconstructed/adsl_cbzp.rds"))
adtte <- bind_rows(read_xpt("04_adam/adtte_v.xpt"),
                   readRDS("01_raw_source/cbzp_reconstructed/adtte_cbzp.rds"))
adlb <- bind_rows(read_xpt("04_adam/adlb_v.xpt"),
                  readRDS("01_raw_source/cbzp_reconstructed/adlb_cbzp.rds"))
adex <- bind_rows(read_xpt("04_adam/adex_v.xpt"),
                  readRDS("01_raw_source/cbzp_reconstructed/adex_cbzp.rds"))

# KM hazard ratios/CIs and displayed risk counts.
sas_km <- read.csv(required[1], check.names = FALSE) |>
  rename_with(toupper)
for (endpoint in c("OS", "PFS")) {
  d <- adtte |>
    filter(PARAMCD == endpoint) |>
    left_join(adsl |> select(USUBJID, ECOGBL, MEASDISF), by = "USUBJID")
  r <- compute_tte_stats(d)
  s <- sas_km[sas_km$PARAMCD == endpoint, ]
  delta <- max(abs(c(r$hr - s$HAZARDRATIO, r$lcl - s$WALDLOWER,
                     r$ucl - s$WALDUPPER)))
  if (nrow(s) == 1L && delta <= 0.01) pass(paste("KM", endpoint), sprintf("HR/CI max delta %.5f", delta)) else
    fail(paste("KM", endpoint), sprintf("HR/CI max delta %.5f", delta))
}

sas_risk <- read.csv(required[2], check.names = FALSE) |>
  rename_with(toupper)
risk_ok <- TRUE
for (i in seq_len(nrow(sas_risk))) {
  z <- sas_risk[i, ]
  expected <- sum(adtte$PARAMCD == z$PARAMCD & adtte$TRT01P == z$TRT01P &
                    adtte$AVAL / 30.4375 >= z$AVALM)
  if (expected != z$NRISK) risk_ok <- FALSE
}
if (risk_ok) pass("KM risk tables", sprintf("%d displayed counts identical", nrow(sas_risk))) else
  fail("KM risk tables", "one or more displayed counts differ")

# Waterfall subject/value/category set.
r_water <- adlb |>
  filter(PARAMCD == "PSA", !is.na(PCHG)) |>
  group_by(USUBJID, TRT01P) |>
  summarise(BEST = min(PCHG), .groups = "drop") |>
  mutate(RESPCAT = case_when(
    BEST <= -50 ~ "PSA Response (>=50% dec)",
    BEST < 0 ~ "PSA Decrease (<50%)",
    TRUE ~ "PSA Increase"
  )) |>
  arrange(USUBJID, TRT01P)
s_water <- read.csv(required[3], stringsAsFactors = FALSE) |>
  rename_with(toupper) |>
  select(USUBJID, TRT01P, BEST, RESPCAT) |>
  arrange(USUBJID, TRT01P)
water_ok <- nrow(r_water) == nrow(s_water) &&
  identical(r_water$USUBJID, s_water$USUBJID) &&
  identical(r_water$TRT01P, s_water$TRT01P) &&
  # PROC EXPORT respects the SAS display format; tolerate only its last
  # serialized decimal place (the in-session plot uses the unrounded value).
  max(abs(r_water$BEST - s_water$BEST)) < 1e-8 &&
  identical(r_water$RESPCAT, s_water$RESPCAT)
if (water_ok) pass("Waterfall", sprintf("%d subjects/values/categories identical", nrow(r_water))) else
  fail("Waterfall", "figure-driving records differ")

# Swimmer selected subject set, durations, and event markers.
r_swim <- adsl |>
  transmute(USUBJID, TRT01P, DURM = TRTDURD / 30.4375,
            DEATH = as.integer(DTHFL == "Y")) |>
  arrange(TRT01P, desc(DURM)) |>
  group_by(TRT01P) |>
  slice_head(n = 30) |>
  ungroup() |>
  arrange(USUBJID, TRT01P)
s_swim <- read.csv(required[4], stringsAsFactors = FALSE) |>
  rename_with(toupper) |>
  select(USUBJID, TRT01P, DURM, DEATH) |>
  arrange(USUBJID, TRT01P)
swim_ok <- nrow(r_swim) == nrow(s_swim) &&
  identical(r_swim$USUBJID, s_swim$USUBJID) &&
  identical(r_swim$TRT01P, s_swim$TRT01P) &&
  max(abs(r_swim$DURM - s_swim$DURM)) < 1e-10 &&
  identical(r_swim$DEATH, as.integer(s_swim$DEATH))
if (swim_ok) pass("Swimmer", "60 subjects, durations, and death markers identical") else
  fail("Swimmer", "figure-driving records differ")

# Exposure-response joined observations.
nadir_er <- adlb |>
  filter(PARAMCD == "ANCNADIR", AVISIT == "CYCLE 1") |>
  select(USUBJID, ANC = AVAL)
r_er <- adex |>
  filter(PARAMCD == "RDI", AVISIT == "ALL CYCLES") |>
  select(USUBJID, TRT01P, RDI = AVAL) |>
  inner_join(nadir_er, by = "USUBJID") |>
  arrange(USUBJID, TRT01P)
s_er <- read.csv(required[5], stringsAsFactors = FALSE) |>
  rename_with(toupper) |>
  select(USUBJID, TRT01P, RDI, ANC) |>
  arrange(USUBJID, TRT01P)
er_ok <- nrow(r_er) == nrow(s_er) &&
  identical(r_er$USUBJID, s_er$USUBJID) &&
  identical(r_er$TRT01P, s_er$TRT01P) &&
  max(abs(r_er$RDI - s_er$RDI)) <= 0.00501 &&
  max(abs(r_er$ANC - s_er$ANC)) < 1e-8
if (er_ok) pass("Exposure-response", sprintf("%d joined observations identical", nrow(r_er))) else
  fail("Exposure-response", "figure-driving records differ")

cat("==========================================================\n")
if (!ok) quit(save = "no", status = 1)
cat("FIGURE-DATA RECONCILIATION: PASS\n")

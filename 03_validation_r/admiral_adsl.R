# Program: admiral_adsl.R | Author: Antony Bevan, Clinical Programming
# Description: THIRD independent derivation track for TROPIC ADSL using the
#   pharmaverse `admiral` package (industry-standard, validated ADaM tooling).
#   This complements the SAS production track (A_adsl_generation.sas) and the
#   hand-rolled R validation track (v_adsl_validation.R): same de-identified
#   staging inputs and the same study date model, but the ADaM derivation steps
#   are expressed with admiral verbs (derive_vars_merged, derive_var_trtdurd).
#   It is reconciled against the SAS production output by
#   05_reconciliation/admiral_reconcile.R (admiral-derivable CORE variables only).
#
# SCOPE (honest): admiral re-derives the standard, admiral-idiomatic ADSL core —
#   treatment dates/duration, survival dates, demographics, population flags. The
#   study-specific baseline covariates (PSABL/ECOGBL/PAINBL/… and their *IF
#   imputation flags) are NOT admiral-native derivations and remain covered by the
#   existing SAS+R double-programming; they are out of scope here by design.

suppressMessages({
  library(dplyr)
  library(lubridate)
  library(admiral)
  library(haven)
})

source("03_validation_r/config_study.R")

cat("NOTE: [ADMIRAL] Starting ADSL admiral re-derivation...\n")

st <- "01_raw_source/real_sdtm/staging"
dm <- readRDS(file.path(st, "dm.rds"))
ex <- readRDS(file.path(st, "ex.rds"))
ds <- readRDS(file.path(st, "ds.rds"))

# --- Prepare clean date inputs (study date model) ----------------------------
# Treatment exposure dates from EX (ISO datetime -> date).
# Only complete (>= 10-char) ISO dates are parsed; partial dates (e.g. "2008-08")
# are set missing, matching the production date convention (a partial end date must
# not win the TRTEDT extreme over a complete date).
ex2 <- ex |>
  mutate(
    EXSTDT = ymd(if_else(nchar(EXSTDTC) >= 10, substr(EXSTDTC, 1, 10), NA_character_),
                 quiet = TRUE),
    EXENDT = ymd(if_else(nchar(EXENDTC) >= 10, substr(EXENDTC, 1, 10), NA_character_),
                 quiet = TRUE)
  )

# Disposition event dates: de-identified week offset anchored on RFSTDTC
# (DSSTWK == 1 is the randomisation week), matching the production date model.
ds2 <- ds |>
  left_join(select(dm, USUBJID, RFSTDTC), by = "USUBJID") |>
  mutate(DSDT = ymd(substr(RFSTDTC, 1, 10), quiet = TRUE) + days((DSSTWK - 1) * 7))

# --- Build ADSL: one row per subject from DM, then admiral merges ------------
adsl <- dm |>
  transmute(
    STUDYID = STUDYID,
    USUBJID = USUBJID,
    SUBJID  = SUBJID,
    SITEID  = substr(SUBJID, 1, 3),
    RANDDT  = ymd(substr(RFSTDTC, 1, 10), quiet = TRUE),
    AGE     = if_else(AGEGRP == ">=85", 85, suppressWarnings(as.numeric(AGEGRP))),
    SEX     = "M",
    ITTFL   = coalesce(ITT, "N"),
    SAFFL   = coalesce(SAFETY, "N"),
    TRT01P  = TRT01P_CODE,
    TRT01PN = TRT01PN_CODE
  ) |>
  mutate(
    AGEGR1  = if_else(AGE < AGE_STRAT_CUT, "<65", ">=65"),
    AGEGR1N = if_else(AGE < AGE_STRAT_CUT, 1, 2)
  ) |>
  # Treatment start = first dosing date; treatment end = last dosing end date.
  derive_vars_merged(
    dataset_add = ex2, by_vars = exprs(USUBJID),
    order = exprs(EXSTDT), new_vars = exprs(TRTSDT = EXSTDT),
    mode = "first", filter_add = !is.na(EXSTDT)
  ) |>
  derive_vars_merged(
    dataset_add = ex2, by_vars = exprs(USUBJID),
    order = exprs(EXENDT), new_vars = exprs(TRTEDT = EXENDT),
    mode = "last", filter_add = !is.na(EXENDT)
  ) |>
  # Treatment duration (admiral: TRTEDT - TRTSDT + 1).
  derive_var_trtdurd() |>
  # Death date = earliest DEATH/DEAD disposition; last known alive = latest of any
  # disposition record (admiral extreme-record merges).
  derive_vars_merged(
    dataset_add = ds2, by_vars = exprs(USUBJID),
    order = exprs(DSDT), new_vars = exprs(DTHDT = DSDT),
    mode = "first", filter_add = DSDECOD %in% c("DEATH", "DEAD") & !is.na(DSDT)
  ) |>
  derive_vars_merged(
    dataset_add = ds2, by_vars = exprs(USUBJID),
    order = exprs(DSDT), new_vars = exprs(LSTALVDT = DSDT),
    mode = "last", filter_add = !is.na(DSDT)
  ) |>
  mutate(DTHFL = if_else(!is.na(DTHDT), "Y", "N")) |>
  arrange(USUBJID)

# --- Guard + write -----------------------------------------------------------
if (nrow(adsl) != 371) {
  stop(sprintf("ERROR: [ADMIRAL] ADSL expected 371 subjects, got %d", nrow(adsl)))
}

for (.dv in names(adsl)) {
  if (inherits(adsl[[.dv]], "Date")) attr(adsl[[.dv]], "format.sas") <- "DATE9."
}
names(adsl) <- toupper(names(adsl))
dir.create("04_adam", showWarnings = FALSE)
write_xpt(adsl, "04_adam/adsl_admiral.xpt")
cat(sprintf("NOTE: [ADMIRAL] Wrote 04_adam/adsl_admiral.xpt (%d subjects, %d vars)\n",
            nrow(adsl), ncol(adsl)))

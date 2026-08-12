# Program: admiral_adsl.R | Author: Antony Bevan, Clinical Programming
# Description: THIRD independent derivation track for TROPIC ADSL using the
#   pharmaverse `admiral` package (industry-standard, validated ADaM tooling).
#   This complements the SAS production track (A_adsl_generation.sas) and the
#   hand-rolled R validation track (v_adsl_validation.R): same de-identified
#   staging inputs and the same study date model, but the ADaM derivation steps
#   are expressed with admiral verbs (derive_vars_merged, derive_var_trtdurd).
#   It is reconciled against the SAS production output by
#   06_qc_evidence/reconciliation/admiral_reconcile.R (admiral-derivable CORE variables only).
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

source("04_analysis_datasets/programs/r/config_study.R")

cat("NOTE: [ADMIRAL] Starting ADSL admiral re-derivation...\n")

dm <- readRDS(stage_file("dm"))
ex <- readRDS(stage_file("ex"))
ds <- readRDS(stage_file("ds"))
vs <- readRDS(stage_file("vs"))
lb <- readRDS(stage_file("lb"))
ls <- readRDS(stage_file("ls"))
pn <- readRDS(stage_file("pn"))
sv <- readRDS(stage_file("sv"))
ae <- readRDS(stage_file("ae"))

date10 <- function(x) {
  value <- substr(as.character(x), 1, 10)
  ymd(
    if_else(
      grepl("^\\d{4}-\\d{2}-\\d{2}$", value),
      value,
      NA_character_
    ),
    quiet = TRUE
  )
}

# --- Prepare clean date inputs (study date model) ----------------------------
# Treatment exposure dates from EX (ISO datetime -> date).
# Only complete (>= 10-char) ISO dates are parsed; partial dates (e.g. "2008-08")
# are set missing, matching the production date convention (a partial end date must
# not win the TRTEDT extreme over a complete date).
ex2 <- ex |>
  mutate(
    EXSTDT = date10(EXSTDTC),
    EXENDT = date10(EXENDTC)
  )

ex_start_src <- ex2 |>
  filter(!is.na(EXSTDT)) |>
  distinct(USUBJID, EXSTDT)
ex_end_src <- ex2 |>
  filter(!is.na(EXENDT)) |>
  distinct(USUBJID, EXENDT)

# Disposition event dates: de-identified week offset anchored on RFSTDTC
# (DSSTWK == 1 is the randomisation week), matching the production date model.
ds2 <- ds |>
  left_join(select(dm, USUBJID, RFSTDTC), by = "USUBJID") |>
  mutate(DSDT = date10(RFSTDTC) + days((as.numeric(DSSTWK) - 1) * 7))

# Actual treatment is independently classified from the qualifying administered
# IV antineoplastic, preserving planned/actual discrepancies in the third track.
actual_trt <- ex |>
  group_by(USUBJID) |>
  summarise(
    has_cbzp = any(grepl("XRP|CABAZ", coalesce(EXTRT, ""), ignore.case = TRUE)),
    has_mp = any(grepl("MITOX", coalesce(EXTRT, ""), ignore.case = TRUE)),
    .groups = "drop"
  )

# Prefer complete source-reported AE death dates. DS provides a week-anchored
# fallback and cause; this source assembly is intentionally independent of the
# production program while preserving the same precision hierarchy.
death_approx <- ds2 |>
  filter(DSDECOD %in% c("DEATH", "DEAD"), !is.na(DSDT)) |>
  arrange(USUBJID, DSDT, DSSEQ) |>
  group_by(USUBJID) |>
  summarise(
    approx_dthdt = first(DSDT),
    DTHCAUS = first(DSTERM),
    .groups = "drop"
  )

death_exact <- ae |>
  filter(!is.na(AEDTHDTC), nchar(AEDTHDTC) >= 10) |>
  transmute(USUBJID, exact_dthdt = date10(AEDTHDTC)) |>
  filter(!is.na(exact_dthdt)) |>
  group_by(USUBJID) |>
  summarise(exact_dthdt = min(exact_dthdt), .groups = "drop")

death_src <- full_join(death_approx, death_exact, by = "USUBJID") |>
  transmute(USUBJID, DTHDT = coalesce(exact_dthdt, approx_dthdt), DTHCAUS)

# Last-known-alive uses the latest dated observed contact/assessment and is
# capped at death below. The domain set matches the governed production rule.
contact_src <- bind_rows(
  transmute(ds2, USUBJID, CONTACTDT = DSDT),
  transmute(ex, USUBJID, CONTACTDT = date10(EXSTDTC)),
  transmute(ex, USUBJID, CONTACTDT = date10(EXENDTC)),
  transmute(vs, USUBJID, CONTACTDT = date10(VSDTC)),
  transmute(lb, USUBJID, CONTACTDT = date10(LBDTC)),
  transmute(ls, USUBJID, CONTACTDT = date10(LSDTC)),
  transmute(pn, USUBJID, CONTACTDT = date10(PNDTC)),
  transmute(sv, USUBJID, CONTACTDT = date10(SVSTDTC)),
  transmute(sv, USUBJID, CONTACTDT = date10(SVENDTC))
) |>
  filter(!is.na(CONTACTDT)) |>
  group_by(USUBJID) |>
  summarise(LSTALVDT = max(CONTACTDT), .groups = "drop")

# --- Build ADSL: one row per subject from DM, then admiral merges ------------
adsl <- dm |>
  transmute(
    STUDYID = STUDYID,
    USUBJID = USUBJID,
    SUBJID  = SUBJID,
    SITEID  = substr(SUBJID, 1, 3),
    RANDDT  = date10(RFSTDTC),
    AGE     = if_else(AGEGRP == ">=85", 85, suppressWarnings(as.numeric(AGEGRP))),
    SEX     = "M",
    ITTFL   = coalesce(ITT, "N"),
    SAFFL   = coalesce(SAFETY, "N"),
    TRT01P = case_when(
      grepl("MITOX", ARM, ignore.case = TRUE) | ARMCD == "A" ~ "MP",
      grepl("CABAZ|XRP", ARM, ignore.case = TRUE) ~ "CbzP",
      TRUE ~ TRT01P_CODE
    ),
    TRT01PN = case_when(
      grepl("MITOX", ARM, ignore.case = TRUE) | ARMCD == "A" ~ 2L,
      grepl("CABAZ|XRP", ARM, ignore.case = TRUE) ~ 1L,
      TRUE ~ as.integer(TRT01PN_CODE)
    )
  ) |>
  mutate(
    AGEGR1  = if_else(AGE < AGE_STRAT_CUT, "<65", ">=65"),
    AGEGR1N = if_else(AGE < AGE_STRAT_CUT, 1, 2)
  ) |>
  # Treatment start = first dosing date; treatment end = last dosing end date.
  derive_vars_merged(
    dataset_add = ex_start_src, by_vars = exprs(USUBJID),
    order = exprs(EXSTDT), new_vars = exprs(TRTSDT = EXSTDT),
    mode = "first", filter_add = !is.na(EXSTDT)
  ) |>
  derive_vars_merged(
    dataset_add = ex_end_src, by_vars = exprs(USUBJID),
    order = exprs(EXENDT), new_vars = exprs(TRTEDT = EXENDT),
    mode = "last", filter_add = !is.na(EXENDT)
  ) |>
  # Treatment duration (admiral: TRTEDT - TRTSDT + 1).
  derive_var_trtdurd() |>
  left_join(actual_trt, by = "USUBJID") |>
  left_join(death_src, by = "USUBJID") |>
  left_join(contact_src, by = "USUBJID") |>
  mutate(
    TRT01A = case_when(
      has_cbzp ~ "CbzP",
      has_mp ~ "MP",
      TRUE ~ TRT01P
    ),
    TRT01AN = case_when(
      has_cbzp ~ 1L,
      has_mp ~ 2L,
      TRUE ~ TRT01PN
    ),
    DTHFL = if_else(!is.na(DTHDT), "Y", "N"),
    LSTALVDT = if_else(
      DTHFL == "Y" & !is.na(DTHDT) & LSTALVDT > DTHDT,
      DTHDT,
      LSTALVDT
    )
  ) |>
  select(-has_cbzp, -has_mp) |>
  arrange(USUBJID)

# --- Guard + write -----------------------------------------------------------
if (nrow(adsl) != 371) {
  stop(sprintf("ERROR: [ADMIRAL] ADSL expected 371 subjects, got %d", nrow(adsl)))
}
if (any(adsl$DTHFL == "Y" & is.na(adsl$DTHDT))) {
  stop("ERROR: [ADMIRAL] death flag/date inconsistency")
}
if (any(!is.na(adsl$DTHDT) & adsl$LSTALVDT > adsl$DTHDT)) {
  stop("ERROR: [ADMIRAL] last-known-alive date exceeds death date")
}

for (.dv in names(adsl)) {
  if (inherits(adsl[[.dv]], "Date")) attr(adsl[[.dv]], "format.sas") <- "DATE9."
}
names(adsl) <- toupper(names(adsl))
dir.create("04_analysis_datasets/adam", showWarnings = FALSE)
write_xpt(adsl, "04_analysis_datasets/adam/adsl_admiral.xpt")
cat(sprintf("NOTE: [ADMIRAL] Wrote 04_analysis_datasets/adam/adsl_admiral.xpt (%d subjects, %d vars)\n",
            nrow(adsl), ncol(adsl)))

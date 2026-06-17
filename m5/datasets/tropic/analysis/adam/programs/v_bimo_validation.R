# =============================================================================
# Program: v_bimo_validation.R
# Author : Antony Bevan, Clinical Programming
# Purpose: Independent R validation of the BIMO summary-level clinical-site
#          dataset (clinsite). Mirrors B_bimo_generation.sas exactly so the two
#          tracks can be reconciled SAS<->R on the (STUDYID, SITEID) key.
#
# Scope/limitations are documented in 08_reviewers_guides/BDRG.md. In particular
# INVNAM is a SYNTHETIC placeholder (the de-identified release has no PI identity),
# and populations follow ICH E9 as DISTINCT sets - ITT is not relabelled "Efficacy".
# =============================================================================

library(dplyr)
library(haven)
source("03_validation_r/config_study.R")

adsl <- read_xpt("04_adam/adsl_v.xpt")
adae <- read_xpt("04_adam/adae_v.xpt")

# Site-level population counts from ADSL (one row per subject).
bimo_adsl <- adsl |>
  group_by(STUDYID, SITEID) |>
  summarise(
    N_RAND  = n_distinct(USUBJID),
    N_SAF   = sum(SAFFL == "Y", na.rm = TRUE),
    N_ITT   = sum(ITTFL == "Y", na.rm = TRUE),
    N_PPROT = sum(PPROTFL == "Y", na.rm = TRUE),
    N_DEATH = sum(DTHFL == "Y", na.rm = TRUE),
    .groups = "drop"
  )

# Site-level safety counts from ADAE: route subjects to their site via ADSL, then
# count unique subjects per site with a serious AE / a treatment-emergent AE.
bimo_ae <- adsl |>
  select(USUBJID, SITEID) |>
  left_join(adae |> select(USUBJID, AESER, TRTEMFL), by = "USUBJID") |>
  group_by(SITEID) |>
  summarise(
    N_SAE  = n_distinct(USUBJID[!is.na(AESER) & AESER == "Y"]),
    N_TEAE = n_distinct(USUBJID[!is.na(TRTEMFL) & TRTEMFL == "Y"]),
    .groups = "drop"
  )

clinsite <- bimo_adsl |>
  left_join(bimo_ae, by = "SITEID") |>
  mutate(
    INVNAM = paste("PI", trimws(SITEID), sep = "_"),
    N_SAE  = dplyr::coalesce(N_SAE, 0L),
    N_TEAE = dplyr::coalesce(N_TEAE, 0L)
  ) |>
  select(STUDYID, SITEID, INVNAM, N_RAND, N_SAF, N_ITT, N_PPROT, N_DEATH, N_SAE, N_TEAE) |>
  arrange(STUDYID, SITEID)

# F-7: explicit structural conformance gate. The BIMO clinsite is intentionally not in
# the ADaM define.xml, so adam_conf_check.R never sees it; assert its schema here so a
# silent column/type drift fails the stage rather than passing only the cell-diff.
expected_cols <- c(
  "STUDYID", "SITEID", "INVNAM", "N_RAND", "N_SAF",
  "N_ITT", "N_PPROT", "N_DEATH", "N_SAE", "N_TEAE"
)
if (!identical(names(clinsite), expected_cols)) {
  stop(sprintf(
    "BIMO clinsite schema drift: expected [%s], got [%s]",
    paste(expected_cols, collapse = ", "),
    paste(names(clinsite), collapse = ", ")
  ))
}
char_cols <- c("STUDYID", "SITEID", "INVNAM")
num_cols <- setdiff(expected_cols, char_cols)
stopifnot(
  "clinsite char columns must be character" =
    all(vapply(clinsite[char_cols], is.character, logical(1))),
  "clinsite count columns must be numeric" =
    all(vapply(clinsite[num_cols], is.numeric, logical(1))),
  "clinsite must be one row per site (unique SITEID)" =
    anyDuplicated(clinsite$SITEID) == 0L
)

# BIMO labels (match B_bimo_generation.sas).
attr(clinsite$STUDYID, "label") <- "Study Identifier"
attr(clinsite$SITEID, "label")  <- "Study Site Identifier"
attr(clinsite$INVNAM, "label")  <- "Principal Investigator (SYNTHETIC placeholder - see BDRG)"
attr(clinsite$N_RAND, "label")  <- "Number of Subjects Randomized"
attr(clinsite$N_SAF, "label")   <- "Number of Subjects Treated (Safety Population)"
attr(clinsite$N_ITT, "label")   <- "Number of Subjects in ITT Population"
attr(clinsite$N_PPROT, "label") <- "Number of Subjects in Per-Protocol Population"
attr(clinsite$N_DEATH, "label") <- "Number of Subjects Who Died"
attr(clinsite$N_SAE, "label")   <- "Number of Subjects with a Serious AE"
attr(clinsite$N_TEAE, "label")  <- "Number of Subjects with a TEAE"

haven::write_xpt(clinsite, "04_adam/clinsite_v.xpt", name = "CLINSITE")
cat(sprintf(
  "NOTE: [VALIDATION] Wrote validation CLINSITE: 04_adam/clinsite_v.xpt (%d sites)\n",
  nrow(clinsite)
))

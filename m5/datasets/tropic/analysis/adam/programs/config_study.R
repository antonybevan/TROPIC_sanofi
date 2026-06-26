# config_study.R — read from governed study_config.yaml
# Version: 3.5.0
# Date: 2026-06-12
# Reference: TROPIC SAP v4.0 controlled draft (EFC6193 / XRP6258)

config_file <- "study_config.yaml"
if (!file.exists(config_file)) {
  if (file.exists(file.path("..", "study_config.yaml"))) {
    config_file <- file.path("..", "study_config.yaml")
  } else {
    stop("study_config.yaml not found in . or ..")
  }
}

cfg <- yaml::read_yaml(config_file)

STUDYID           <- as.character(cfg$STUDYID)
TRT01P_CODE       <- as.character(cfg$TRT01P_CODE)
TRT01PN_CODE      <- as.integer(cfg$TRT01PN_CODE)

STUDY_CUTOFF_DT   <- as.Date(cfg$STUDY_CUTOFF_DT)

PLANNED_DOSE      <- as.numeric(cfg$PLANNED_DOSE)
AGE_STRAT_CUT     <- as.integer(cfg$AGE_STRAT_CUT)

# Missing data imputation defaults (no formal SAP imputation section; method per ADRG §5.1)
ECOGBL_DEFAULT    <- as.numeric(cfg$ECOGBL_DEFAULT)
PSABL_DEFAULT     <- as.numeric(cfg$PSABL_DEFAULT)
ALPBL_DEFAULT     <- as.numeric(cfg$ALPBL_DEFAULT)
HGBBL_DEFAULT     <- as.numeric(cfg$HGBBL_DEFAULT)
ALBBL_DEFAULT     <- as.numeric(cfg$ALBBL_DEFAULT)
LDHBL_DEFAULT     <- as.numeric(cfg$LDHBL_DEFAULT)

# RECIST v1.0 response thresholds (SAP v4.0 §10.3)
RECIST_PD_PCT     <- as.numeric(cfg$RECIST_PD_PCT)
RECIST_PD_ABS     <- as.numeric(cfg$RECIST_PD_ABS)
RECIST_PR_PCT     <- as.numeric(cfg$RECIST_PR_PCT)
RECIST_CONFIRM_DAYS <- as.integer(cfg$RECIST_CONFIRM_DAYS)

# PCWG3 bone-scan 2+2 progression (Scher 2016 — methodological demonstration; see ADRG §4A)
BONE_PROG_MIN_NEW     <- as.integer(cfg$BONE_PROG_MIN_NEW)
BONE_PROG_CONFIRM_NEW <- as.integer(cfg$BONE_PROG_CONFIRM_NEW)

# PSA thresholds (SAP v4.0 §10.2)
PSA_RESP_THRESHOLD   <- as.numeric(cfg$PSA_RESP_THRESHOLD)
PSA_RESP_CONFIRM     <- as.integer(cfg$PSA_RESP_CONFIRM)
PSA_PROG_MULT_RESP   <- as.numeric(cfg$PSA_PROG_MULT_RESP)
PSA_PROG_MULT_NORESP <- as.numeric(cfg$PSA_PROG_MULT_NORESP)
PSA_PROG_ABS         <- as.numeric(cfg$PSA_PROG_ABS)
PSA_PROG_CONFIRM     <- as.integer(cfg$PSA_PROG_CONFIRM)

# OCCDS v1.0 continuous episode merging (SAP §7.7, Custom Query 02)
EPISODE_GAP_DAYS  <- as.integer(cfg$EPISODE_GAP_DAYS)

# Project Optimus ANC kinetics (SAP v4.0 §12)
ANC_RECOVERY_THRESHOLD <- as.numeric(cfg$ANC_RECOVERY_THRESHOLD)

# LB analysis windows — study days from TRTSDT (SAP v4.0 §14)
W_BL_HI    <- as.integer(cfg$W_BL_HI)
W_C1D1_LO  <- as.integer(cfg$W_C1D1_LO)
W_C1D1_HI  <- as.integer(cfg$W_C1D1_HI)
W_C1D8_LO  <- as.integer(cfg$W_C1D8_LO)
W_C1D8_HI  <- as.integer(cfg$W_C1D8_HI)
W_C1D15_LO <- as.integer(cfg$W_C1D15_LO)
W_C1D15_HI <- as.integer(cfg$W_C1D15_HI)
W_C2D1_LO  <- as.integer(cfg$W_C2D1_LO)
W_C2D1_HI  <- as.integer(cfg$W_C2D1_HI)
W_C2D8_LO  <- as.integer(cfg$W_C2D8_LO)
W_C2D8_HI  <- as.integer(cfg$W_C2D8_HI)
W_C3D1_LO  <- as.integer(cfg$W_C3D1_LO)
W_C3D1_HI  <- as.integer(cfg$W_C3D1_HI)

# Staging data path (relative to project root)
STAGING_PATH <- do.call(file.path, as.list(strsplit(cfg$STAGING_PATH, "/")[[1]]))

# --------------------------------------------------------------------------- #
# write_xpt_v(): xportr_write wrapper for the R validation track.
#
# Validation-track outputs use a deliberate `<domain>_v.xpt` naming convention to
# keep them distinct from the SAS production `<domain>_prod.xpt` the reconciliation
# compares against. The underscore in that member name is valid for a SAS v5
# transport file, but xportr's name check (stricter than the v5 spec — it rejects
# underscores) emits a benign warning:
#   "The following validation checks failed: `.df` cannot contain any non-ASCII,
#    symbol or underscore characters."
# That single, known false-positive is the only thing standing between the nine
# validation logs and a clean Errors/Warnings section. Muffle ONLY that exact
# message; every other xportr warning (real label/type/length violations) still
# surfaces in the log untouched.
# spec-sourced variable labels (GENERATED: 06_telemetry/gen_adam_labels.R from the authoritative
# 00_specifications/ADaM_spec.xlsx — audit C-4 inversion). Applied so the R validation-track datasets
# carry the same spec labels as the SAS production track — closes the missing-label ADaM conformance
# findings (06_telemetry/adam_conformance_report.md) symmetrically.
.adam_label_spec <- local({
  p <- Filter(file.exists, c("03_validation_r/adam_var_labels.csv", "adam_var_labels.csv"))
  if (length(p)) utils::read.csv(p[[1]], stringsAsFactors = FALSE, colClasses = "character")
  else data.frame(dataset = character(), variable = character(), label = character())
})

write_xpt_v <- function(.df, path, domain) {
  sp <- .adam_label_spec[.adam_label_spec$dataset == toupper(domain), ]
  for (i in seq_len(nrow(sp)))
    if (sp$variable[i] %in% names(.df)) attr(.df[[sp$variable[i]]], "label") <- sp$label[i]
  withCallingHandlers(
    xportr::xportr_write(.df, path, domain = domain),
    warning = function(w) {
      if (grepl("non-ASCII, symbol or underscore", conditionMessage(w), fixed = TRUE)) {
        invokeRestart("muffleWarning")
      }
    }
  )
}

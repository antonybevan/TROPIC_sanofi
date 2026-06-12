# config_study.R — read from single source of truth study_config.yaml
# Version: 3.5.0
# Date: 2026-06-12
# Reference: TROPIC SAP v3.0 (EFC6193 / XRP6258)

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

# Missing data imputation defaults (SAP §6.3)
ECOGBL_DEFAULT    <- as.numeric(cfg$ECOGBL_DEFAULT)
PSABL_DEFAULT     <- as.numeric(cfg$PSABL_DEFAULT)
ALPBL_DEFAULT     <- as.numeric(cfg$ALPBL_DEFAULT)
HGBBL_DEFAULT     <- as.numeric(cfg$HGBBL_DEFAULT)
ALBBL_DEFAULT     <- as.numeric(cfg$ALBBL_DEFAULT)
LDHBL_DEFAULT     <- as.numeric(cfg$LDHBL_DEFAULT)

# RECIST v1.0 response thresholds (SAP §5.3)
RECIST_PD_PCT     <- as.numeric(cfg$RECIST_PD_PCT)
RECIST_PD_ABS     <- as.numeric(cfg$RECIST_PD_ABS)
RECIST_PR_PCT     <- as.numeric(cfg$RECIST_PR_PCT)

# PCWG3 PSA thresholds (SAP §5.4)
PSA_RESP_THRESHOLD   <- as.numeric(cfg$PSA_RESP_THRESHOLD)
PSA_RESP_CONFIRM     <- as.integer(cfg$PSA_RESP_CONFIRM)
PSA_PROG_MULT_RESP   <- as.numeric(cfg$PSA_PROG_MULT_RESP)
PSA_PROG_MULT_NORESP <- as.numeric(cfg$PSA_PROG_MULT_NORESP)
PSA_PROG_ABS         <- as.numeric(cfg$PSA_PROG_ABS)
PSA_PROG_CONFIRM     <- as.integer(cfg$PSA_PROG_CONFIRM)

# OCCDS v1.1 continuous episode merging (SAP §5.2, Custom Query 02)
EPISODE_GAP_DAYS  <- as.integer(cfg$EPISODE_GAP_DAYS)

# Project Optimus ANC kinetics (SAP §5.5)
ANC_RECOVERY_THRESHOLD <- as.numeric(cfg$ANC_RECOVERY_THRESHOLD)

# LB analysis windows — study days from TRTSDT (SAP §5.6)
W_BL_HI    <- as.integer(cfg$W_BL_HI)
W_C1D1_LO  <- as.integer(cfg$W_C1D1_LO);  W_C1D1_HI  <- as.integer(cfg$W_C1D1_HI)
W_C1D8_LO  <- as.integer(cfg$W_C1D8_LO);  W_C1D8_HI  <- as.integer(cfg$W_C1D8_HI)
W_C1D15_LO <- as.integer(cfg$W_C1D15_LO); W_C1D15_HI <- as.integer(cfg$W_C1D15_HI)
W_C2D1_LO  <- as.integer(cfg$W_C2D1_LO);  W_C2D1_HI  <- as.integer(cfg$W_C2D1_HI)
W_C2D8_LO  <- as.integer(cfg$W_C2D8_LO);  W_C2D8_HI  <- as.integer(cfg$W_C2D8_HI)
W_C3D1_LO  <- as.integer(cfg$W_C3D1_LO);  W_C3D1_HI  <- as.integer(cfg$W_C3D1_HI)

# Staging data path (relative to project root)
STAGING_PATH <- do.call(file.path, as.list(strsplit(cfg$STAGING_PATH, "/")[[1]]))


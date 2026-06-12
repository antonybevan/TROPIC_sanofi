# config_study.R — single source of truth for study parameters
# Reference: TROPIC SAP v3.0 (EFC6193 / XRP6258)
# Sourced at the top of every validation script; mirrors 00_config.sas constants.

STUDYID           <- "TROPIC-NCT00417079"
TRT01P_CODE       <- "MP"
TRT01PN_CODE      <- 2L

STUDY_CUTOFF_DT   <- as.Date("2009-09-25")  # DSMB follow-up cutoff

PLANNED_DOSE      <- 12.0   # Mitoxantrone mg/m2 per cycle
AGE_STRAT_CUT     <- 65L    # Stratification age cutoff (years)

# Missing data imputation defaults (SAP §6.3)
ECOGBL_DEFAULT    <- 1.0
PSABL_DEFAULT     <- 110.0
ALPBL_DEFAULT     <- 140.0
HGBBL_DEFAULT     <- 11.5
ALBBL_DEFAULT     <- 38.0   # g/dL — population reference mean
LDHBL_DEFAULT     <- 220.0  # U/L  — population reference mean

# RECIST v1.0 response thresholds (SAP §5.3)
RECIST_PD_PCT     <- 20.0   # % increase from nadir = PD
RECIST_PD_ABS     <- 5.0    # mm absolute minimum = PD
RECIST_PR_PCT     <- -30.0  # % decrease from baseline = PR

# PCWG3 PSA thresholds (SAP §5.4)
PSA_RESP_THRESHOLD   <- 0.5   # >= 50% decline from baseline
PSA_RESP_CONFIRM     <- 21L   # days between confirming measurements
PSA_PROG_MULT_RESP   <- 1.5   # PSA responder: >= 1.5x nadir
PSA_PROG_MULT_NORESP <- 1.25  # Non-responder: >= 1.25x nadir
PSA_PROG_ABS         <- 5.0   # Absolute increment >= 5 ng/mL
PSA_PROG_CONFIRM     <- 7L    # Confirmation within 7 days

# OCCDS v1.1 continuous episode merging (SAP §5.2, Custom Query 02)
EPISODE_GAP_DAYS  <- 3L     # <= 3-day gap = same episode

# Project Optimus ANC kinetics (SAP §5.5)
ANC_RECOVERY_THRESHOLD <- 1.5  # x10^3/uL

# LB analysis windows — study days from TRTSDT (SAP §5.6)
W_BL_HI    <- 0L
W_C1D1_LO  <- 1L;  W_C1D1_HI  <- 3L
W_C1D8_LO  <- 4L;  W_C1D8_HI  <- 13L
W_C1D15_LO <- 14L; W_C1D15_HI <- 17L
W_C2D1_LO  <- 18L; W_C2D1_HI  <- 24L
W_C2D8_LO  <- 25L; W_C2D8_HI  <- 34L
W_C3D1_LO  <- 39L; W_C3D1_HI  <- 45L

# Staging data path (relative to project root)
STAGING_PATH <- file.path("01_raw_source", "real_sdtm", "staging")

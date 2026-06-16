# Program: v_adtte_validation.R | Version: 2.4.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-06-13
# Standard: ADaMIG v1.3 BDS-TTE | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADTTE.
#
# Remediation v2.4.0 (roadmap #2/#3/#4/#5/#7/#10). This track is structured
# around an explicit branch enumeration + a single finalize_tte() contract
# rather than mirroring the SAS control flow statement-for-statement (#5).
# Output content is identical to the SAS production track by design (that is the
# point of the reconciliation); true clean-room independence is bounded here by
# single authorship and is disclosed as such in ADRG §6.
# Rules implemented (must match A_adtte_generation.sas exactly):
#   Rule 4  Population per parameter, carried on-record (ITTFL + SAFFL):
#         OS, PFS        -> ITT  (ITTFL is "Y")
#         TTSAE, TTPAIN,
#         TTPSA          -> Safety (SAFFL is "Y")
#         TTUMOR         -> Safety and MEASDISF is "Y"
#   Rule 3  PSA-progression censoring date read from ADLB (adlb_v.xpt,
#       where PARAMCD is "PSA"), an ADaM input -- not raw staging LB.
#   Rule 2  Same-day pain scores aggregated with min() (order-independent;
#       matches SAS).
#   Rule 7  PARAMN / PARCAT1 / AVALU carried.
#   Rule 10 Administrative cutoff applied to every censoring branch.

library(jsonlite)
library(dplyr)
library(haven)
library(lubridate)
library(tidyr)
library(xportr)

# Avoid linter warnings for column names in ggplot/dplyr pipelines
.env <- NULL
source("03_validation_r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADTTE Validation script...\n")

# Load ADaM inputs (validation reads ONLY *_v.xpt + staging — never *_prod.xpt)
df_adsl <- read_xpt("04_adam/adsl_v.xpt")
adrs    <- read_xpt("04_adam/adrs_v.xpt")
adcm    <- read_xpt("04_adam/adcm_v.xpt")
adae    <- read_xpt("04_adam/adae_v.xpt")
adlb    <- read_xpt("04_adam/adlb_v.xpt")

# ------------------------------------------------------------------------------
# Standard BDS-TTE output contract: one finalize step shared by every parameter,
# so each derivation only has to produce the raw event/censor decision.
# ------------------------------------------------------------------------------
adtte_cols <- c(
  "STUDYID", "USUBJID", "SUBJID", "SITEID", "TRT01P", "TRT01PN",
  "ITTFL", "SAFFL", "PARAMCD", "PARAM", "PARAMN", "PARCAT1",
  "STARTDT", "ADT", "AVAL", "AVALU", "CNSR", "EVNTDESC", "CNSDTDSC"
)

finalize_tte <- function(d) {
  # Audit MO-4: surface (do not silently mask) any event/censor date that precedes
  # the time origin before flooring it to 1 day, so a data anomaly is investigable.
  neg <- d[!is.na(d$ADT) & !is.na(d$STARTDT) & d$ADT < d$STARTDT, , drop = FALSE]
  if (nrow(neg) > 0) {
    ids <- if ("USUBJID" %in% names(neg)) {
      paste(utils::head(unique(neg$USUBJID), 3), collapse = ", ")
    } else {
      "n/a"
    }
    warning(sprintf(
      paste0("[ADTTE] %d record(s) have event/censor date before time origin ",
             "(e.g. %s); floored to 1 day - review source data."),
      nrow(neg), ids
    ))
  }
  d |>
    mutate(
      STUDYID = .env$STUDYID,
      ADT     = pmax(.data$STARTDT, .data$ADT),
      AVAL    = as.numeric(.data$ADT - .data$STARTDT + 1),
      AVALU   = "DAYS"
    ) |>
    select(all_of(adtte_cols))
}

# First event dates per subject, pulled once from the relevant ADaM domains.
first_pd <- adrs |>
  filter(
    (PARAMCD == "OVRLRESP" & AVALC == "PD") |
      (PARAMCD == "BSGRESP"  & AVALC == "PROGRESSION") |
      (PARAMCD == "PSPROG"   & AVALC == "Y")
  ) |>
  group_by(USUBJID) |>
  summarise(
    pd_dt = min(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

first_sae <- adae |>
  filter(AESER == "Y" & TRTEMFL == "Y" & !is.na(ASTDT)) |>
  group_by(USUBJID) |>
  summarise(
    sae_dt = min(as.Date(ASTDT, origin = "1960-01-01")),
    .groups = "drop"
  )

first_nact <- adcm |>
  filter(!is.na(NACTDT)) |>
  group_by(USUBJID) |>
  summarise(
    nactdt = min(as.Date(NACTDT, origin = "1960-01-01")),
    .groups = "drop"
  )

# ------------------------------------------------------------------------------
# OS — Overall Survival (ITT, anchored at randomisation)
# ------------------------------------------------------------------------------
os <- df_adsl |>
  filter(ITTFL == "Y") |>
  mutate(
    PARAMCD = "OS", PARAM = "Overall Survival", PARAMN = 1,
    PARCAT1 = "EFFICACY",
    STARTDT  = RANDDT,
    died     = DTHFL == "Y",
    ADT      = if_else(died, DTHDT, pmin(LSTALVDT, STUDY_CUTOFF_DT)),
    CNSR     = if_else(died, 0, 1),
    EVNTDESC = if_else(died, "DEATH", ""),
    CNSDTDSC = if_else(died, "", "LAST KNOWN ALIVE DATE")
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTSAE — Time to First Serious AE (Safety, anchored at first dose)
# ------------------------------------------------------------------------------
ttsae <- df_adsl |>
  filter(SAFFL == "Y") |>
  left_join(first_sae, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTSAE", PARAM = "Time to First Serious AE", PARAMN = 6,
    PARCAT1 = "SAFETY",
    STARTDT  = TRTSDT,
    had_sae  = !is.na(sae_dt),
    ADT      = if_else(had_sae, sae_dt, pmin(LSTALVDT, STUDY_CUTOFF_DT)),
    CNSR     = if_else(had_sae, 0, 1),
    EVNTDESC = if_else(had_sae, "SERIOUS ADVERSE EVENT", ""),
    CNSDTDSC = if_else(had_sae, "", "LAST KNOWN ALIVE DATE")
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# PFS — Progression-Free Survival (ITT). NACT-censoring hierarchy expressed as a
# single ordered branch label, then mapped to ADT/CNSR/EVNTDESC/CNSDTDSC.
# ------------------------------------------------------------------------------
pfs <- df_adsl |>
  filter(ITTFL == "Y") |>
  left_join(first_pd, by = "USUBJID") |>
  left_join(first_nact, by = "USUBJID") |>
  mutate(
    PARAMCD = "PFS", PARAM = "Progression Free Survival", PARAMN = 2,
    PARCAT1 = "EFFICACY",
    STARTDT = RANDDT,
    pd_found   = !is.na(pd_dt),
    nact_found = !is.na(nactdt),
    branch = case_when(
      pd_found & nact_found & nactdt < pd_dt            ~ "NACT_PRE_PD",
      pd_found                                          ~ "PD",
      DTHFL == "Y" & nact_found & nactdt < DTHDT        ~ "NACT_PRE_DEATH",
      DTHFL == "Y"                                      ~ "DEATH",
      nact_found                                        ~ "NACT_ONLY",
      TRUE                                              ~ "CENSOR_LASTEVAL"
    ),
    ADT = case_when(
      branch == "PD"    ~ pd_dt,
      branch == "DEATH" ~ DTHDT,
      branch %in% c("NACT_PRE_PD", "NACT_PRE_DEATH", "NACT_ONLY") ~
        nactdt - days(1),
      TRUE ~ pmin(LSTALVDT, STUDY_CUTOFF_DT)
    ),
    CNSR     = if_else(branch %in% c("PD", "DEATH"), 0, 1),
    EVNTDESC = case_when(
      branch == "PD"    ~ "TUMOR OR PSA PROGRESSION",
      branch == "DEATH" ~ "DEATH",
      TRUE ~ ""
    ),
    CNSDTDSC = case_when(
      branch %in% c("NACT_PRE_PD", "NACT_PRE_DEATH", "NACT_ONLY") ~
        "NEW ANTI-CANCER THERAPY START",
      branch == "CENSOR_LASTEVAL" ~ "LAST EVALUABLE TUMOR ASSESSMENT",
      TRUE ~ ""
    )
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTPAIN — Time to Pain Progression (Safety). PN has no ADaM intermediate; both
# tracks derive from the same reconciled staging PN (documented in ADRG/SDRG).
# Same-day scores aggregated with min() (#2).
# ------------------------------------------------------------------------------
pn <- readRDS("01_raw_source/real_sdtm/staging/pn.rds")

pn_anchored <- pn |>
  inner_join(
    df_adsl |> select(USUBJID, TRTSDT, RANDDT, LSTALVDT, SAFFL),
    by = "USUBJID"
  ) |>
  filter(SAFFL == "Y") |>
  mutate(
    PNDT     = if_else(
      grepl("^\\d{4}-\\d{1,2}-\\d{1,2}", trimws(PNDTC)),
      ymd(trimws(PNDTC), quiet = TRUE),
      as.Date(NA)
    ),
    PNSTRESN = as.numeric(PNSTRESN)
  )

pain_baseline <- pn_anchored |>
  filter(PNDT <= TRTSDT & !is.na(PNSTRESN)) |>
  group_by(USUBJID, PNTESTCD) |>
  summarise(base_val = median(PNSTRESN, na.rm = TRUE), .groups = "drop") |>
  pivot_wider(
    id_cols = USUBJID,
    names_from = PNTESTCD,
    values_from = base_val
  ) |>
  rename(base_ppi = PAININT, base_an = ANSCORE)

pain_days <- pn_anchored |>
  filter(PNDT > TRTSDT & !is.na(PNSTRESN)) |>
  group_by(USUBJID, VISITNUM, VISIT, PNDT, PNTESTCD) |>
  summarise(day_val = min(PNSTRESN, na.rm = TRUE), .groups = "drop")

cycle_dates <- pain_days |>
  group_by(USUBJID, VISITNUM, VISIT) |>
  summarise(cycle_date = min(PNDT, na.rm = TRUE), .groups = "drop")

cycle_vals <- pain_days |>
  group_by(USUBJID, VISITNUM, VISIT, PNTESTCD) |>
  summarise(cycle_val = median(day_val, na.rm = TRUE), .groups = "drop") |>
  pivot_wider(
    id_cols = c(USUBJID, VISITNUM, VISIT),
    names_from = PNTESTCD,
    values_from = cycle_val
  ) |>
  rename(cycle_ppi = PAININT, cycle_an = ANSCORE)

pain_cycles <- cycle_vals |>
  left_join(cycle_dates, by = c("USUBJID", "VISITNUM", "VISIT")) |>
  arrange(USUBJID, VISITNUM)

pain_triggers <- pain_cycles |>
  left_join(pain_baseline, by = "USUBJID") |>
  mutate(
    base_ppi = coalesce(base_ppi, 0),
    base_an  = coalesce(base_an, 0),
    trig = if_else(
      (!is.na(cycle_ppi - base_ppi) & (cycle_ppi - base_ppi) >= 2) |
        (!is.na(cycle_an  - base_an)  & (cycle_an  - base_an)  >= 10),
      1, 0
    )
  )

# Sustained confirmation: a trigger counts if the next consecutive cycle also
# triggers, or if it is the subject's last observed cycle (terminal trigger).
pain_prog <- pain_triggers |>
  group_by(USUBJID) |>
  mutate(
    confirmed = if_else(
      trig == 1 & (coalesce(lead(trig), 0) == 1 | row_number() == n()),
      1, 0
    )
  ) |>
  filter(confirmed == 1) |>
  summarise(prog_date = min(cycle_date), .groups = "drop")

pain_lastassess <- pn_anchored |>
  group_by(USUBJID) |>
  summarise(last_pn_dt = max(PNDT, na.rm = TRUE), .groups = "drop")

ttpain <- df_adsl |>
  filter(SAFFL == "Y") |>
  left_join(pain_prog, by = "USUBJID") |>
  left_join(pain_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTPAIN", PARAM = "Time to Pain Progression", PARAMN = 5,
    PARCAT1 = "EFFICACY",
    STARTDT  = RANDDT,
    progressed = !is.na(prog_date),
    ADT = case_when(
      progressed          ~ prog_date,
      !is.na(last_pn_dt)  ~ pmin(last_pn_dt, STUDY_CUTOFF_DT),
      TRUE                ~ RANDDT
    ),
    CNSR     = if_else(progressed, 0, 1),
    EVNTDESC = if_else(progressed, "PAIN PROGRESSION", ""),
    CNSDTDSC = if_else(
      progressed, "",
      if_else(
        !is.na(last_pn_dt),
        "LAST PAIN ASSESSMENT DATE",
        "NO PAIN ASSESSMENT"
      )
    )
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTPSA — Time to PSA Progression (Safety). Censor date from ADLB (#3).
# ------------------------------------------------------------------------------
psa_event <- adrs |>
  filter(PARAMCD == "PSPROG" & AVALC == "Y") |>
  transmute(USUBJID, psa_prog_dt = as.Date(ADT, origin = "1960-01-01"))

psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA" & !is.na(AVAL) & !is.na(ADT)) |>
  group_by(USUBJID) |>
  summarise(
    last_psa_dt = max(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

ttpsa <- df_adsl |>
  filter(SAFFL == "Y") |>
  left_join(psa_event, by = "USUBJID") |>
  left_join(psa_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTPSA", PARAM = "Time to PSA Progression", PARAMN = 3,
    PARCAT1 = "EFFICACY",
    STARTDT  = TRTSDT,
    progressed = !is.na(psa_prog_dt),
    ADT = case_when(
      progressed           ~ psa_prog_dt,
      !is.na(last_psa_dt)  ~ pmin(last_psa_dt, STUDY_CUTOFF_DT),
      TRUE                 ~ pmin(LSTALVDT, STUDY_CUTOFF_DT)
    ),
    CNSR     = if_else(progressed, 0, 1),
    EVNTDESC = if_else(progressed, "PSA PROGRESSION", ""),
    CNSDTDSC = if_else(
      progressed, "",
      if_else(
        !is.na(last_psa_dt),
        "LAST PSA ASSESSMENT",
        "LAST KNOWN ALIVE DATE"
      )
    )
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTUMOR — Time to Tumor Progression (Safety & measurable-disease subpopulation)
# ------------------------------------------------------------------------------
tumor_event <- adrs |>
  filter(PARAMCD == "OVRLRESP" & AVALC == "PD") |>
  group_by(USUBJID) |>
  summarise(
    tumor_prog_dt = min(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP" & !is.na(ADT)) |>
  group_by(USUBJID) |>
  summarise(
    last_tumor_dt = max(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

ttumor <- df_adsl |>
  filter(SAFFL == "Y" & MEASDISF == "Y") |>
  left_join(tumor_event, by = "USUBJID") |>
  left_join(tumor_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTUMOR", PARAM = "Time to Tumor Progression", PARAMN = 4,
    PARCAT1 = "EFFICACY",
    STARTDT  = TRTSDT,
    progressed = !is.na(tumor_prog_dt),
    ADT = case_when(
      progressed             ~ tumor_prog_dt,
      !is.na(last_tumor_dt)  ~ pmin(last_tumor_dt, STUDY_CUTOFF_DT),
      TRUE                   ~ TRTSDT
    ),
    CNSR     = if_else(progressed, 0, 1),
    EVNTDESC = if_else(progressed, "TUMOR PROGRESSION", ""),
    CNSDTDSC = if_else(
      progressed, "",
      if_else(
        !is.na(last_tumor_dt),
        "LAST TUMOR ASSESSMENT",
        "NO POST-BASELINE ASSESSMENT"
      )
    )
  ) |>
  finalize_tte()

# Combine and save
adtte <- bind_rows(os, ttsae, pfs, ttpain, ttpsa, ttumor) |>
  arrange(USUBJID, PARAMCD) |>
  mutate(AVAL = as.numeric(AVAL), CNSR = as.numeric(CNSR))

# Assertions and Error Guards (QC-03)
if (nrow(adtte) == 0) {
  stop("ERROR: [VALIDATION] ADTTE output dataset is empty!")
}
expected_params <- c("OS", "PFS", "TTPAIN", "TTPSA", "TTUMOR", "TTSAE")
missing_params <- setdiff(expected_params, unique(adtte$PARAMCD))
if (length(missing_params) > 0) {
  stop(
    paste(
      "ERROR: [VALIDATION] ADTTE is missing mandatory parameters:",
      paste(missing_params, collapse = ", ")
    )
  )
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adtte) <- toupper(names(adtte))
for (.dv in names(adtte)) {
  if (inherits(adtte[[.dv]], "Date")) {
    attr(adtte[[.dv]], "format.sas") <- "DATE9."
  }
}
write_xpt_v(adtte, "04_adam/adtte_v.xpt", domain = "ADTTE")
cat("NOTE: [VALIDATION] Wrote validation ADTTE: 04_adam/adtte_v.xpt\n")

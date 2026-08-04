# Program: v_adtte_validation.R | Version: 2.5.0
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
#         OS, PFS, TTPSA, TTPAIN -> one row per ADSL ITTFL=="Y" (Path A: 371)
#         TTSAE                  -> one row per ADSL SAFFL=="Y"
#         TTUMOR                 -> ADSL ITTFL=="Y" (MEASDISF sensitivity)
#         TRT01P always from ADSL (DM arm; never EXTRT)
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
source("04_analysis_datasets/programs/r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADTTE Validation script...\n")

# Load ADaM inputs (validation reads ONLY *_v.xpt + staging — never *_prod.xpt)
df_adsl <- read_xpt("04_analysis_datasets/adam/adsl_v.xpt")
adrs    <- read_xpt("04_analysis_datasets/adam/adrs_v.xpt")
adcm    <- read_xpt("04_analysis_datasets/adam/adcm_v.xpt")
adae    <- read_xpt("04_analysis_datasets/adam/adae_v.xpt")
adlb    <- read_xpt("04_analysis_datasets/adam/adlb_v.xpt")

# F-042 Phase 2 R track.  The controlled module consumes the governed staged
# PN/SV/CM/PR/DS inputs and returns the primary diary-or-RT event pool plus
# traceable sensitivity lineages.  The SAS program implements the same adopted
# rules independently; this is not code copied into the production track.
source("04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R")
f042_phase2 <- f042_derive(
  df_adsl,
  readRDS("01_source_data/real_sdtm/staging/pn.rds"),
  readRDS("01_source_data/real_sdtm/staging/sv.rds"),
  readRDS("01_source_data/real_sdtm/staging/cm.rds"),
  readRDS("01_source_data/real_sdtm/staging/pr.rds"),
  adrs,
  readRDS("01_source_data/real_sdtm/staging/ds.rds")
)

# Aggregate-only F-042 lineage evidence.  Patient-level adjudication worksheets
# remain local/non-versioned; this controlled artifact records the event-source
# counts needed to connect the primary result to the adopted sensitivities.
dir.create("06_qc_evidence/reconciliation", recursive = TRUE, showWarnings = FALSE)
f042_event_source_summary <- tibble(
  analysis = c(
    "primary_diary_or_direct_rt",
    "diary_only_sensitivity",
    "rt_only_supportive",
    "rt_complete_date_inventory",
    "rt_missing_or_partial_date_inventory",
    "pain_response_events"
  ),
  subject_count = c(
    n_distinct(f042_phase2$primary_events$USUBJID[!is.na(f042_phase2$primary_events$event_date)]),
    n_distinct(f042_phase2$sensitivity_events$diary_only$USUBJID),
    n_distinct(f042_phase2$sensitivity_events$rt_only$USUBJID),
    sum(f042_phase2$sensitivity_events$date_bound_rt$date_status == "COMPLETE"),
    sum(f042_phase2$sensitivity_events$date_bound_rt$date_status == "MISSING_OR_PARTIAL"),
    n_distinct(f042_phase2$pain_response_events$USUBJID)
  ),
  record_count = c(
    sum(!is.na(f042_phase2$primary_events$event_date)),
    nrow(f042_phase2$sensitivity_events$diary_only),
    nrow(f042_phase2$sensitivity_events$rt_only),
    sum(f042_phase2$sensitivity_events$date_bound_rt$date_status == "COMPLETE"),
    sum(f042_phase2$sensitivity_events$date_bound_rt$date_status == "MISSING_OR_PARTIAL"),
    nrow(f042_phase2$pain_response_events)
  )
)
write.csv(
  f042_event_source_summary,
  "06_qc_evidence/reconciliation/f042_phase2_event_source_summary.csv",
  row.names = FALSE
)

phase2_primary_pain <- f042_phase2$primary_events |>
  filter(!is.na(event_date)) |>
  transmute(
    USUBJID,
    pain_prog_dt = event_date,
    pain_event_source = event_source,
    pain_event_component = event_component,
    pain_support_types = support_types,
    pain_source_keys = source_keys
  )

phase2_pain_lastassess <- f042_phase2$visits |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(
    !is.na(visit_date), visit_date > as.Date(RANDDT, origin = "1960-01-01"),
    ppi_evaluable | as_evaluable
  ) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(visit_date), .groups = "drop")

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
  mutate(PDDT = as.Date(ADT, origin = "1960-01-01")) |>
  filter(
    (PARAMCD == "OVRLRESP" & AVALC == "PD") |
      (PARAMCD == "BSGRESP"  & AVALC == "PROGRESSION") |
      (PARAMCD == "PSPROG"   & AVALC == "Y")
  ) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(PDDT) & PDDT > RANDDT) |>
  group_by(USUBJID) |>
  summarise(
    pd_dt = min(PDDT),
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

# SAP v4.0 PFS censoring: use the last evaluable post-baseline RECIST, PSA, or
# five-of-seven pain visit when there is no event; randomisation is the censor
# date when none of those assessments exists.  Death milestones are excluded
# from the tumour assessment pool.
pfs_tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP", AVALC %in% c("CR", "PR", "SD", "PD")) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(last_eval_dt) & last_eval_dt > RANDDT) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA", !is.na(AVAL), !is.na(ADT)) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_eval_dt > RANDDT) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_pain_lastassess <- phase2_pain_lastassess

pfs_lastassess <- bind_rows(
  pfs_tumor_lastassess,
  pfs_psa_lastassess,
  pfs_pain_lastassess
) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

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
  left_join(phase2_primary_pain, by = "USUBJID") |>
  left_join(first_nact, by = "USUBJID") |>
  left_join(pfs_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "PFS", PARAM = "Progression Free Survival", PARAMN = 2,
    PARCAT1 = "EFFICACY",
    STARTDT = RANDDT,
    prog_dt = case_when(
      !is.na(pd_dt) & !is.na(pain_prog_dt) ~ pmin(pd_dt, pain_prog_dt),
      !is.na(pd_dt)                        ~ pd_dt,
      !is.na(pain_prog_dt)                 ~ pain_prog_dt,
      TRUE                                 ~ as.Date(NA)
    ),
    prog_event_desc = case_when(
      !is.na(pain_prog_dt) & (is.na(pd_dt) | pain_prog_dt < pd_dt) ~
        "PAIN PROGRESSION",
      !is.na(pd_dt) ~ "DISEASE PROGRESSION",
      !is.na(pain_prog_dt) ~ "PAIN PROGRESSION",
      TRUE ~ ""
    ),
    pd_found   = !is.na(prog_dt),
    nact_found = !is.na(nactdt),
    branch = case_when(
      pd_found & nact_found & nactdt < prog_dt          ~ "NACT_PRE_PD",
      pd_found                                          ~ "PD",
      DTHFL == "Y" & nact_found & nactdt < DTHDT        ~ "NACT_PRE_DEATH",
      DTHFL == "Y"                                      ~ "DEATH",
      nact_found                                        ~ "NACT_ONLY",
      !is.na(last_eval_dt)                               ~ "CENSOR_LASTEVAL",
      TRUE                                               ~ "CENSOR_NO_POST"
    ),
    ADT = case_when(
      branch == "PD"    ~ prog_dt,
      branch == "DEATH" ~ DTHDT,
      branch %in% c("NACT_PRE_PD", "NACT_PRE_DEATH", "NACT_ONLY") ~
        nactdt - days(1),
      branch == "CENSOR_LASTEVAL" ~ pmin(last_eval_dt, STUDY_CUTOFF_DT),
      branch == "CENSOR_NO_POST"  ~ RANDDT
    ),
    CNSR     = if_else(branch %in% c("PD", "DEATH"), 0, 1),
    EVNTDESC = case_when(
      branch == "PD"    ~ prog_event_desc,
      branch == "DEATH" ~ "DEATH",
      TRUE ~ ""
    ),
    CNSDTDSC = case_when(
      branch %in% c("NACT_PRE_PD", "NACT_PRE_DEATH", "NACT_ONLY") ~
        "NEW ANTI-CANCER THERAPY START",
      branch == "CENSOR_LASTEVAL" ~ "LAST EVALUABLE ASSESSMENT",
      branch == "CENSOR_NO_POST"  ~ "NO POST-BASELINE ASSESSMENT",
      TRUE ~ ""
    )
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTPAIN — Time to Pain Progression (Path A Phase 2).
# The primary event pool is the earliest qualified diary-or-direct-intent-RT
# event from the controlled F-042 R track.  Non-events censor at the last
# evaluable scheduled pain assessment, never at an arbitrary raw PN date.
# ------------------------------------------------------------------------------
ttpain <- df_adsl |>
  filter(ITTFL == "Y") |>
  left_join(phase2_primary_pain, by = "USUBJID") |>
  left_join(phase2_pain_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTPAIN", PARAM = "Time to Pain Progression", PARAMN = 5,
    PARCAT1 = "EFFICACY",
    STARTDT  = RANDDT,
    progressed = !is.na(pain_prog_dt),
    ADT = case_when(
      progressed          ~ pain_prog_dt,
      !is.na(last_eval_dt) ~ pmin(last_eval_dt, STUDY_CUTOFF_DT),
      TRUE                ~ RANDDT
    ),
    CNSR     = if_else(progressed, 0, 1),
    EVNTDESC = if_else(progressed, "PAIN PROGRESSION", ""),
    CNSDTDSC = if_else(
      progressed, "",
      if_else(
        !is.na(last_eval_dt), "LAST EVALUABLE PAIN ASSESSMENT",
        "NO EVALUABLE PAIN ASSESSMENT"
      )
    )
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# TTPSA — Time to PSA Progression (ITT, anchored at randomization). Censor date from ADLB (#3).
# ------------------------------------------------------------------------------
psa_event <- adrs |>
  filter(PARAMCD == "PSPROG" & AVALC == "Y") |>
  transmute(USUBJID, psa_prog_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(psa_prog_dt) & psa_prog_dt > RANDDT) |>
  select(USUBJID, psa_prog_dt)

psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA" & !is.na(AVAL) & !is.na(ADT)) |>
  group_by(USUBJID) |>
  summarise(
    last_psa_dt = max(as.Date(ADT, origin = "1960-01-01")),
    .groups = "drop"
  )

ttpsa <- df_adsl |>
  filter(ITTFL == "Y") |>
  left_join(psa_event, by = "USUBJID") |>
  left_join(psa_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTPSA", PARAM = "Time to PSA Progression", PARAMN = 3,
    PARCAT1 = "EFFICACY",
    STARTDT  = RANDDT,
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
# TTUMOR — Time to Tumor Progression (ITT; measurable-disease sensitivity)
# ------------------------------------------------------------------------------
tumor_event <- adrs |>
  filter(PARAMCD == "OVRLRESP" & AVALC == "PD") |>
  transmute(USUBJID, tumor_prog_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(tumor_prog_dt) & tumor_prog_dt > RANDDT) |>
  group_by(USUBJID) |>
  summarise(
    tumor_prog_dt = min(tumor_prog_dt),
    .groups = "drop"
  )

tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP" & AVALC %in% c("CR", "PR", "SD", "PD") & !is.na(ADT)) |>
  transmute(USUBJID, last_tumor_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_tumor_dt > RANDDT) |>
  group_by(USUBJID) |>
  summarise(
    last_tumor_dt = max(last_tumor_dt),
    .groups = "drop"
  )

ttumor <- df_adsl |>
  filter(ITTFL == "Y") |>
  left_join(tumor_event, by = "USUBJID") |>
  left_join(tumor_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "TTUMOR", PARAM = "Time to Tumor Progression", PARAMN = 4,
    PARCAT1 = "EFFICACY",
    STARTDT  = RANDDT,
    progressed = !is.na(tumor_prog_dt),
    ADT = case_when(
      progressed             ~ tumor_prog_dt,
      !is.na(last_tumor_dt)  ~ pmin(last_tumor_dt, STUDY_CUTOFF_DT),
      TRUE                   ~ RANDDT
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
write_xpt_v(adtte, "04_analysis_datasets/adam/adtte_v.xpt", domain = "ADTTE")
cat("NOTE: [VALIDATION] Wrote validation ADTTE: 04_analysis_datasets/adam/adtte_v.xpt\n")

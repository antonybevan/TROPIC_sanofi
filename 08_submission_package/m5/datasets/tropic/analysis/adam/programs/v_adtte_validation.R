# Program: v_adtte_validation.R | Version: 4.0.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-08-09
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
  readRDS(stage_file("pn")),
  readRDS(stage_file("sv")),
  readRDS(stage_file("cm")),
  readRDS(stage_file("pr")),
  adrs,
  readRDS(stage_file("ds"))
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
    visit_date <= STUDY_CUTOFF_DT,
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
  invalid <- d[is.na(d$ADT) | is.na(d$STARTDT) | d$ADT < d$STARTDT, , drop = FALSE]
  if (nrow(invalid) > 0) {
    ids <- paste(utils::head(unique(invalid$USUBJID), 5), collapse = ", ")
    stop(sprintf(
      "ERROR: [ADTTE-QC] %d missing/pre-origin date records (e.g. %s)",
      nrow(invalid), ids
    ))
  }
  d |>
    mutate(
      STUDYID = .env$STUDYID,
      AVAL    = as.numeric(.data$ADT - .data$STARTDT + 1),
      AVALU   = "DAYS"
    ) |>
    select(all_of(adtte_cols))
}

# Typed PFS components. Exploratory BSGRESP and generic CLINPROG are excluded.
pfs_tumor_event <- adrs |>
  mutate(PDDT = as.Date(ADT, origin = "1960-01-01")) |>
  filter(PARAMCD == "OVRLRESP", AVALC == "PD") |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(PDDT), PDDT > RANDDT, PDDT <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(tumor_prog_dt = min(PDDT), .groups = "drop")

pfs_psa_event <- adrs |>
  mutate(PDDT = as.Date(ADT, origin = "1960-01-01")) |>
  filter(PARAMCD == "PSPROG", AVALC == "Y") |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(PDDT), PDDT > RANDDT, PDDT <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(psa_prog_dt = min(PDDT), .groups = "drop")

first_sae <- adae |>
  transmute(USUBJID, AESER, TRTEMFL,
            sae_dt = as.Date(ASTDT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, TRTSDT, TRTEDT), by = "USUBJID") |>
  filter(
    AESER == "Y", TRTEMFL == "Y", !is.na(sae_dt),
    sae_dt >= TRTSDT, sae_dt <= STUDY_CUTOFF_DT,
    is.na(TRTEDT) | sae_dt <= TRTEDT + days(SAFETY_FOLLOWUP_DAYS)
  ) |>
  group_by(USUBJID) |>
  summarise(sae_dt = min(sae_dt), .groups = "drop")

first_nact <- adcm |>
  transmute(USUBJID, nactdt = as.Date(NACTDT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(nactdt), nactdt > RANDDT, nactdt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(nactdt = min(nactdt), .groups = "drop")

# SAP v4.0 PFS censoring: use the last evaluable post-baseline RECIST, PSA, or
# five-of-seven pain visit when there is no event; randomisation is the censor
# date when none of those assessments exists.  Death milestones are excluded
# from the tumour assessment pool.
pfs_tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP", AVALC %in% c("CR", "PR", "SD", "PD")) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(last_eval_dt), last_eval_dt > RANDDT,
         last_eval_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA", !is.na(AVAL), !is.na(ADT)) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_eval_dt > RANDDT, last_eval_dt <= STUDY_CUTOFF_DT) |>
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
    died     = DTHFL == "Y" & !is.na(DTHDT) &
      DTHDT >= RANDDT & DTHDT <= STUDY_CUTOFF_DT,
    os_censor_dt = if_else(
      is.na(LSTALVDT),
      RANDDT,
      pmin(LSTALVDT, STUDY_CUTOFF_DT)
    ),
    ADT      = if_else(died, DTHDT, os_censor_dt),
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
    safety_end = pmin(
      coalesce(LSTALVDT, STUDY_CUTOFF_DT),
      coalesce(TRTEDT + days(SAFETY_FOLLOWUP_DAYS), STUDY_CUTOFF_DT),
      STUDY_CUTOFF_DT
    ),
    had_sae  = !is.na(sae_dt) & sae_dt <= safety_end,
    ADT      = if_else(had_sae, sae_dt, safety_end),
    CNSR     = if_else(had_sae, 0, 1),
    EVNTDESC = if_else(had_sae, "SERIOUS ADVERSE EVENT", ""),
    CNSDTDSC = if_else(had_sae, "", "END OF SAFETY FOLLOW-UP")
  ) |>
  finalize_tte()

# ------------------------------------------------------------------------------
# PFS — Progression-Free Survival (ITT). NACT-censoring hierarchy expressed as a
# single ordered branch label, then mapped to ADT/CNSR/EVNTDESC/CNSDTDSC.
# ------------------------------------------------------------------------------
pfs <- df_adsl |>
  filter(ITTFL == "Y") |>
  left_join(pfs_tumor_event, by = "USUBJID") |>
  left_join(pfs_psa_event, by = "USUBJID") |>
  left_join(phase2_primary_pain, by = "USUBJID") |>
  left_join(first_nact, by = "USUBJID") |>
  left_join(pfs_lastassess, by = "USUBJID") |>
  mutate(
    PARAMCD = "PFS", PARAM = "Progression Free Survival", PARAMN = 2,
    PARCAT1 = "EFFICACY",
    STARTDT = RANDDT,
    pain_event_dt = if_else(
      !is.na(pain_prog_dt) & pain_prog_dt > RANDDT &
        pain_prog_dt <= STUDY_CUTOFF_DT,
      pain_prog_dt, as.Date(NA)
    ),
    death_event_dt = if_else(
      DTHFL == "Y" & !is.na(DTHDT) & DTHDT >= RANDDT &
        DTHDT <= STUDY_CUTOFF_DT,
      DTHDT, as.Date(NA)
    ),
    event_found = !is.na(tumor_prog_dt) | !is.na(psa_prog_dt) |
      !is.na(pain_event_dt) | !is.na(death_event_dt),
    event_dt = case_when(
      event_found ~ pmin(
        coalesce(tumor_prog_dt, as.Date("9999-12-31")),
        coalesce(psa_prog_dt, as.Date("9999-12-31")),
        coalesce(pain_event_dt, as.Date("9999-12-31")),
        coalesce(death_event_dt, as.Date("9999-12-31"))
      ),
      TRUE ~ as.Date(NA)
    ),
    event_desc = case_when(
      event_dt == tumor_prog_dt ~ "TUMOR PROGRESSION",
      event_dt == psa_prog_dt ~ "PSA PROGRESSION",
      event_dt == pain_event_dt ~ "PAIN PROGRESSION",
      event_dt == death_event_dt ~ "DEATH",
      TRUE ~ ""
    ),
    nact_found = !is.na(nactdt),
    branch = case_when(
      event_found & nact_found & nactdt < event_dt      ~ "NACT_PRE_EVENT",
      event_found                                       ~ "EVENT",
      nact_found                                        ~ "NACT_ONLY",
      !is.na(last_eval_dt)                               ~ "CENSOR_LASTEVAL",
      TRUE                                               ~ "CENSOR_NO_POST"
    ),
    ADT = case_when(
      branch == "EVENT" ~ event_dt,
      branch %in% c("NACT_PRE_EVENT", "NACT_ONLY") ~
        nactdt - days(1),
      branch == "CENSOR_LASTEVAL" ~ pmin(last_eval_dt, STUDY_CUTOFF_DT),
      branch == "CENSOR_NO_POST"  ~ RANDDT
    ),
    CNSR     = if_else(branch == "EVENT", 0, 1),
    EVNTDESC = case_when(
      branch == "EVENT" ~ event_desc,
      TRUE ~ ""
    ),
    CNSDTDSC = case_when(
      branch %in% c("NACT_PRE_EVENT", "NACT_ONLY") ~
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
    progressed = !is.na(pain_prog_dt) & pain_prog_dt > RANDDT &
      pain_prog_dt <= STUDY_CUTOFF_DT,
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
  filter(!is.na(psa_prog_dt), psa_prog_dt > RANDDT,
         psa_prog_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(psa_prog_dt = min(psa_prog_dt), .groups = "drop")

psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA", !is.na(AVAL), !is.na(ADT)) |>
  transmute(USUBJID, last_psa_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_psa_dt > RANDDT, last_psa_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(
    last_psa_dt = max(last_psa_dt),
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
      TRUE                 ~ RANDDT
    ),
    CNSR     = if_else(progressed, 0, 1),
    EVNTDESC = if_else(progressed, "PSA PROGRESSION", ""),
    CNSDTDSC = if_else(
      progressed, "",
      if_else(
        !is.na(last_psa_dt),
        "LAST PSA ASSESSMENT",
        "NO POST-BASELINE PSA ASSESSMENT"
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
  filter(!is.na(tumor_prog_dt), tumor_prog_dt > RANDDT,
         tumor_prog_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(
    tumor_prog_dt = min(tumor_prog_dt),
    .groups = "drop"
  )

tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP" & AVALC %in% c("CR", "PR", "SD", "PD") & !is.na(ADT)) |>
  transmute(USUBJID, last_tumor_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(df_adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_tumor_dt > RANDDT, last_tumor_dt <= STUDY_CUTOFF_DT) |>
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

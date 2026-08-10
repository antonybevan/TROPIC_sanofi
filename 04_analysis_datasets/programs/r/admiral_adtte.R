# Program: admiral_adtte.R | Author: Antony Bevan, Clinical Programming
# Description: THIRD independent derivation track for TROPIC ADTTE (BDS-TTE) using
#   pharmaverse `admiral`'s derive_param_tte() with explicit event_source /
#   censor_source objects -- admiral's signature time-to-event capability.
#   Complements the SAS production (A_adtte_generation.sas) and hand-rolled R
#   validation (v_adtte_validation.R) tracks. Reconciled (MP arm; the synthetic
#   CbzP comparator is not in the ADaM ADTTE) by admiral_reconcile.R.
#
# SCOPE: the two ITT EFFICACY parameters admiral models idiomatically:
#   OS  -- Overall Survival: death event, last-known-alive censor (admiral-clean).
#   PFS -- Progression-Free Survival: composite progression (typed tumour/PSA + the
#          author-adopted F-042 pain event pool) and death, with the study's NACT
#          censoring hierarchy.
#   The SAFETY parameters (TTSAE/TTPAIN/TTPSA/TTUMOR) stay with the SAS+R tracks.

suppressMessages({
  library(dplyr)
  library(tidyr)
  library(lubridate)
  library(admiral)
  library(haven)
})

source("04_analysis_datasets/programs/r/config_study.R")
cat("NOTE: [ADMIRAL] Starting ADTTE admiral re-derivation (OS, PFS)...\n")

adsl <- read_xpt("04_analysis_datasets/adam/adsl_admiral.xpt")
names(adsl) <- toupper(names(adsl))
adsl <- adsl |>
  mutate(across(c(RANDDT, TRTSDT, TRTEDT, DTHDT, LSTALVDT), as.Date))

# Event dates: typed ADRS progression + the author-adopted F-042 Phase 2 pain pool
# + ADCM NACT for censoring.  The F-042 module is a governed component shared by
# the controlled R validation track; admiral independently derives the TTE
# event/censor assembly below.
adrs <- read_xpt("04_analysis_datasets/adam/adrs_v.xpt")
names(adrs) <- toupper(names(adrs))
adlb <- read_xpt("04_analysis_datasets/adam/adlb_v.xpt")
names(adlb) <- toupper(names(adlb))
adcm <- read_xpt("04_analysis_datasets/adam/adcm_v.xpt")
names(adcm) <- toupper(names(adcm))
sv <- readRDS(stage_file("sv"))
pn <- readRDS(stage_file("pn"))
cm <- readRDS(stage_file("cm"))
pr <- readRDS(stage_file("pr"))
ds <- readRDS(stage_file("ds"))

first_nonpain <- bind_rows(
  adrs |>
    filter(PARAMCD == "OVRLRESP", AVALC == "PD") |>
    transmute(
      USUBJID,
      PDDT = as.Date(ADT, origin = "1960-01-01"),
      NONPAIN_EVENT = "TUMOR PROGRESSION",
      event_rank = 1L
    ),
  adrs |>
    filter(PARAMCD == "PSPROG", AVALC == "Y") |>
    transmute(
      USUBJID,
      PDDT = as.Date(ADT, origin = "1960-01-01"),
      NONPAIN_EVENT = "PSA PROGRESSION",
      event_rank = 2L
    )
) |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(PDDT), PDDT > RANDDT, PDDT <= STUDY_CUTOFF_DT) |>
  arrange(USUBJID, PDDT, event_rank) |>
  group_by(USUBJID) |>
  slice_head(n = 1) |>
  ungroup() |>
  select(USUBJID, PDDT, NONPAIN_EVENT)

# F-042 is evaluated from the same governed staged domains as the R validation
# track.  It supplies the primary pain event pool and evaluable-visit lineage;
# the admiral event/censor source objects remain independently assembled.
source("04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R")
f042_phase2 <- f042_derive(adsl, pn, sv, cm, pr, adrs, ds)
pain_prog_pfs <- f042_phase2$primary_events |>
  filter(!is.na(event_date)) |>
  transmute(
    USUBJID,
    PAIN_PROG_DT = event_date,
    pain_event_source = event_source,
    pain_event_component = event_component,
    pain_source_keys = source_keys
  ) |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(PAIN_PROG_DT > RANDDT, PAIN_PROG_DT <= STUDY_CUTOFF_DT) |>
  select(-RANDDT)

# PFS last-evaluable censor date: valid post-randomisation RECIST, PSA, or
# evaluable pain visit.  Death milestones are not tumour assessments.
pfs_tumor_lastassess <- adrs |>
  filter(PARAMCD == "OVRLRESP", AVALC %in% c("CR", "PR", "SD", "PD")) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(!is.na(last_eval_dt), last_eval_dt > RANDDT,
         last_eval_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_psa_lastassess <- adlb |>
  filter(PARAMCD == "PSA", !is.na(AVAL), !is.na(ADT)) |>
  transmute(USUBJID, last_eval_dt = as.Date(ADT, origin = "1960-01-01")) |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(last_eval_dt > RANDDT, last_eval_dt <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_pain_lastassess <- f042_phase2$visits |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(
    !is.na(visit_date), visit_date > RANDDT,
    visit_date <= STUDY_CUTOFF_DT,
    ppi_evaluable | as_evaluable
  ) |>
  transmute(USUBJID, last_eval_dt = visit_date) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

pfs_lastassess <- bind_rows(
  pfs_tumor_lastassess,
  pfs_psa_lastassess,
  pfs_pain_lastassess
) |>
  group_by(USUBJID) |>
  summarise(last_eval_dt = max(last_eval_dt), .groups = "drop")

# Composite progression date = earliest of typed tumour/PSA PD and pain progression.
first_prog <- first_nonpain |>
  rename(NONPAIN_PROG_DT = PDDT) |>
  full_join(pain_prog_pfs, by = "USUBJID") |>
  mutate(
    PDDT = case_when(
      !is.na(NONPAIN_PROG_DT) & !is.na(PAIN_PROG_DT) ~
        pmin(NONPAIN_PROG_DT, PAIN_PROG_DT),
      !is.na(NONPAIN_PROG_DT)                        ~ NONPAIN_PROG_DT,
      TRUE                                ~ PAIN_PROG_DT
    )
  ) |>
  select(USUBJID, PDDT, NONPAIN_PROG_DT, NONPAIN_EVENT, PAIN_PROG_DT)

first_nact <- adcm |>
  filter(!is.na(NACTDT)) |>
  transmute(USUBJID, NACTDT = as.Date(NACTDT, origin = "1960-01-01")) |>
  inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
  filter(NACTDT > RANDDT, NACTDT <= STUDY_CUTOFF_DT) |>
  group_by(USUBJID) |>
  summarise(NACTDT = min(NACTDT), .groups = "drop")

# Augment ADSL with the per-subject event/censor anchor dates + precomputed
# censoring dates, so the source objects below can reference plain ADSL columns.
adsl_tte <- adsl |>
  left_join(first_prog, by = "USUBJID") |>
  left_join(first_nact, by = "USUBJID") |>
  left_join(pfs_lastassess, by = "USUBJID") |>
  mutate(
    LSTALV_CAP = case_when(
      is.na(LSTALVDT) | LSTALVDT < RANDDT ~ RANDDT,
      TRUE ~ pmin(LSTALVDT, STUDY_CUTOFF_DT)
    ),
    # PFS censoring hierarchy (SAP): a new anti-cancer therapy censors at the day
    # before NACT and OUTRANKS last-evaluable. admiral's derive_param_tte selects
    # the LATEST date among competing censor_sources, which does not honour this
    # priority (it would pick last-evaluable). So the single PFS censor date is
    # pre-derived per the SAP and fed to admiral as one censor_source.
    PFS_CENSDT  = case_when(
      !is.na(NACTDT)       ~ NACTDT - days(1),
      !is.na(last_eval_dt) ~ pmin(last_eval_dt, STUDY_CUTOFF_DT),
      TRUE                 ~ RANDDT
    ),
    PFS_CENSDSC = case_when(
      !is.na(NACTDT)       ~ "NEW ANTI-CANCER THERAPY START",
      !is.na(last_eval_dt) ~ "LAST EVALUABLE ASSESSMENT",
      TRUE                 ~ "NO POST-BASELINE ASSESSMENT"
    )
  )

# ---- OS: Overall Survival (ITT) --------------------------------------------
os_death <- event_source(
  dataset_name = "adsl",
  filter = DTHFL == "Y" & !is.na(DTHDT) &
    DTHDT >= RANDDT & DTHDT <= STUDY_CUTOFF_DT,
  date = DTHDT,
  set_values_to = exprs(EVNTDESC = "DEATH")
)
os_censor <- censor_source(
  dataset_name = "adsl", date = LSTALV_CAP,
  set_values_to = exprs(CNSDTDSC = "LAST KNOWN ALIVE DATE")
)

os <- derive_param_tte(
  dataset_adsl = adsl_tte |> filter(ITTFL == "Y"),
  start_date = RANDDT,
  event_conditions = list(os_death),
  censor_conditions = list(os_censor),
  source_datasets = list(adsl = adsl_tte |> filter(ITTFL == "Y")),
  set_values_to = exprs(PARAMCD = "OS", PARAM = "Overall Survival",
                        PARAMN = 1, PARCAT1 = "EFFICACY")
)

# ---- PFS: Progression-Free Survival (ITT), study NACT censoring hierarchy ----
# Faithful to the SAP branch order (NACT before PD/death censors the event): an
# event only fires if NOT pre-empted by an earlier NACT. NACT-pre-event subjects
# fall through to the NACT censor; everyone else to last-evaluable.
# EVNTDESC retains the earliest composite component.  A same-day tie is
# assigned to the non-pain component, matching the SAS/R tracks.
pfs_pd <- event_source(
  dataset_name = "adsl",
  filter = !is.na(NONPAIN_PROG_DT) &
    (is.na(PAIN_PROG_DT) | PDDT <= PAIN_PROG_DT) &
    (is.na(NACTDT) | NACTDT >= NONPAIN_PROG_DT),
  date = NONPAIN_PROG_DT,
  set_values_to = exprs(EVNTDESC = NONPAIN_EVENT)
)
pfs_pain <- event_source(
  dataset_name = "adsl",
  filter = !is.na(PAIN_PROG_DT) &
    (is.na(NONPAIN_PROG_DT) | PAIN_PROG_DT < NONPAIN_PROG_DT) &
    (is.na(NACTDT) | NACTDT >= PAIN_PROG_DT),
  date = PAIN_PROG_DT, set_values_to = exprs(EVNTDESC = "PAIN PROGRESSION")
)
pfs_death <- event_source(
  dataset_name = "adsl",
  filter = DTHFL == "Y" & !is.na(DTHDT) &
    DTHDT >= RANDDT & DTHDT <= STUDY_CUTOFF_DT &
    (is.na(NACTDT) | NACTDT >= DTHDT),
  date = DTHDT, set_values_to = exprs(EVNTDESC = "DEATH")
)
pfs_censor <- censor_source(
  dataset_name = "adsl", date = PFS_CENSDT,
  set_values_to = exprs(CNSDTDSC = PFS_CENSDSC)
)

pfs <- derive_param_tte(
  dataset_adsl = adsl_tte |> filter(ITTFL == "Y"),
  start_date = RANDDT,
  event_conditions = list(pfs_pd, pfs_pain, pfs_death),
  censor_conditions = list(pfs_censor),
  source_datasets = list(adsl = adsl_tte |> filter(ITTFL == "Y")),
  set_values_to = exprs(PARAMCD = "PFS", PARAM = "Progression Free Survival",
                        PARAMN = 2, PARCAT1 = "EFFICACY")
)

# ---- Combine + AVAL (admiral duration, +1 day convention) -------------------
adtte <- bind_rows(os, pfs) |>
  derive_vars_duration(
    new_var = AVAL, new_var_unit = AVALU,
    start_date = STARTDT, end_date = ADT, out_unit = "days", add_one = TRUE
  ) |>
  mutate(AVALU = "DAYS") |>
  arrange(USUBJID, PARAMCD)

invalid <- adtte |>
  filter(is.na(STARTDT) | is.na(ADT) | ADT < STARTDT | AVAL < 1)
if (nrow(invalid) > 0) {
  stop(sprintf(
    "ERROR: [ADMIRAL] ADTTE has %d missing/pre-origin duration records",
    nrow(invalid)
  ))
}

for (.dv in names(adtte)) {
  if (inherits(adtte[[.dv]], "Date")) attr(adtte[[.dv]], "format.sas") <- "DATE9."
}
names(adtte) <- toupper(names(adtte))
write_xpt(adtte, "04_analysis_datasets/adam/adtte_admiral.xpt")
cat(sprintf("NOTE: [ADMIRAL] Wrote 04_analysis_datasets/adam/adtte_admiral.xpt (%d rows: OS=%d, PFS=%d)\n",
            nrow(adtte), sum(adtte$PARAMCD == "OS"), sum(adtte$PARAMCD == "PFS")))

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
#   PFS -- Progression-Free Survival: composite progression (tumour/PSA/bone + pain
#          diary per SAP v4.0) and death, with the study's NACT censoring hierarchy.
#   The SAFETY parameters (TTSAE/TTPAIN/TTPSA/TTUMOR) stay with the SAS+R tracks.

suppressMessages({
  library(dplyr)
  library(tidyr)
  library(lubridate)
  library(admiral)
  library(haven)
})

source("03_validation_r/config_study.R")
cat("NOTE: [ADMIRAL] Starting ADTTE admiral re-derivation (OS, PFS)...\n")

adsl <- read_xpt("04_adam/adsl_admiral.xpt")
names(adsl) <- toupper(names(adsl))
adsl <- adsl |>
  mutate(across(c(RANDDT, TRTSDT, TRTEDT, DTHDT, LSTALVDT), as.Date))

# Event dates: ADRS composite PD + SAP v4.0 diary pain progression (same pool as
# A_adtte_generation.sas / v_adtte_validation.R) + ADCM NACT for censoring.
adrs <- read_xpt("04_adam/adrs_v.xpt")
names(adrs) <- toupper(names(adrs))
adcm <- read_xpt("04_adam/adcm_v.xpt")
names(adcm) <- toupper(names(adcm))

first_pd <- adrs |>
  filter((PARAMCD == "OVRLRESP" & AVALC == "PD") |
           (PARAMCD == "BSGRESP" & AVALC == "PROGRESSION") |
           (PARAMCD == "PSPROG"  & AVALC == "Y")) |>
  group_by(USUBJID) |>
  summarise(PDDT = min(as.Date(ADT, origin = "1960-01-01")), .groups = "drop")

# Pain progression eligible for composite PFS (mirror v_adtte_validation.R).
pn <- readRDS("01_raw_source/real_sdtm/staging/pn.rds")
pn_anchored <- pn |>
  inner_join(adsl |> select(USUBJID, TRTSDT, ITTFL), by = "USUBJID") |>
  filter(ITTFL == "Y") |>
  mutate(
    PNDT = if_else(
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
  pivot_wider(id_cols = USUBJID, names_from = PNTESTCD, values_from = base_val) |>
  rename(base_ppi = PAININT, base_an = ANSCORE)
pain_days <- pn_anchored |>
  filter(PNDT > TRTSDT & !is.na(PNSTRESN)) |>
  group_by(USUBJID, VISITNUM, VISIT) |>
  filter(n_distinct(PNDT) >= 5) |>
  ungroup() |>
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
    names_from = PNTESTCD, values_from = cycle_val
  ) |>
  rename(cycle_ppi = PAININT, cycle_an = ANSCORE)
pain_prog_pfs <- cycle_vals |>
  left_join(cycle_dates, by = c("USUBJID", "VISITNUM", "VISIT")) |>
  left_join(pain_baseline, by = "USUBJID") |>
  arrange(USUBJID, VISITNUM) |>
  mutate(
    base_ppi = coalesce(base_ppi, 0),
    base_an = coalesce(base_an, 0),
    trig = if_else(
      (!is.na(cycle_ppi - base_ppi) & (cycle_ppi - base_ppi) >= 2) |
        (!is.na(cycle_an - base_an) & (cycle_an - base_an) >= 10),
      1, 0
    )
  ) |>
  group_by(USUBJID) |>
  mutate(
    confirmed = if_else(
      trig == 1 & (coalesce(lead(trig), 0) == 1 | row_number() == n()),
      1, 0
    )
  ) |>
  filter(confirmed == 1) |>
  summarise(PAIN_PROG_DT = min(cycle_date), .groups = "drop")

# Composite progression date = earliest of tumour/PSA/bone PD and pain progression.
first_prog <- first_pd |>
  full_join(pain_prog_pfs, by = "USUBJID") |>
  mutate(
    PDDT = case_when(
      !is.na(PDDT) & !is.na(PAIN_PROG_DT) ~ pmin(PDDT, PAIN_PROG_DT),
      !is.na(PDDT)                        ~ PDDT,
      TRUE                                ~ PAIN_PROG_DT
    )
  ) |>
  select(USUBJID, PDDT)

first_nact <- adcm |>
  filter(!is.na(NACTDT)) |>
  group_by(USUBJID) |>
  summarise(NACTDT = min(as.Date(NACTDT, origin = "1960-01-01")), .groups = "drop")

# Augment ADSL with the per-subject event/censor anchor dates + precomputed
# censoring dates, so the source objects below can reference plain ADSL columns.
adsl_tte <- adsl |>
  left_join(first_prog, by = "USUBJID") |>
  left_join(first_nact, by = "USUBJID") |>
  mutate(
    LSTALV_CAP = pmin(LSTALVDT, STUDY_CUTOFF_DT),          # admin cutoff applied
    # PFS censoring hierarchy (SAP): a new anti-cancer therapy censors at the day
    # before NACT and OUTRANKS last-evaluable. admiral's derive_param_tte selects
    # the LATEST date among competing censor_sources, which does not honour this
    # priority (it would pick last-evaluable). So the single PFS censor date is
    # pre-derived per the SAP and fed to admiral as one censor_source.
    PFS_CENSDT  = if_else(!is.na(NACTDT), NACTDT - days(1), LSTALV_CAP),
    PFS_CENSDSC = if_else(!is.na(NACTDT),
                          "NEW ANTI-CANCER THERAPY START",
                          "LAST EVALUABLE TUMOR ASSESSMENT")
  )

# ---- OS: Overall Survival (ITT) --------------------------------------------
os_death <- event_source(
  dataset_name = "adsl", filter = DTHFL == "Y", date = DTHDT,
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
# EVNTDESC matches production vocabulary ("DISEASE PROGRESSION") for recon.
pfs_pd <- event_source(
  dataset_name = "adsl",
  filter = !is.na(PDDT) & (is.na(NACTDT) | NACTDT >= PDDT),
  date = PDDT, set_values_to = exprs(EVNTDESC = "DISEASE PROGRESSION")
)
pfs_death <- event_source(
  dataset_name = "adsl",
  filter = DTHFL == "Y" & (is.na(NACTDT) | NACTDT >= DTHDT),
  date = DTHDT, set_values_to = exprs(EVNTDESC = "DEATH")
)
pfs_censor <- censor_source(
  dataset_name = "adsl", date = PFS_CENSDT,
  set_values_to = exprs(CNSDTDSC = PFS_CENSDSC)
)

pfs <- derive_param_tte(
  dataset_adsl = adsl_tte |> filter(ITTFL == "Y"),
  start_date = RANDDT,
  event_conditions = list(pfs_pd, pfs_death),
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

for (.dv in names(adtte)) {
  if (inherits(adtte[[.dv]], "Date")) attr(adtte[[.dv]], "format.sas") <- "DATE9."
}
names(adtte) <- toupper(names(adtte))
write_xpt(adtte, "04_adam/adtte_admiral.xpt")
cat(sprintf("NOTE: [ADMIRAL] Wrote 04_adam/adtte_admiral.xpt (%d rows: OS=%d, PFS=%d)\n",
            nrow(adtte), sum(adtte$PARAMCD == "OS"), sum(adtte$PARAMCD == "PFS")))

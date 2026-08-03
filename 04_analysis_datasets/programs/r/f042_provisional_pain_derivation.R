# Provisional F-042 pain derivation -------------------------------------------
#
# Scope: exploratory, author-directed Path A implementation.  This file is not
# sourced by the production DAG and does not replace the sealed ADTTE outputs.
# Formal accountable-author sign-off remains pending; no output from this file
# may be described as sponsor-approved, independently reviewed, or filing-ready.
#
# The implementation is deliberately organized as reusable functions so a later
# signed integration can call the same rules from a controlled production step.
# The current production SAS program is intentionally unchanged; after formal
# sign-off, SAS and R must be programmed separately and reconciled without
# copying derivation code between languages.

suppressPackageStartupMessages({
  library(dplyr)
  library(haven)
  library(lubridate)
  library(tidyr)
})

`%||%` <- function(x, y) if (is.null(x)) y else x

f042_as_date <- function(x) {
  if (inherits(x, "Date")) return(x)
  if (inherits(x, "POSIXt")) return(as.Date(x))
  if (is.numeric(x)) return(as.Date(x, origin = "1960-01-01"))
  x <- as.character(x)
  ok <- grepl("^\\d{4}-\\d{2}-\\d{2}", x)
  out <- as.Date(rep(NA_character_, length(x)))
  out[ok] <- as.Date(substr(x[ok], 1, 10))
  out
}

f042_text <- function(x) {
  x <- as.character(x)
  x[is.na(x)] <- ""
  trimws(x)
}

f042_require_columns <- function(x, required, object_name) {
  missing <- setdiff(required, names(x))
  if (length(missing)) {
    stop(sprintf("%s is missing required columns: %s", object_name,
                 paste(missing, collapse = ", ")), call. = FALSE)
  }
  invisible(x)
}

f042_prepare_adsl <- function(adsl) {
  names(adsl) <- toupper(names(adsl))
  f042_require_columns(
    adsl,
    c("USUBJID", "RANDDT", "TRTSDT", "ITTFL", "LSTALVDT"),
    "ADSL"
  )
  adsl |>
    mutate(across(any_of(c("RANDDT", "TRTSDT", "TRTEDT", "DTHDT", "LSTALVDT")), f042_as_date)) |>
    mutate(ITTFL = toupper(f042_text(ITTFL)))
}

f042_prepare_pn <- function(pn) {
  names(pn) <- toupper(names(pn))
  f042_require_columns(
    pn,
    c("USUBJID", "PNTESTCD", "PNSTRESN", "PNDTC", "VISITNUM", "VISIT"),
    "PN"
  )
  pn |>
    mutate(
      PNDT = f042_as_date(PNDTC),
      PNTESTCD = toupper(f042_text(PNTESTCD)),
      VISIT = f042_text(VISIT),
      PNSTRESN = as.numeric(PNSTRESN),
      VISITNUM = as.numeric(VISITNUM)
    )
}

# Collapse exact same-test/date/value duplicates, while making discordant
# same-test/date values non-evaluable rather than selecting one silently.
f042_component_summary <- function(x, group_cols) {
  f042_require_columns(x, c(group_cols, "PNTESTCD", "PNDT", "PNSTRESN"), "PN window")
  if (!nrow(x)) {
    return(tibble())
  }

  daily <- x |>
    filter(PNTESTCD %in% c("PAININT", "ANSCORE"), !is.na(PNDT), !is.na(PNSTRESN)) |>
    group_by(across(all_of(c(group_cols, "PNTESTCD", "PNDT")))) |>
    summarise(
      n_distinct_values = n_distinct(PNSTRESN),
      day_value = if (n_distinct(PNSTRESN) == 1) first(PNSTRESN) else NA_real_,
      discordant_day = n_distinct(PNSTRESN) > 1,
      .groups = "drop"
    )

  daily |>
    group_by(across(all_of(c(group_cols, "PNTESTCD")))) |>
    summarise(
      n_valid_days = sum(!is.na(day_value)),
      discordant_days = sum(discordant_day),
      component_value = if (all(is.na(day_value))) {
        NA_real_
      } else if (first(PNTESTCD) == "PAININT") {
        median(day_value, na.rm = TRUE)
      } else {
        mean(day_value, na.rm = TRUE)
      },
      component_evaluable = n_valid_days >= 5 & discordant_days == 0,
      .groups = "drop"
    )
}

f042_widen_components <- function(x, group_cols) {
  if (!nrow(x)) return(tibble())
  out <- x |>
    select(all_of(c(group_cols, "PNTESTCD", "component_value", "n_valid_days",
                    "discordant_days", "component_evaluable"))) |>
    pivot_wider(
      id_cols = all_of(group_cols),
      names_from = PNTESTCD,
      values_from = c(component_value, n_valid_days, discordant_days, component_evaluable),
      names_glue = "{.value}_{PNTESTCD}"
    )

  expected <- c(
    "component_value_PAININT", "component_value_ANSCORE",
    "n_valid_days_PAININT", "n_valid_days_ANSCORE",
    "discordant_days_PAININT", "discordant_days_ANSCORE",
    "component_evaluable_PAININT", "component_evaluable_ANSCORE"
  )
  for (nm in setdiff(expected, names(out))) {
    out[[nm]] <- if (grepl("component_evaluable", nm)) FALSE else NA_real_
  }
  out
}

f042_build_schedule <- function(adsl, pn, sv) {
  names(sv) <- toupper(names(sv))
  f042_require_columns(sv, c("USUBJID", "VISITNUM", "VISIT", "SVSTDTC"), "SV")
  sv0 <- sv |>
    mutate(
      VISITNUM = as.numeric(VISITNUM),
      VISIT = f042_text(VISIT),
      SVSTDTC_DATE = f042_as_date(SVSTDTC)
    ) |>
    filter(!is.na(VISITNUM), !VISITNUM %in% c(0, 99)) |>
    group_by(USUBJID, VISITNUM, VISIT) |>
    summarise(
      sv_date = if (all(is.na(SVSTDTC_DATE))) as.Date(NA) else min(SVSTDTC_DATE, na.rm = TRUE),
      .groups = "drop"
    )

  pn_visits <- pn |>
    inner_join(adsl |> select(USUBJID, TRTSDT), by = "USUBJID") |>
    filter(
      !is.na(VISITNUM), VISITNUM > 1, VISITNUM != 99,
      !is.na(PNDT), PNDT > TRTSDT
    ) |>
    group_by(USUBJID, VISITNUM, VISIT) |>
    summarise(pn_max_date = max(PNDT), .groups = "drop")

  schedule <- adsl |>
    filter(ITTFL == "Y") |>
    select(USUBJID) |>
    left_join(sv0, by = "USUBJID") |>
    full_join(pn_visits, by = c("USUBJID", "VISITNUM", "VISIT")) |>
    filter(!is.na(VISITNUM), VISITNUM > 1, VISITNUM != 99) |>
    mutate(
      visit_date = coalesce(sv_date, pn_max_date),
      visit_date_source = case_when(
        !is.na(sv_date) ~ "SVSTDTC",
        !is.na(pn_max_date) ~ "PN_MAX_FALLBACK",
        TRUE ~ "MISSING"
      )
    ) |>
    arrange(USUBJID, VISITNUM)

  schedule
}

f042_prepare_pain_visits <- function(adsl, pn, sv) {
  adsl_itt <- adsl |> filter(ITTFL == "Y")
  pn_itt <- pn |> inner_join(adsl_itt |> select(USUBJID, TRTSDT, RANDDT), by = "USUBJID")

  baseline_long <- pn_itt |>
    filter(
      PNTESTCD %in% c("PAININT", "ANSCORE"),
      !is.na(PNDT), PNDT >= TRTSDT - 6, PNDT <= TRTSDT
    ) |>
    f042_component_summary(c("USUBJID"))

  baseline <- adsl_itt |>
    select(USUBJID, TRTSDT) |>
    left_join(f042_widen_components(baseline_long, c("USUBJID")), by = "USUBJID")

  schedule <- f042_build_schedule(adsl, pn, sv)
  post <- pn_itt |>
    inner_join(schedule |> select(USUBJID, VISITNUM, VISIT, visit_date),
               by = c("USUBJID", "VISITNUM", "VISIT")) |>
    filter(
      PNTESTCD %in% c("PAININT", "ANSCORE"),
      !is.na(PNDT), !is.na(visit_date),
      PNDT >= visit_date - 6, PNDT <= visit_date
    )

  visit_long <- post |>
    f042_component_summary(c("USUBJID", "VISITNUM", "VISIT"))
  visits <- schedule |>
    left_join(
      f042_widen_components(visit_long, c("USUBJID", "VISITNUM", "VISIT")),
      by = c("USUBJID", "VISITNUM", "VISIT")
    ) |>
    left_join(baseline |> select(
      USUBJID,
      base_ppi = component_value_PAININT,
      base_an = component_value_ANSCORE,
      base_n_days_ppi = n_valid_days_PAININT,
      base_n_days_an = n_valid_days_ANSCORE,
      base_discordant_ppi = discordant_days_PAININT,
      base_discordant_an = discordant_days_ANSCORE,
      base_eval_ppi = component_evaluable_PAININT,
      base_eval_an = component_evaluable_ANSCORE
    ), by = "USUBJID") |>
    mutate(
      ppi_value = component_value_PAININT,
      as_value = component_value_ANSCORE,
      ppi_evaluable = coalesce(component_evaluable_PAININT, FALSE),
      as_evaluable = coalesce(component_evaluable_ANSCORE, FALSE),
      ppi_trigger = ppi_evaluable & base_eval_ppi & !is.na(ppi_value) &
        !is.na(base_ppi) & (ppi_value - base_ppi >= 1),
      as_trigger = as_evaluable & base_eval_an & !is.na(as_value) &
        !is.na(base_an) & base_an > 0 & ((as_value - base_an) / base_an >= 0.25)
    ) |>
    arrange(USUBJID, VISITNUM)

  visits
}

f042_confirm_diary <- function(visits) {
  if (!nrow(visits)) return(tibble())
  visits |>
    group_by(USUBJID) |>
    arrange(VISITNUM, .by_group = TRUE) |>
    mutate(
      next_visitnum = lead(VISITNUM),
      next_visit_date = lead(visit_date),
      next_visit_source = lead(visit_date_source),
      next_ppi_trigger = lead(ppi_trigger, default = FALSE),
      next_as_trigger = lead(as_trigger, default = FALSE),
      ppi_confirmed = ppi_trigger & next_ppi_trigger &
        !is.na(visit_date) & !is.na(next_visit_date) &
        as.numeric(next_visit_date - visit_date) >= 21,
      as_confirmed = as_trigger & next_as_trigger &
        !is.na(visit_date) & !is.na(next_visit_date) &
        as.numeric(next_visit_date - visit_date) >= 21
    ) |>
    ungroup() |>
    filter(ppi_confirmed | as_confirmed) |>
    transmute(
      diary_event_id = row_number(), USUBJID,
      event_date = visit_date, confirming_date = next_visit_date,
      event_date_source = visit_date_source,
      confirming_date_source = next_visit_source,
      component = case_when(
        ppi_confirmed & as_confirmed ~ "PPI+AS",
        ppi_confirmed ~ "PPI",
        as_confirmed ~ "AS",
        TRUE ~ ""
      )
    )
}

f042_direct_rt <- function(adsl, cm, pr) {
  names(cm) <- toupper(names(cm)); names(pr) <- toupper(names(pr))
  f042_require_columns(cm, c("USUBJID", "CMSEQ", "CMSTDTC"), "CM")
  f042_require_columns(pr, c("USUBJID", "PRSEQ", "PRDTC"), "PR")

  value <- function(x, nm) {
    if (nm %in% names(x)) f042_text(x[[nm]]) else rep("", nrow(x))
  }

  direct <- function(x, domain) {
    date_col <- if (domain == "CM") "CMSTDTC" else "PRDTC"
    seq_col <- if (domain == "CM") "CMSEQ" else "PRSEQ"
    treatment_text <- if (domain == "CM") {
      paste(value(x, "CMTRT"), value(x, "CMDECOD"), sep = " | ")
    } else {
      value(x, "PRTRT")
    }
    # The source audit's direct-intent screen is deliberately anchored to the
    # reported treatment/procedure text.  CMINDC is retained as context but is
    # not allowed to turn generic RADIOTHERAPY into an automatic event.
    intent_text <- if (domain == "CM") value(x, "CMTRT") else value(x, "PRTRT")
    indication_text <- if (domain == "CM") value(x, "CMINDC") else rep("", nrow(x))
    category_text <- if (domain == "CM") value(x, "CMCAT") else value(x, "PRCAT")
    radiation_concept <- grepl(
      "radiat|radiotherapy|radiation|photon|\\bcgy\\b|\\bgray\\b|beam",
      treatment_text, ignore.case = TRUE
    )
    explicit_intent <- grepl("\\b(palliative|antalgic)\\b", intent_text, ignore.case = TRUE)
    radiopharm_concept <- grepl(
      "radiopharm|radium|strontium|samarium|radioisotope|radionuclide",
      treatment_text, ignore.case = TRUE
    )
    prior_category <- grepl("\\bprior\\b|history", category_text, ignore.case = TRUE)

    tibble(
      USUBJID = x$USUBJID,
      source_domain = domain,
      source_seq = as.character(x[[seq_col]]),
      treatment_text = treatment_text,
      intent_text = intent_text,
      indication_text = indication_text,
      category_text = category_text,
      event_date = f042_as_date(x[[date_col]]),
      radiation_concept,
      explicit_intent,
      radiopharm_concept,
      prior_category,
      rt_inventory_candidate = radiation_concept & explicit_intent,
      rt_autoqualifies = radiation_concept & explicit_intent &
        !radiopharm_concept & !prior_category,
      exclusion_reason = case_when(
        !radiation_concept ~ "NO_RADIATION_CONCEPT",
        !explicit_intent ~ "NO_EXPLICIT_PALLIATIVE_OR_ANTALGIC_INTENT",
        radiopharm_concept ~ "RADIOPHARMACEUTICAL_CLASSIFICATION_OR_TREATMENT",
        prior_category ~ "PRIOR_OR_HISTORY_CATEGORY",
        TRUE ~ ""
      )
    ) |>
      filter(rt_inventory_candidate)
  }

  adsl_dates <- adsl |>
    mutate(RANDDT = f042_as_date(RANDDT)) |>
    select(USUBJID, RANDDT)
  bind_rows(direct(cm, "CM"), direct(pr, "PR")) |>
    inner_join(adsl_dates, by = "USUBJID") |>
    filter(
      (!is.na(event_date) & !is.na(RANDDT) & event_date > RANDDT) |
        is.na(event_date)
    ) |>
  group_by(USUBJID, event_date) |>
    summarise(
      event_source = "RT",
      source_domains = paste(sort(unique(source_domain)), collapse = ";"),
      source_keys = paste(sort(unique(paste(source_domain, source_seq, sep = ":"))), collapse = ";"),
      source_record_count = n(),
      rt_autoqualifies = all(rt_autoqualifies) & !all(is.na(event_date)),
      inventory_candidate_count = n(),
      exclusion_reasons = paste(sort(unique(c(
        exclusion_reason[exclusion_reason != ""],
        if (all(is.na(event_date))) "MISSING_START_DATE" else character()
      ))), collapse = ";"),
      treatment_text = paste(sort(unique(treatment_text)), collapse = " || "),
      .groups = "drop"
    )
}

f042_supporting_evidence <- function(adsl, adrs, ds, rt_candidates) {
  names(adrs) <- toupper(names(adrs)); names(ds) <- toupper(names(ds))
  f042_require_columns(adrs, c("USUBJID", "PARAMCD", "AVALC", "ADT"), "ADRS")
  f042_require_columns(ds, c("USUBJID", "DSDECOD", "DSSTWK", "DSSEQ"), "DS")
  adrs_evidence <- adrs |>
    mutate(PARAMCD = toupper(f042_text(PARAMCD))) |>
    filter(PARAMCD == "OVRLRESP", toupper(f042_text(AVALC)) == "PD") |>
    transmute(
      USUBJID, evidence_type = "RADIOLOGICAL_RECIST_PD",
      evidence_date = f042_as_date(ADT), latest_possible_date = f042_as_date(ADT),
      evidence_key = paste("ADRS", row_number(), sep = ":")
    ) |>
    inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
    filter(!is.na(evidence_date), !is.na(RANDDT), evidence_date >= RANDDT) |>
    select(-RANDDT)

  ds_evidence <- ds |>
    mutate(
      DSDECOD = toupper(f042_text(DSDECOD)),
      DSSTWK = as.numeric(DSSTWK)
    ) |>
    filter(DSDECOD %in% c("DISEASE PROGRESSION", "PROGRESSION")) |>
    inner_join(adsl |> select(USUBJID, RANDDT), by = "USUBJID") |>
    mutate(
      evidence_date = RANDDT + days(7 * (DSSTWK - 1)),
      latest_possible_date = evidence_date + days(4)
    ) |>
    filter(!is.na(evidence_date), evidence_date >= RANDDT) |>
    transmute(
      USUBJID, evidence_type = "CLINICAL_DS_PROGRESSION_WEEK",
      evidence_date, latest_possible_date,
      evidence_key = paste("DS", DSSEQ, sep = ":")
    )

  rt_evidence <- rt_candidates |>
    filter(rt_autoqualifies) |>
    transmute(
      USUBJID, evidence_type = "PALLIATIVE_RT",
      evidence_date = event_date, latest_possible_date = event_date,
      evidence_key = source_keys
    )
  bind_rows(adrs_evidence, ds_evidence, rt_evidence)
}

f042_qualify_diary <- function(diary_events, evidence) {
  if (!nrow(diary_events)) return(diary_events |> mutate(support_qualified = logical()))
  if (!nrow(evidence)) {
    return(diary_events |> mutate(support_qualified = FALSE, support_types = "", support_keys = ""))
  }
  support <- lapply(seq_len(nrow(diary_events)), function(i) {
    ev <- diary_events[i, ]
    hit <- evidence |>
      filter(
        USUBJID == ev$USUBJID,
        !is.na(latest_possible_date),
        !is.na(ev$confirming_date),
        latest_possible_date <= ev$confirming_date
      )
    tibble(
      diary_event_id = ev$diary_event_id,
      support_qualified = nrow(hit) > 0,
      support_types = paste(sort(unique(hit$evidence_type)), collapse = ";"),
      support_keys = paste(hit$evidence_key, collapse = ";")
    )
  }) |>
    bind_rows()
  diary_events |>
    left_join(support, by = "diary_event_id") |>
    mutate(
      support_qualified = coalesce(support_qualified, FALSE),
      support_types = coalesce(support_types, ""),
      support_keys = coalesce(support_keys, "")
    )
}

f042_primary_events <- function(adsl, diary_events, rt_candidates) {
  diary <- diary_events |>
    filter(support_qualified) |>
    transmute(
      USUBJID, event_date, event_source = "DIARY",
      event_component = component,
      support_types, source_keys = support_keys
    )
  rt <- rt_candidates |>
    filter(rt_autoqualifies, !is.na(event_date)) |>
    transmute(
      USUBJID, event_date, event_source = "RT",
      event_component = "RT",
      support_types = "PALLIATIVE_RT", source_keys
    )
  candidates <- bind_rows(diary, rt)
  if (!nrow(candidates)) {
    return(adsl |> filter(ITTFL == "Y") |> transmute(USUBJID, event_date = as.Date(NA),
      event_source = "", event_component = "", support_types = "", source_keys = ""))
  }
  candidates |>
    group_by(USUBJID, event_date) |>
    summarise(
      event_source = paste(sort(unique(event_source)), collapse = "+"),
      event_component = paste(sort(unique(event_component)), collapse = "+"),
      support_types = paste(sort(unique(unlist(strsplit(support_types, ";", fixed = TRUE)))), collapse = ";"),
      source_keys = paste(source_keys, collapse = ";"),
      .groups = "drop"
    ) |>
    group_by(USUBJID) |>
    slice_min(event_date, with_ties = TRUE) |>
    ungroup()
}

f042_compare_current <- function(adsl, primary_events, adtte = NULL) {
  current <- tibble(USUBJID = character(), current_ttpain_date = as.Date(character()),
                    current_pfs_pain_date = as.Date(character()))
  if (!is.null(adtte)) {
    names(adtte) <- toupper(names(adtte))
    current_ttpain <- adtte |>
      mutate(PARAMCD = toupper(f042_text(PARAMCD)), ITTFL = toupper(f042_text(ITTFL))) |>
      filter(PARAMCD == "TTPAIN", ITTFL == "Y", CNSR == 0) |>
      transmute(USUBJID, current_ttpain_date = f042_as_date(ADT))
    current_pfs <- adtte |>
      mutate(PARAMCD = toupper(f042_text(PARAMCD)), ITTFL = toupper(f042_text(ITTFL))) |>
      filter(PARAMCD == "PFS", ITTFL == "Y", toupper(f042_text(EVNTDESC)) == "PAIN PROGRESSION") |>
      transmute(USUBJID, current_pfs_pain_date = f042_as_date(ADT))
    current <- full_join(current_ttpain, current_pfs, by = "USUBJID")
  }
  adsl |>
    filter(ITTFL == "Y") |>
    select(USUBJID) |>
    left_join(current, by = "USUBJID") |>
    left_join(primary_events |> transmute(USUBJID, provisional_ttpain_date = event_date,
                                           provisional_source = event_source), by = "USUBJID") |>
    mutate(
      disposition = case_when(
        is.na(current_ttpain_date) & !is.na(provisional_ttpain_date) ~ "ADDED_PROVISIONAL",
        !is.na(current_ttpain_date) & is.na(provisional_ttpain_date) ~ "REMOVED_PROVISIONAL",
        !is.na(current_ttpain_date) & !is.na(provisional_ttpain_date) &
          current_ttpain_date != provisional_ttpain_date ~ "REDATED_PROVISIONAL",
        !is.na(current_ttpain_date) & !is.na(provisional_ttpain_date) ~ "UNCHANGED_DATE",
        TRUE ~ "NO_CURRENT_OR_PROVISIONAL_EVENT"
      )
    )
}

f042_derive <- function(adsl, pn, sv, cm, pr, adrs, ds, adtte = NULL) {
  adsl <- f042_prepare_adsl(adsl)
  pn <- f042_prepare_pn(pn)
  visits <- f042_prepare_pain_visits(adsl, pn, sv)
  diary <- f042_confirm_diary(visits)
  rt <- f042_direct_rt(adsl, cm, pr)
  evidence <- f042_supporting_evidence(adsl, adrs, ds, rt)
  diary_qualified <- f042_qualify_diary(diary, evidence)
  primary <- f042_primary_events(adsl, diary_qualified, rt)
  comparison <- f042_compare_current(adsl, primary, adtte)
  list(
    provisional = TRUE,
    visits = visits,
    diary_events = diary_qualified,
    rt_candidates = rt,
    supporting_evidence = evidence,
    primary_events = primary,
    comparison = comparison,
    summary = tibble(
      itt_subjects = sum(adsl$ITTFL == "Y"),
      diary_confirmed_events = nrow(diary_qualified),
      diary_qualified_events = sum(diary_qualified$support_qualified),
      direct_rt_inventory = nrow(rt),
      direct_rt_inventory_records = nrow(rt),
      direct_rt_complete_date_events = sum(!is.na(rt$event_date)),
      direct_rt_autoqualifying_events = sum(rt$rt_autoqualifies),
      direct_rt_adjudication_records = sum(!rt$rt_autoqualifies),
      direct_rt_adjudication_events = sum(!rt$rt_autoqualifies & !is.na(rt$event_date)),
      direct_rt_missing_date_records = sum(is.na(rt$event_date)),
      direct_rt_events = sum(rt$rt_autoqualifies),
      primary_event_subjects = n_distinct(primary$USUBJID[!is.na(primary$event_date)]),
      current_ttpain_events = sum(!is.na(comparison$current_ttpain_date)),
      added_events = sum(comparison$disposition == "ADDED_PROVISIONAL"),
      removed_events = sum(comparison$disposition == "REMOVED_PROVISIONAL"),
      redated_events = sum(comparison$disposition == "REDATED_PROVISIONAL")
    )
  )
}

f042_run_provisional <- function(
    project_root = ".",
    out_dir = NULL
) {
  root <- normalizePath(project_root, mustWork = TRUE)
  adsl <- read_xpt(file.path(root, "04_analysis_datasets/adam/adsl_v.xpt"))
  adtte <- read_xpt(file.path(root, "04_analysis_datasets/adam/adtte_prod.xpt"))
  adrs <- read_xpt(file.path(root, "04_analysis_datasets/adam/adrs_v.xpt"))
  pn <- readRDS(file.path(root, "01_source_data/real_sdtm/staging/pn.rds"))
  cm <- readRDS(file.path(root, "01_source_data/real_sdtm/staging/cm.rds"))
  ds <- readRDS(file.path(root, "01_source_data/real_sdtm/staging/ds.rds"))
  sv <- read_sas(file.path(root, "01_source_data/real_sdtm/sv.sas7bdat"))
  pr <- read_sas(file.path(root, "01_source_data/real_sdtm/pr.sas7bdat"))
  result <- f042_derive(adsl, pn, sv, cm, pr, adrs, ds, adtte)
  if (!is.null(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
    write.csv(result$summary, file.path(out_dir, "f042_provisional_summary.csv"), row.names = FALSE)
    write.csv(result$comparison, file.path(out_dir, "f042_provisional_subject_impact.csv"), row.names = FALSE)
    write.csv(result$primary_events, file.path(out_dir, "f042_provisional_primary_events.csv"), row.names = FALSE)
    write.csv(result$diary_events, file.path(out_dir, "f042_provisional_diary_lineage.csv"), row.names = FALSE)
    write.csv(result$rt_candidates, file.path(out_dir, "f042_provisional_rt_lineage.csv"), row.names = FALSE)
    write.csv(
      result$rt_candidates |>
        filter(!rt_autoqualifies) |>
        mutate(
          author_disposition = "",
          author_reason = "",
          author_initials = "",
          author_signature_ref = "",
          decision_date = ""
        ),
      file.path(out_dir, "f042_provisional_rt_adjudication_worksheet.csv"),
      row.names = FALSE
    )
  }
  result
}

if (sys.nframe() == 0 && !interactive()) {
  args <- commandArgs(trailingOnly = TRUE)
  root <- if (length(args) >= 1) args[[1]] else "."
  out <- if (length(args) >= 2) args[[2]] else NULL
  result <- f042_run_provisional(root, out)
  print(result$summary)
  cat("NOTE: [F042] Provisional output only; production ADTTE and release seal were not modified.\n")
}

# F-042 Phase 2 controlled derivation regression tests ------------------------
#
# These tests use synthetic records only.  They exercise the high-risk rule
# boundaries without reading or writing the sealed production ADTTE:
#   * component-specific baseline summaries and thresholds;
#   * same-component confirmation at the immediately next scheduled visit;
#   * 21-day minimum interval, no terminal exception, and no missing-visit bridge;
#   * same-day duplicate/discordance handling and unscheduled-visit exclusion;
#   * CM+PR provenance with conservative RT adjudication flags; and
#   * post-randomization filtering of radiological evidence.

suppressPackageStartupMessages({
  library(dplyr)
})

f042_env <- new.env(parent = globalenv())
sys.source("04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R",
           envir = f042_env)

adsl <- data.frame(
  USUBJID = sprintf("S%d", 1:8),
  RANDDT = as.Date("2020-01-01"),
  TRTSDT = as.Date("2020-01-01"),
  ITTFL = "Y",
  PAINBL = "Y",
  LSTALVDT = as.Date("2021-12-31"),
  stringsAsFactors = FALSE
)

sv <- do.call(rbind, lapply(adsl$USUBJID, function(id) {
  dates <- switch(
    id,
    S4 = c("2020-02-01", "2020-02-15", "2020-03-01"),
    S8 = c("2020-02-01", "2020-02-22", "2020-03-14"),
    c("2020-02-01", "2020-02-23", "2020-03-20")
  )
  data.frame(
    USUBJID = id,
    VISITNUM = 2:4,
    VISIT = paste("Cycle", 2:4),
    SVSTDTC = dates,
    stringsAsFactors = FALSE
  )
}))

pn <- data.frame(
  USUBJID = character(), PNTESTCD = character(), PNSTRESN = numeric(),
  PNDTC = character(), VISITNUM = numeric(), VISIT = character(),
  stringsAsFactors = FALSE
)
add_pn <- function(id, test, date, value, visitnum, visit) {
  pn <<- rbind(
    pn,
    data.frame(
      USUBJID = id, PNTESTCD = test, PNSTRESN = value,
      PNDTC = format(as.Date(date), "%Y-%m-%d"),
      VISITNUM = visitnum, VISIT = visit,
      stringsAsFactors = FALSE
    )
  )
}
add_baseline <- function(id, ppi = rep(2, 5), ans = rep(4, 5),
                         discordant_ppi = FALSE) {
  # Baseline window is the seven days ending on TRTSDT, so build five
  # observations on the five calendar days immediately preceding treatment.
  dates <- as.Date("2020-01-01") - 4:0
  for (i in seq_along(dates)) {
    add_pn(id, "PAININT", dates[i], ppi[i], 1, "Cycle 1")
    add_pn(id, "ANSCORE", dates[i], ans[i], 1, "Cycle 1")
  }
  if (discordant_ppi) {
    add_pn(id, "PAININT", dates[5], ppi[5] + 1, 1, "Cycle 1")
  }
}
add_post <- function(id, visitnum, date, ppi = NA_real_, ans = NA_real_) {
  # Post-visit summaries also require five valid distinct diary dates in the
  # seven-day window ending at the scheduled evaluation.
  dates <- as.Date(date) - 4:0
  for (d in dates) {
    if (!is.na(ppi)) add_pn(id, "PAININT", d, ppi, visitnum, paste("Cycle", visitnum))
    if (!is.na(ans)) add_pn(id, "ANSCORE", d, ans, visitnum, paste("Cycle", visitnum))
  }
}

# S1: PPI median baseline = 2; PPI rises by one at two visits 22 days apart.
add_baseline("S1", ans = c(3, 4, 5, 4, 4))
add_post("S1", 2, "2020-02-01", ppi = 3, ans = 4)
add_post("S1", 3, "2020-02-23", ppi = 3, ans = 4)

# S2: trigger components are split across visits; no cross-component bridge.
add_baseline("S2")
add_post("S2", 2, "2020-02-01", ppi = 3, ans = 4)
add_post("S2", 3, "2020-02-23", ppi = 2, ans = 5)

# S3: AS baseline is zero; the percent branch is non-evaluable.
add_baseline("S3", ans = rep(0, 5))
add_post("S3", 2, "2020-02-01", ppi = 2, ans = 10)
add_post("S3", 3, "2020-02-23", ppi = 2, ans = 10)

# S4: same-component triggers are only 14 days apart.
add_baseline("S4")
add_post("S4", 2, "2020-02-01", ppi = 3, ans = 4)
add_post("S4", 3, "2020-02-15", ppi = 3, ans = 4)

# S5: a terminal single trigger is not sufficient.
add_baseline("S5")
add_post("S5", 2, "2020-02-01", ppi = 3, ans = 4)

# S6: discordant same-day baseline values make the PPI component non-evaluable.
add_baseline("S6", discordant_ppi = TRUE)
add_post("S6", 2, "2020-02-01", ppi = 3, ans = 4)
add_post("S6", 3, "2020-02-23", ppi = 3, ans = 4)

# S7: an unscheduled high value is not a primary scheduled evaluation.
add_baseline("S7")
add_pn("S7", "PAININT", "2020-02-10", 3, 99, "Unscheduled")

# S8: the second trigger occurs after a missing/non-evaluable scheduled visit;
# it must not bridge over that scheduled visit.
add_baseline("S8")
add_post("S8", 2, "2020-02-01", ppi = 3, ans = 4)
add_post("S8", 4, "2020-03-14", ppi = 3, ans = 4)

visits <- f042_env$f042_prepare_pain_visits(adsl, f042_env$f042_prepare_pn(pn), sv)
diary <- f042_env$f042_confirm_diary(visits)

s1 <- visits |> filter(USUBJID == "S1") |> arrange(VISITNUM)
stopifnot(identical(as.numeric(s1$base_ppi[1]), 2))
stopifnot(abs(as.numeric(s1$base_an[1]) - 4) < 1e-12)
stopifnot(isTRUE(s1$ppi_trigger[1]), isTRUE(s1$ppi_trigger[2]))
stopifnot(nrow(diary) == 1L, diary$USUBJID == "S1",
          diary$component == "PPI",
          diary$event_date == as.Date("2020-02-01"),
          diary$confirming_date == as.Date("2020-02-23"))

stopifnot(!any(diary$USUBJID %in% c("S2", "S3", "S4", "S5", "S6", "S7", "S8")))
stopifnot(!any(visits$USUBJID == "S3" & visits$as_trigger))
stopifnot(!any(visits$USUBJID == "S6" & visits$ppi_trigger))
stopifnot(!any(visits$USUBJID == "S7" & visits$ppi_trigger))
stopifnot(!any(visits$USUBJID == "S8" & visits$ppi_confirmed))

cm <- data.frame(
  USUBJID = c("S1", "S2", "S3", "S4", "S6"),
  CMSEQ = 1:5,
  CMSTDTC = c("2020-02-01", "2020-02-02", "2020-02-03", "2020-02-04", ""),
  CMTRT = c("PALLIATIVE RADIATION", "PALLIATIVE RADIATION",
            "PALLIATIVE RADIATION", "RADIOTHERAPY", "PALLIATIVE RADIATION"),
  CMDECOD = c("", "THERAPEUTIC RADIOPHARMACEUTICALS", "", "", ""),
  CMCAT = c("POST TREATMENT", "POST TREATMENT", "PRIOR TREATMENT",
            "POST TREATMENT", "POST TREATMENT"),
  # S4 has only a generic treatment term; an indication-field word alone must
  # not turn it into a direct-intent candidate.
  CMINDC = c("", "", "", "PALLIATIVE", ""),
  stringsAsFactors = FALSE
)
pr <- data.frame(
  USUBJID = "S5", PRSEQ = 1, PRDTC = "2020-02-05",
  PRTRT = "PALLIATIVE RADIATION TO SPINE", PRCAT = "OTHER",
  stringsAsFactors = FALSE
)
rt <- f042_env$f042_direct_rt(adsl, cm, pr)
stopifnot(nrow(rt) == 5L)
stopifnot(sum(rt$rt_autoqualifies) == 2L)
stopifnot(rt$rt_autoqualifies[rt$USUBJID == "S1"])
stopifnot(rt$rt_autoqualifies[rt$USUBJID == "S5"])
stopifnot(!rt$rt_autoqualifies[rt$USUBJID == "S2"],
          grepl("RADIOPHARMACEUTICAL", rt$exclusion_reasons[rt$USUBJID == "S2"]))
stopifnot(!rt$rt_autoqualifies[rt$USUBJID == "S3"],
          grepl("PRIOR", rt$exclusion_reasons[rt$USUBJID == "S3"]))
stopifnot(!rt$rt_autoqualifies[rt$USUBJID == "S6"],
          is.na(rt$event_date[rt$USUBJID == "S6"]),
          grepl("MISSING_START_DATE", rt$exclusion_reasons[rt$USUBJID == "S6"]))

# Exact CM/PR same-date duplicates collapse with both source keys; non-exact
# cross-domain dates remain separate candidates; missing-date records remain
# one row per source key for bounded adjudication.
cm_dup <- data.frame(
  USUBJID = "S1", CMSEQ = 101, CMSTDTC = "2020-02-05",
  CMTRT = "PALLIATIVE RADIATION", CMDECOD = "", CMCAT = "POST TREATMENT",
  CMINDC = "", stringsAsFactors = FALSE
)
pr_dup <- data.frame(
  USUBJID = c("S1", "S1"), PRSEQ = c(201, 202),
  PRDTC = c("2020-02-05", "2020-02-06"),
  PRTRT = c("PALLIATIVE RADIATION", "PALLIATIVE RADIATION"),
  PRCAT = "OTHER", stringsAsFactors = FALSE
)
rt_dup <- f042_env$f042_direct_rt(adsl, cm_dup, pr_dup)
stopifnot(nrow(rt_dup) == 2L)
same_day <- rt_dup |> filter(event_date == as.Date("2020-02-05"))
stopifnot(nrow(same_day) == 1L,
          same_day$source_record_count == 2L,
          same_day$source_domains == "CM;PR",
          same_day$rt_autoqualifies)

cm_missing <- rbind(cm_dup, transform(cm_dup, CMSEQ = 102, CMSTDTC = ""))
rt_missing <- f042_env$f042_direct_rt(adsl, cm_missing, data.frame(
  USUBJID = character(), PRSEQ = numeric(), PRDTC = character(),
  PRTRT = character(), PRCAT = character(), stringsAsFactors = FALSE
))
stopifnot(sum(is.na(rt_missing$event_date)) == 1L)

# SV-first dating falls back to the maximum complete PN date when the matching
# SV date is absent; the fallback is explicit and never uses the minimum date.
fallback_adsl <- data.frame(
  USUBJID = "S9", RANDDT = as.Date("2020-01-01"),
  TRTSDT = as.Date("2020-01-01"), ITTFL = "Y",
  LSTALVDT = as.Date("2021-12-31"), stringsAsFactors = FALSE
)
fallback_pn <- data.frame(
  USUBJID = rep("S9", 5), PNTESTCD = "PAININT", PNSTRESN = 2,
  PNDTC = paste0("2020-02-", sprintf("%02d", 18:22)),
  VISITNUM = 2, VISIT = "Cycle 2", stringsAsFactors = FALSE
)
fallback_sv <- data.frame(
  USUBJID = "S9", VISITNUM = 2, VISIT = "Cycle 2", SVSTDTC = "",
  stringsAsFactors = FALSE
)
fallback_schedule <- f042_env$f042_build_schedule(
  fallback_adsl, f042_env$f042_prepare_pn(fallback_pn), fallback_sv
)
stopifnot(nrow(fallback_schedule) == 1L,
          fallback_schedule$visit_date == as.Date("2020-02-22"),
          fallback_schedule$visit_date_source == "PN_MAX_FALLBACK")

# DS progression-week uncertainty is represented as point date +4 for the
# conservative primary boundary.
boundary_evidence <- f042_env$f042_supporting_evidence(
  fallback_adsl,
  data.frame(USUBJID = character(), PARAMCD = character(), AVALC = character(),
             ADT = character(), stringsAsFactors = FALSE),
  data.frame(USUBJID = "S9", DSDECOD = "PROGRESSION", DSSTWK = 2,
             DSSEQ = 1, stringsAsFactors = FALSE),
  rt_missing[0, ]
)
stopifnot(boundary_evidence$evidence_date == as.Date("2020-01-08"),
          boundary_evidence$latest_possible_date == as.Date("2020-01-12"))

# Pain-response fixture: a two-point PPI reduction without analgesic increase
# maintained at the next scheduled assessment for >=21 days is one response;
# a terminal response or a missing companion component is not.
response_adsl <- data.frame(
  USUBJID = c("R1", "R2"), ITTFL = "Y", PAINBL = "Y",
  stringsAsFactors = FALSE
)
response_visits <- data.frame(
  USUBJID = c("R1", "R1", "R2", "R2"),
  VISITNUM = c(2, 3, 2, 3),
  visit_date = as.Date(c("2020-02-01", "2020-02-23", "2020-02-01", "2020-02-23")),
  visit_date_source = "SVSTDTC",
  base_ppi = 4, base_an = 10, base_eval_ppi = TRUE, base_eval_an = TRUE,
  ppi_value = c(2, 2, 2, NA), as_value = c(10, 10, 10, NA),
  ppi_evaluable = c(TRUE, TRUE, TRUE, FALSE),
  as_evaluable = c(TRUE, TRUE, TRUE, FALSE),
  stringsAsFactors = FALSE
)
response_events <- f042_env$f042_pain_response_events(response_adsl, response_visits)
stopifnot(nrow(response_events) == 1L,
          response_events$USUBJID == "R1",
          response_events$response_component == "PPI",
          response_events$event_date == as.Date("2020-02-01"),
          response_events$confirming_date == as.Date("2020-02-23"))

adrs <- data.frame(
  USUBJID = c("S1", "S1"), PARAMCD = "OVRLRESP", AVALC = "PD",
  ADT = c("2019-12-31", "2020-02-10"), stringsAsFactors = FALSE
)
ds <- data.frame(
  USUBJID = c("S1", "S1"),
  DSDECOD = c("PROGRESSION", "PROGRESSION"),
  DSSTWK = c(2, 0), DSSEQ = c(1, 2), stringsAsFactors = FALSE
)
evidence <- f042_env$f042_supporting_evidence(adsl, adrs, ds, rt)
stopifnot(sum(evidence$evidence_type == "RADIOLOGICAL_RECIST_PD") == 1L)
stopifnot(sum(evidence$evidence_type == "CLINICAL_DS_PROGRESSION_WEEK") == 1L)
stopifnot(all(evidence$evidence_date >= as.Date("2020-01-01")))

cat("F-042 provisional derivation tests: PASS (synthetic rule-boundary coverage)\n")

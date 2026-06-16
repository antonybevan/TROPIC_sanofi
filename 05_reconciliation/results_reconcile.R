# Program: results_reconcile.R | Author: Antony Bevan, Clinical Programming
# Description: NUMERICAL analysis-results reconciliation (audit M-1).
#   Double-programming previously stopped at the ADaM DATASET layer
#   (cross_lang_audit.R). This step extends it to the ANALYSIS-RESULTS layer: the
#   SAS production track computes the MP-arm survival statistics independently with
#   PROC LIFETEST (exported to 04_adam/tte_stats_prod.csv during the ODA run); here
#   the R track recomputes the same statistics with survival::survfit and the two
#   are diffed numerically with an explicit tolerance.
#
#   SCOPE: the real Mitoxantrone (MP) arm only — the reconciled cohort both engines
#   derive independently. The two-arm HR / log-rank p-values reported in the TFLs
#   use the SYNTHETIC CbzP comparator and are therefore R-only by construction
#   (a single engine has the synthetic data); they are out of scope for an
#   independent numerical reconciliation and are labelled as such in the ADRG.
#
#   Graceful degradation: when the SAS statistics file is absent (e.g. a sim-mode
#   run with no ODA SAS engine), the step records overall='not_available' and exits
#   0 — it does not manufacture a pass.

suppressMessages({
  library(haven)
  library(survival)
})

MEDIAN_TOL_DAYS <- 1 # KM-median agreement tolerance (Kaplan-Meier 50th percentile)
sas_path <- "04_adam/tte_stats_prod.csv"
status_path <- "06_telemetry/results_reconciliation_status.json"
dir.create("06_telemetry", showWarnings = FALSE)

write_status <- function(overall, params = list()) {
  rows <- vapply(
    names(params),
    function(k) sprintf("    \"%s\": \"%s\"", k, params[[k]]),
    character(1)
  )
  json <- paste0(
    "{\n  \"overall\": \"", overall, "\",\n  \"scope\": \"MP arm only (real cohort); ",
    "two-arm HR with synthetic CbzP is R-only by construction\",\n",
    "  \"median_tol_days\": ", MEDIAN_TOL_DAYS, ",\n  \"parameters\": {\n",
    paste(rows, collapse = ",\n"), "\n  }\n}\n"
  )
  writeLines(json, status_path)
}

cat("NOTE: [RESULTS-RECON] Starting numerical SAS<->R analysis-results reconciliation...\n")

if (!file.exists(sas_path)) {
  cat("NOTE: [RESULTS-RECON] SAS statistics file not found (", sas_path,
      "); this run did not execute real SAS analysis stats. Recording 'not_available'.\n", sep = "")
  write_status("not_available")
  quit(save = "no", status = 0)
}

# --- Independent R computation of MP-arm survival statistics --------------------
adtte <- haven::read_xpt("04_adam/adtte_v.xpt")
names(adtte) <- toupper(names(adtte))
adtte <- adtte[adtte$TRT01P == "MP" & !is.na(adtte$AVAL), ]

r_stats <- do.call(rbind, lapply(sort(unique(adtte$PARAMCD)), function(p) {
  d <- adtte[adtte$PARAMCD == p, ]
  fit <- survival::survfit(survival::Surv(AVAL, 1 - CNSR) ~ 1, data = d)
  tab <- summary(fit)$table
  med <- if (is.matrix(tab)) tab[, "median"] else tab["median"]
  data.frame(
    PARAMCD = p, R_N = nrow(d), R_EVENTS = sum(d$CNSR == 0),
    R_MEDIAN = unname(as.numeric(med)), stringsAsFactors = FALSE
  )
}))

# --- SAS PROC LIFETEST statistics ---------------------------------------------
sas_stats <- utils::read.csv(sas_path, stringsAsFactors = FALSE)
names(sas_stats) <- toupper(names(sas_stats))
sas_stats$PARAMCD <- trimws(as.character(sas_stats$PARAMCD))

cmp <- merge(r_stats, sas_stats, by = "PARAMCD", all = TRUE)

results <- list()
for (i in seq_len(nrow(cmp))) {
  row <- cmp[i, ]
  n_ok <- isTRUE(row$R_N == row$N)
  e_ok <- isTRUE(row$R_EVENTS == row$EVENTS)
  rm_na <- is.na(row$R_MEDIAN)
  sm_na <- is.na(row$MEDIAN_DAYS)
  med_ok <- (rm_na && sm_na) ||
    (!rm_na && !sm_na && abs(row$R_MEDIAN - row$MEDIAN_DAYS) <= MEDIAN_TOL_DAYS)
  ok <- n_ok && e_ok && med_ok
  results[[row$PARAMCD]] <- if (ok) "PASS" else "FAIL"
  cat(sprintf(
    "NOTE: [RESULTS-RECON] %-8s N(R=%s/SAS=%s) EVENTS(R=%s/SAS=%s) MEDIAN_d(R=%s/SAS=%s) -> %s\n",
    row$PARAMCD, row$R_N, row$N, row$R_EVENTS, row$EVENTS,
    ifelse(rm_na, "NR", round(row$R_MEDIAN, 1)),
    ifelse(sm_na, "NR", round(row$MEDIAN_DAYS, 1)),
    results[[row$PARAMCD]]
  ))
}

any_fail <- any(vapply(results, function(s) s != "PASS", logical(1)))
write_status(if (any_fail) "FAIL" else "PASS", results)

if (any_fail) {
  failed <- names(Filter(function(s) s != "PASS", results))
  stop(sprintf(
    "RESULTS RECONCILIATION FAILED: SAS PROC LIFETEST vs R survfit disagree for %s.",
    paste(failed, collapse = ", ")
  ))
}
cat("NOTE: [RESULTS-RECON] PASS - SAS and R analysis statistics agree (MP arm).\n")

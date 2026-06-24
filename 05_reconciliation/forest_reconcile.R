# Program: forest_reconcile.R | Author: Antony Bevan, Clinical Programming
# Description: NUMERICAL reconciliation of the F-12-1 OS subgroup forest hazard
#   ratios. The SAS production figure (T_tfl_generation.sas) computes 13 subgroup
#   Cox HRs (CbzP vs MP) with PROC PHREG and exports the figure's own forest
#   dataset to 04_adam/forest_hr_prod.csv during the ODA render; here the R track
#   independently recomputes the same 13 HRs with survival::coxph and the two are
#   diffed numerically with an explicit tolerance.
#
#   WHY: cross_lang_audit.R reconciles the ADaM DATASETS and results_reconcile.R
#   reconciles the MP-arm KM medians, but NEITHER validates the figure-driving
#   statistics. A SAS figure program can silently diverge from the R figure in
#   data selection (e.g. omitting a subgroup, or filtering the wrong AVISIT) with
#   no gate to catch it -- only visual inspection. This step closes that gap: a
#   divergence in any subgroup HR/CI, or a missing/extra subgroup, fails the
#   build. Because the export is the figure's OWN forest dataset, the check
#   validates the actual deliverable, not an independent re-derivation that could
#   silently share none of the figure's defects.
#
#   This two-arm reconciliation is only well-defined because the synthetic CbzP
#   comparator is now single-sourced and gated (check_cbzp_bridge.R): both tracks
#   provably consume the same comparator cohort.
#
#   Graceful degradation: if the SAS forest CSV is absent (a sim-mode run with no
#   ODA figure render), records overall='not_available' and exits 0 -- it does not
#   manufacture a pass. NOTE: wired as a non-gated rscript step, so not_available
#   surfaces as SUCCESS rather than a distinct SKIPPED state; a genuine numeric
#   disagreement exits 1 and fails the build.

suppressMessages({
  library(haven)
  library(survival)
})

HR_TOL <- 0.02 # absolute tolerance on HR / CI bounds (figure reports 2 dp)
sas_path <- "04_adam/forest_hr_prod.csv"
status_path <- "06_telemetry/forest_reconciliation_status.json"
dir.create("06_telemetry", showWarnings = FALSE)

# Subgroups keyed by the SAS figure's subgroup LABEL so the merge is label-exact
# (a relabelled or dropped SAS subgroup surfaces as a mismatch, by design).
# var=NA => overall (all patients). Levels are matched as character.
subgroup_defs <- list(
  list(label = "All Patients",            var = NA,         level = NA),
  list(label = "Age < 65",                var = "AGEGR1",   level = "<65"),
  list(label = "Age >= 65",               var = "AGEGR1",   level = ">=65"),
  list(label = "ECOG 0",                  var = "ECOGBL",   level = "0"),
  list(label = "ECOG 1",                  var = "ECOGBL",   level = "1"),
  list(label = "Measurable Disease: Yes", var = "MEASDISF", level = "Y"),
  list(label = "Measurable Disease: No",  var = "MEASDISF", level = "N"),
  list(label = "Visceral Mets: Yes",      var = "VISCFL",   level = "Y"),
  list(label = "Visceral Mets: No",       var = "VISCFL",   level = "N"),
  list(label = "Baseline Pain: Yes",      var = "PAINBL",   level = "Y"),
  list(label = "Baseline Pain: No",       var = "PAINBL",   level = "N"),
  list(label = "Docetaxel Prog: After",   var = "DOCPROG",  level = "AFTER"),
  list(label = "Docetaxel Prog: During",  var = "DOCPROG",  level = "DURING")
)

write_status <- function(overall, rows = list()) {
  body <- vapply(names(rows), function(k)
    sprintf('    "%s": "%s"', k, rows[[k]]), character(1))
  json <- paste0(
    '{\n  "overall": "', overall, '",\n',
    '  "scope": "F-12-1 subgroup forest HRs (CbzP vs MP), SAS PROC PHREG vs R coxph",\n',
    '  "hr_tol": ', HR_TOL, ',\n  "subgroups": {\n',
    paste(body, collapse = ",\n"), "\n  }\n}\n")
  writeLines(json, status_path)
}

cat("NOTE: [FOREST-RECON] Starting numerical SAS<->R forest-HR reconciliation...\n")

if (!file.exists(sas_path)) {
  cat("NOTE: [FOREST-RECON] SAS forest CSV not found (", sas_path,
      "); no ODA figure render this run. Recording 'not_available'.\n", sep = "")
  write_status("not_available")
  quit(save = "no", status = 0)
}

# --- Assemble the dual-arm OS analysis set (same inputs as the figure) ---------
read_arm <- function(adtte_path, adsl_path, reader) {
  tte <- reader(adtte_path)
  sl <- reader(adsl_path)
  names(tte) <- toupper(names(tte))
  names(sl) <- toupper(names(sl))
  tte <- tte[tte$PARAMCD == "OS", c("USUBJID", "TRT01P", "AVAL", "CNSR")]
  sg <- c("AGEGR1", "ECOGBL", "MEASDISF", "VISCFL", "PAINBL", "DOCPROG")
  for (v in sg) sl[[v]] <- as.character(haven::zap_labels(sl[[v]]))
  out <- merge(tte, sl[, c("USUBJID", sg)], by = "USUBJID")
  out$AVAL <- as.numeric(haven::zap_labels(out$AVAL))
  out$CNSR <- as.numeric(haven::zap_labels(out$CNSR))
  out$TRT01P <- as.character(out$TRT01P)
  out
}
er <- rbind(
  read_arm("04_adam/adtte_v.xpt", "04_adam/adsl_v.xpt", haven::read_xpt),
  read_arm("01_raw_source/cbzp_reconstructed/adtte_cbzp.rds",
           "01_raw_source/cbzp_reconstructed/adsl_cbzp.rds", readRDS)
)
er$TREAT <- ifelse(er$TRT01P == "CbzP", 1, 0)

r_hr <- function(d) {
  fit <- survival::coxph(survival::Surv(AVAL, 1 - CNSR) ~ TREAT, data = d)
  ci <- summary(fit)$conf.int
  c(HR = unname(ci[1]), LCL = unname(ci[3]), UCL = unname(ci[4]))
}
r_forest <- do.call(rbind, lapply(subgroup_defs, function(s) {
  d <- if (is.na(s$var)) er else er[er[[s$var]] == s$level, ]
  est <- r_hr(d)
  data.frame(subgroup = s$label, R_HR = est["HR"], R_LCL = est["LCL"],
             R_UCL = est["UCL"], stringsAsFactors = FALSE)
}))
rownames(r_forest) <- NULL

# --- SAS figure forest HRs ----------------------------------------------------
sas <- utils::read.csv(sas_path, stringsAsFactors = FALSE)
names(sas) <- toupper(names(sas))
sas$SUBGROUP <- trimws(as.character(sas$SUBGROUP))
sas <- sas[, c("SUBGROUP", "HAZARDRATIO", "WALDLOWER", "WALDUPPER")]
names(sas) <- c("subgroup", "SAS_HR", "SAS_LCL", "SAS_UCL")

cmp <- merge(r_forest, sas, by = "subgroup", all = TRUE)

results <- list()
any_fail <- FALSE
for (i in seq_len(nrow(cmp))) {
  row <- cmp[i, ]
  if (is.na(row$R_HR)) {
    res <- "FAIL: extra subgroup in SAS forest (not in R)"
  } else if (is.na(row$SAS_HR)) {
    res <- "FAIL: subgroup missing from SAS forest"
  } else {
    d_hr <- abs(row$R_HR - row$SAS_HR)
    d_lcl <- abs(row$R_LCL - row$SAS_LCL)
    d_ucl <- abs(row$R_UCL - row$SAS_UCL)
    res <- if (d_hr <= HR_TOL && d_lcl <= HR_TOL && d_ucl <= HR_TOL) "PASS" else
      sprintf("FAIL: dHR=%.3f dLCL=%.3f dUCL=%.3f (tol=%.2f)", d_hr, d_lcl, d_ucl, HR_TOL)
  }
  if (!startsWith(res, "PASS")) any_fail <- TRUE
  results[[row$subgroup]] <- res
  cat(sprintf("NOTE: [FOREST-RECON] %-26s R=%s SAS=%s -> %s\n", row$subgroup,
      ifelse(is.na(row$R_HR), "NA", sprintf("%.2f", row$R_HR)),
      ifelse(is.na(row$SAS_HR), "NA", sprintf("%.2f", row$SAS_HR)), res))
}

write_status(if (any_fail) "FAIL" else "PASS", results)
if (any_fail) {
  failed <- names(Filter(function(s) !startsWith(s, "PASS"), results))
  stop(sprintf("FOREST RECONCILIATION FAILED: SAS PROC PHREG vs R coxph disagree for %s.",
       paste(failed, collapse = ", ")))
}
cat("NOTE: [FOREST-RECON] PASS - all 13 subgroup HRs agree (SAS figure vs R).\n")

# Program: admiral_reconcile.R | Author: Antony Bevan, Clinical Programming
# Description: Reconciles the admiral re-derivation track (Finding #4) against the
#   SAS production track. The admiral track (03_validation_r/admiral_adsl.R,
#   admiral_adtte.R) independently derives the admiral-idiomatic CORE of ADSL and
#   ADTTE (OS, PFS); this step diffs those against *_prod.xpt cell-by-cell at zero
#   tolerance and writes a machine-readable status.
#
# SCOPE (honest, by design):
#   * Column-scoped: only the admiral-derivable CORE variables are compared. The
#     study-specific ADSL covariates (PSABL/ECOGBL/PAINBL/… + *IF) and the SAFETY
#     ADTTE params (TTSAE/TTPAIN/TTPSA/TTUMOR) are NOT admiral re-derived here; they
#     remain covered by the SAS+R double-programming and are out of scope.
#   * MP arm only: the ADaM ADTTE is MP-only (the synthetic CbzP comparator is added
#     downstream at the analysis layer), so no arm filtering is needed.
#   Graceful degradation: if an admiral output is absent, the domain is recorded
#   'not_available' and the step exits 0 (it does not manufacture a pass).

suppressMessages(library(haven))

ADSL_CORE <- c("TRT01P", "TRT01PN", "RANDDT", "TRTSDT", "TRTEDT", "TRTDURD",
               "AGE", "AGEGR1", "AGEGR1N", "SEX", "ITTFL", "SAFFL",
               "DTHFL", "DTHDT", "LSTALVDT")
ADTTE_CORE <- c("STARTDT", "ADT", "AVAL", "CNSR", "EVNTDESC", "CNSDTDSC")
ADTTE_PARAMS <- c("OS", "PFS")
status_path <- "06_telemetry/admiral_reconciliation_status.json"
dir.create("06_telemetry", showWarnings = FALSE)

cat("NOTE: [ADMIRAL-RECON] Starting admiral<->SAS reconciliation (scoped core)...\n")

# Cell-diff count for one column across two aligned frames, type-aware, exact.
# A diff = exactly one side missing, OR both present but unequal (both-missing is a
# match, so it must not poison the count with NA).
col_diffs <- function(a, b) {
  if (inherits(b, "Date")) a <- as.Date(a)
  if (is.numeric(b)) {
    a <- as.numeric(a)
    b <- as.numeric(b)
  } else {
    a <- trimws(as.character(a))
    b <- trimws(as.character(b))
  }
  sum((is.na(a) != is.na(b)) | (!is.na(a) & !is.na(b) & a != b))
}

reconcile <- function(adm_path, prod_path, cols, key_extra = NULL,
                      param = NULL, param_col = "PARAMCD") {
  if (!file.exists(adm_path) || !file.exists(prod_path)) return(NULL)
  ad <- read_xpt(adm_path)
  names(ad) <- toupper(names(ad))
  pr <- read_xpt(prod_path)
  names(pr) <- toupper(names(pr))
  if (!is.null(param)) {
    ad <- ad[ad[[param_col]] == param, ]
    pr <- pr[pr[[param_col]] == param, ]
  }
  ord <- function(d) d[do.call(order, d[c("USUBJID", key_extra)]), ]
  ad <- ord(ad)
  pr <- ord(pr)
  # Compare on the common subject set (admiral covers the real MP cohort).
  common <- intersect(ad$USUBJID, pr$USUBJID)
  ad <- ad[ad$USUBJID %in% common, ]
  pr <- pr[pr$USUBJID %in% common, ]
  total <- 0L
  for (v in cols) {
    if (!v %in% names(ad) || !v %in% names(pr)) {
      total <- total + nrow(pr)
      next
    }
    total <- total + col_diffs(ad[[v]], pr[[v]])
  }
  list(n = length(common), diffs = total, status = if (total == 0) "PASS" else "FAIL")
}

results <- list()
results[["ADSL"]] <- reconcile("04_adam/adsl_admiral.xpt", "04_adam/adsl_prod.xpt", ADSL_CORE)
for (p in ADTTE_PARAMS) {
  results[[paste0("ADTTE.", p)]] <- reconcile(
    "04_adam/adtte_admiral.xpt", "04_adam/adtte_prod.xpt", ADTTE_CORE,
    key_extra = "PARAMCD", param = p
  )
}

avail <- Filter(Negate(is.null), results)
if (length(avail) == 0) {
  cat("NOTE: [ADMIRAL-RECON] No admiral outputs found; recording 'not_available'.\n")
  writeLines('{\n  "overall": "not_available"\n}\n', status_path)
  quit(save = "no", status = 0)
}

for (nm in names(results)) {
  r <- results[[nm]]
  if (is.null(r)) {
    cat(sprintf("NOTE: [ADMIRAL-RECON] %-10s -> not_available\n", nm))
    next
  }
  cat(sprintf("NOTE: [ADMIRAL-RECON] %-10s n=%-4d cell-diffs=%-3d -> %s\n",
              nm, r$n, r$diffs, r$status))
}

any_fail <- any(vapply(avail, function(r) r$status != "PASS", logical(1)))
rows <- vapply(names(avail), function(nm) {
  r <- avail[[nm]]
  sprintf('    "%s": {"n": %d, "cell_diffs": %d, "status": "%s"}', nm, r$n, r$diffs, r$status)
}, character(1))
json <- paste0(
  '{\n  "overall": "', if (any_fail) "FAIL" else "PASS", '",\n',
  '  "scope": "admiral-derivable core only; ADSL covariates + SAFETY TTE params out of scope; MP arm",\n',
  '  "tolerance": "exact (0 cell differences)",\n',
  '  "domains": {\n', paste(rows, collapse = ",\n"), "\n  }\n}\n"
)
writeLines(json, status_path)
cat(sprintf("NOTE: [ADMIRAL-RECON] Wrote %s\n", status_path))

if (any_fail) {
  failed <- names(Filter(function(r) r$status != "PASS", avail))
  stop(sprintf("ADMIRAL RECONCILIATION FAILED: %s", paste(failed, collapse = ", ")))
}
cat("NOTE: [ADMIRAL-RECON] PASS - admiral track agrees with SAS production on the scoped core.\n")

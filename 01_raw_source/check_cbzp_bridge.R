# ==============================================================================
# Program: check_cbzp_bridge.R
# Purpose: Parity gate for the SYNTHETIC CbzP comparator bridge. The R reporting
#   track reads <dom>_cbzp.rds; the SAS production track reads <dom>_cbzp.xpt.
#   Both must be the SAME reconstruction -- the .xpt must be the current
#   deterministic export of the .rds (see export_cbzp_xpt.R). Nothing else in the
#   pipeline compares them: cross_lang_audit.R reconciles the MP-only production
#   ADaM, and results_reconcile.R scopes the synthetic arm out by construction, so
#   the synthetic comparator sat in a reconciliation blind spot. This gate closes
#   it. The blind spot let F-11-1 OS show HR=0.43 on the SAS track (stale .xpt,
#   200 OS events) against HR=0.71 on the R track (current .rds, 228 OS events).
#
# Method: re-derive the expected XPORT content from each .rds using the SAME
#   transform export_cbzp_xpt.R applies (Date -> SAS epoch, names UPCASE), then
#   compare row-for-row against the on-disk .xpt. The exporter preserves row
#   order, so a correctly-derived .xpt is row-aligned with its .rds; any order or
#   value drift therefore surfaces as a mismatch. Numerics are compared with a
#   tolerance (V5 IBM-float round-trip); text is compared trimmed.
#
# Exit: 0 = every domain in parity; 1 = any drift (build-gating).
# Writes: 06_telemetry/cbzp_bridge_status.json
# Run:    Rscript 01_raw_source/check_cbzp_bridge.R   (from project root)
# ==============================================================================
suppressMessages(library(haven))

dir  <- "01_raw_source/cbzp_reconstructed"
doms <- c("adsl", "adtte", "adae", "adlb", "adex", "adrs")
TOL  <- 1e-6
status_path <- "06_telemetry/cbzp_bridge_status.json"
dir.create("06_telemetry", showWarnings = FALSE)

# Mirror export_cbzp_xpt.R's RDS -> V5 XPORT transform, then drop attributes that
# do not survive the round-trip (haven value labels, variable labels, SAS formats)
# so the comparison is on values only.
to_xport <- function(x) {
  x <- as.data.frame(x)
  for (col in names(x)) {
    v <- x[[col]]
    if (inherits(v, "Date")) v <- as.numeric(v) + 3653
    if (is.factor(v))        v <- as.character(v)
    attributes(v) <- NULL
    x[[col]] <- v
  }
  names(x) <- toupper(names(x))
  x
}

strip_attrs <- function(df) {
  for (col in names(df)) {
    v <- df[[col]]
    attributes(v) <- NULL
    df[[col]] <- v
  }
  df
}

# Count mismatching cells between two equal-length vectors (NA-aware).
count_mismatch <- function(a, b) {
  na_mis <- xor(is.na(a), is.na(b))
  both   <- !is.na(a) & !is.na(b)
  if (is.numeric(a) && is.numeric(b)) {
    val_mis <- both & (abs(a - b) > TOL * pmax(1, abs(b)))
  } else {
    val_mis <- both & (trimws(as.character(a)) != trimws(as.character(b)))
  }
  sum(na_mis) + sum(val_mis)
}

domains <- list()
overall <- "PASS"

for (d in doms) {
  rds_p <- file.path(dir, paste0(d, "_cbzp.rds"))
  xpt_p <- file.path(dir, paste0(d, "_cbzp.xpt"))
  if (!file.exists(rds_p) || !file.exists(xpt_p)) {
    domains[[d]] <- "MISSING file"
    overall <- "FAIL"
    cat(sprintf("  [BRIDGE-PARITY] %-6s FAIL -> missing .rds or .xpt\n", toupper(d)))
    next
  }

  exp <- to_xport(readRDS(rds_p))
  act <- strip_attrs(as.data.frame(read_xpt(xpt_p)))

  reasons <- character(0)
  if (nrow(exp) != nrow(act)) {
    reasons <- c(reasons, sprintf("row count rds=%d xpt=%d", nrow(exp), nrow(act)))
  }
  miss_in_xpt <- setdiff(names(exp), names(act))
  extra_in_xpt <- setdiff(names(act), names(exp))
  if (length(miss_in_xpt))  reasons <- c(reasons, paste("cols absent from xpt:",  paste(miss_in_xpt,  collapse = ",")))
  if (length(extra_in_xpt)) reasons <- c(reasons, paste("cols extra in xpt:",     paste(extra_in_xpt, collapse = ",")))

  if (nrow(exp) == nrow(act)) {
    for (col in intersect(names(exp), names(act))) {
      m <- count_mismatch(exp[[col]], act[[col]])
      if (m > 0) reasons <- c(reasons, sprintf("%s: %d cell diff", col, m))
    }
  }

  if (length(reasons)) {
    domains[[d]] <- paste(reasons, collapse = "; ")
    overall <- "FAIL"
    cat(sprintf("  [BRIDGE-PARITY] %-6s FAIL -> %s\n", toupper(d), domains[[d]]))
  } else {
    domains[[d]] <- "PASS"
    cat(sprintf("  [BRIDGE-PARITY] %-6s PASS\n", toupper(d)))
  }
}

esc  <- function(s) gsub('"', '\\\\"', s)
rows <- vapply(names(domains),
               function(k) sprintf('    "%s": "%s"', k, esc(domains[[k]])),
               character(1))
json <- paste0(
  "{\n",
  sprintf('  "overall": "%s",\n', overall),
  '  "scope": "synthetic CbzP bridge: <dom>_cbzp.xpt must equal the current export of <dom>_cbzp.rds",\n',
  '  "domains": {\n',
  paste(rows, collapse = ",\n"), "\n",
  "  }\n}\n"
)
writeLines(json, status_path)

if (overall != "PASS") {
  cat("FAIL: [BRIDGE-PARITY] synthetic CbzP .xpt has drifted from .rds -- re-run 01_raw_source/export_cbzp_xpt.R\n")
  quit(status = 1)
}
cat("NOTE: [BRIDGE-PARITY] all synthetic CbzP .xpt files match their .rds source.\n")

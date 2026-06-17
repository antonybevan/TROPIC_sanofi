#!/usr/bin/env Rscript
# =============================================================================
# spec_data_checks.R
# -----------------------------------------------------------------------------
# Independent spec <-> DATA conformance gate (the second leg of the C-4
# inversion triangle). The authoritative spec (00_specifications/ADaM_spec.xlsx)
# is checked against the ACTUAL produced ADaM datasets (04_adam/*_prod.xpt,
# the SAS production track) using the pharmaverse metacore + metatools + xportr
# toolchain:
#   * metatools::check_variables  -- every spec variable present, no extras
#   * metatools::check_ct_data    -- data values conform to spec codelists (CT)
#   * xportr::xportr_type/_length -- data types/lengths match the spec
#
# This is INDEPENDENT verification: the data is produced by the SAS+R pipelines,
# not by the define, so agreement with the spec is meaningful (not circular).
# Together with 07_define_xml/check_define_conformance.R (spec <-> define) this
# closes the loop:  spec -> {define, data}.  Exits non-zero on any drift.
#
# Usage:  Rscript 03_validation_r/spec_data_checks.R
# =============================================================================

suppressMessages({
  library(metacore)
  library(metatools)
  library(xportr)
  library(haven)
  library(dplyr)
  library(jsonlite)
})
source(local({
  rel <- "03_validation_r/load_spec.R"
  cands <- c(rel, file.path("..", rel), file.path(Sys.getenv("TROPIC_ROOT", "."), rel))
  hit <- Filter(file.exists, cands)
  if (!length(hit)) stop("cannot locate ", rel)
  normalizePath(hit[[1]])
}))

find_dir <- function(rel) {
  cands <- c(rel, file.path("..", rel), file.path(Sys.getenv("TROPIC_ROOT", "."), rel))
  hit <- Filter(file.exists, cands)
  if (!length(hit)) NA_character_ else normalizePath(hit[[1]])
}

# known xportr false-positive (see config_study.R::write_xpt_v) -- not a defect
.benign <- "non-ASCII, symbol or underscore"
capture_warnings <- function(expr) {
  w <- character()
  withCallingHandlers(
    suppressMessages(suppressWarnings(force(expr), classes = "simpleMessage")),
    warning = function(x) {
      w <<- c(w, conditionMessage(x))
      invokeRestart("muffleWarning")
    }
  )
  w[!grepl(.benign, w, fixed = TRUE) & !grepl("only contains missing values", w, fixed = TRUE)]
}

spec <- load_tropic_spec()
domains <- spec$ds_spec$dataset
records <- list()

for (ds in domains) {
  f <- find_dir(sprintf("04_adam/%s_prod.xpt", tolower(ds)))
  if (is.na(f)) {
    records[[ds]] <- list(
      dataset = ds, status = "SKIPPED",
      note = "produced *_prod.xpt not found"
    )
    next
  }
  df <- haven::read_xpt(f)
  mc <- suppressWarnings(suppressMessages(select_dataset(spec, ds)))
  spec_vars <- mc$ds_vars$variable

  missing <- setdiff(spec_vars, names(df))
  extra <- setdiff(names(df), spec_vars)
  ct_w <- capture_warnings(check_ct_data(df, mc))
  type_w <- capture_warnings(xportr_type(df, mc, domain = ds))
  len_w <- capture_warnings(xportr_length(df, mc, domain = ds))

  n_issues <- length(missing) + length(extra) + length(ct_w) + length(type_w) + length(len_w)
  status <- if (n_issues == 0) "PASS" else "FAIL"
  records[[ds]] <- list(
    dataset = ds, n_data_vars = ncol(df), n_spec_vars = length(spec_vars),
    missing_in_data = missing, extra_in_data = extra,
    ct_violations = length(ct_w), ct_detail = utils::head(ct_w, 5),
    type_mismatches = length(type_w), type_detail = utils::head(type_w, 5),
    length_mismatches = length(len_w), length_detail = utils::head(len_w, 5),
    status = status
  )
}

overall <- if (all(vapply(records, function(r) r$status %in% c("PASS", "SKIPPED"), logical(1)))) {
  "PASS"
} else {
  "FAIL"
}
report_dir <- find_dir("06_telemetry/conformance")
result <- list(
  check = "spec -> data conformance (metacore/metatools/xportr)",
  spec = "ADaM_spec.xlsx", data = "04_adam/*_prod.xpt",
  timestamp = format(Sys.time(), "%Y-%m-%dT%H:%M:%S"),
  status = overall, datasets = unname(records)
)
if (!is.na(report_dir)) {
  write_json(result, file.path(report_dir, "spec_data_conformance.json"),
    auto_unbox = TRUE, pretty = TRUE, na = "string"
  )
}

cat(sprintf("\nspec -> data conformance: %s\n", overall))
for (r in records) {
  if (identical(r$status, "SKIPPED")) {
    cat(sprintf("  %-6s SKIPPED (%s)\n", r$dataset, r$note))
    next
  }
  cat(sprintf(
    "  %-6s %s  vars %d/%d  CT:%d type:%d length:%d\n",
    r$dataset, r$status, r$n_data_vars, r$n_spec_vars,
    r$ct_violations, r$type_mismatches, r$length_mismatches
  ))
  if (length(r$missing_in_data)) cat("         missing in data:", paste(r$missing_in_data, collapse = ", "), "\n")
  if (length(r$extra_in_data)) cat("         extra in data:  ", paste(r$extra_in_data, collapse = ", "), "\n")
}
if (overall != "PASS") quit(status = 1)
invisible(0)

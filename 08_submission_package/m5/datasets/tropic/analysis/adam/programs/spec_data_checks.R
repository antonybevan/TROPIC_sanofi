#!/usr/bin/env Rscript
# =============================================================================
# spec_data_checks.R
# -----------------------------------------------------------------------------
# Independent spec <-> DATA conformance gate (the second leg of the C-4
# inversion triangle). The authoritative spec (03_metadata/adam/ADaM_spec.xlsx)
# is checked against the ACTUAL produced ADaM datasets (04_analysis_datasets/adam/*_prod.xpt,
# the SAS production track) using the pharmaverse metacore + metatools + xportr
# toolchain:
#   * metatools::check_variables  -- every spec variable present, no extras
#   * metatools::check_ct_data    -- data values conform to spec codelists (CT)
#   * xportr::xportr_type/_length -- data types/lengths match the spec
#
# This is INDEPENDENT verification: the data is produced by the SAS+R pipelines,
# not by the define, so agreement with the spec is meaningful (not circular).
# Together with 03_metadata/define/check_define_conformance.R (spec <-> define) this
# closes the loop:  spec -> {define, data}.  Exits non-zero on any drift.
#
# Usage:  Rscript 04_analysis_datasets/programs/r/spec_data_checks.R
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
  rel <- "04_analysis_datasets/programs/r/load_spec.R"
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
  f <- find_dir(sprintf("04_analysis_datasets/adam/%s_prod.xpt", tolower(ds)))
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

  # Semantic checks supplement the structural metacore checks.  These are
  # deliberately limited to Path-A contracts that are otherwise invisible to
  # variable/length conformance: DM is the planned-arm authority (F-028), actual
  # treatment is independently derived from administered EX, ETHNIC is an assigned
  # NOT REPORTED placeholder because the public DM has no ETHNIC field, and
  # ALBBL/LDHBL are genuinely unavailable and therefore remain missing.
  semantic_w <- character()
  semantic_observations <- character()
  if (identical(toupper(ds), "ADSL")) {
    planned_n <- case_when(
      as.character(df$TRT01P) == "CbzP" ~ 1,
      as.character(df$TRT01P) == "MP" ~ 2,
      TRUE ~ NA_real_
    )
    actual_n <- case_when(
      as.character(df$TRT01A) == "CbzP" ~ 1,
      as.character(df$TRT01A) == "MP" ~ 2,
      TRUE ~ NA_real_
    )
    if (any(is.na(planned_n)) ||
          any(as.numeric(df$TRT01PN) != planned_n, na.rm = TRUE)) {
      semantic_w <- c(semantic_w, "TRT01P/TRT01PN planned-treatment mapping is inconsistent")
    }
    if (any(is.na(actual_n)) ||
          any(as.numeric(df$TRT01AN) != actual_n, na.rm = TRUE)) {
      semantic_w <- c(semantic_w, "TRT01A/TRT01AN actual-treatment mapping is inconsistent")
    }
    n_trt_diff <- sum(
      as.character(df$TRT01A) != as.character(df$TRT01P),
      na.rm = TRUE
    )
    semantic_observations <- c(
      semantic_observations,
      sprintf(
        "%d planned/actual treatment discrepancy(ies) retained for source traceability",
        n_trt_diff
      )
    )
    if (!all(as.character(df$ETHNIC) == "NOT REPORTED", na.rm = TRUE)) {
      semantic_w <- c(semantic_w, "ETHNIC is not the documented NOT REPORTED assignment")
    }
    if (any(!is.na(df$ALBBL)) || any(!is.na(df$LDHBL))) {
      semantic_w <- c(semantic_w, "ALBBL/LDHBL contain values although the source release has no fields")
    }
    if (any(!is.na(df$ALBBLIF) & nzchar(trimws(as.character(df$ALBBLIF)))) ||
          any(!is.na(df$LDHBLIF) & nzchar(trimws(as.character(df$LDHBLIF))))) {
      semantic_w <- c(semantic_w, "ALBBLIF/LDHBLIF are non-blank despite unavailable baseline labs")
    }
  }

  n_issues <- length(missing) + length(extra) + length(ct_w) + length(type_w) +
    length(len_w) + length(semantic_w)
  status <- if (n_issues == 0) "PASS" else "FAIL"
  records[[ds]] <- list(
    dataset = ds, n_data_vars = ncol(df), n_spec_vars = length(spec_vars),
    missing_in_data = missing, extra_in_data = extra,
    ct_violations = length(ct_w), ct_detail = utils::head(ct_w, 5),
    type_mismatches = length(type_w), type_detail = utils::head(type_w, 5),
    length_mismatches = length(len_w), length_detail = utils::head(len_w, 5),
    semantic_violations = length(semantic_w), semantic_detail = utils::head(semantic_w, 5),
    semantic_observations = semantic_observations,
    status = status
  )
}

overall <- if (all(vapply(records, function(r) r$status %in% c("PASS", "SKIPPED"), logical(1)))) {
  "PASS"
} else {
  "FAIL"
}
report_dir <- find_dir("platform/conformance")
result <- list(
  check = "spec -> data conformance (metacore/metatools/xportr)",
  spec = "ADaM_spec.xlsx", data = "04_analysis_datasets/adam/*_prod.xpt",
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
    "  %-6s %s  vars %d/%d  CT:%d type:%d length:%d semantic:%d\n",
    r$dataset, r$status, r$n_data_vars, r$n_spec_vars,
    r$ct_violations, r$type_mismatches, r$length_mismatches,
    if (is.null(r$semantic_violations)) 0 else r$semantic_violations
  ))
  if (length(r$missing_in_data)) cat("         missing in data:", paste(r$missing_in_data, collapse = ", "), "\n")
  if (length(r$extra_in_data)) cat("         extra in data:  ", paste(r$extra_in_data, collapse = ", "), "\n")
  if (!is.null(r$semantic_detail) && length(r$semantic_detail)) {
    cat(
      "         semantic:       ",
      paste(r$semantic_detail, collapse = " | "),
      "\n"
    )
  }
  if (!is.null(r$semantic_observations) && length(r$semantic_observations)) {
    cat(
      "         observation:    ",
      paste(r$semantic_observations, collapse = " | "),
      "\n"
    )
  }
}
if (overall != "PASS") quit(status = 1)
invisible(0)

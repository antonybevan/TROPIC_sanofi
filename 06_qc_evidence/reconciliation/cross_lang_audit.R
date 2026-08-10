# Program: cross_lang_audit.R | Version: 4.0.0 | Author: Antony Bevan, Clinical Programming | Date: 2026-08-10
# Description: Cross-Language reconciliation comparing the SAS production track
#   (*_prod.xpt) against the independent R validation track (*_v.xpt).
#
# METHODOLOGY (audit F-6): every reconciled dataset now has a governed, unique
#   business key in config/study_manifest.yaml. Source sequence variables are
#   retained where occurrence-level ties require them (ADCM.CMSEQ, ADAE.AESEQ,
#   ADLB.LBSEQ); BDS keys include the analysis parameter/visit/date components.
#   Both tracks must be unique on the declared key before diffdf compares values.
#   This is direct keyed row parity, not positional or content-sorted pairing.
#   Neither track reads the other's output. As with all double programming, a
#   correlated error implemented independently in both tracks remains possible.

library(haven)
library(dplyr)
library(diffdf)
source("04_analysis_datasets/programs/r/config_study.R")

# Study structure from the manifest (I/J platform generalisation): the reconciled
# dataset list, their per-dataset business keys, and the study identity are declared
# in config/study_manifest.yaml rather than hardcoded here. Resolve from . or .. so the
# script works whether invoked from the repo root (via cibuild) or 06_qc_evidence/reconciliation/.
.manifest_file <- Filter(file.exists,
                         c("config/study_manifest.yaml", file.path("..", "config/study_manifest.yaml")))
if (!length(.manifest_file)) stop("config/study_manifest.yaml not found in . or ..")
.manifest <- yaml::read_yaml(.manifest_file[[1]])
datasets <- vapply(.manifest$datasets, function(d) d$name, character(1))
.key_map <- stats::setNames(
  lapply(.manifest$datasets, function(d) unlist(d$keys, use.names = FALSE)),
  datasets
)
.study_title <- .manifest$study$title
.study_code  <- .manifest$study$code

cat("NOTE: [RECONCILIATION] Starting Cross-Language Audit...\n")

# Carry the execution mode into every reconciliation decision. A transient
# subject-level SAS endpoint extract is mandatory only for a current real-SAS
# run; sim/cached modes remain explicitly non-release evidence.
execution_mode <- Sys.getenv("TROPIC_SAS_MODE", unset = "sim")
is_simulated <- Sys.getenv("TROPIC_SAS_SIMULATION") == "TRUE"

compare_datasets <- function(ds_name) {
  prod_path <- paste0("04_analysis_datasets/adam/", ds_name, "_prod.xpt")
  val_path <- paste0("04_analysis_datasets/adam/", ds_name, "_v.xpt")

  if (!file.exists(prod_path) || !file.exists(val_path)) {
    return(list(status = "FAIL", reason = "Missing production or validation XPT file"))
  }

  prod <- read_xpt(prod_path)
  val <- read_xpt(val_path)

  diff_dir <- "06_qc_evidence/reconciliation/differences"
  dir.create(diff_dir, recursive = TRUE, showWarnings = FALSE)
  stale <- list.files(
    diff_dir,
    pattern = paste0("^", tolower(ds_name), "__"),
    full.names = TRUE
  )
  if (length(stale)) unlink(stale)

  # Standardize column casing
  colnames(prod) <- toupper(colnames(prod))
  colnames(val) <- toupper(colnames(val))

  # Column symmetry check (QC-02)
  prod_cols <- colnames(prod)
  val_cols <- colnames(val)
  extra_in_prod <- setdiff(prod_cols, val_cols)
  extra_in_val <- setdiff(val_cols, prod_cols)

  if (length(extra_in_prod) > 0 || length(extra_in_val) > 0) {
    reason_parts <- c()
    if (length(extra_in_prod) > 0) {
      reason_parts <- c(reason_parts, paste("Extra in Prod:", paste(extra_in_prod, collapse = ", ")))
    }
    if (length(extra_in_val) > 0) {
      reason_parts <- c(reason_parts, paste("Extra in Val:", paste(extra_in_val, collapse = ", ")))
    }
    return(list(status = "FAIL", reason = paste("Column mismatch -", paste(reason_parts, collapse = "; "))))
  }

  # Align business keys from the manifest's per-dataset key map (QC-01)
  sort_keys <- .key_map[[ds_name]]
  if (is.null(sort_keys) || !length(sort_keys)) {
    return(list(status = "FAIL",
                reason = paste("No business keys declared in manifest for", ds_name)))
  }

  # Align column classes & types first to ensure clean sorting
  common_cols <- intersect(colnames(prod), colnames(val))
  for (col in common_cols) {
    p_col <- prod[[col]]
    v_col <- val[[col]]

    # Handle factor/character mismatch
    if (is.character(p_col) || is.factor(p_col)) {
      prod[[col]] <- as.character(p_col)
      val[[col]]  <- as.character(v_col)
    }

    # Coerce transport blank strings to missing, but preserve literal "NA" as data.
    # A literal "NA" must fail reconciliation unless it is explicitly defined as a
    # legitimate analysis value.
    if (is.character(prod[[col]])) {
      prod[[col]] <- trimws(prod[[col]])
      val[[col]]  <- trimws(val[[col]])
      prod[[col]][is.na(prod[[col]]) | prod[[col]] == ""] <- NA_character_
      val[[col]][is.na(val[[col]]) | val[[col]] == ""]   <- NA_character_
    }
  }

  missing_prod_keys <- setdiff(sort_keys, names(prod))
  missing_val_keys <- setdiff(sort_keys, names(val))
  if (length(missing_prod_keys) || length(missing_val_keys)) {
    return(list(
      status = "FAIL",
      reason = paste0(
        "Declared key missing (prod: ", paste(missing_prod_keys, collapse = ", "),
        "; validation: ", paste(missing_val_keys, collapse = ", "), ")"
      )
    ))
  }
  prod_dups <- sum(duplicated(prod[sort_keys]))
  val_dups <- sum(duplicated(val[sort_keys]))
  if (prod_dups || val_dups) {
    return(list(
      status = "FAIL",
      reason = paste0(
        "Governed key is not unique (prod duplicates=", prod_dups,
        ", validation duplicates=", val_dups, ")"
      )
    ))
  }

  prod <- prod %>% arrange(across(all_of(sort_keys)))
  val <- val %>% arrange(across(all_of(sort_keys)))

  # Compare using diffdf package
  diff_res <- diffdf(prod, val, keys = sort_keys, suppress_warnings = TRUE)

  actual_issues <- setdiff(names(diff_res), c("DataSummary", "AttribDiffs"))

  if (length(actual_issues) == 0) {
    return(list(status = "PASS", reason = "Zero cell-level differences"))
  } else {
    detail_names <- grep("^VarDiff_", names(diff_res), value = TRUE)
    for (detail_name in detail_names) {
      variable <- sub("^VarDiff_", "", detail_name)
      detail_path <- file.path(
        diff_dir,
        paste0(tolower(ds_name), "__", tolower(variable), ".csv")
      )
      utils::write.csv(as.data.frame(diff_res[[detail_name]]), detail_path, row.names = FALSE)
      cat("  [DETAIL] ", detail_path, "\n", sep = "")
      print(utils::head(as.data.frame(diff_res[[detail_name]]), 10), row.names = FALSE)
    }
    total_diffs <- 0
    if ("NumDiff" %in% names(diff_res)) {
      num_diff <- diff_res$NumDiff
      for (i in seq_len(nrow(num_diff))) {
        var_name <- num_diff$Variable[i]
        n_mismatches <- num_diff[["No of Differences"]][i]
        total_diffs <- total_diffs + n_mismatches
        cat(paste("  [MISMATCH] Column", var_name, "has", n_mismatches, "cell differences (diffdf audit).\n"))
      }
    } else {
      total_diffs <- 1
    }
    return(list(status = "FAIL", reason = paste(total_diffs, "cell differences found")))
  }
}

parse_endpoint_date <- function(x) {
  if (inherits(x, "Date")) return(x)
  if (is.numeric(x)) return(as.Date(x, origin = "1960-01-01"))
  value <- trimws(as.character(x))
  value[value %in% c("", ".")] <- NA_character_
  out <- as.Date(rep(NA_character_, length(value)))
  for (fmt in c("%Y-%m-%d", "%m/%d/%Y", "%d%b%Y")) {
    pending <- is.na(out) & !is.na(value)
    if (any(pending)) {
      out[pending] <- as.Date(value[pending], format = fmt)
    }
  }
  numeric_value <- suppressWarnings(as.numeric(value))
  numeric_pending <- is.na(out) & !is.na(numeric_value)
  out[numeric_pending] <- as.Date(numeric_value[numeric_pending], origin = "1960-01-01")
  out
}

compare_f042_pain_response <- function() {
  sas_path <- "04_analysis_datasets/adam/f042_pain_response_prod.csv"
  if (!file.exists(sas_path)) {
    if (execution_mode %in% c("oda", "local")) {
      return(list(
        status = "FAIL",
        reason = "Current real-SAS run did not produce the required F-042 response extract"
      ))
    }
    return(list(
      status = "SKIPPED",
      reason = paste("Endpoint extract unavailable in", execution_mode, "mode")
    ))
  }
  on.exit(unlink(sas_path), add = TRUE)

  tryCatch({
    sas <- read.csv(
      sas_path,
      stringsAsFactors = FALSE,
      check.names = FALSE,
      na.strings = c("", ".")
    )
    names(sas) <- toupper(names(sas))
    required <- c(
      "USUBJID", "EVENT_DATE", "CONFIRMING_DATE", "RESPONSE_COMPONENT",
      "EVENT_DATE_SOURCE", "CONFIRMING_DATE_SOURCE"
    )
    missing_sas <- setdiff(required, names(sas))
    if (length(missing_sas)) {
      return(list(
        status = "FAIL",
        reason = paste("SAS F-042 extract missing columns:", paste(missing_sas, collapse = ", "))
      ))
    }

    source(
      "04_analysis_datasets/programs/r/f042_provisional_pain_derivation.R",
      local = TRUE
    )
    r_result <- f042_derive(
      read_xpt("04_analysis_datasets/adam/adsl_v.xpt"),
      readRDS(stage_file("pn")),
      readRDS(stage_file("sv")),
      readRDS(stage_file("cm")),
      readRDS(stage_file("pr")),
      read_xpt("04_analysis_datasets/adam/adrs_v.xpt"),
      readRDS(stage_file("ds"))
    )

    sas_cmp <- sas |>
      transmute(
        USUBJID = trimws(as.character(USUBJID)),
        EVENT_DATE = format(parse_endpoint_date(EVENT_DATE), "%Y-%m-%d"),
        CONFIRMING_DATE = format(parse_endpoint_date(CONFIRMING_DATE), "%Y-%m-%d"),
        RESPONSE_COMPONENT = trimws(as.character(RESPONSE_COMPONENT)),
        EVENT_DATE_SOURCE = trimws(as.character(EVENT_DATE_SOURCE)),
        CONFIRMING_DATE_SOURCE = trimws(as.character(CONFIRMING_DATE_SOURCE))
      ) |>
      arrange(USUBJID, EVENT_DATE, CONFIRMING_DATE, RESPONSE_COMPONENT) |>
      as.data.frame()

    r_cmp <- r_result$pain_response_events |>
      transmute(
        USUBJID = trimws(as.character(USUBJID)),
        EVENT_DATE = format(event_date, "%Y-%m-%d"),
        CONFIRMING_DATE = format(confirming_date, "%Y-%m-%d"),
        RESPONSE_COMPONENT = trimws(as.character(response_component)),
        EVENT_DATE_SOURCE = trimws(as.character(event_date_source)),
        CONFIRMING_DATE_SOURCE = trimws(as.character(confirming_date_source))
      ) |>
      arrange(USUBJID, EVENT_DATE, CONFIRMING_DATE, RESPONSE_COMPONENT) |>
      as.data.frame()

    sas_rows <- do.call(paste, c(sas_cmp, sep = "\u001f"))
    r_rows <- do.call(paste, c(r_cmp, sep = "\u001f"))
    sas_only <- sum(!sas_rows %in% r_rows)
    r_only <- sum(!r_rows %in% sas_rows)
    if (identical(sas_cmp, r_cmp)) {
      return(list(
        status = "PASS",
        reason = paste(nrow(r_cmp), "subject-level response records agree exactly")
      ))
    }
    list(
      status = "FAIL",
      reason = paste0(
        "SAS/R F-042 response mismatch: SAS n=", nrow(sas_cmp),
        ", R n=", nrow(r_cmp), ", SAS-only=", sas_only, ", R-only=", r_only
      )
    )
  }, error = function(e) {
    list(status = "FAIL", reason = paste("F-042 comparison error:", conditionMessage(e)))
  })
}

# `datasets` is defined at the top of this script from config/study_manifest.yaml
# (single source of truth); do not redeclare it here.
results <- list()

for (ds in datasets) {
  res <- compare_datasets(ds)
  results[[ds]] <- res
  cat(paste("NOTE: [RECONCILIATION] Dataset:", toupper(ds), "-", res$status, "-", res$reason, "\n"))
}

f042_pain_response <- compare_f042_pain_response()
cat(
  paste(
    "NOTE: [RECONCILIATION] Endpoint control: F042_PAIN_RESPONSE -",
    f042_pain_response$status, "-", f042_pain_response$reason, "\n"
  )
)

banner_html <- ""
if (is_simulated) {
  banner_html <- paste0(
    "<div style='background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; ",
    "padding: 15px; border-radius: 5px; margin-bottom: 20px; font-weight: bold;'>",
    "⚠️ WARNING: Simulated SAS compilation was used. Production datasets (*_prod.xpt) ",
    "were generated by copying the R validation datasets rather than executing a real SAS engine. ",
    "Zero differences are expected and do not guarantee independent double-programming parity on a SAS engine.",
    "</div>"
  )
}

# Generate visual HTML report. Static HTML/CSS template lines exceed the line
# length limit by nature; scoped nolint keeps the markup readable in one piece.
# nolint start: line_length_linter.
html_content <- paste0(
  "<html><head><title>", .study_title, " Cross-Language Reconciliation Report</title>",
  "<style>body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 40px; }",
  "h1 { color: #002d62; } .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
  "table { width: 100%; border-collapse: collapse; margin-top: 20px; } th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }",
  "th { background-color: #002d62; color: white; } .pass { color: green; font-weight: bold; } .fail { color: red; font-weight: bold; }</style></head>",
  "<body><div class='card'><h1>", .study_title, " (Study ", .study_code, ") Cross-Language Audit Dashboard</h1>",
  banner_html,
  "<p>Direct keyed reconciliation comparing the SAS 9.4 production track vs the independent R 4.6.0 Pharmaverse validation track. ",
  "Each dataset must be unique on its governed business key before records are aligned and compared cell-by-cell with diffdf. ",
  "A PASS confirms direct row and value parity; neither track reads the other's output.</p>",
  "<table><thead><tr><th>Dataset</th><th>Status</th><th>Audit Details</th></tr></thead><tbody>"
)

for (ds in datasets) {
  res <- results[[ds]]
  status_class <- if (res$status == "PASS") "pass" else "fail"
  html_content <- paste0(
    html_content,
    "<tr><td><strong>", toupper(ds), "</strong></td><td class='", status_class, "'>", res$status, "</td><td>", res$reason, "</td></tr>"
  )
}

endpoint_status_class <- if (f042_pain_response$status == "PASS") {
  "pass"
} else if (f042_pain_response$status == "FAIL") {
  "fail"
} else {
  ""
}
html_content <- paste0(
  html_content,
  "<tr><td><strong>F042_PAIN_RESPONSE</strong></td><td class='",
  endpoint_status_class, "'>", f042_pain_response$status,
  "</td><td>", f042_pain_response$reason, "</td></tr>"
)

html_content <- paste0(html_content, "</tbody></table></div></body></html>")
# nolint end

dir.create("platform", showWarnings = FALSE)
writeLines(html_content, "platform/reconciliation_report.html")
cat("NOTE: [RECONCILIATION] Visual HTML audit saved to platform/reconciliation_report.html\n")

# Build honesty (audit): emit a machine-readable status and FAIL on any difference.
# Previously this script logged FAILs but exited 0, allowing the orchestrator to
# report GREEN while a domain had cell-level differences. The orchestrator now
# also reads this file to gate Stage 11.
any_fail <- any(vapply(results, function(r) r$status != "PASS", logical(1))) ||
  f042_pain_response$status == "FAIL"
# Carry the execution mode into the machine-readable status so a tautological sim PASS is
# distinguishable from a genuine double-programmed PASS (audit M-1). The orchestrator exports
# TROPIC_SAS_MODE; default to "sim" if absent (safer than implying a real run).
status_json <- paste0(
  "{\n  \"overall\": \"", if (any_fail) "FAIL" else "PASS", "\",\n",
  "  \"simulated\": ", if (is_simulated) "true" else "false", ",\n",
  "  \"execution_mode\": \"", execution_mode, "\",\n",
  "  \"domains\": {\n",
  paste(sprintf("    \"%s\": \"%s\"", toupper(datasets),
                vapply(datasets, function(d) results[[d]]$status, character(1))),
        collapse = ",\n"),
  "\n  },\n",
  "  \"endpoint_controls\": {\n",
  "    \"F042_PAIN_RESPONSE\": \"", f042_pain_response$status, "\"\n",
  "  }\n}\n"
)
writeLines(status_json, "platform/reconciliation_status.json")

if (any_fail) {
  failed <- toupper(names(Filter(function(r) r$status != "PASS", results)))
  if (f042_pain_response$status == "FAIL") {
    failed <- c(failed, "F042_PAIN_RESPONSE")
  }
  stop(sprintf("RECONCILIATION FAILED: differences in %s. See cross_lang_audit.log.",
               paste(failed, collapse = ", ")))
}

# Program: cross_lang_audit.R | Version: 3.5.0 | Author: Clinical Data Architect | Date: 2026-06-12
# Description: Cross-Language reconciliation comparing the SAS production track
#   (*_prod.xpt) against the independent R validation track (*_v.xpt).
#
# METHODOLOGY (audit F-6): This is a KEYED RECORD-CONTENT (multiset) comparison.
#   Some reconciled ADaM datasets carry a unique within-subject record identifier and
#   some do not: ADAE retains AESEQ end-to-end in BOTH tracks, so it is compared on the
#   unique key USUBJID+AESEQ (positional parity). The BDS/OCCDS datasets that have no
#   unique record id (ADCM, ADLB, ADRS, ADEX) get the multiset test below. When no
#   unique key exists, the only well-defined parity test is whether both tracks
#   contain the SAME MULTISET of records within each business-key group. Records
#   are therefore aligned by business keys and, within tie groups, by full record
#   content to form a deterministic pairing; diffdf then compares cell values.
#   A PASS means "both engines produced identical record content" -- it does NOT
#   assert that an independent unique-key row index was reproduced. Neither track
#   reads the other's output (the R track was decoupled from *_prod.xpt per F-1).
#   RESIDUAL LIMITATION (documented, not a defect of the multiset test): like ALL
#   double-programming, reconciliation cannot detect a CORRELATED error -- if both
#   independent tracks compute the SAME wrong value, the comparison passes. This is
#   inherent to dual-programming, not specific to the keyless path; the multiset test
#   detects every single-track content difference (see tests/smoke_test.R Cases C-E).

library(haven)
library(dplyr)
library(diffdf)

cat("NOTE: [RECONCILIATION] Starting Cross-Language Audit...\n")

compare_datasets <- function(ds_name) {
  prod_path <- paste0("04_adam/", ds_name, "_prod.xpt")
  val_path <- paste0("04_adam/", ds_name, "_v.xpt")
  
  if (!file.exists(prod_path) || !file.exists(val_path)) {
    return(list(status = "FAIL", reason = "Missing production or validation XPT file"))
  }
  
  prod <- read_xpt(prod_path)
  val <- read_xpt(val_path)
  
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
  
  # Align business keys based on dataset name (QC-01)
  if (ds_name == "adsl") {
    sort_keys <- "USUBJID"
  } else if (ds_name == "adex") {
    sort_keys <- c("USUBJID", "PARAMCD", "AVISIT")
  } else if (ds_name == "adcm") {
    sort_keys <- c("USUBJID", "CMSTDT", "CMDECOD")
  } else if (ds_name == "adae") {
    sort_keys <- c("USUBJID", "AESEQ")
  } else if (ds_name == "adlb") {
    sort_keys <- c("USUBJID", "PARAMCD", "AVISITN", "LBDY")
  } else if (ds_name == "adrs") {
    sort_keys <- c("USUBJID", "PARAMCD", "AVISIT")
  } else if (ds_name == "adtte") {
    sort_keys <- c("USUBJID", "PARAMCD")
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
    
    # Coerce missing representations (empty strings and "NA" to NA)
    if (is.character(prod[[col]])) {
      prod[[col]] <- trimws(prod[[col]])
      val[[col]]  <- trimws(val[[col]])
      prod[[col]][is.na(prod[[col]]) | prod[[col]] == "" | prod[[col]] == "NA"] <- NA_character_
      val[[col]][is.na(val[[col]]) | val[[col]] == "" | val[[col]] == "NA"]   <- NA_character_
    }
  }
  
  # Keyed multiset alignment (audit F-6): sort by business keys FIRST, then by
  # remaining columns only to disambiguate records that share a (non-unique)
  # business key. This makes the within-group pairing deterministic so diffdf can
  # compare cell values; it is a record-content/multiset test, not a claim that an
  # independent unique-key row index was reproduced (see methodology note above).
  other_cols <- setdiff(common_cols, sort_keys)
  prod <- prod %>% arrange(across(all_of(c(sort_keys, other_cols))))
  val  <- val  %>% arrange(across(all_of(c(sort_keys, other_cols))))

  # Add SEQ number within each business key group to guarantee uniqueness
  prod <- prod %>%
    group_by(across(all_of(sort_keys))) %>% 
    mutate(SEQ = row_number()) %>% 
    ungroup()
    
  val <- val %>% 
    group_by(across(all_of(sort_keys))) %>% 
    mutate(SEQ = row_number()) %>% 
    ungroup()
    
  keys <- c(sort_keys, "SEQ")
  
  # Compare using diffdf package
  diff_res <- diffdf(prod, val, keys = keys, suppress_warnings = TRUE)
  
  actual_issues <- setdiff(names(diff_res), c("DataSummary", "AttribDiffs"))
  
  if (length(actual_issues) == 0) {
    return(list(status = "PASS", reason = "Zero cell-level differences"))
  } else {
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

datasets <- c("adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte")
results <- list()

for (ds in datasets) {
  res <- compare_datasets(ds)
  results[[ds]] <- res
  cat(paste("NOTE: [RECONCILIATION] Dataset:", toupper(ds), "-", res$status, "-", res$reason, "\n"))
}

# Determine if simulation mode is active
is_simulated <- Sys.getenv("TROPIC_SAS_SIMULATION") == "TRUE"

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

# Generate visual HTML report
html_content <- paste0(
  "<html><head><title>TROPIC Cross-Language Reconciliation Report</title>",
  "<style>body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 40px; }",
  "h1 { color: #002d62; } .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
  "table { width: 100%; border-collapse: collapse; margin-top: 20px; } th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }",
  "th { background-color: #002d62; color: white; } .pass { color: green; font-weight: bold; } .fail { color: red; font-weight: bold; }</style></head>",
  "<body><div class='card'><h1>TROPIC (Study EFC6193 / XRP6258) Cross-Language Audit Dashboard</h1>",
  banner_html,
  "<p>Keyed record-content (multiset) reconciliation comparing the SAS 9.4 production track vs the independent R 4.6.0 Pharmaverse validation track. ",
  "Records are aligned by business keys (within tie groups, by full record content) and compared cell-by-cell with diffdf. ",
  "A PASS confirms both engines produced identical record content for datasets that carry no unique row identifier; neither track reads the other's output.</p>",
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

html_content <- paste0(html_content, "</tbody></table></div></body></html>")

dir.create("06_telemetry", showWarnings = FALSE)
writeLines(html_content, "06_telemetry/reconciliation_report.html")
cat("NOTE: [RECONCILIATION] Visual HTML audit saved to 06_telemetry/reconciliation_report.html\n")

# Build honesty (audit): emit a machine-readable status and FAIL on any difference.
# Previously this script logged FAILs but exited 0, allowing the orchestrator to
# report GREEN while a domain had cell-level differences. The orchestrator now
# also reads this file to gate Stage 11.
any_fail <- any(vapply(results, function(r) r$status != "PASS", logical(1)))
status_json <- paste0(
  "{\n  \"overall\": \"", if (any_fail) "FAIL" else "PASS", "\",\n  \"domains\": {\n",
  paste(sprintf("    \"%s\": \"%s\"", toupper(datasets),
                vapply(datasets, function(d) results[[d]]$status, character(1))),
        collapse = ",\n"),
  "\n  }\n}\n"
)
writeLines(status_json, "06_telemetry/reconciliation_status.json")

if (any_fail) {
  failed <- toupper(names(Filter(function(r) r$status != "PASS", results)))
  stop(sprintf("RECONCILIATION FAILED: cell-level differences in %s. See cross_lang_audit.log.",
               paste(failed, collapse = ", ")))
}

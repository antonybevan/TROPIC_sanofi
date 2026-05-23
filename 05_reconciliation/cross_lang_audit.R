# Program: cross_lang_audit.R | Version: 2.0 | Author: Clinical Data Architect | Date: 2026-05-23
# Description: Cross-Language cell-by-cell validation audit comparing SAS (*_prod.xpt) and R (*_val.xpt).

library(haven)
library(dplyr)

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
  
  # Align keys and columns
  prod <- prod %>% arrange(USUBJID)
  val <- val %>% arrange(USUBJID)
  
  # Cell-by-cell comparison
  diffs <- 0
  common_cols <- intersect(colnames(prod), colnames(val))
  
  if (nrow(prod) != nrow(val)) {
    return(list(status = "FAIL", reason = paste("Row count mismatch: Prod =", nrow(prod), ", Val =", nrow(val))))
  }
  
  for (col in common_cols) {
    p_col <- prod[[col]]
    v_col <- val[[col]]
    
    # Handle factor/character mismatch
    if (is.character(p_col) || is.factor(p_col)) {
      p_col <- as.character(p_col)
      v_col <- as.character(v_col)
    }
    
    # Coerce missing representations
    p_col[is.na(p_col) | p_col == ""] <- NA
    v_col[is.na(v_col) | v_col == ""] <- NA
    
    mismatches <- which(p_col != v_col & !(is.na(p_col) & is.na(v_col)))
    if (length(mismatches) > 0) {
      diffs <- diffs + length(mismatches)
      cat(paste("  [MISMATCH] Column", col, "has", length(mismatches), "cell differences.\n"))
    }
  }
  
  if (diffs == 0) {
    return(list(status = "PASS", reason = "Zero cell-level differences"))
  } else {
    return(list(status = "FAIL", reason = paste(diffs, "cell differences found")))
  }
}

datasets <- c("adsl", "adex", "adcm", "adae", "adlb", "adrs", "adtte")
results <- list()

for (ds in datasets) {
  res <- compare_datasets(ds)
  results[[ds]] <- res
  cat(paste("NOTE: [RECONCILIATION] Dataset:", toupper(ds), "-", res$status, "-", res$reason, "\n"))
}

# Generate visual HTML report
html_content <- paste0(
  "<html><head><title>TROPIC Cross-Language Reconciliation Report</title>",
  "<style>body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f8f9fa; color: #333; margin: 40px; }",
  "h1 { color: #002d62; } .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }",
  "table { width: 100%; border-collapse: collapse; margin-top: 20px; } th, td { padding: 12px; border-bottom: 1px solid #ddd; text-align: left; }",
  "th { background-color: #002d62; color: white; } .pass { color: green; font-weight: bold; } .fail { color: red; font-weight: bold; }</style></head>",
  "<body><div class='card'><h1>TROPIC-CDI-E2E-v2.0 Cross-Language Audit Dashboard</h1>",
  "<p>Cell-by-cell validation report comparing SAS 9.4 Production models vs R 4.5.2 Pharmaverse Validation Track.</p>",
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

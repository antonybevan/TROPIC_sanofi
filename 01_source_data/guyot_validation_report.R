# ==============================================================================
# guyot_validation_report.R — Acceptance gates for the Guyot reconstruction
# Author: Antony Bevan | Date: 2026-06-18
#
# Validates the genuine IPDfromKM reconstruction (reconstruct_cbzp_guyot.R)
# against the published de Bono 2010 CbzP summary statistics. It also runs
# NON-BLOCKING comparative-compatibility diagnostics against the current real
# MP derivation using the exact stratified TFL method. A compatibility warning
# does not invalidate the digitised CbzP curve; it means the two live endpoint
# implementations should not be represented as reproducing the published HR.
#
# Run:  Rscript 01_source_data/guyot_validation_report.R
# Emits: console table + 01_source_data/guyot_validation_report.md
#        platform/guyot_validation_status.json
#        Exit status 1 if a core reconstruction gate fails or coordinates are
#        not DIGITISED. Comparative diagnostics are disclosed warnings.
#
# Published targets (de Bono Lancet 2010;376:1147-1154):
#   OS:  deaths=227 (Table 5), median=15.1 mo (14.1-16.3), HR=0.70 (0.59-0.83) vs MP
#   PFS: median=2.8 mo (2.4-3.0), HR=0.74 (0.64-0.86) vs MP (no published PFS event count)
# ==============================================================================

suppressMessages({
  library(survival)
  library(haven)
  library(dplyr)
})
source("05_outputs/tfl/tfl_stats.R")

DAYS_PER_MONTH <- 30.4375

# ---- 1. Reconstruct (sources the genuine IPDfromKM engine) -------------------
source("01_source_data/reconstruct_cbzp_guyot.R")
# Provides: guyot_os_ipd, guyot_pfs_ipd (time = months, status); os_rec, pfs_rec;
#           .provenance, .guyot_verified

# ---- 2. Live TFL compatibility inputs ----------------------------------------
# The reconstruction stage immediately preceding this gate creates the exact
# comparator RDS objects consumed by tfl_generation.R. Reuse them and the shared
# statistical function so the validation report cannot drift from the display.
required_files <- c(
  "04_analysis_datasets/adam/adsl_v.xpt",
  "04_analysis_datasets/adam/adtte_v.xpt",
  "01_source_data/cbzp_reconstructed/adsl_cbzp.rds",
  "01_source_data/cbzp_reconstructed/adtte_cbzp.rds"
)
missing_files <- required_files[!file.exists(required_files)]
if (length(missing_files) > 0L) {
  stop(
    "Missing live compatibility input(s): ", paste(missing_files, collapse = ", "),
    ". Run 01_source_data/reconstruct_cbzp_arm.R after the R ADaM derivations."
  )
}

adsl_all <- bind_rows(
  read_xpt(required_files[1]) |> filter(TRT01P == "MP"),
  readRDS(required_files[3])
)
adtte_all <- bind_rows(
  read_xpt(required_files[2]) |> filter(TRT01P == "MP"),
  readRDS(required_files[4])
)

live_tte_stats <- function(paramcd) {
  d <- adtte_all |>
    filter(PARAMCD == paramcd) |>
    select(USUBJID, TRT01P, AVAL, CNSR) |>
    left_join(adsl_all |> select(USUBJID, ECOGBL, MEASDISF), by = "USUBJID")
  compute_tte_stats(d)
}
os_live <- live_tte_stats("OS")
pfs_live <- live_tte_stats("PFS")

# ---- 4. Gate table -----------------------------------------------------------
gate <- function(classification, name, value, pass, target, required = TRUE) {
  data.frame(Classification = classification, Gate = name, Value = value, Target = target,
             Result = ifelse(isTRUE(pass), "PASS", "FAIL"),
             Required = required,
             stringsAsFactors = FALSE)
}
gates <- rbind(
  gate("CORE", "OS median (mo)",  sprintf("%.1f", os_rec$median),
       !is.na(os_rec$median) && os_rec$median >= 14.1 && os_rec$median <= 16.1, "14.1-16.1"),
  gate("CORE", "PFS median (mo)", sprintf("%.1f", pfs_rec$median),
       !is.na(pfs_rec$median) && pfs_rec$median >= 2.3 && pfs_rec$median <= 3.3, "2.3-3.3"),
  gate("CORE", "OS deaths",  os_rec$events,  abs(os_rec$events - 227L) <= 10L, "~227 (Table 5)"),
  gate("CORE", "PFS events", pfs_rec$events, TRUE, "reconstructed (no pub. count)"),
  gate("CORE", "OS curve fit max|dev|",  sprintf("%.4f", os_rec$max_dev),  os_rec$max_dev  < 0.05, "< 0.05"),
  gate("CORE", "PFS curve fit max|dev|", sprintf("%.4f", pfs_rec$max_dev), pfs_rec$max_dev < 0.05, "< 0.05"),
  gate("COMPATIBILITY", "OS stratified HR vs live MP",
       sprintf("%.2f (%.2f-%.2f)", os_live$hr, os_live$lcl, os_live$ucl),
       os_live$hr >= 0.60 && os_live$hr <= 0.80, "0.60-0.80", required = FALSE),
  gate("COMPATIBILITY", "PFS stratified HR vs live MP",
       sprintf("%.2f (%.2f-%.2f)", pfs_live$hr, pfs_live$lcl, pfs_live$ucl),
       pfs_live$hr >= 0.64 && pfs_live$hr <= 0.84, "0.64-0.84", required = FALSE)
)

cat("\n  [VALIDATION] ============ ACCEPTANCE GATES ============\n")
for (i in seq_len(nrow(gates))) {
    cat(sprintf("    %-13s %-34s %-18s (target %-10s) %s\n",
              gates$Classification[i], gates$Gate[i], gates$Value[i],
              gates$Target[i], gates$Result[i]))
}
core_pass <- all(gates$Result[gates$Required] == "PASS")
compatibility_pass <- all(gates$Result[!gates$Required] == "PASS")
verified <- isTRUE(.guyot_verified)
overall <- if (!core_pass || !verified) {
  "FAIL"
} else if (!compatibility_pass) {
  "PASS_WITH_WARNING"
} else {
  "PASS"
}
cat(sprintf("\n  Core: %s | Compatibility: %s | Provenance: %s\n",
            ifelse(core_pass, "PASS", "FAIL"),
            ifelse(compatibility_pass, "PASS", "WARNING"),
            ifelse(verified, "VERIFIED-DIGITISED", "UNVERIFIED (placeholder coords)")))
cat("  ====================================================\n")
if (!compatibility_pass && core_pass && verified) {
  cat("  [WARNING] The live comparative PFS HR is outside the legacy compatibility range.\n")
  cat("            Do not claim that the mixed-source PFS comparison reproduces the published effect.\n")
}

# ---- 5. Markdown report ------------------------------------------------------
md <- c(
  "# Guyot Reconstruction — Validation Report",
  "",
  sprintf("_Generated: %s_", format(Sys.time(), "%Y-%m-%d %H:%M")),
  sprintf("_Coordinate provenance: **%s**_", .provenance),
  "",
  "Method: genuine Guyot (2012) IPD reconstruction via `IPDfromKM` from digitised",
  "de Bono 2010 Lancet KM curves (Fig 2A OS, Fig 3 PFS), CbzP arm.",
  "Core gates assess the CbzP reconstruction itself. Compatibility diagnostics",
  "compare it with the current real-MP derivation using the same stratified Cox",
  "method as the TFLs; those diagnostics are non-blocking because a mixed-source",
  "comparison is not intrinsic validation of the digitised CbzP curve.",
  "",
  "| Classification | Gate | Value | Target | Result |",
  "|---|---|---|---|---|",
  apply(gates, 1, function(r) {
    sprintf("| %s | %s | %s | %s | %s |", r["Classification"], r["Gate"],
            r["Value"], r["Target"], r["Result"])
  }),
  "",
  sprintf("**Overall: %s** — core reconstruction %s; comparative compatibility %s; provenance %s.",
          gsub("_", " ", overall),
          ifelse(core_pass, "PASS", "FAIL"),
          ifelse(compatibility_pass, "PASS", "WARNING"),
          ifelse(verified, "VERIFIED-DIGITISED", "UNVERIFIED (placeholder coordinates)")),
  ""
)
if (!compatibility_pass && core_pass && verified) {
  md <- c(md,
          "> [!WARNING]",
          "> The live stratified PFS comparison is outside the legacy compatibility range.",
          "> The corrected real-MP PFS endpoint uses typed RECIST/PSA/F-042 pain/death",
          "> components and excludes exploratory bone/clinical-progression signals. The",
          "> mixed-source comparison must not be described as reproducing the published PFS HR.", "")
}
if (!verified) {
  md <- c(md,
          "> [!WARNING]",
          "> Coordinates are placeholder (not figure-digitised). Gate results are",
          "> mechanical only and do not certify the reconstruction. Supply genuinely",
          "> digitised CSVs and set `PROVENANCE` to `DIGITISED`, then re-run.", "")
}
writeLines(md, "01_source_data/guyot_validation_report.md")
cat("  [VALIDATION] Wrote 01_source_data/guyot_validation_report.md\n")

dir.create("platform", showWarnings = FALSE)
status_json <- c(
  "{",
  sprintf('  "overall": "%s",', overall),
  sprintf('  "core_reconstruction": "%s",', ifelse(core_pass, "PASS", "FAIL")),
  sprintf('  "comparative_compatibility": "%s",', ifelse(compatibility_pass, "PASS", "WARNING")),
  sprintf('  "coordinate_provenance": "%s",', .provenance),
  sprintf('  "os_hr": %.10f,', os_live$hr),
  sprintf('  "pfs_hr": %.10f,', pfs_live$hr),
  sprintf('  "pfs_logrank_p": %.12g', pfs_live$pval),
  "}"
)
writeLines(status_json, "platform/guyot_validation_status.json")
cat("  [VALIDATION] Wrote platform/guyot_validation_status.json\n")

# ---- 6. Exit status for pipeline integration ---------------------------------
if (!core_pass || !verified) quit(status = 1L, save = "no")

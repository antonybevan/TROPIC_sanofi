# ==============================================================================
# guyot_validation_report.R — Acceptance gates for the Guyot reconstruction
# Author: Antony Bevan | Date: 2026-06-18
#
# Validates the genuine IPDfromKM reconstruction (reconstruct_cbzp_guyot.R)
# against the published de Bono 2010 summary statistics, INCLUDING the
# HR-vs-real-MP-arm gates that the reconstruction script cannot check on its
# own (it has no access to the MP arm).
#
# Run:  Rscript 01_raw_source/guyot_validation_report.R
# Emits: console table + 01_raw_source/guyot_validation_report.md
#        Exit status 1 if any gate fails OR coordinates are not DIGITISED.
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

DAYS_PER_MONTH <- 30.4375

# ---- 1. Reconstruct (sources the genuine IPDfromKM engine) -------------------
source("01_raw_source/reconstruct_cbzp_guyot.R")
# Provides: guyot_os_ipd, guyot_pfs_ipd (time = months, status); os_rec, pfs_rec;
#           .provenance, .guyot_verified

# ---- 2. Real MP arm (ground-truth comparator) --------------------------------
adtte_mp <- read_xpt("04_adam/adtte_v.xpt") %>% filter(TRT01P == "MP")
mp_arm <- function(pcd) {
  d <- adtte_mp %>% filter(PARAMCD == pcd)
  data.frame(time = d$AVAL / DAYS_PER_MONTH, status = as.integer(1 - d$CNSR))
}
os_mp  <- mp_arm("OS")
pfs_mp <- mp_arm("PFS")

# ---- 3. HR of Guyot CbzP vs real MP (Cox PH, reference = MP) ------------------
cox_hr <- function(cbzp_ipd, mp_ipd) {
  df <- rbind(
    transform(cbzp_ipd[, c("time", "status")], arm = "CbzP"),
    transform(mp_ipd[,   c("time", "status")], arm = "MP")
  )
  df$arm <- relevel(factor(df$arm), ref = "MP")
  fit <- coxph(Surv(time, status) ~ arm, data = df)
  ci  <- summary(fit)$conf.int            # exp(coef), lower .95, upper .95
  c(hr = unname(ci[1, "exp(coef)"]),
    lo = unname(ci[1, "lower .95"]),
    hi = unname(ci[1, "upper .95"]))
}
os_hr  <- cox_hr(guyot_os_ipd,  os_mp)
pfs_hr <- cox_hr(guyot_pfs_ipd, pfs_mp)

# ---- 4. Gate table -----------------------------------------------------------
gate <- function(name, value, pass, target) {
  data.frame(Gate = name, Value = value, Target = target,
             Result = ifelse(isTRUE(pass), "PASS", "FAIL"),
             stringsAsFactors = FALSE)
}
gates <- rbind(
  gate("OS median (mo)",  sprintf("%.1f", os_rec$median),
       !is.na(os_rec$median) && os_rec$median >= 14.1 && os_rec$median <= 16.1, "14.1-16.1"),
  gate("PFS median (mo)", sprintf("%.1f", pfs_rec$median),
       !is.na(pfs_rec$median) && pfs_rec$median >= 2.3 && pfs_rec$median <= 3.3, "2.3-3.3"),
  gate("OS deaths",  os_rec$events,  abs(os_rec$events - 227L) <= 10L, "~227 (Table 5)"),
  gate("PFS events", pfs_rec$events, TRUE, "reconstructed (no pub. count)"),
  gate("OS HR vs MP",  sprintf("%.2f (%.2f-%.2f)", os_hr["hr"],  os_hr["lo"],  os_hr["hi"]),
       os_hr["hr"]  >= 0.60 && os_hr["hr"]  <= 0.80, "0.60-0.80"),
  gate("PFS HR vs MP", sprintf("%.2f (%.2f-%.2f)", pfs_hr["hr"], pfs_hr["lo"], pfs_hr["hi"]),
       pfs_hr["hr"] >= 0.64 && pfs_hr["hr"] <= 0.84, "0.64-0.84"),
  gate("OS curve fit max|dev|",  sprintf("%.4f", os_rec$max_dev),  os_rec$max_dev  < 0.05, "< 0.05"),
  gate("PFS curve fit max|dev|", sprintf("%.4f", pfs_rec$max_dev), pfs_rec$max_dev < 0.05, "< 0.05")
)

cat("\n  [VALIDATION] ============ ACCEPTANCE GATES ============\n")
for (i in seq_len(nrow(gates))) {
  cat(sprintf("    %-26s %-18s (target %-10s) %s\n",
              gates$Gate[i], gates$Value[i], gates$Target[i], gates$Result[i]))
}
all_pass <- all(gates$Result == "PASS")
verified <- isTRUE(.guyot_verified)
cat(sprintf("\n  Gates: %s | Provenance: %s\n",
            ifelse(all_pass, "ALL PASSED", "SOME FAILED"),
            ifelse(verified, "VERIFIED-DIGITISED", "UNVERIFIED (placeholder coords)")))
cat("  ====================================================\n")

# ---- 5. Markdown report ------------------------------------------------------
md <- c(
  "# Guyot Reconstruction — Validation Report",
  "",
  sprintf("_Generated: %s_  ", format(Sys.time(), "%Y-%m-%d %H:%M")),
  sprintf("_Coordinate provenance: **%s**_", .provenance),
  "",
  "Method: genuine Guyot (2012) IPD reconstruction via `IPDfromKM` from digitised",
  "de Bono 2010 Lancet KM curves (Fig 2A OS, Fig 3 PFS), CbzP arm. HR gates",
  "compare the reconstructed CbzP arm against the **real** MP arm (Cox PH).",
  "",
  "| Gate | Value | Target | Result |",
  "|---|---|---|---|",
  apply(gates, 1, function(r)
    sprintf("| %s | %s | %s | %s |", r["Gate"], r["Value"], r["Target"], r["Result"])),
  "",
  sprintf("**Overall: %s** — provenance %s.",
          ifelse(all_pass, "ALL GATES PASSED", "SOME GATES FAILED"),
          ifelse(verified, "VERIFIED-DIGITISED", "UNVERIFIED (placeholder coordinates)")),
  ""
)
if (!verified) {
  md <- c(md,
    "> [!WARNING]",
    "> Coordinates are placeholder (not figure-digitised). Gate results are",
    "> mechanical only and do not certify the reconstruction. Supply genuinely",
    "> digitised CSVs and set `PROVENANCE` to `DIGITISED`, then re-run.", "")
}
writeLines(md, "01_raw_source/guyot_validation_report.md")
cat("  [VALIDATION] Wrote 01_raw_source/guyot_validation_report.md\n")

# ---- 6. Exit status for pipeline integration ---------------------------------
if (!all_pass || !verified) quit(status = 1L, save = "no")

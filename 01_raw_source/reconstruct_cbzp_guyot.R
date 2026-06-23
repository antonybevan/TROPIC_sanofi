# ==============================================================================
# reconstruct_cbzp_guyot.R — Guyot (2012) IPD reconstruction (genuine)
# Version: 2.0.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-06-18
#
# Purpose: Reconstruct synthetic CbzP-arm Individual Patient Data from the
#          published de Bono 2010 Lancet trial (TROPIC, NCT00417079) using the
#          Guyot (2012) algorithm as implemented in the IPDfromKM CRAN package.
#
# Method (this is a TRUE reconstruction, not a parametric simulation):
#   1. Digitised (time, survival) coordinates are read from the published
#      Kaplan-Meier curve (Figure 2A = OS, Figure 3 = PFS, CbzP arm).
#   2. The published numbers-at-risk table anchors each reporting interval.
#   3. IPDfromKM::preprocess() + getIPD() invert the KM estimator to solve for
#      the event/censoring times that reproduce the observed step function,
#      constrained by total N and total published events.
#
#   Crucially: the survival SHAPE comes from the digitised published curve, NOT
#   from any assumed parametric form and NOT from any hazard ratio. This is the
#   accepted HTA/meta-analysis technique (NICE TSD-14) and removes the
#   circularity of both (a) the superseded PH-scaling approach and (b) the
#   v1.0 Weibull-simulation approach that this script replaces.
#
# Algorithm reference:
#   Guyot P, Ades AE, Ouwens MJNM, Welton NJ. Enhanced secondary analysis of
#   survival data: reconstructing the data from published Kaplan-Meier survival
#   curves. BMC Med Res Methodol 2012;12:9. DOI: 10.1186/1471-2288-12-9
#
# Source data:
#   de Bono JS et al. Lancet 2010;376:1147-1154, Figure 2A (OS) / Figure 3 (PFS).
#
# Inputs (must be GENUINELY digitised — see guyot_digitised/README.md):
#   guyot_digitised/os_cbzp_digitised.csv   (cols: time [months], surv [0-1])
#   guyot_digitised/os_cbzp_nrisk.csv       (cols: time, nrisk)
#   guyot_digitised/pfs_cbzp_digitised.csv  (cols: time [months], surv [0-1])
#   guyot_digitised/pfs_cbzp_nrisk.csv      (cols: time, nrisk)
#   guyot_digitised/PROVENANCE             (text: first line DIGITISED|PLACEHOLDER)
#
# Output objects (interface consumed by reconstruct_cbzp_arm.R):
#   guyot_os_ipd  — data.frame(time [MONTHS], status [1=event,0=censored])
#   guyot_pfs_ipd — data.frame(time [MONTHS], status)
#
# Validation targets (de Bono 2010):
#   OS:  N=378, deaths=227 (Table 5: cabazitaxel total deaths, 61%),
#        median=15.1 mo (14.1-16.3), HR=0.70 (0.59-0.83).
#   PFS: N=378, median=2.8 mo (2.4-3.0), HR=0.74 (0.64-0.86). The paper reports
#        NO separate cabazitaxel PFS event count, so PFS events are reconstructed
#        from the curve + at-risk table (not constrained to an assumed total).
#   (HR-vs-MP gates are checked in guyot_validation_report.R, which has access
#    to the real MP arm; this script checks intrinsic reconstruction quality.)
# ==============================================================================

suppressMessages({
  library(IPDfromKM)
  library(survival)
})

cat("NOTE: [GUYOT] Starting Guyot (2012) IPD reconstruction via IPDfromKM...\n")
cat("      Source: de Bono et al., Lancet 2010;376:1147-1154, Figure 2A (OS) / Figure 3 (PFS)\n")
cat("      Algorithm: Guyot et al., BMC Med Res Methodol 2012;12:9\n\n")

.GUYOT_DIR <- "01_raw_source/guyot_digitised"

# ------------------------------------------------------------------------------
# Provenance guard: refuse to silently pass off placeholder coordinates as a
# real reconstruction. The PROVENANCE file's first token must be DIGITISED for
# the result to be trustworthy; anything else emits a loud warning.
# ------------------------------------------------------------------------------
.provenance <- {
  pf <- file.path(.GUYOT_DIR, "PROVENANCE")
  if (file.exists(pf)) toupper(trimws(readLines(pf, n = 1L, warn = FALSE))) else "MISSING"
}
if (!identical(.provenance, "DIGITISED")) {
  warning(sprintf(
    paste0("[GUYOT] Digitised-curve provenance is '%s', not 'DIGITISED'. ",
           "The reconstruction will RUN but its accuracy is unverified until ",
           "genuinely digitised coordinates from the Lancet figure are supplied. ",
           "See %s/README.md."),
    .provenance, .GUYOT_DIR), call. = FALSE)
  cat(sprintf("WARN: [GUYOT] *** PROVENANCE=%s — coordinates are NOT verified-digitised ***\n\n",
              .provenance))
}

# ------------------------------------------------------------------------------
# Core reconstruction wrapper around IPDfromKM
# ------------------------------------------------------------------------------
reconstruct_guyot <- function(dig_csv, nrisk_csv, total_pts, tot_events, label) {
  #' @param dig_csv    path to digitised (time, surv) CSV; surv on 0-1 scale
  #' @param nrisk_csv  path to numbers-at-risk CSV (time, nrisk)
  #' @param total_pts  published N in the arm
  #' @param tot_events published total event count (constrains censoring split)
  #' @param label      endpoint label for logging
  #' @return list(IPD = data.frame(time [months], status), prep, fit, dig)

  dig <- read.csv(dig_csv)
  stopifnot(all(c("time", "surv") %in% names(dig)))

  # IPDfromKM expects monotone, in-range survival probabilities.
  dig <- dig[order(dig$time), ]
  dig$surv <- cummin(pmax(0, pmin(1, dig$surv)))  # enforce non-increasing in [0,1]

  # At-risk table is optional. When a verified nrisk CSV exists we use it (Guyot
  # full mode); both os/pfs_cbzp_nrisk.csv are transcribed from the published
  # Fig 2A / Fig 3 at-risk rows (see guyot_digitised/PROVENANCE) and improve
  # accuracy (Guyot 2012). Absent a table, we fall back to N + total-events mode.
  have_nrisk <- !is.null(nrisk_csv) && file.exists(nrisk_csv)
  if (have_nrisk) {
    nr <- read.csv(nrisk_csv)
    stopifnot(all(c("time", "nrisk") %in% names(nr)))
    prep <- preprocess(dat = dig[, c("time", "surv")],
                       trisk = nr$time, nrisk = nr$nrisk,
                       totalpts = total_pts, maxy = 1)
  } else {
    cat(sprintf("  [GUYOT] %s: no verified at-risk table — using N + total-events mode.\n", label))
    prep <- preprocess(dat = dig[, c("time", "surv")],
                       totalpts = total_pts, maxy = 1)
  }

  ipd_obj <- if (is.null(tot_events)) {
    getIPD(prep = prep, armID = 1L)
  } else {
    getIPD(prep = prep, armID = 1L, tot.events = tot_events)
  }

  # Normalise to the downstream interface: time (months) + status only.
  ipd <- data.frame(
    time   = ipd_obj$IPD$time,
    status = as.integer(ipd_obj$IPD$status)
  )

  fit          <- survfit(Surv(time, status) ~ 1, data = ipd)
  recon_median <- unname(summary(fit)$table["median"])
  recon_events <- sum(ipd$status)

  # Goodness-of-fit: reconstructed S(t) vs digitised S(t) at digitised times.
  sfun     <- stepfun(fit$time, c(1, fit$surv))
  s_hat    <- sfun(dig$time)
  rmse     <- sqrt(mean((s_hat - dig$surv)^2))
  max_dev  <- max(abs(s_hat - dig$surv))   # Kolmogorov-Smirnov style supremum

  tgt <- if (is.null(tot_events)) "curve-derived" else as.character(tot_events)
  cat(sprintf(
    "  [GUYOT] %s: N=%d, events=%d (target %s), median=%.1f mo | fit RMSE=%.4f, max|dev|=%.4f\n",
    label, nrow(ipd), recon_events, tgt, recon_median, rmse, max_dev))

  list(IPD = ipd, prep = prep, fit = fit, dig = dig,
       median = recon_median, events = recon_events,
       rmse = rmse, max_dev = max_dev)
}

# ==============================================================================
# SECTION 1: OS — Overall Survival (CbzP arm), Figure 2A
# ==============================================================================
os_rec <- reconstruct_guyot(
  dig_csv    = file.path(.GUYOT_DIR, "os_cbzp_digitised.csv"),
  nrisk_csv  = file.path(.GUYOT_DIR, "os_cbzp_nrisk.csv"),
  total_pts  = 378L,
  tot_events = 227L,   # Table 5: cabazitaxel total deaths (61%)
  label      = "OS "
)
guyot_os_ipd <- os_rec$IPD

# ==============================================================================
# SECTION 2: PFS — Progression-Free Survival (CbzP arm), Figure 3
# ==============================================================================
pfs_rec <- reconstruct_guyot(
  dig_csv    = file.path(.GUYOT_DIR, "pfs_cbzp_digitised.csv"),
  nrisk_csv  = file.path(.GUYOT_DIR, "pfs_cbzp_nrisk.csv"),
  total_pts  = 378L,
  tot_events = NULL,   # no published PFS event count — reconstruct from curve + at-risk
  label      = "PFS"
)
guyot_pfs_ipd <- pfs_rec$IPD

# ==============================================================================
# SECTION 3: Intrinsic validation gates (median, events, fit quality)
# HR-vs-real-MP gates live in guyot_validation_report.R.
# ==============================================================================
cat("\n  [GUYOT] ============ RECONSTRUCTION QUALITY ============\n")

gates <- data.frame(
  Gate = c("OS median in range (14.1-16.3 mo)",
           "PFS median in range (2.3-3.3 mo)",
           "OS deaths ~227 (Table 5, +/-10)",
           "OS curve fit max|dev| < 0.05",
           "PFS curve fit max|dev| < 0.05"),
  Result = c(
    !is.na(os_rec$median)  && os_rec$median  >= 14.1 && os_rec$median  <= 16.3,
    !is.na(pfs_rec$median) && pfs_rec$median >= 2.3  && pfs_rec$median <= 3.3,
    abs(os_rec$events - 227L) <= 10L,
    os_rec$max_dev  < 0.05,
    pfs_rec$max_dev < 0.05
  )
)
cat(sprintf("    (PFS reconstructed events = %d — no published count to gate against)\n",
            pfs_rec$events))
for (i in seq_len(nrow(gates))) {
  cat(sprintf("    %s: %s\n", gates$Gate[i],
              ifelse(isTRUE(gates$Result[i]), "PASS", "FAIL")))
}

.guyot_verified <- identical(.provenance, "DIGITISED")
all_pass <- all(gates$Result)
cat(sprintf("\n  Reconstruction gates: %s | Provenance: %s\n",
            ifelse(all_pass, "ALL PASSED", "SOME FAILED"),
            ifelse(.guyot_verified, "VERIFIED-DIGITISED", "UNVERIFIED")))
cat("  ====================================================\n\n")

if (!all_pass) {
  warning("[GUYOT] Not all reconstruction quality gates passed — review before integration.")
}

cat("NOTE: [GUYOT] Reconstruction complete.\n")
cat("      Objects: guyot_os_ipd, guyot_pfs_ipd (time = months, status = 1/0)\n")

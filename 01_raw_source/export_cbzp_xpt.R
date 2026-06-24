# ==============================================================================
# Program: export_cbzp_xpt.R
# Purpose: Bridge the SYNTHETIC CbzP comparator from R (RDS) to SAS-readable V5
#          XPORT, so the SAS production-track TFL program (T_tfl_generation.sas)
#          can read the comparator arm. Idempotent: derives XPT from the existing
#          reconstructed RDS without re-running the (stochastic) reconstruction.
#
# Contract with T_tfl_generation.sas (%rdcbz macro):
#   - one XPT per domain at 01_raw_source/cbzp_reconstructed/<dom>_cbzp.xpt
#   - the single member is named UPCASE(<dom>)_C  (e.g. adtte -> ADTTE_C), which
#     the SAS side references as  set _cz.<UPCASE(dom)>_C;
#
# Run: Rscript 01_raw_source/export_cbzp_xpt.R   (from project root)
# ==============================================================================
suppressMessages({
  library(haven)
})

dir  <- "01_raw_source/cbzp_reconstructed"
doms <- c("adsl", "adtte", "adae", "adlb", "adex", "adrs")

for (d in doms) {
  rds <- file.path(dir, paste0(d, "_cbzp.rds"))
  if (!file.exists(rds)) {
    stop(sprintf("Missing %s -- run 01_raw_source/reconstruct_cbzp_arm.R first.", rds))
  }
  x <- as.data.frame(readRDS(rds))

  # Convert R Date (days since 1970-01-01) to SAS date (days since 1960-01-01).
  # These date columns are not used by the figures, but keeping them valid avoids
  # a silent epoch error if a future figure references them.
  for (col in names(x)) {
    if (inherits(x[[col]], "Date")) x[[col]] <- as.numeric(x[[col]]) + 3653
  }
  names(x) <- toupper(names(x))

  member <- paste0(toupper(d), "_C")          # <=8 chars for all 6 domains
  out    <- file.path(dir, paste0(d, "_cbzp.xpt"))
  write_xpt(x, out, version = 5, name = member)
  cat(sprintf("  [BRIDGE] %-18s -> %s (member %s, %d rows)\n",
              basename(rds), basename(out), member, nrow(x)))
}

cat("NOTE: [BRIDGE] CbzP RDS -> SAS V5 XPORT export complete.\n")

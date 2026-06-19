# DEMO02 stub ADSL validation-track generator (I/J Phase 2).
# Self-contained: synthesises a tiny subject-level dataset and writes the validation
# -track XPT the engine reconciles against. No real data, no SAS, no external inputs.
suppressMessages(library(haven))
dir.create("04_adam", showWarnings = FALSE, recursive = TRUE)

set.seed(42)
n <- 20
adsl <- data.frame(
  STUDYID = "DEMO02",
  USUBJID = sprintf("DEMO02-%03d", seq_len(n)),
  TRT01P  = rep(c("DRUG", "PLACEBO"), length.out = n),
  AGE     = as.integer(round(runif(n, 50, 80))),
  SEX     = rep(c("M", "F"), length.out = n),
  stringsAsFactors = FALSE
)

write_xpt(adsl, "04_adam/adsl_v.xpt")
cat(sprintf("NOTE: [DEMO02] wrote 04_adam/adsl_v.xpt (%d subjects)\n", nrow(adsl)))

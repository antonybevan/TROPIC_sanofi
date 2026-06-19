# DEMO02 stub ADAE validation-track generator (I/J Phase 2).
# Self-contained: synthesises a tiny adverse-event dataset with a unique within-subject
# key (USUBJID+AESEQ) and writes the validation-track XPT the engine reconciles against.
suppressMessages(library(haven))
dir.create("04_adam", showWarnings = FALSE, recursive = TRUE)

set.seed(7)
subj <- sprintf("DEMO02-%03d", rep(seq_len(20), each = 2))
adae <- data.frame(
  STUDYID = "DEMO02",
  USUBJID = subj,
  AESEQ   = as.integer(rep(1:2, times = 20)),
  AEDECOD = rep(c("HEADACHE", "NAUSEA", "FATIGUE", "RASH"), length.out = length(subj)),
  ATOXGR  = as.integer(rep(1:3, length.out = length(subj))),
  stringsAsFactors = FALSE
)

write_xpt(adae, "04_adam/adae_v.xpt")
cat(sprintf("NOTE: [DEMO02] wrote 04_adam/adae_v.xpt (%d records)\n", nrow(adae)))

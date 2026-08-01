# Program: tfl_stats.R | Author: Antony Bevan, Clinical Programming
# Description: Statistical core shared by the TFL reporting track and its regression test.
#   Extracted from tfl_generation.R (roadmap #8) so the survival-analysis recipe can be
#   snapshot-tested on a deterministic fixture without the licensed ADaM data.
# Requires: survival.

# Stratified Cox proportional-hazards HR (+95% CI) and stratified log-rank p-value for a
# two-arm time-to-event analysis, per SAP v4.0 §9 (OS) / §10.1 (PFS). Input df must carry AVAL (days),
# CNSR (0=event,1=censored), TRT01P ("MP"/"CbzP"), and the stratification factors
# ECOGBL and MEASDISF. Returns list(hr, lcl, ucl, pval).
compute_tte_stats <- function(df) {
  df$TRT01P <- factor(df$TRT01P, levels = c("MP", "CbzP"))
  # SAP randomization strata: ECOG 0-1 pooled vs 2 (locked definition), crossed
  # with measurable-disease status. Raw ECOG levels must NOT enter as 3 separate
  # strata (audit MAJOR: previously 6 strata instead of the locked 4).
  df$ECOGBLGRP <- ifelse(df$ECOGBL <= 1, "0-1", "2")
  fit_cox <- survival::coxph(survival::Surv(AVAL, 1 - CNSR) ~ TRT01P + survival::strata(ECOGBLGRP, MEASDISF), data = df)
  s_cox <- summary(fit_cox)
  hr <- s_cox$conf.int[1]
  hr_lcl <- s_cox$conf.int[3]
  hr_ucl <- s_cox$conf.int[4]

  fit_lr <- survival::survdiff(survival::Surv(AVAL, 1 - CNSR) ~ TRT01P + survival::strata(ECOGBLGRP, MEASDISF), data = df)
  pval <- 1 - pchisq(fit_lr$chisq, 1)

  list(hr = hr, lcl = hr_lcl, ucl = hr_ucl, pval = pval)
}

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
  required <- c("AVAL", "CNSR", "TRT01P", "ECOGBL", "MEASDISF")
  missing_vars <- setdiff(required, names(df))
  if (length(missing_vars) > 0L) {
    stop(sprintf("TTE model input is missing required variable(s): %s",
                 paste(missing_vars, collapse = ", ")))
  }
  if (nrow(df) == 0L) stop("TTE model input contains no records.")
  if (any(!complete.cases(df[, required]))) {
    stop("TTE model input has missing AVAL, CNSR, treatment, or stratification values.")
  }
  if (any(!is.finite(df$AVAL)) || any(df$AVAL < 0)) {
    stop("TTE model input AVAL must be finite and non-negative.")
  }
  if (!all(df$CNSR %in% c(0, 1))) {
    stop("TTE model input CNSR must contain only 0 (event) or 1 (censored).")
  }
  if (!setequal(unique(as.character(df$TRT01P)), c("MP", "CbzP"))) {
    stop("TTE model input must contain exactly the MP and CbzP treatment arms.")
  }
  if (!all(df$ECOGBL %in% c(0, 1, 2))) {
    stop("TTE model input ECOGBL must contain only the locked levels 0, 1, or 2.")
  }
  if (!all(as.character(df$MEASDISF) %in% c("N", "Y"))) {
    stop("TTE model input MEASDISF must contain only N or Y.")
  }

  df$TRT01P <- factor(df$TRT01P, levels = c("MP", "CbzP"))
  # SAP randomization strata: ECOG 0-1 pooled vs 2 (locked definition), crossed
  # with measurable-disease status. Raw ECOG levels must NOT enter as 3 separate
  # strata (audit MAJOR: previously 6 strata instead of the locked 4).
  df$ECOGBLGRP <- ifelse(df$ECOGBL <= 1, "0-1", "2")
  fit_cox <- survival::coxph(
    survival::Surv(AVAL, 1 - CNSR) ~ TRT01P +
      survival::strata(ECOGBLGRP, MEASDISF),
    data = df,
    ties = "efron",
    na.action = stats::na.fail,
    singular.ok = FALSE
  )
  s_cox <- summary(fit_cox)
  hr <- s_cox$conf.int[1]
  hr_lcl <- s_cox$conf.int[3]
  hr_ucl <- s_cox$conf.int[4]

  fit_lr <- survival::survdiff(
    survival::Surv(AVAL, 1 - CNSR) ~ TRT01P + survival::strata(ECOGBLGRP, MEASDISF),
    data = df,
    rho = 0,
    na.action = stats::na.fail
  )
  pval <- 1 - pchisq(fit_lr$chisq, 1)

  list(
    hr = hr,
    lcl = hr_lcl,
    ucl = hr_ucl,
    pval = pval,
    n = nrow(df),
    events = sum(1 - df$CNSR),
    logrank_chisq = unname(fit_lr$chisq)
  )
}

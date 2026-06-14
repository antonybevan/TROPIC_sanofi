# ==============================================================================
# Program: tests/test_tfl_stats.R
# Purpose: Numeric SNAPSHOT/regression test for the TFL survival-statistics core
#          (roadmap #8). It locks the stratified Cox / log-rank recipe used to
#          produce every survival HR, CI and p-value in the TFL package
#          (09_tfl/tfl_stats.R, shared by 09_tfl/tfl_generation.R) against
#          deterministic synthetic fixtures, so a change in the modelling code or
#          the survival package version that moves the numbers is caught.
#
#          This is self-contained: it uses NO real ADaM data (which is licensed
#          and git-ignored; a full TFL-output snapshot against the real cohort is
#          a data-gated step — see REPRODUCIBILITY.md). It exercises the actual
#          shared statistical function, not a re-implementation.
#
#          Run:  Rscript tests/test_tfl_stats.R   (or via cibuild --demo)
# ==============================================================================
cat("============== TROPIC TFL-STATS SNAPSHOT TEST ==============\n")
ok <- TRUE
fail <- function(msg) { cat(sprintf("  [FAIL] %s\n", msg)); ok <<- FALSE }
pass <- function(msg) cat(sprintf("  [PASS] %s\n", msg))

if (!requireNamespace("survival", quietly = TRUE)) {
  fail("package 'survival' not installed — run: renv::restore()")
  cat("TFL-STATS SNAPSHOT TEST: FAIL\n"); quit(save = "no", status = 1)
}
source("09_tfl/tfl_stats.R")

# Deterministic two-arm fixture builder (fixed seed -> reproducible draws).
mk_arm <- function(arm, rate, n) data.frame(
  USUBJID  = paste0(arm, seq_len(n)),
  TRT01P   = arm,
  AVAL     = round(rexp(n, rate) * 100) + 1,
  CNSR     = rbinom(n, 1, 0.25),
  ECOGBL   = sample(c(0, 1), n, replace = TRUE),
  MEASDISF = sample(c("Y", "N"), n, replace = TRUE),
  stringsAsFactors = FALSE
)

near <- function(a, b, tol) is.finite(a) && abs(a - b) < tol

# ---- Case 1: strong treatment effect (CbzP hazard < MP hazard) ---------------
# Snapshot captured from survival::coxph on this exact seeded fixture.
set.seed(101)
eff <- rbind(mk_arm("MP", 0.90, 150), mk_arm("CbzP", 0.45, 150))
s <- compute_tte_stats(eff)

if (all(c("hr", "lcl", "ucl", "pval") %in% names(s))) pass("compute_tte_stats returns hr/lcl/ucl/pval") else
  fail(sprintf("unexpected return shape: %s", paste(names(s), collapse = ", ")))

if (near(s$hr, 0.3581843138, 1e-3)) pass(sprintf("effect HR matches snapshot 0.3582 (got %.6f)", s$hr)) else
  fail(sprintf("effect HR drifted from snapshot 0.3582 (got %.6f)", s$hr))
if (near(s$lcl, 0.2648602741, 1e-3) && near(s$ucl, 0.4843912627, 1e-3))
  pass(sprintf("effect 95%% CI matches snapshot [0.265, 0.484] (got [%.3f, %.3f])", s$lcl, s$ucl)) else
  fail(sprintf("effect CI drifted (got [%.6f, %.6f])", s$lcl, s$ucl))
if (s$ucl < 1) pass("effect CI excludes HR=1 (separation detected)") else
  fail("effect CI does not exclude 1 — model lost sensitivity")
if (s$pval < 1e-6) pass(sprintf("effect log-rank p highly significant (%.2e)", s$pval)) else
  fail(sprintf("effect log-rank p not significant (%.3e)", s$pval))

# ---- Case 2: null — two arms with IDENTICAL data must give HR=1, p=1 ----------
set.seed(101)
base <- mk_arm("X", 0.70, 150)
mp   <- transform(base, USUBJID = paste0("MP",   seq_len(150)), TRT01P = "MP")
cbzp <- transform(base, USUBJID = paste0("CbzP", seq_len(150)), TRT01P = "CbzP")
n <- compute_tte_stats(rbind(mp, cbzp))
if (near(n$hr, 1.0, 1e-6)) pass(sprintf("null (identical arms) HR == 1 (got %.6f)", n$hr)) else
  fail(sprintf("null HR != 1 (got %.6f) — false separation", n$hr))
if (near(n$pval, 1.0, 1e-6)) pass(sprintf("null log-rank p == 1 (got %.6f)", n$pval)) else
  fail(sprintf("null p != 1 (got %.6f)", n$pval))

cat("===========================================================\n")
if (ok) {
  cat("TFL-STATS SNAPSHOT TEST: PASS — survival recipe matches snapshot.\n")
  quit(save = "no", status = 0)
} else {
  cat("TFL-STATS SNAPSHOT TEST: FAIL — see [FAIL] lines above.\n")
  quit(save = "no", status = 1)
}

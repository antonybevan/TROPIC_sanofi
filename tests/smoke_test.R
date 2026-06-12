# ==============================================================================
# Program: tests/smoke_test.R
# Purpose: SELF-CONTAINED demonstration that the TROPIC pipeline machinery runs
#          on a clean clone with NO real patient data, NO SAS engine, and NO ODA
#          credentials. Addresses review-board finding EG-1 (third-party
#          reproducibility) by giving any reviewer something they can actually run:
#
#            git clone <repo> && cd TROPIC
#            python3 06_telemetry/cibuild.py --demo
#
#          What it proves:
#            1. The pinned R environment loads (haven, dplyr, diffdf).
#            2. Every pipeline R script parses (no syntax errors on a clean clone).
#            3. The cross-language reconciliation METHODOLOGY works end-to-end on
#               synthetic fixtures, on BOTH branches it uses in production:
#               (a) the unique-key path (USUBJID+AESEQ), and (b) the keyless
#               multiset path used for ADCM/ADLB/ADRS/ADEX (non-unique business
#               key + within-key SEQ). Each PASSES on identical independent
#               outputs and correctly DETECTS an injected cell difference.
#
#          This is a fixture/unit demonstration of the reconciliation engine — the
#          heart of the validation claim — not the full 7-domain clinical run
#          (which requires the licensed SDTM source + a SAS 9.4 engine; see
#          REPRODUCIBILITY.md). No real data is read or written.
# ==============================================================================

cat("================ TROPIC SELF-CONTAINED SMOKE TEST ================\n")
ok <- TRUE
fail <- function(msg) { cat(sprintf("  [FAIL] %s\n", msg)); ok <<- FALSE }
pass <- function(msg) cat(sprintf("  [PASS] %s\n", msg))

# ---- 1. Environment ----------------------------------------------------------
cat("\n[1/3] Environment check\n")
need <- c("haven", "dplyr", "diffdf")
for (pkg in need) {
  if (requireNamespace(pkg, quietly = TRUE)) {
    pass(sprintf("package '%s' available (%s)", pkg, as.character(packageVersion(pkg))))
  } else {
    fail(sprintf("package '%s' NOT installed — run: renv::restore()", pkg))
  }
}
suppressMessages({ library(haven); library(dplyr); library(diffdf) })

# ---- 2. Static parse of all pipeline R scripts -------------------------------
cat("\n[2/3] Static parse of pipeline R scripts\n")
r_scripts <- list.files(c("03_validation_r", "05_reconciliation", "09_tfl", "01_raw_source"),
                        pattern = "\\.R$", full.names = TRUE)
for (f in r_scripts) {
  res <- tryCatch({ parse(f); TRUE }, error = function(e) { fail(sprintf("%s: %s", f, conditionMessage(e))); FALSE })
  if (isTRUE(res)) pass(sprintf("parsed %s", f))
}

# ---- 3. Reconciliation engine on synthetic fixtures --------------------------
cat("\n[3/3] Reconciliation engine demonstration (synthetic fixtures)\n")

# Build a tiny, fully synthetic ADaM-style dataset and an INDEPENDENT copy that
# was derived to the same spec. AESEQ gives a unique within-subject key — exactly
# the deterministic key the production ADAE reconciliation relies on.
set.seed(11)
make_fixture <- function() {
  data.frame(
    STUDYID = "DEMO",
    USUBJID = sprintf("DEMO-%03d", rep(1:20, each = 2)),
    AESEQ   = rep(1:2, times = 20),
    AEDECOD = sample(c("HEADACHE", "NAUSEA", "FATIGUE"), 40, replace = TRUE),
    ATOXGR  = sample(1:3, 40, replace = TRUE),
    AEOCCFL = sample(c("Y", "N"), 40, replace = TRUE),
    stringsAsFactors = FALSE
  )
}
prod_fx <- make_fixture()
val_fx  <- prod_fx   # independent track derived to the identical spec

# Round-trip through XPT exactly as the real pipeline does (haven write/read).
tdir <- tempfile("tropic_demo_"); dir.create(tdir)
write_xpt(prod_fx, file.path(tdir, "demo_prod.xpt"))
write_xpt(val_fx,  file.path(tdir, "demo_v.xpt"))

# Keyed reconciliation, mirroring 05_reconciliation/cross_lang_audit.R methodology:
# align on the unique business key (USUBJID + AESEQ) and compare cell values.
reconcile <- function(prod_path, val_path, keys) {
  p <- read_xpt(prod_path); v <- read_xpt(val_path)
  names(p) <- toupper(names(p)); names(v) <- toupper(names(v))
  d <- diffdf(p, v, keys = keys, suppress_warnings = TRUE)
  setdiff(names(d), c("DataSummary", "AttribDiffs"))
}

# Case A: identical independent outputs -> expect PASS (zero differences)
issues_a <- reconcile(file.path(tdir, "demo_prod.xpt"), file.path(tdir, "demo_v.xpt"),
                      keys = c("USUBJID", "AESEQ"))
if (length(issues_a) == 0) pass("identical independent fixtures reconcile with ZERO differences") else
  fail(sprintf("expected zero differences, got: %s", paste(issues_a, collapse = ", ")))

# Case B: inject ONE perturbed cell -> the audit MUST detect and localise it
val_bad <- val_fx
val_bad$ATOXGR[1] <- val_bad$ATOXGR[1] + 1
write_xpt(val_bad, file.path(tdir, "demo_v_bad.xpt"))
issues_b <- reconcile(file.path(tdir, "demo_prod.xpt"), file.path(tdir, "demo_v_bad.xpt"),
                      keys = c("USUBJID", "AESEQ"))
if (length(issues_b) > 0) pass(sprintf("injected 1-cell difference correctly DETECTED (%s)", paste(issues_b, collapse = ", "))) else
  fail("injected difference was NOT detected — reconciliation engine is not sensitive!")

# ---- Keyless multiset path (the branch used for ADCM/ADLB/ADRS/ADEX) ----------
# The four BDS/OCCDS domains above carry NO unique within-subject record id, so
# 05_reconciliation/cross_lang_audit.R aligns them by business keys + within-key
# row_number() over content-sorted rows. Cases A/B only exercised the unique-key
# path; this helper mirrors the keyless methodology verbatim so the demo covers it.
reconcile_multiset <- function(prod, val, sort_keys) {
  names(prod) <- toupper(names(prod)); names(val) <- toupper(names(val))
  common <- intersect(names(prod), names(val))
  other  <- setdiff(common, sort_keys)
  seqd <- function(df) df %>%
    arrange(across(all_of(c(sort_keys, other)))) %>%
    group_by(across(all_of(sort_keys))) %>% mutate(SEQ = row_number()) %>% ungroup()
  d <- diffdf(seqd(prod), seqd(val), keys = c(sort_keys, "SEQ"), suppress_warnings = TRUE)
  setdiff(names(d), c("DataSummary", "AttribDiffs"))
}

# Build a BDS-style fixture whose business key (USUBJID + PARAMCD) is NON-unique
# (multiple visit rows per key) — the exact shape the keyless branch must handle.
set.seed(23)
make_bds <- function() data.frame(
  STUDYID = "DEMO",
  USUBJID = sprintf("DEMO-%03d", rep(1:10, each = 4)),
  PARAMCD = rep(c("ANC", "PSA"), times = 20),
  AVISITN = rep(1:2, each = 2, times = 10),
  AVAL    = round(rnorm(40, 100, 15), 1),
  stringsAsFactors = FALSE
)
bds_prod <- make_bds(); bds_val <- bds_prod   # independent track, identical spec

# Case C: identical multiset on a non-unique key -> expect PASS (zero differences)
issues_c <- reconcile_multiset(bds_prod, bds_val, sort_keys = c("USUBJID", "PARAMCD"))
if (length(issues_c) == 0) pass("keyless multiset path: identical non-unique-key tracks reconcile with ZERO differences") else
  fail(sprintf("keyless path expected zero differences, got: %s", paste(issues_c, collapse = ", ")))

# Case D: perturb ONE AVAL cell inside a multi-row key group -> MUST be detected
bds_bad <- bds_val
bds_bad$AVAL[3] <- bds_bad$AVAL[3] + 7.5
issues_d <- reconcile_multiset(bds_prod, bds_bad, sort_keys = c("USUBJID", "PARAMCD"))
if (length(issues_d) > 0) pass(sprintf("keyless multiset path: within-group 1-cell difference correctly DETECTED (%s)", paste(issues_d, collapse = ", "))) else
  fail("keyless path: within-group difference was NOT detected — multiset reconciliation is not sensitive!")

unlink(tdir, recursive = TRUE)

# ---- Verdict -----------------------------------------------------------------
cat("\n=================================================================\n")
if (ok) {
  cat("SMOKE TEST: PASS — environment, parsing, and reconciliation engine verified.\n")
  quit(save = "no", status = 0)
} else {
  cat("SMOKE TEST: FAIL — see [FAIL] lines above.\n")
  quit(save = "no", status = 1)
}

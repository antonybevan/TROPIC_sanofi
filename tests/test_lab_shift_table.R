# Focused regression test for T-21 laboratory shift table selection.

cat("================ TROPIC LAB SHIFT TABLE TEST ================\n")

suppressMessages({
  library(dplyr)
  library(tidyr)
})

source("05_outputs/tfl/lab_shift_table.R")

ok <- TRUE
fail <- function(msg) { cat(sprintf("  [FAIL] %s\n", msg)); ok <<- FALSE }
pass <- function(msg) cat(sprintf("  [PASS] %s\n", msg))

fixture <- tibble::tribble(
  ~USUBJID, ~PARAMCD, ~BASEFL, ~ANL01FL, ~ATOXGR, ~ADT, ~LBDY,
  "S01",   "NEUT",   "Y",     "N",      0,       as.Date("2020-01-01"), -10,
  "S01",   "NEUT",   "Y",     "Y",      1,       as.Date("2020-01-05"),  -6,
  "S01",   "NEUT",   "N",     "Y",      2,       as.Date("2020-01-20"),   9,
  "S01",   "NEUT",   "N",     "Y",      4,       as.Date("2020-02-01"),  21,
  "S02",   "NEUT",   "Y",     "N",      0,       as.Date("2020-01-02"),  -9,
  "S02",   "NEUT",   "N",     "Y",      3,       as.Date("2020-01-21"),  10,
  "S03",   "NEUT",   "Y",     "Y",      2,       as.Date("2020-01-03"),  -8
)

result <- build_lab_shift_result(fixture, "NEUT", safety_n = 3)
grade_cols <- paste0("Grade ", 0:4)
cell_total <- sum(as.matrix(result$table[, grade_cols, drop = FALSE]))

if (result$baseline_subjects == 3) pass("baseline source subjects counted once") else
  fail(sprintf("expected 3 baseline subjects, got %d", result$baseline_subjects))
if (result$worst_subjects == 2) pass("worst source subjects counted once") else
  fail(sprintf("expected 2 worst subjects, got %d", result$worst_subjects))
if (result$shift_n == 2) pass("shift denominator excludes subject without post-baseline") else
  fail(sprintf("expected shift n=2, got %d", result$shift_n))
if (cell_total == result$shift_n) pass("shift cell total equals selected denominator") else
  fail(sprintf("cell total %d != shift n %d", cell_total, result$shift_n))

row_s01 <- result$table |> filter(.data$BASE_GRADE == "Grade 1")
if (nrow(row_s01) == 1 && row_s01[["Grade 4"]] == 1) {
  pass("selected baseline prefers ANL01FL='Y' and worst grade uses max post-baseline grade")
} else {
  fail("S01 did not shift from selected Grade 1 baseline to Grade 4 worst")
}

txt <- build_lab_shift_table(fixture, "NEUT", "ANC / Neutrophils", safety_n = 3)
if (grepl("shift n=2; safety N=3", txt, fixed = TRUE)) {
  pass("rendered header separates shift denominator from safety denominator")
} else {
  fail("rendered header does not show shift and safety denominators")
}

cat("=============================================================\n")
if (ok) {
  cat("LAB SHIFT TABLE TEST: PASS\n")
  quit(save = "no", status = 0)
}
cat("LAB SHIFT TABLE TEST: FAIL\n")
quit(save = "no", status = 1)

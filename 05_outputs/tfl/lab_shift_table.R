# Laboratory shift-table helpers for T-21.
#
# The key control is one selected baseline record per subject/parameter before
# joining to one selected worst post-baseline record. Without that, duplicated
# baseline flags inflate shift-table cell counts.

select_lab_baseline <- function(lb_data, paramcd_val) {
  lb_data |>
    filter(
      .data$PARAMCD == paramcd_val,
      .data$ABLFL == "Y",
      !is.na(.data$ATOXGR)
    ) |>
    mutate(
      .row_id = row_number(),
      .selected_baseline = if_else(.data$ANL01FL == "Y", 1L, 0L, missing = 0L)
    ) |>
    group_by(.data$USUBJID) |>
    arrange(
      desc(.data$.selected_baseline),
      desc(.data$ADT),
      desc(.data$LBDY),
      desc(.data$.row_id),
      .by_group = TRUE
    ) |>
    slice(1L) |>
    ungroup() |>
    transmute(USUBJID = .data$USUBJID, BASE_GRADE = .data$ATOXGR)
}

select_lab_worst <- function(lb_data, paramcd_val) {
  lb_data |>
    filter(
      .data$PARAMCD == paramcd_val,
      is.na(.data$ABLFL),
      .data$ANL01FL == "Y",
      !is.na(.data$ATOXGR)
    ) |>
    mutate(.row_id = row_number()) |>
    group_by(.data$USUBJID) |>
    arrange(
      desc(.data$ATOXGR),
      desc(.data$ADT),
      desc(.data$LBDY),
      desc(.data$.row_id),
      .by_group = TRUE
    ) |>
    slice(1L) |>
    ungroup() |>
    transmute(USUBJID = .data$USUBJID, WORST_GRADE = .data$ATOXGR)
}

build_lab_shift_result <- function(lb_data, paramcd_val, safety_n) {
  base <- select_lab_baseline(lb_data, paramcd_val)
  worst <- select_lab_worst(lb_data, paramcd_val)

  if (anyDuplicated(base$USUBJID)) {
    stop(sprintf("baseline selection is not unique for %s", paramcd_val))
  }
  if (anyDuplicated(worst$USUBJID)) {
    stop(sprintf("worst post-baseline selection is not unique for %s", paramcd_val))
  }

  shift <- base |>
    inner_join(worst, by = "USUBJID") |>
    mutate(
      BASE_GRADE = paste0("Grade ", .data$BASE_GRADE),
      WORST_GRADE = paste0("Grade ", .data$WORST_GRADE)
    )

  shift_n <- n_distinct(shift$USUBJID)
  if (shift_n > safety_n) {
    stop(sprintf(
      "%s shift denominator %d exceeds safety denominator %d",
      paramcd_val, shift_n, safety_n
    ))
  }

  grade_levels <- paste0("Grade ", 0:4)
  tbl <- shift |>
    count(.data$BASE_GRADE, .data$WORST_GRADE, name = "n") |>
    complete(
      BASE_GRADE = grade_levels,
      WORST_GRADE = grade_levels,
      fill = list(n = 0L)
    ) |>
    pivot_wider(
      names_from = "WORST_GRADE",
      values_from = "n",
      values_fill = 0,
      names_sort = TRUE
    ) |>
    mutate(.row_total = rowSums(across(all_of(grade_levels)))) |>
    filter(.data$.row_total > 0) |>
    select(-".row_total")

  cell_total <- sum(as.matrix(tbl[, grade_levels, drop = FALSE]))
  if (cell_total != shift_n) {
    stop(sprintf(
      "%s shift cell total %d does not equal selected shift denominator %d",
      paramcd_val, cell_total, shift_n
    ))
  }

  list(
    table = tbl,
    shift_n = shift_n,
    safety_n = safety_n,
    baseline_subjects = n_distinct(base$USUBJID),
    worst_subjects = n_distinct(worst$USUBJID)
  )
}

build_lab_shift_table <- function(lb_data, paramcd_val, param_label, safety_n) {
  result <- build_lab_shift_result(lb_data, paramcd_val, safety_n)
  header <- sprintf(
    "\n  %s Baseline vs Worst Post-Baseline Grade Shift (shift n=%d; safety N=%d)\n",
    param_label, result$shift_n, safety_n
  )
  tbl_str <- paste(capture.output(print(as.data.frame(result$table))), collapse = "\n")
  paste0(header, tbl_str, "\n")
}

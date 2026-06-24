# Program: tests/test_figure_outputs.R
# Purpose: Fast, data-independent QC gate for rendered TFL figures.
# Run after 09_tfl/tfl_generation.R.  This checks the properties that commonly
# regress without producing an R error: missing files, wrong canvas size,
# transparency, and implausibly tiny/truncated output.

cat("================ TROPIC FIGURE OUTPUT QC ================\n")

if (!requireNamespace("png", quietly = TRUE)) {
  stop("Package 'png' is required for figure QC; restore the locked environment.")
}

spec <- data.frame(
  file = c(
    "F-01-1_CONSORT_Disposition.png",
    "F-11-1_KM_OS.png",
    "F-11-2_KM_PFS.png",
    "F-12-1_Subgroup_Forest.png",
    "F-13-1_PSA_Waterfall.png",
    "F-14-1_Swimmer_Plot.png",
    "F-17-1_Optimus_Scatter.png"
  ),
  width = rep(2400L, 7),
  height = c(2100L, 1650L, 1650L, 1650L, 1650L, 1650L, 1650L),
  stringsAsFactors = FALSE
)

root <- "09_tfl/output/figures"
ok <- TRUE

for (i in seq_len(nrow(spec))) {
  path <- file.path(root, spec$file[i])
  problems <- character()

  if (!file.exists(path)) {
    problems <- "missing"
  } else {
    info <- file.info(path)
    if (info$size < 50000) problems <- c(problems, "unexpectedly small (<50 KB)")

    img <- png::readPNG(path)
    actual <- dim(img)[1:2]
    if (!identical(as.integer(actual), c(spec$height[i], spec$width[i]))) {
      problems <- c(problems, sprintf(
        "canvas %dx%d; expected %dx%d",
        actual[2], actual[1], spec$width[i], spec$height[i]
      ))
    }

    # A transparent figure can turn black when embedded by a dossier viewer.
    if (length(dim(img)) == 3L && dim(img)[3] == 4L &&
        any(img[, , 4] < 1 - 1e-7)) {
      problems <- c(problems, "contains transparent pixels")
    }
  }

  if (length(problems)) {
    ok <- FALSE
    cat(sprintf("  [FAIL] %-38s %s\n", spec$file[i], paste(problems, collapse = "; ")))
  } else {
    cat(sprintf("  [PASS] %-38s %dx%d, opaque\n",
      spec$file[i], spec$width[i], spec$height[i]))
  }
}

cat("---------------- SAS PRODUCTION TRACK -------------------\n")
spec_sas <- data.frame(
  file = c(
    "F-11-1_KM_OS_SAS.png",
    "F-11-2_KM_PFS_SAS.png",
    "F-12-1_Subgroup_Forest_SAS.png",
    "F-13-1_PSA_Waterfall_SAS.png",
    "F-14-1_Swimmer_Plot_SAS.png",
    "F-17-1_Optimus_Scatter_SAS.png"
  ),
  width = rep(2400L, 6),
  height = rep(1650L, 6),
  stringsAsFactors = FALSE
)

for (i in seq_len(nrow(spec_sas))) {
  path <- file.path(root, "sas", spec_sas$file[i])
  problems <- character()
  if (!file.exists(path)) {
    problems <- "missing"
  } else {
    info <- file.info(path)
    if (info$size < 50000) problems <- c(problems, "unexpectedly small (<50 KB)")
    img <- png::readPNG(path)
    actual <- dim(img)[1:2]
    if (!identical(as.integer(actual), c(spec_sas$height[i], spec_sas$width[i]))) {
      problems <- c(problems, sprintf(
        "canvas %dx%d; expected %dx%d", actual[2], actual[1],
        spec_sas$width[i], spec_sas$height[i]
      ))
    }
    if (length(dim(img)) == 3L && dim(img)[3] == 4L &&
        any(img[, , 4] < 1 - 1e-7)) {
      problems <- c(problems, "contains transparent pixels")
    }
  }
  if (length(problems)) {
    ok <- FALSE
    cat(sprintf("  [FAIL] %-38s %s\n", spec_sas$file[i],
      paste(problems, collapse = "; ")))
  } else {
    cat(sprintf("  [PASS] %-38s %dx%d, opaque\n", spec_sas$file[i],
      spec_sas$width[i], spec_sas$height[i]))
  }
}

cat("=========================================================\n")
if (!ok) quit(save = "no", status = 1)
cat("FIGURE OUTPUT QC: PASS\n")

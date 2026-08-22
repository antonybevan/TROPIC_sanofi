# Program: tests/test_figure_outputs.R
# Purpose: Fast, data-independent QC gate for rendered TFL figures.
# Run after 05_outputs/tfl/tfl_generation.R.  This checks the properties that commonly
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

root <- "05_outputs/tfl/output/figures"
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

# Semantic source contracts. Pixel dimensions and opacity alone cannot detect a
# fabricated estimate, a hard axis limit that drops data, or colour-only arm
# encoding. Keep these high-risk figure requirements fail-closed in CI.
r_source <- paste(readLines("05_outputs/tfl/tfl_generation.R", warn = FALSE), collapse = "\n")
sas_source <- paste(
  readLines("04_analysis_datasets/programs/sas/T_tfl_generation.sas", warn = FALSE),
  collapse = "\n"
)

require_source <- function(source, needle, label) {
  if (!grepl(needle, source, fixed = TRUE)) {
    ok <<- FALSE
    cat(sprintf("  [FAIL] semantic contract: %s\n", label))
  } else {
    cat(sprintf("  [PASS] semantic contract: %s\n", label))
  }
}

require_source(r_source, "HR = NA_real_, LCL = NA_real_, UCL = NA_real_",
               "non-estimable R subgroups render as NE, never a fabricated null")
if (grepl("HR = 1.0, LCL = 1.0, UCL = 1.0", r_source, fixed = TRUE)) {
  ok <- FALSE
  cat("  [FAIL] semantic contract: fabricated HR=1.00 subgroup fallback remains\n")
}
require_source(r_source, "Intent-to-Treat Population", "forest overall row names the ITT population")
require_source(r_source, "Not in Safety Population", "population flow accounts for non-safety subjects")
require_source(r_source, "arm-specific Safety Population", "population-flow denominators are explicit")
require_source(r_source, "No treatment-by-subgroup interaction tests",
               "forest plot carries a heterogeneity interpretation guardrail")
require_source(r_source, "line_types <- c(\"CbzP\" = 1, \"MP\" = 2)",
               "R KM arms have non-colour line cues")
require_source(r_source, "scale_shape_manual", "R exposure-response points have non-colour shape cues")
require_source(r_source, "scale_linetype_manual",
               "R exposure-response curves have non-colour line cues")

if (grepl("xaxis label=\"Relative Dose Intensity (%)\" grid max=105", sas_source,
          fixed = TRUE)) {
  ok <- FALSE
  cat("  [FAIL] semantic contract: SAS exposure-response axis still clips RDI above 105\n")
} else {
  cat("  [PASS] semantic contract: SAS exposure-response x-axis is data-inclusive\n")
}
require_source(sas_source, "datasymbols=(circlefilled trianglefilled)",
               "SAS exposure-response arms have non-colour point cues")
if (grepl("scatter x=rdi y=loganc / group=trt01p markerattrs=(symbol=", sas_source,
          fixed = TRUE)) {
  ok <- FALSE
  cat("  [FAIL] semantic contract: SAS exposure-response scatter overrides group point symbols\n")
} else {
  cat("  [PASS] semantic contract: SAS exposure-response keeps group point-symbol mapping\n")
}
require_source(sas_source, "yaxistable ntext", "SAS forest companion reports subgroup N")
require_source(sas_source, "No treatment-by-subgroup interaction tests",
               "SAS forest companion carries the interpretation guardrail")
require_source(sas_source,
               "Swimmer Plot (30 Longest Exposures per Arm) - SAS Production Track",
               "SAS swimmer companion identifies its production track")

cat("=========================================================\n")
if (!ok) quit(save = "no", status = 1)
cat("FIGURE OUTPUT QC: PASS\n")

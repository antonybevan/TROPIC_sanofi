# =============================================================================
# load_spec.R -- metadata control loader for the ADaM specification.
#
# The authoritative ADaM metadata specification is
#     00_specifications/ADaM_spec.xlsx   (CDISC / Pinnacle-21 metacore format)
# Everything downstream is GOVERNED BY this spec:
#   * the R validation-track XPT export (xportr, driven from the metacore object)
#   * the variable-label artifacts for both tracks (gen_adam_labels.R)
#   * define.xml conformance (07_define_xml/check_define_conformance.R)
#   * spec<->data conformance (03_validation_r/spec_data_checks.R, metatools)
#
# This INVERTS the pre-2026-06-17 flow (define.xml -> extract workbook), which
# the portfolio audit flagged as a circular, zero-verification inversion (C-4).
# =============================================================================

suppressMessages({
  library(metacore)
})

# Resolve the spec path whether the caller runs from the project root or from a
# sub-directory (the validation scripts run from both).
tropic_spec_path <- function() {
  cands <- c(
    "00_specifications/ADaM_spec.xlsx",
    "../00_specifications/ADaM_spec.xlsx",
    file.path(Sys.getenv("TROPIC_ROOT", "."), "00_specifications", "ADaM_spec.xlsx")
  )
  hit <- Filter(file.exists, cands)
  if (!length(hit)) {
    stop(
      "ADaM_spec.xlsx not found. Looked in:\n  ",
      paste(cands, collapse = "\n  ")
    )
  }
  normalizePath(hit[[1]])
}

# Load the spec into a validated metacore object (cached per session).
.tropic_spec_cache <- new.env(parent = emptyenv())
load_tropic_spec <- function(path = tropic_spec_path(), refresh = FALSE) {
  key <- path
  if (!refresh && !is.null(.tropic_spec_cache[[key]])) {
    return(.tropic_spec_cache[[key]])
  }
  mc <- metacore::spec_to_metacore(path, verbose = "silent")
  .tropic_spec_cache[[key]] <- mc
  mc
}

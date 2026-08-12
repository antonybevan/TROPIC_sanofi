#!/usr/bin/env Rscript

repository_root <- normalizePath(".")
app_path <- file.path(repository_root, "07_reviewer_explanation", "tools",
                      "shiny", "app.R")

assert <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
}

source_app <- function(root) {
  environment <- new.env(parent = globalenv())
  previous <- Sys.getenv("TROPIC_PROJECT_ROOT", unset = NA_character_)
  on.exit({
    if (is.na(previous)) {
      Sys.unsetenv("TROPIC_PROJECT_ROOT")
    } else {
      Sys.setenv(TROPIC_PROJECT_ROOT = previous)
    }
  })
  Sys.setenv(TROPIC_PROJECT_ROOT = root)
  sys.source(app_path, envir = environment)
  environment
}

# The repository intentionally does not distribute patient data. A public clone
# must therefore start in a clearly disclosed, read-only degraded mode rather
# than crashing while constructing an empty endpoint selector.
empty_root <- tempfile("tropic-shiny-data-free-")
dir.create(file.path(empty_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(empty_root, "04_analysis_datasets", "adam"), recursive = TRUE)
dir.create(file.path(empty_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(empty_root, "renv.lock")))
on.exit(unlink(empty_root, recursive = TRUE), add = TRUE)

data_free_app <- source_app(empty_root)
assert(length(data_free_app$km_endpoints) == 0,
       "Data-free dashboard exposed endpoints")
assert(is.na(data_free_app$n_randomised),
       "Data-free dashboard exposed a randomised count")
assert(length(data_free_app$load_issues) == 8,
       "Data-free dashboard did not disclose every required local input")
assert(all(grepl("not found$", data_free_app$load_issues)),
       "Data-free dashboard emitted an unexpected input status")
assert(inherits(data_free_app$ui, "shiny.tag.list"),
       "Data-free dashboard failed to construct its UI")

# Reject plausible-looking but structurally invalid inputs before any reactive
# or chart code touches missing columns.
malformed_root <- tempfile("tropic-shiny-malformed-")
dir.create(file.path(malformed_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(malformed_root, "04_analysis_datasets", "adam"),
           recursive = TRUE)
dir.create(file.path(malformed_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(malformed_root, "renv.lock")))
writeLines("PARAMCD,HAZARDRATIO\nOS,0.71",
           file.path(malformed_root, "04_analysis_datasets", "adam",
                     "figure_km_stats_prod.csv"))
on.exit(unlink(malformed_root, recursive = TRUE), add = TRUE)

malformed_app <- source_app(malformed_root)
assert(is.null(malformed_app$km_stats),
       "Malformed hazard-ratio input was accepted")
assert(any(grepl("figure_km_stats_prod.csv: missing required column",
                 malformed_app$load_issues, fixed = TRUE)),
       "Malformed hazard-ratio input was not diagnosed")

cat("Shiny dashboard contracts: PASS\n")

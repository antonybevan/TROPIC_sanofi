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
rendered_ui <- htmltools::renderTags(data_free_app$ui)$html
assert(grepl('col-widths-sm="12,12"', rendered_ui, fixed = TRUE) &&
         grepl('col-widths-xl="7,5"', rendered_ui, fixed = TRUE),
       "Safety plot and table do not stack at constrained desktop widths")
assert(grepl("affected panels show", rendered_ui, fixed = TRUE) &&
         grepl("unavailable-data messages", rendered_ui, fixed = TRUE),
       "Data-free dashboard overstates disabled-panel behavior")
assert(grepl('<input id="soc_n" type="number"', rendered_ui, fixed = TRUE) &&
         grepl('min="5" max="20" step="1"', rendered_ui, fixed = TRUE) &&
         !grepl('id="soc_n" class="js-range-slider"', rendered_ui,
                fixed = TRUE),
       "Safety table-size control is not a bounded native number input")
assert(grepl("Kaplan-Meier controls", rendered_ui, fixed = TRUE) &&
         grepl("Safety controls", rendered_ui, fixed = TRUE),
       "Dashboard sidebars do not expose descriptive titles")

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

# Numeric/domain corruption must fail closed before ggplot or survival code is
# reached. readr otherwise accepts a mixed column as character, which would
# produce a later and less actionable rendering error.
domain_root <- tempfile("tropic-shiny-domain-")
dir.create(file.path(domain_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(domain_root, "04_analysis_datasets", "adam"), recursive = TRUE)
dir.create(file.path(domain_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(domain_root, "renv.lock")))
writeLines(
  c("PARAMCD,HAZARDRATIO,WALDLOWER,WALDUPPER", "OS,oops,0.5,0.9"),
  file.path(domain_root, "04_analysis_datasets", "adam",
            "figure_km_stats_prod.csv")
)
on.exit(unlink(domain_root, recursive = TRUE), add = TRUE)

domain_app <- source_app(domain_root)
assert(is.null(domain_app$km_stats),
       "Non-numeric hazard-ratio input was accepted")
assert(any(grepl("figure_km_stats_prod.csv: non-numeric required column",
                 domain_app$load_issues, fixed = TRUE)),
       "Non-numeric hazard-ratio input was not diagnosed")

# Reconciliation counts must remain numeric for table sorting, while median
# values preserve tokens such as NR. Invalid statuses and contradictory PASS
# records must fail closed instead of being presented as trusted evidence.
recon_root <- tempfile("tropic-shiny-reconciliation-")
dir.create(file.path(recon_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(recon_root, "04_analysis_datasets", "adam"),
           recursive = TRUE)
dir.create(file.path(recon_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(recon_root, "renv.lock")))
recon_path <- file.path(recon_root, "06_qc_evidence", "reconciliation",
                        "results_reconcile.log")
writeLines(
  c(
    "NOTE: [RESULTS-RECON] OS N(R=371/SAS=371) EVENTS(R=266/SAS=266) MEDIAN_d(R=386/SAS=386) -> PASS",
    "NOTE: [RESULTS-RECON] PFS N(R=371/SAS=371) EVENTS(R=326/SAS=326) MEDIAN_d(R=50/SAS=50) -> PASS",
    "NOTE: [RESULTS-RECON] TTPAIN N(R=371/SAS=371) EVENTS(R=37/SAS=37) MEDIAN_d(R=NR/SAS=NR) -> PASS",
    "NOTE: [RESULTS-RECON] TTPSA N(R=371/SAS=371) EVENTS(R=265/SAS=265) MEDIAN_d(R=68/SAS=68) -> PASS",
    "NOTE: [RESULTS-RECON] TTSAE N(R=371/SAS=371) EVENTS(R=78/SAS=78) MEDIAN_d(R=NR/SAS=NR) -> PASS",
    "NOTE: [RESULTS-RECON] TTUMOR N(R=371/SAS=371) EVENTS(R=96/SAS=96) MEDIAN_d(R=153/SAS=153) -> PASS"
  ),
  recon_path
)
on.exit(unlink(recon_root, recursive = TRUE), add = TRUE)

recon_app <- source_app(recon_root)
assert(is.integer(recon_app$recon$`N (R)`) &&
         is.integer(recon_app$recon$`Events (SAS)`),
       "Reconciliation count columns were not parsed as integers")
assert(identical(recon_app$recon$`Median days (R)`,
                 c("386", "50", "NR", "68", "NR", "153")),
       "Reconciliation median values did not preserve NR semantics")

writeLines(
  "NOTE: [RESULTS-RECON] OS N(R=371/SAS=371) EVENTS(R=266/SAS=266) MEDIAN_d(R=386/SAS=386) -> BANANA",
  recon_path
)
invalid_status_app <- source_app(recon_root)
assert(is.null(invalid_status_app$recon) &&
         any(grepl("contains unrecognised reconciliation status",
                   invalid_status_app$load_issues, fixed = TRUE)),
       "Unrecognised reconciliation status was accepted")

writeLines(
  "NOTE: [RESULTS-RECON] OS N(R=371/SAS=370) EVENTS(R=266/SAS=265) MEDIAN_d(R=386/SAS=385) -> PASS",
  recon_path
)
contradictory_pass_app <- source_app(recon_root)
assert(is.null(contradictory_pass_app$recon) &&
         any(grepl("inconsistent PASS record(s) OS",
                   contradictory_pass_app$load_issues, fixed = TRUE)),
       "Contradictory reconciliation PASS record was accepted")

writeLines(
  c(
    "NOTE: [RESULTS-RECON] OS N(R=371/SAS=371) EVENTS(R=266/SAS=266) MEDIAN_d(R=386/SAS=386) -> PASS",
    "NOTE: [RESULTS-RECON] PFS N(R=371/SAS=371) EVENTS(R=326/SAS=326) MEDIAN_d(R=50/SAS=50) -> PASS",
    "NOTE: [RESULTS-RECON] TTPAIN N(R=371/SAS=371) EVENTS(R=37/SAS=37) MEDIAN_d(R=NR/SAS=NR) -> PASS",
    "NOTE: [RESULTS-RECON] TTPSA N(R=371/SAS=371) EVENTS(R=265/SAS=265) MEDIAN_d(R=68/SAS=68) -> PASS",
    "NOTE: [RESULTS-RECON] TTSAE N(R=371/SAS=371) EVENTS(R=78/SAS=78) MEDIAN_d(R=NR/SAS=NR) -> PASS",
    "NOTE: [RESULTS-RECON] OS N(R=371/SAS=371) EVENTS(R=266/SAS=266) MEDIAN_d(R=386/SAS=386) -> PASS"
  ),
  recon_path
)
duplicate_endpoint_app <- source_app(recon_root)
assert(is.null(duplicate_endpoint_app$recon) &&
         any(grepl("exactly one record for each production endpoint",
                   duplicate_endpoint_app$load_issues, fixed = TRUE)),
       "Duplicate reconciliation endpoint displaced a required endpoint")

# The study display N assumes exactly one OS time-zero risk row per recognised
# treatment arm. Duplicate rows must fail closed rather than silently inflating
# this prominent count.
risk_root <- tempfile("tropic-shiny-risk-")
dir.create(file.path(risk_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(risk_root, "04_analysis_datasets", "adam"),
           recursive = TRUE)
dir.create(file.path(risk_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(risk_root, "renv.lock")))
writeLines(
  c(
    "PARAMCD,AVALM,TRT01P,NRISK",
    "OS,0,CbzP,378",
    "OS,0,CbzP,378",
    "OS,0,MP,371"
  ),
  file.path(risk_root, "04_analysis_datasets", "adam",
            "figure_km_risk_prod.csv")
)
on.exit(unlink(risk_root, recursive = TRUE), add = TRUE)

duplicate_risk_app <- source_app(risk_root)
assert(is.null(duplicate_risk_app$km_risk) &&
         is.na(duplicate_risk_app$n_randomised) &&
         any(grepl("exactly one finite OS time-zero record per treatment arm",
                   duplicate_risk_app$load_issues, fixed = TRUE)),
       "Duplicate baseline risk row silently inflated the study display N")

# Partially missing waterfall values must not change the denominator of a KPI
# described as the response rate in plotted records. Also exercise a one-arm,
# one-endpoint ADTTE input, which survfit represents without strata metadata.
partial_root <- tempfile("tropic-shiny-partial-")
dir.create(file.path(partial_root, "07_reviewer_explanation", "tools", "shiny"),
           recursive = TRUE)
dir.create(file.path(partial_root, "04_analysis_datasets", "adam"),
           recursive = TRUE)
dir.create(file.path(partial_root, "06_qc_evidence", "reconciliation"),
           recursive = TRUE)
invisible(file.create(file.path(partial_root, "renv.lock")))
writeLines(
  c(
    "TRT01P,BEST,RESPCAT",
    "CbzP,-60,PSA Response",
    "MP,NA,PSA Response",
    "MP,-20,No Response",
    ", -70,PSA Response"
  ),
  file.path(partial_root, "04_analysis_datasets", "adam",
            "figure_waterfall_prod.csv")
)
haven::write_xpt(
  data.frame(
    PARAMCD = c("ONLY", "ONLY"),
    AVAL = c(1, 2),
    AVALU = c("MONTHS", "MONTHS"),
    CNSR = c(0, 1),
    TRT01P = c("CbzP", "CbzP")
  ),
  file.path(partial_root, "04_analysis_datasets", "adam", "adtte_prod.xpt")
)
on.exit(unlink(partial_root, recursive = TRUE), add = TRUE)

partial_app <- source_app(partial_root)
assert(identical(partial_app$psa_response_rate, 50),
       "PSA response KPI included records excluded from the waterfall plot")
assert(identical(partial_app$km_endpoints, "ONLY"),
       "Single-endpoint ADTTE input did not produce one selector choice")

# Empty safety filters should return an intentional validation state. Invalid
# or absent slider input must do the same instead of leaking a dplyr error.
partial_app$adae <- data.frame(
  AEDECOD = "Headache",
  AEBODSYS = "Nervous system disorders",
  TRTEMFL = ""
)
shiny::testServer(partial_app$server, {
  session$setInputs(km_param = "ONLY", soc_n = 5)
  assert(identical(output$km_title, "Kaplan-Meier Estimate — ONLY"),
         "Single-endpoint Kaplan-Meier title did not render")
  assert(is.list(output$km_plot),
         "Single-arm Kaplan-Meier plot did not render")

  missing_teae <- tryCatch(ae_filtered(), error = identity)
  assert(inherits(missing_teae, "shiny.silent.error") &&
           grepl("Treatment-emergent filter is unavailable",
                 conditionMessage(missing_teae), fixed = TRUE),
         "Missing treatment-emergent input silently enabled all events")

  session$setInputs(teae_only = TRUE)
  assert(nrow(ae_filtered()) == 0,
         "Empty treatment-emergent filter did not produce an empty dataset")

  empty_pt <- tryCatch(output$ae_pt_plot, error = identity)
  assert(inherits(empty_pt, "shiny.silent.error") &&
           grepl("No adverse events match", conditionMessage(empty_pt),
                 fixed = TRUE),
         "Empty preferred-term filter did not return its validation message")

  session$setInputs(teae_only = FALSE)
  assert(is.list(output$ae_pt_plot),
         "All-events preferred-term plot did not recover after an empty filter")
  assert(is.character(output$ae_soc_table),
         "All-events system-organ-class table did not render")

  session$setInputs(soc_n = NULL)
  missing_soc_n <- tryCatch(output$ae_soc_table, error = identity)
  assert(inherits(missing_soc_n, "shiny.silent.error") &&
           grepl("whole number from 5 to 20", conditionMessage(missing_soc_n),
                 fixed = TRUE),
         "Missing safety table-size input leaked an internal error")

  session$setInputs(soc_n = 4.5)
  fractional_soc_n <- tryCatch(output$ae_soc_table, error = identity)
  assert(inherits(fractional_soc_n, "shiny.silent.error") &&
           grepl("whole number from 5 to 20",
                 conditionMessage(fractional_soc_n), fixed = TRUE),
         "Malformed safety table-size input leaked an internal error")
})

cat("Shiny dashboard contracts: PASS\n")

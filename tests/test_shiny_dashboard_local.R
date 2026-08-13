#!/usr/bin/env Rscript

# Local acceptance test for a data-bearing workspace. This is intentionally not
# part of data-free CI because production XPT/CSV/log files are gitignored by the
# repository's patient-data and generated-artifact policy.

environment <- new.env(parent = globalenv())
app_path <- file.path("07_reviewer_explanation", "tools", "shiny", "app.R")
sys.source(app_path, envir = environment)

assert <- function(condition, message) {
  if (!isTRUE(condition)) stop(message, call. = FALSE)
}

assert(identical(environment$PROJECT_ROOT, normalizePath(".")),
       "Dashboard did not resolve the repository root")
assert(identical(environment$n_randomised, 749),
       "Dashboard randomised count is not derived from the production risk set")
assert(identical(environment$fmt_hr(environment$os_hr), "0.71 (0.60–0.85)"),
       "Dashboard OS hazard-ratio summary drifted")
assert(identical(environment$fmt_hr(environment$pfs_hr), "0.87 (0.75–1.02)"),
       "Dashboard PFS hazard-ratio summary drifted")
assert(identical(environment$psa_response_rate, 50.3),
       "Dashboard PSA-response summary drifted")
assert(identical(environment$km_endpoints,
                 c("OS", "PFS", "TTPAIN", "TTPSA", "TTSAE", "TTUMOR")),
       "Dashboard endpoint selector does not match production ADTTE")
assert(nrow(environment$recon) == 6 && all(environment$recon$Status == "PASS"),
       "Dashboard reconciliation table must contain six passing endpoints")
assert(length(environment$load_issues) == 0,
       paste("Dashboard reported unexpected load issues:",
             paste(environment$load_issues, collapse = "; ")))

# Exercise every server output and the interactive filter boundaries without a
# browser so data/shape regressions fail before manual UI acceptance.
shiny::testServer(environment$server, {
  session$setInputs(km_param = "OS", teae_only = TRUE, soc_n = 5)
  assert(identical(output$km_title, "Kaplan-Meier Estimate — OS"),
         "Kaplan-Meier title did not react to the endpoint selector")
  assert(is.list(output$forest_plot), "Forest plot did not render")
  assert(is.list(output$km_plot), "Kaplan-Meier plot did not render")
  assert(is.list(output$waterfall_plot), "Waterfall plot did not render")
  assert(is.list(output$swimmer_plot), "Swimmer plot did not render")
  assert(is.list(output$ae_pt_plot), "Preferred-term safety plot did not render")
  assert(is.character(output$ae_soc_table), "Safety table did not render")
  assert(is.character(output$recon_table), "Reconciliation table did not render")
  plot_alts <- vapply(
    list(output$forest_plot, output$km_plot, output$waterfall_plot,
         output$swimmer_plot, output$ae_pt_plot),
    function(plot) plot$alt,
    character(1)
  )
  assert(all(nzchar(plot_alts)) && !any(plot_alts == "Plot object") &&
           length(unique(plot_alts)) == length(plot_alts),
         "Dashboard plots do not expose unique meaningful alt text")
  assert(grepl("endpoint OS", output$km_plot$alt, fixed = TRUE),
         "Kaplan-Meier alt text does not identify the selected endpoint")
  assert(grepl('Adverse events by system organ class',
               output$ae_soc_table, fixed = TRUE) &&
           grepl('"selection":{"mode":"none"',
                 output$ae_soc_table, fixed = TRUE),
         "Safety table lacks a caption or enables purposeless row selection")
  assert(grepl('SAS versus R analysis-results reconciliation for the MP arm',
               output$recon_table, fixed = TRUE) &&
           grepl('"selection":{"mode":"none"',
                 output$recon_table, fixed = TRUE),
         "Reconciliation table lacks a caption or enables row selection")
  assert(nrow(ae_filtered()) == 3921,
         "Treatment-emergent safety filter did not select the expected records")

  session$setInputs(km_param = "TTUMOR", teae_only = FALSE, soc_n = 20)
  assert(identical(output$km_title, "Kaplan-Meier Estimate — TTUMOR"),
         "Kaplan-Meier endpoint boundary did not render")
  assert(is.list(output$km_plot), "Boundary endpoint plot did not render")
  assert(grepl("endpoint TTUMOR", output$km_plot$alt, fixed = TRUE),
         "Kaplan-Meier alt text did not react to the endpoint boundary")
  assert(nrow(ae_filtered()) == 5428,
         "All-events safety filter did not select the expected records")
  assert(is.character(output$ae_soc_table),
         "Maximum-size safety table did not render")
})

cat("Local Shiny dashboard production-data contracts: PASS\n")

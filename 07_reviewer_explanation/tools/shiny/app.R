# ==============================================================================
# TROPIC Sponsor Overview Dashboard
# ------------------------------------------------------------------------------
# Purpose : Executive-level review of the TROPIC study, driven exclusively by
#           pipeline-controlled production outputs. This
#           application is a read-only presentation layer. It does not
#           regenerate, transform, or persist any analysis result and therefore
#           does not affect the validated pipeline or its audit trail.
#
# Data     : ../04_analysis_datasets/adam/  (production ADaM datasets and reconciled figure data)
# Scope    : Single-file minimum viable product (sponsor/executive overview).
#
# To run   : from the repository root, with the project renv restored:
#              R -e "shiny::runApp('07_reviewer_explanation/tools/shiny', launch.browser = TRUE)"
# ==============================================================================

library(shiny)
library(bslib)
library(readr)
library(dplyr)
library(ggplot2)
library(survival)
library(DT)

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------
find_project_root <- function(start = getwd()) {
  path <- normalizePath(start, mustWork = TRUE)
  repeat {
    if (file.exists(file.path(path, "renv.lock")) &&
          dir.exists(file.path(path, "07_reviewer_explanation"))) {
      return(path)
    }
    parent <- dirname(path)
    if (identical(parent, path)) {
      stop("Unable to locate the TROPIC project root from: ", start)
    }
    path <- parent
  }
}

project_root_from <- function(start = getwd()) {
  configured <- Sys.getenv("TROPIC_PROJECT_ROOT", unset = "")
  if (nzchar(configured)) {
    root <- normalizePath(configured, mustWork = TRUE)
    if (!file.exists(file.path(root, "renv.lock")) ||
          !dir.exists(file.path(root, "07_reviewer_explanation"))) {
      stop("TROPIC_PROJECT_ROOT is not a TROPIC repository root: ", root)
    }
    return(root)
  }
  find_project_root(start)
}

# runApp() does not guarantee that the working directory is changed to the app
# directory. Resolve all inputs from the repository root so the documented
# root-level launch command and app-directory launches behave identically.
PROJECT_ROOT <- project_root_from()
ADAM_DIR <- file.path(PROJECT_ROOT, "04_analysis_datasets", "adam")

# Consistent treatment-arm colours used across every figure.
ARM_COLOURS <- c(CbzP = "#1f4e79", MP = "#c55a11")

# ------------------------------------------------------------------------------
# Data acquisition helpers
# ------------------------------------------------------------------------------
adam_path <- function(file) file.path(ADAM_DIR, file)

load_issues <- character(0)

record_load_issue <- function(file, detail) {
  load_issues <<- c(load_issues, paste0(file, ": ", detail))
  NULL
}

validate_source_data <- function(data, file, required) {
  missing_columns <- setdiff(required, names(data))
  if (length(missing_columns) > 0) {
    return(record_load_issue(
      file,
      paste("missing required column(s)", paste(missing_columns, collapse = ", "))
    ))
  }
  if (nrow(data) == 0) {
    return(record_load_issue(file, "contains no records"))
  }
  data
}

read_figure_csv <- function(file, required) {
  path <- adam_path(file)
  if (!file.exists(path)) {
    return(record_load_issue(file, "not found"))
  }
  data <- tryCatch(
    suppressMessages(readr::read_csv(path, show_col_types = FALSE)),
    error = function(error) record_load_issue(file, conditionMessage(error))
  )
  if (is.null(data)) return(NULL)
  validate_source_data(data, file, required)
}

read_adam_xpt <- function(file, required) {
  path <- adam_path(file)
  if (!file.exists(path)) {
    return(record_load_issue(file, "not found"))
  }
  data <- tryCatch(
    haven::read_xpt(path),
    error = function(error) record_load_issue(file, conditionMessage(error))
  )
  if (is.null(data)) return(NULL)
  validate_source_data(data, file, required)
}

# Parse the SAS-versus-R analysis-results reconciliation log into a table.
# Each production endpoint is emitted as a single, machine-readable NOTE line.
read_reconciliation <- function() {
  path <- file.path(PROJECT_ROOT, "06_qc_evidence", "reconciliation",
                    "results_reconcile.log")
  file <- "results_reconcile.log"
  if (!file.exists(path)) return(record_load_issue(file, "not found"))
  lines <- tryCatch(
    readLines(path, warn = FALSE),
    error = function(error) record_load_issue(file, conditionMessage(error))
  )
  if (is.null(lines)) return(NULL)
  pattern <- paste0(
                    "\\[RESULTS-RECON\\]\\s+(\\S+)\\s+",
                    "N\\(R=(\\S+)/SAS=(\\S+)\\)\\s+",
                    "EVENTS\\(R=(\\S+)/SAS=(\\S+)\\)\\s+",
                    "MEDIAN_d\\(R=(\\S+)/SAS=(\\S+)\\)\\s+->\\s+(\\w+)")
  m <- regmatches(lines, regexec(pattern, lines))
  m <- m[vapply(m, length, integer(1)) == 9]
  if (length(m) == 0) {
    return(record_load_issue(file, "contains no parseable reconciliation records"))
  }
  d <- as.data.frame(do.call(rbind, m), stringsAsFactors = FALSE)[, -1]
  names(d) <- c("Endpoint", "N (R)", "N (SAS)", "Events (R)", "Events (SAS)",
                "Median days (R)", "Median days (SAS)", "Status")
  d
}

# Load once at start-up. The dashboard is a static view of a completed run.
km_stats <- read_figure_csv(
  "figure_km_stats_prod.csv",
  c("PARAMCD", "HAZARDRATIO", "WALDLOWER", "WALDUPPER")
)
km_risk <- read_figure_csv(
  "figure_km_risk_prod.csv",
  c("PARAMCD", "AVALM", "TRT01P", "NRISK")
)
waterfall <- read_figure_csv(
  "figure_waterfall_prod.csv",
  c("TRT01P", "BEST", "RESPCAT")
)
swimmer <- read_figure_csv(
  "figure_swimmer_prod.csv",
  c("TRT01P", "DURM", "DEATH")
)
forest_hr <- read_figure_csv(
  "forest_hr_prod.csv",
  c("SUBGROUP", "HAZARDRATIO", "WALDLOWER", "WALDUPPER")
)
adtte <- read_adam_xpt(
  "adtte_prod.xpt",
  c("PARAMCD", "AVAL", "AVALU", "CNSR", "TRT01P")
)
adae <- read_adam_xpt(
  "adae_prod.xpt",
  c("AEDECOD", "AEBODSYS", "TRTEMFL")
)
recon     <- read_reconciliation()

# ------------------------------------------------------------------------------
# Derived executive metrics
# ------------------------------------------------------------------------------
# Randomised subjects per arm are taken from the number-at-risk at time zero,
# which is the only production source that contains both treatment arms.
n_randomised <- if (!is.null(km_risk)) {
  baseline_risk <- km_risk %>%
    filter(PARAMCD == "OS", AVALM == 0, is.finite(NRISK), NRISK >= 0)
  if (nrow(baseline_risk) > 0) sum(baseline_risk$NRISK) else NA_integer_
} else {
  NA_integer_
}

hr_for <- function(paramcd) {
  if (is.null(km_stats)) return(NULL)
  km_stats %>% filter(PARAMCD == paramcd) %>% slice(1)
}
os_hr  <- hr_for("OS")
pfs_hr <- hr_for("PFS")

# This is the pooled responder fraction in the plotted waterfall records. It is
# descriptive only and is not the arm-specific SAP efficacy estimand.
psa_response_rate <- if (!is.null(waterfall)) {
  responders <- sum(grepl("PSA Response", waterfall$RESPCAT, ignore.case = TRUE))
  round(100 * responders / nrow(waterfall), 1)
} else {
  NA_real_
}

fmt_hr <- function(row) {
  if (is.null(row) || nrow(row) == 0) return("n/a")
  values <- unlist(row[1, c("HAZARDRATIO", "WALDLOWER", "WALDUPPER")],
                   use.names = FALSE)
  if (!all(is.finite(values)) || any(values <= 0)) return("n/a")
  sprintf("%.2f (%.2f–%.2f)", row$HAZARDRATIO, row$WALDLOWER, row$WALDUPPER)
}

# Endpoints available for the Kaplan-Meier panel (survival curve computed live).
km_endpoints <- if (!is.null(adtte)) {
  values <- unique(as.character(adtte$PARAMCD))
  sort(values[!is.na(values) & nzchar(trimws(values))])
} else {
  character(0)
}

# ------------------------------------------------------------------------------
# User interface
# ------------------------------------------------------------------------------
kpi_card <- function(title, value, subtitle = NULL) {
  card(
    class = "text-center",
    card_body(
      div(class = "text-muted small text-uppercase", title),
      div(class = "fs-3 fw-semibold", value),
      if (!is.null(subtitle)) div(class = "small text-muted", subtitle)
    )
  )
}

ui <- page_navbar(
  title = "TROPIC — Sponsor Overview",
  theme = bs_theme(version = 5, primary = "#1f4e79"),
  fillable = FALSE,

  nav_panel(
    "Overview",
    if (length(load_issues) > 0) {
      div(
        class = "alert alert-warning mt-3",
        role = "alert",
        tags$h4(class = "alert-heading", "Local review data are incomplete"),
        p("The dashboard is still available, but affected panels are disabled. ",
          "Generate the local production outputs before using this review aid."),
        tags$details(
          tags$summary(paste(length(load_issues), "input issue(s)")),
          tags$ul(lapply(load_issues, tags$li))
        )
      )
    },
    layout_columns(
      col_widths = c(3, 3, 3, 3),
      kpi_card("Study Display N",
               ifelse(is.na(n_randomised), "n/a",
                      format(n_randomised, big.mark = ",")),
               "real MP + reconstructed CbzP"),
      kpi_card("Overall Survival HR", fmt_hr(os_hr), "CbzP vs MP (95% CI)"),
      kpi_card("Progression-Free HR", fmt_hr(pfs_hr), "CbzP vs MP (95% CI)"),
      kpi_card("Plotted PSA Responders",
               ifelse(is.na(psa_response_rate), "n/a",
                      paste0(psa_response_rate, "%")),
               "pooled descriptive figure data")
    ),
    layout_columns(
      col_widths = c(7, 5),
      card(card_header("Hazard Ratios by Subgroup"), plotOutput("forest_plot", height = "420px")),
      card(card_header("Study Provenance"),
           card_body(
             p(strong("Source: "), "production ADaM and reconciled figure data in ",
               tags$code("04_analysis_datasets/adam/")),
             p(strong("Evidence boundary: "),
               "MP ADaM and analysis results have single-author SAS/R ",
               "implementation reconciliation; this is not organisationally ",
               "independent double programming."),
             p(strong("Treatment arms: "),
               "MP is de-identified clinical data. CbzP is reconstructed or ",
               "synthetic, depending on the display; mixed-source comparisons ",
               "are portfolio demonstrations, not clinical findings."),
             p(strong("External validation: "),
               "Pinnacle 21 Community issue-discovery was informative and ",
               "retains open findings plus a CLI compatibility caveat; no ",
               "licensed Enterprise clearance is claimed."),
             p(class = "text-muted small",
               "Read-only internal review aid; not a submission artefact. ",
               "Binding scope: docs/PRODUCT_CLAIM.md.")
           ))
    )
  ),

  nav_panel(
    "Kaplan-Meier",
    layout_sidebar(
      sidebar = sidebar(
        selectInput("km_param", "Endpoint",
                    choices = km_endpoints,
                    selected = if ("OS" %in% km_endpoints) {
                      "OS"
                    } else if (length(km_endpoints) > 0) {
                      km_endpoints[[1]]
                    } else {
                      NULL
                    }),
        helpText("Survival curve computed live from adtte_prod.xpt via",
                 tags$code("survival::survfit"), ".")
      ),
      card(card_header(textOutput("km_title")), plotOutput("km_plot", height = "480px"))
    )
  ),

  nav_panel(
    "Response",
    layout_columns(
      col_widths = c(6, 6),
      card(card_header("Best PSA Change from Baseline (Waterfall)"),
           plotOutput("waterfall_plot", height = "460px")),
      card(card_header("Time on Study by Subject (Swimmer)"),
           plotOutput("swimmer_plot", height = "460px"))
    )
  ),

  nav_panel(
    "Safety",
    layout_sidebar(
      sidebar = sidebar(
        checkboxInput("teae_only", "Treatment-emergent only", value = TRUE),
        sliderInput("soc_n", "Top system organ classes", min = 5, max = 20,
                    value = 10, step = 1),
        helpText("Adverse events from adae_prod.xpt (MP arm).")
      ),
      layout_columns(
        col_widths = c(7, 5),
        card(card_header("Most Frequent Preferred Terms"),
             plotOutput("ae_pt_plot", height = "460px")),
        card(card_header("Adverse Events by System Organ Class"),
             DT::DTOutput("ae_soc_table"))
      )
    )
  ),

  nav_panel(
    "Reconciliation",
    card(
      card_header("SAS versus R Analysis-Results Reconciliation (MP arm)"),
      card_body(
        p("Single-author implementation reconciliation: each MP production ",
          "endpoint is independently implemented in R and compared against ",
          "SAS. This is methodological, not organisational, independence. Source: ",
          tags$code("06_qc_evidence/reconciliation/results_reconcile.log"), "."),
        DT::DTOutput("recon_table")
      )
    )
  )
)

# ------------------------------------------------------------------------------
# Server
# ------------------------------------------------------------------------------
server <- function(input, output, session) {

  output$forest_plot <- renderPlot({
    validate(need(!is.null(forest_hr) && !is.null(km_stats),
                  "Forest-plot data are unavailable."))

    primary <- km_stats %>%
      transmute(SUBGROUP = paste0(PARAMCD, " (overall)"),
                HAZARDRATIO, WALDLOWER, WALDUPPER)
    dat <- bind_rows(primary, forest_hr) %>%
      filter(is.finite(HAZARDRATIO), is.finite(WALDLOWER),
             is.finite(WALDUPPER), HAZARDRATIO > 0,
             WALDLOWER > 0, WALDUPPER > 0) %>%
      mutate(SUBGROUP = factor(SUBGROUP, levels = rev(SUBGROUP)))
    validate(need(nrow(dat) > 0, "No valid hazard-ratio records are available."))

    ggplot(dat, aes(x = HAZARDRATIO, y = SUBGROUP)) +
      geom_vline(xintercept = 1, linetype = "dashed", colour = "grey50") +
      geom_errorbar(aes(xmin = WALDLOWER, xmax = WALDUPPER),
                    orientation = "y", width = 0.25, colour = "#1f4e79") +
      geom_point(size = 3, colour = "#1f4e79") +
      scale_x_log10() +
      labs(x = "Hazard ratio (log scale) — favours CbzP < 1 < favours MP",
           y = NULL) +
      theme_minimal(base_size = 13)
  })

  output$km_title <- renderText({
    req(input$km_param)
    paste0("Kaplan-Meier Estimate — ", input$km_param)
  })

  output$km_plot <- renderPlot({
    validate(need(!is.null(adtte), "adtte_prod.xpt is unavailable."))
    req(input$km_param)

    dat <- adtte %>%
      filter(PARAMCD == input$km_param) %>%
      filter(is.finite(AVAL), AVAL >= 0, is.finite(CNSR),
             CNSR %in% c(0, 1), !is.na(TRT01P), nzchar(trimws(TRT01P))) %>%
      mutate(event = as.integer(round(CNSR)) == 0)
    validate(need(nrow(dat) > 0, "No records for the selected endpoint."))
    validate(need(all(unique(dat$TRT01P) %in% names(ARM_COLOURS)),
                  "Treatment-arm values are not recognised."))

    fit <- survfit(Surv(AVAL, event) ~ TRT01P, data = dat)
    # A single treatment arm yields no strata; fall back to that arm's label.
    if (is.null(fit$strata)) {
      arm_seq <- rep(unique(as.character(dat$TRT01P))[1], length(fit$time))
    } else {
      arms <- sub("TRT01P=", "", names(fit$strata))
      arm_seq <- rep(arms, fit$strata)
    }
    sdat <- data.frame(time = fit$time, surv = fit$surv, arm = arm_seq)

    units <- unique(as.character(dat$AVALU))
    units <- units[!is.na(units) & nzchar(trimws(units))]
    unit <- if (length(units) == 1) units else "units"

    ggplot(sdat, aes(time, surv, colour = arm)) +
      geom_step(linewidth = 0.9) +
      scale_colour_manual(values = ARM_COLOURS, name = "Arm") +
      scale_y_continuous(limits = c(0, 1), labels = scales::percent) +
      labs(x = paste0("Time (", unit, ")"),
           y = "Survival probability") +
      theme_minimal(base_size = 13)
  })

  output$waterfall_plot <- renderPlot({
    validate(need(!is.null(waterfall), "Waterfall data are unavailable."))
    dat <- waterfall %>%
      filter(is.finite(BEST), !is.na(TRT01P), nzchar(trimws(TRT01P))) %>%
      arrange(desc(BEST)) %>%
      mutate(idx = row_number())
    validate(need(nrow(dat) > 0, "No valid waterfall records are available."))
    validate(need(all(unique(dat$TRT01P) %in% names(ARM_COLOURS)),
                  "Treatment-arm values are not recognised."))

    ggplot(dat, aes(idx, BEST, fill = TRT01P)) +
      geom_col() +
      geom_hline(yintercept = -50, linetype = "dashed", colour = "grey40") +
      scale_fill_manual(values = ARM_COLOURS, name = "Arm") +
      labs(x = "Subjects (ordered by response)",
           y = "Best % change in PSA from baseline") +
      theme_minimal(base_size = 13) +
      theme(axis.text.x = element_blank(), axis.ticks.x = element_blank())
  })

  output$swimmer_plot <- renderPlot({
    validate(need(!is.null(swimmer), "Swimmer data are unavailable."))
    dat <- swimmer %>%
      filter(is.finite(DURM), DURM >= 0, !is.na(TRT01P),
             nzchar(trimws(TRT01P)), DEATH %in% c(0, 1)) %>%
      arrange(TRT01P, DURM) %>%
      mutate(row = row_number())
    validate(need(nrow(dat) > 0, "No valid swimmer records are available."))
    validate(need(all(unique(dat$TRT01P) %in% names(ARM_COLOURS)),
                  "Treatment-arm values are not recognised."))

    ggplot(dat, aes(y = row)) +
      geom_segment(aes(x = 0, xend = DURM, yend = row, colour = TRT01P),
                   linewidth = 0.6) +
      geom_point(data = dplyr::filter(dat, DEATH == 1),
                 aes(x = DURM), shape = 4, size = 1.6, colour = "black") +
      scale_colour_manual(values = ARM_COLOURS, name = "Arm") +
      labs(x = "Duration on study (months)", y = "Subjects",
           caption = "× marks a death event") +
      theme_minimal(base_size = 13) +
      theme(axis.text.y = element_blank(), axis.ticks.y = element_blank())
  })

  ae_filtered <- reactive({
    validate(need(!is.null(adae), "adae_prod.xpt is unavailable."))
    d <- adae
    if (isTRUE(input$teae_only)) d <- dplyr::filter(d, TRTEMFL == "Y")
    d
  })

  output$ae_pt_plot <- renderPlot({
    dat <- ae_filtered() %>%
      filter(!is.na(AEDECOD), nzchar(trimws(AEDECOD))) %>%
      count(AEDECOD, name = "n") %>%
      arrange(desc(n)) %>%
      slice_head(n = 15) %>%
      mutate(AEDECOD = factor(AEDECOD, levels = rev(AEDECOD)))
    validate(need(nrow(dat) > 0, "No adverse events match the current filter."))

    ggplot(dat, aes(n, AEDECOD)) +
      geom_col(fill = "#1f4e79") +
      labs(x = "Number of events", y = NULL) +
      theme_minimal(base_size = 13)
  })

  output$ae_soc_table <- DT::renderDT({
    dat <- ae_filtered() %>%
      filter(!is.na(AEBODSYS), nzchar(trimws(AEBODSYS))) %>%
      count(`System Organ Class` = AEBODSYS, name = "Events") %>%
      arrange(desc(Events)) %>%
      slice_head(n = input$soc_n)
    validate(need(nrow(dat) > 0,
                  "No system-organ-class records match the current filter."))
    DT::datatable(dat, rownames = FALSE, options = list(dom = "t", pageLength = 20))
  })

  output$recon_table <- DT::renderDT({
    validate(need(!is.null(recon), "Reconciliation log is unavailable."))
    DT::datatable(recon, rownames = FALSE,
                  options = list(dom = "t", pageLength = 20)) %>%
      DT::formatStyle("Status",
                      backgroundColor = DT::styleEqual(
                        c("PASS", "FAIL"), c("#d4edda", "#f8d7da")
                      ),
                      fontWeight = "bold")
  })
}

shinyApp(ui, server)

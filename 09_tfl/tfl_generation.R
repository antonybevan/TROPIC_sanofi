# Program: tfl_generation.R | Version: 3.5.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-06-12
# Standard: ICH E3 TFL Catalogue / NEJM & Lancet Style Guides
# renv.lock hash: locked
# Description: Compiles all efficacy, safety, and Project Optimus clinical
#              reports, rendering the efficacy/safety tables and figures.

library(haven)
library(dplyr)
library(tidyr)
library(ggplot2)
library(survival)
library(patchwork)
library(scales)

# Avoid linter warnings for column names in ggplot/dplyr pipelines
surv <- NULL

# --- Deterministic output -----------------------------------------------------
# Fixed RNG seed (insurance against any randomness in layout) and a helper that
# strips non-deterministic PNG metadata (the tIME timestamp + text chunks that some
# graphics devices, e.g. ragg/Cairo, embed) so every figure is byte-reproducible
# across machines and devices. Applied to all rendered figures at the end.
set.seed(20100701L) # de Bono 2010 publication year; arbitrary but fixed

strip_png_metadata <- function(path) {
  raw <- readBin(path, "raw", n = file.info(path)$size)
  drop <- c("tIME", "tEXt", "zTXt", "iTXt")
  pieces <- list(raw[1:8]) # PNG signature
  i <- 9L
  n <- length(raw)
  repeat {
    b <- as.integer(raw[i:(i + 3)])
    len <- b[1] * 16777216 + b[2] * 65536 + b[3] * 256 + b[4] # big-endian, double-safe
    type <- rawToChar(raw[(i + 4):(i + 7)])
    end <- i + 12 + len - 1 # 4 length + 4 type + len data + 4 CRC
    if (!type %in% drop) pieces[[length(pieces) + 1L]] <- raw[i:end]
    i <- end + 1
    if (type == "IEND" || i > n) break
  }
  writeBin(unlist(pieces), path)
}

cat("NOTE: [TFL] Starting Efficacy & Safety TFL Suite compilation...\n")

dir.create("09_tfl/output/tables", showWarnings = FALSE, recursive = TRUE)
dir.create("09_tfl/output/figures", showWarnings = FALSE, recursive = TRUE)
dir.create("09_tfl/output/listings", showWarnings = FALSE, recursive = TRUE)

# Mandatory on-artifact disclosure (review-board condition CR-1): every
# comparative figure carries this caption so a detached PNG cannot be
# mistaken for a real result.
synth_cap <- paste0(
  "CbzP is a SYNTHETIC, illustrative comparator — NOT real patient data; the MP arm is real.\n",
  "Primary endpoints (OS, PFS): Guyot (2012) IPD reconstruction from the published KM curves.\n",
  "Secondary endpoints (TTPSA/TTPAIN/TTUMOR): PH-scaled from MP — circular by construction."
)
# Plain-text banner prepended to every text table output for the same reason.
synth_banner <- paste0(
  "==========================================================",
  "==================\n",
  " NOTICE: The CbzP (Cabazitaxel) arm shown below is a ",
  "SYNTHETIC, illustrative cohort.\n",
  " Primary endpoints (OS, PFS) are reconstructed via Guyot (2012) IPD ",
  "reconstruction from\n",
  " the published Kaplan-Meier curves; secondary endpoints (TTPSA/TTPAIN/TTUMOR) ",
  "are PH-scaled\n",
  " from the real MP arm and are circular by construction. ",
  "All Mitoxantrone (MP) arm\n",
  " values are derived from real trial data.\n",
  "==========================================================",
  "==================\n"
)

# Load validation datasets
adsl <- read_xpt("04_adam/adsl_v.xpt")
adex <- read_xpt("04_adam/adex_v.xpt")
adae <- read_xpt("04_adam/adae_v.xpt")
adlb <- read_xpt("04_adam/adlb_v.xpt")
adtte <- read_xpt("04_adam/adtte_v.xpt")
adrs <- read_xpt("04_adam/adrs_v.xpt")

# Dynamically load and merge reconstructed CbzP data
adsl_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adsl_cbzp.rds")
adex_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adex_cbzp.rds")
adae_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adae_cbzp.rds")
adlb_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adlb_cbzp.rds")
adtte_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adtte_cbzp.rds")
adrs_cbzp <- readRDS("01_raw_source/cbzp_reconstructed/adrs_cbzp.rds")

# Standardize date column type
adsl$DTHDT <- as.Date(adsl$DTHDT)
adsl_cbzp$DTHDT <- as.Date(adsl_cbzp$DTHDT)

adsl <- bind_rows(adsl, adsl_cbzp)
adex <- bind_rows(adex, adex_cbzp)
adae <- bind_rows(adae, adae_cbzp)
adlb <- bind_rows(adlb, adlb_cbzp)
adtte <- bind_rows(adtte, adtte_cbzp)
adrs <- bind_rows(adrs, adrs_cbzp)

# Enforce presence of both treatment arms for comparative analysis
if (length(unique(adsl$TRT01P)) < 2) {
  stop("ERROR: [TFL] Both treatment arms (MP and CbzP) must be present in the data for analysis.") # nolint
}

# ==============================================================================
# HIERARCHICAL STEP-DOWN GATEKEEPING (ICH E9 Conformance Check)
# ==============================================================================
cat("NOTE: [TFL] Verifying statistical boundaries (Hierarchical step-down gatekeeping)...\n") # nolint

# Stratified Cox / log-rank helper (SAP pre-specified). Extracted to 09_tfl/tfl_stats.R so the # nolint
# same recipe is regression-tested on a deterministic fixture (tests/test_tfl_stats.R, roadmap #8). # nolint
source("09_tfl/tfl_stats.R")

os_data <- adtte |>
  filter(PARAMCD == "OS") |>
  left_join(adsl |> select(USUBJID, ECOGBL, MEASDISF), by = "USUBJID")
os_stats <- compute_tte_stats(os_data)
os_pval <- os_stats$pval
os_significant <- os_pval < 0.05
cat(sprintf("  Step 1: OS Significance check -> p = %f (Significant: %s)\n", os_pval, # nolint
    as.character(os_significant))) # nolint

# Step 2: Progression-Free Survival (Tested only if OS is significant)
pfs_data <- adtte |>
  filter(PARAMCD == "PFS") |>
  left_join(adsl |> select(USUBJID, ECOGBL, MEASDISF), by = "USUBJID")
pfs_stats <- compute_tte_stats(pfs_data)
pfs_pval <- pfs_stats$pval
pfs_significant <- os_significant && (pfs_pval < 0.05)
cat(sprintf("  Step 2: PFS Significance check -> p = %f (Significant & Tested: %s)\n", pfs_pval, # nolint
    as.character(pfs_significant))) # nolint

# Step 3: PSA Response (Tested only if PFS is significant)
psa_resp_data <- adrs |>
  filter(PARAMCD == "PSARESP") |>
  mutate(
    TRT01P = factor(TRT01P, levels = c("MP", "CbzP")),
    AVALC = factor(AVALC, levels = c("N", "Y"))
  )
psa_table <- table(psa_resp_data$TRT01P, psa_resp_data$AVALC)
psa_test <- fisher.test(psa_table)
psa_pval <- psa_test$p.value
psa_significant <- pfs_significant && (psa_pval < 0.05)
cat(sprintf("  Step 3: PSA Response Significance check -> p = %e (Significant & Tested: %s)\n", psa_pval, # nolint
    as.character(psa_significant))) # nolint

# Step 4: ORR (Tested only if PSA Response is significant)
# Conformed to SAP measurable-disease ITT population (MEASDISF == 'Y')
orr_resp_data <- adrs |>
  filter(PARAMCD == "OBJRESP") |>
  filter(USUBJID %in% adsl$USUBJID[adsl$MEASDISF == "Y"]) |>
  mutate(
    TRT01P = factor(TRT01P, levels = c("MP", "CbzP")),
    AVALC = factor(AVALC, levels = c("N", "Y"))
  )
orr_table <- table(orr_resp_data$TRT01P, orr_resp_data$AVALC)
orr_test <- fisher.test(orr_table)
orr_pval <- orr_test$p.value
orr_significant <- psa_significant && (orr_pval < 0.05)
cat(sprintf("  Step 4: ORR Significance check -> p = %f (Significant & Tested: %s)\n", orr_pval, # nolint
    as.character(orr_significant))) # nolint

if (!os_significant) {
  cat("WARNING: [TFL] Primary endpoint (OS) did not meet statistical significance boundary. Subsequent p-values are descriptive.\n") # nolint
}

# ==============================================================================
# FIGURE THEME (NEJM/Lancet style)
# ==============================================================================
theme_nejm_custom <- function() {
  theme_minimal(base_family = "serif") +
    theme(
      # Anchor title/subtitle/caption to the whole-plot left edge (not the panel
      # edge) so they sit flush-left like the SAS ODS titles, instead of indented
      # past the y-axis labels.
      plot.title.position = "plot",
      plot.caption.position = "plot",
      plot.title = element_text(face = "bold", size = 12, color = "#111111",
        hjust = 0, margin = margin(b = 4)), # nolint
      plot.subtitle = element_text(size = 9, color = "#444444",
        hjust = 0, margin = margin(b = 12)), # nolint
      axis.title = element_text(face = "bold", size = 9.5, color = "#111111"),
      axis.text = element_text(size = 8.5, color = "#222222"),
      panel.grid.major.y = element_line(color = "#e5e7eb", linewidth = 0.3),
      panel.grid.major.x = element_blank(),
      panel.grid.minor = element_blank(),
      axis.line = element_line(linewidth = 0.5, color = "#333333"),
      axis.ticks = element_line(linewidth = 0.5, color = "#333333"),
      legend.position = "top",
      legend.justification = "left",
      legend.title = element_text(face = "bold", size = 8.5),
      legend.text = element_text(size = 8.5),
      legend.margin = margin(t = -5, b = -5),
      legend.background = element_blank(),
      legend.key = element_blank(),
      plot.caption = element_text(size = 7, color = "#A6192E", face = "bold",
        hjust = 0, margin = margin(t = 8)) # nolint
    )
}

# ==============================================================================
# KAPLAN-MEIER PLOT GENERATION HELPER (Deduplicated, fits once, vectorized risk table) # nolint
# ==============================================================================
render_km <- function(data, stats, x_max, title, subtitle_endpoint, y_lab, outfile) { # nolint
  # Fit survfit once (Issue 5)
  fit <- survfit(Surv(AVAL / 30.4375, 1 - CNSR) ~ TRT01P, data = data)

  # Extract true KM step-plot data.
  # NB: index the RAW fit arrays (fit$time/$surv) by their own strata layout via
  # rep(names, fit$strata). Do NOT use which(summary(fit)$strata==...): summary()
  # drops censoring-only rows, so its indices are shorter than fit$time and would
  # mis-map strata onto the wrong rows (scrambled curves / spurious vertical drops).
  plot_list <- list()
  if (!is.null(fit$strata)) {
    strata_of_row <- rep(names(fit$strata), fit$strata)
    for (stratum in names(fit$strata)) {
      stratum_clean <- gsub("TRT01P=", "", stratum)
      sel <- strata_of_row == stratum

      # Ensure curves start at time 0 with 100% survival
      plot_list[[stratum_clean]] <- data.frame(
        time = c(0, fit$time[sel]),
        surv = c(1.0, fit$surv[sel]),
        TRT01P = stratum_clean
      )
    }
  } else {
    single_trt <- unique(data$TRT01P)
    plot_list[[single_trt]] <- data.frame(
      time = c(0, fit$time),
      surv = c(1.0, fit$surv),
      TRT01P = single_trt
    )
  }
  plot_data <- bind_rows(plot_list)

  # Main KM Plot Panel
  km_plot <- ggplot(plot_data, aes(x = time, y = surv, color = TRT01P)) +
    geom_step(linewidth = 1.0) +
    scale_color_manual(
      values = c("CbzP" = "#005A9C", "MP" = "#A6192E"),
      labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)")
    ) +
    scale_y_continuous(labels = scales::percent, expand = c(0, 0)) +
    scale_x_continuous(breaks = seq(0, x_max, by = 3), expand = c(0, 0)) +
    coord_cartesian(xlim = c(0, x_max), ylim = c(0, 1.02)) +
    labs(
      title = title,
      subtitle = subtitle_endpoint,
      x = "Months from Randomization",
      y = y_lab,
      color = "Treatment Group:",
      caption = synth_cap
    ) +
    theme_nejm_custom() +
    theme(
      legend.position = c(0.78, 0.85),
      legend.background = element_rect(fill = "white", color = "#eaeaea", linewidth = 0.4), # nolint
      legend.key = element_blank(),
      plot.margin = margin(t = 10, r = 15, b = 5, l = 30)
    )

  # Vectorized risk table counts query (Issue 4 & 5)
  times <- seq(0, x_max, by = 3)
  sum_fit <- summary(fit, times = times, extend = TRUE)
  risk_data <- data.frame(
    TRT01P = gsub("TRT01P=", "", as.character(sum_fit$strata)),
    Time = sum_fit$time,
    n.risk = sum_fit$n.risk
  )

  active_trts <- c("CbzP", "MP")
  risk_data$TRT01P <- factor(risk_data$TRT01P, levels = active_trts)

  risk_table_plot <- ggplot(risk_data, aes(x = .data$Time, y = factor(TRT01P, levels = rev(active_trts)), label = .data$n.risk)) + # nolint
    geom_text(size = 3.2, fontface = "bold", aes(color = TRT01P), family = "serif") + # nolint
    scale_color_manual(
      values = c("CbzP" = "#005A9C", "MP" = "#A6192E"),
      labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)"),
      guide = "none"
    ) +
    scale_y_discrete(labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)")) + # nolint
    # right-side room so the final at-risk labels (e.g. month-24 "28") are not clipped
    scale_x_continuous(limits = c(0, x_max), breaks = times,
                       expand = expansion(mult = c(0.02, 0.04))) +
    labs(
      x = NULL,
      y = "Number at risk:"
    ) +
    theme_minimal(base_family = "serif") +
    theme(
      panel.grid = element_blank(),
      axis.text.x = element_blank(),
      axis.ticks = element_blank(),
      axis.title.y = element_text(face = "bold", size = 8.5, color = "#111111",
        angle = 0, vjust = 0.5), # nolint
      axis.text.y = element_text(face = "bold", size = 8.5, color = "#222222"),
      plot.margin = margin(t = -5, r = 15, b = 5, l = 30)
    )

  final_km_plot <- km_plot / risk_table_plot + plot_layout(heights = c(4.1, 1))
  ggsave(outfile, final_km_plot, width = 8, height = 5.5, dpi = 300)
}

# ==============================================================================
# FIGURE F-11-1: Kaplan-Meier Curve — OS by Arm (Primary Endpoint)
# ==============================================================================
cat("  [TFL] Rendering KM Curve: Overall Survival (with Aligned Risk Table)...\n") # nolint
os_data <- adtte |> filter(PARAMCD == "OS")

render_km(
  data = os_data,
  stats = os_stats,
  x_max = 24,
  title = "F-11-1: Kaplan-Meier Overall Survival (OS) Analysis — ITT Population", # nolint
  subtitle_endpoint = sprintf(
    "Primary Endpoint: Cabazitaxel + Prednisone (CbzP) vs Mitoxantrone + Prednisone (MP)\nHR = %.2f (95%% CI: %.2f-%.2f), Stratified Log-Rank %s", # nolint
    os_stats$hr, os_stats$lcl, os_stats$ucl,
    if (os_stats$pval < 0.0001) "p < 0.0001" else sprintf("p = %.4f", os_stats$pval) # nolint
  ),
  y_lab = "Overall Survival Probability",
  outfile = "09_tfl/output/figures/F-11-1_KM_OS.png"
)

# ==============================================================================
# FIGURE F-17-1: Exposure-Response Scatter: RDI vs ANC Nadir (Optimus)
# ==============================================================================
cat("  [TFL] Rendering Project Optimus E-R Scatter Plot...\n")
# Fetch RDI from ADEX
rdi_data <- adex |>
  filter(PARAMCD == "RDI" & AVISIT == "ALL CYCLES") |>
  select(USUBJID, RDI = AVAL, TRT01P)

# Fetch ANC Nadir from ADLB
nadir_data <- adlb |>
  filter(PARAMCD == "ANCNADIR" & AVISIT == "CYCLE 1") |>
  select(USUBJID, ANC = AVAL)

er_data <- rdi_data |>
  inner_join(nadir_data, by = "USUBJID")

# Use the dual-arm exposure-response data directly from ADaM

er_plot <- ggplot(er_data, aes(x = RDI, y = ANC, color = TRT01P)) +
  # Styled points with white fill, transparency, and clinical palette borders
  geom_point(alpha = 0.5, size = 2.0, shape = 21, stroke = 0.6, fill = "white", aes(color = TRT01P)) + # nolint
  geom_smooth(method = "loess", span = 1.0, se = TRUE, linewidth = 1.2, aes(fill = TRT01P, color = TRT01P), alpha = 0.15) + # nolint
  scale_color_manual(values = c("CbzP" = "#005A9C", "MP" = "#A6192E"),
    labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)")) + # nolint
  scale_fill_manual(values = c("CbzP" = "#005A9C", "MP" = "#A6192E"),
    labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)")) + # nolint
  labs(
    title = "F-17-1: Project Optimus Exposure-Response Analysis",
    subtitle = "Continuous ANC Nadir (Cycle 1) vs Relative Dose Intensity (RDI) by Arm\nFitted with LOWESS smoothing local regression curves", # nolint
    x = "Relative Dose Intensity (%)",
    y = "ANC Nadir Value (x10^3/uL)",
    color = "Treatment Group:",
    fill = "95% Confidence Interval:",
    caption = synth_cap
  ) +
  geom_hline(yintercept = 0.5, linetype = "dashed", color = "#e74c3c", linewidth = 0.8) + # nolint
  annotate("text", x = 43, y = 0.72, label = "Grade 4 Neutropenia Limit (< 0.5 x 10^3/uL)", # nolint
    color = "#e74c3c", # nolint
    size = 3.2, fontface = "bold", family = "serif", hjust = 0) +
  coord_cartesian(ylim = c(0, 6.0)) +
  theme_nejm_custom() +
  theme(
    panel.grid.major.x = element_line(color = "#eaeaea", linewidth = 0.3),
    plot.margin = margin(t = 10, r = 15, b = 10, l = 15)
  )

ggsave("09_tfl/output/figures/F-17-1_Optimus_Scatter.png", er_plot,
  width = 8, height = 5.5, dpi = 300) # nolint

# ==============================================================================
# FIGURE F-12-1: Statistical Subgroup Forest Plot (OS Subgroups)
# ==============================================================================
cat("  [TFL] Rendering Subgroup Forest Plot...\n")

# Filter OS data and join with ADSL covariates
os_sub_data <- adtte |>
  filter(PARAMCD == "OS") |>
  left_join(select(adsl, USUBJID, AGEGR1, ECOGBL, MEASDISF, VISCFL, PAINBL, DOCPROG), by = "USUBJID") # nolint

# Use the dual-arm subgroup data directly from ADaM

# Helper to run subgroup Cox models of CbzP vs MP
run_subgroup_cox <- function(factor_name, level_val, display_label) {
  df <- os_sub_data |>
    filter(get(factor_name) == level_val) |>
    mutate(TREAT = if_else(TRT01P == "CbzP", 1, 0))

  n_total <- nrow(df)

  if (n_total < 5) {
    data.frame(Subgroup = display_label, N = n_total, HR = 1.0, LCL = 1.0, UCL = 1.0) # nolint
  }

  fit <- coxph(Surv(AVAL, 1 - CNSR) ~ TREAT, data = df)
  s <- summary(fit)

  hr <- s$conf.int[1]
  lcl <- s$conf.int[3]
  ucl <- s$conf.int[4]

  data.frame(
    Subgroup = display_label,
    N = n_total,
    HR = hr, LCL = lcl, UCL = ucl
  )
}

# Run for pre-specified subgroup factors comparing treatment groups
overall_df <- os_sub_data |> mutate(TREAT = if_else(TRT01P == "CbzP", 1, 0))
fit_overall <- coxph(Surv(AVAL, 1 - CNSR) ~ TREAT, data = overall_df)
s_overall <- summary(fit_overall)

subgroups <- rbind(
  data.frame(
    Subgroup = "All Treated Patients",
    N = nrow(os_sub_data),
    HR = s_overall$conf.int[1],
    LCL = s_overall$conf.int[3],
    UCL = s_overall$conf.int[4]
  ),
  run_subgroup_cox("AGEGR1", "<65", "Age < 65"),
  run_subgroup_cox("AGEGR1", ">=65", "Age >= 65"),
  run_subgroup_cox("ECOGBL", 0, "ECOG Performance Status 0"),
  run_subgroup_cox("ECOGBL", 1, "ECOG Performance Status 1"),
  run_subgroup_cox("MEASDISF", "N", "Measurable Disease: No"),
  run_subgroup_cox("MEASDISF", "Y", "Measurable Disease: Yes"),
  run_subgroup_cox("VISCFL", "N", "Visceral Metastasis: No"),
  run_subgroup_cox("VISCFL", "Y", "Visceral Metastasis: Yes"),
  run_subgroup_cox("PAINBL", "N", "Baseline Pain: No"),
  run_subgroup_cox("PAINBL", "Y", "Baseline Pain: Yes"),
  run_subgroup_cox("DOCPROG", "AFTER", "Docetaxel Prog: After"),
  run_subgroup_cox("DOCPROG", "DURING", "Docetaxel Prog: During")
)

subgroups$Subgroup <- factor(subgroups$Subgroup, levels = rev(subgroups$Subgroup)) # nolint

# Setup background banding data
bg_rects <- data.frame(
  ymin = seq(1, nrow(subgroups), by = 2) - 0.5,
  ymax = seq(1, nrow(subgroups), by = 2) + 0.5
)

# Left Panel: Forest Plot Graphical curves
forest_left <- ggplot(subgroups) +
  # Alternating row bands
  geom_rect(data = bg_rects, aes(xmin = 0.1, xmax = 2.7, ymin = ymin, ymax = ymax), fill = "#f5f7f8", alpha = 0.8, # nolint
    inherit.aes = FALSE) + # nolint
  geom_vline(xintercept = 1.0, linetype = "dashed", color = "#7f8c8d", linewidth = 0.5) + # nolint
  geom_errorbar(aes(y = Subgroup, xmin = LCL, xmax = UCL), orientation = "y", width = 0.15, color = "#1a5276", linewidth = 0.8) + # nolint
  geom_point(aes(y = Subgroup, x = HR), shape = 22, size = 3.2, fill = "#1a5276", color = "#0f324a") + # Clinical square symbol # nolint
  scale_x_continuous(limits = c(0.1, 2.7), breaks = c(0.2, 0.5, 1.0, 1.5, 2.0, 2.5)) + # nolint
  labs(
    title = "F-12-1: Prognostic Subgroup Forest Plot for Overall Survival",
    subtitle = "Univariate Hazard Ratios (Cox Proportional Hazards model of CbzP (Synthetic) vs MP (Real)) and 95% Wald CIs", # nolint
    x = "Hazard Ratio (Favors CbzP (Synthetic) <-- | --> Favors MP (Real))",
    y = "",
    caption = synth_cap
  ) +
  theme_nejm_custom() +
  theme(
    axis.line.y = element_blank(),
    axis.ticks.y = element_blank(),
    axis.text.y = element_text(face = "bold", size = 8.5, color = "#333333"),
    panel.grid.major.y = element_blank(),
    plot.margin = margin(t = 10, r = 5, b = 10, l = 15)
  )

# Right Panel: Aligned Text Data Columns (Lancet Standard!)
table_right <- ggplot(subgroups, aes(y = Subgroup)) +
  geom_rect(data = bg_rects, aes(xmin = -0.5, xmax = 2.5, ymin = ymin, ymax = ymax), fill = "#f5f7f8", alpha = 0.8, # nolint
    inherit.aes = FALSE) + # nolint
  geom_text(aes(x = 0, label = N),
    size = 3, fontface = "bold", color = "#333333", family = "serif") + # nolint
  geom_text(aes(x = 1.4, label = sprintf("%.2f (95%% CI: %.2f-%.2f)", HR, LCL, UCL)), # nolint
    size = 3, fontface = "bold", color = "#333333", family = "serif") + # nolint
  # Text Headers
  annotate("text", x = 0, y = nrow(subgroups) + 0.8, label = "N",
    size = 3.2, fontface = "bold", # nolint
    color = "#111111", family = "serif") +
  annotate("text", x = 1.4, y = nrow(subgroups) + 0.8, label = "Hazard Ratio (95% CI)", # nolint
    size = 3.2, fontface = "bold", # nolint
    color = "#111111", family = "serif") +
  scale_x_continuous(limits = c(-0.5, 2.5), expand = c(0, 0)) +
  scale_y_discrete(expand = expansion(add = c(0.5, 1.2))) +
  theme_void(base_family = "serif") +
  theme(
    plot.margin = margin(t = 38, r = 15, b = 28, l = 5)
  )

# Combine Left Graphical & Right Text panels horizontally
final_forest <- forest_left + table_right + plot_layout(widths = c(3.5, 2))

ggsave("09_tfl/output/figures/F-12-1_Subgroup_Forest.png", final_forest,
  width = 8, height = 5.5, dpi = 300) # nolint

# ==============================================================================
# TABLES T-17-1 / T-17-2 / T-17-4: Text-based summary table exports
# ==============================================================================
cat("  [TFL] Compiling clinical table summaries...\n")

# Dynamic calculations for T-17-1
rdi_mp_85 <- sum(adex$TRT01P == "MP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == ">=85%") # nolint
rdi_mp_65 <- sum(adex$TRT01P == "MP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == "65-<85%") # nolint
rdi_mp_low <- sum(adex$TRT01P == "MP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == "<65%") # nolint

rdi_cbzp_85 <- sum(adex$TRT01P == "CbzP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == ">=85%") # nolint
rdi_cbzp_65 <- sum(adex$TRT01P == "CbzP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == "65-<85%") # nolint
rdi_cbzp_low <- sum(adex$TRT01P == "CbzP" & adex$PARAMCD == "RDIDL" &
    adex$AVALC == "<65%") # nolint

n_mp_rdi <- sum(adex$TRT01P == "MP" & adex$PARAMCD == "RDIDL")
n_cbzp_rdi <- sum(adex$TRT01P == "CbzP" & adex$PARAMCD == "RDIDL")

# Dynamic calculations for T-17-2
optimus_gcsf <- adlb |>
  filter(TRT01P == "CbzP" & PARAMCD == "ANCNADIR" & AVISIT == "CYCLE 1") |>
  left_join(select(adsl, USUBJID, GCSFPRFL), by = "USUBJID") |>
  mutate(GCSF_PROP = coalesce(GCSFPRFL, "N"))

n_gcsf_y <- sum(optimus_gcsf$GCSF_PROP == "Y")
n_gcsf_n <- sum(optimus_gcsf$GCSF_PROP == "N")

gcsf_y_g12 <- sum(optimus_gcsf$GCSF_PROP == "Y" & optimus_gcsf$ATOXGR <= 2)
gcsf_y_g3 <- sum(optimus_gcsf$GCSF_PROP == "Y" & optimus_gcsf$ATOXGR == 3)
gcsf_y_g4 <- sum(optimus_gcsf$GCSF_PROP == "Y" & optimus_gcsf$ATOXGR == 4)

gcsf_n_g12 <- sum(optimus_gcsf$GCSF_PROP == "N" & optimus_gcsf$ATOXGR <= 2)
gcsf_n_g3 <- sum(optimus_gcsf$GCSF_PROP == "N" & optimus_gcsf$ATOXGR == 3)
gcsf_n_g4 <- sum(optimus_gcsf$GCSF_PROP == "N" & optimus_gcsf$ATOXGR == 4)

# Dynamic calculations for T-17-4
cbzp_rdi <- adex |>
  filter(TRT01P == "CbzP" & PARAMCD == "RDIDL" & AVISIT == "ALL CYCLES") |>
  select(USUBJID, RDIDL = AVALC)

cbzp_os <- adtte |>
  filter(TRT01P == "CbzP" & PARAMCD == "OS") |>
  left_join(cbzp_rdi, by = "USUBJID")

cbzp_neut <- adlb |>
  filter(TRT01P == "CbzP" & PARAMCD == "NEUT" & BASEFL == "N" & ANL01FL == "Y") |> # nolint
  group_by(USUBJID) |>
  summarise(worst_grade = max(ATOXGR, na.rm = TRUE), .groups = "drop") |>
  left_join(cbzp_rdi, by = "USUBJID")

get_tertile_stats <- function(cat_name) {
  sub_os <- cbzp_os |> filter(.data$RDIDL == cat_name)
  fit_os <- survfit(Surv(AVAL / 30.4375, 1 - CNSR) ~ 1, data = sub_os)
  med_os <- summary(fit_os)$table["median"]

  sub_neut <- cbzp_neut |> filter(.data$RDIDL == cat_name)
  n_total <- nrow(sub_neut)
  n_g34 <- sum(sub_neut$worst_grade >= 3, na.rm = TRUE)
  rate_g34 <- if (n_total > 0) 100 * n_g34 / n_total else 0

  list(med_os = med_os, rate_g34 = rate_g34)
}

high_stats <- get_tertile_stats(">=85%")
med_stats <- get_tertile_stats("65-<85%")
low_stats <- get_tertile_stats("<65%")

table_content <- sprintf(
  "
TROPIC (Study EFC6193 / XRP6258) Clinical Reporting Tables
=============================================

T-17-1: Relative Dose Intensity (RDI) Category Distribution by Arm
------------------------------------------------------------------
Category     CbzP (N=%d)   MP (N=%d)
>=85%%        %d (%.1f%%)    %d (%.1f%%)
65-<85%%      %d (%.1f%%)     %d (%.1f%%)
<65%%         %d (%.1f%%)     %d (%.1f%%)

T-17-2: Worst Cycle ANC Nadir Grade Stratified by G-CSF Usage (CbzP)
--------------------------------------------------------------------
Group                   Grade 1/2      Grade 3        Grade 4
G-CSF Prophylaxis (N=%d) %d (%.1f%%)    %d (%.1f%%)      %d (%.1f%%)
No Prophylaxis (N=%d)  %d (%.1f%%)     %d (%.1f%%)      %d (%.1f%%)

T-17-4: Benefit-Risk Summary by RDI Tertile (CbzP Arm)
------------------------------------------------------
RDI Tertile    Median OS (Months)   Grade >=3 Neutropenia Rate (%%)
High (>=85%%)   %.1f months          %.1f%%
Med (65-<85%%)  %.1f months          %.1f%%
Low (<65%%)     %.1f months          %.1f%%
",
  n_cbzp_rdi, n_mp_rdi,
  rdi_cbzp_85, 100 * rdi_cbzp_85 / n_cbzp_rdi, rdi_mp_85, 100 * rdi_mp_85 / n_mp_rdi, # nolint
  rdi_cbzp_65, 100 * rdi_cbzp_65 / n_cbzp_rdi, rdi_mp_65, 100 * rdi_mp_65 / n_mp_rdi, # nolint
  rdi_cbzp_low, 100 * rdi_cbzp_low / n_cbzp_rdi, rdi_mp_low, 100 * rdi_mp_low / n_mp_rdi, # nolint
  n_gcsf_y, gcsf_y_g12, 100 * gcsf_y_g12 / n_gcsf_y, gcsf_y_g3, 100 * gcsf_y_g3 / n_gcsf_y, gcsf_y_g4, 100 * gcsf_y_g4 / n_gcsf_y, # nolint
  n_gcsf_n, gcsf_n_g12, 100 * gcsf_n_g12 / n_gcsf_n, gcsf_n_g3, 100 * gcsf_n_g3 / n_gcsf_n, gcsf_n_g4, 100 * gcsf_n_g4 / n_gcsf_n, # nolint
  high_stats$med_os, high_stats$rate_g34,
  med_stats$med_os, med_stats$rate_g34,
  low_stats$med_os, low_stats$rate_g34
)

writeLines(paste0(synth_banner, table_content),
  "09_tfl/output/tables/T-17-Optimus_Tables.txt") # nolint

# ==============================================================================
# TABLES T-11-6 / T-11-7: Dynamic Efficacy Summaries for Secondary Endpoints
# ==============================================================================
cat("  [TFL] Calculating dynamic KM and Cox PH statistics for TTPSA and TTUMOR...\n") # nolint

# TTPSA Analysis
psa_data <- adtte |> filter(PARAMCD == "TTPSA")
fit_psa <- survfit(Surv(AVAL / 30.4375, 1 - CNSR) ~ TRT01P, data = psa_data)
psa_data$TRT01P <- factor(psa_data$TRT01P, levels = c("MP", "CbzP"))
cox_psa <- coxph(Surv(AVAL, 1 - CNSR) ~ TRT01P, data = psa_data)

sum_fit_psa <- summary(fit_psa)$table
sum_cox_psa <- summary(cox_psa)

med_psa_cbzp <- sum_fit_psa["TRT01P=CbzP", "median"]
med_psa_mp <- sum_fit_psa["TRT01P=MP", "median"]
ci_psa_cbzp <- sprintf("(95%% CI: %.1f-%.1f)", sum_fit_psa["TRT01P=CbzP", "0.95LCL"], sum_fit_psa["TRT01P=CbzP", "0.95UCL"]) # nolint
ci_psa_mp <- sprintf("(95%% CI: %.1f-%.1f)", sum_fit_psa["TRT01P=MP", "0.95LCL"], sum_fit_psa["TRT01P=MP", "0.95UCL"]) # nolint

hr_psa <- sum_cox_psa$conf.int[1]
hr_psa_lcl <- sum_cox_psa$conf.int[3]
hr_psa_ucl <- sum_cox_psa$conf.int[4]
p_psa <- sum_cox_psa$coefficients[1, "Pr(>|z|)"]

events_psa_cbzp <- sum_fit_psa["TRT01P=CbzP", "events"]
total_psa_cbzp <- sum_fit_psa["TRT01P=CbzP", "n.max"]
events_psa_mp <- sum_fit_psa["TRT01P=MP", "events"]
total_psa_mp <- sum_fit_psa["TRT01P=MP", "n.max"]

# TTUMOR Analysis
tumor_data <- adtte |> filter(PARAMCD == "TTUMOR")
fit_tumor <- survfit(Surv(AVAL / 30.4375, 1 - CNSR) ~ TRT01P, data = tumor_data)
tumor_data$TRT01P <- factor(tumor_data$TRT01P, levels = c("MP", "CbzP"))
cox_tumor <- coxph(Surv(AVAL, 1 - CNSR) ~ TRT01P, data = tumor_data)

sum_fit_tumor <- summary(fit_tumor)$table
sum_cox_tumor <- summary(cox_tumor)

med_tumor_cbzp <- sum_fit_tumor["TRT01P=CbzP", "median"]
med_tumor_mp <- sum_fit_tumor["TRT01P=MP", "median"]
ci_tumor_cbzp <- sprintf("(95%% CI: %.1f-%.1f)", sum_fit_tumor["TRT01P=CbzP", "0.95LCL"], sum_fit_tumor["TRT01P=CbzP", "0.95UCL"]) # nolint
ci_tumor_mp <- sprintf("(95%% CI: %.1f-%.1f)", sum_fit_tumor["TRT01P=MP", "0.95LCL"], sum_fit_tumor["TRT01P=MP", "0.95UCL"]) # nolint

hr_tumor <- sum_cox_tumor$conf.int[1]
hr_tumor_lcl <- sum_cox_tumor$conf.int[3]
hr_tumor_ucl <- sum_cox_tumor$conf.int[4]
p_tumor <- sum_cox_tumor$coefficients[1, "Pr(>|z|)"]

events_tumor_cbzp <- sum_fit_tumor["TRT01P=CbzP", "events"]
total_tumor_cbzp <- sum_fit_tumor["TRT01P=CbzP", "n.max"]
events_tumor_mp <- sum_fit_tumor["TRT01P=MP", "events"]
total_tumor_mp <- sum_fit_tumor["TRT01P=MP", "n.max"]

# Best Clinical Response Endpoints Analysis (PSA response and ORR)
psa_resp_data <- adrs |> filter(PARAMCD == "PSARESP")
psa_cbzp_resp <- sum(psa_resp_data$AVALC == "Y" & psa_resp_data$TRT01P == "CbzP") # nolint
psa_cbzp_total <- sum(psa_resp_data$TRT01P == "CbzP")
psa_cbzp_pct <- psa_cbzp_resp / psa_cbzp_total * 100
psa_mp_resp <- sum(psa_resp_data$AVALC == "Y" & psa_resp_data$TRT01P == "MP")
psa_mp_total <- sum(psa_resp_data$TRT01P == "MP")
psa_mp_pct <- psa_mp_resp / psa_mp_total * 100

# Objective Response Rate (ORR) restricted to Measurable-Disease ITT population
meas_subj <- adsl |>
  filter(MEASDISF == "Y") |>
  select(USUBJID, TRT01P)
orr_resp_data <- adrs |>
  filter(PARAMCD == "OBJRESP") |>
  filter(USUBJID %in% meas_subj$USUBJID)
orr_cbzp_resp <- sum(orr_resp_data$AVALC == "Y" & orr_resp_data$TRT01P == "CbzP") # nolint
orr_cbzp_total <- sum(meas_subj$TRT01P == "CbzP")
orr_cbzp_pct <- orr_cbzp_resp / orr_cbzp_total * 100
orr_mp_resp <- sum(orr_resp_data$AVALC == "Y" & orr_resp_data$TRT01P == "MP")
orr_mp_total <- sum(meas_subj$TRT01P == "MP")
orr_mp_pct <- orr_mp_resp / orr_mp_total * 100

n_cbzp_itt <- sum(adsl$TRT01P == "CbzP")
n_mp_itt <- sum(adsl$TRT01P == "MP")

# nolint start: line_length_linter.
efficacy_tables <- sprintf(
  "
TROPIC (Study EFC6193 / XRP6258) Secondary Efficacy Tables
==========================================================

T-11-6: Kaplan-Meier Analysis of Time to PSA Progression (TTPSA) - ITT Population
---------------------------------------------------------------------------------
Statistic                                 CbzP (N=%d)        MP (N=%d)
Number of Events / Total N                %d/%d               %d/%d
Median Survival Time (Months)             %.1f                %.1f
95%% Confidence Interval                   %s      %s
Unstratified Hazard Ratio (CbzP vs MP)     %.2f (95%% CI: %.2f-%.2f)
Wald Log-Rank p-value                     %.4f


T-11-7: Kaplan-Meier Analysis of Time to Tumor Progression (TTUMOR) - Measurable Subpopulation
------------------------------------------------------------------------------------------------
Statistic                                 CbzP (N=%d)        MP (N=%d)
Number of Events / Total N                %d/%d               %d/%d
Median Survival Time (Months)             %.1f                %.1f
95%% Confidence Interval                   %s      %s
Unstratified Hazard Ratio (CbzP vs MP)     %.2f (95%% CI: %.2f-%.2f)
Wald Log-Rank p-value                     %.4f


T-11-8: Analysis of Best Clinical Response Endpoints
----------------------------------------------------
Statistic                                 CbzP                MP
PSA Response Rate (>=50%% decline) - ITT Population
  Responders / N (%%)                      %d/%d (%.1f%%)      %d/%d (%.1f%%)
  Fisher's Exact p-value                  %.4e

Objective Response Rate (ORR) - Measurable ITT Population†
  Responders / N (%%)                      %d/%d (%.1f%%)      %d/%d (%.1f%%)
  Fisher's Exact p-value                  %.4f

†Restricted to patients with measurable disease at baseline (CbzP N=%d, MP N=%d).
",
  n_cbzp_itt, n_mp_itt,
  as.integer(events_psa_cbzp), as.integer(total_psa_cbzp),
  as.integer(events_psa_mp), as.integer(total_psa_mp),
  med_psa_cbzp, med_psa_mp, ci_psa_cbzp, ci_psa_mp,
  hr_psa, hr_psa_lcl, hr_psa_ucl, p_psa,
  total_tumor_cbzp, total_tumor_mp,
  as.integer(events_tumor_cbzp), as.integer(total_tumor_cbzp),
  as.integer(events_tumor_mp), as.integer(total_tumor_mp),
  med_tumor_cbzp, med_tumor_mp, ci_tumor_cbzp, ci_tumor_mp,
  hr_tumor, hr_tumor_lcl, hr_tumor_ucl, p_tumor,
  as.integer(psa_cbzp_resp), as.integer(psa_cbzp_total), psa_cbzp_pct,
  as.integer(psa_mp_resp), as.integer(psa_mp_total), psa_mp_pct,
  psa_pval,
  as.integer(orr_cbzp_resp), as.integer(orr_cbzp_total), orr_cbzp_pct,
  as.integer(orr_mp_resp), as.integer(orr_mp_total), orr_mp_pct,
  orr_pval,
  total_tumor_cbzp, total_tumor_mp
)
# nolint end

# Objective Response Rate (ORR) with response-evaluable denominator (review-board SR-1). # nolint
# The T-11-8 block above uses the SAP measurable-disease ITT denominator.
# Report the response-evaluable denominator version here for full transparency.
orr_ev_resp_data <- adrs |> filter(PARAMCD == "OBJRESP")
orr_ev_cbzp_resp <- sum(orr_ev_resp_data$AVALC == "Y" & orr_ev_resp_data$TRT01P == "CbzP") # nolint
orr_ev_cbzp_total <- sum(orr_ev_resp_data$TRT01P == "CbzP")
orr_ev_mp_resp <- sum(orr_ev_resp_data$AVALC == "Y" & orr_ev_resp_data$TRT01P == "MP") # nolint
orr_ev_mp_total <- sum(orr_ev_resp_data$TRT01P == "MP")
orr_md_addendum <- sprintf(
  paste0(
    "\nT-11-8b: Objective Response Rate — Response-Evaluable Denominator (review-board SR-1)\n", # nolint
    "--------------------------------------------------------------------------------------\n", # nolint
    "Denominator basis        CbzP (evaluable)          MP (evaluable)\n",
    "Responders / N (%%)       %d/%d (%.1f%%)             %d/%d (%.1f%%)\n",
    "Note: T-11-8 above uses the SAP-specified measurable-disease ITT denominator. The response-\n", # nolint
    "evaluable denominator version is reported here for full traceability.\n"
  ),
  orr_ev_cbzp_resp, orr_ev_cbzp_total, 100 * orr_ev_cbzp_resp / max(orr_ev_cbzp_total, 1), # nolint
  orr_ev_mp_resp, orr_ev_mp_total,
  100 * orr_ev_mp_resp / max(orr_ev_mp_total, 1)
)
efficacy_tables <- paste0(efficacy_tables, orr_md_addendum)
cat(sprintf(
  "  [TFL] ORR (response-evaluable): MP %d/%d (%.1f%%)\n",
  orr_ev_mp_resp, orr_ev_mp_total,
  100 * orr_ev_mp_resp / max(orr_ev_mp_total, 1)
))

writeLines(paste0(synth_banner, efficacy_tables),
           "09_tfl/output/tables/T-11-Efficacy_Tables.txt")

# ==============================================================================
# FIGURE F-11-2: Kaplan-Meier Curve — PFS by Arm (Secondary Endpoint)
# ==============================================================================
cat("  [TFL] Rendering KM Curve: Progression-Free Survival...\n")
pfs_data <- adtte |> filter(PARAMCD == "PFS")

render_km(
  data = pfs_data,
  stats = pfs_stats,
  x_max = 18,
  title = paste0(
      "F-11-2: Kaplan-Meier Progression-Free Survival (PFS) Analysis ", # nolint
      "— ITT Population"
    ),
  subtitle_endpoint = sprintf(
    paste0(
      "Secondary Endpoint: Cabazitaxel + Prednisone (CbzP) vs ",
      "Mitoxantrone + Prednisone (MP)\nHR = %.2f ",
      "(95%% CI: %.2f-%.2f), Stratified Log-Rank %s"
    ),
    pfs_stats$hr, pfs_stats$lcl, pfs_stats$ucl,
    if (pfs_stats$pval < 0.0001) {
      "p < 0.0001"
    } else {
      sprintf("p = %.4f", pfs_stats$pval)
    }
  ),
  y_lab = "Progression-Free Survival Probability",
  outfile = "09_tfl/output/figures/F-11-2_KM_PFS.png"
)

# ==============================================================================
# FIGURE F-13-1: PSA Waterfall Plot — Best % Change from Baseline
# ==============================================================================
cat("  [TFL] Rendering PSA Waterfall Plot...\n")

# Best PSA % change from baseline per subject
psa_lb <- adlb |>
  filter(PARAMCD == "PSA", !is.na(PCHG)) |>
  group_by(USUBJID) |>
  summarise(best_pchg = min(PCHG, na.rm = TRUE), .groups = "drop") |>
  left_join(select(adsl, USUBJID, TRT01P), by = "USUBJID") |>
  filter(!is.na(TRT01P))

# Use the dual-arm PSA data directly from ADaM

psa_lb <- psa_lb |>
  arrange(TRT01P, best_pchg) |>
  mutate(
    subj_rank = row_number(),
    TRT_LABEL = if_else(TRT01P == "CbzP", "CbzP (Synthetic)", "MP (Real)"),
    response_color = case_when(
      best_pchg <= -50 ~ "PSA Response (>=50% decrease)",
      best_pchg < 0 ~ "PSA Decrease (<50%)",
      TRUE ~ "PSA Increase"
    )
  )

waterfall_plot <- ggplot(psa_lb, aes(
  x = subj_rank, y = best_pchg, fill = response_color
)) +
  geom_col(width = 0.85) +
  geom_hline(
    yintercept = -50, linetype = "dashed", color = "#005A9C", linewidth = 0.7
  ) +
  geom_hline(yintercept = 0, color = "#333333", linewidth = 0.4) +
  annotate("text",
    x = max(psa_lb$subj_rank) * 0.05, y = -54, label = "50% decrease threshold",
    color = "#005A9C", size = 3, fontface = "bold", hjust = 0, family = "serif"
  ) +
  scale_fill_manual(values = c(
    "PSA Response (>=50% decrease)" = "#005A9C",
    "PSA Decrease (<50%)"           = "#7fb3d3",
    "PSA Increase"                  = "#A6192E"
  )) +
  scale_y_continuous(
    labels = function(x) paste0(x, "%"),
    limits = c(-105, min(max(psa_lb$best_pchg, na.rm = TRUE) + 20, 300))
  ) +
  facet_wrap(~TRT_LABEL, scales = "free_x", ncol = 2) +
  labs(
    title = "F-13-1: PSA Best Percentage Change from Baseline — Waterfall Plot",
    subtitle = paste0(
      "Each bar represents one subject's maximum PSA decrease \n",
      "(or increase). Sorted within arm."
    ),
    x = "Subjects (ranked by PSA response within arm)",
    y = "Best PSA % Change from Baseline",
    fill = "Response Category:",
    caption = synth_cap
  ) +
  theme_nejm_custom() +
  theme(
    axis.text.x = element_blank(),
    axis.ticks.x = element_blank(),
    strip.text = element_text(face = "bold", size = 9.5),
    legend.position = "bottom"
  )

ggsave("09_tfl/output/figures/F-13-1_PSA_Waterfall.png", waterfall_plot,
       width = 9, height = 5.5, dpi = 300)

# ==============================================================================
# FIGURE F-14-1: Treatment Exposure Swimmer Plot
# ==============================================================================
cat("  [TFL] Rendering Treatment Swimmer Plot...\n")

# Build per-subject exposure duration from ADEX (cycle count) & ADSL
ncycle_all <- adex |>
  filter(PARAMCD == "NCYCLE", AVISIT == "ALL CYCLES") |>
  select(USUBJID, n_cycles = AVAL)

swimmer_data <- adsl |>
  select(USUBJID, TRT01P, TRTDURD, DTHFL, TRTSDT) |>
  left_join(ncycle_all, by = "USUBJID") |>
  mutate(
    duration_months = TRTDURD / 30.4375,
    death_event = DTHFL == "Y",
    TRT_LABEL = if_else(TRT01P == "CbzP", "CbzP (Synthetic)", "MP (Real)")
  ) |>
  arrange(TRT01P, desc(duration_months)) |>
  group_by(TRT01P) |>
  slice_head(n = 30) |> # Top 30 per arm for readability
  ungroup() |>
  mutate(subj_label = factor(row_number()))

# Round the shared x-axis up to the next 3-month tick so the longest bars and
# their death markers sit inside the panel (parity with the SAS auto-scaled
# 0-9 axis); without an explicit limit the top break is dropped and clipped.
x_max <- ceiling(max(swimmer_data$duration_months, na.rm = TRUE) / 3) * 3

swimmer_plot <- ggplot(swimmer_data, aes(
  y = subj_label, x = duration_months, fill = TRT01P
)) +
  geom_col(width = 0.85, alpha = 0.85) +
  geom_point(
    data = swimmer_data |> filter(death_event),
    aes(x = duration_months, y = subj_label), shape = 4, size = 2.5,
    color = "#111111", stroke = 1.2
  ) +
  scale_fill_manual(values = c("CbzP" = "#005A9C", "MP" = "#A6192E"),
    labels = c("CbzP" = "CbzP (Synthetic)", "MP" = "MP (Real)")) + # nolint
  scale_x_continuous(
    breaks = seq(0, x_max, by = 3),
    limits = c(0, x_max),
    expand = expansion(mult = c(0, 0.03))
  ) +
  facet_wrap(~TRT_LABEL, scales = "free_y", ncol = 2) +
  labs(
    title = paste0(
      "F-14-1: Treatment Exposure Duration \n",
      "— Swimmer Plot (Representative Sample)"
    ),
    subtitle = "Bar length = treatment duration. \nX = death event on study. Top 30 subjects per arm shown.", # nolint
    x = "Months on Treatment",
    y = "Subjects (ranked by duration)",
    fill = "Treatment Arm:",
    caption = synth_cap
  ) +
  theme_nejm_custom() +
  theme(
    axis.text.y = element_blank(),
    axis.ticks.y = element_blank(),
    strip.text = element_text(face = "bold", size = 9.5),
    legend.position = "bottom"
  )

ggsave("09_tfl/output/figures/F-14-1_Swimmer_Plot.png", swimmer_plot,
       width = 9, height = 5.5, dpi = 300)

# ==============================================================================
# TABLE T-20-1: Adverse Event Summary Table (Safety Population)
# ==============================================================================
cat("  [TFL] Compiling AE Summary Tables...\n")

# Join AE to ADSL to get treatment arm (TRTEMFL: T=treatment-emergent,
# P=pre-existing, N=not TEAE)
ae_safety <- adae |>
  select(-any_of("TRT01P")) |>
  filter(TRTEMFL == "Y") |>
  left_join(adsl |> select(USUBJID, TRT01P), by = "USUBJID")

# Safety Population denominators per arm from ADSL (SAFFL); these head the
# Safety Population AE (T-20) and lab shift (T-21) tables. ITT (TRT01P only)
# would over-count CbzP (378 ITT vs 371 safety).
n_mp <- sum(adsl$SAFFL == "Y" & adsl$TRT01P == "MP")
n_cbzp <- sum(adsl$SAFFL == "Y" & adsl$TRT01P == "CbzP")

# Precompute AE summary counts once (Issue 6 / 2.4)
ae_counts <- ae_safety |>
  group_by(TRT01P) |>
  summarise(
    any_teae = n_distinct(USUBJID),
    g3 = n_distinct(USUBJID[!is.na(ATOXGR) & ATOXGR >= 3]),
    sae = n_distinct(USUBJID[AESER == "Y"]),
    .groups = "drop"
  )

n_any_cbzp <- if ("CbzP" %in% ae_counts$TRT01P) {
  ae_counts$any_teae[ae_counts$TRT01P == "CbzP"]
} else {
  0
}
n_any_mp <- if ("MP" %in% ae_counts$TRT01P) {
  ae_counts$any_teae[ae_counts$TRT01P == "MP"]
} else {
  0
}

n_g3_cbzp_tot <- if ("CbzP" %in% ae_counts$TRT01P) {
  ae_counts$g3[ae_counts$TRT01P == "CbzP"]
} else {
  0
}
n_g3_mp_tot <- if ("MP" %in% ae_counts$TRT01P) {
  ae_counts$g3[ae_counts$TRT01P == "MP"]
} else {
  0
}

n_sae_cbzp <- if ("CbzP" %in% ae_counts$TRT01P) {
  ae_counts$sae[ae_counts$TRT01P == "CbzP"]
} else {
  0
}
n_sae_mp <- if ("MP" %in% ae_counts$TRT01P) {
  ae_counts$sae[ae_counts$TRT01P == "MP"]
} else {
  0
}

# Overall AE incidence
tot_ae <- ae_safety |>
  group_by(TRT01P) |>
  summarise(n_subj = n_distinct(USUBJID), .groups = "drop")

# Top 10 SOC by frequency (MP arm as reference)
top_soc <- ae_safety |>
  filter(!is.na(AEBODSYS)) |>
  group_by(AEBODSYS) |>
  summarise(n_mp_soc = n_distinct(USUBJID[TRT01P == "MP"]), .groups = "drop") |>
  arrange(desc(n_mp_soc)) |>
  slice_head(n = 10)

# Grade >=3 AEs by SOC
ae_g3 <- ae_safety |>
  filter(!is.na(ATOXGR) & ATOXGR >= 3) |>
  group_by(AEBODSYS) |>
  summarise(
    n_mp_g3 = n_distinct(USUBJID[TRT01P == "MP"]),
    n_cbzp_g3 = n_distinct(USUBJID[TRT01P == "CbzP"]),
    .groups = "drop"
  )

# Serious AEs
ae_ser <- ae_safety |>
  filter(AESER == "Y") |>
  group_by(AEBODSYS) |>
  summarise(
    n_mp_ser = n_distinct(USUBJID[TRT01P == "MP"]),
    n_cbzp_ser = n_distinct(USUBJID[TRT01P == "CbzP"]),
    .groups = "drop"
  )

# Derive from ae_safety (arm resolved via the ADSL join above). The real
# adae_v.xpt carries no TRT01P, so filtering raw adae would coerce every MP
# row to NA after bind_rows and silently drop all MP discontinuations.
n_disc_mp <- ae_safety |>
  filter(TRT01P == "MP" & AEACN == "DRUG WITHDRAWN") |>
  distinct(USUBJID) |>
  nrow()

n_disc_cbzp <- ae_safety |>
  filter(TRT01P == "CbzP" & AEACN == "DRUG WITHDRAWN") |>
  distinct(USUBJID) |>
  nrow()

ae_summary_txt <- sprintf(
  "
 TROPIC (Study EFC6193 / XRP6258) Adverse Event Summary Tables
 ==============================================================

 T-20-1: Treatment-Emergent Adverse Events Summary (Safety Population)
 -----------------------------------------------------------------------
                                           CbzP (N=%d)        MP (N=%d)
 Any TEAE                                  %3d (%d%%)       %3d (%d%%)
 Any Grade >= 3 TEAE                       %3d (%d%%)       %3d (%d%%)
 Any Serious TEAE (SAE)                    %3d (%d%%)       %3d (%d%%)
 Any TEAE leading to discontinuation        %d (%d%%)        %d (%d%%)

 T-20-2: Grade >=3 TEAEs by System Organ Class (Top 10, MP Arm)
 -----------------------------------------------------------------------
 System Organ Class                         CbzP (n, %%)        MP (n, %%)
",
  n_cbzp, n_mp,
  n_any_cbzp, round(100 * n_any_cbzp / n_cbzp),
  n_any_mp, round(100 * n_any_mp / n_mp),
  n_g3_cbzp_tot, round(100 * n_g3_cbzp_tot / n_cbzp),
  n_g3_mp_tot, round(100 * n_g3_mp_tot / n_mp),
  n_sae_cbzp, round(100 * n_sae_cbzp / n_cbzp),
  n_sae_mp, round(100 * n_sae_mp / n_mp),
  n_disc_cbzp, round(100 * n_disc_cbzp / n_cbzp),
  n_disc_mp, round(100 * n_disc_mp / n_mp)
)

for (i in seq_len(nrow(top_soc))) {
  soc <- top_soc$AEBODSYS[i]
  n_g3_mp <- if (soc %in% ae_g3$AEBODSYS) {
    ae_g3$n_mp_g3[ae_g3$AEBODSYS == soc]
  } else {
    0
  }
  n_g3_cbzp <- if (soc %in% ae_g3$AEBODSYS) {
    ae_g3$n_cbzp_g3[ae_g3$AEBODSYS == soc]
  } else {
    0
  }
  ae_summary_txt <- paste0(
    ae_summary_txt,
    sprintf(
      "  %-50s  %3d (%d%%)       %3d (%d%%)\n",
      substr(soc, 1, 50),
      n_g3_cbzp, round(100 * n_g3_cbzp / n_cbzp),
      n_g3_mp, round(100 * n_g3_mp / n_mp)
    )
  )
}

ae_summary_txt <- paste0(
  ae_summary_txt,
  "\n",
  " Note: The synthetic CbzP adverse-event dictionary is limited to the\n",
  " principal cabazitaxel preferred terms. System Organ Classes outside that\n",
  " set (skin, metabolism, respiratory, investigations) therefore report 0%\n",
  " for the CbzP arm. All MP arm values are derived from real trial data.\n"
)

writeLines(paste0(synth_banner, ae_summary_txt),
           "09_tfl/output/tables/T-20-AE_Summary_Tables.txt")

# ==============================================================================
# TABLE T-21-1: Lab Shift Table — ANC/PSA Baseline to Worst
# ==============================================================================
cat("  [TFL] Compiling Lab Shift Tables...\n")

build_shift_table <- function(lb_data, paramcd_val, param_label, n_total) {
  # Baseline values
  base <- lb_data |>
    filter(
      .data$PARAMCD == paramcd_val,
      .data$BASEFL == "Y",
      !is.na(.data$ATOXGR)
    ) |>
    select("USUBJID", BASE_GRADE = "ATOXGR")

  # Worst post-baseline
  worst <- lb_data |>
    filter(
      .data$PARAMCD == paramcd_val,
      .data$BASEFL == "N",
      .data$ANL01FL == "Y",
      !is.na(.data$ATOXGR)
    ) |>
    group_by(.data$USUBJID) |>
    slice_max(.data$ATOXGR, n = 1, with_ties = FALSE) |>
    ungroup() |>
    select("USUBJID", WORST_GRADE = "ATOXGR")

  shift <- base |>
    inner_join(worst, by = "USUBJID") |>
    mutate(
      BASE_GRADE  = paste0("Grade ", .data$BASE_GRADE),
      WORST_GRADE = paste0("Grade ", .data$WORST_GRADE)
    )

  tbl <- shift |>
    count(.data$BASE_GRADE, .data$WORST_GRADE) |>
    pivot_wider(
      names_from = "WORST_GRADE",
      values_from = "n",
      values_fill = 0,
      names_sort = TRUE
    )

  header <- sprintf(
    "\n  %s Baseline vs Worst Post-Baseline Grade Shift (n=%d)\n",
    param_label, n_total
  )
  tbl_str <- paste(capture.output(print(as.data.frame(tbl))), collapse = "\n")
  paste0(header, tbl_str, "\n")
}

# Restrict to Safety Population so the shift counts match the SAFFL
# denominators (n_mp / n_cbzp); the 7 non-safety CbzP subjects carry ADLB rows.
saf_ids <- adsl$USUBJID[adsl$SAFFL == "Y"]
adlb_mp <- adlb |> filter(TRT01P == "MP", USUBJID %in% saf_ids)
adlb_cbzp <- adlb |> filter(TRT01P == "CbzP", USUBJID %in% saf_ids)

shift_output <- paste0(
  "\n TROPIC (Study EFC6193 / XRP6258) Laboratory Toxicity Shift Tables\n",
  " =================================================================\n",
  " T-21-1: Baseline to Worst Post-Baseline CTCAE Grade Shift (MP Arm)\n\n",
  build_shift_table(adlb_mp, "NEUT", "ANC / Neutrophils", n_mp),
  build_shift_table(adlb_mp, "HGB", "Haemoglobin", n_mp),
  build_shift_table(adlb_mp, "PLAT", "Platelets", n_mp),
  "\n -----------------------------------------------------------------\n",
  " T-21-2: Baseline to Worst Post-Baseline CTCAE Grade Shift (CbzP Arm)\n\n",
  build_shift_table(adlb_cbzp, "NEUT", "ANC / Neutrophils", n_cbzp),
  build_shift_table(adlb_cbzp, "HGB", "Haemoglobin", n_cbzp),
  build_shift_table(adlb_cbzp, "PLAT", "Platelets", n_cbzp)
)

writeLines(paste0(synth_banner, shift_output),
           "09_tfl/output/tables/T-21-Lab_Shift_Tables.txt")

# ==============================================================================
# FIGURE F-01-1: CONSORT Patient Disposition Flow Diagram
# ==============================================================================
cat("  [TFL] Rendering CONSORT Patient Disposition Diagram...\n")

# Derive disposition numbers from ADSL. The diagram is the Safety Population,
# so disposition counts and percentages are within SAFFL == "Y" (742), which
# is smaller than the ITT set (749); the two are not interchangeable.
n_total <- nrow(adsl)
n_itt <- nrow(adsl |> filter(ITTFL == "Y"))
saf <- adsl |> filter(SAFFL == "Y")
n_safety <- nrow(saf)
n_deaths <- nrow(saf |> filter(DTHFL == "Y"))
n_completed <- nrow(saf |> filter(TRTDURD >= 60))
n_disc <- n_safety - n_completed

# Build diagram as a ggplot canvas with annotated boxes and arrows
consort <- ggplot() +
  # ---- Box coordinates (x_center, y_center, width, height) ----
  # Screened
  annotate("rect",
    xmin = 0.3, xmax = 0.7, ymin = 0.88, ymax = 0.98,
    fill = "#dbeafe", color = "#1d4ed8", linewidth = 0.6
  ) +
  annotate("text",
    x = 0.5, y = 0.93,
    label = sprintf("Patients enrolled\nN = %d", n_total),
    size = 3.2, fontface = "bold", color = "#1e3a5f", family = "serif"
  ) +
  # Arrow down
  annotate("segment",
    x = 0.5, xend = 0.5, y = 0.88, yend = 0.79,
    arrow = arrow(length = unit(0.025, "npc")),
    color = "#333333", linewidth = 0.5
  ) +
  annotate("rect",
    xmin = 0.3, xmax = 0.7, ymin = 0.68, ymax = 0.79,
    fill = "#d1fae5", color = "#065f46", linewidth = 0.6
  ) +
  annotate("text",
    x = 0.5, y = 0.735,
    label = sprintf(
      "ITT Population: N = %d\nSafety Population: N = %d (100%%)",
      n_itt, n_safety
    ),
    size = 3.2, fontface = "bold", color = "#065f46", family = "serif"
  ) +
  # Arrow down to branches
  annotate("segment",
    x = 0.5, xend = 0.5, y = 0.68, yend = 0.63,
    arrow = arrow(length = unit(0.025, "npc")),
    color = "#333333", linewidth = 0.5
  ) +
  # Branch left: Completed
  annotate("segment", x = 0.5, xend = 0.25, y = 0.63, yend = 0.63,
           color = "#333333", linewidth = 0.5) +
  annotate("segment",
    x = 0.25, xend = 0.25, y = 0.63, yend = 0.575,
    arrow = arrow(length = unit(0.025, "npc")),
    color = "#333333", linewidth = 0.5
  ) +
  annotate("rect",
    xmin = 0.05, xmax = 0.45, ymin = 0.49, ymax = 0.575,
    fill = "#f0fdf4", color = "#15803d", linewidth = 0.6
  ) +
  annotate("text",
    x = 0.25, y = 0.532,
    label = sprintf(
      "Completed >=60 days\nn = %d (%d%%)", n_completed,
      round(100 * n_completed / n_safety)
    ),
    size = 3, color = "#15803d", family = "serif"
  ) +
  # Branch right: Discontinued
  annotate("segment", x = 0.5, xend = 0.75, y = 0.63, yend = 0.63,
           color = "#333333", linewidth = 0.5) +
  annotate("segment",
    x = 0.75, xend = 0.75, y = 0.63, yend = 0.575,
    arrow = arrow(length = unit(0.025, "npc")),
    color = "#333333", linewidth = 0.5
  ) +
  annotate("rect",
    xmin = 0.55, xmax = 0.95, ymin = 0.49, ymax = 0.575,
    fill = "#fef2f2", color = "#b91c1c", linewidth = 0.6
  ) +
  annotate("text",
    x = 0.75, y = 0.532,
    label = sprintf(
      "Discontinued early\nn = %d (%d%%)", n_disc,
      round(100 * n_disc / n_safety)
    ),
    size = 3, color = "#b91c1c", family = "serif"
  ) +
  # Deaths merge from BOTH branches: deaths occur among completers and
  # discontinuers alike, so the box is not subordinate to either branch.
  annotate("segment", x = 0.25, xend = 0.25, y = 0.49, yend = 0.45,
           color = "#333333", linewidth = 0.5) +
  annotate("segment", x = 0.75, xend = 0.75, y = 0.49, yend = 0.45,
           color = "#333333", linewidth = 0.5) +
  annotate("segment", x = 0.25, xend = 0.75, y = 0.45, yend = 0.45,
           color = "#333333", linewidth = 0.5) +
  annotate("segment",
    x = 0.5, xend = 0.5, y = 0.45, yend = 0.415,
    arrow = arrow(length = unit(0.025, "npc")),
    color = "#333333", linewidth = 0.5
  ) +
  annotate("rect",
    xmin = 0.3, xmax = 0.7, ymin = 0.33, ymax = 0.415,
    fill = "#fef9c3", color = "#854d0e", linewidth = 0.6
  ) +
  annotate("text",
    x = 0.5, y = 0.372,
    label = sprintf(
      "Deaths during study\nN = %d (%d%%)", n_deaths,
      round(100 * n_deaths / n_safety)
    ),
    size = 3.2, fontface = "bold", color = "#854d0e", family = "serif"
  ) +
  # Title
  annotate("text",
    x = 0.5, y = 1.02,
    label = paste0(
      "F-01-1: CONSORT Patient Disposition Flow Diagram \n",
      "— Safety Population"
    ),
    size = 4, fontface = "bold", color = "#111111", family = "serif"
  ) +
  annotate("text",
    x = 0.5, y = 0.24,
    label = paste0(
      "Source: ADSL (N=", n_total, "). \n",
      "All percentages are relative to Safety Population.\n",
      paste0(
        "SYNTHETIC illustrative Cabazitaxel (CbzP) arm integrated ",
        "alongside the REAL Mitoxantrone (MP) arm; \n",
        "CbzP is not real data."
      )
    ),
    size = 2.8, color = "#555555", family = "serif"
  ) +
  coord_cartesian(xlim = c(0, 1), ylim = c(0.20, 1.05)) +
  theme_void(base_family = "serif") +
  theme(plot.margin = margin(10, 20, 10, 20))

ggsave("09_tfl/output/figures/F-01-1_CONSORT_Disposition.png", consort,
       width = 8, height = 7, dpi = 300)

# Byte-stability pass: strip embedded timestamps/text from the R-track figures so the
# committed PNGs are identical across rebuilds and graphics devices (the SAS-track
# figures under figures/sas/ are rendered separately and are not touched here).
invisible(lapply(
  list.files("09_tfl/output/figures", pattern = "[.]png$", full.names = TRUE),
  strip_png_metadata
))

cat(
  "NOTE: [TFL] TFL suites compiled successfully.\n",
  "Figures & tables saved to 09_tfl/output/figures/ & tables/\n",
  sep = ""
)

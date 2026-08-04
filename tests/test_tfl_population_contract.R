# Program: tests/test_tfl_population_contract.R
# Purpose: Regression gate for SAP v4.0 PSA eligibility, demonstration-population
#          naming, and the ECOG 0-1 versus 2 subgroup contract.

suppressPackageStartupMessages({
  library(haven)
  library(dplyr)
})

# The contract is exercised against the validation ADaM XPTs on a data-bearing
# run.  CI intentionally checks out the data-free portfolio surface, so make
# that boundary explicit instead of failing on an expected absent input.
validation_inputs <- c(
  "04_analysis_datasets/adam/adsl_v.xpt",
  "04_analysis_datasets/adam/adrs_v.xpt",
  "01_source_data/cbzp_reconstructed/adsl_cbzp.rds",
  "01_source_data/cbzp_reconstructed/adrs_cbzp.rds"
)
missing_inputs <- validation_inputs[!file.exists(validation_inputs)]
if (length(missing_inputs)) {
  cat(
    "TFL population contract: SKIP (data-free checkout; missing ",
    paste(missing_inputs, collapse = ", "),
    ")\n",
    sep = ""
  )
  quit(save = "no", status = 0)
}

adsl <- bind_rows(
  read_xpt("04_analysis_datasets/adam/adsl_v.xpt"),
  readRDS("01_source_data/cbzp_reconstructed/adsl_cbzp.rds")
)
adrs <- bind_rows(
  read_xpt("04_analysis_datasets/adam/adrs_v.xpt"),
  readRDS("01_source_data/cbzp_reconstructed/adrs_cbzp.rds")
)

psa <- adrs |>
  filter(PARAMCD == "PSARESP") |>
  inner_join(select(adsl, USUBJID, PSABL, any_of("PSABLIF")), by = "USUBJID") |>
  filter(coalesce(PSABLIF, "N") != "Y", !is.na(PSABL), PSABL >= 20)
stopifnot(nrow(psa) == 690L)
stopifnot(all((psa |> count(TRT01P) |> arrange(TRT01P))$n == c(361L, 329L)))
stopifnot(all((psa |> count(TRT01P, AVALC) |> filter(AVALC == "Y") |> arrange(TRT01P))$n == c(145L, 61L)))

eco <- adsl |>
  mutate(ECOGBLGRP = case_when(ECOGBL <= 1 ~ "0-1", ECOGBL == 2 ~ "2", TRUE ~ NA_character_)) |>
  count(ECOGBLGRP) |>
  arrange(ECOGBLGRP)
stopifnot(identical(eco$ECOGBLGRP, c("0-1", "2")))
stopifnot(identical(eco$n, c(691L, 58L)))

tfl_text <- paste(readLines("05_outputs/tfl/output/tables/T-11-Efficacy_Tables.txt", warn = FALSE), collapse = "\n")
stopifnot(grepl("T-11-6: Time to Tumou?r Progression \\(TTUMOR; ITT primary\\)", tfl_text))
stopifnot(grepl("T-11-7:.*PSA Progression", tfl_text))
stopifnot(grepl("145/361", tfl_text), grepl("61/329", tfl_text))
stopifnot(!grepl("148/378|69/371", tfl_text))

cat("TFL population contract: PASS (PSA baseline eligibility, ECOG pooling, and output labels)\n")

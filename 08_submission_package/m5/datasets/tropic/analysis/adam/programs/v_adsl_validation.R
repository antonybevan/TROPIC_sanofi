# Program: v_adsl_validation.R | Version: 4.0.0
# Author: Antony Bevan, Clinical Programming | Date: 2026-08-09
# Standard: ADaMIG v1.3 | renv.lock hash: locked
# Description: R Independent Validation double-programming for TROPIC ADSL.
#
# ADaM entry criteria: TRT01P is planned treatment from DM; TRT01A is actual
# administered IV antineoplastic from EX. ADSL n must equal DM n.

library(dplyr)
library(haven)
library(lubridate)
library(tidyr)
library(xportr)

# Avoid linter warnings for column names in ggplot/dplyr pipelines
.env <- NULL
source("04_analysis_datasets/programs/r/config_study.R")

cat("NOTE: [VALIDATION] Starting ADSL Validation script...\n")

# Load real staging tables
dm <- readRDS(stage_file("dm"))
ex <- readRDS(stage_file("ex"))
ds <- readRDS(stage_file("ds"))
vs <- readRDS(stage_file("vs"))
lb <- readRDS(stage_file("lb"))
ls <- readRDS(stage_file("ls"))
pn <- readRDS(stage_file("pn"))
cm <- readRDS(stage_file("cm"))
sv <- readRDS(stage_file("sv"))
ae <- readRDS(stage_file("ae"))

date10 <- function(x) {
  value <- substring(as.character(x), 1, 10)
  ymd(
    if_else(
      grepl("^\\d{4}-\\d{2}-\\d{2}$", value),
      value,
      NA_character_
    ),
    quiet = TRUE
  )
}

# Exposure dates. Planned treatment is never taken from EXTRT; actual treatment
# is independently classified from qualifying administered IV exposure below.
df_ex <- ex |>
  filter(!is.na(EXSTDTC)) |>
  mutate(
    exstdt = ymd(if_else(
      !is.na(EXSTDTC) & nchar(EXSTDTC) >= 10,
      substring(EXSTDTC, 1, 10),
      NA_character_
    )),
    exendt = ymd(if_else(
      !is.na(EXENDTC) & nchar(EXENDTC) >= 10,
      substring(EXENDTC, 1, 10),
      NA_character_
    ))
  ) |>
  group_by(USUBJID) |>
  summarise(
    TRTSDT = min(exstdt, na.rm = TRUE),
    TRTEDT = max(exendt, na.rm = TRUE),
    TRTDURD = as.numeric(TRTEDT - TRTSDT + 1),
    .groups = "drop"
  )

# Derive actual treatment independently from administered IV drug. This keeps
# the single observed planned/actual discrepancy visible in analysis data.
df_actual_trt <- ex |>
  group_by(USUBJID) |>
  summarise(
    has_cbzp = any(grepl("XRP|CABAZ", coalesce(EXTRT, ""),
                         ignore.case = TRUE)),
    has_mp = any(grepl("MITOX", coalesce(EXTRT, ""), ignore.case = TRUE)),
    .groups = "drop"
  )

# Calculate approximate death dates from DS week precision.
df_death_approx <- ds |>
  filter(DSDECOD %in% c("DEATH", "DEAD")) |>
  left_join(select(dm, USUBJID, RFSTDTC), by = "USUBJID") |>
  mutate(
    dth_dt = date10(RFSTDTC) + (as.numeric(DSSTWK) - 1) * 7
  ) |>
  filter(!is.na(dth_dt)) |>
  arrange(USUBJID, dth_dt, DSSEQ) |>
  group_by(USUBJID) |>
  summarise(
    approx_dthdt = first(dth_dt),
    DTHCAUS = first(DSTERM),
    .groups = "drop"
  )

# Prefer complete source-reported dates from SUPPAE over DS point estimates.
df_death_exact <- ae |>
  filter(!is.na(AEDTHDTC), nchar(AEDTHDTC) >= 10) |>
  transmute(USUBJID, exact_dthdt = date10(AEDTHDTC)) |>
  filter(!is.na(exact_dthdt)) |>
  group_by(USUBJID) |>
  summarise(exact_dthdt = min(exact_dthdt), .groups = "drop")

df_death <- full_join(df_death_approx, df_death_exact, by = "USUBJID") |>
  mutate(DTHFL = "Y", DTHDT = coalesce(exact_dthdt, approx_dthdt)) |>
  select(USUBJID, DTHFL, DTHDT, DTHCAUS)

# Latest dated evidence of contact/assessment. Medication end dates are not
# included because they may represent planned rather than observed exposure.
ds_contact <- ds |>
  left_join(select(dm, USUBJID, RFSTDTC), by = "USUBJID") |>
  transmute(USUBJID,
            CONTACTDT = date10(RFSTDTC) + (as.numeric(DSSTWK) - 1) * 7)

df_alive <- bind_rows(
  ds_contact,
  transmute(ex, USUBJID, CONTACTDT = date10(EXSTDTC)),
  transmute(ex, USUBJID, CONTACTDT = date10(EXENDTC)),
  transmute(vs, USUBJID, CONTACTDT = date10(VSDTC)),
  transmute(lb, USUBJID, CONTACTDT = date10(LBDTC)),
  transmute(ls, USUBJID, CONTACTDT = date10(LSDTC)),
  transmute(pn, USUBJID, CONTACTDT = date10(PNDTC)),
  transmute(sv, USUBJID, CONTACTDT = date10(SVSTDTC)),
  transmute(sv, USUBJID, CONTACTDT = date10(SVENDTC))
) |>
  filter(!is.na(CONTACTDT)) |>
  group_by(USUBJID) |>
  summarise(
    LSTALVDT = max(CONTACTDT),
    .groups = "drop"
  )

# 1. ECOGBL
df_ecog <- vs |>
  filter(VSTESTCD == "ECOG" & VSBLFL == "Y") |>
  group_by(USUBJID) |>
  summarise(ECOGBL = first(VSSTRESN), .groups = "drop")

# 2. MEASDISF
df_meas <- ls |>
  filter(LSCAT == "TARGET" & VISIT == "BASELINE") |>
  group_by(USUBJID) |>
  summarise(MEASDISF = "Y", .groups = "drop")

# 3. VISCFL
df_visc <- ls |>
  filter(
    LSLOC %in% c("LIVER", "LUNGS", "KIDNEYS", "PANCREAS", "ADRENAL",
                 "BRAIN / CNS") &
      VISIT == "BASELINE"
  ) |>
  group_by(USUBJID) |>
  summarise(VISCFL = "Y", .groups = "drop")

# 4. PAINBL: protocol diary baseline window TRTSDT-6 through TRTSDT.
pn_trt <- pn |>
  left_join(df_ex, by = "USUBJID") |>
  mutate(PNDT = date10(PNDTC)) |>
  filter(
    PNTESTCD %in% c("PAININT", "ANSCORE"),
    !is.na(PNDT), !is.na(PNSTRESN),
    PNDT >= TRTSDT - 6, PNDT <= TRTSDT
  )

baseline_daily <- pn_trt |>
  group_by(USUBJID, PNTESTCD, PNDT) |>
  summarise(
    n_values = n_distinct(PNSTRESN),
    day_value = if_else(n_values == 1L, first(PNSTRESN), NA_real_),
    .groups = "drop"
  ) |>
  filter(n_values == 1L, !is.na(day_value))

baseline_summary <- baseline_daily |>
  group_by(USUBJID, PNTESTCD) |>
  summarise(
    n_valid_days = n(),
    median_value = median(day_value),
    mean_value = mean(day_value),
    .groups = "drop"
  )

pain_subjs <- baseline_summary |>
  filter(
    n_valid_days >= 5L,
    (PNTESTCD == "PAININT" & median_value >= 2) |
      (PNTESTCD == "ANSCORE" & mean_value >= 10)
  ) |>
  distinct(USUBJID) |>
  pull(USUBJID)

# 5. Baseline Labs
df_labs <- lb |>
  filter(LBBLFL == "Y") |>
  group_by(USUBJID, LBTESTCD) |>
  summarise(val = first(LBSTRESN), .groups = "drop") |>
  filter(LBTESTCD %in% c("PSA", "ALP", "HGB")) |>
  pivot_wider(id_cols = USUBJID, names_from = LBTESTCD, values_from = val) |>
  rename(PSABL = PSA, ALPBL = ALP, HGBBL = HGB)

# 6. Docetaxel Prior History
docetaxel <- cm |>
  filter(CMDECOD == "DOCETAXEL" & CMCAT == "PRIOR TREATMENT CHEMOTHERAPY") |>
  group_by(USUBJID) |>
  summarise(
    DOCRESP = if_else(
      any(CMRLTL %in% c("COMPLETE RESPONSE", "PARTIAL RESPONSE"), na.rm = TRUE),
      "Y", "N"
    ),
    DOCPROG = if_else(
      any(CMRSON == "DISEASE PROGRESSION" | CMRLTL == "PROGRESSIVE DISEASE",
          na.rm = TRUE),
      "DURING", "AFTER"
    ),
    .groups = "drop"
  )

# Combine into ADSL
adsl <- dm |>
  left_join(df_ex, by = "USUBJID") |>
  left_join(df_actual_trt, by = "USUBJID") |>
  left_join(df_death, by = "USUBJID") |>
  left_join(df_alive, by = "USUBJID") |>
  left_join(df_ecog, by = "USUBJID") |>
  left_join(df_meas, by = "USUBJID") |>
  left_join(df_visc, by = "USUBJID") |>
  left_join(df_labs, by = "USUBJID") |>
  left_join(docetaxel, by = "USUBJID") |>
  mutate(
    STUDYID = .env$STUDYID,
    SITEID = substring(SUBJID, 1, 3),
    AGE = if_else(AGEGRP == ">=85", 85, suppressWarnings(as.numeric(AGEGRP))),
    AGEGR1 = if_else(AGE < .env$AGE_STRAT_CUT, "<65", ">=65"),
    AGEGR1N = if_else(AGE < .env$AGE_STRAT_CUT, 1.0, 2.0),
    ETHNIC = "NOT REPORTED",
    SEX = "M",
    # Planned treatment comes from DM; actual treatment comes from administered EX.
    TRT01P = dplyr::case_when(
      grepl("MITOX", ARM, ignore.case = TRUE) | ARMCD == "A" ~ "MP",
      grepl("CABAZ|XRP", ARM, ignore.case = TRUE) ~ "CbzP",
      TRUE ~ .env$TRT01P_CODE
    ),
    TRT01PN = dplyr::case_when(
      grepl("MITOX", ARM, ignore.case = TRUE) | ARMCD == "A" ~ 2L,
      grepl("CABAZ|XRP", ARM, ignore.case = TRUE) ~ 1L,
      TRUE ~ as.integer(.env$TRT01PN_CODE)
    ),
    TRT01A = case_when(
      has_cbzp ~ "CbzP",
      has_mp ~ "MP",
      TRUE ~ TRT01P
    ),
    TRT01AN = case_when(
      has_cbzp ~ 1L,
      has_mp ~ 2L,
      TRUE ~ TRT01PN
    ),
    RANDDT = ymd(substring(RFSTDTC, 1, 10), quiet = TRUE),
    ITTFL = coalesce(ITT, "N"),
    SAFFL = coalesce(SAFETY, "N"),
    PPROTFL = coalesce(PPROT, "N"),
    DTHFL = coalesce(DTHFL, "N"),
    LSTALVDT = if_else(
      DTHFL == "Y" & !is.na(DTHDT) & LSTALVDT > DTHDT,
      DTHDT, LSTALVDT
    ),

    # No unapproved constant imputation in the real-data track.
    ECOGBLIF = "N",
    MEASDISF = coalesce(MEASDISF, "N"),
    VISCFL = coalesce(VISCFL, "N"),
    PAINBL = if_else(USUBJID %in% pain_subjs, "Y", "N"),
    ALBBLIF = " ",
    ALBBL = as.numeric(NA),
    LDHBLIF = " ",
    LDHBL = as.numeric(NA),
    PSABLIF = "N",
    ALPBLIF = "N",
    HGBBLIF = "N",
    DOCPROG = coalesce(DOCPROG, "AFTER"),
    DOCRESP = coalesce(DOCRESP, "N")
  ) |>
  select(
    STUDYID, USUBJID, SUBJID, SITEID,
    AGE, AGEGR1, AGEGR1N, RACE, ETHNIC, SEX,
    TRT01P, TRT01PN, TRT01A, TRT01AN, RANDDT, TRTSDT, TRTEDT, TRTDURD,
    ITTFL, SAFFL, PPROTFL, DTHFL, DTHDT, DTHCAUS, LSTALVDT,
    ECOGBL, MEASDISF, VISCFL, PAINBL, PSABL, ALPBL, ALBBL, LDHBL, HGBBL,
    DOCPROG, DOCRESP, ECOGBLIF, PSABLIF, ALPBLIF, HGBBLIF, ALBBLIF, LDHBLIF
  )

# Sort and Save
adsl <- adsl |> arrange(USUBJID)
dir.create("04_analysis_datasets/adam", showWarnings = FALSE)

# Assertions and Error Guards (QC-03)
if (nrow(adsl) < 371) {
  stop(
    "ERROR: [VALIDATION] ADSL output dataset is incomplete (expected N=371)!"
  )
}

# XPT v5 compliance (clean log): uppercase variable names + SAS date formats
names(adsl) <- toupper(names(adsl))
for (.dv in names(adsl)) {
  if (inherits(adsl[[.dv]], "Date")) {
    attr(adsl[[.dv]], "format.sas") <- "DATE9."
  }
}
write_xpt_v(adsl, "04_analysis_datasets/adam/adsl_v.xpt", domain = "ADSL")

cat("NOTE: [VALIDATION] Wrote validation ADSL: 04_analysis_datasets/adam/adsl_v.xpt\n")
cat(sprintf("NOTE: [ADSL-QC] ADSL n=%d DM n=%d\n", nrow(adsl), nrow(dm)))
if (nrow(adsl) != nrow(dm)) {
  warning("ADSL-QC: ADSL row count differs from DM")
}
trt_tab <- table(adsl$TRT01P, adsl$TRT01A, useNA = "ifany")
cat("NOTE: [ADSL-QC] planned-by-actual treatment:\n")
print(trt_tab)

#!/usr/bin/env Rscript
# ==============================================================================
# uplift_sdtm_34.R  —  SDTMIG 3.1.1 -> 3.4 conformance uplift (terminal session)
#
# Reads the PRISTINE real source SDTM (01_raw_source/real_sdtm/*.sas7bdat, the
# de-identified single-arm TROPIC mitoxantrone data, built trial-era to SDTMIG
# 3.1.1) and produces a 3.4-aligned derived layer. Raw source is never modified.
#
# Transforms (each a standard SDTM derivation, not a data invention):
#   DM  : AGE (numeric) from de-identified AGEGRP ('>=85' floored to 85, the cap
#         carried to SUPPDM); ACTARM/ACTARMCD (single completed arm); drop the
#         non-standard AGEGRP column; model variable order. -> CORE-000453/550
#   AE  : AESOC = AEBODSYS (MedDRA SOC already in AEBODSYS); EPOCH from VISIT. ->
#         CORE-000264/701
#   EX  : EPOCH from VISIT; EXENDY study day from EXENDTC vs DM.RFSTDTC. ->
#         CORE-000701/776
#   DS  : fill any blank EPOCH from VISIT (DS already carries EPOCH).
#   VS  : EPOCH from VISIT. -> CORE-000701
#   TS  : enrich with public NCT00417079 facts (NARMS, ACTSUB, SSTDTC, AGEMIN).
#   TA  : build the public 2-arm trial-design (Trial Arms) domain.
#   SUPPDM: append AGEGRP de-identification cap qualifier for the '>=85' group.
#
# EPOCH derivation rule (documented in SDRG): Subject Elements (SE) are absent
# from this de-identified extract, so EPOCH is derived from the collected VISIT
# structure — SCREENING -> SCREENING; BASELINE / CYCLE n / END OF TREATMENT ->
# TREATMENT; FOLLOW-UP n -> FOLLOW-UP; UNSCHEDULED -> TREATMENT (assessments
# occurred on-study). EPOCH values are valid CDISC CT.
#
# Output: writes XPT v5 to BOTH .core_run/sdtm34/ (CORE validation staging) and
# the git-ignored m5 tabulation copy. Source stays pristine.
# ==============================================================================
suppressMessages({library(haven); library(dplyr)})

ROOT <- normalizePath(file.path(dirname(sub("--file=", "", grep("--file=", commandArgs(FALSE), value=TRUE))), ".."))
if (length(ROOT) == 0 || is.na(ROOT)) ROOT <- getwd()
SRC <- file.path(ROOT, "01_raw_source", "real_sdtm")
STG <- file.path(ROOT, ".core_run", "sdtm34")
M5  <- file.path(ROOT, "m5", "datasets", "tropic", "tabulations", "sdtm", "datasets")
dir.create(STG, recursive = TRUE, showWarnings = FALSE)

rd  <- function(n) read_sas(file.path(SRC, paste0(n, ".sas7bdat")))
lab <- function(df, m) { for (v in names(m)) if (v %in% names(df)) attr(df[[v]], "label") <- m[[v]]; df }
# Canonical title-cased SDTM labels (mirror of 07_define_xml/uplift_define_34.py LBL) so the
# XPT variable labels match the define and are title-case (clears CORE-000594/398).
CLBL <- c(
 STUDYID="Study Identifier", DOMAIN="Domain Abbreviation", USUBJID="Unique Subject Identifier",
 SUBJID="Subject Identifier for the Study", RFSTDTC="Subject Reference Start Date/Time",
 RFENDTC="Subject Reference End Date/Time", AGE="Age", AGEU="Age Units", SEX="Sex", RACE="Race",
 ARM="Description of Planned Arm", ARMCD="Planned Arm Code", ACTARM="Description of Actual Arm",
 ACTARMCD="Actual Arm Code", EPOCH="Epoch", VISITNUM="Visit Number", VISIT="Visit Name",
 AESEQ="Sequence Number", AESPID="Sponsor-Defined Identifier", AEREFID="Reference ID",
 AETERM="Reported Term for the Adverse Event", AEDECOD="Dictionary-Derived Term",
 AEBODSYS="Body System or Organ Class", AESOC="Primary System Organ Class", AESER="Serious Event",
 AEACN="Action Taken with Study Treatment", AECONTRT="Concomitant or Additional Trtmnt Given",
 AEREL="Causality", AEPATT="Pattern of Adverse Event", AEOUT="Outcome of Adverse Event",
 AETOXGR="Standard Toxicity Grade", AESTWK="Study Week of Start of Adverse Event",
 AEENWK="Study Week of End of Adverse Event", AESTWKF="Imputation Level of AESTWK",
 AEENWKF="Imputation Level of AEENWK", EXSEQ="Sequence Number", EXTRT="Name of Actual Treatment",
 EXLOT="Lot Number", EXDOSE="Dose per Administration", EXDOSU="Dose Units", EXDOSFRM="Dose Form",
 EXROUTE="Route of Administration", EXSTDTC="Start Date/Time of Treatment",
 EXENDTC="End Date/Time of Treatment", EXSTDY="Study Day of Start of Treatment",
 EXENDY="Study Day of End of Treatment", DSSEQ="Sequence Number",
 DSTERM="Reported Term for the Disposition Event", DSDECOD="Standardized Disposition Term",
 DSCAT="Category for Disposition Event", DSSCAT="Subcategory for Disposition Event",
 DSSTWK="Study Week of Start of Disposition Event", DSSTWKF="Imputation Level of DSSTWK",
 VSSEQ="Sequence Number", VSTESTCD="Vital Signs Test Short Name", VSTEST="Vital Signs Test Name",
 VSORRES="Result or Finding in Original Units", VSORRESU="Original Units",
 VSSTRESC="Character Result/Finding in Std Format", VSSTRESN="Numeric Finding in Standard Units",
 VSSTRESU="Standard Units", VSMETHOD="Method of Test or Examination", VSBLFL="Baseline Flag",
 VSDRVFL="Derived Flag", VSDTC="Date/Time of Measurements", VSDY="Study Day of Vital Signs",
 RDOMAIN="Related Domain Abbreviation", IDVAR="Identifying Variable",
 IDVARVAL="Identifying Variable Value", QNAM="Qualifier Variable Name", QLABEL="Qualifier Variable Label",
 QVAL="Data Value", QORIG="Origin", QEVAL="Evaluator", TSSEQ="Sequence Number",
 TSPARMCD="Trial Summary Parameter Short Name", TSPARM="Trial Summary Parameter", TSVAL="Parameter Value",
 TAETORD="Planned Order of Element within Arm", ETCD="Element Code", ELEMENT="Description of Element",
 TABRANCH="Branch")
# Strip leading/trailing whitespace (clears CORE-000867; whitespace carries no clinical meaning)
# and apply canonical labels — both preserve data values, only hygiene/metadata.
finalize <- function(df) {
  for (c in names(df)) {
    if (is.character(df[[c]])) df[[c]] <- trimws(df[[c]])
    if (c %in% names(CLBL)) attr(df[[c]], "label") <- unname(CLBL[[c]])
  }
  df
}
# CDISC SDTM library variable order per domain (clears CORE-000852); others keep their order
ORD <- list(
 dm = c("STUDYID","DOMAIN","USUBJID","SUBJID","RFSTDTC","RFENDTC","AGE","AGEU","SEX","RACE","ARMCD","ARM","ACTARMCD","ACTARM"),
 ae = c("STUDYID","DOMAIN","USUBJID","AESEQ","AEREFID","AESPID","AETERM","AEDECOD","AEBODSYS","AESOC","AESER","AEACN","AEREL","AEPATT","AEOUT","AESCONG","AESDISAB","AESDTH","AESHOSP","AESLIFE","AESMIE","AECONTRT","AETOXGR","VISITNUM","VISIT","EPOCH"),
 ex = c("STUDYID","DOMAIN","USUBJID","EXSEQ","EXTRT","EXDOSE","EXDOSU","EXDOSFRM","EXROUTE","EXLOT","VISITNUM","VISIT","EPOCH","EXSTDTC","EXENDTC","EXSTDY","EXENDY"),
 ds = c("STUDYID","DOMAIN","USUBJID","DSSEQ","DSTERM","DSDECOD","DSCAT","DSSCAT","VISITNUM","VISIT","EPOCH"),
 vs = c("STUDYID","DOMAIN","USUBJID","VSSEQ","VSTESTCD","VSTEST","VSORRES","VSORRESU","VSSTRESC","VSSTRESN","VSSTRESU","VSMETHOD","VSBLFL","VSDRVFL","VISITNUM","VISIT","EPOCH","VSDTC","VSDY"))
# write v5 XPT to both staging and the m5 submission copy
wr  <- function(df, name) {
  if (!is.null(ORD[[name]])) df <- df[, ORD[[name]], drop = FALSE]
  df <- finalize(df)
  haven::write_xpt(df, file.path(STG, paste0(name, ".xpt")), version = 5, name = toupper(name))
  haven::write_xpt(df, file.path(M5,  paste0(name, ".xpt")), version = 5, name = toupper(name))
  cat(sprintf("  wrote %-8s rows=%-6d cols=%d\n", toupper(name), nrow(df), ncol(df)))
}

# VISIT -> EPOCH (CDISC EPOCH CT)
epoch_of <- function(visit) {
  v <- toupper(trimws(ifelse(is.na(visit), "", visit)))
  dplyr::case_when(
    grepl("^SCREEN", v)                      ~ "SCREENING",
    grepl("^FOLLOW", v)                      ~ "FOLLOW-UP",
    grepl("^BASELINE|^CYCLE|END OF TREAT", v) ~ "TREATMENT",
    grepl("^UNSCHEDULED", v)                 ~ "TREATMENT",
    v == ""                                  ~ "TREATMENT",
    TRUE                                     ~ "TREATMENT"
  )
}
studyday <- function(d, ref) ifelse(is.na(d) | is.na(ref), NA_real_,
                                    ifelse(d >= ref, as.numeric(d - ref) + 1, as.numeric(d - ref)))
`%||%` <- function(a,b) if (is.null(a) || is.na(a)) b else a
# Build SUPP-- records relocating non-standard qualifier vars (e.g. the de-identification
# week-offset timing) out of the parent domain into SUPPQUAL, linked by IDVAR/IDVARVAL.
mk_supp <- function(dat, rdom, idvar, qnams) {
  out <- list()
  for (q in qnams) if (q %in% names(dat)) {
    keep <- !is.na(dat[[q]]) & trimws(as.character(dat[[q]])) != ""
    sub <- dat[keep, , drop = FALSE]
    if (nrow(sub) == 0) next
    out[[q]] <- tibble(STUDYID = sub$STUDYID, RDOMAIN = rdom, USUBJID = sub$USUBJID,
                       IDVAR = idvar, IDVARVAL = as.character(sub[[idvar]]),
                       QNAM = q, QLABEL = substr(CLBL[[q]] %||% q, 1, 40),
                       QVAL = as.character(sub[[q]]), QORIG = "Derived", QEVAL = "")
  }
  if (length(out)) bind_rows(out) else tibble()
}

cat("== SDTM 3.4 uplift ==\n")

# ---- DM ----------------------------------------------------------------------
dm <- rd("dm")
ref <- dm %>% transmute(USUBJID, RFREF = as.Date(substr(RFSTDTC, 1, 10)))
age_num <- suppressWarnings(as.integer(dm$AGEGRP))
capped  <- is.na(age_num) & grepl(">=?\\s*85|>85|85\\+", dm$AGEGRP)
dm$AGE <- ifelse(capped, 85L, age_num)
dm$ACTARM   <- dm$ARM
dm$ACTARMCD <- dm$ARMCD
dm_out <- dm %>%
  select(STUDYID, DOMAIN, USUBJID, SUBJID, RFSTDTC, RFENDTC,
         AGE, AGEU, SEX, RACE, ARM, ARMCD, ACTARM, ACTARMCD) %>%
  lab(list(AGE="Age", AGEU="Age Units", ACTARM="Description of Actual Arm",
           ACTARMCD="Actual Arm Code", ARM="Description of Planned Arm",
           ARMCD="Planned Arm Code"))
wr(dm_out, "dm")
cat(sprintf("   DM: AGE derived (capped '>=85'->85 for %d subj), ACTARM/ACTARMCD added, AGEGRP dropped\n", sum(capped)))

# ---- SUPPDM (append AGEGRP cap qualifier) ------------------------------------
suppdm <- rd("suppdm")
if (any(capped)) {
  add <- dm %>% filter(capped) %>%
    transmute(STUDYID, RDOMAIN="DM", USUBJID, IDVAR="", IDVARVAL="",
              QNAM="AGEGRP", QLABEL="Age Group (de-identification cap)",
              QVAL=">=85", QORIG="Assigned", QEVAL="SPONSOR", SUBJID)
  common <- intersect(names(suppdm), names(add))
  suppdm <- bind_rows(suppdm[common], add[common])
}
wr(suppdm %>% select(-any_of("SUBJID")), "suppdm")   # SUPP-- carries USUBJID, not SUBJID

# ---- AE ----------------------------------------------------------------------
ae <- rd("ae")
ae$AESOC <- ae$AEBODSYS
ae$EPOCH <- epoch_of(ae$VISIT)
supp_ae <- mk_supp(ae, "AE", "AESEQ", c("AESTWK","AEENWK","AESTWKF","AEENWKF"))
ae_out <- ae %>%   # drop redundant SUBJID (DM-only) + week vars relocated to SUPPAE
  select(STUDYID, DOMAIN, USUBJID, AESEQ, any_of(c("AESPID","AEREFID")),
         AETERM, AEDECOD, AEBODSYS, AESOC,
         AESER, any_of(c("AESCONG","AESDISAB","AESDTH","AESHOSP","AESLIFE","AESMIE")),
         AEACN, AECONTRT, AEREL, AEPATT, AEOUT, AETOXGR, EPOCH, VISITNUM, VISIT)
wr(ae_out, "ae")

# ---- EX ----------------------------------------------------------------------
ex <- rd("ex") %>% left_join(ref, by="USUBJID")
ex$EPOCH  <- epoch_of(ex$VISIT)
ex$EXENDY <- studyday(as.Date(substr(ex$EXENDTC,1,10)), ex$RFREF)
ex_out <- ex %>%   # drop redundant SUBJID (DM-only)
  select(STUDYID, DOMAIN, USUBJID, EXSEQ, EXTRT, any_of("EXLOT"), EXDOSE, EXDOSU,
         any_of(c("EXDOSFRM","EXROUTE")), EPOCH, VISITNUM, VISIT,
         EXSTDTC, EXENDTC, EXSTDY, EXENDY)
wr(ex_out, "ex")

# ---- DS ----------------------------------------------------------------------
ds <- rd("ds")
ds$EPOCH <- ifelse(is.na(ds$EPOCH) | trimws(ds$EPOCH)=="", epoch_of(ds$VISIT), ds$EPOCH)
supp_ds <- mk_supp(ds, "DS", "DSSEQ", c("DSSTWK","DSSTWKF"))
ds_out <- ds %>%   # drop redundant SUBJID + week vars relocated to SUPPDS
  select(STUDYID, DOMAIN, USUBJID, DSSEQ, DSTERM, DSDECOD, DSCAT, DSSCAT, EPOCH, VISITNUM, VISIT)
wr(ds_out, "ds")

# ---- VS ----------------------------------------------------------------------
vs <- rd("vs")
vs$EPOCH <- epoch_of(vs$VISIT)
vs_out <- vs %>% select(-any_of("SUBJID")) %>% relocate(EPOCH, .before = VISITNUM)
wr(vs_out, "vs")

# ---- TS (enrich with public NCT00417079 facts) -------------------------------
ts <- rd("ts")
sid <- ts$STUDYID[1]
new <- tibble(
  STUDYID = sid, DOMAIN = "TS",
  TSPARMCD = c("NARMS","ACTSUB","SSTDTC","AGEMIN"),
  TSPARM   = c("Planned Number of Arms","Actual Number of Subjects",
               "Study Start Date","Planned Minimum Age of Subjects"),
  TSVAL    = c("2","371","2007","P18Y"))
ts2 <- ts %>% filter(!TSPARMCD %in% new$TSPARMCD)
ts_out <- bind_rows(ts2[intersect(names(ts2), c("STUDYID","DOMAIN","TSPARMCD","TSPARM","TSVAL"))],
                    new) %>%
  group_by(TSPARMCD) %>% slice(1) %>% ungroup() %>%
  arrange(TSPARMCD) %>% mutate(TSSEQ = row_number()) %>%
  select(STUDYID, DOMAIN, TSSEQ, TSPARMCD, TSPARM, TSVAL)
wr(ts_out, "ts")
cat(sprintf("   TS: %d params (added NARMS, ACTSUB, SSTDTC, AGEMIN)\n", nrow(ts_out)))

# ---- TA (public 2-arm trial design) ------------------------------------------
elems <- tibble(TAETORD=1:3, ETCD=c("SCRN","TRT","FUP"),
                ELEMENT=c("Screening","Treatment","Follow-up"),
                EPOCH=c("SCREENING","TREATMENT","FOLLOW-UP"))
ta_out <- bind_rows(
  mutate(elems, ARMCD="A", ARM="MITOXANTRONE/PREDNISONE"),
  mutate(elems, ARMCD="B", ARM="CABAZITAXEL/PREDNISONE")
) %>% transmute(STUDYID=sid, DOMAIN="TA", ARMCD, ARM, TAETORD, ETCD, ELEMENT,
                TABRANCH="", EPOCH)
wr(ta_out, "ta")

# ---- SUPPAE / SUPPDS (source SUPP + relocated week-offset qualifiers) ---------
sup_ae <- rd("suppae") %>% select(-any_of("SUBJID"))
if (nrow(supp_ae)) { cm <- intersect(names(sup_ae), names(supp_ae)); sup_ae <- bind_rows(sup_ae[cm], supp_ae[cm]) }
wr(sup_ae, "suppae")
sup_ds <- rd("suppds") %>% select(-any_of("SUBJID"))
if (nrow(supp_ds)) { cm <- intersect(names(sup_ds), names(supp_ds)); sup_ds <- bind_rows(sup_ds[cm], supp_ds[cm]) }
wr(sup_ds, "suppds")

cat("== uplift complete ==\n")

# adam_conf_check.R — focused ADaM conformance check (CDISC ADaMIG v1.3-aligned).
#
# Executable, transparent QC gate implementing the high-value, objectively-checkable ADaM
# conformance rule families that Pinnacle 21 / CDISC CORE cover: dataset<->define.xml consistency,
# ADaMIG structural rules, key/identifier integrity, and controlled-terminology conformance.
#
# This is NOT the full FDA Validator rule pack and does NOT replace the authoritative Pinnacle 21
# Enterprise run (see 06_telemetry/p21_adam_runrecord.md). It is an honest interim gate that runs
# in-environment and surfaces real findings. Inputs: 04_adam/<ds>_prod.xpt + define metadata JSON.
suppressMessages({library(haven); library(jsonlite)})

meta <- jsonlite::fromJSON("06_telemetry/adam_conf_define_meta.json",
                           simplifyDataFrame = TRUE)
F <- list()  # findings accumulator
add <- function(rule, sev, ds, var, n, msg)
  F[[length(F) + 1]] <<- data.frame(rule, severity = sev, dataset = ds, variable = var,
                                    count = n, message = msg, stringsAsFactors = FALSE)

ds_names <- names(meta$datasets)
adsl_usubjid <- NULL

for (ds in ds_names) {
  f <- sprintf("04_adam/%s_prod.xpt", tolower(ds))
  if (!file.exists(f)) { add("AD0000", "Error", ds, NA, 1, "dataset XPT not found"); next }
  d  <- haven::read_xpt(f)
  dv <- meta$datasets[[ds]]$variables          # define vars (data.frame)
  structure <- meta$datasets[[ds]]$structure
  dn <- names(d)
  if (ds == "ADSL" && "USUBJID" %in% dn) adsl_usubjid <- unique(as.character(d$USUBJID))

  # ---- Dataset <-> define.xml consistency -----------------------------------------------------
  miss_in_data <- setdiff(dv$name, dn)
  for (v in miss_in_data) add("AD0002", "Error", ds, v, 1, "Variable defined in define.xml is absent from the dataset")
  extra_in_data <- setdiff(dn, dv$name)
  for (v in extra_in_data) add("AD0001", "Error", ds, v, 1, "Dataset variable is not described in define.xml")

  for (i in seq_len(nrow(dv))) {
    v <- dv$name[i]; if (!v %in% dn) next
    col <- d[[v]]
    data_type <- if (is.numeric(col)) "numeric" else "character"
    if (!is.na(dv$type[i]) && data_type != dv$type[i])
      add("AD0003", "Error", ds, v, 1,
          sprintf("Type mismatch: define=%s, data=%s", dv$type[i], data_type))
    dlab <- attr(col, "label"); dlab <- if (is.null(dlab)) "" else dlab
    deflab <- dv$label[i]; deflab <- if (is.na(deflab)) "" else deflab
    if (nzchar(trimws(dlab)) && nzchar(deflab) && trimws(dlab) != trimws(deflab))
      add("AD0004", "Warning", ds, v, 1,
          sprintf("Label differs from define: data='%s' vs define='%s'", dlab, deflab))
    if (data_type == "character" && !is.na(dv$length[i])) {
      mx <- suppressWarnings(max(nchar(as.character(col)), na.rm = TRUE)); if (!is.finite(mx)) mx <- 0
      if (mx > dv$length[i])
        add("AD0005", "Warning", ds, v, mx, sprintf("Max data length %d exceeds define Length %d", mx, dv$length[i]))
    }
    # ---- v5 XPORT / ADaMIG variable-attribute rules ----
    if (nchar(v) > 8)  add("AD0101", "Error", ds, v, nchar(v), "Variable name exceeds 8 characters")
    if (!nzchar(trimws(dlab))) add("AD0102", "Error", ds, v, 1, "Variable label is missing")
    else if (nchar(dlab) > 40) add("AD0102", "Error", ds, v, nchar(dlab), "Variable label exceeds 40 characters")
    if (isTRUE(dv$mandatory[i]) && all(is.na(col)))
      add("AD0105", "Warning", ds, v, 1, "Mandatory variable is entirely missing")
  }

  # ---- ADaMIG structural rules ----------------------------------------------------------------
  for (req in c("STUDYID", "USUBJID")) if (!req %in% dn)
    add("AD0104", "Error", ds, req, 1, "Required ADaM identifier variable is missing")

  if (tolower(trimws(structure)) == "one record per subject" && "USUBJID" %in% dn) {
    dup <- sum(duplicated(d$USUBJID))
    if (dup > 0) add("AD0103", "Error", ds, "USUBJID", dup,
                     "Structure is one-record-per-subject but USUBJID has duplicate records")
  }

  is_bds <- ("PARAMCD" %in% dn) || grepl("parameter", tolower(structure))
  if (is_bds) {
    for (req in c("PARAMCD", "PARAM")) if (!req %in% dn)
      add("AD0106", "Warning", ds, req, 1, "BDS dataset is missing a required parameter variable")
    if ("PARAMCD" %in% dn) {
      nm <- sum(is.na(d$PARAMCD) | trimws(as.character(d$PARAMCD)) == "")
      if (nm > 0) add("AD0109", "Error", ds, "PARAMCD", nm, "PARAMCD has missing values")
      if ("PARAM" %in% dn) {
        pc <- as.character(d$PARAMCD); pm <- as.character(d$PARAM)
        bad <- tapply(pm, pc, function(x) length(unique(x)) > 1)
        n_bad <- sum(bad, na.rm = TRUE)
        if (n_bad > 0) add("AD0107", "Error", ds, "PARAMCD/PARAM", n_bad,
                           "PARAMCD does not map 1:1 to PARAM")
      }
    }
    if (!any(c("AVAL", "AVALC") %in% dn))
      add("AD0108", "Warning", ds, "AVAL/AVALC", 1, "BDS dataset has neither AVAL nor AVALC")
  }

  if (ds != "ADSL" && "USUBJID" %in% dn && !is.null(adsl_usubjid)) {
    orph <- setdiff(unique(as.character(d$USUBJID)), adsl_usubjid)
    if (length(orph) > 0) add("AD0110", "Warning", ds, "USUBJID", length(orph),
                              "USUBJID value(s) not present in ADSL")
  }

  # ---- Controlled Terminology (data vs define.xml codelists) ----------------------------------
  for (i in seq_len(nrow(dv))) {
    cl <- dv$codelist[i]; v <- dv$name[i]
    if (is.na(cl) || !v %in% dn) next
    allowed <- meta$codelists[[cl]]; if (is.null(allowed)) next
    vals <- as.character(d[[v]]); vals <- vals[!is.na(vals) & trimws(vals) != ""]
    bad <- unique(vals[!vals %in% allowed])
    if (length(bad) > 0)
      add("AD0201", "Error", ds, v, length(bad),
          sprintf("Value(s) not in codelist %s: %s", cl,
                  paste(utils::head(bad, 5), collapse = ", ")))
  }
}

res <- if (length(F)) do.call(rbind, F) else
  data.frame(rule = character(), severity = character(), dataset = character(),
             variable = character(), count = integer(), message = character())
res <- res[order(factor(res$severity, levels = c("Error", "Warning", "Notice")), res$dataset), ]

write.csv(res, "06_telemetry/adam_conformance_report.csv", row.names = FALSE)
n_err <- sum(res$severity == "Error"); n_warn <- sum(res$severity == "Warning")
status <- if (n_err == 0) "PASS (0 errors at this check level)" else "FAIL — errors present"
cat(sprintf("\n=== ADaM Conformance Check — %d findings (Error=%d, Warning=%d) -> %s ===\n",
            nrow(res), n_err, n_warn, status))
if (nrow(res)) {
  agg <- aggregate(count ~ rule + severity, data = res, FUN = length)
  agg <- agg[order(factor(agg$severity, levels = c("Error","Warning","Notice"))), ]
  print(agg, row.names = FALSE)
  cat("\n-- by dataset --\n"); print(table(res$dataset, res$severity))
}
jsonlite::write_json(list(status = status, errors = n_err, warnings = n_warn,
                          findings = nrow(res)),
                     "06_telemetry/adam_conformance_status.json", auto_unbox = TRUE)

# ---- machine-refreshed markdown report (data tables; interpretation lives in the run-record) ----
md <- c(
  "# ADaM Conformance Report (focused, CDISC ADaMIG v1.3-aligned)",
  "",
  sprintf("*Generated:* `%s`  ", format(Sys.time())),
  sprintf("*Engine:* in-repo `adam_conf_check.R` — interim gate (NOT the full FDA Validator pack; see `p21_adam_runrecord.md`).  "),
  sprintf("*Inputs:* 7 ADaM `*_prod.xpt` + `07_define_xml/define.xml`.  "),
  sprintf("*Result:* **%s** — %d findings (Error **%d**, Warning **%d**).", status, nrow(res), n_err, n_warn),
  "", "## Findings by rule", "",
  "| Rule | Severity | Count | What it checks |", "|---|---|---|---|")
desc <- c(AD0001="Dataset variable not described in define.xml", AD0002="define.xml variable absent from dataset",
          AD0003="Type mismatch (define vs data)", AD0004="Variable label differs from define.xml",
          AD0005="Char length exceeds define.xml Length", AD0101="Variable name > 8 characters",
          AD0102="Variable label missing or > 40 characters", AD0103="One-record-per-subject violated (ADSL)",
          AD0104="Required identifier (STUDYID/USUBJID) missing", AD0105="Mandatory variable entirely missing",
          AD0106="BDS missing PARAMCD/PARAM", AD0107="PARAMCD not 1:1 with PARAM",
          AD0108="BDS has neither AVAL nor AVALC", AD0109="PARAMCD has missing values",
          AD0110="USUBJID not present in ADSL", AD0201="Value not in define.xml codelist")
if (nrow(res)) {
  byrule <- as.data.frame(table(res$rule, res$severity)); byrule <- byrule[byrule$Freq > 0, ]
  byrule <- byrule[order(factor(byrule$Var2, levels = c("Error","Warning","Notice")), byrule$Var1), ]
  for (i in seq_len(nrow(byrule)))
    md <- c(md, sprintf("| %s | %s | %d | %s |", byrule$Var1[i], byrule$Var2[i], byrule$Freq[i],
                        ifelse(is.na(desc[as.character(byrule$Var1[i])]), "", desc[as.character(byrule$Var1[i])])))
  md <- c(md, "", "## Specific findings (excluding the AD0102 label list)", "",
          "| Rule | Sev | Dataset | Variable | n | Message |", "|---|---|---|---|---|---|")
  det <- res[res$rule != "AD0102", ]
  for (i in seq_len(nrow(det)))
    md <- c(md, sprintf("| %s | %s | %s | %s | %s | %s |", det$rule[i], det$severity[i], det$dataset[i],
                        det$variable[i], det$count[i], gsub("\\|", "/", det$message[i])))
  ad <- res[res$rule == "AD0102", ]
  if (nrow(ad)) {
    md <- c(md, "", sprintf("## AD0102 — missing variable labels (%d variables)", nrow(ad)), "")
    tb <- table(ad$dataset)
    md <- c(md, "| Dataset | Unlabelled vars |", "|---|---|")
    for (nm in names(tb)) md <- c(md, sprintf("| %s | %d |", nm, tb[[nm]]))
  }
}
writeLines(md, "06_telemetry/adam_conformance_report.md")
cat("\nWrote: adam_conformance_report.{csv,md}, adam_conformance_status.json\n")

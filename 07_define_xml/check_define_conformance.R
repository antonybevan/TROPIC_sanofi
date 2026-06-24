#!/usr/bin/env Rscript
# =============================================================================
# check_define_conformance.R
# -----------------------------------------------------------------------------
# Assert that 07_define_xml/define.xml CONFORMS TO the authoritative spec
# 00_specifications/ADaM_spec.xlsx.
#
# This is the INVERTED C-4 direction. Previously generate_adam_specs.py rendered
# a "spec" FROM the define (circular: the spec could never disagree). Now the
# spec is the single source of truth and the define is the artifact UNDER TEST:
# every dataset / variable / attribute / codelist in the define must match the
# spec, or this script reports the drift and exits non-zero (so it can gate the
# build and CI).
#
# Usage:
#   Rscript 07_define_xml/check_define_conformance.R            # gate
#   Rscript 07_define_xml/check_define_conformance.R --self-test # prove teeth
# =============================================================================

suppressMessages({
  library(xml2)
  library(dplyr)
  library(readxl)
  library(tidyr)
  library(jsonlite)
})

find_file <- function(rel) {
  cands <- c(rel, file.path("..", rel), file.path(Sys.getenv("TROPIC_ROOT", "."), rel))
  hit <- Filter(file.exists, cands)
  if (!length(hit)) stop("cannot locate ", rel, " from ", getwd())
  normalizePath(hit[[1]])
}

# ---- the spec (master) ------------------------------------------------------
read_spec_grid <- function(path) {
  v <- read_excel(path, "Variables")
  d <- read_excel(path, "Datasets")
  cl <- read_excel(path, "Codelists")
  list(
    vars = transmute(v,
      dataset = Dataset, variable = Variable,
      order = as.integer(Order), label = Label, type = `Data Type`,
      length = as.integer(Length), mandatory = Mandatory,
      codelist = Codelist, method = Method
    ),
    ds = transmute(d,
      dataset = Dataset, class = Class,
      structure = Structure, label = Description
    ),
    # Codelist/term NCI controlled-terminology codes (one row per term). Empty for
    # sponsor-defined codelists; populated for codelists derived from CDISC CT.
    cl = transmute(cl,
      codelist = ID, term = as.character(Term),
      cl_code = `NCI Codelist Code`, term_code = `NCI Term Code`
    )
  )
}

# ---- the define (artifact under test) ---------------------------------------
read_define_grid <- function(path) {
  x <- read_xml(path)
  ns <- xml_ns(x)
  attr_local <- function(node, xp, a) {
    n <- xml_find_first(node, xp, ns)
    if (inherits(n, "xml_missing")) NA_character_ else xml_attr(n, a)
  }
  itemdefs <- xml_find_all(x, ".//d1:ItemDef", ns)
  idmap <- tibble(
    oid = xml_attr(itemdefs, "OID"),
    name = xml_attr(itemdefs, "Name"), # authoritative variable name (OID suffix may differ)
    type = xml_attr(itemdefs, "DataType"),
    length = suppressWarnings(as.integer(xml_attr(itemdefs, "Length"))),
    label = vapply(itemdefs, function(n) {
      t <- xml_find_first(n, "./d1:Description/d1:TranslatedText", ns)
      if (inherits(t, "xml_missing")) NA_character_ else xml_text(t)
    }, character(1)),
    codelist = vapply(itemdefs, attr_local, character(1),
      xp = "./d1:CodeListRef", a = "CodeListOID"
    )
  )
  igs <- xml_find_all(x, ".//d1:ItemGroupDef", ns)
  vars <- bind_rows(lapply(igs, function(ig) {
    refs <- xml_find_all(ig, "./d1:ItemRef", ns)
    m <- idmap[match(xml_attr(refs, "ItemOID"), idmap$oid), ]
    tibble(
      dataset = xml_attr(ig, "Name"),
      variable = m$name,
      order = suppressWarnings(as.integer(xml_attr(refs, "OrderNumber"))),
      label = m$label, type = m$type, length = m$length,
      mandatory = ifelse(xml_attr(refs, "Mandatory") %in% "Yes", "Yes", "No"),
      codelist = m$codelist, method = xml_attr(refs, "MethodOID")
    )
  }))
  ds <- tibble(
    dataset = xml_attr(igs, "Name"),
    class = vapply(igs, attr_local, character(1), xp = "./def:Class", a = "Name"),
    structure = xml_attr(igs, "Structure"),
    label = vapply(igs, function(n) {
      t <- xml_find_first(n, "./d1:Description/d1:TranslatedText", ns)
      if (inherits(t, "xml_missing")) NA_character_ else xml_text(t)
    }, character(1))
  )
  # Codelist/term NCI codes carried as <Alias Context="nci:ExtCodeID" Name="C..."/>.
  cls <- xml_find_all(x, ".//d1:CodeList", ns)
  alias_code <- function(node) {
    a <- xml_find_first(node, "./d1:Alias[@Context='nci:ExtCodeID']", ns)
    if (inherits(a, "xml_missing")) NA_character_ else xml_attr(a, "Name")
  }
  cl <- bind_rows(lapply(cls, function(c) {
    oid <- xml_attr(c, "OID")
    clc <- alias_code(c)
    items <- xml_find_all(c, "./d1:CodeListItem", ns)
    if (!length(items)) {
      return(tibble(codelist = oid, term = NA_character_, cl_code = clc, term_code = NA_character_))
    }
    bind_rows(lapply(items, function(it) {
      tibble(codelist = oid, term = xml_attr(it, "CodedValue"),
             cl_code = clc, term_code = alias_code(it))
    }))
  }))
  list(vars = vars, ds = ds, cl = cl)
}

# ---- comparison -------------------------------------------------------------
ne <- function(a, b) { # NA-safe "not equal"
  (is.na(a) != is.na(b)) | (!is.na(a) & !is.na(b) & a != b)
}

compare <- function(spec, def) {
  out <- list()
  # dataset presence
  miss_ds <- setdiff(spec$ds$dataset, def$ds$dataset)
  extra_ds <- setdiff(def$ds$dataset, spec$ds$dataset)
  if (length(miss_ds)) {
    out[[length(out) + 1]] <- tibble(
      level = "dataset",
      dataset = miss_ds, variable = NA, attribute = "presence",
      spec_value = "present", define_value = "ABSENT", severity = "ERROR"
    )
  }
  if (length(extra_ds)) {
    out[[length(out) + 1]] <- tibble(
      level = "dataset",
      dataset = extra_ds, variable = NA, attribute = "presence",
      spec_value = "ABSENT", define_value = "present", severity = "ERROR"
    )
  }
  # dataset attributes
  dj <- inner_join(spec$ds, def$ds, by = "dataset", suffix = c(".s", ".d"))
  for (a in c("class", "structure", "label")) {
    bad <- dj[ne(dj[[paste0(a, ".s")]], dj[[paste0(a, ".d")]]), ]
    if (nrow(bad)) {
      out[[length(out) + 1]] <- tibble(
        level = "dataset",
        dataset = bad$dataset, variable = NA, attribute = a,
        spec_value = bad[[paste0(a, ".s")]], define_value = bad[[paste0(a, ".d")]],
        severity = "ERROR"
      )
    }
  }
  # variable presence
  sk <- paste(spec$vars$dataset, spec$vars$variable)
  dk <- paste(def$vars$dataset, def$vars$variable)
  miss_v <- spec$vars[!sk %in% dk, ]
  extra_v <- def$vars[!dk %in% sk, ]
  if (nrow(miss_v)) {
    out[[length(out) + 1]] <- tibble(
      level = "variable",
      dataset = miss_v$dataset, variable = miss_v$variable, attribute = "presence",
      spec_value = "present", define_value = "ABSENT", severity = "ERROR"
    )
  }
  if (nrow(extra_v)) {
    out[[length(out) + 1]] <- tibble(
      level = "variable",
      dataset = extra_v$dataset, variable = extra_v$variable, attribute = "presence",
      spec_value = "ABSENT", define_value = "present", severity = "ERROR"
    )
  }
  # variable attributes
  vj <- inner_join(spec$vars, def$vars,
    by = c("dataset", "variable"),
    suffix = c(".s", ".d")
  )
  for (a in c("order", "label", "type", "length", "mandatory", "codelist", "method")) {
    bad <- vj[ne(vj[[paste0(a, ".s")]], vj[[paste0(a, ".d")]]), ]
    if (nrow(bad)) {
      out[[length(out) + 1]] <- tibble(
        level = "variable",
        dataset = bad$dataset, variable = bad$variable, attribute = a,
        spec_value = as.character(bad[[paste0(a, ".s")]]),
        define_value = as.character(bad[[paste0(a, ".d")]]), severity = "ERROR"
      )
    }
  }
  # codelist NCI controlled-terminology codes (spec <-> define). Drift fires only when a
  # code differs or is present on one side and absent on the other; sponsor codelists
  # (no code on either side) are NA-equal and never flagged.
  scl <- distinct(spec$cl, codelist, cl_code)
  dcl <- distinct(def$cl, codelist, cl_code)
  clj <- inner_join(scl, dcl, by = "codelist", suffix = c(".s", ".d"))
  bad <- clj[ne(clj[["cl_code.s"]], clj[["cl_code.d"]]), ]
  if (nrow(bad)) {
    out[[length(out) + 1]] <- tibble(
      level = "codelist", dataset = NA, variable = bad$codelist,
      attribute = "nci_codelist_code",
      spec_value = bad[["cl_code.s"]], define_value = bad[["cl_code.d"]], severity = "ERROR"
    )
  }
  tj <- inner_join(spec$cl, def$cl, by = c("codelist", "term"), suffix = c(".s", ".d"))
  bad <- tj[ne(tj[["term_code.s"]], tj[["term_code.d"]]), ]
  if (nrow(bad)) {
    out[[length(out) + 1]] <- tibble(
      level = "codelist", dataset = NA, variable = paste0(bad$codelist, "/", bad$term),
      attribute = "nci_term_code",
      spec_value = bad[["term_code.s"]], define_value = bad[["term_code.d"]], severity = "ERROR"
    )
  }
  if (length(out)) {
    bind_rows(out)
  } else {
    tibble(
      level = character(), dataset = character(), variable = character(),
      attribute = character(), spec_value = character(),
      define_value = character(), severity = character()
    )
  }
}

run_gate <- function() {
  spec_path <- find_file("00_specifications/ADaM_spec.xlsx")
  define_path <- find_file("07_define_xml/define.xml")
  spec <- read_spec_grid(spec_path)
  def <- read_define_grid(define_path)
  findings <- compare(spec, def)

  report_dir <- find_file("06_telemetry/conformance")
  ts <- format(Sys.time(), "%Y-%m-%dT%H:%M:%S")
  result <- list(
    check = "spec -> define conformance (C-4 inversion)",
    spec = basename(spec_path), define = basename(define_path),
    timestamp = ts,
    datasets_checked = nrow(spec$ds), variables_checked = nrow(spec$vars),
    findings = nrow(findings),
    status = if (nrow(findings) == 0) "PASS" else "FAIL",
    detail = findings
  )
  write_json(result, file.path(report_dir, "spec_define_conformance.json"),
    auto_unbox = TRUE, pretty = TRUE, na = "string"
  )

  cat(sprintf("\nspec -> define conformance: %s\n", result$status))
  cat(sprintf(
    "  spec:   %s  (%d datasets / %d variables)\n",
    result$spec, result$datasets_checked, result$variables_checked
  ))
  cat(sprintf("  define: %s\n  findings: %d\n", result$define, result$findings))
  if (nrow(findings)) {
    print(as.data.frame(findings), right = FALSE)
    cat(
      "\nDefine.xml DRIFTED from the spec. Re-author the spec or regenerate the\n",
      "define to match, then re-run.\n"
    )
    quit(status = 1)
  }
  cat("  define.xml conforms to the authoritative spec.\n")
  invisible(0)
}

self_test <- function() {
  spec_path <- find_file("00_specifications/ADaM_spec.xlsx")
  define_path <- find_file("07_define_xml/define.xml")
  spec <- read_spec_grid(spec_path)
  def <- read_define_grid(define_path)

  clean <- compare(spec, def)
  cat(
    "[self-test] clean compare findings:", nrow(clean),
    if (nrow(clean) == 0) "(expected 0) OK\n" else "(UNEXPECTED)\n"
  )

  # inject drift into a COPY of the spec: change a length+label, drop a variable, and
  # corrupt a codelist NCI code (proves the CT drift check has teeth)
  bad <- spec
  bad$vars$length[1] <- bad$vars$length[1] + 7
  bad$vars$label[2] <- paste0(bad$vars$label[2], " XX")
  dropped <- bad$vars[nrow(bad$vars), ]
  bad$vars <- bad$vars[-nrow(bad$vars), ]
  bad$cl$cl_code[bad$cl$codelist == "CL.SEX"] <- "C99999"
  drift <- compare(bad, def)
  kinds <- sort(unique(paste(drift$attribute)))
  cat(
    "[self-test] drifted compare findings:", nrow(drift),
    "->", paste(kinds, collapse = ", "), "\n"
  )

  ok <- nrow(clean) == 0 && nrow(drift) >= 4 &&
    all(c("length", "label", "presence", "nci_codelist_code") %in% drift$attribute)
  cat(if (ok) {
    "[self-test] PASS: gate detects injected drift.\n"
  } else {
    "[self-test] FAIL: gate did not behave as expected.\n"
  })
  quit(status = if (ok) 0 else 1)
}

args <- commandArgs(TRUE)
if ("--self-test" %in% args) self_test() else run_gate()

#!/usr/bin/env Rscript
# =============================================================================
# build_spec_seed.R  --  ONE-TIME MIGRATION (run once, 2026-06-17)
# -----------------------------------------------------------------------------
# Seeds the authoritative ADaM specification workbook
#   00_specifications/ADaM_spec.xlsx
# in the CDISC / Pinnacle-21 metacore format, by parsing the *existing*
# 07_define_xml/define.xml directly (one row per dataset+variable, plus full
# value-level + where-clause + codelist + method metadata).
#
# WHY this exists and WHY it is a migration, not a generator:
#   Before this change the only "spec" was ADaM_Define_Extract.xlsx, generated
#   FROM define.xml on every build (audit finding C-4: a circular, zero-
#   verification inversion -- the spec could never disagree with the define it
#   was meant to govern). This script runs ONCE to bootstrap a real upstream
#   spec from the define content, after which:
#       * ADaM_spec.xlsx becomes the human-edited single source of truth;
#       * the define -> spec generator (generate_adam_specs.py) is RETIRED;
#       * define.xml is CHECKED AGAINST the spec (07_define_xml/
#         check_define_conformance.R), not the other way round;
#       * the spec is independently CHECKED AGAINST the produced ADaM data
#         (metatools, 03_validation_r/spec_data_checks.R).
#   Do NOT re-run this to "sync" the spec to the define -- that would re-create
#   the C-4 circularity. Edit ADaM_spec.xlsx by hand from here on.
# =============================================================================

suppressMessages({
  library(metacore)
  library(dplyr)
  library(tidyr)
  library(purrr)
  library(stringr)
  library(writexl)
  library(xml2)
})

root <- normalizePath(".")
define_path <- file.path(root, "07_define_xml", "define.xml")
out_path <- file.path(root, "00_specifications", "ADaM_spec.xlsx")
stopifnot(file.exists(define_path))
message("Seeding spec by direct parse of: ", define_path)

x <- read_xml(define_path)
ns <- xml_ns(x)
txt <- function(node, xp) {
  n <- xml_find_first(node, xp, ns)
  if (inherits(n, "xml_missing")) NA_character_ else xml_text(n)
}
attr1 <- function(node, xp, a) {
  n <- xml_find_first(node, xp, ns)
  if (inherits(n, "xml_missing")) NA_character_ else xml_attr(n, a)
}

# -- ItemDef lookup: OID -> metadata ------------------------------------------
itemdefs <- xml_find_all(x, ".//d1:ItemDef", ns)
idmap <- tibble(
  oid      = xml_attr(itemdefs, "OID"),
  name     = xml_attr(itemdefs, "Name"),
  type     = xml_attr(itemdefs, "DataType"),
  length   = suppressWarnings(as.integer(xml_attr(itemdefs, "Length"))),
  label    = vapply(itemdefs, txt, character(1), xp = "./d1:Description/d1:TranslatedText"),
  origin   = vapply(itemdefs, attr1, character(1), xp = "./def:Origin", a = "Type"),
  codelist = vapply(itemdefs, attr1, character(1), xp = "./d1:CodeListRef", a = "CodeListOID"),
  vlist    = vapply(itemdefs, attr1, character(1), xp = "./def:ValueListRef", a = "ValueListOID")
)
get_id <- function(oid) idmap[match(oid, idmap$oid), ]

# dataset/variable from OID convention IT.<DS>.<VAR>[.<WHERE>]
ds_from_oid <- function(oid) vapply(strsplit(oid, ".", fixed = TRUE), `[`, character(1), 2)
var_from_oid <- function(oid) vapply(strsplit(oid, ".", fixed = TRUE), `[`, character(1), 3)

# ============================================================== Study sheet ===
study <- tibble(
  Attribute = c(
    "StudyName", "StudyDescription", "ProtocolName",
    "StandardName", "StandardVersion", "Language"
  ),
  Value = c(
    "TROPIC / EFC6193",
    "Phase III, cabazitaxel (XRP6258) vs mitoxantrone in mCRPC",
    "EFC6193", "CDISC ADaM", "ADaMIG 1.3", "en"
  )
)

# =========================================================== Datasets sheet ===
igs <- xml_find_all(x, ".//d1:ItemGroupDef", ns)
datasets <- tibble(
  Dataset = xml_attr(igs, "Name"),
  Description = vapply(igs, txt, character(1), xp = "./d1:Description/d1:TranslatedText"),
  Class = vapply(igs, attr1, character(1), xp = "./def:Class", a = "Name"),
  Structure = xml_attr(igs, "Structure"), # def:Structure (xml2 matches by local name)
  Purpose = xml_attr(igs, "Purpose") |> coalesce("Analysis"),
  `Key Variables` = NA_character_, # define declares no keys; enrich in spec
  Repeating = ifelse(xml_attr(igs, "Repeating") %in% "Yes", "Yes", "No"),
  `Reference Data` = "No",
  Comment = NA_character_
)

# ========================================================== Variables sheet ===
var_rows <- map_dfr(seq_along(igs), function(i) {
  ds <- xml_attr(igs[[i]], "Name")
  refs <- xml_find_all(igs[[i]], "./d1:ItemRef", ns)
  tibble(
    Order     = suppressWarnings(as.integer(xml_attr(refs, "OrderNumber"))),
    Dataset   = ds,
    item_oid  = xml_attr(refs, "ItemOID"),
    Mandatory = ifelse(xml_attr(refs, "Mandatory") %in% "Yes", "Yes", "No"),
    Method    = xml_attr(refs, "MethodOID")
  )
})
vi <- get_id(var_rows$item_oid)
variables <- tibble(
  Order = var_rows$Order, Dataset = var_rows$Dataset, Variable = vi$name,
  Label = vi$label, `Data Type` = vi$type, Length = vi$length,
  `Significant Digits` = NA_integer_, Format = NA_character_,
  Mandatory = var_rows$Mandatory, Codelist = vi$codelist, Origin = vi$origin,
  Pages = NA_character_, Method = var_rows$Method,
  Predecessor = NA_character_, Role = NA_character_, Comment = NA_character_
)

# ========================================================= ValueLevel sheet ===
vls <- xml_find_all(x, ".//def:ValueListDef", ns)
value_level <- map_dfr(vls, function(vl) {
  vloid <- xml_attr(vl, "OID") # VL.<DS>.<VAR>
  parts <- strsplit(vloid, ".", fixed = TRUE)[[1]]
  ds <- parts[2]
  var <- parts[3]
  refs <- xml_find_all(vl, "./d1:ItemRef", ns)
  ii <- get_id(xml_attr(refs, "ItemOID"))
  tibble(
    Order = seq_along(refs), Dataset = ds, Variable = var,
    `Where Clause` = vapply(refs, attr1, character(1), xp = "./def:WhereClauseRef", a = "WhereClauseOID"),
    Description = ii$label, `Data Type` = ii$type, Length = ii$length,
    `Significant Digits` = NA_integer_, Format = NA_character_,
    Mandatory = ifelse(xml_attr(refs, "Mandatory") %in% "Yes", "Yes", "No"),
    Codelist = ii$codelist, Origin = ii$origin, Pages = NA_character_,
    Method = xml_attr(refs, "MethodOID"), Predecessor = NA_character_,
    Comment = NA_character_
  )
})

# ======================================================= WhereClauses sheet ===
wcs <- xml_find_all(x, ".//def:WhereClauseDef", ns)
where_clauses <- map_dfr(wcs, function(wc) {
  rc <- xml_find_first(wc, "./d1:RangeCheck", ns)
  toid <- xml_attr(rc, "ItemOID") # def:ItemOID (xml2 matches by local name)
  vals <- xml_text(xml_find_all(rc, "./d1:CheckValue", ns))
  tibble(
    ID = xml_attr(wc, "OID"), Dataset = ds_from_oid(toid),
    Variable = get_id(toid)$name %||% var_from_oid(toid),
    Comparator = xml_attr(rc, "Comparator"),
    Value = paste(vals, collapse = ", ")
  )
})
`%||%` <- function(a, b) ifelse(is.na(a), b, a)

# =========================================================== Codelists sheet ===
cls <- xml_find_all(x, ".//d1:CodeList", ns)
codelists <- map_dfr(cls, function(cl) {
  id <- xml_attr(cl, "OID")
  nm <- xml_attr(cl, "Name")
  dt <- xml_attr(cl, "DataType")
  items <- xml_find_all(cl, "./d1:CodeListItem", ns)
  enums <- xml_find_all(cl, "./d1:EnumeratedItem", ns)
  if (length(items)) {
    tibble(
      ID = id, Name = nm, `NCI Codelist Code` = NA_character_,
      `Data Type` = dt, Order = seq_along(items),
      Term = xml_attr(items, "CodedValue"), `NCI Term Code` = NA_character_,
      `Decoded Value` = vapply(items, txt, character(1),
        xp = "./d1:Decode/d1:TranslatedText"
      )
    )
  } else if (length(enums)) {
    cv <- xml_attr(enums, "CodedValue")
    tibble(
      ID = id, Name = nm, `NCI Codelist Code` = NA_character_,
      `Data Type` = dt, Order = seq_along(enums),
      Term = cv, `NCI Term Code` = NA_character_, `Decoded Value` = cv
    )
  } else {
    tibble()
  }
})

# ============================================================= Methods sheet ===
mds <- xml_find_all(x, ".//d1:MethodDef", ns)
methods <- tibble(
  ID = xml_attr(mds, "OID"), Name = xml_attr(mds, "Name"),
  Type = coalesce(xml_attr(mds, "Type"), "Computation"),
  Description = vapply(mds, txt, character(1), xp = "./d1:Description/d1:TranslatedText"),
  `Expression Context` = NA_character_, `Expression Code` = NA_character_,
  Document = NA_character_, Pages = NA_character_
)

# referential integrity: only reference IDs that exist
variables$Method[!variables$Method %in% methods$ID] <- NA_character_
variables$Codelist[!variables$Codelist %in% codelists$ID] <- NA_character_

dictionaries <- tibble(
  ID = character(), Name = character(),
  `Data Type` = character(), Dictionary = character(), Version = character()
)
comments <- tibble(
  ID = character(), Description = character(),
  Document = character(), Pages = character()
)
documents <- tibble(ID = character(), Title = character(), Href = character())

sheets <- list(
  Study = study, Datasets = datasets, Variables = variables,
  ValueLevel = value_level, WhereClauses = where_clauses, Codelists = codelists,
  Dictionaries = dictionaries, Methods = methods, Comments = comments,
  Documents = documents
)

dir.create(dirname(out_path), showWarnings = FALSE, recursive = TRUE)
write_xlsx(sheets, out_path)
message(
  "Wrote: ", out_path, "  (", nrow(variables), " variables, ",
  nrow(datasets), " datasets, ", nrow(value_level), " value-level, ",
  nrow(where_clauses), " where-clauses, ", nrow(codelists),
  " codelist terms, ", nrow(methods), " methods)"
)

# --------------------------------------------------- self-validating round-trip
message("\nValidating round-trip via spec_to_metacore() ...")
mc <- spec_to_metacore(out_path, verbose = "silent")
na_meta <- mc$var_spec %>% filter(is.na(type) | is.na(length))
stopifnot("all variables have type+length" = nrow(na_meta) == 0)
stopifnot("7 datasets" = nrow(mc$ds_spec) == 7)
message(
  "OK: parsed ", nrow(mc$ds_spec), " datasets / ", nrow(mc$ds_vars),
  " ds_vars / ", nrow(mc$var_spec), " var_spec rows; 0 NA type/length."
)

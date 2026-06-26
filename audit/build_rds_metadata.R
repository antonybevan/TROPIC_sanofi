#!/usr/bin/env Rscript
# Extract structural RDS metadata without reproducing subject-level values.

root <- normalizePath(".", mustWork = TRUE)
inventory <- read.csv(file.path(root, "audit", "file_inventory.csv"), stringsAsFactors = FALSE)
rel_paths <- inventory$path[grepl("\\.rds$", inventory$path, ignore.case = TRUE)]
paths <- file.path(root, rel_paths)
rows <- lapply(sort(paths), function(path) {
  rel <- substring(path, nchar(root) + 2L)
  out <- tryCatch({
    obj <- readRDS(path)
    dims <- dim(obj)
    data.frame(
      path = rel,
      object_class = paste(class(obj), collapse = "|"),
      rows = if (length(dims)) dims[[1L]] else length(obj),
      columns = if (length(dims) > 1L) dims[[2L]] else NA_integer_,
      column_names = if (!is.null(names(obj))) paste(names(obj), collapse = "|") else "",
      inspection = "Full deserialization and structure inspection; values not reproduced",
      status = "READABLE",
      stringsAsFactors = FALSE
    )
  }, error = function(e) data.frame(
    path = rel, object_class = "", rows = NA_integer_, columns = NA_integer_,
    column_names = "", inspection = "Deserialization attempted",
    status = paste("UNREADABLE:", conditionMessage(e)), stringsAsFactors = FALSE
  ))
  out
})
result <- do.call(rbind, rows)
write.csv(result, file.path(root, "audit", "rds_metadata.csv"), row.names = FALSE, na = "")
cat(sprintf("Inspected %d RDS files; failures=%d\n", nrow(result), sum(result$status != "READABLE")))

# Declarative CI-only R dependency inventory for renv discovery.
# This file is not executed as a test; the false branch keeps the lint dependency
# visible to renv without attaching it during clinical pipeline execution.
if (FALSE) {
  library(lintr)
}

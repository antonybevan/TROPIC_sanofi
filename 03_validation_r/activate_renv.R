# activate_renv.R
# Version: 2.0
# Author: Clinical Programming
# Date: 2026-05-23
# Description: Environmental manager for R validation packages, ensuring automated
#              self-healing installation of CRAN/Pharmaverse packages.

required_packages <- c("jsonlite", "dplyr", "haven", "lubridate", "ggplot2", "xportr", "logrx", "survival", "patchwork", "scales", "diffdf")
missing_packages <- required_packages[!(required_packages %in% rownames(installed.packages()))]

if (length(missing_packages) > 0) {
  cat("NOTE: [RENV] Installing missing validation packages:", paste(missing_packages, collapse = ", "), "\n")
  install.packages(missing_packages, repos = "https://cloud.r-project.org", dependencies = TRUE)
} else {
  cat("NOTE: [RENV] All required validation packages are already installed.\n")
}

cat("NOTE: [RENV] Environment activated successfully in R session.\n")

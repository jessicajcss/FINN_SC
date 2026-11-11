# R dependencies for the FINN Santa Catarina pipeline (R route).
# Run once with:  Rscript install_r_packages.R
#
# 'sf' needs the system libraries GDAL, GEOS and PROJ. On Debian/Ubuntu:
#   sudo apt-get install libgdal-dev libgeos-dev libproj-dev libudunits2-dev
# On macOS (Homebrew):  brew install gdal geos proj udunits
# On Windows, the CRAN binary of 'sf' bundles these.

pkgs <- c(
  "yaml",        # read config/config.yml
  "httr",        # FINN file download
  "fs",          # file-system helpers
  "readr",       # fast text I/O
  "data.table",  # fast fread/fwrite and aggregation
  "dplyr",       # data manipulation
  "stringr",     # string parsing of file names
  "purrr",       # functional iteration
  "tibble",
  "sf",          # spatial features (points, polygons, joins)
  "ggplot2",     # plots
  "scales",      # axis scaling
  "patchwork",   # multi-panel figures
  # analysis layer (R/analysis/kde_events.R):
  "spatstat.geom",    # point patterns, observation window
  "spatstat.explore"  # kernel density with edge correction, bandwidth selectors
)
# Versions used for the published results (2026-10-03): R 4.3.3, sf 1.0.15, spatstat.geom 3.2.8,
# spatstat.explore 3.2.5, ggplot2 3.4.4.

to_install <- pkgs[!(pkgs %in% rownames(installed.packages()))]
if (length(to_install)) {
  install.packages(to_install, repos = "https://cloud.r-project.org")
} else {
  message("All required R packages are already installed.")
}

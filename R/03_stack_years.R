# =============================================================================
# 03_stack_years.R  -  Stack SC-clipped point files across years/sensors/versions
# -----------------------------------------------------------------------------
# Step 4 (optional) of the FINN Santa Catarina pipeline.
# Combines all filtered_points_*_within_grid.csv files under data/interim/ into
# a single long table, tagging each row with year, sensor and version parsed
# from the file name. Useful for multi-year point-level analysis.
#
# 2026-10-03 review: duplicate guards - two input files resolving to the same
# (year, sensor, version) stop the run (the mechanism behind the 2011 MODIS
# v2.5 rows appearing twice in the old aggregated_emissions_all.csv), exact
# duplicate rows are dropped and repeated record keys are reported.
#
# Run from the project root:  Rscript R/03_stack_years.R
# =============================================================================

source("R/utils_finn.R")
.finn_require(c("purrr", "tibble"))
library(stringr); library(dplyr)
cfg <- finn_load_config()

files <- list.files(cfg$paths$interim,
                    pattern = "^filtered_points_\\d{4}_.+_within_grid\\.csv$",
                    full.names = TRUE)
if (length(files) == 0) {
  stop("No filtered_points_*_within_grid.csv files found in ", cfg$paths$interim,
       ". Run step 02 first.")
}

# 2026-10-03 review: one file per (year, sensor, version).
fkeys <- paste(str_extract(basename(files), "\\d{4}"),
               str_extract(basename(files), "MODIS\\+VIIRS|MODIS|VIIRS"),
               str_extract(basename(files), "v[0-9]+(\\.[0-9]+)*"))
if (anyDuplicated(fkeys)) {
  stop("Several input files map to the same (year, sensor, version): ",
       paste(basename(files)[fkeys %in% fkeys[duplicated(fkeys)]], collapse = ", "),
       ". Remove the extra file(s) to avoid double counting.")
}

stacked <- purrr::map_dfr(files, function(p) {
  fname   <- basename(p)
  df      <- drop_exact_duplicates(data.table::fread(p), label = fname)   # 2026-10-03 review
  df$year    <- as.integer(str_extract(fname, "\\d{4}"))
  df$sensor  <- str_extract(fname, "MODIS\\+VIIRS|MODIS|VIIRS")
  df$version <- str_extract(fname, "v[0-9]+(\\.[0-9]+)*")
  df$path    <- p
  df
})

fs::dir_create(cfg$paths$output)
out_path <- file.path(cfg$paths$output, "filtered_points_stacked.csv")
data.table::fwrite(stacked, out_path)
message("Stacked ", length(files), " files, ", nrow(stacked), " rows -> ", out_path)

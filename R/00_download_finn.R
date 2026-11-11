# =============================================================================
# 00_download_finn.R  -  Download & merge FINN fire-emission files
# -----------------------------------------------------------------------------
# Step 1 of the FINN Santa Catarina pipeline.
# Reads config/config.yml, builds the FINN download URLs for the requested
# year(s)/version/sensor, downloads them, merges and de-duplicates, and writes
# one combined CSV per year under data/raw_finn/.
#
# Run from the project root:  Rscript R/00_download_finn.R
# =============================================================================

source("R/utils_finn.R")
cfg <- finn_load_config()

sel      <- cfg$selection
bounds   <- finn_date_bounds(cfg)     # NULL unless start_date/end_date are set
years    <- selected_years(cfg)
all_urls <- build_finn_urls()

if (!is.null(bounds)) {
  message("Date selection: ", bounds$start, " .. ", bounds$end,
          "  (only the file(s) overlapping this range are downloaded)")
}

for (YEAR in years) {
  message("\n=== Downloading FINN ", sel$version, " / ", sel$sensor, " / ", YEAR, " ===")
  urls <- filter_finn_urls(all_urls, version = sel$version,
                           sensor = sel$sensor, year = YEAR)
  if (!is.null(bounds)) urls <- filter_finn_by_date(urls, bounds$start, bounds$end)
  if (length(urls) == 0) {
    message("No FINN files match this selection; skipping.")
    next
  }
  out_name <- sprintf("%d_finn_%s_%s.csv", YEAR, sel$version, sel$sensor)
  download_finn_files(
    url_list           = urls,
    dest_folder        = cfg$paths$raw_finn,
    combined_filename  = out_name,
    include_source_url = cfg$download$include_source_url,
    min_file_size_kb   = cfg$download$min_file_size_kb,
    timeout_seconds    = cfg$download$timeout_seconds)
}

message("\nStep 00 complete. Combined FINN files are in: ", cfg$paths$raw_finn)

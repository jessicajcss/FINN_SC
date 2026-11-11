# =============================================================================
# 04_aggregate_region.R  -  Emissions summed per region polygon
# -----------------------------------------------------------------------------
# Step 5 of the FINN pipeline. For every region-clipped point file (step 02),
# performs a point-in-polygon join against the boundaries shapefile
# (config: region$boundaries_shp), sums each FINN species by polygon (grouping
# on region$region_field), adds fire counts (2026-10-03 review: n_rows, events,
# detections - replacing the old row count `focos`), burned_km2 and NOx_as_NO2,
# stacks all years/sensors/versions, joins the totals back onto the polygon
# geometry, and writes:
#   - data/output/aggregated_emissions_all.shp   (for QGIS; 10-char field names)
#   - data/output/aggregated_emissions_all.csv   (tabular, full field names)
#
# Works for ANY polygon layer. Default: IBGE Santa Catarina municipalities
# (region_field = "NM_MUN"). For another region, set region$boundaries_shp and
# region$region_field in config. See data/inputs/README.
#
# 2026-10-03 review: duplicate guards - one input file per (year, sensor,
# version), exact duplicate rows dropped, and a final check that every
# (region, period, year, sensor, version) row is unique.
#
# Run from the project root:  Rscript R/04_aggregate_region.R
# =============================================================================

source("R/utils_finn.R")
.finn_require(c("sf", "dplyr", "stringr", "purrr"))
library(sf); library(dplyr); library(stringr)
cfg <- finn_load_config()

shp_path <- cfg$region$boundaries_shp
if (is.null(shp_path) || !file.exists(shp_path)) {
  stop("Boundaries shapefile not found at '", shp_path, "'. Place your region ",
       "shapefile there (default: IBGE SC municipalities; see data/inputs/README).")
}
shp <- st_read(shp_path, quiet = TRUE)
region_field <- cfg$region$region_field
if (!region_field %in% names(shp)) {
  stop("region$region_field '", region_field, "' not found in the shapefile. ",
       "Available columns: ", paste(names(shp), collapse = ", "))
}

# All region-clipped point files (any year/sensor/version).
files <- list.files(cfg$paths$interim,
                    pattern = "^filtered_points_\\d{4}_.+_within_grid\\.csv$",
                    full.names = TRUE)
if (length(files) == 0) {
  stop("No region-clipped point files found in ", cfg$paths$interim, ". Run step 02 first.")
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

process_one <- function(p) {
  fname   <- basename(p)
  year    <- as.integer(str_extract(fname, "\\d{4}"))
  sensor  <- str_extract(fname, "MODIS\\+VIIRS|MODIS|VIIRS")
  version <- str_extract(fname, "v[0-9]+(\\.[0-9]+)*")
  df <- drop_exact_duplicates(data.table::fread(p), label = fname)   # 2026-10-03 review
  if (!all(c("LONGI", "LATI") %in% names(df))) {
    warning("No coordinates in ", fname, "; skipping.")
    return(NULL)
  }
  aggregate_by_region(df, shp, cfg, year = year, sensor = sensor, version = version)
}

all_summaries <- purrr::map(files, process_one) |> purrr::compact() |> dplyr::bind_rows()

# 2026-10-03 review: final guard - each polygon/period/product appears once.
k <- c(region_field, "period", "year", "sensor", "version")
if (anyDuplicated(as.data.frame(all_summaries)[, k])) {
  stop("Duplicated (", paste(k, collapse = ", "), ") rows in the aggregated table.")
}

# Join totals back onto polygon geometry (one geometry, many year/sensor rows).
final_sf <- dplyr::left_join(shp, all_summaries, by = region_field) |> st_as_sf()

# --- Save CSV (full field names) ---
fs::dir_create(cfg$paths$output)
out_csv <- file.path(cfg$paths$output, "aggregated_emissions_all.csv")
data.table::fwrite(st_drop_geometry(final_sf), out_csv)
message("Saved: ", out_csv)

# --- Save shapefile (ESRI 10-char field-name limit) ---
final_shp <- final_sf
names(final_shp) <- substr(make.names(names(final_shp), unique = TRUE), 1, 10)
out_shp <- file.path(cfg$paths$output, "aggregated_emissions_all.shp")
st_write(final_shp, out_shp, delete_layer = TRUE, quiet = TRUE)
message("Saved: ", out_shp)

message("\nStep 04 complete. Region-level inventory written to ", cfg$paths$output)

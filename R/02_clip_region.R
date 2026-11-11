# =============================================================================
# 02_clip_region.R  -  Clip the global FINN cloud to the study region
# -----------------------------------------------------------------------------
# Step 3 of the FINN pipeline. Reads the unit-converted file(s) from step 01 and
# keeps only fire points inside the study-region bounding box.
#
# The bounding box comes from config (region$bbox):
#   auto  -> derived automatically from the boundaries shapefile's extent
#            (+ region$bbox_margin_deg). This makes the step work for ANY region.
#   none  -> no pre-filter (all points pass through; the polygon join in step 04
#            does the real "inside the region" test).
#   explicit degrees -> used as given.
#
# Default region: Santa Catarina (config default). Point `region$boundaries_shp`
# at any other shapefile to inventory a different state / country / polygon.
#
# 2026-10-03 review: after the bbox pre-filter, points are now also restricted
# to the study POLYGONS (point-in-polygon, st_within; see clip_to_region in
# utils_finn.R), so the filtered_points_*_within_grid.csv files and the stacked
# table of step 03 no longer contain points of neighbouring states/countries or
# the ocean. The boundaries shapefile is therefore required.
#
# Run from the project root:  Rscript R/02_clip_region.R
# =============================================================================

source("R/utils_finn.R")
cfg <- finn_load_config()
sel <- cfg$selection

# 2026-10-03 review: the shapefile is now REQUIRED (point-in-polygon clip).
shp_path <- cfg$region$boundaries_shp
if (is.null(shp_path) || !file.exists(shp_path)) {
  stop("Boundaries shapefile not found at '", shp_path, "'. Step 02 restricts ",
       "points to the study polygons, so the shapefile is required ",
       "(see data/inputs/README).")
}
.finn_require("sf")
shp <- sf::st_read(shp_path, quiet = TRUE)

for (YEAR in selected_years(cfg)) {
  in_path <- file.path(cfg$paths$interim,
                       sprintf("%d_finn_%s_%s_converted.csv", YEAR, sel$version, sel$sensor))
  if (!file.exists(in_path)) {
    message("Missing converted input for ", YEAR, " (", in_path, "); run step 01 first. Skipping.")
    next
  }
  message("Clipping ", YEAR, " to region '", cfg$region$name, "' ...")
  df <- data.table::fread(in_path)
  clipped <- clip_to_region(df, cfg, shp)   # 2026-10-03 review: bbox + polygons
  # File name kept for compatibility ("within_grid"); content is now in-polygon.

  out_path <- file.path(cfg$paths$interim,
                        sprintf("filtered_points_%d_%s_%s_converted_within_grid.csv",
                                YEAR, sel$sensor, sel$version))
  data.table::fwrite(clipped, out_path)
  message("  kept ", nrow(clipped), " of ", nrow(df), " records inside the region polygons -> ", out_path)
}

message("\nStep 02 complete. Region-clipped point files are in: ", cfg$paths$interim)

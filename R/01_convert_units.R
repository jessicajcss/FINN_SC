# =============================================================================
# 01_convert_units.R  -  Convert FINN native units to metric tonnes
# -----------------------------------------------------------------------------
# Step 2 of the FINN Santa Catarina pipeline.
# Reads the combined file(s) written by step 00, converts every emission
# column to tonnes (gases via molar mass; aerosols via kg/1000) and writes a
# *_converted.csv per year under data/interim/.
#
#   FINN native units (official README): gases in mole/day, aerosols in kg/day.
#   Conversion: gas  tonnes = mol * molar_mass[g/mol] / 1e6
#               solid tonnes = kg / 1000
#
# Run from the project root:  Rscript R/01_convert_units.R
# =============================================================================

source("R/utils_finn.R")
cfg <- finn_load_config()
sel <- cfg$selection
bounds <- finn_date_bounds(cfg)       # NULL unless start_date/end_date are set

for (YEAR in selected_years(cfg)) {
  in_path  <- file.path(cfg$paths$raw_finn,
                        sprintf("%d_finn_%s_%s.csv", YEAR, sel$version, sel$sensor))
  if (!file.exists(in_path)) {
    message("Missing input for ", YEAR, " (", in_path, "); run step 00 first. Skipping.")
    next
  }
  message("Converting units for ", YEAR, " ...")
  data <- tryCatch(data.table::fread(in_path), error = function(e) NULL)
  if (is.null(data) || nrow(data) == 0) {
    message("  ", basename(in_path), " is empty (no FINN files matched, or all ",
            "downloads 404'd for this selection). Nothing to convert; skipping. ",
            "Check config selection (version/sensor/dates) and the step 00 log.")
    next
  }
  converted <- convert_finn_units(data, cfg)

  # Keep only rows within the exact date range (adds a DATE column), if set.
  if (!is.null(bounds)) {
    converted <- filter_rows_by_date(converted, YEAR, bounds$start, bounds$end)
    message("  date-filtered to ", bounds$start, "..", bounds$end, ": ", nrow(converted), " rows")
  }

  fs::dir_create(cfg$paths$interim)
  out_path <- file.path(cfg$paths$interim,
                        sprintf("%d_finn_%s_%s_converted.csv", YEAR, sel$version, sel$sensor))
  data.table::fwrite(converted, out_path)
  message("  saved: ", out_path)
}

message("\nStep 01 complete. Unit-converted files are in: ", cfg$paths$interim)

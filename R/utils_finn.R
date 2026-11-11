# =============================================================================
# utils_finn.R  -  Shared helper functions for the FINN Santa Catarina pipeline
# -----------------------------------------------------------------------------
# Author : Santos-Silva, J. C. (jessica.jcss@gmail.com)
# Project: Inventario de Emissoes Atmosfericas de Santa Catarina (FAPESC)
#
# This file gathers the reusable functions that the numbered scripts
# (00_... to 05_...) source. It is a refactor of the author's original
# scripts (kept outside this repository) with the same logic, organised into
# documented functions and driven by config/config.yml.
#
# Data reference (official): Wiedinmyer et al., 2011 (FINNv1) and 2023 (FINNv2.5)
#   FINNv1   : https://doi.org/10.5194/gmd-4-625-2011
#   FINNv2.5 : https://doi.org/10.5194/gmd-16-3873-2023
#   Archive  : https://rda.ucar.edu/datasets/ds312-9/  (NSF NCAR RDA ds312.9)
# =============================================================================

# ---- Package bootstrap -------------------------------------------------------
# Install-on-demand so the scripts run on a fresh machine.
.finn_require <- function(pkgs) {
  for (p in pkgs) {
    if (!requireNamespace(p, quietly = TRUE)) {
      message("Installing missing package: ", p)
      install.packages(p, repos = "https://cloud.r-project.org")
    }
  }
}
.finn_require(c("yaml", "httr", "fs", "readr", "data.table", "dplyr", "stringr"))

# Null-coalescing helper.
`%||%` <- function(a, b) if (is.null(a)) b else a

# ---- Configuration -----------------------------------------------------------

#' Load the shared YAML configuration.
#' @param path Path to config.yml (default: config/config.yml under project root).
#' @return A named list mirroring config.yml.
finn_load_config <- function(path = "config/config.yml") {
  if (!file.exists(path)) {
    stop("Config file not found at '", path, "'. Run scripts from the project root.")
  }
  yaml::read_yaml(path)
}

# ---- 1. Build the catalogue of FINN download URLs ----------------------------

#' Build the full list of FINN file URLs across versions, sensors and years.
#'
#' Reproduces the URL templates published on the UCAR/ACOM and NSF NCAR RDA
#' servers for FINNv1.5, FINNv2.5 and FINNv2.5.1 (monthly + near-real-time daily).
#'
#' @param include_monthly Include the 2022-2023 monthly FINNv2.5.1 files.
#' @param include_daily   Include the 2024+ near-real-time daily files.
#' @return A list of URL descriptors, each a list(url, version, sensor,
#'   granularity, year[, month, day]).
build_finn_urls <- function(include_monthly = TRUE, include_daily = TRUE) {
  base_v1     <- "https://www.acom.ucar.edu/Data/fire/data/finn1"
  base_v25    <- "https://data-osdf.rda.ucar.edu/ncar/rda/d312009"
  base_v25nrt <- "https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt"

  urls <- list()

  # FINNv1.5 GEOS-CHEM, MODIS (2002-2020). Every year, 2002 included, is a .tar.gz archive; the earlier ".txt.gz"
  # address of 2002 returned 404 (corrected 11 Nov 2026). The FINN page (https://www.acom.ucar.edu/Data/fire/) asks
  # users to submit their name and contact information before downloading the FINN v1.5 files.
  for (year in 2002:2020) {
    suffix <- ".tar.gz"
    urls[[length(urls) + 1]] <- list(
      url = sprintf("%s/FINNv1.5_%d.GEOSCHEM%s", base_v1, year, suffix),
      version = "v1.5", sensor = "MODIS", granularity = "yearly", year = year)
  }

  # FINNv2.5 GEOS-CHEM, MODIS (2003-2021)
  for (year in 2003:2021) {
    suffix <- if (year == 2021) "c20221105" else "c20211213"
    urls[[length(urls) + 1]] <- list(
      url = sprintf("%s/%d_eachfire_modis/FINNv2.5_mod_GEOSCHEM_%d_%s.txt.gz",
                    base_v25, year, year, suffix),
      version = "v2.5", sensor = "MODIS", granularity = "yearly", year = year)
  }

  # FINNv2.5 GEOS-CHEM, MODIS+VIIRS (2012-2021)
  for (year in 2012:2021) {
    suffix <- if (year == 2021) "c20220714" else "c20211213"
    urls[[length(urls) + 1]] <- list(
      url = sprintf("%s/%d_eachfire_modisviirs/FINNv2.5_modvrs_GEOSCHEM_%d_%s.txt.gz",
                    base_v25, year, year, suffix),
      version = "v2.5", sensor = "MODIS+VIIRS", granularity = "yearly", year = year)
  }

  # FINNv2.5.1 monthly (2022-2023), MODIS and MODIS+VIIRS
  if (include_monthly) {
    for (i in 1:12) {
      urls[[length(urls) + 1]] <- list(
        url = sprintf("%s/2022_eachfire_modis/FINNv2.5.1_mod_GEOSCHEM_2022%02d_c20240525.txt.gz", base_v25, i),
        version = "v2.5.1", sensor = "MODIS", granularity = "monthly", year = 2022, month = i)
      urls[[length(urls) + 1]] <- list(
        url = sprintf("%s/2023_eachfire_modis/FINNv2.5.1_mod_GEOSCHEM_2023%02d_c20240621.txt.gz", base_v25, i),
        version = "v2.5.1", sensor = "MODIS", granularity = "monthly", year = 2023, month = i)
      urls[[length(urls) + 1]] <- list(
        url = sprintf("%s/2022_eachfire_modisviirs/FINNv2.5.1_modvrs_GEOSCHEM_2022%02d_c20240506.txt.gz", base_v25, i),
        version = "v2.5.1", sensor = "MODIS+VIIRS", granularity = "monthly", year = 2022, month = i)
      urls[[length(urls) + 1]] <- list(
        url = sprintf("%s/2023_eachfire_modisviirs/FINNv2.5.1_modvrs_GEOSCHEM_2023%02d_c20240521.txt.gz", base_v25, i),
        version = "v2.5.1", sensor = "MODIS+VIIRS", granularity = "monthly", year = 2023, month = i)
    }
  }

  # FINNv2.5.1 near-real-time (NRT) daily (2024-present), MODIS+VIIRS.
  # File name is always FINNv2.5.1_modvrs_nrt_GEOSCHEM_<YYYYMMDD>.txt.gz, but
  # UCAR moves files between two spots over time (verified on the live index):
  #   * the CURRENT year's files sit directly in .../finn_emis_txt/
  #   * PAST years are archived into a per-year folder .../FINN2nrt_<year>/
  # The split shifts at each year rollover, so every NRT date carries BOTH
  # candidate URLs and the downloader uses whichever responds. NRT is a rolling
  # product: very old dates may 404 once finalized - those are skipped cleanly.
  if (include_daily) {
    current_year <- as.integer(format(Sys.Date(), "%Y"))
    for (year in 2024:current_year) {
      leap <- (year %% 4 == 0 & year %% 100 != 0) | (year %% 400 == 0)
      days_in_year <- if (leap) 366 else 365
      for (day in 1:days_in_year) {
        date  <- format(as.Date(day - 1, origin = paste0(year, "-01-01")), "%Y%m%d")
        month <- as.integer(substr(date, 5, 6))
        root   <- sprintf("%s/FINNv2.5.1_modvrs_nrt_GEOSCHEM_%s.txt.gz", base_v25nrt, date)
        folder <- sprintf("%s/FINN2nrt_%d/FINNv2.5.1_modvrs_nrt_GEOSCHEM_%s.txt.gz", base_v25nrt, year, date)
        candidates <- if (year == current_year) list(root, folder) else list(folder, root)
        urls[[length(urls) + 1]] <- list(
          url = candidates[[1]], url_candidates = candidates,
          version = "v2.5.1", sensor = "MODIS+VIIRS",
          granularity = "daily", year = year, month = month,
          day = as.integer(substr(date, 7, 8)))
      }
    }
  }
  urls
}

#' Filter the URL catalogue by version / sensor / year.
filter_finn_urls <- function(urls, version = NULL, sensor = NULL, year = NULL) {
  Filter(function(u) {
    (is.null(version) || u$version %in% version) &&
    (is.null(sensor)  || u$sensor  %in% sensor)  &&
    (is.null(year)    || u$year    %in% year)
  }, urls)
}

# ---- 1b. Optional exact date-range selection ---------------------------------

#' Effective (start, end) dates from config, or NULL if not in date mode.
#' `start_date` alone -> a single day (end = start). Both set -> a range.
finn_date_bounds <- function(cfg) {
  sd <- cfg$selection$start_date
  if (is.null(sd) || !nzchar(as.character(sd))) return(NULL)
  ed <- cfg$selection$end_date
  if (is.null(ed) || !nzchar(as.character(ed))) ed <- sd
  list(start = as.character(sd), end = as.character(ed))
}

#' Years to process: the span of the date range if set, else selection$years.
selected_years <- function(cfg) {
  b <- finn_date_bounds(cfg)
  if (is.null(b)) return(cfg$selection$years)
  seq(as.integer(format(as.Date(b$start), "%Y")),
      as.integer(format(as.Date(b$end),   "%Y")))
}

#' Keep only URL descriptors whose period overlaps [start, end].
#'   daily   : the exact date is within the range;
#'   monthly : the (year, month) overlaps the range;
#'   yearly  : the year is within the range (a whole-year file is the only option).
filter_finn_by_date <- function(urls, start_date, end_date) {
  s <- as.Date(start_date); e <- as.Date(end_date)
  ys <- as.integer(format(s, "%Y")); ye <- as.integer(format(e, "%Y"))
  Filter(function(u) {
    g <- u$granularity %||% "yearly"
    if (identical(g, "daily")) {
      d <- as.Date(sprintf("%04d-%02d-%02d", u$year, u$month, u$day))
      !is.na(d) && d >= s && d <= e
    } else if (identical(g, "monthly")) {
      m_start <- as.Date(sprintf("%04d-%02d-01", u$year, u$month))
      m_end   <- seq(m_start, by = "month", length.out = 2)[2] - 1
      m_start <= e && m_end >= s
    } else {
      u$year >= ys && u$year <= ye
    }
  }, urls)
}

#' Add a DATE column (from DAY-of-year + year) and keep rows within [start, end].
filter_rows_by_date <- function(df, year, start_date, end_date) {
  df$DATE <- as.Date(as.integer(df$DAY) - 1, origin = paste0(year, "-01-01"))
  keep <- !is.na(df$DATE) & df$DATE >= as.Date(start_date) & df$DATE <= as.Date(end_date)
  df[keep, ]
}

# ---- 2. Download and combine -------------------------------------------------

# Fixed column names for the FINNv1.5 GEOS-CHEM files, whose headers are not
# self-describing. Order matches the released files.
FINN_V15_COLNAMES <- c(
  "DAY", "TIME", "GENVEG", "LATI", "LONGI", "AREA", "CO2", "CO", "NO", "NO2",
  "SO2", "NH3", "CH4", "ACET", "ALD2", "ALK4", "BENZ", "C2H2", "C2H4", "C2H6",
  "C3H8", "CH2O", "GLYC", "GLYX", "HAC", "MEK", "MGLY", "PRPE", "TOLU", "XYLE",
  "OC", "BC", "PM25")

#' Read the text lines of a downloaded FINN file.
#'
#' Handles both distribution formats: plain gzipped text (.txt.gz, v2.5/2.5.1)
#' and gzipped tar archives (.tar.gz, FINNv1.5 annual files, which extract to a
#' folder containing the emissions .txt). Detected via the 'ustar' tar magic at
#' offset 257 of the decompressed stream.
#' @return character vector of lines (character(0) if nothing readable).
.finn_read_lines <- function(path) {
  con_hdr <- gzfile(path, "rb")
  hdr <- readBin(con_hdr, "raw", n = 300)
  close(con_hdr)
  is_tar <- length(hdr) >= 262 && identical(rawToChar(hdr[258:262]), "ustar")
  if (is_tar) {
    exdir <- tempfile(); dir.create(exdir)
    on.exit(unlink(exdir, recursive = TRUE), add = TRUE)
    utils::untar(path, exdir = exdir)
    txts <- list.files(exdir, pattern = "\\.(txt|csv)$", recursive = TRUE, full.names = TRUE)
    if (length(txts) == 0) txts <- list.files(exdir, recursive = TRUE, full.names = TRUE)
    if (length(txts) == 0) return(character(0))
    txt <- txts[which.max(file.info(txts)$size)]   # emissions table = largest file
    readLines(txt, warn = FALSE)
  } else {
    con_in <- gzfile(path, "rt")
    on.exit(close(con_in), add = TRUE)
    readLines(con_in, warn = FALSE)
  }
}

#' Download a list of FINN files, combine them and de-duplicate rows.
#'
#' Handles the FINNv1.5 header quirk (fixed column names) and, for v2.5+,
#' optionally records the source URL as a provenance column.
#'
#' @param url_list         Output of filter_finn_urls().
#' @param dest_folder      Where to write the combined file.
#' @param combined_filename Output file name (.csv).
#' @param include_source_url Prepend a source_url column (v2.5+ only).
#' @param min_file_size_kb Skip files smaller than this.
#' @param timeout_seconds  Per-file HTTP timeout.
#' @return Path to the combined file.
download_finn_files <- function(url_list,
                                dest_folder = "data/raw_finn",
                                combined_filename = "combined_finn.csv",
                                include_source_url = TRUE,
                                min_file_size_kb = 0.5,
                                timeout_seconds = 600) {
  fs::dir_create(dest_folder)
  combined_path <- file.path(dest_folder, combined_filename)
  tmp_combined  <- tempfile(fileext = ".csv")
  con_out <- file(tmp_combined, "wt")
  header_written <- FALSE

  for (u in url_list) {
    # A descriptor may offer several candidate URLs for the same file
    # (e.g. NRT root vs FINN2nrt_<year>/ folder); use whichever responds.
    candidates <- if (!is.null(u$url_candidates)) u$url_candidates else list(u$url)
    filename <- basename(candidates[[1]])
    message("Processing: ", filename)
    added <- FALSE
    for (cand in candidates) {
      tmp_file <- tempfile(fileext = ".gz")
      ok <- tryCatch({
        resp <- httr::GET(cand, httr::write_disk(tmp_file, overwrite = TRUE),
                          httr::timeout(timeout_seconds))
        file_size_kb <- file.info(tmp_file)$size / 1024
        status_ok <- !is.na(httr::status_code(resp)) && httr::status_code(resp) == 200
        if (!status_ok || is.na(file_size_kb) || file_size_kb < min_file_size_kb) {
          FALSE
        } else {
          lines <- .finn_read_lines(tmp_file)   # handles .txt.gz and .tar.gz (v1.5)
          if (length(lines) == 0) {
            message("  empty file: ", filename); FALSE
          } else {
            is_v15      <- !is.null(u$version) && u$version == "v1.5"
            header      <- lines[1]
            data_lines  <- lines[-1]
            if (!header_written) {
              if (is_v15) {
                writeLines(paste(FINN_V15_COLNAMES, collapse = ","), con_out)
              } else {
                # Prepend provenance with a COMMA (not a tab) so the combined
                # file stays a clean, single-delimiter CSV. FINN GEOS-CHEM text
                # files are comma-delimited (see the official FINN README).
                final_header <- if (include_source_url) paste("source_url", header, sep = ",") else header
                writeLines(final_header, con_out)
              }
              header_written <- TRUE
            }
            if (is_v15) {
              writeLines(data_lines, con_out)
            } else {
              final_data <- if (include_source_url) paste(cand, data_lines, sep = ",") else data_lines
              writeLines(final_data, con_out)
            }
            message("  added: ", filename); TRUE
          }
        }
      }, error = function(e) {
        message("  FAILED: ", cand, " - ", conditionMessage(e)); FALSE
      })
      if (file.exists(tmp_file)) file.remove(tmp_file)
      if (isTRUE(ok)) { added <- TRUE; break }
    }
    if (!added) message("  skipped (not available / too small): ", filename)
  }
  close(con_out)

  all_lines <- readr::read_lines(tmp_combined)
  if (length(all_lines) > 1) {
    readr::write_lines(c(all_lines[1], unique(all_lines[-1])), combined_path)
    message("Deduplicated and saved: ", combined_path)
  } else {
    readr::write_lines(all_lines, combined_path)
    message("No data rows; header only written: ", combined_path)
  }
  file.remove(tmp_combined)
  combined_path
}

# ---- 3. Unit conversion ------------------------------------------------------

#' Convert FINN native emission units to metric tonnes.
#'
#' Gas-phase species (in mol/day) -> tonnes via molar mass:  mol * g/mol / 1e6.
#' Aerosols / mass species (in kg/day) -> tonnes via  kg / 1000.
#' Columns not present in `data` are silently skipped.
#' 2026-10-03 review: NOXasNO, NMOC and NMHC are kg/day MASS fields in the
#' v2.5/v2.5.1 files (implied EFs match Wiedinmyer et al. 2023, Table 4); NMHC
#' was previously converted as a gas (x 72 g/mol), i.e. 13.9x too low. The lists
#' and the corrected molar masses (GLYC, GLYX, HAC, MGLY, H2) are in config.yml.
#'
#' @param data A data.frame/data.table of FINN emissions.
#' @param cfg  The loaded config list (for molar masses and mass-species list).
#' @return `data` with the emission columns rescaled to tonnes.
convert_finn_units <- function(data, cfg) {
  molar <- unlist(cfg$conversion$molar_mass_g_per_mol)
  mass_species <- unlist(cfg$conversion$mass_species_kg)
  # 2026-10-03 review: strip padded header names (FINN writes e.g. " ACET").
  data.table::setnames(data, trimws(names(data)))
  # 2026-10-03 review: a species in both lists would be converted twice.
  both <- intersect(mass_species, names(molar))
  if (length(both)) stop("Species listed both as kg/day and mol/day in config: ",
                         paste(both, collapse = ", "))

  for (col in mass_species) {
    if (col %in% names(data)) data[[col]] <- data[[col]] / 1000
  }
  for (col in names(molar)) {
    if (col %in% names(data)) data[[col]] <- data[[col]] * as.numeric(molar[[col]]) / 1e6
  }
  data
}

# ---- 4. Spatial clip to the study-region bounding box ------------------------

#' Resolve the bounding box for the study region.
#'
#' Three config modes for `region$bbox`:
#'   * list(lon_min,lon_max,lat_min,lat_max) -> used as given (explicit);
#'   * "auto" (or unset) -> derived from the shapefile extent (reprojected to
#'       EPSG:4326) plus region$bbox_margin_deg; requires `shp`;
#'   * "none" -> returns NULL (caller skips the pre-filter).
#' @param cfg loaded config list.
#' @param shp optional sf polygons (required when bbox = "auto").
#' @return list(lon_min,lon_max,lat_min,lat_max) or NULL.
resolve_bbox <- function(cfg, shp = NULL) {
  b <- cfg$region$bbox
  if (is.list(b) && all(c("lon_min", "lon_max", "lat_min", "lat_max") %in% names(b))) {
    return(b[c("lon_min", "lon_max", "lat_min", "lat_max")])
  }
  if (is.character(b) && tolower(b) == "none") return(NULL)
  # "auto" (or unset): derive from the shapefile extent + margin.
  if (is.null(shp)) {
    stop("region$bbox is 'auto' but no shapefile was supplied. Pass the ",
         "boundaries shapefile, or set an explicit bbox / 'none' in config.")
  }
  .finn_require("sf")
  bb <- sf::st_bbox(sf::st_transform(shp, 4326))
  m  <- cfg$region$bbox_margin_deg %||% 0
  list(lon_min = unname(bb["xmin"]) - m, lon_max = unname(bb["xmax"]) + m,
       lat_min = unname(bb["ymin"]) - m, lat_max = unname(bb["ymax"]) + m)
}

#' 2026-10-03 review: bbox pre-filter + point-in-polygon clip.
#'
#' Returns the rows of `df` whose point (LONGI, LATI) lies inside at least one
#' polygon of `shp` (st_within, planar test as in GEOS/geopandas so that the R
#' and Python routes agree). Each row is returned at most once. A bounding box
#' alone also keeps points of neighbouring states/countries and the ocean.
clip_to_region <- function(df, cfg, shp) {
  if (is.null(shp)) stop("clip_to_region needs the boundaries shapefile ",
                         "(region$boundaries_shp): points must be restricted to ",
                         "the study polygons, not only to the bounding box.")
  .finn_require("sf")
  pre <- clip_to_bbox(df, cfg, shp = shp)
  if (nrow(pre) == 0) return(pre)
  old_s2 <- sf::sf_use_s2()
  suppressMessages(sf::sf_use_s2(FALSE))
  on.exit(suppressMessages(sf::sf_use_s2(old_s2)), add = TRUE)
  pts <- sf::st_as_sf(data.frame(LONGI = pre$LONGI, LATI = pre$LATI),
                      coords = c("LONGI", "LATI"), crs = cfg$region$crs_epsg)
  if (sf::st_crs(pts) != sf::st_crs(shp)) pts <- sf::st_transform(pts, sf::st_crs(shp))
  inside <- lengths(suppressMessages(sf::st_within(pts, shp))) > 0
  pre[inside, ]
}

#' Keep only FINN points inside the study-region bounding box.
#'
#' Cheap pre-filter before the point-in-polygon join. If the resolved bbox is
#' NULL (config bbox = "none"), the data is returned unchanged.
#' @param df  data.frame / data.table with LONGI / LATI columns.
#' @param cfg loaded config list.
#' @param shp optional sf polygons (used when region$bbox = "auto").
#' @return the rows of `df` whose LONGI/LATI fall inside the bbox.
#'
#' Performance: FINN coordinates are native lon/lat (EPSG:4326) and the bbox is
#' an axis-aligned lon/lat rectangle, so a vectorised coordinate comparison is
#' EXACT and far faster than building sf points and running st_within over the
#' whole (global) cloud - the original bottleneck. Precise polygon membership is
#' still tested later, in step 04 (aggregate_by_region).
clip_to_bbox <- function(df, cfg, shp = NULL) {
  bb <- resolve_bbox(cfg, shp)
  if (is.null(bb)) return(df)                  # bbox: none -> no pre-filter
  keep <- df$LONGI >= bb$lon_min & df$LONGI <= bb$lon_max &
          df$LATI  >= bb$lat_min & df$LATI  <= bb$lat_max
  keep[is.na(keep)] <- FALSE
  df[keep, ]
}

# ---- 5. Aggregate emissions by region polygon --------------------------------

# Canonical FINN emission species (gases + aerosols + aggregate masses). Only
# these numeric columns are summed, so arbitrary numeric attributes carried by
# the boundary shapefile (population, area, codes, ...) are never mistaken for
# emissions. Covers all FINN versions/mechanisms used by this pipeline.
FINN_SPECIES <- c(
  "CO2", "CO", "CH4", "H2", "SO2", "NH3", "NO", "NO2", "NMHC", "NMOC", "NOXasNO",
  "ACET", "ALD2", "ALK4", "BENZ", "C2H2", "C2H4", "C2H6", "C3H8", "CH2O", "GLYC",
  "GLYX", "HAC", "MEK", "MGLY", "PRPE", "TOLU", "XYLE", "OC", "BC", "PM25",
  "PM10", "TPM", "TPC")

#' 2026-10-03 review: duplicate-row guard.
#' Drops exact duplicate rows (reporting how many) and REPORTS - but keeps -
#' rows sharing the record key (source_url, DAY, POLYID, FIREID, GENVEG) while
#' differing in other fields: FINN files legitimately contain such records (on
#' the SC 2003-2025 records: 26,197 rows in 12,907 key groups, all with
#' different AREA), so that key is NOT unique and must not be used to dedupe.
drop_exact_duplicates <- function(df, label = "") {
  n0 <- nrow(df)
  df <- df[!duplicated(df), ]
  if (n0 - nrow(df) > 0)
    message("  [dup-guard] ", label, ": dropped ", n0 - nrow(df), " exact duplicate row(s)")
  key <- intersect(c("source_url", "DAY", "POLYID", "FIREID", "GENVEG"), names(df))
  if (all(c("POLYID", "FIREID") %in% key)) {
    kd <- as.data.frame(df)[, key, drop = FALSE]
    n_key <- sum(duplicated(kd) | duplicated(kd, fromLast = TRUE))
    if (n_key > 0)
      message("  [dup-guard] ", label, ": ", n_key, " row(s) share a (",
              paste(key, collapse = ", "), ") key with another row but differ in ",
              "other fields; kept (distinct FINN records).")
  }
  df
}

#' 2026-10-03 review: fire `events` and `detections` per region polygon.
#'   events     = distinct (year, sensor, version, DAY, POLYID)  (FINN daily
#'                burned-area polygon; may hold several points)
#'   detections = distinct (year, sensor, version, DAY, FIREID)  (one point)
#' Each unit is assigned to ONE polygon: the one holding the largest summed
#' AREA of its in-region rows (ties -> first polygon name in C-locale order,
#' as in the Python route), so per-polygon counts add up to the regional total.
#' Returns NULL when POLYID/FIREID are absent (FINN v1.5).
count_fire_units <- function(jd, region_field,
                             group_cols = c("period", "year", "sensor", "version")) {
  need <- c("DAY", "POLYID", "FIREID", region_field, group_cols)
  if (nrow(jd) == 0 || !all(need %in% names(jd)) || all(is.na(jd$POLYID))) return(NULL)
  d <- as.data.frame(jd)[, c(region_field, group_cols, "DAY", "POLYID", "FIREID"), drop = FALSE]
  d$AREA_w <- if ("AREA" %in% names(jd)) suppressWarnings(as.numeric(jd$AREA)) else 0
  d$AREA_w[is.na(d$AREA_w)] <- 0
  res <- NULL
  for (u in list(c("events", "POLYID"), c("detections", "FIREID"))) {
    unit <- u[1]; idcol <- u[2]
    key <- c("year", "sensor", "version", "DAY", idcol)
    s <- d[!is.na(d[[idcol]]), , drop = FALSE] |>
      dplyr::group_by(dplyr::across(dplyr::all_of(c(key, "period", region_field)))) |>
      dplyr::summarise(AREA_w = sum(AREA_w), .groups = "drop") |>
      as.data.frame()
    ord <- do.call(order, c(unname(as.list(s[key])),
                            list(-s$AREA_w, s[[region_field]], method = "radix")))
    s <- s[ord, , drop = FALSE]
    s <- s[!duplicated(s[key]), , drop = FALSE]
    cnt <- s |>
      dplyr::count(dplyr::across(dplyr::all_of(c(region_field, group_cols))), name = unit)
    res <- if (is.null(res)) cnt else dplyr::full_join(res, cnt, by = c(region_field, group_cols))
  }
  # a polygon can hold a detection whose event is assigned to a neighbour -> 0, not NA
  res$events[is.na(res$events)] <- 0L
  res$detections[is.na(res$detections)] <- 0L
  res
}

#' Join emission points to the region polygons and sum by polygon.
#'
#' Generic: groups by cfg$region$region_field (a municipality, country, admin
#' unit, ... - whatever attribute your shapefile uses). Only known FINN species
#' (FINN_SPECIES) are summed.
#' 2026-10-03 review: the old `focos` (= number of ROWS, i.e. FIREID x GENVEG
#' pieces, not fires) is replaced by n_rows (diagnostic), events and detections
#' (see count_fire_units); burned_km2 = sum(AREA)/1e6 is added (the shapefile's
#' AREA_KM2 is the polygon's own area, NOT burned area); NOx_as_NO2 =
#' NOXasNO * 46.0055/30.0061 is added when cfg$derived$nox_as_no2 is TRUE.
#'
#' @param df  Converted, region-clipped emissions (LONGI/LATI columns).
#' @param shp An sf object of the region polygons (ANY polygon layer).
#' @param cfg loaded config list.
#' @param year,sensor,version Metadata attached to the summary.
#' @return A tibble: one row per polygon x period with n_rows, events,
#'   detections, burned_km2 and summed emissions per pollutant.
aggregate_by_region <- function(df, shp, cfg, year = NA, sensor = NA, version = NA) {
  .finn_require(c("sf", "dplyr"))
  region_field <- cfg$region$region_field
  if (!region_field %in% names(shp)) {
    stop("region_field '", region_field, "' not found in the shapefile. ",
         "Set region$region_field in config to one of: ",
         paste(names(shp), collapse = ", "))
  }
  tr <- cfg$aggregation$time_resolution %||% "year"   # "day" | "month" | "year"
  # 2026-10-03 review: planar point-in-polygon with st_within (the default
  # st_intersects assigned a point lying on a shared border to BOTH polygons;
  # s2 off so R matches the GEOS test used by geopandas in the Python route).
  old_s2 <- sf::sf_use_s2()
  suppressMessages(sf::sf_use_s2(FALSE))
  on.exit(suppressMessages(sf::sf_use_s2(old_s2)), add = TRUE)
  df <- as.data.frame(df)
  df$.rid <- seq_len(nrow(df))
  emiss_sf <- sf::st_as_sf(df, coords = c("LONGI", "LATI"), crs = cfg$region$crs_epsg)
  if (sf::st_crs(emiss_sf) != sf::st_crs(shp)) {
    emiss_sf <- sf::st_transform(emiss_sf, crs = sf::st_crs(shp))
  }
  # 2026-10-03 review: join ONLY the grouping attribute (shapefile columns such
  # as AREA_KM2 must never be summed or clash with FINN fields).
  joined  <- suppressMessages(sf::st_join(emiss_sf, shp[, region_field],
                                          join = sf::st_within, left = FALSE))
  jd <- sf::st_drop_geometry(joined)
  dup_pt <- duplicated(jd$.rid)
  if (any(dup_pt)) {
    warning(sum(dup_pt), " point(s) fall in more than one polygon; each is kept once (first match).")
    jd <- jd[!dup_pt, , drop = FALSE]
  }
  jd$.rid <- NULL
  present <- intersect(FINN_SPECIES, names(jd))

  # Temporal bucket `period` from DAY-of-year + year, at the chosen resolution.
  if (tr %in% c("day", "month") && "DAY" %in% names(jd)) {
    d <- suppressWarnings(as.Date(as.integer(jd$DAY) - 1, origin = paste0(year, "-01-01")))
    jd$period <- if (tr == "day") format(d, "%Y-%m-%d") else format(d, "%Y-%m")
    jd$period[is.na(jd$period)] <- as.character(year)
  } else {
    jd$period <- as.character(year)                    # "year" resolution (default)
  }
  jd$year <- year; jd$sensor <- sensor; jd$version <- version

  gcols <- c(region_field, "period", "year", "sensor", "version")
  # 2026-10-03 review: burned area from FINN AREA (m2 -> km2).
  if ("AREA" %in% names(jd)) jd$burned_km2 <- suppressWarnings(as.numeric(jd$AREA)) / 1e6
  sum_cols <- c(present, intersect("burned_km2", names(jd)))
  out <- jd |>
    dplyr::group_by(dplyr::across(dplyr::all_of(gcols))) |>
    dplyr::summarise(n_rows = dplyr::n(),
                     dplyr::across(dplyr::all_of(sum_cols), \(x) sum(x, na.rm = TRUE)),
                     .groups = "drop")
  units <- count_fire_units(jd, region_field)
  if (!is.null(units)) {
    out <- dplyr::left_join(out, units, by = gcols)
    out$events[is.na(out$events)] <- 0L
    out$detections[is.na(out$detections)] <- 0L
  } else {                                   # FINN v1.5: no POLYID / FIREID
    out$events <- NA_integer_
    out$detections <- NA_integer_
  }
  if ("NOXasNO" %in% names(out) && isTRUE(cfg$derived$nox_as_no2 %||% TRUE)) {
    out$NOx_as_NO2 <- out$NOXasNO * 46.0055 / 30.0061   # NOx as NO2-equivalent mass
  }
  dplyr::relocate(out, dplyr::any_of(c("n_rows", "events", "detections", "burned_km2")),
                  .after = "version")
}

# Backward-compatible alias (earlier scripts/notebooks referenced this name).
aggregate_by_municipality <- aggregate_by_region

message("utils_finn.R loaded: ",
        paste(c("build_finn_urls", "filter_finn_urls", "download_finn_files",
                "convert_finn_units", "resolve_bbox", "clip_to_bbox",
                "clip_to_region", "drop_exact_duplicates", "count_fire_units",
                "aggregate_by_region"),
              collapse = ", "))

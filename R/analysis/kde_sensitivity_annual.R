#!/usr/bin/env Rscript
# =============================================================================
# R/analysis/kde_sensitivity_annual.R  (co-authors' review of 2026-10-19)
# Run from the project root:  Rscript R/analysis/kde_sensitivity_annual.R
#
# Two analyses requested by the co-authors on manuscript v.6 (comments C10, C23 and C24):
#  A. Bandwidth sensitivity by mesoregion (2025). For every bandwidth of the sensitivity analysis of
#     kde_events.R (likelihood cross-validation, Cronie-van Lieshout, Scott, Diggle and fixed 2, 4 and 8 km),
#     the mean density of each mesoregion and its share of the pixels in the top 10% and top 1% of the density
#     distribution. Question: does the Serrana remain the area of highest density with other bandwidths?
#  B. Annual kernel densities, 2012-2025, with ONE fixed bandwidth (the 2025 likelihood cross-validation value,
#     2774.1 m), so that the maps of different years are comparable; the year's own cross-validation bandwidth is
#     also computed and reported. Same estimator as kde_events.R: events = distinct (year, DAY, POLYID) of the FINN
#     MODIS+VIIRS records inside SC, centroid of the event's detections, persistent thermal anomalies screened
#     (>= 16 distinct days within 1 km in the year), isotropic Gaussian kernel in SIRGAS 2000 / UTM 22S, SC polygon
#     as window, Jones-Diggle edge correction, 1 km pixels, density in events per 100 km2.
#
# Inputs : data/derived/finn_sc_records_2003_2025.csv.gz; data/inputs/SC_Municipios_2024.shp;
#          data/external/sc_municipios_2024_atributos.csv
# Outputs: results/tables/kde_2025_sensitivity_mesoregion.csv   (A)
#          results/tables/kde_annual_summary.csv                (B; one row per year x mesoregion)
#          results/tables/kde_annual_grid.csv.gz                (B; pixel densities of every year, fixed sigma)
#          results/logs/kde_sensitivity_annual.txt
# The figure with the 14 annual maps is drawn by python/analysis/a11_coauthor_review.py (Figure S3).
# Packages: sf, spatstat.geom, spatstat.explore (as kde_events.R).
# =============================================================================

RECORDS  <- "data/derived/finn_sc_records_2003_2025.csv.gz"
SHP      <- "data/inputs/SC_Municipios_2024.shp"
SHP_ENC  <- "LATIN1"
MESO     <- "data/external/sc_municipios_2024_atributos.csv"
OUTDIR   <- "results/tables"
EPSG_M   <- 31982
PIXEL    <- 1000
R_SCREEN <- 1000
MIN_DAYS <- 16
YEARS    <- 2012:2025
SIGMA_FIXED_ANNUAL <- 2774.1   # 2025 likelihood cross-validation bandwidth (results/tables/kde_2025_bandwidths.csv)
SENS_2025 <- c(ppl = 2774.1, CvL = 8757.5, scott = 21719, diggle = 754.7,
               fixed_2km = 2000, fixed_4km = 4000, fixed_8km = 8000)   # values of kde_2025_bandwidths.csv
PPL_EACH_YEAR <- FALSE   # TRUE: also compute each year's own likelihood cross-validation bandwidth (about 8 min per year)
# part to run: Rscript R/analysis/kde_sensitivity_annual.R [A|B|all]   (default: all)
PART <- toupper(if (length(commandArgs(TRUE))) commandArgs(TRUE)[1] else "ALL")

suppressPackageStartupMessages({
  for (p in c("sf", "spatstat.geom", "spatstat.explore"))
    if (!requireNamespace(p, quietly = TRUE)) stop("install.packages('", p, "') first")
  library(sf); library(spatstat.geom); library(spatstat.explore)
})
sf_use_s2(FALSE)
if (!isTRUE(l10n_info()[["UTF-8"]]))
  for (loc in c("C.UTF-8", "C.utf8", "en_US.UTF-8", "en_US.utf8")) if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", loc)))) break
log_lines <- character()
say <- function(...) { s <- paste0(...); cat(s, "\n"); log_lines <<- c(log_lines, s) }

mun   <- st_make_valid(st_read(SHP, quiet = TRUE, options = paste0("ENCODING=", SHP_ENC)))
mun_m <- st_transform(mun, EPSG_M)
meso  <- read.csv(MESO, encoding = "UTF-8")
mun_m$meso <- meso$mesorregiao[match(mun_m$NM_MUN, meso$NM_MUN)]
sc_m  <- st_union(mun_m)
W     <- as.owin(sc_m)
meso_m <- aggregate(mun_m["meso"], by = list(meso = mun_m$meso), FUN = function(x) x[1])[, "meso"]
MESOS <- sort(unique(mun_m$meso))

rec_all <- read.csv(RECORDS)
rec_all <- rec_all[rec_all$sensor == "MODIS+VIIRS" & rec_all$version %in% c("v2.5", "v2.5.1") & rec_all$year %in% YEARS,
                   c("year", "DAY", "POLYID", "FIREID", "LONGI", "LATI")]

## screened events of one year, with the centroid of their detections (same steps as kde_events.R) --------------
events_of <- function(y) {
  rec <- rec_all[rec_all$year == y, ]
  pts <- st_transform(st_as_sf(rec, coords = c("LONGI", "LATI"), crs = 4326, remove = FALSE), EPSG_M)
  inside <- lengths(st_intersects(pts, mun_m)) > 0
  rec <- rec[inside, ]
  rec$key <- paste(rec$year, rec$DAY, rec$POLYID, sep = "_")
  det <- rec[!duplicated(paste(rec$key, rec$FIREID)), c("key", "DAY", "FIREID", "LONGI", "LATI")]
  det_m <- st_transform(st_as_sf(det, coords = c("LONGI", "LATI"), crs = 4326), EPSG_M)
  nb <- st_is_within_distance(det_m, det_m, dist = R_SCREEN)
  det$ndays <- vapply(nb, function(i) length(unique(det$DAY[i])), integer(1))
  flag_keys <- unique(det$key[det$ndays >= MIN_DAYS])
  ev <- data.frame(key = unique(rec$key))
  ev$lon <- as.numeric(tapply(det$LONGI, det$key, mean)[ev$key])
  ev$lat <- as.numeric(tapply(det$LATI,  det$key, mean)[ev$key])
  ev$flag <- ev$key %in% flag_keys
  list(ev = ev[!ev$flag, ], n_all = nrow(ev), n_flag = sum(ev$flag))
}
ppp_of <- function(ev) {
  xy <- st_coordinates(st_transform(st_as_sf(ev, coords = c("lon", "lat"), crs = 4326), EPSG_M))
  inW <- inside.owin(xy[, 1], xy[, 2], W)
  ppp(xy[inW, 1], xy[inW, 2], window = W, check = FALSE)
}
kd <- function(X, s) density.ppp(X, sigma = s, eps = PIXEL, edge = TRUE, diggle = TRUE, positive = TRUE) * 1e8

## pixel -> mesoregion (fixed grid: same window and pixel size in every year) -------------------------------
pixel_meso <- function(D) {
  g <- as.data.frame(D)
  gs <- st_as_sf(g, coords = c("x", "y"), crs = EPSG_M)
  m <- meso_m$meso[vapply(st_intersects(gs, meso_m), function(i) if (length(i)) i[1] else NA_integer_, integer(1))]
  list(x = g$x, y = g$y, meso = m)
}
summ <- function(dens, pm) {
  q99 <- quantile(dens, 0.99); q90 <- quantile(dens, 0.90)
  data.frame(meso = MESOS,
             mean_density = as.numeric(tapply(dens, factor(pm$meso, levels = MESOS), mean)),
             share_top10 = as.numeric(prop.table(table(factor(pm$meso[dens >= q90], levels = MESOS)))),
             share_top1  = as.numeric(prop.table(table(factor(pm$meso[dens >= q99], levels = MESOS)))))
}

## A. 2025 bandwidth sensitivity by mesoregion ---------------------------------------------------------------
e25 <- events_of(2025); X25 <- ppp_of(e25$ev)
say("2025: events ", e25$n_all, ", flagged ", e25$n_flag, ", analysed ", npoints(X25), " (kde_events.R: 5160 / 39 / 5121)")
D0 <- kd(X25, SENS_2025[["ppl"]]); pm <- pixel_meso(D0); d0 <- as.data.frame(D0)[, 3]
if (PART %in% c("A", "ALL")) {
A <- do.call(rbind, lapply(names(SENS_2025), function(nm) {
  d <- if (nm == "ppl") d0 else as.data.frame(kd(X25, SENS_2025[[nm]]))[, 3]
  s <- summ(d, pm)
  s$rank_mean <- rank(-s$mean_density, ties.method = "min")
  cbind(selector = nm, sigma_m = SENS_2025[[nm]], s,
        pearson_vs_main = cor(d0, d), max_density = max(d))
}))
write.csv(A, file.path(OUTDIR, "kde_2025_sensitivity_mesoregion.csv"), row.names = FALSE, fileEncoding = "UTF-8")
for (nm in names(SENS_2025)) {
  a <- A[A$selector == nm & A$meso == "Serrana", ]
  top <- A[A$selector == nm, ]; top <- top[order(-top$mean_density), ]
  say(sprintf("A | %-9s sigma %7.0f m: Serrana mean %.2f (rank %d; next: %s %.2f); Serrana share of top 10%% = %.1f%%, top 1%% = %.1f%%; r vs main = %.3f",
              nm, a$sigma_m, a$mean_density, a$rank_mean, top$meso[2], top$mean_density[2],
              100 * a$share_top10, 100 * a$share_top1, a$pearson_vs_main))
}
}

## B. annual densities with a fixed bandwidth ---------------------------------------------------------------
if (PART %in% c("B", "ALL")) {
grid_rows <- list(); B <- list()
for (y in YEARS) {
  e <- events_of(y); X <- ppp_of(e$ev)
  bw_y <- if (PPL_EACH_YEAR) as.numeric(bw.ppl(X)) else NA_real_
  D <- kd(X, SIGMA_FIXED_ANNUAL); d <- as.data.frame(D)[, 3]
  s <- summ(d, pm)
  pk <- which.max(d)
  pk_ll <- st_coordinates(st_transform(st_sfc(st_point(c(pm$x[pk], pm$y[pk])), crs = EPSG_M), 4326))
  pk_mun <- mun_m$NM_MUN[st_intersects(st_sfc(st_point(c(pm$x[pk], pm$y[pk])), crs = EPSG_M), mun_m)[[1]][1]]
  B[[as.character(y)]] <- cbind(year = y, events = npoints(X), flagged = e$n_flag, sigma_fixed_m = SIGMA_FIXED_ANNUAL,
                                sigma_ppl_year_m = round(bw_y, 1), integral = integral(D) / 1e8,
                                max_density = max(d), max_lon = pk_ll[1], max_lat = pk_ll[2], max_mun = pk_mun, s)
  grid_rows[[as.character(y)]] <- data.frame(year = y, ev_100km2 = round(d, 5))
  sr <- s[s$meso == "Serrana", ]
  say(sprintf("B | %d: events %d (flagged %d); own CV sigma %s m; integral %.1f; max %.1f in %s; Serrana mean %.2f (state %.2f); Serrana share of top 1%% = %.1f%%, top 10%% = %.1f%%",
              y, npoints(X), e$n_flag, if (is.na(bw_y)) "not computed" else sprintf("%.0f", bw_y), integral(D) / 1e8, max(d), pk_mun, sr$mean_density, mean(d),
              100 * sr$share_top1, 100 * sr$share_top10))
}
BB <- do.call(rbind, B)
write.csv(BB, file.path(OUTDIR, "kde_annual_summary.csv"), row.names = FALSE, fileEncoding = "UTF-8")
G <- data.frame(x = pm$x, y = pm$y, meso = pm$meso)
for (y in YEARS) G[[paste0("y", y)]] <- grid_rows[[as.character(y)]]$ev_100km2
gz <- gzfile(file.path(OUTDIR, "kde_annual_grid.csv.gz"), "w", encoding = "UTF-8"); write.csv(G, gz, row.names = FALSE); close(gz)
}
con <- file(sprintf("results/logs/kde_sensitivity_annual_%s.txt", tolower(PART)), open = "w", encoding = "UTF-8"); writeLines(log_lines, con); close(con)
say("done")

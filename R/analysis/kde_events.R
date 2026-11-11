#!/usr/bin/env Rscript
# =============================================================================
# R/analysis/kde_events.R  (formerly 22_kde_eventos_queimada.R)
# Run from the project root:  Rscript R/analysis/kde_events.R
# Kernel density of wildfire events (eventos de queimada) in Santa Catarina.
# Manuscript (v3.2): section 2.6 (method), Figure 5 (map), sections 3 and 4 (summary values).
#
# What this script corrects relative to 03-kernell_map_FINN_relatorio.R (MASS::kde2d):
#  1. Unit of analysis: fire EVENTS (daily FINN burned-area polygons, POLYID), not FINN rows.
#     A FINN row is a land-cover piece (GENVEG) of one detection (FIREID); in 2025 there were
#     1.66 rows per event, so counting rows inflates and distorts the density.
#  2. Sample: only events inside SC (point-in-polygon on the IBGE 2024 mesh), not every record
#     of the processing grid (the grid also covers parts of PR, RS and Argentina).
#  3. Year: the year filtered is the year shown in the figure.
#  4. Geometry: the density is computed in a metric CRS (SIRGAS 2000 / UTM zone 22S, EPSG:31982,
#     whose zone, 54-48 deg W, contains all of SC), so the kernel is isotropic in km and the output
#     is directly in events per 100 km2 (kde2d works in degrees and needs an ad hoc conversion).
#  5. Edge effects: Jones-Diggle edge correction inside the SC polygon window, so the density is not
#     biased low near the coast and the state borders (kernel mass falling outside the window).
#  6. Bandwidth: data-driven (likelihood cross-validation, spatstat bw.ppl) as the main choice,
#     with a sensitivity analysis (bw.CvL, bw.scott.iso, bw.diggle and fixed values).
#  7. Persistent thermal anomalies (possible non-vegetation static sources): screened with the
#     MODIS C6/C6.1 static-source criterion (detected on >= 16 distinct days in a calendar year;
#     Giglio et al. 2021, MODIS C6/C6.1 Active Fire Product User's Guide), implemented without a
#     grid: for each detection, distinct detection days within R_SCREEN m in the same year.
#
# Inputs (edit CONFIG):
#   RECORDS : FINN 'each fire' records of SC, one row per (FIREID, GENVEG) piece, with columns
#             year, sensor, version, DAY, POLYID, FIREID, GENVEG, AREA (m2), LONGI, LATI (WGS84)
#             (data/derived/finn_sc_records_2003_2025.csv.gz). Only SENSOR records of YEAR are used;
#             records outside SC are dropped here, so a grid-clipped file can also be used.
#   SHP     : IBGE 2024 municipal mesh of SC (SC_Municipios_2024.shp; field NM_MUN).
#   MESO    : municipality -> mesoregion table (sc_municipios_2024_atributos.csv: NM_MUN, mesorregiao).
# Outputs (OUTDIR):
#   kde_events_<YEAR>.csv           event table (key, municipality, centroid, area, flag)
#   kde_<YEAR>_bandwidths.csv    bandwidth selectors (m)
#   kde_<YEAR>_grid.csv          pixel centres (UTM and lon/lat) and density (events per 100 km2)
#   results/logs/kde_<YEAR>_summary.txt      sample sizes, checks, sensitivity, summaries by mesoregion
#   results/figures/kde_<YEAR>_quicklook.png      quick-look map
# Packages: sf (>= 1.0), spatstat.geom and spatstat.explore (spatstat >= 3.0), ggplot2 (>= 3.4).
# References: Diggle (1985) Appl. Stat. 34:138-147 (edge correction); Jones (1993) Stat. Comput.
#   3:135-146; Loader (1999) Local Regression and Likelihood (bw.ppl); Cronie & van Lieshout (2018)
#   Biometrika 105:455-462 (bw.CvL); Baddeley, Rubak & Turner (2015) Spatial Point Patterns (spatstat).
# =============================================================================

## ---------------- CONFIG ------------------------------------------------------
RECORDS  <- "data/derived/finn_sc_records_2003_2025.csv.gz"   # archived SC records (all products)
SENSOR   <- "MODIS+VIIRS"
SHP      <- "data/inputs/SC_Municipios_2024.shp"
SHP_ENC  <- "LATIN1"       # encoding of the IBGE .dbf (no .cpg file)
MESO     <- "data/external/sc_municipios_2024_atributos.csv"   # columns NM_MUN, mesorregiao
OUTDIR   <- "results/tables"
YEAR     <- 2025
EPSG_M   <- 31982        # SIRGAS 2000 / UTM zone 22S
PIXEL    <- 1000         # output pixel size (m)
R_SCREEN <- 1000         # radius (m) for the persistent-anomaly screening
MIN_DAYS <- 16           # MODIS static-source criterion (distinct days per calendar year)
SIGMA    <- "ppl"        # main bandwidth: "ppl", "CvL", "scott", "diggle" or a number (m)
SIGMA_FIXED <- c(2000, 4000, 8000)   # fixed values for the sensitivity analysis (m)
BREAKS   <- c(0, 1, 2, 4, 8, 16, 32, 64, 128)   # legend classes (events per 100 km2)
## -----------------------------------------------------------------------------

suppressPackageStartupMessages({
  for (p in c("sf", "spatstat.geom", "spatstat.explore", "ggplot2"))
    if (!requireNamespace(p, quietly = TRUE)) stop("install.packages('", p, "') first")
  library(sf); library(spatstat.geom); library(spatstat.explore); library(ggplot2)
})
sf_use_s2(FALSE)
# Municipality and mesoregion names have accents: switch a non-UTF-8 session (e.g. LANG=C on Linux) to a UTF-8
# character locale, so that the names are written correctly to the CSV, the log and the PNG
if (!isTRUE(l10n_info()[["UTF-8"]]))
  for (loc in c("C.UTF-8", "C.utf8", "en_US.UTF-8", "en_US.utf8")) if (nzchar(suppressWarnings(Sys.setlocale("LC_CTYPE", loc)))) break
if (!isTRUE(l10n_info()[["UTF-8"]])) message("Note: the R session is not in a UTF-8 locale; accented names may be written as <U+00F3> escapes.")
log_lines <- character()
say <- function(...) { s <- paste0(...); cat(s, "\n"); log_lines <<- c(log_lines, s) }
dec <- function(x, d = 2) formatC(x, format = "f", digits = d, decimal.mark = ",", big.mark = ".")

## 1. Municipal mesh, SC window and mesoregions ---------------------------------
mun   <- st_make_valid(st_read(SHP, quiet = TRUE, options = paste0("ENCODING=", SHP_ENC)))
mun_m <- st_transform(mun, EPSG_M)
meso  <- read.csv(MESO, encoding = "UTF-8")
mun_m$meso <- meso$mesorregiao[match(mun_m$NM_MUN, meso$NM_MUN)]
if (anyNA(mun_m$meso)) stop("municipalities without mesoregion: ", paste(mun_m$NM_MUN[is.na(mun_m$meso)], collapse = ", "))
sc_m  <- st_union(mun_m)
W     <- as.owin(sc_m)
meso_m <- aggregate(mun_m["meso"], by = list(meso = mun_m$meso), FUN = function(x) x[1])[, "meso"]

## 2. Records of YEAR inside SC -------------------------------------------------
rec <- read.csv(RECORDS)
rec <- rec[rec$sensor == SENSOR & rec$version %in% c("v2.5", "v2.5.1") & rec$year == YEAR, c("year", "DAY", "POLYID", "FIREID", "GENVEG", "AREA", "LONGI", "LATI")]
pts <- st_transform(st_as_sf(rec, coords = c("LONGI", "LATI"), crs = 4326, remove = FALSE), EPSG_M)
hit <- st_intersects(pts, mun_m)
rec$mun <- mun_m$NM_MUN[vapply(hit, function(i) if (length(i)) i[1] else NA_integer_, integer(1))]
say("records of ", YEAR, " in file: ", nrow(rec), " | inside SC: ", sum(!is.na(rec$mun)))
rec <- rec[!is.na(rec$mun), ]

## 3. Fire events = distinct (year, DAY, POLYID) --------------------------------
rec$key <- paste(rec$year, rec$DAY, rec$POLYID, sep = "_")
# municipality of the event = municipality holding the largest share of its AREA
am <- aggregate(AREA ~ key + mun, data = rec, FUN = sum)
am <- am[order(am$key, -am$AREA), ]; am <- am[!duplicated(am$key), c("key", "mun")]
# detections = distinct (year, DAY, FIREID); each FIREID has a single coordinate
det <- rec[!duplicated(paste(rec$key, rec$FIREID)), c("key", "year", "DAY", "POLYID", "FIREID", "LONGI", "LATI")]
# events in numeric (year, DAY, POLYID) order, so that the row order of kde_events_<YEAR>.csv does not depend
# on the collation rules of the computer's locale
ev_ids <- unique(rec[, c("key", "year", "DAY", "POLYID")])
ev <- data.frame(key = ev_ids$key[order(ev_ids$year, ev_ids$DAY, ev_ids$POLYID)])
ev$area_m2 <- as.numeric(tapply(rec$AREA, rec$key, sum)[ev$key])
ev$n_rows  <- as.integer(table(rec$key)[ev$key])
ev$n_det   <- as.integer(table(det$key)[ev$key])
ev$lon     <- as.numeric(tapply(det$LONGI, det$key, mean)[ev$key])   # centroid of the event's detections
ev$lat     <- as.numeric(tapply(det$LATI,  det$key, mean)[ev$key])
ev$DAY     <- as.integer(sub("^[0-9]+_([0-9.]+)_.*$", "\\1", ev$key))
ev$mun     <- am$mun[match(ev$key, am$key)]
say("rows: ", nrow(rec), " | detections: ", nrow(det), " | events: ", nrow(ev),
    " | rows per event: ", dec(nrow(rec) / nrow(ev), 3))

## 4. Persistent thermal anomalies (grid-free MODIS static-source criterion) ----
det_m <- st_transform(st_as_sf(det, coords = c("LONGI", "LATI"), crs = 4326), EPSG_M)
nb <- st_is_within_distance(det_m, det_m, dist = R_SCREEN)
det$ndays <- vapply(nb, function(i) length(unique(det$DAY[i])), integer(1))
flag_keys <- unique(det$key[det$ndays >= MIN_DAYS])
ev$flag <- ev$key %in% flag_keys
say("persistent-anomaly screening (", R_SCREEN, " m, >= ", MIN_DAYS, " days): flagged events ", sum(ev$flag),
    " (", dec(100 * mean(ev$flag)), "%) in ", paste(sort(unique(ev$mun[ev$flag])), collapse = "; "),
    " | max distinct days around a detection: ", max(det$ndays))
write.csv(ev, file.path(OUTDIR, sprintf("kde_events_%d.csv", YEAR)), row.names = FALSE, fileEncoding = "UTF-8")
evs <- ev[!ev$flag, ]
say("events analysed: ", nrow(evs))

## 5. Point pattern and bandwidths ---------------------------------------------
xy <- st_coordinates(st_transform(st_as_sf(evs, coords = c("lon", "lat"), crs = 4326), EPSG_M))
inW <- inside.owin(xy[, 1], xy[, 2], W)
if (any(!inW)) say("note: ", sum(!inW), " event centroid(s) fall outside the window (border/coast) and are dropped")
X <- ppp(xy[inW, 1], xy[inW, 2], window = W, check = FALSE)
bw <- c(ppl = as.numeric(bw.ppl(X)), CvL = as.numeric(bw.CvL(X)),
        scott = as.numeric(bw.scott.iso(X)), diggle = as.numeric(bw.diggle(X)))
write.csv(data.frame(selector = names(bw), sigma_m = round(bw, 1)), file.path(OUTDIR, sprintf("kde_%d_bandwidths.csv", YEAR)), row.names = FALSE)
say("bandwidth selectors (sigma, m): ", paste(names(bw), round(bw), sep = " = ", collapse = "; "))
sig <- if (is.numeric(SIGMA)) SIGMA else bw[[SIGMA]]
say("main sigma: ", round(sig), " m (", SIGMA, ")")

## 6. Kernel density with Jones-Diggle edge correction --------------------------
kd <- function(s) density.ppp(X, sigma = s, eps = PIXEL, edge = TRUE, diggle = TRUE, positive = TRUE) * 1e8  # per 100 km2
D <- kd(sig)
say("check: integral of the density over SC = ", dec(integral(D) / 1e8, 1), " events (n = ", npoints(X), ")")
g <- as.data.frame(D); names(g)[3] <- "ev_100km2"
gs <- st_as_sf(g, coords = c("x", "y"), crs = EPSG_M, remove = FALSE)
g$meso <- meso_m$meso[vapply(st_intersects(gs, meso_m), function(i) if (length(i)) i[1] else NA_integer_, integer(1))]
ll <- st_coordinates(st_transform(gs, 4326)); g$lon <- ll[, 1]; g$lat <- ll[, 2]
pk <- which.max(g$ev_100km2)
say("max density: ", dec(g$ev_100km2[pk]), " events/100 km2 at lon ", dec(g$lon[pk], 3), ", lat ", dec(g$lat[pk], 3),
    " | state mean of pixels: ", dec(mean(g$ev_100km2)), " | events/area: ", dec(npoints(X) / (area.owin(W) / 1e8)))

## 7. Sensitivity -----------------------------------------------------------------
sens <- c(bw[c("CvL", "scott", "diggle")], setNames(SIGMA_FIXED, paste0("fixed_", SIGMA_FIXED / 1000, "km")))
for (nm in names(sens)) {
  Ds <- as.data.frame(kd(sens[[nm]]))[, 3]
  say(sprintf("sensitivity %s (sigma %.0f m): Pearson r = %s; Spearman rho = %s; max = %s",
              nm, sens[[nm]], dec(cor(g$ev_100km2, Ds), 3), dec(cor(g$ev_100km2, Ds, method = "spearman"), 3), dec(max(Ds))))
}

## 8. Summaries by mesoregion ---------------------------------------------------
q99 <- quantile(g$ev_100km2, 0.99); q90 <- quantile(g$ev_100km2, 0.90)
tab <- data.frame(
  mean_density = tapply(g$ev_100km2, g$meso, mean),
  share_pixels = as.numeric(prop.table(table(g$meso))),
  share_top10  = as.numeric(prop.table(table(factor(g$meso[g$ev_100km2 >= q90], levels = sort(unique(g$meso)))))),
  share_top1   = as.numeric(prop.table(table(factor(g$meso[g$ev_100km2 >= q99], levels = sort(unique(g$meso)))))))
say("by mesoregion (mean density in events/100 km2; shares of pixels overall, in the top 10% and top 1%):")
say(paste(capture.output(print(round(tab, 3))), collapse = "\n"))
write.csv(g[, c("x", "y", "lon", "lat", "meso", "ev_100km2")], file.path(OUTDIR, sprintf("kde_%d_grid.csv", YEAR)), row.names = FALSE, fileEncoding = "UTF-8")

## 9. Quick-look map (same classes as Figure 4) -----------------------------------
g$cls <- cut(g$ev_100km2, BREAKS, include.lowest = TRUE, right = FALSE,
             labels = paste0(dec(head(BREAKS, -1), 0), "–", dec(BREAKS[-1], 0)))
bb <- st_bbox(sc_m)
# scale bar in the bottom-right corner, over the ocean (authors' request of 2026-10-16): right end 10 km inside the
# frame, at the lowest height (from 8 km above the frame) where the bar and its labels stay 3 km clear of the State
x1 <- bb[["xmax"]] - 1e4
for (y0 in seq(bb[["ymin"]] + 8e3, bb[["ymin"]] + 6e4, by = 2e3)) {
  zone <- st_sfc(st_polygon(list(rbind(c(x1 - 1.06e5, y0), c(x1, y0), c(x1, y0 + 1.6e4), c(x1 - 1.06e5, y0 + 1.6e4),
                                       c(x1 - 1.06e5, y0)))), crs = EPSG_M)
  if (!st_intersects(zone, st_buffer(sc_m, 3e3), sparse = FALSE)[1, 1]) break
}
x0 <- x1 - 1e5
# north rose (eight-point compass rose, same design as python/finn_sc/cartography.py), centred above the scale bar
# (authors' requests of 2026-10-16); drawn in map units (UTM metres), so it keeps its shape
ROSE_S <- 2.0e4                                    # length of the north point (m)
rose_layers <- function(xc, yc, s = ROSE_S) {
  t <- seq(0, 2 * pi, length.out = 121)
  out <- list(annotate("path", x = xc + 0.46 * s * cos(t), y = yc + 0.46 * s * sin(t), linewidth = 0.2))
  add_point <- function(ang, len, waist, dark) {
    a <- ang * pi / 180
    lapply(1:2, function(h) {
      side <- if (h == 1) a + pi / 4 else a - pi / 4       # counter-clockwise half dark
      annotate("polygon", x = c(xc, xc + len * cos(a), xc + waist * cos(side)),
               y = c(yc, yc + len * sin(a), yc + waist * sin(side)),
               fill = if (h == 1) dark else "white", colour = "black", linewidth = 0.2)
    })
  }
  for (ang in c(45, 135, 225, 315)) out <- c(out, add_point(ang, 0.42 * s, 0.13 * s, "grey62"))
  for (ang in c(0, 270, 180)) out <- c(out, add_point(ang, 0.62 * s, 0.26 * s, "grey35"))
  out <- c(out, add_point(90, s, 0.26 * s, "black"),
           list(annotate("text", x = xc, y = yc + s + 6e3, label = "N", fontface = "bold", size = 3.2)))
  out
}
# rose centre: over the middle of the bar, 5 km above its labels, or further right if it would come within 3 km of the State
yc <- y0 + 2.05e4 + 0.62 * ROSE_S
for (xc in seq(x0 + 5e4, x1 - 1.5e4, by = 2e3)) {
  rz <- st_sfc(st_polygon(list(rbind(c(xc - 0.62 * ROSE_S, y0 + 1.6e4), c(xc + 0.62 * ROSE_S, y0 + 1.6e4),
                                     c(xc + 0.62 * ROSE_S, yc + ROSE_S + 1.2e4), c(xc - 0.62 * ROSE_S, yc + ROSE_S + 1.2e4),
                                     c(xc - 0.62 * ROSE_S, y0 + 1.6e4)))), crs = EPSG_M)
  if (!st_intersects(rz, st_buffer(sc_m, 3e3), sparse = FALSE)[1, 1]) break
}
pmap <- ggplot() +
  geom_tile(data = g, aes(x, y, fill = cls), width = PIXEL, height = PIXEL) +
  geom_sf(data = mun_m, fill = NA, colour = "grey55", linewidth = 0.08) +
  scale_fill_viridis_d(option = "magma", direction = -1, name = "Eventos por 100 km²", drop = FALSE) +
  annotate("rect", xmin = x0, xmax = x0 + 5e4, ymin = y0, ymax = y0 + 4e3, fill = "black") +
  annotate("rect", xmin = x0 + 5e4, xmax = x0 + 1e5, ymin = y0, ymax = y0 + 4e3, fill = "white", colour = "black", linewidth = 0.2) +
  annotate("text", x = c(x0, x0 + 5e4, x0 + 1e5), y = y0 + 1.1e4, label = c("0", "50", "100 km"), size = 2.6, hjust = c(0.5, 0.5, 1)) +
  rose_layers(xc, yc) +
  coord_sf(crs = st_crs(EPSG_M), datum = st_crs(4674), expand = FALSE) +
  labs(x = NULL, y = NULL,
       caption = sprintf("FINN MODIS+VIIRS, %d: %d eventos de queimada; núcleo gaussiano, σ = %s km; SIRGAS 2000 / UTM 22S",
                         YEAR, npoints(X), dec(sig / 1000, 1))) +
  theme_minimal(base_size = 9) + theme(panel.grid = element_line(colour = "grey92", linewidth = 0.2))
ggsave(file.path("results/figures", sprintf("kde_%d_quicklook.png", YEAR)), pmap, width = 18, height = 11, units = "cm", dpi = 300, bg = "white")
con <- file(file.path("results/logs", sprintf("kde_%d_summary.txt", YEAR)), open = "w", encoding = "UTF-8"); writeLines(log_lines, con); close(con)
say("done")

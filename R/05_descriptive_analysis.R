# =============================================================================
# 05_descriptive_analysis.R  -  Descriptive plots & summary table
# -----------------------------------------------------------------------------
# Step 6 of the FINN Santa Catarina pipeline.
# Reads data/output/aggregated_emissions_all.csv (step 04) and produces:
#   - a stacked 4-panel figure (fire events, burned area, CO, PM2.5 by year)
#     (2026-10-03 review: events + burned_km2 replace focos + AREA_KM2)
#   - a per-year summary table of key pollutants
#   - a version x sensor comparison of annual CO2
# Figures are written to data/output/.
#
# Adapted from the author's 03-analise_descritiva_FINN.R.
# Run from the project root:  Rscript R/05_descriptive_analysis.R
# =============================================================================

source("R/utils_finn.R")
.finn_require(c("ggplot2", "scales", "patchwork"))
library(ggplot2); library(dplyr); library(patchwork)
cfg <- finn_load_config()

agg_path <- file.path(cfg$paths$output, "aggregated_emissions_all.csv")
if (!file.exists(agg_path)) stop("Missing ", agg_path, "; run step 04 first.")
data_aggregated <- data.table::fread(agg_path)

# Scientific-notation axis labels (a x 10^b), as in the original script.
label_base10 <- function(x) {
  s <- ifelse(x == 0, "0",
              paste0(formatC(x / 10^floor(log10(abs(x))), format = "fg", digits = 2, flag = "#"),
                     " %*% 10^", floor(log10(abs(x)))))
  parse(text = s)
}

# Pick a version/sensor to plot (defaults to the configured selection).
V <- cfg$selection$version
S <- cfg$selection$sensor
base_theme <- theme_minimal(base_size = 14) +
  theme(panel.grid.major.x = element_blank(),
        panel.grid.minor = element_blank(),
        panel.grid.major.y = element_line(color = "gray80", linewidth = 0.4),
        axis.title.y = element_text(margin = margin(r = 10), face = "bold"))

# Parse a `period` value ("2019" / "2019-06" / "2019-06-15") to a Date. Tolerant
# of float-like years ("2019.0") that arise from step 04's left join.
res <- cfg$aggregation$time_resolution %||% "year"
period_to_date <- function(p) {
  p <- sub("\\.0$", "", as.character(p))
  as.Date(ifelse(nchar(p) == 4, paste0(p, "-01-01"),
           ifelse(nchar(p) == 7, paste0(p, "-01"), p)))
}
bar_width_days <- c(day = 0.85, month = 22, year = 250)[res]
if (is.na(bar_width_days)) bar_width_days <- 0.85
# DATE-ONLY x-axis labels (never times): day -> YYYY-MM-DD, month -> YYYY-MM, year -> YYYY.
date_lab <- c(day = "%Y-%m-%d", month = "%Y-%m", year = "%Y")[res]
if (is.na(date_lab)) date_lab <- "%Y-%m-%d"

# --- Primary overview: bar 4-panel at the period / resolution actually run ----
# (a 7-day run -> one bar per day, never a forced single 'annual' bar)
period_bar <- function(var, ylab, fill) {
  if (!"period" %in% names(data_aggregated) ||
      !var %in% names(data_aggregated)) {
    message("  (skipping panel '", var, "': column not present)")
    return(NULL)
  }
  data_aggregated |>
    dplyr::filter(version == V, sensor == S, !is.na(period)) |>
    dplyr::mutate(period_date = period_to_date(period)) |>
    dplyr::filter(!is.na(period_date)) |>
    dplyr::group_by(period_date) |>
    dplyr::summarize(val = sum(.data[[var]], na.rm = TRUE), .groups = "drop") |>
    ggplot(aes(period_date, val)) +
    geom_col(width = bar_width_days, fill = fill) +
    scale_x_date(date_labels = date_lab) +
    scale_y_continuous(labels = label_base10) +
    labs(x = NULL, y = ylab) + base_theme
}

# 2026-10-03 review: fire EVENTS (not row counts) and FINN burned area
# (burned_km2 = sum of AREA); AREA_KM2 is the polygon's own area, not burned area.
panels <- list(
  period_bar("events",     "Fire events",                      "gray40"),
  period_bar("burned_km2", expression("Burned area" ~ (km^2)),  "red4"),
  period_bar("CO",       expression(CO ~ (t)),                "dodgerblue4"),
  period_bar("PM25",     expression(PM[2.5] ~ (t)),           "yellow3"))
panels <- panels[!vapply(panels, is.null, logical(1))]   # drop absent columns

if (length(panels)) {
  fig <- Reduce(`/`, panels) +
    patchwork::plot_annotation(caption = paste0("period (", res, ")"))
  ggsave(file.path(cfg$paths$output, paste0("overview_", res, ".png")), fig,
         width = 8, height = 2.7 * length(panels), dpi = 200)
  message("Saved: ", file.path(cfg$paths$output, paste0("overview_", res, ".png")))
}

# --- Time series at the configured resolution (day / month / year) ---
if ("period" %in% names(data_aggregated)) {
  ts <- data_aggregated |>
    dplyr::filter(version == V, sensor == S) |>
    dplyr::group_by(period) |>
    dplyr::summarize(dplyr::across(dplyr::any_of(c("events", "CO", "PM25", "CO2")),
                                   \(x) sum(x, na.rm = TRUE)), .groups = "drop") |>
    dplyr::mutate(period_date = period_to_date(period)) |>
    dplyr::arrange(period_date)

  ts_panel <- function(var, ylab, color) {
    if (!var %in% names(ts)) return(NULL)
    ggplot(ts, aes(period_date, .data[[var]])) +
      geom_line(color = color, linewidth = 0.6) +
      geom_point(color = color, size = 1) +
      scale_x_date(date_labels = date_lab) +
      labs(x = NULL, y = ylab) + base_theme
  }
  ts_panels <- list(
    ts_panel("events", "Fire events",             "gray40"),   # 2026-10-03 review
    ts_panel("CO",    expression(CO ~ (t)),       "dodgerblue4"),
    ts_panel("PM25",  expression(PM[2.5] ~ (t)),  "yellow3"),
    ts_panel("CO2",   expression(CO[2] ~ (t)),    "seagreen4"))
  ts_panels <- ts_panels[!vapply(ts_panels, is.null, logical(1))]
  ts_fig <- Reduce(`/`, ts_panels) +
    patchwork::plot_annotation(caption = paste0("period (", res, ")"))
  ggsave(file.path(cfg$paths$output, paste0("timeseries_", res, ".png")),
         ts_fig, width = 9, height = 2.4 * length(ts_panels), dpi = 200)
  message("Saved: ", file.path(cfg$paths$output, paste0("timeseries_", res, ".png")))

  # Region totals per period (long table).
  # 2026-10-03 review: NOx = NOXasNO (NO mass; NOx_as_NO2 = NO2-equivalent),
  # VOC = NMOC; events/detections replace the row count `focos`.
  key2 <- c("CO2", "CO", "PM25", "OC", "NOXasNO", "NOx_as_NO2", "NMOC", "CH4", "NH3",
            "BC", "SO2", "events", "detections", "burned_km2")
  period_tbl <- data_aggregated |>
    dplyr::filter(version == V, sensor == S) |>
    dplyr::group_by(period) |>
    dplyr::summarize(dplyr::across(dplyr::any_of(key2), \(x) sum(x, na.rm = TRUE)),
                     .groups = "drop") |>
    dplyr::arrange(period)
  data.table::fwrite(period_tbl, file.path(cfg$paths$output, paste0("period_summary_", res, ".csv")))
  message("Saved: ", file.path(cfg$paths$output, paste0("period_summary_", res, ".csv")))

  # Coverage note: which requested periods actually had fires INSIDE the region,
  # so a multi-day range that yields a single bar is self-explanatory (the step
  # 02 bounding box is a rectangle that also covers ocean/neighbouring states;
  # step 04's point-in-polygon test is what keeps only true in-region fires).
  region <- cfg$region$name %||% "the region"
  present <- sort(unique(as.character(period_tbl$period)))
  b <- finn_date_bounds(cfg)
  if (!is.null(b)) {
    fmt <- c(day = "%Y-%m-%d", month = "%Y-%m", year = "%Y")[res]
    if (is.na(fmt)) fmt <- "%Y-%m-%d"
    req <- sort(unique(format(seq(as.Date(b$start), as.Date(b$end), by = "day"), fmt)))
    missing <- setdiff(req, present)
    message("Coverage: requested ", b$start, " .. ", b$end, " (", res, " resolution).")
    message("  Periods with fires inside ", region, ": ",
            if (length(present)) paste(present, collapse = ", ") else "none")
    if (length(missing))
      message("  No fires inside ", region, " on: ", paste(missing, collapse = ", "),
              "  (", length(missing), " of ", length(req),
              " requested period(s) had no in-region fires - points there fell outside ",
              "the region's polygons, or none occurred). This is expected, not an error.")
  } else {
    message("Coverage: periods with fires inside ", region, ": ",
            if (length(present)) paste(present, collapse = ", ") else "none")
  }
}

# --- By-year rollup: only meaningful when the data span >= 2 calendar years ---
years_present <- data_aggregated |>
  dplyr::filter(version == V, sensor == S, !is.na(year)) |>
  dplyr::pull(year) |> unique()
if (length(years_present) >= 2) {
  yr_bar <- function(var, ylab, fill) {
    if (!var %in% names(data_aggregated)) return(NULL)
    data_aggregated |>
      dplyr::filter(version == V, sensor == S, !is.na(.data[[var]]), !is.na(year)) |>
      dplyr::group_by(year) |>
      dplyr::summarize(val = sum(.data[[var]], na.rm = TRUE), .groups = "drop") |>
      ggplot(aes(year, val)) +
      geom_col(width = 0.6, fill = fill) +
      scale_x_continuous(breaks = function(x) seq(floor(min(x)), ceiling(max(x)), 1),
                         expand = c(0, 0.05)) +
      scale_y_continuous(labels = label_base10) +
      labs(x = NULL, y = ylab) + base_theme
  }
  yr_panels <- list(
    yr_bar("events",     "Fire events",                      "gray40"),   # 2026-10-03 review
    yr_bar("burned_km2", expression("Burned area" ~ (km^2)),  "red4"),
    yr_bar("CO",       expression(CO ~ (t/yr)),             "dodgerblue4"),
    yr_bar("PM25",     expression(PM[2.5] ~ (t/yr)),        "yellow3"))
  yr_panels <- yr_panels[!vapply(yr_panels, is.null, logical(1))]
  yr_fig <- Reduce(`/`, yr_panels)
  ggsave(file.path(cfg$paths$output, "overview_by_year.png"), yr_fig,
         width = 8, height = 2.7 * length(yr_panels), dpi = 200)
  message("Saved: ", file.path(cfg$paths$output, "overview_by_year.png"))

  key <- c("CO2", "CO", "PM25", "OC", "NOXasNO", "NOx_as_NO2", "NMOC", "CH4", "NH3",
           "BC", "SO2", "events", "detections", "burned_km2")   # 2026-10-03 review
  summary_tbl <- data_aggregated |>
    dplyr::filter(version == V, sensor == S, !is.na(year)) |>
    dplyr::group_by(year) |>
    dplyr::summarize(dplyr::across(dplyr::any_of(key), \(x) sum(x, na.rm = TRUE)),
                     .groups = "drop")
  data.table::fwrite(summary_tbl, file.path(cfg$paths$output, "summary_by_year.csv"))
  message("Saved: ", file.path(cfg$paths$output, "summary_by_year.csv"))
} else {
  span <- if (length(years_present)) years_present[1] else "no fires found"
  message("By-year rollup skipped: data span a single year (", span,
          "). The '", res, "'-grain outputs already describe this run.")
}

# --- Version x sensor comparison of annual CO2 (if multiple present) ---
if (dplyr::n_distinct(data_aggregated$version) > 1 ||
    dplyr::n_distinct(data_aggregated$sensor) > 1) {
  cmp <- data_aggregated |>
    dplyr::filter(!is.na(sensor)) |>
    dplyr::group_by(year, version, sensor) |>
    dplyr::summarize(co2 = sum(CO2, na.rm = TRUE), .groups = "drop") |>
    ggplot(aes(year, co2)) +
    geom_col(width = 0.6, fill = "dodgerblue4") +
    scale_y_continuous(labels = label_base10) +
    labs(x = NULL, y = expression(CO[2] ~ (t/yr))) +
    facet_grid(version ~ sensor) + base_theme
  ggsave(file.path(cfg$paths$output, "co2_version_sensor_comparison.png"),
         cmp, width = 10, height = 8, dpi = 200)
  message("Saved: ", file.path(cfg$paths$output, "co2_version_sensor_comparison.png"))
}

message("\nStep 05 complete. Figures and tables written to ", cfg$paths$output)

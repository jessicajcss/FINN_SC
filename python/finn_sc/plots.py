"""Descriptive plots (Python port of 05_descriptive_analysis.R).

Produces figures and summary tables from the aggregated municipality inventory.

Outputs are named after the *period / resolution actually run* (day / month /
year), so a 7-day window yields a day-grain overview rather than a degenerate
single "annual" bar. Helpers here:

    period_4panel        -> bar 4-panel (fires, area, CO, PM2.5) at the period grain
    period_timeseries    -> line 4-panel at the period grain
    period_summary_table -> per-period totals table
    distinct_years       -> how many calendar years the data actually span
    annual_4panel        -> bar 4-panel by YEAR   (used only for multi-year runs)
    annual_summary_table -> per-year totals table (used only for multi-year runs)
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd


def _select(data_aggregated: pd.DataFrame, version: str, sensor: str) -> pd.DataFrame:
    """Rows for one FINN version/sensor (tolerant of a missing column)."""
    return data_aggregated[(data_aggregated.get("version") == version) &
                           (data_aggregated.get("sensor") == sensor)].copy()


def distinct_years(data_aggregated: pd.DataFrame, version: str, sensor: str) -> List[int]:
    """Sorted list of distinct calendar years present for this version/sensor.

    No-fire polygons arrive with a NaN year after step 04's left join; those are
    dropped. Used to decide whether a by-year rollup is meaningful (>= 2 years).
    """
    sub = _select(data_aggregated, version, sensor)
    yrs = pd.to_numeric(sub.get("year"), errors="coerce").dropna()
    return sorted({int(y) for y in yrs})


def annual_4panel(data_aggregated: pd.DataFrame,
                  version: str,
                  sensor: str,
                  out_path: str | Path) -> Path:
    """Stacked bar panels of fire count, burned area, CO and PM2.5 by year."""
    sub = data_aggregated[(data_aggregated.get("version") == version) &
                          (data_aggregated.get("sensor") == sensor)].copy()

    panels = [
        # 2026-10-03 review: fire EVENTS (not row counts) and FINN burned area
        # (burned_km2 = sum AREA); AREA_KM2 is the polygon's own area.
        ("events", "Fire events", "#4d4d4d"),
        ("burned_km2", "Burned area (km$^2$)", "#8b1a1a"),
        ("CO", "CO (t/yr)", "#1b4f8a"),
        ("PM25", "PM$_{2.5}$ (t/yr)", "#c9b400"),
    ]

    fig, axes = plt.subplots(len(panels), 1, figsize=(8, 11), sharex=True)
    for ax, (col, ylab, color) in zip(axes, panels):
        if col in sub.columns:
            by_year = sub.groupby("year")[col].sum(min_count=1)
            ax.bar(by_year.index.astype(int), by_year.values, width=0.6, color=color)
        ax.set_ylabel(ylab, fontweight="bold")
        ax.grid(axis="y", color="0.8", linewidth=0.4)
        ax.set_axisbelow(True)
    axes[-1].set_xlabel("")
    fig.suptitle(f"FINN {version} / {sensor} - Santa Catarina", y=0.995)
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def annual_summary_table(data_aggregated: pd.DataFrame,
                         version: str,
                         sensor: str,
                         out_path: Optional[str | Path] = None) -> pd.DataFrame:
    """Per-year totals of key pollutants (t/yr).

    2026-10-03 review: NOx = NOXasNO (NO mass; NOx_as_NO2 = NO2-equivalent),
    VOC = NMOC (total non-methane organic gases); fire events/detections added.
    """
    key = ["CO2", "CO", "PM25", "OC", "NOXasNO", "NOx_as_NO2", "NMOC", "CH4", "NH3", "BC",
           "SO2", "events", "detections", "burned_km2"]
    sub = data_aggregated[(data_aggregated.get("version") == version) &
                          (data_aggregated.get("sensor") == sensor)].copy()
    sub = sub[sub["year"].notna()].copy()           # drop no-fire polygons (NaN year)
    sub["year"] = sub["year"].astype("int64")       # 2019.0 -> 2019
    present = [k for k in key if k in sub.columns]
    tbl = sub.groupby("year")[present].sum(min_count=1).reset_index()
    if out_path is not None:
        tbl.to_csv(out_path, index=False)
    return tbl


def _period_to_date(p) -> "pd.Timestamp":
    """Parse a `period` value to a sortable date: YYYY / YYYY-MM / YYYY-MM-DD.

    Tolerates float-like years ("2019.0") and missing values (no-fire polygons,
    which arrive as NaN after the left join in step 04)."""
    s = str(p).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if s in ("", "nan", "NaN", "None", "<NA>"):
        return pd.NaT
    if len(s) == 4:
        return pd.Timestamp(f"{s}-01-01")
    if len(s) == 7:
        return pd.Timestamp(f"{s}-01")
    return pd.Timestamp(s)


_TS_LABELS = {"CO": "CO (t)", "PM25": "PM$_{2.5}$ (t)", "CO2": "CO$_2$ (t)",
              "events": "Fire events", "NOXasNO": "NOx as NO (t)",  # 2026-10-03 review
              "OC": "OC (t)", "BC": "BC (t)", "CH4": "CH$_4$ (t)"}
_TS_COLORS = {"CO": "#1b4f8a", "PM25": "#c9b400", "CO2": "#3a7d44",
              "events": "#4d4d4d"}

# Date-only x-axis label format per resolution (no hours/minutes).
_DATE_FMT = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}


def _format_date_axis(ax, resolution: str, dates) -> None:
    """Show DATE-ONLY tick labels on a datetime x-axis (never times).

    One tick per period, thinned to at most ~12 labels so a long run stays
    readable: day -> YYYY-MM-DD, month -> YYYY-MM, year -> YYYY.
    """
    import matplotlib.dates as mdates
    try:
        n = len({pd.Timestamp(d).normalize() for d in dates if pd.notna(d)})
    except Exception:
        n = 0
    step = max(1, -(-n // 12)) if n else 1          # ceil(n / 12)
    if resolution == "day":
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=step))
    elif resolution == "month":
        ax.xaxis.set_major_locator(mdates.MonthLocator(interval=step))
    else:
        ax.xaxis.set_major_locator(mdates.YearLocator(max(1, step)))
    ax.xaxis.set_major_formatter(
        mdates.DateFormatter(_DATE_FMT.get(resolution, "%Y-%m-%d")))


def period_timeseries(data_aggregated: pd.DataFrame,
                      version: str,
                      sensor: str,
                      out_path: str | Path,
                      pollutants=("events", "CO", "PM25", "CO2"),  # 2026-10-03 review
                      resolution: str = "year") -> Path:
    """Region-total time series (one panel per pollutant) at the `period` grain.

    Sums each pollutant over all polygons per `period` and plots it against the
    parsed period date. Works for year / month / day resolutions.
    """
    sub = data_aggregated[(data_aggregated.get("version") == version) &
                          (data_aggregated.get("sensor") == sensor)].copy()
    if "period" not in sub.columns:                 # older files: fall back to year
        sub["period"] = sub.get("year")
    sub = sub[sub["period"].notna()].copy()         # drop no-fire polygons (NaN period)
    sub["period_date"] = sub["period"].map(_period_to_date)
    sub = sub[sub["period_date"].notna()]
    present = [c for c in pollutants if c in sub.columns]
    ts = (sub.groupby("period_date")[present].sum(min_count=1)
             .reset_index().sort_values("period_date"))

    fig, axes = plt.subplots(len(present), 1, figsize=(9, 2.4 * len(present)), sharex=True)
    if len(present) == 1:
        axes = [axes]
    for ax, col in zip(axes, present):
        ax.plot(ts["period_date"], ts[col], marker="o", ms=3, lw=1.4,
                color=_TS_COLORS.get(col, "#333333"))
        ax.set_ylabel(_TS_LABELS.get(col, f"{col} (t)"), fontweight="bold")
        ax.grid(axis="y", color="0.85", linewidth=0.4)
        ax.set_axisbelow(True)
    _format_date_axis(axes[-1], resolution, ts["period_date"])   # date-only labels
    axes[-1].set_xlabel(f"period ({resolution})")
    fig.suptitle(f"FINN {version} / {sensor} - {resolution} time series", y=0.997)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


# Bar width (in days) for the period 4-panel, chosen per resolution so bars
# read cleanly on a date axis.
_BAR_WIDTH_DAYS = {"day": 0.85, "month": 22.0, "year": 250.0}


def period_4panel(data_aggregated: pd.DataFrame,
                  version: str,
                  sensor: str,
                  out_path: str | Path,
                  resolution: str = "year") -> Path:
    """Bar 4-panel (fire count, burned area, CO, PM2.5) at the `period` grain.

    The period analogue of :func:`annual_4panel`. For a 7-day run this yields
    one bar per day; for a multi-year run one bar per year - always reflecting
    the resolution that was actually run, never a forced single annual bar.
    """
    sub = _select(data_aggregated, version, sensor)
    if "period" not in sub.columns:                 # older files: fall back to year
        sub["period"] = sub.get("year")
    sub = sub[sub["period"].notna()].copy()         # drop no-fire polygons
    sub["period_date"] = sub["period"].map(_period_to_date)
    sub = sub[sub["period_date"].notna()]

    panels = [
        # 2026-10-03 review: fire EVENTS (not row counts) and FINN burned area
        # (burned_km2 = sum AREA); AREA_KM2 is the polygon's own area.
        ("events", "Fire events", "#4d4d4d"),
        ("burned_km2", "Burned area (km$^2$)", "#8b1a1a"),
        ("CO", "CO (t)", "#1b4f8a"),
        ("PM25", "PM$_{2.5}$ (t)", "#c9b400"),
    ]
    width = _BAR_WIDTH_DAYS.get(resolution, 0.85)
    fig, axes = plt.subplots(len(panels), 1, figsize=(9, 11), sharex=True)
    for ax, (col, ylab, color) in zip(axes, panels):
        if col in sub.columns:
            by_p = sub.groupby("period_date")[col].sum(min_count=1)
            ax.bar(by_p.index, by_p.values, width=width, color=color)
        ax.set_ylabel(ylab, fontweight="bold")
        ax.grid(axis="y", color="0.8", linewidth=0.4)
        ax.set_axisbelow(True)
    _format_date_axis(axes[-1], resolution, sub["period_date"])   # date-only labels
    axes[-1].set_xlabel(f"period ({resolution})")
    fig.suptitle(f"FINN {version} / {sensor} - {resolution} overview", y=0.997)
    fig.autofmt_xdate()
    fig.tight_layout()
    out_path = Path(out_path)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def period_summary_table(data_aggregated: pd.DataFrame,
                         version: str,
                         sensor: str,
                         out_path: Optional[str | Path] = None) -> pd.DataFrame:
    """Region-total pollutant table, one row per `period` (t per period)."""
    # 2026-10-03 review: NOx = NOXasNO, VOC = NMOC; events/detections replace focos.
    key = ["CO2", "CO", "PM25", "OC", "NOXasNO", "NOx_as_NO2", "NMOC", "CH4", "NH3", "BC",
           "SO2", "events", "detections", "burned_km2"]
    sub = data_aggregated[(data_aggregated.get("version") == version) &
                          (data_aggregated.get("sensor") == sensor)].copy()
    if "period" not in sub.columns:
        sub["period"] = sub.get("year")
    sub = sub[sub["period"].notna()].copy()         # drop no-fire polygons (NaN period)
    sub["period"] = sub["period"].map(lambda v: str(v)[:-2] if str(v).endswith(".0") else str(v))
    present = [k for k in key if k in sub.columns]
    tbl = sub.groupby("period")[present].sum(min_count=1).reset_index().sort_values("period")
    if out_path is not None:
        tbl.to_csv(out_path, index=False)
    return tbl

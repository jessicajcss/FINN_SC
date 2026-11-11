"""Optional exact date-range selection (YYYY-MM-DD).

When ``selection.start_date`` (and optionally ``end_date``) are set in config,
these helpers decide which years to process and trim the emissions table to the
exact requested dates, adding a ``DATE`` column. See config.yml for the
download-granularity nuance (daily 2024+, monthly 2022-2023, annual pre-2022).
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def date_bounds(cfg: Dict[str, Any]) -> Optional[Tuple[str, str]]:
    """Return (start, end) ISO date strings, or None if not in date mode.

    ``start_date`` alone -> a single day (end = start). Both set -> a range.
    """
    sel = cfg["selection"]
    s = sel.get("start_date")
    if not s:
        return None
    e = sel.get("end_date") or s
    return str(s), str(e)


def selected_years(cfg: Dict[str, Any]) -> List[int]:
    """Years to process: the span of the date range if set, else ``years``."""
    b = date_bounds(cfg)
    if b is None:
        y = cfg["selection"]["years"]
        return y if isinstance(y, list) else [y]
    ys = _dt.date.fromisoformat(b[0]).year
    ye = _dt.date.fromisoformat(b[1]).year
    return list(range(ys, ye + 1))


def filter_rows_by_date(df: pd.DataFrame, year: int,
                        start_date: str, end_date: str) -> pd.DataFrame:
    """Add a DATE column (from DAY-of-year + year) and keep rows in [start, end]."""
    day = pd.to_numeric(df["DAY"], errors="coerce")
    date = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(day - 1, unit="D")
    out = df.copy()
    out["DATE"] = date.dt.strftime("%Y-%m-%d")
    mask = (date >= pd.to_datetime(start_date)) & (date <= pd.to_datetime(end_date))
    return out[mask]


_PERIOD_FMT = {"day": "%Y-%m-%d", "month": "%Y-%m", "year": "%Y"}


def requested_periods(cfg: Dict[str, Any], resolution: str) -> Optional[List[str]]:
    """The period labels the current selection ASKS for, at ``resolution``.

    Only defined when an exact date range is set (``selection.start_date`` /
    ``end_date``); returns ``None`` for a whole-``years`` selection, where the
    set of days/months in range is not fixed in advance. Day → every date in
    the range; month → every month touched; year → every year touched.
    """
    b = date_bounds(cfg)
    if b is None:
        return None
    days = pd.date_range(pd.to_datetime(b[0]), pd.to_datetime(b[1]), freq="D")
    if len(days) == 0:
        return None
    fmt = _PERIOD_FMT.get(resolution, "%Y-%m-%d")
    return sorted({d.strftime(fmt) for d in days})


def coverage_note(cfg: Dict[str, Any], periods_present, resolution: str) -> str:
    """A human-readable note on which requested periods actually had in-region fires.

    ``periods_present`` is the list of ``period`` labels present in the final,
    polygon-clipped inventory. When a date range is set, the note also lists the
    requested periods that had NO fires inside the region (so a 3-day run that
    yields a single bar is self-explanatory rather than looking like a bug).
    """
    region = cfg.get("region", {}).get("name", "the region")
    present = sorted({(str(p)[:-2] if str(p).endswith(".0") else str(p))
                      for p in periods_present if str(p) not in ("", "nan", "None")})
    req = requested_periods(cfg, resolution)
    lines: List[str] = []
    if req is not None:
        b = date_bounds(cfg)
        missing = [p for p in req if p not in set(present)]
        lines.append(f"Coverage: requested {b[0]} .. {b[1]} ({resolution} resolution).")
        lines.append(f"  Periods with fires inside {region}: "
                     + (", ".join(present) if present else "none"))
        if missing:
            lines.append(
                f"  No fires inside {region} on: " + ", ".join(missing)
                + f"  ({len(missing)} of {len(req)} requested period(s) had no in-region "
                  "fires - points there fell outside the region's polygons, or none occurred). "
                  "This is expected, not an error.")
    else:
        lines.append(f"Coverage: periods with fires inside {region}: "
                     + (", ".join(present) if present else "none"))
    return "\n".join(lines)

"""Aggregate emissions by region polygon (Python port of 04_aggregate_region.R).

Generic: joins FINN fire points to ANY polygon layer (municipalities, a country,
admin units, a biome, ...) and sums each FINN species per polygon, grouping by
the configured ``region.region_field``.

2026-10-03 review - fire counting. A FINN row is a (FIREID, GENVEG) piece, so
the number of rows is NOT a number of fires (the old ``focos`` column). In the
v2.5/v2.5.1 files POLYID is the daily burned-area polygon (adjacent detections
merged; may contain several points) and FIREID is one point (single
coordinate) inside a POLYID (verified on the SC records: 5 of 151,441 FIREIDs
have >1 coordinate; 20,766 of 124,602 POLYIDs hold >1 FIREID). Output columns:
    n_rows      number of FINN records (pieces) - diagnostic only
    events      distinct (year, DAY, POLYID); each event is assigned to ONE
                polygon, the one holding the largest share of its AREA
    detections  distinct (year, DAY, FIREID), assigned the same way
    burned_km2  sum of FINN AREA (m2) / 1e6 (NOT the shapefile's AREA_KM2,
                which is the polygon's own area)
    NOx_as_NO2  NOXasNO * 46.0055/30.0061 (optional, config derived.nox_as_no2)
FINN v1.5 has no POLYID/FIREID: events/detections are NA there.

Only known FINN species (``FINN_SPECIES``) are summed, so arbitrary numeric
attributes carried by the boundary shapefile (population, area, codes, ...) are
never mistaken for emissions.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd

# geopandas is imported lazily inside aggregate_by_region() so that importing
# the finn_sc package does not require the spatial stack (see clip_sc.py).

# Canonical FINN emission species across the versions/mechanisms this pipeline
# handles (gases + aerosols + aggregate masses).
FINN_SPECIES = [
    "CO2", "CO", "CH4", "H2", "SO2", "NH3", "NO", "NO2", "NMHC", "NMOC", "NOXasNO",
    "ACET", "ALD2", "ALK4", "BENZ", "C2H2", "C2H4", "C2H6", "C3H8", "CH2O", "GLYC",
    "GLYX", "HAC", "MEK", "MGLY", "PRPE", "TOLU", "XYLE", "OC", "BC", "PM25",
    "PM10", "TPM", "TPC",
]


# 2026-10-03 review: molar masses for the NOx-as-NO2 equivalent (NOXasNO is NO mass).
_M_NO2, _M_NO = 46.0055, 30.0061


def drop_exact_duplicates(df: pd.DataFrame, label: str = "") -> pd.DataFrame:
    """2026-10-03 review: duplicate-row guard.

    * Drops rows that are exact copies of another row (all columns equal) and
      reports how many were dropped.
    * Reports - but keeps - rows that share the record key
      (source_url, DAY, POLYID, FIREID, GENVEG) while differing in other fields:
      FINN files legitimately contain such records (on the SC 2003-2025 records,
      26,197 rows in 12,907 key groups, every group with different AREA values),
      so the key is NOT unique and must not be used to de-duplicate.
    """
    n0 = len(df)
    out = df.drop_duplicates().copy()
    if n0 - len(out):
        print(f"  [dup-guard] {label}: dropped {n0 - len(out)} exact duplicate row(s)")
    key = [c for c in ("source_url", "DAY", "POLYID", "FIREID", "GENVEG") if c in out.columns]
    if {"POLYID", "FIREID"} <= set(key):
        n_key = int(out.duplicated(key, keep=False).sum())
        if n_key:
            print(f"  [dup-guard] {label}: {n_key} row(s) share a ({', '.join(key)}) key with "
                  "another row but differ in other fields; kept (distinct FINN records).")
    return out


def count_fire_units(joined: pd.DataFrame,
                     region_field: str,
                     group_cols=("period", "year", "sensor", "version")) -> Optional[pd.DataFrame]:
    """2026-10-03 review: fire ``events`` and ``detections`` per region polygon.

    events     = distinct (year, sensor, version, DAY, POLYID)
    detections = distinct (year, sensor, version, DAY, FIREID)
    Each unit is assigned to ONE polygon: the one holding the largest summed
    AREA of the unit's in-region rows (ties -> first polygon name in sort
    order), so per-polygon counts add up to the regional total.
    Returns None when POLYID/FIREID are absent (FINN v1.5).
    """
    need = {"DAY", "POLYID", "FIREID", region_field, *group_cols}
    if not need <= set(joined.columns) or joined["POLYID"].isna().all():
        return None
    d = joined[[region_field, *group_cols, "DAY", "POLYID", "FIREID"]].copy()
    d["AREA_w"] = (pd.to_numeric(joined["AREA"], errors="coerce").fillna(0.0)
                   if "AREA" in joined.columns else 0.0)
    out = []
    for unit, idcol in (("events", "POLYID"), ("detections", "FIREID")):
        key = ["year", "sensor", "version", "DAY", idcol]
        dd = d[d[idcol].notna()]
        share = (dd.groupby(key + ["period", region_field], dropna=False)["AREA_w"]
                   .sum().reset_index())
        share = share.sort_values(key + ["AREA_w", region_field],
                                  ascending=[True] * len(key) + [False, True],
                                  kind="mergesort")
        first = share.drop_duplicates(subset=key, keep="first")
        out.append(first.groupby([region_field, *group_cols], dropna=False)
                        .size().rename(unit))
    # a polygon can hold a detection whose event is assigned to a neighbour -> 0, not NaN
    return pd.concat(out, axis=1).fillna(0).astype("int64")


def aggregate_by_region(df: pd.DataFrame,
                        shp: gpd.GeoDataFrame,
                        cfg: Dict[str, Any],
                        year: Optional[int] = None,
                        sensor: Optional[str] = None,
                        version: Optional[str] = None) -> pd.DataFrame:
    """Sum emissions per region polygon.

    Parameters
    ----------
    df   : converted, region-clipped emissions with LONGI/LATI columns.
    shp  : GeoDataFrame of region polygons (any polygon layer).
    cfg  : loaded config dict.
    year, sensor, version : metadata attached to every output row.

    Returns
    -------
    DataFrame with one row per polygon x period: ``n_rows``, ``events``,
    ``detections``, ``burned_km2``, summed emissions per FINN species and
    (optionally) ``NOx_as_NO2`` (2026-10-03 review; replaces ``focos``).
    """
    import geopandas as gpd

    region = cfg["region"]
    region_field = region["region_field"]
    if region_field not in shp.columns:
        raise KeyError(
            f"region_field '{region_field}' not found in the shapefile. "
            f"Set region.region_field in config to one of: {list(shp.columns)}"
        )
    tr = cfg.get("aggregation", {}).get("time_resolution", "year")  # day|month|year
    crs = f"EPSG:{region['crs_epsg']}"

    emiss = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df["LONGI"], df["LATI"]),
        crs=crs,
    )
    if emiss.crs != shp.crs:
        emiss = emiss.to_crs(shp.crs)

    # 2026-10-03 review: join ONLY the grouping attribute, so shapefile columns
    # (e.g. AREA_KM2, or any name clashing with a FINN field) never enter the
    # sums or get renamed *_left/*_right by sjoin.
    emiss = emiss.reset_index(drop=True)
    joined = gpd.sjoin(emiss, shp[[region_field, "geometry"]], how="inner", predicate="within")
    # 2026-10-03 review: a point inside two (overlapping) polygons would be
    # counted twice; keep the first match and report.
    n_multi = int(joined.index.duplicated().sum())
    if n_multi:
        print(f"  WARNING: {n_multi} point(s) fall in more than one polygon; "
              "each is kept once (first match).")
        joined = joined[~joined.index.duplicated(keep="first")]
    joined = pd.DataFrame(joined.drop(columns=["geometry", "index_right"], errors="ignore"))

    present = [c for c in FINN_SPECIES if c in joined.columns]

    # Temporal bucket `period` from DAY-of-year + year, at the chosen resolution.
    period = pd.Series(str(year), index=joined.index, dtype=object)
    if tr in ("day", "month") and "DAY" in joined.columns and year is not None:
        day = pd.to_numeric(joined["DAY"], errors="coerce")
        date = pd.to_datetime(f"{year}-01-01") + pd.to_timedelta(day - 1, unit="D")
        fmt = "%Y-%m-%d" if tr == "day" else "%Y-%m"
        valid = date.notna()
        period.loc[valid] = date[valid].dt.strftime(fmt)

    joined["period"] = period
    joined["year"] = year
    joined["sensor"] = sensor
    joined["version"] = version

    gcols = [region_field, "period", "year", "sensor", "version"]
    # 2026-10-03 review: burned area from FINN AREA (m2 -> km2).
    if "AREA" in joined.columns:
        joined["burned_km2"] = pd.to_numeric(joined["AREA"], errors="coerce") / 1e6
    grouped = joined.groupby(gcols, dropna=False)
    sum_cols = present + (["burned_km2"] if "burned_km2" in joined.columns else [])
    summary = grouped[sum_cols].sum(min_count=1)
    # 2026-10-03 review: the old `focos` (= number of rows) is replaced by
    # n_rows (records, diagnostic) + events + detections (see module docstring).
    summary.insert(0, "n_rows", grouped.size())
    units = count_fire_units(joined, region_field)
    if units is not None:
        summary = summary.join(units, how="left")
        summary[["events", "detections"]] = summary[["events", "detections"]].fillna(0).astype("int64")
    else:
        summary["events"] = pd.NA
        summary["detections"] = pd.NA
    if "NOXasNO" in summary.columns and (cfg.get("derived") or {}).get("nox_as_no2", True):
        summary["NOx_as_NO2"] = summary["NOXasNO"] * _M_NO2 / _M_NO
    lead = ["n_rows", "events", "detections"] + (["burned_km2"] if "burned_km2" in summary.columns else [])
    summary = summary[lead + [c for c in summary.columns if c not in lead]]
    return summary.reset_index()


# Backward-compatible alias (earlier scripts/notebooks referenced this name).
aggregate_by_municipality = aggregate_by_region

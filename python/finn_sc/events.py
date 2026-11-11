"""Fire events, detections and screening of persistent thermal anomalies (analysis layer).

Counting units (verified on the Santa Catarina records; docs/methodology.md, section 3):
    record    one row of a FINN v2.5/v2.5.1 "each fire" file = one (FIREID, GENVEG) piece
    detection distinct (year, sensor, version, DAY, FIREID)   -> one coordinate
    event     distinct (year, sensor, version, DAY, POLYID)   -> FINN daily burned-area polygon
              ("evento de queimada" in the manuscript and in the inventory report)
Wiedinmyer et al. (2023, GMD 16:3873, Sect. 2.2): adjacent or overlapping detections of the
same day are merged into one burned-area polygon, so one event may hold several detections.

Each event is assigned to ONE municipality, the one that holds the largest share of its AREA;
ties are broken by the alphabetical (code-point) order of the municipality name. Municipal
counts therefore add up to the state total.

Persistent thermal anomalies: criterion of the MODIS C6/C6.1 active-fire product for static
sources (detections on >= 16 distinct days of a calendar year; Giglio, Schroeder, Hall and
Justice, 2021, User's Guide v1.0, Sect. 5.5, Table 10), applied without a grid: for every
detection, the number of distinct days with detections within `radius_km` (great-circle
distance) in the same product-year is counted; a detection is flagged when that number is
>= `min_days`, and an event is flagged when any of its detections is flagged.
"""
from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd

PRODUCT = ["year", "sensor", "version"]
EVENT_KEY = PRODUCT + ["DAY", "POLYID"]
DET_KEY = PRODUCT + ["DAY", "FIREID"]
SPECIES = ["CO2", "CO", "CH4", "NMOC", "NOXasNO", "SO2", "NH3", "PM25", "PM10", "OC", "BC"]
EARTH_RADIUS_KM = 6371.0


def build_events(rec: pd.DataFrame, mun_col: str = "NM_MUN") -> pd.DataFrame:
    """One row per fire event with summed AREA (m2) and emissions (t), the number of
    records and detections, the mean record coordinate and the assigned municipality."""
    share = (rec.groupby(EVENT_KEY + [mun_col]).AREA.sum().rename("area").reset_index()
             .sort_values(["area", mun_col], ascending=[False, True], kind="mergesort"))
    ev_mun = share.drop_duplicates(EVENT_KEY)[EVENT_KEY + [mun_col]].rename(columns={mun_col: "mun_event"})
    agg = {"area_m2": ("AREA", "sum"), "n_rows": ("GENVEG", "size"), "n_det": ("FIREID", "nunique"),
           "lon": ("LONGI", "mean"), "lat": ("LATI", "mean"),
           "n_mun": (mun_col, "nunique")}
    for s in SPECIES:
        if s in rec.columns:
            agg[s] = (s, "sum")
    tot = rec.groupby(EVENT_KEY).agg(**agg).reset_index()
    return tot.merge(ev_mun, on=EVENT_KEY, how="left")


def _unit_xyz(lon_deg: np.ndarray, lat_deg: np.ndarray) -> np.ndarray:
    lo, la = np.radians(lon_deg), np.radians(lat_deg)
    return np.column_stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)])


def distinct_days_within(lon: np.ndarray, lat: np.ndarray, day: np.ndarray, radius_km: float) -> np.ndarray:
    """For each point, the number of distinct `day` values among points within
    `radius_km` (great-circle distance, sphere of radius 6371 km), itself included.

    Uses the equivalence: great-circle distance <= R  <=>  chord <= 2 sin(R / (2 R_E)).
    """
    from scipy.spatial import cKDTree
    xyz = _unit_xyz(np.asarray(lon, float), np.asarray(lat, float))
    chord = 2.0 * np.sin(radius_km / (2.0 * EARTH_RADIUS_KM))
    tree = cKDTree(xyz)
    nbrs = tree.query_ball_point(xyz, r=chord * (1 + 1e-12))
    day = np.asarray(day)
    return np.array([len(np.unique(day[idx])) for idx in nbrs], dtype=int)


def flag_persistent(rec: pd.DataFrame, radius_km: float = 1.0, min_days: int = 16,
                    sensors: Iterable[str] = ("MODIS+VIIRS", "MODIS")) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Screen persistent thermal anomalies.

    Returns (detections, flagged_events): `detections` holds one row per detection with
    `ndays` and `flag`; `flagged_events` holds the EVENT_KEY of every flagged event.
    The detection coordinate is the first record of the detection (records sorted by
    product, DAY, POLYID, FIREID, GENVEG).
    """
    d = rec[rec.sensor.isin(list(sensors))]
    det = (d.groupby(DET_KEY, sort=True)
             .agg(lon=("LONGI", "first"), lat=("LATI", "first"), POLYID=("POLYID", "first"),
                  NM_MUN=("NM_MUN", "first"))
             .reset_index())
    out = []
    for _, g in det.groupby(PRODUCT, sort=True):
        g = g.copy()
        g["ndays"] = distinct_days_within(g.lon.values, g.lat.values, g.DAY.values, radius_km)
        out.append(g)
    det = pd.concat(out, ignore_index=True)
    det["flag"] = det.ndays >= min_days
    flagged = det.loc[det.flag, EVENT_KEY].drop_duplicates().reset_index(drop=True)
    return det, flagged


def doy_to_month(year: Iterable[int], day: Iterable[int]) -> np.ndarray:
    """Calendar month of a day-of-year (FINN DAY, local date; Wiedinmyer et al., 2023)."""
    dates = pd.to_datetime(pd.Series(list(year)).astype(int).astype(str) + "-01-01") + \
        pd.to_timedelta(pd.Series(list(day)).astype(int) - 1, unit="D")
    return dates.dt.month.values

#!/usr/bin/env python3
"""tools/legacy_finn15_2020.py - FINN v1.5 totals of one year inside Santa Catarina, from the authors' legacy file.

Documents (and lets anyone with the legacy file re-run) the FINN v1.5 row of
data/external/legacy_finn15_lcqar_2020.csv, used to compare the 2020 state inventory (LCQAR, 2022) with FINN v1.5
and v2.5 (manuscript v6, Discussion; inventory report v3, section 3; tests/test_round5.py).

Input: the authors' `filtered_points_grid.csv` (original scripts, February 2026 run; ~480 MB; not distributed),
whose first column joins the source URL and DAY with a tab; FINN v1.5 rows come from
https://www.acom.ucar.edu/Data/fire/data/finn1/FINNv1.5_<year>.GEOSCHEM.tar.gz (GEOS-Chem speciation, MODIS only).
Species are already in tonnes (original conversion scripts); AREA is in m2.
Points are assigned to the IBGE 2024 municipalities by point in polygon (data/inputs/SC_Municipios_2024.shp).

Usage: python tools/legacy_finn15_2020.py <filtered_points_grid.csv> [year]
Output: printed summary and results/tables/legacy_finn15_<year>_SC.csv
"""
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
src = sys.argv[1]
year = int(sys.argv[2]) if len(sys.argv) > 2 else 2020
SPEC = ["GENVEG", "AREA", "CO2", "CO", "PM25", "NO", "NO2"]

hdr = pd.read_csv(src, nrows=0).columns.tolist()
first = hdr[0]                                   # "source_url<TAB>DAY"
use = [first] + SPEC + ["LONGI", "LATI", "year", "version"]
parts = []
for ch in pd.read_csv(src, usecols=use, chunksize=300_000, low_memory=False, dtype={"version": str}):
    ch = ch[(ch.year == year) & (ch.version.astype(str).str.strip() == "v1.5")].copy()
    if ch.empty:
        continue
    ch["DAY"] = ch[first].astype(str).str.split("\t").str[-1].str.strip().astype(int)
    parts.append(ch.drop(columns=[first]))
d = pd.concat(parts, ignore_index=True)
for c in SPEC:
    d[c] = pd.to_numeric(d[c], errors="coerce")

SHP = ROOT / "data" / "inputs" / "SC_Municipios_2024.shp"
try:
    shp = gpd.read_file(SHP, encoding="cp1252")
except UnicodeDecodeError:                       # older pyogrio ignores `encoding`; only the code and the geometry are needed
    shp = gpd.read_file(SHP, columns=["CD_MUN"])
shp = shp.to_crs(4674)
pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.LONGI, d.LATI), crs=4674)
s = gpd.sjoin(pts, shp[["CD_MUN", "geometry"]], how="inner", predicate="within")
s = s[~s.index.duplicated()]                     # a point on a shared border is counted once

veg = s.groupby("GENVEG")[["AREA", "CO2"]].sum()
row = {
    "year": year, "records": len(s), "day_location_combinations": len(s[["DAY", "LONGI", "LATI"]].drop_duplicates()),
    "CO2_t": s.CO2.sum(), "CO_t": s.CO.sum(), "PM25_t": s.PM25.sum(), "NO_plus_NO2_t": (s.NO + s.NO2).sum(),
    "area_km2": s.AREA.sum() / 1e6,
    "veg_code3_area_pct": 100 * veg.AREA.get(3, 0) / veg.AREA.sum(), "veg_code3_CO2_pct": 100 * veg.CO2.get(3, 0) / veg.CO2.sum(),
    "veg_code4_area_pct": 100 * veg.AREA.get(4, 0) / veg.AREA.sum(),
}
out = ROOT / "results" / "tables" / f"legacy_finn15_{year}_SC.csv"
out.parent.mkdir(parents=True, exist_ok=True)
pd.DataFrame([row]).to_csv(out, index=False)
for k, v in row.items():
    print(f"{k}: {v:,.1f}" if isinstance(v, float) else f"{k}: {v}")
print("by GENVEG (area km2, CO2 t):")
print((veg.assign(AREA=veg.AREA / 1e6)).round(1).to_string())
print("written", out)

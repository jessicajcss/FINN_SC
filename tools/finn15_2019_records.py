#!/usr/bin/env python3
"""tools/finn15_2019_records.py - FINN v1.5 records of 2019 inside Santa Catarina, from the authors' per-year file.

Input: the authors' `data/data_finn_2019/filtered_points_2019_MODIS_v1.5_converted_within_grid_newfuncao.txt` (original R
scripts, June 2025; FINN v1.5 GEOS-Chem annual file of 2019, MODIS, rows inside the grid box, species already in tonnes,
AREA in m2; not distributed). Points are assigned to the IBGE 2024 municipalities by point in polygon
(data/inputs/SC_Municipios_2024.shp), as for 2020 (tools/legacy_finn15_2020.py).
Usage: python tools/finn15_2019_records.py <filtered_points_2019_MODIS_v1.5_...txt>
Output: data/external/finn15_2019_SC_records.csv (DAY, GENVEG, AREA, CO2, CO, PM25, NO, NO2, LONGI, LATI, CD_MUN)
"""
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(sys.argv[1], usecols=["DAY", "GENVEG", "AREA", "CO2", "CO", "PM25", "NO", "NO2", "LONGI", "LATI"])
SHP = ROOT / "data" / "inputs" / "SC_Municipios_2024.shp"
try:
    shp = gpd.read_file(SHP, encoding="cp1252")
except UnicodeDecodeError:
    shp = gpd.read_file(SHP, columns=["CD_MUN"])
shp = shp.to_crs(4674)
pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.LONGI, d.LATI), crs=4674)
s = gpd.sjoin(pts, shp[["CD_MUN", "geometry"]], how="inner", predicate="within")
s = s[~s.index.duplicated()]
out = ROOT / "data" / "external" / "finn15_2019_SC_records.csv"
s.drop(columns=["geometry", "index_right"]).to_csv(out, index=False)
print(f"{len(d)} records in the file; {len(s)} inside SC; CO2 {s.CO2.sum():,.1f} t; CO {s.CO.sum():,.1f} t; "
      f"PM2.5 {s.PM25.sum():,.1f} t; area {s.AREA.sum() / 1e6:,.1f} km2 -> {out.relative_to(ROOT)}")

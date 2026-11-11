#!/usr/bin/env python3
"""Step 06 (route A) - build the record table used by the analysis layer.

Reads every region-clipped point file written by step 02
(data/interim/filtered_points_<year>_<sensor>_<version>_converted_within_grid.csv), attaches the
municipality that contains each record (point-in-polygon, predicate 'within', IBGE 2024 mesh) and
writes ONE table with the columns of the archived dataset:

    year, sensor, version, DAY, POLYID, FIREID, GENVEG, LONGI, LATI, AREA, BMASS,
    CO2, CO, CH4, NMOC, NOXasNO, SO2, NH3, PM25, PM10, OC, BC, CD_MUN, NM_MUN, source_file

Output: data/derived/finn_sc_records_rebuilt.csv.gz (the archived file
data/derived/finn_sc_records_2003_2025.csv.gz is never overwritten). Compare the two with
tools/compare_records.py. Run steps 00-02 first for every (year, version, sensor) needed:
    MODIS+VIIRS v2.5 2012-2021, MODIS+VIIRS v2.5.1 2022-2025, MODIS v2.5 2003-2021, MODIS v2.5.1 2022-2023.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from finn_sc import load_config, drop_exact_duplicates
from finn_sc.config import resolve

COLS = ["year", "sensor", "version", "DAY", "POLYID", "FIREID", "GENVEG", "LONGI", "LATI", "AREA", "BMASS",
        "CO2", "CO", "CH4", "NMOC", "NOXasNO", "SO2", "NH3", "PM25", "PM10", "OC", "BC", "CD_MUN", "NM_MUN", "source_file"]

cfg = load_config()
interim = resolve(cfg, cfg["paths"]["interim"])
files = sorted(interim.glob("filtered_points_*_within_grid.csv"))
if not files:
    raise FileNotFoundError(f"No filtered_points_*_within_grid.csv in {interim}. Run steps 00-02 first.")
import geopandas as gpd
shp = gpd.read_file(resolve(cfg, cfg["region"]["boundaries_shp"]), encoding="cp1252")
rf, cf = cfg["region"]["region_field"], cfg["region"].get("code_field")
parts, seen = [], set()
for p in files:
    m_year = re.search(r"\d{4}", p.name)
    m_sensor = re.search(r"MODIS\+VIIRS|MODIS|VIIRS", p.name)
    m_version = re.search(r"v[0-9]+(?:\.[0-9]+)*", p.name)
    key = (int(m_year.group()), m_sensor.group(), m_version.group())
    if key in seen:
        raise RuntimeError(f"two files for {key}")
    seen.add(key)
    d = drop_exact_duplicates(pd.read_csv(p), label=p.name)
    if d.empty:
        continue
    d.columns = [str(c).strip() for c in d.columns]
    d["year"], d["sensor"], d["version"] = key
    d["source_file"] = d["source_url"].astype(str).str.rsplit("/", n=1).str[-1] if "source_url" in d.columns else p.name
    pts = gpd.GeoDataFrame(d.reset_index(drop=True), geometry=gpd.points_from_xy(d.LONGI, d.LATI), crs=4326).to_crs(shp.crs)
    keep = [rf] + ([cf] if cf else [])
    j = gpd.sjoin(pts, shp[keep + ["geometry"]], how="inner", predicate="within")
    j = j[~j.index.duplicated(keep="first")]
    j = j.rename(columns={rf: "NM_MUN", **({cf: "CD_MUN"} if cf else {})})
    parts.append(pd.DataFrame(j.drop(columns=["geometry", "index_right"], errors="ignore")))
    print(f"{p.name}: {len(d)} records, {len(j)} inside a municipality")
rec = pd.concat(parts, ignore_index=True)
rec = rec[[c for c in COLS if c in rec.columns]].sort_values(
    ["sensor", "version", "year", "DAY", "POLYID", "FIREID", "GENVEG"], kind="mergesort")
out = resolve(cfg, "data/derived")
out.mkdir(parents=True, exist_ok=True)
rec.to_csv(out / "finn_sc_records_rebuilt.csv.gz", index=False, compression={"method": "gzip", "mtime": 0})
print("records:", len(rec), "->", out / "finn_sc_records_rebuilt.csv.gz")

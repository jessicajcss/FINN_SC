#!/usr/bin/env python3
"""Build data/derived/finn_sc_records_2003_2025.csv.gz from the authors' legacy grid file (provenance tool).

The legacy file `filtered_points_grid.csv` (Feb 2026 run of the authors' original R scripts, kept outside this repository: download, unit conversion and
clipping to a box around SC) holds the FINN records of every product-year in tonnes; its first column is
'source_url<TAB>DAY' (header written with a TAB by 00-download-FINN.R). This tool keeps the FINN v2.5/v2.5.1
records, splits that column, assigns each record to the IBGE 2024 municipality that contains its point
(tools/shp_pip.py: matplotlib Path, non-zero winding; no GIS dependency) and writes the archived table.
It was run on 2026-10-03 on the authors' machine:
    python tools/build_records_from_legacy.py <path>/filtered_points_grid.csv data/inputs/SC_Municipios_2024
Result: 817 168 input rows -> 258 694 SC records, 0 exact duplicates (docs/provenance.md, section 1).
"""
import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shp_pip import read_dbf, read_polygons, assign   # noqa: E402

SRC, SHP = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else "data/derived/finn_sc_records_2003_2025.csv.gz"
dbf = read_dbf(SHP + ".dbf")
names = [r["NM_MUN"] for r in dbf]
codes = dict(zip(names, [r["CD_MUN"] for r in dbf]))
polys = read_polygons(SHP + ".shp")
SPEC = ["CO2", "CO", "CH4", "NMOC", "NOXasNO", "SO2", "NH3", "PM25", "PM10", "OC", "BC"]
use = ["source_url\tDAY", "POLYID", "FIREID", "GENVEG", "AREA", "BMASS", "LONGI", "LATI", "year", "sensor", "version"] + SPEC
parts, n_in = [], 0
for ch in pd.read_csv(SRC, usecols=use, chunksize=500000, low_memory=False):
    n_in += len(ch)
    ch = ch[(ch.version != "v1.5") & ch.LONGI.between(-54.0, -48.2) & ch.LATI.between(-29.5, -25.9)]
    if len(ch):
        sd = ch["source_url\tDAY"].astype(str).str.split("\t")
        ch = ch.assign(source_file=sd.str[0].str.rsplit("/", n=1).str[-1],
                       DAY=sd.str[-1].astype(float).astype(int)).drop(columns=["source_url\tDAY"])
        parts.append(ch)
d = pd.concat(parts, ignore_index=True)
d["NM_MUN"] = assign(d.LONGI.values, d.LATI.values, polys, names)
d = d[d.NM_MUN != ""].copy()
d["CD_MUN"] = d.NM_MUN.map(codes)
n0 = len(d)
d = d.drop_duplicates()
cols = ["year", "sensor", "version", "DAY", "POLYID", "FIREID", "GENVEG", "LONGI", "LATI", "AREA", "BMASS"] + SPEC + ["CD_MUN", "NM_MUN", "source_file"]
d = d[cols].sort_values(["sensor", "version", "year", "DAY", "POLYID", "FIREID", "GENVEG"], kind="mergesort")
d.to_csv(OUT, index=False, compression={"method": "gzip", "mtime": 0})
print("input rows", n_in, "| SC records", len(d), "| exact duplicates dropped", n0 - len(d))

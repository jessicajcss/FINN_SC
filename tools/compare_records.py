#!/usr/bin/env python3
"""Compare a record table rebuilt by route A (python/06_build_sc_records.py) with the archived one.

Usage: python tools/compare_records.py [rebuilt.csv.gz] [archived.csv.gz]
Only the (year, sensor, version, DAY) present in the rebuilt table are compared, so a partial
download (e.g. a few days of the NRT product) can be checked against the archive.
Matching key: (year, sensor, version, DAY, POLYID, FIREID, GENVEG, LONGI, LATI, AREA); FINN files can hold
records that share (DAY, POLYID, FIREID, GENVEG) with different AREA (docs/methodology.md), so AREA and the
coordinates are part of the key. Reports unmatched records and the maximum relative difference per species.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
reb = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data/derived/finn_sc_records_rebuilt.csv.gz"
arc = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "data/derived/finn_sc_records_2003_2025.csv.gz"
A, B = pd.read_csv(reb), pd.read_csv(arc)
days = A[["year", "sensor", "version", "DAY"]].drop_duplicates()
B = B.merge(days, on=["year", "sensor", "version", "DAY"])
KEY = ["year", "sensor", "version", "DAY", "POLYID", "FIREID", "GENVEG", "LONGI", "LATI", "AREA"]
for d in (A, B):
    d["k"] = d.groupby(KEY).cumcount()
m = A.merge(B, on=KEY + ["k"], how="outer", suffixes=("_reb", "_arc"), indicator=True)
print(f"rebuilt {len(A)} | archived (same days) {len(B)} | matched {int((m._merge == 'both').sum())} | "
      f"only rebuilt {int((m._merge == 'left_only').sum())} | only archived {int((m._merge == 'right_only').sum())}")
b = m[m._merge == "both"]
print("municipality differences:", int((b.NM_MUN_reb != b.NM_MUN_arc).sum()))
for s in ["CO2", "CO", "CH4", "NMOC", "NOXasNO", "SO2", "NH3", "PM25", "PM10", "OC", "BC", "BMASS"]:
    if f"{s}_reb" in b:
        x, y = b[f"{s}_reb"].astype(float), b[f"{s}_arc"].astype(float)
        rel = (np.abs(x - y) / np.maximum(np.abs(y), 1e-30)).max()
        print(f"  {s:8s} max relative difference {rel:.2e}")
sys.exit(0 if (m._merge == "both").all() else 1)

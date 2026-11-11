#!/usr/bin/env python3
"""Step 4 (optional) - stack SC-clipped point files across years (Python).
Run: python python/03_stack_years.py

Combines all filtered_points_*_within_grid.csv files under data/interim/ into a
single long table tagged with year/sensor/version parsed from the file name.
Mirrors R/03_stack_years.R.

2026-10-03 review: duplicate guards - (1) two input files that resolve to the
same (year, sensor, version) stop the run (that is how the old
aggregated_emissions_all.csv got the 2011 MODIS v2.5 rows twice); (2) exact
duplicate rows are dropped and repeated record keys are reported.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from finn_sc import load_config, drop_exact_duplicates   # 2026-10-03 review
from finn_sc.config import resolve

cfg = load_config()
interim = resolve(cfg, cfg["paths"]["interim"])
out_dir = resolve(cfg, cfg["paths"]["output"])
out_dir.mkdir(parents=True, exist_ok=True)

files = sorted(interim.glob("filtered_points_*_within_grid.csv"))
if not files:
    raise FileNotFoundError(f"No filtered_points_*_within_grid.csv in {interim}. Run step 02 first.")

frames = []
seen_keys = {}                      # 2026-10-03 review: one file per (year, sensor, version)
for p in files:
    m_year = re.search(r"\d{4}", p.name)
    m_sensor = re.search(r"MODIS\+VIIRS|MODIS|VIIRS", p.name)
    m_version = re.search(r"v[0-9]+(?:\.[0-9]+)*", p.name)
    fkey = (m_year.group() if m_year else None, m_sensor.group() if m_sensor else None,
            m_version.group() if m_version else None)
    if fkey in seen_keys:
        raise RuntimeError(f"Two input files map to the same (year, sensor, version) {fkey}: "
                           f"{seen_keys[fkey]} and {p.name}. Remove one to avoid double counting.")
    seen_keys[fkey] = p.name
    df = drop_exact_duplicates(pd.read_csv(p), label=p.name)
    df["year"] = int(m_year.group()) if m_year else None
    df["sensor"] = m_sensor.group() if m_sensor else None
    df["version"] = m_version.group() if m_version else None
    df["path"] = str(p)
    frames.append(df)

stacked = pd.concat(frames, ignore_index=True)
out_path = out_dir / "filtered_points_stacked.csv"
stacked.to_csv(out_path, index=False)
print(f"Stacked {len(files)} files, {len(stacked)} rows -> {out_path}")

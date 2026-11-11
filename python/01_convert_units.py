#!/usr/bin/env python3
"""Step 2 - convert FINN units to tonnes (Python).  Run: python python/01_convert_units.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from finn_sc import load_config, convert_finn_units, date_bounds, selected_years, filter_rows_by_date
from finn_sc.config import resolve

cfg = load_config()
sel = cfg["selection"]
bounds = date_bounds(cfg)          # None unless start_date/end_date are set
raw_dir = resolve(cfg, cfg["paths"]["raw_finn"])
interim = resolve(cfg, cfg["paths"]["interim"])
interim.mkdir(parents=True, exist_ok=True)

for year in selected_years(cfg):
    in_path = raw_dir / f"{year}_finn_{sel['version']}_{sel['sensor']}.csv"
    if not in_path.is_file():
        print(f"Missing {in_path}; run step 00 first. Skipping.")
        continue
    print(f"Converting units for {year} ...")
    try:
        df = pd.read_csv(in_path)
    except pd.errors.EmptyDataError:
        print(f"  {in_path.name} is empty (no FINN files matched, or all "
              f"downloads 404'd for this selection). Nothing to convert; "
              f"skipping. Check config.selection (version/sensor/dates) and the "
              f"step 00 log above.")
        continue
    if df.empty:
        print(f"  {in_path.name} has 0 data rows; skipping.")
        continue
    out = convert_finn_units(df, cfg)
    # Keep only rows within the exact date range (adds a DATE column), if set.
    if bounds:
        out = filter_rows_by_date(out, year, bounds[0], bounds[1])
        print(f"  date-filtered to {bounds[0]}..{bounds[1]}: {len(out)} rows")
    out_path = interim / f"{year}_finn_{sel['version']}_{sel['sensor']}_converted.csv"
    out.to_csv(out_path, index=False)
    print("  saved:", out_path)

print("\nStep 01 complete. Converted files are in:", cfg["paths"]["interim"])

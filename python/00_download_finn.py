#!/usr/bin/env python3
"""Step 1 - download & merge FINN files (Python).  Run: python python/00_download_finn.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))  # make finn_sc importable

from finn_sc import (load_config, build_finn_urls, filter_finn_urls,
                     filter_finn_by_date, download_finn_files,
                     date_bounds, selected_years)
from finn_sc.config import resolve

cfg = load_config()
sel = cfg["selection"]
bounds = date_bounds(cfg)          # None unless start_date/end_date are set
years = selected_years(cfg)
all_urls = build_finn_urls()
if bounds:
    print(f"Date selection: {bounds[0]} .. {bounds[1]} "
          "(only the file(s) overlapping this range are downloaded)")

for year in years:
    print(f"\n=== Downloading FINN {sel['version']} / {sel['sensor']} / {year} ===")
    urls = filter_finn_urls(all_urls, version=sel["version"], sensor=sel["sensor"], year=year)
    if bounds:
        urls = filter_finn_by_date(urls, bounds[0], bounds[1])
    if not urls:
        print("No FINN files match this selection; skipping.")
        continue
    out_name = f"{year}_finn_{sel['version']}_{sel['sensor']}.csv"
    download_finn_files(
        urls,
        dest_folder=resolve(cfg, cfg["paths"]["raw_finn"]),
        combined_filename=out_name,
        include_source_url=cfg["download"]["include_source_url"],
        min_file_size_kb=cfg["download"]["min_file_size_kb"],
        timeout_seconds=cfg["download"]["timeout_seconds"],
    )
print("\nStep 00 complete. Combined FINN files are in:", cfg["paths"]["raw_finn"])

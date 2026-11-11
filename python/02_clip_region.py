#!/usr/bin/env python3
"""Step 3 - clip the global FINN cloud to the study region (Python).
Run: python python/02_clip_region.py

The bounding box comes from config (region.bbox): 'auto' derives it from the
boundaries shapefile's extent (works for ANY region), 'none' skips the
pre-filter, or explicit degrees are used as given. Default region: Santa
Catarina; point region.boundaries_shp at any shapefile to change it.

2026-10-03 review: after the bbox pre-filter, points are now also restricted to
the study POLYGONS (point-in-polygon, predicate "within"), so the
filtered_points_*_within_grid.csv files (and the stacked table of step 03)
no longer contain points of neighbouring states / countries / the ocean.
The boundaries shapefile is therefore required.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from finn_sc import load_config, clip_to_region, selected_years  # 2026-10-03 review
from finn_sc.config import resolve

cfg = load_config()
sel = cfg["selection"]
years = selected_years(cfg)
interim = resolve(cfg, cfg["paths"]["interim"])

# 2026-10-03 review: the boundaries shapefile is now REQUIRED (point-in-polygon
# clip), not only when region.bbox == 'auto'.
shp_path = resolve(cfg, cfg["region"]["boundaries_shp"])
if not shp_path.is_file():
    raise FileNotFoundError(
        f"Boundaries shapefile not found at {shp_path}. Step 02 restricts points "
        "to the study polygons, so the shapefile is required (see data/inputs/README)."
    )
import geopandas as gpd
shp = gpd.read_file(shp_path)

for year in years:
    in_path = interim / f"{year}_finn_{sel['version']}_{sel['sensor']}_converted.csv"
    if not in_path.is_file():
        print(f"Missing {in_path}; run step 01 first. Skipping.")
        continue
    print(f"Clipping {year} to region '{cfg['region']['name']}' ...")
    df = pd.read_csv(in_path)
    clipped = clip_to_region(df, cfg, shp)   # 2026-10-03 review: bbox + polygons
    # File name kept for compatibility ("within_grid"); content is now in-polygon.
    out_path = interim / f"filtered_points_{year}_{sel['sensor']}_{sel['version']}_converted_within_grid.csv"
    clipped.to_csv(out_path, index=False)
    print(f"  kept {len(clipped)} of {len(df)} records inside the region polygons -> {out_path}")

print("\nStep 02 complete. Region-clipped files are in:", cfg["paths"]["interim"])

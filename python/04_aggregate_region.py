#!/usr/bin/env python3
"""Step 5 - aggregate emissions per region polygon (Python).
Run: python python/04_aggregate_region.py

Joins FINN fire points to ANY polygon layer and sums each FINN species per
polygon, grouping on config region.region_field. Default: IBGE Santa Catarina
municipalities (region_field = "NM_MUN"). For another region, set
region.boundaries_shp and region.region_field in config.

2026-10-03 review: output columns n_rows / events / detections / burned_km2 /
NOx_as_NO2 replace the old `focos` row count (see finn_sc/aggregate.py), and
duplicate guards were added: one input file per (year, sensor, version),
exact duplicate rows dropped, and a final check that every
(region, period, year, sensor, version) row is unique.
"""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import geopandas as gpd
import pandas as pd
from finn_sc import load_config, aggregate_by_region, drop_exact_duplicates  # 2026-10-03 review
from finn_sc.config import resolve

cfg = load_config()
region_field = cfg["region"]["region_field"]

shp_path = resolve(cfg, cfg["region"]["boundaries_shp"])
if not shp_path.is_file():
    raise FileNotFoundError(
        f"Boundaries shapefile not found at {shp_path}. Place your region "
        "shapefile there (default: IBGE SC municipalities; see data/inputs/README)."
    )
shp = gpd.read_file(shp_path)
if region_field not in shp.columns:
    raise KeyError(
        f"region.region_field '{region_field}' not found in the shapefile. "
        f"Available columns: {list(shp.columns)}"
    )

interim = resolve(cfg, cfg["paths"]["interim"])
files = sorted(interim.glob("filtered_points_*_within_grid.csv"))
if not files:
    raise FileNotFoundError(f"No region-clipped files in {interim}. Run step 02 first.")

summaries = []
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
    df = drop_exact_duplicates(pd.read_csv(p), label=p.name)   # 2026-10-03 review
    if not {"LONGI", "LATI"}.issubset(df.columns):
        print(f"No coordinates in {p.name}; skipping.")
        continue
    summaries.append(aggregate_by_region(
        df, shp, cfg,
        year=int(m_year.group()) if m_year else None,
        sensor=m_sensor.group() if m_sensor else None,
        version=m_version.group() if m_version else None,
    ))

all_summaries = pd.concat(summaries, ignore_index=True)

# 2026-10-03 review: final guard - each polygon/period/product appears once.
_k = [region_field, "period", "year", "sensor", "version"]
_dup = all_summaries.duplicated(_k, keep=False)
if _dup.any():
    raise RuntimeError(f"{int(_dup.sum())} duplicated {_k} rows in the aggregated table:\n"
                       f"{all_summaries.loc[_dup, _k].head(10)}")

# Join totals back onto polygon geometry.
final = shp.merge(all_summaries, on=region_field, how="left")

out_dir = resolve(cfg, cfg["paths"]["output"])
out_dir.mkdir(parents=True, exist_ok=True)

out_csv = out_dir / "aggregated_emissions_all.csv"
pd.DataFrame(final.drop(columns="geometry")).to_csv(out_csv, index=False)
print("Saved:", out_csv)

# Shapefile with ESRI 10-char field-name limit.
final_shp = final.copy()
final_shp.columns = [c[:10] for c in final_shp.columns]
out_shp = out_dir / "aggregated_emissions_all.shp"
final_shp.to_file(out_shp)
print("Saved:", out_shp)

print("\nStep 04 complete. Region-level inventory in:", cfg["paths"]["output"])

#!/usr/bin/env python3
"""Step 6 - descriptive plots & summary tables (Python).
Run: python python/05_descriptive_analysis.py

Outputs are named after the *period / resolution actually run* (config
aggregation.time_resolution: day | month | year), so a 7-day window produces
day-grain figures - not a degenerate single 'annual' bar. Files written:

    overview_<res>.png        bar 4-panel (fires, area, CO, PM2.5) by period
    timeseries_<res>.png      line 4-panel (fires, CO, PM2.5, CO2) by period
    period_summary_<res>.csv  per-period totals table

A by-year rollup (overview_by_year.png + summary_by_year.csv) is added ONLY
when the data actually span >= 2 calendar years; otherwise it is skipped with a
note, because a single-year/partial run has nothing to compare across years.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
from finn_sc import load_config
from finn_sc.config import resolve
from finn_sc.dates import coverage_note
from finn_sc.plots import (period_4panel, period_timeseries, period_summary_table,
                           annual_4panel, annual_summary_table, distinct_years)

cfg = load_config()
out_dir = resolve(cfg, cfg["paths"]["output"])
agg_path = out_dir / "aggregated_emissions_all.csv"
if not agg_path.is_file():
    raise FileNotFoundError(f"Missing {agg_path}; run step 04 first.")

data_aggregated = pd.read_csv(agg_path)
V, S = cfg["selection"]["version"], cfg["selection"]["sensor"]
res = cfg.get("aggregation", {}).get("time_resolution", "year")

# --- Primary outputs: named after the period / resolution actually run --------
ov_path = period_4panel(data_aggregated, V, S,
                        out_dir / f"overview_{res}.png", resolution=res)
print("Saved:", ov_path)

ts_path = period_timeseries(data_aggregated, V, S,
                            out_dir / f"timeseries_{res}.png", resolution=res)
print("Saved:", ts_path)

pt = period_summary_table(data_aggregated, V, S, out_dir / f"period_summary_{res}.csv")
print("Saved:", out_dir / f"period_summary_{res}.csv")
if not pt.empty:
    print(pt.to_string(index=False))

# Which requested periods actually had fires inside the region (so a multi-day
# range that yields a single bar is self-explanatory, not mistaken for a bug).
periods_present = pt["period"].tolist() if "period" in pt.columns else []
print(coverage_note(cfg, periods_present, res))

# --- By-year rollup: only meaningful when the data span >= 2 distinct years ---
years = distinct_years(data_aggregated, V, S)
if len(years) >= 2:
    fig_path = annual_4panel(data_aggregated, V, S, out_dir / "overview_by_year.png")
    print("Saved:", fig_path)
    tbl = annual_summary_table(data_aggregated, V, S, out_dir / "summary_by_year.csv")
    print("Saved:", out_dir / "summary_by_year.csv")
    print(tbl.to_string(index=False))
else:
    span = years[0] if years else "no fires found"
    print(f"By-year rollup skipped: data span a single year ({span}). "
          f"The '{res}'-grain outputs above already describe this run.")

print("\nStep 05 complete. Figures and tables in:", cfg["paths"]["output"])

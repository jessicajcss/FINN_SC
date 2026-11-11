#!/usr/bin/env python3
"""a02 - annual state series, Table 2, effect of adding VIIRS, Mann-Kendall trends.

Events exclude the persistent thermal anomalies (a01); burned area and emissions keep every
FINN record (the inventory as distributed). NOx = NOXasNO (mass as NO); COV = NMOC.
Outputs: results/tables/table2_state_emissions_2012_2025.csv, series_state_all_products.csv,
         viirs_effect.csv, mann_kendall.csv; results/logs/a02_series_trends.txt
Manuscript (v3.2): Table 2, Figure 2, Tables S1, S2 and S5, sections 2.6 and 3 (Mann-Kendall, Sen, lag-1
autocorrelation, Hamed-Rao test). Inventory report: Table 2, section 3, Appendix A.
"""
from _setup import TAB, Log, load_records, screened_events
import pandas as pd
from finn_sc.stats import mann_kendall, lag1_autocorrelation
try:                                     # modified test for autocorrelated data (Hamed and Rao, 1998)
    import pymannkendall as pmk
except ImportError:                      # optional; the column is then left empty
    pmk = None

L = Log("a02_series_trends")
SP = ["CO2", "CO", "PM25", "OC", "NOXasNO", "CH4", "NH3", "NMOC", "BC", "SO2"]
rec = load_records()
E = screened_events()
prod = ["year", "sensor", "version"]

S = rec.groupby(prod).agg(area_km2=("AREA", lambda a: a.sum() / 1e6), **{s: (s, "sum") for s in SP}).reset_index()
S = S.merge(E[~E.flag].groupby(prod).size().rename("events").reset_index(), on=prod, how="left")
S.to_csv(TAB / "series_state_all_products.csv", index=False)

mv = S[S.sensor == "MODIS+VIIRS"].set_index("year").sort_index()
T2 = mv[SP].copy()
T2.to_csv(TAB / "table2_state_emissions_2012_2025.csv")
L("Table 2 (t/yr; NOx as NO; COV = NMOC):")
L(T2.round(0).astype("int64").to_string())
L("events (screened) 2012-2025:", mv.events.to_dict())
L(f"events: max {mv.events.max()} ({mv.events.idxmax()}), min {mv.events.min()} ({mv.events.idxmin()}), mean {mv.events.mean():.1f}")
L(f"events mean 2022-2025 {mv.events.loc[2022:2025].mean():.1f}, sample SD {mv.events.loc[2022:2025].std(ddof=1):.1f}")
for y0, y1 in ((2020, 2023), (2023, 2024), (2024, 2025)):
    L(f"events change {y0}->{y1}: {100 * (mv.events[y1] / mv.events[y0] - 1):+.2f}%")
for y0, y1 in ((2023, 2024), (2024, 2025), (2020, 2023)):
    ch = 100 * (T2.loc[y1] / T2.loc[y0] - 1)
    L(f"emission change {y0}->{y1} (%):", ch.round(2).to_dict(), f"| min {ch.idxmin()} {ch.min():.2f} | max {ch.idxmax()} {ch.max():.2f}")
L("year of maximum per species:", T2.idxmax().to_dict())
L(f"area km2: 2020 {mv.area_km2[2020]:.1f}; 2023 {mv.area_km2[2023]:.1f}; 2024 {mv.area_km2[2024]:.1f}; 2025 {mv.area_km2[2025]:.1f}; "
  f"max {mv.area_km2.idxmax()}")
from scipy.stats import spearmanr
r = spearmanr(mv.events, mv.area_km2)
L(f"Spearman events vs area 2012-2025: rho = {r[0]:.3f} (n = {len(mv)})")

# VIIRS effect: MODIS+VIIRS relative to MODIS-only, same version and year
mo = S[S.sensor == "MODIS"].set_index(["year", "version"])
mvv = S[S.sensor == "MODIS+VIIRS"].set_index(["year", "version"])
V = pd.DataFrame({"events_ratio": mvv.events / mo.events})
for c in ["area_km2", "CO2", "CO", "PM25", "NOXasNO"]:
    V[c + "_inc_pct"] = 100 * (mvv[c] / mo[c] - 1)
V = V.dropna().reset_index()
V.to_csv(TAB / "viirs_effect.csv", index=False)
v25 = V[V.version == "v2.5"].set_index("year")
L("VIIRS effect, v2.5 2012-2021:")
for c in V.columns[2:]:
    L(f"  {c}: {v25[c].min():.2f} ({v25[c].idxmin()}) to {v25[c].max():.2f} ({v25[c].idxmax()})")
L("  across CO2, CO, PM25, NOXasNO: "
  f"{v25[['CO2_inc_pct', 'CO_inc_pct', 'PM25_inc_pct', 'NOXasNO_inc_pct']].min().min():.1f}% to "
  f"{v25[['CO2_inc_pct', 'CO_inc_pct', 'PM25_inc_pct', 'NOXasNO_inc_pct']].max().max():.1f}%")
L("VIIRS effect, v2.5.1 (2022-2023):", V[V.version == "v2.5.1"].round(2).to_dict("records"))

# Mann-Kendall
rows = []
ser = pd.DataFrame({"events": mv.events, "area_km2": mv.area_km2, "CO2_t": mv.CO2, "PM25_t": mv.PM25})
for c in ser.columns:
    for lab, yy in (("2012-2025", ser[c]), ("2012-2021", ser[c].loc[2012:2021])):
        m = mann_kendall(yy.values)
        m.update(variable=c, period=lab, r1=lag1_autocorrelation(yy.values),
                 p_hamed_rao=pmk.hamed_rao_modification_test(yy.values).p if pmk else float("nan"))
        rows.append(m)
MK = pd.DataFrame(rows)[["variable", "period", "n", "S", "tau", "z", "p", "sen", "sen_pct_mean", "r1", "p_hamed_rao"]]
MK.to_csv(TAB / "mann_kendall.csv", index=False)
L(MK.round(3).to_string(index=False))
L.save()

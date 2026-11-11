#!/usr/bin/env python3
"""a12 - results of the Earth Engine notebooks of the co-authors' review (run by the authors in Colab on 2026-10-21;
manuscript v.6.2, Supplementary Material v3.4).

  1  mcd64a1_comparison_state.csv     MCD64A1 burned area (gee/mcd64a1_municipal_2012_2024.ipynb) by year, with the
     mcd64a1_comparison_summary.csv   MapBiomas Fogo Collection 4 area and the FINN area (MODIS+VIIRS records), the
                                      ratios, the number of municipalities with mapped area, correlations of the State
                                      series and of the municipal values, shares of the Serrana and changes 2020-2023
                                      and 2023-2024 (comment C11)
  2  climate_serrana_correlations.csv Spearman correlations of the annual State responses (screened events, FINN area,
                                      CO2) and of the Serrana events with the July-November and July-September climate
                                      of the State and of the Serrana (gee/era5land_serrana_monthly.ipynb), with Holm
                                      adjustment over the four climate predictors of each response, climate region and
                                      period, and the same correlations without 2015 and 2023 (comments C12 and C27)
  3  landcover_figure1_2019_2023.csv  State shares of the legend groups of Figure 1 in 2019 (Collection 10) and 2023
                                      (Collection 10.1, gee/mapbiomas_lulc2023_figure1.ipynb) (comment C4)

Log: results/logs/a12_gee_review_outputs.txt
"""
import warnings
warnings.filterwarnings("ignore")
from _setup import CFG, TAB, Log, path, load_records, screened_events, municipalities
import numpy as np
import pandas as pd
from scipy import stats
from finn_sc.stats import holm

L = Log("a12_gee_review_outputs")
mu = municipalities()
MESO_CD = dict(zip(mu.CD_MUN, mu.mesorregiao))
MESO_NM = dict(zip(mu.NM_MUN, mu.mesorregiao))
rec = load_records("MV")

# ------------------------------------------------------------------ 1. MCD64A1 vs MapBiomas Fogo vs FINN (2012-2024)
L("1. MCD64A1 (MODIS C6.1 burned area, 500 m) vs MapBiomas Fogo Collection 4 (30 m) vs FINN (MODIS+VIIRS), 2012-2024")
mcd = pd.read_csv(path("mcd64a1"))
assert len(mcd) == 295 * 13 and mcd.CD_MUN.nunique() == 295 and (mcd.burned_km2 >= 0).all()
mb = pd.read_csv(path("mapbiomas_fire"))
r = rec[rec.year.between(2012, 2024)]
finn = r.groupby(["year", "CD_MUN"]).AREA.sum().div(1e6).rename("finn_km2")
D = pd.concat([mcd.set_index(["year", "CD_MUN"]).burned_km2.rename("mcd_km2"),
               mb.set_index(["year", "CD_MUN"]).burned_km2.rename("mb_km2"), finn], axis=1).fillna(0).reset_index()
assert len(D) == 295 * 13
S = D.groupby("year")[["mcd_km2", "mb_km2", "finn_km2"]].sum()
S["finn_over_mcd"] = S.finn_km2 / S.mcd_km2
S["mb_over_mcd"] = S.mb_km2 / S.mcd_km2
S["finn_over_mb"] = S.finn_km2 / S.mb_km2
S["municipalities_mcd"] = D[D.mcd_km2 > 0].groupby("year").size()
S["municipalities_mb"] = D[D.mb_km2 > 0].groupby("year").size()
S["top10_share_mcd_pct"] = D.groupby("year").apply(lambda g: 100 * g.nlargest(10, "mcd_km2").mcd_km2.sum() / g.mcd_km2.sum())
S.round(4).to_csv(TAB / "mcd64a1_comparison_state.csv")
L(S.round(2).to_string())
rows = []
add = lambda metric, value, note="": rows.append(dict(metric=metric, value=value, note=note))
add("median_finn_over_mcd", S.finn_over_mcd.median()); add("median_mb_over_mcd", S.mb_over_mcd.median())
add("median_finn_over_mb", S.finn_over_mb.median())
add("mcd_over_mb_min", (S.mcd_km2 / S.mb_km2).min()); add("mcd_over_mb_max", (S.mcd_km2 / S.mb_km2).max())
for a, b in (("mcd_km2", "mb_km2"), ("mcd_km2", "finn_km2")):
    pr, pp = stats.pearsonr(S[a], S[b]); sr, sp = stats.spearmanr(S[a], S[b])
    tag = a.split("_")[0] + "_" + b.split("_")[0]
    add(f"state_pearson_{tag}", pr, f"p = {pp:.4f}; n = 13"); add(f"state_pearson_p_{tag}", pp)
    add(f"state_spearman_{tag}", sr, f"p = {sp:.4f}; n = 13"); add(f"state_spearman_p_{tag}", sp)
    L(f"State series {a} vs {b}: Pearson r = {pr:.3f} (p = {pp:.4f}); Spearman rho = {sr:.3f} (p = {sp:.4f}); n = 13")
    rr = [stats.spearmanr(g[a], g[b])[0] for _, g in D.groupby("year")]
    add(f"municipal_spearman_min_{tag}", min(rr), "per year, n = 295"); add(f"municipal_spearman_max_{tag}", max(rr), "per year, n = 295")
    L(f"municipal Spearman {a} vs {b} per year (n = 295): {min(rr):.2f} to {max(rr):.2f}")
T = D.groupby("CD_MUN")[["mcd_km2", "mb_km2", "finn_km2"]].sum()
for a, b in (("mcd_km2", "mb_km2"), ("mcd_km2", "finn_km2"), ("mb_km2", "finn_km2")):
    sr, sp = stats.spearmanr(T[a], T[b])
    tag = a.split("_")[0] + "_" + b.split("_")[0]
    add(f"municipal_total_spearman_{tag}", sr, f"2012-2024 totals, n = 295, p = {sp:.2g}")
    L(f"2012-2024 municipal totals {a} vs {b}: Spearman rho = {sr:.2f} (p = {sp:.2g}; n = 295)")
add("municipalities_mcd_any_year", int((T.mcd_km2 > 0).sum()))
T["meso"] = T.index.map(MESO_CD)
M = T.groupby("meso")[["mcd_km2", "mb_km2", "finn_km2"]].sum()
sh = 100 * M / M.sum()
for c in sh.columns:
    add(f"serrana_share_pct_{c.split('_')[0]}", sh.loc["Serrana", c], "2012-2024")
L("share of each mesoregion, 2012-2024 (%):"); L(sh.round(1).to_string())
for c in ("mcd_km2", "mb_km2", "finn_km2"):
    add(f"change_2020_2023_pct_{c.split('_')[0]}", 100 * (S.loc[2023, c] / S.loc[2020, c] - 1))
    add(f"change_2023_2024_pct_{c.split('_')[0]}", 100 * (S.loc[2024, c] / S.loc[2023, c] - 1))
L("change 2020-2023 (%):", {c: round(100 * (S.loc[2023, c] / S.loc[2020, c] - 1), 1) for c in ("mcd_km2", "mb_km2", "finn_km2")},
  "| change 2023-2024 (%):", {c: round(100 * (S.loc[2024, c] / S.loc[2023, c] - 1), 1) for c in ("mcd_km2", "mb_km2", "finn_km2")})
pd.DataFrame(rows).to_csv(TAB / "mcd64a1_comparison_summary.csv", index=False)

# ------------------------------------------------------------------ 2. climate of the Serrana and July-September
L("\n2. ERA5-Land climate of the State and of the Serrana, July-November and July-September, 2012-2025")
clim = pd.read_csv(path("era5land_serrana"))
assert clim.groupby("region").size().to_dict() == {"Santa Catarina": 168, "Serrana": 168}
def season(months):
    s = clim[clim.month.isin(months)].groupby(["region", "year"])
    return s.agg(precip_mm=("precip_mm", "sum"), Tc=("Tc", "mean"), VPD_kPa=("VPD_kPa", "mean"), soil_moist=("soil_moist", "mean"))
SEAS = {"Jul-Nov": season(CFG["analysis"]["fire_season_months"]), "Jul-Sep": season([7, 8, 9])}
arch = pd.read_csv(path("climate")).set_index("year")
new = SEAS["Jul-Nov"].loc["Santa Catarina"]
dmax = {v: float((new[v] - arch[v + "_fs"]).abs().max()) for v in ("precip_mm", "Tc", "VPD_kPa", "soil_moist")}
L("check against the archived State July-November climate (a06 input), max |difference|:", {k: round(v, 4) for k, v in dmax.items()})
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)].copy()
E["meso"] = E.mun_event.map(MESO_NM)
assert E.meso.notna().all()
y0, y1 = CFG["analysis"]["series_years"]
RESP = {"State events": E.groupby("year").size(), "State FINN area": rec.groupby("year").AREA.sum() / 1e6,
        "State CO2": rec.groupby("year").CO2.sum(), "Serrana events": E[E.meso == "Serrana"].groupby("year").size()}
PRED = ["precip_mm", "Tc", "VPD_kPa", "soil_moist"]
rows = []
for rname, y in RESP.items():
    y = y.loc[y0:y1]
    for region in ("Santa Catarina", "Serrana"):
        for period, tab in SEAS.items():
            X = tab.loc[region].loc[y0:y1]
            res = [stats.spearmanr(y, X[v]) for v in PRED]
            keep = ~X.index.isin([2015, 2023])
            res_ex = [stats.spearmanr(y[keep], X[v][keep]) for v in PRED]
            ph, ph_ex = holm([q[1] for q in res]), holm([q[1] for q in res_ex])
            for v, q, h, qe, he in zip(PRED, res, ph, res_ex, ph_ex):
                rows.append(dict(response=rname, climate=region, period=period, predictor=v, n=len(y), rho=q[0], p=q[1],
                                 p_holm=h, n_without_2015_2023=int(keep.sum()), rho_without_2015_2023=qe[0],
                                 p_without_2015_2023=qe[1], p_holm_without_2015_2023=he))
C = pd.DataFrame(rows)
C.to_csv(TAB / "climate_serrana_correlations.csv", index=False)
L(C[C.predictor == "precip_mm"].round(3).to_string(index=False))
L("Serrana share of the screened events by year (%):", (100 * RESP["Serrana events"] / RESP["State events"]).round(1).to_dict())

# ------------------------------------------------------------------ 3. Figure 1 legend groups, 2019 and 2023
L("\n3. State shares of the legend groups of Figure 1 (% of the classified area)")
GROUPS = {"forest": [3, 5, 49], "grassland": [12], "other_nonforest": [11, 29, 32, 50], "silviculture": [9], "pasture": [15],
          "temporary_crops": [39, 40, 41], "mosaic": [21], "urban": [24], "other_nonvegetated": [23, 25, 30, 75], "water": [33, 31]}
out = []
for year, key in ((2019, "landcover2019_classes"), (2023, "landcover2023_classes")):
    a = pd.read_csv(path(key)).set_index("class_id")
    for g, ids in GROUPS.items():
        out.append(dict(year=year, group=g, pct_classified=a.loc[a.index.intersection(ids), "pct_classified"].sum()))
F = pd.DataFrame(out).pivot(index="group", columns="year", values="pct_classified")
F["difference_pp"] = F[2023] - F[2019]
F.round(3).to_csv(TAB / "landcover_figure1_2019_2023.csv")
L(F.round(2).to_string())
L.save()

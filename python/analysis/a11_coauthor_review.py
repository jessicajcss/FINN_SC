#!/usr/bin/env python3
"""a11 - analyses requested by the co-authors on manuscript v.6 (review of 2026-10-19).

Each block answers one or more comments of the co-authors (C<number> = comment number in the manuscript v.6 file)
and writes one table to results/tables/ and its lines to results/logs/a11_coauthor_review.txt.

  1  seasonality_by_mesoregion.csv     monthly share of screened events, state and mesoregions, 2012-2025 (C12, C35)
  2  max_area_2020.csv                 municipalities with the largest FINN area in 2020, the year of the maximum (C17)
  3  mesoregion_area_metrics_2025.csv  events per 100 km2, CO2 and PM2.5 per km2, burned fraction by mesoregion (C25, C34, C46)
  4  mesoregion_density_tests.csv      Kruskal-Wallis and Dunn tests (Holm) of the municipal event density among
                                       mesoregions, 2025 and 2012-2025 mean, and a spatial error model with mesoregion
                                       indicators as a check for spatial dependence (C26)
  5  climate_correlations_sensitivity.csv  Spearman correlations of a06 without the El Niño years 2015 and 2023,
                                       without each of them, and leave-one-year-out range (C27)
  6  viirs_increment.csv               VIIRS increment by year vs MODIS-only activity and precipitation (C39)
  7  interannual_dispersion.csv        annual event counts vs Poisson variation; CO2 per event by year (C19, C14)
  8  inventory_comparison_2020.csv     LCQAR (2022), FINN v1.5, FINN v2.5 MODIS, FINN v2.5 MODIS+VIIRS (2020) and
                                       FINN v2.5.1 MODIS+VIIRS (2025): counts, area, CO2, CO2 per km2, forest class (C40)
     inventory_decomposition_2020.csv  counterfactual totals: area by vegetation type of one version x CO2 per km2 by
                                       vegetation type of the other (C41)
  9  mesoregion_density_2020_2025.csv  density by mesoregion of the FINN v1.5 records of 2020 (= focos of the 2020
                                       inventory), of the FINN v2.5 events of 2020 and of the 2025 events (C38)
 10  recurrent_sites_silviculture.csv  Spearman correlation of the municipal event density with the land-cover fractions
                                       after excluding events at sites detected on >= k distinct days in the year (C28)
 11  sul_agriculture_split.csv         Sul Catarinense: municipalities with agriculture >= 40% vs the others (season,
                                       FINN cropland share) (C36)
     oeste_within_landcover.csv        within-mesoregion Spearman correlations (Oeste, Sul, Serrana) (C36)
 12  landcover_2019_vs_2023.csv        state shares of the class groups of section 2.8 in 2019 (Figure 1) and 2023 (C4)
 13  results/figures/FigS3_kde_annual.png  annual kernel density maps 2012-2025 (grid from
                                       R/analysis/kde_sensitivity_annual.R; drawn only if that grid exists) (C23, C24)

Inputs: archived records and external tables (config.analysis.inputs); results of a01, a06, a07 and of
R/analysis/kde_events.R and R/analysis/kde_sensitivity_annual.R.
"""
import math
import warnings
warnings.filterwarnings("ignore")
from _setup import CFG, ROOT, TAB, FIG, Log, path, load_records, screened_events, municipalities, read_shapefile
import numpy as np
import pandas as pd
from scipy import stats
from finn_sc.events import doy_to_month, flag_persistent, EVENT_KEY
from finn_sc.stats import holm

L = Log("a11_coauthor_review")
INP = CFG["analysis"]["inputs"]
y0, y1 = CFG["analysis"]["series_years"]
NY = y1 - y0 + 1
SEED = CFG["analysis"]["seed"]
mu = municipalities()
MESO = dict(zip(mu.NM_MUN, mu.mesorregiao))
AREA_MESO = mu.groupby("mesorregiao").AREA_KM2.sum()
MESOS = sorted(AREA_MESO.index)
E_all = screened_events()
E = E_all[(E_all.sensor == "MODIS+VIIRS") & (~E_all.flag)].copy()
E["month"] = doy_to_month(E.year, E.DAY)
E["meso"] = E.mun_event.map(MESO)
rec = load_records("MV")
rec["meso"] = rec.NM_MUN.map(MESO)

# 1 ------------------------------------------------------------------------------------------------ seasonality
rows = []
for name, g in [("Santa Catarina", E)] + [(m, E[E.meso == m]) for m in MESOS]:
    sh = g.month.value_counts(normalize=True).reindex(range(1, 13), fill_value=0) * 100
    rows.append(dict(region=name, events=len(g), **{f"m{k:02d}": sh[k] for k in range(1, 13)},
                     jul_sep=sh.loc[7:9].sum(), jul_nov=sh.loc[7:11].sum(), mar_jun=sh.loc[3:6].sum(),
                     peak_month=int(sh.idxmax())))
S1 = pd.DataFrame(rows)
S1.to_csv(TAB / "seasonality_by_mesoregion.csv", index=False)
L("1 seasonality (share of screened events, %, 2012-2025):")
L(S1[["region", "events", "jul_sep", "jul_nov", "mar_jun", "peak_month"]].round(1).to_string(index=False))
e25 = E[E.year == 2025]
L(f"  2025: Jul-Sep {100 * e25.month.isin([7, 8, 9]).mean():.1f}%, Jul-Nov {100 * e25.month.isin(range(7, 12)).mean():.1f}%")

# 2 ---------------------------------------------------------------------------------------- largest area in 2020
# municipal totals as in the manuscript: each event (screened or not; totals keep every event) assigned to the
# municipality with the largest share of its area
ev20 = E_all[(E_all.year == 2020) & (E_all.sensor == "MODIS+VIIRS")]
a20 = ev20.groupby("mun_event").area_m2.sum().sort_values(ascending=False) / 1e6
M2 = pd.DataFrame({"municipality": a20.index, "finn_area_km2": a20.values, "share_pct": 100 * a20.values / a20.sum()})
M2.head(10).to_csv(TAB / "max_area_2020.csv", index=False)
L(f"2 FINN area 2020 = {a20.sum():.1f} km2; largest: " +
  "; ".join(f"{r.municipality} {r.finn_area_km2:.1f} km2 ({r.share_pct:.1f}%)" for r in M2.head(5).itertuples()))

# 3 ------------------------------------------------------------------------------------ per-area metrics, 2025
M = pd.read_csv(TAB / "mesoregion_2025.csv").set_index("mesorregiao")
M["area_meso_km2"] = AREA_MESO
M["area_share_pct"] = 100 * M.area_meso_km2 / M.area_meso_km2.sum()
M["events_share_pct"] = 100 * M.events / M.events.sum()
M["co2_share_pct"] = 100 * M.CO2 / M.CO2.sum()
M["events_per_100km2"] = M.events / M.area_meso_km2 * 100
M["co2_t_per_km2"] = M.CO2 / M.area_meso_km2
M["pm25_kg_per_km2"] = M.PM25 / M.area_meso_km2 * 1000
M["finn_area_pct_of_meso"] = M.area_km2 / M.area_meso_km2 * 100
M["co2_t_per_event"] = M.CO2 / M.events
mean_ev = E.groupby(["year", "meso"]).size().unstack().mean()
M["events_per_100km2_mean_2012_2025"] = mean_ev / AREA_MESO * 100
M.reset_index().to_csv(TAB / "mesoregion_area_metrics_2025.csv", index=False)
tot = M.sum(numeric_only=True)
L("3 per-area metrics 2025:")
L(M[["area_share_pct", "events_share_pct", "co2_share_pct", "events_per_100km2", "co2_t_per_km2", "pm25_kg_per_km2",
     "finn_area_pct_of_meso", "co2_t_per_event", "events_per_100km2_mean_2012_2025"]].round(2).to_string())
L(f"  state: {tot.events / tot.area_meso_km2 * 100:.2f} events/100 km2; {tot.CO2 / tot.area_meso_km2:.1f} t CO2/km2; "
  f"{tot.PM25 / tot.area_meso_km2 * 1000:.1f} kg PM2.5/km2")

# 4 ------------------------------------------------------------------- differences among mesoregions (municipal density)
cnt = E.groupby(["year", "mun_event"]).size().unstack(fill_value=0).T.reindex(mu.NM_MUN, fill_value=0)
dens = cnt.div(mu.set_index("NM_MUN").AREA_KM2, axis=0) * 100
mg = mu.set_index("NM_MUN").mesorregiao


def dunn_holm(d):
    r = stats.rankdata(d.values); N = len(r)
    _, tc = np.unique(d.values, return_counts=True)
    T = 1 - np.sum(tc ** 3 - tc) / (N ** 3 - N)
    out = []
    for i in range(len(MESOS)):
        for j in range(i + 1, len(MESOS)):
            a = (mg == MESOS[i]).values; b = (mg == MESOS[j]).values
            z = (r[a].mean() - r[b].mean()) / math.sqrt(T * N * (N + 1) / 12 * (1 / a.sum() + 1 / b.sum()))
            out.append([MESOS[i], MESOS[j], z, 2 * stats.norm.sf(abs(z))])
    ph = holm([o[3] for o in out])
    return [o + [p] for o, p in zip(out, ph)]


T4 = []
for lab, d in (("2025", dens[2025]), ("mean_2012_2025", dens.mean(axis=1))):
    groups = [d[mg == m] for m in MESOS]
    H, p = stats.kruskal(*groups)
    eps2 = (H - len(MESOS) + 1) / (len(d) - len(MESOS))
    med = {m: d[mg == m].median() for m in MESOS}
    L(f"4 {lab}: Kruskal-Wallis H = {H:.1f}, p = {p:.2g}, epsilon2 = {eps2:.3f}, n = {len(d)}; medians " +
      "; ".join(f"{m} {v:.2f}" for m, v in med.items()))
    T4.append(dict(response=lab, test="kruskal", group1="", group2="", stat=H, p=p, p_holm=np.nan, effect=eps2))
    for m in MESOS:
        T4.append(dict(response=lab, test="median", group1=m, group2="", stat=med[m], p=np.nan, p_holm=np.nan,
                       effect=int((mg == m).sum())))
    for g1, g2, z, pz, ph in dunn_holm(d):
        T4.append(dict(response=lab, test="dunn", group1=g1, group2=g2, stat=z, p=pz, p_holm=ph, effect=np.nan))
        if "Serrana" in (g1, g2):
            L(f"   Dunn {g1} vs {g2}: z = {z:+.2f}, p (Holm) = {ph:.3g}")
# spatial error model of log density on mesoregion indicators (reference: Serrana), as a check for spatial dependence
import libpysal
import spreg
import esda
g = read_shapefile().to_crs(31982)[["CD_MUN", "geometry"]]
g["CD_MUN"] = g.CD_MUN.astype(int)
Dm = mu.copy(); Dm["d25"] = Dm.NM_MUN.map(dens[2025]); Dm["dmean"] = Dm.NM_MUN.map(dens.mean(axis=1))
others = [m for m in MESOS if m != "Serrana"]
for lab, col in (("2025", "d25"), ("mean_2012_2025", "dmean")):
    G = g.merge(Dm, on="CD_MUN", how="inner")
    G = G[G[col] > 0].reset_index(drop=True)
    X = np.column_stack([(G.mesorregiao == m).astype(float) for m in others])
    y = np.log(G[col].values).reshape(-1, 1)
    W = libpysal.weights.KNN.from_dataframe(G.set_geometry(G.centroid), k=6); W.transform = "r"
    ols = spreg.OLS(y, X, w=W, name_x=others, moran=True, spat_diag=True)
    sem = spreg.ML_Error(y, X, w=W, name_x=others)
    np.random.seed(SEED)
    mi = esda.Moran(sem.e_filtered.flatten(), W, permutations=999)
    L(f"  SEM {lab} (log density > 0, n = {len(G)}, knn6): Moran I OLS residuals = {ols.moran_res[0]:.3f} "
      f"(p = {ols.moran_res[2]:.2g}); lambda = {sem.lam:.3f}; Moran I SEM filtered = {mi.I:.3f} (p = {mi.p_sim:.3f})")
    for i, m in enumerate(others, start=1):
        b, p = float(sem.betas[i][0]), float(sem.z_stat[i][1])
        T4.append(dict(response=lab, test="sem_vs_Serrana", group1=m, group2="Serrana", stat=math.exp(b), p=p,
                       p_holm=np.nan, effect=b))
        L(f"   {m}: density ratio to Serrana = {math.exp(b):.2f} (p = {p:.3g})")
pd.DataFrame(T4).to_csv(TAB / "mesoregion_density_tests.csv", index=False)

# 5 --------------------------------------------------------------------------- climate without the El Niño years
Y = pd.DataFrame({"eventos": E.groupby("year").size(), "area_FINN": rec.groupby("year").AREA.sum() / 1e6,
                  "CO2": rec.groupby("year").CO2.sum(),
                  "area_MapBiomas": pd.read_csv(path("mapbiomas_fire")).groupby("year").burned_km2.sum()}).loc[y0:y1]
XC = pd.read_csv(path("climate")).set_index("year")[["precip_mm_fs", "VPD_kPa_fs", "soil_moist_fs", "Tc_fs", "ONI_fs"]].loc[y0:y1]
rows = []
for excl in ((), (2015, 2023), (2015,), (2023,)):
    part = []
    for yv in Y.columns:
        for xv in XC.columns:
            dd = pd.concat([Y[yv], XC[xv]], axis=1).dropna().drop(list(excl), errors="ignore")
            r, p = stats.spearmanr(dd.iloc[:, 0], dd.iloc[:, 1])
            loo = [stats.spearmanr(dd.drop(k).iloc[:, 0], dd.drop(k).iloc[:, 1])[0] for k in dd.index]
            part.append(dict(excluded=" ".join(map(str, excl)) or "none", resposta=yv, preditor=xv, n=len(dd), rho=r, p=p,
                             rho_loo_min=min(loo), rho_loo_max=max(loo)))
    P = pd.DataFrame(part); P["p_holm"] = P.groupby("resposta").p.transform(lambda s: holm(s.values))
    rows.append(P)
C5 = pd.concat(rows, ignore_index=True)
C5.to_csv(TAB / "climate_correlations_sensitivity.csv", index=False)
L("5 climate correlations, all years vs without 2015 and 2023 (precipitation, soil moisture, ONI):")
for ex in ("none", "2015 2023"):
    s = C5[(C5.excluded == ex) & C5.preditor.isin(["precip_mm_fs", "soil_moist_fs", "ONI_fs"])]
    L(f"  excluded {ex}:\n" + s[["resposta", "preditor", "n", "rho", "p", "p_holm", "rho_loo_min", "rho_loo_max"]].round(3).to_string(index=False))

# 6 ------------------------------------------------------------------------------------------- VIIRS increment
V = pd.read_csv(TAB / "viirs_effect.csv").set_index("year")
st = pd.read_csv(TAB / "state_counts.csv")
mod = st[st.sensor == "MODIS"].set_index("year")
V["modis_events"] = mod.events_screened.reindex(V.index)
V["precip_mm_fs"] = pd.read_csv(path("climate")).set_index("year").precip_mm_fs.reindex(V.index)
V.reset_index().to_csv(TAB / "viirs_increment.csv", index=False)
r1, p1 = stats.spearmanr(V.CO2_inc_pct, V.modis_events)
r2, p2 = stats.spearmanr(V.CO2_inc_pct, V.precip_mm_fs)
lo, hi = V.modis_events.nsmallest(3).index, V.modis_events.nlargest(3).index
L(f"6 VIIRS CO2 increment {V.CO2_inc_pct.min():.1f}-{V.CO2_inc_pct.max():.1f}% (n = {len(V)}); Spearman with MODIS-only "
  f"events rho = {r1:.2f} (p = {p1:.3f}); with precipitation rho = {r2:.2f} (p = {p2:.2f}); "
  f"3 years with fewest MODIS events {list(lo)}: {V.loc[lo, 'CO2_inc_pct'].min():.1f}-{V.loc[lo, 'CO2_inc_pct'].max():.1f}%; "
  f"3 with most {list(hi)}: {V.loc[hi, 'CO2_inc_pct'].min():.1f}-{V.loc[hi, 'CO2_inc_pct'].max():.1f}%")

# 7 ----------------------------------------------------------------------------------- interannual dispersion
ev = E.groupby("year").size()
chi = float(((ev - ev.mean()) ** 2 / ev.mean()).sum()); dfree = len(ev) - 1
groups = [E[E.year == y].CO2.values for y in sorted(E.year.unique())]
H, pk = stats.kruskal(*groups)
eps2 = (H - len(groups) + 1) / (len(E) - len(groups))
med = E.groupby("year").CO2.median()
I7 = pd.DataFrame({"year": ev.index, "events": ev.values, "co2_median_t_per_event": med.values,
                   "co2_mean_t_per_event": E.groupby("year").CO2.mean().values})
I7.to_csv(TAB / "interannual_dispersion.csv", index=False)
L(f"7 annual events: mean {ev.mean():.0f}, variance {ev.var():.0f} (Poisson variance = mean); dispersion chi2 = {chi:.0f}, "
  f"df = {dfree}, p = {stats.chi2.sf(chi, dfree):.2g}; CO2 per event across years: Kruskal-Wallis H = {H:.1f}, "
  f"p = {pk:.2g}, epsilon2 = {eps2:.4f}; median CO2 per event {med.loc[:2021].min():.0f}-{med.loc[:2021].max():.0f} t "
  f"(v2.5, 2012-2021) and {med.loc[2022:].min():.0f}-{med.loc[2022:].max():.0f} t (v2.5.1, 2022-2025)")

# 8 ----------------------------------------------------------------- 2020 inventories and counterfactual totals
v15 = pd.read_csv(ROOT / INP["finn15_2020_records"])
leg = pd.read_csv(ROOT / INP["legacy_2020"]).set_index("source")
allrec = load_records()
r20m = allrec[(allrec.year == 2020) & (allrec.sensor == "MODIS")]
r20v = allrec[(allrec.year == 2020) & (allrec.sensor == "MODIS+VIIRS")]
r25v = allrec[(allrec.year == 2025) & (allrec.sensor == "MODIS+VIIRS")]
evp = E_all.set_index(["year", "sensor"])


def summ(d, label, count_label, count, version, sensor, forest_codes):
    A = d.AREA.sum() / 1e6; C = d.CO2.sum()
    fa = d[d.GENVEG.isin(forest_codes)]
    return dict(inventory=label, version=version, sensor=sensor, count_label=count_label, count=count, area_km2=A,
                CO2_Mt=C / 1e6, CO2_t_per_km2=C / A, forest_area_pct=100 * fa.AREA.sum() / d.AREA.sum(),
                forest_CO2_pct=100 * fa.CO2.sum() / C, forest_CO2_t_per_km2=fa.CO2.sum() / (fa.AREA.sum() / 1e6))


n20m = int(((E_all.year == 2020) & (E_all.sensor == "MODIS") & ~E_all.flag).sum())
n20v = int(((E_all.year == 2020) & (E_all.sensor == "MODIS+VIIRS") & ~E_all.flag).sum())
n25v = int(((E_all.year == 2025) & (E_all.sensor == "MODIS+VIIRS") & ~E_all.flag).sum())
lc = leg.loc["lcqar_2022_report"]
T8 = [dict(inventory="LCQAR (2022), 2020", version="FINN (v1.5, inferred)", sensor="MODIS", count_label="focos de calor",
           count=int(lc["count"]), area_km2=np.nan, CO2_Mt=lc.CO2_t / 1e6, CO2_t_per_km2=np.nan, forest_area_pct=np.nan,
           forest_CO2_pct=np.nan, forest_CO2_t_per_km2=np.nan),
      summ(v15, "FINN v1.5, 2020", "registros", len(v15), "v1.5", "MODIS", [3, 4]),
      summ(r20m, "FINN v2.5 MODIS, 2020", "eventos", n20m, "v2.5", "MODIS", [3, 4, 6]),
      summ(r20v, "FINN v2.5 MODIS+VIIRS, 2020", "eventos", n20v, "v2.5", "MODIS+VIIRS", [3, 4, 6]),
      summ(r25v, "FINN v2.5.1 MODIS+VIIRS, 2025", "eventos", n25v, "v2.5.1", "MODIS+VIIRS", [3, 4, 6])]
T8 = pd.DataFrame(T8)
T8["detections"] = [np.nan, v15.drop_duplicates(["DAY", "LONGI", "LATI"]).shape[0],
                    r20m.drop_duplicates(["DAY", "FIREID"]).shape[0], r20v.drop_duplicates(["DAY", "FIREID"]).shape[0],
                    r25v.drop_duplicates(["DAY", "FIREID"]).shape[0]]
T8["records"] = [np.nan, len(v15), len(r20m), len(r20v), len(r25v)]
T8.to_csv(TAB / "inventory_comparison_2020.csv", index=False)
L("8 inventories (2020 and 2025):")
L(T8.round(2).to_string(index=False))


def by_type(d, forest_codes):
    k = d.GENVEG.where(~d.GENVEG.isin(forest_codes), 0).map(lambda v: "forest" if v == 0 else f"genveg_{int(v)}")
    t = d.groupby(k).agg(A=("AREA", "sum"), C=("CO2", "sum"))
    t["A"] /= 1e6
    return t


h15, h25 = by_type(v15, [3, 4]), by_type(r20v, [3, 4, 6])
idx = sorted(set(h15.index) | set(h25.index))
h15, h25 = h15.reindex(idx, fill_value=0), h25.reindex(idx, fill_value=0)
I15, I25 = h15.C / h15.A, h25.C / h25.A
C15, C25 = h15.C.sum() / 1e6, h25.C.sum() / 1e6
cf_a = float((h25.A * I15).sum()) / 1e6          # v2.5 area by type x v1.5 CO2 per km2 by type
cf_b = float((h15.A * I25).sum()) / 1e6          # v1.5 area by type x v2.5 CO2 per km2 by type
cf_f = (h25.C.sum() - h25.C["forest"] + h25.A["forest"] * I15["forest"]) / 1e6   # v2.5 with the v1.5 forest CO2 per km2 only
gap = C15 - C25
eff_int = 0.5 * ((C15 - cf_b) + (cf_a - C25))
eff_cmp = 0.5 * ((cf_b - C25) + (C15 - cf_a))
D8 = pd.DataFrame({"type": idx, "area_v15_km2": h15.A.values, "area_v25_km2": h25.A.values,
                   "co2_t_per_km2_v15": I15.values, "co2_t_per_km2_v25": I25.values})
D8.to_csv(TAB / "inventory_decomposition_2020.csv", index=False)
L(D8.round(1).to_string(index=False))
L(f"  totals (Mt CO2): v1.5 {C15:.2f}; v2.5 {C25:.2f}; v2.5 area x v1.5 CO2/km2 {cf_a:.2f}; v1.5 area x v2.5 CO2/km2 {cf_b:.2f}; "
  f"v2.5 with the v1.5 forest CO2/km2 only {cf_f:.2f}")
L(f"  symmetric decomposition of the gap ({gap:.2f} Mt): CO2 per km2 by type {eff_int:.2f} Mt ({100 * eff_int / gap:.0f}%), "
  f"area composition by type {eff_cmp:.2f} Mt ({100 * eff_cmp / gap:.0f}%); total area v1.5 {h15.A.sum():.1f} km2, v2.5 {h25.A.sum():.1f} km2")

# 9 ---------------------------------------------------------------------- 2020 (v1.5 records) vs 2025 by mesoregion
v15["meso"] = v15.NM_MUN.map(MESO)
T9 = pd.DataFrame({"v15_records_2020": v15.groupby("meso").size(),
                   "v25_modis_events_2020": E_all[(E_all.year == 2020) & (E_all.sensor == "MODIS") & ~E_all.flag].mun_event.map(MESO).value_counts(),
                   "v25_mv_events_2020": E[E.year == 2020].meso.value_counts(),
                   "v251_mv_events_2025": E[E.year == 2025].meso.value_counts()}).reindex(MESOS)
D9 = T9.div(AREA_MESO, axis=0) * 100
out9 = pd.concat([T9.add_suffix("_n"), D9.add_suffix("_per_100km2"), (100 * T9 / T9.sum()).add_suffix("_share_pct")], axis=1)
out9.reset_index(names="mesorregiao").to_csv(TAB / "mesoregion_density_2020_2025.csv", index=False)
L("9 density by mesoregion (per 100 km2):")
L(D9.round(2).to_string())
for c in D9.columns[1:]:
    L(f"  Spearman (n = 6 mesoregions) v1.5 records 2020 vs {c}: rho = {stats.spearmanr(D9.v15_records_2020, D9[c])[0]:.2f}")

# 10 ----------------------------------------------------------------- recurrent sites and the silviculture association
det, _ = flag_persistent(load_records("MV"), CFG["analysis"]["screening"]["radius_km"], CFG["analysis"]["screening"]["min_days"],
                         sensors=("MODIS+VIIRS",))
evmax = det.groupby(EVENT_KEY).ndays.max().rename("ndays_max").reset_index()
Ek = E.merge(evmax, on=EVENT_KEY, how="left")
LU = pd.read_csv(ROOT / INP["landuse_all295"]).rename(columns={"code_muni": "CD_MUN"})
Dl = mu.merge(LU.drop(columns=[c for c in ("municipality",) if c in LU.columns]), on="CD_MUN")
FR = ["forest", "grassland", "pasture", "agriculture", "silviculture"]
rows = []
for k in (None, 12, 8, 6, 4):
    sub = Ek if k is None else Ek[Ek.ndays_max < k]
    dd = Dl.NM_MUN.map(sub.groupby("mun_event").size()).fillna(0) / Dl.AREA_KM2 * 100 / NY
    row = dict(excluded_sites_min_days=k or 0, events_removed_pct=100 * (1 - len(sub) / len(Ek)))
    for f in FR:
        r, p = stats.spearmanr(dd, Dl[f]); row[f"rho_{f}"] = r; row[f"p_{f}"] = p
    rows.append(row)
T10 = pd.DataFrame(rows)
T10.to_csv(TAB / "recurrent_sites_silviculture.csv", index=False)
L("10 Spearman rho of mean event density (2012-2025) with land-cover fractions, excluding events at sites with >= k days:")
L(T10[["excluded_sites_min_days", "events_removed_pct", "rho_silviculture", "rho_forest", "rho_grassland"]].round(3).to_string(index=False))
d8 = det[(det.ndays >= 8) & (det.ndays < 16)].NM_MUN.value_counts().head(8)
fl = det[det.flag].NM_MUN.value_counts()
L("  detections at sites with 8-15 days, top municipalities: " + "; ".join(f"{m} {n}" for m, n in d8.items()))
L("  flagged detections (>= 16 days) by municipality, 2012-2025: " + "; ".join(f"{m} {n}" for m, n in fl.items()))
L("  silviculture fraction (2023) of municipalities with flagged detections: " +
  "; ".join(f"{m} {Dl.set_index('NM_MUN').silviculture.get(m, float('nan')):.2f}" for m in fl.index) +
  f" | municipal median {Dl.silviculture.median():.3f}")

# 11 ------------------------------------------------------------------------------------- Sul and Oeste
LM = pd.read_csv(TAB / "landcover_municipal.csv")
sul = LM[LM.mesorregiao == "Sul Catarinense"]
rows = []
for lab, names in (("agriculture >= 40%", set(sul[sul.agriculture >= 0.4].NM_MUN)), ("agriculture < 40%", set(sul[sul.agriculture < 0.4].NM_MUN))):
    e = E[E.mun_event.isin(names)]; sh = e.month.value_counts(normalize=True).reindex(range(1, 13), fill_value=0) * 100
    gv = rec[rec.NM_MUN.isin(names)].groupby("GENVEG").AREA.sum()
    area = sul[sul.NM_MUN.isin(names)].AREA_KM2.sum()
    rows.append(dict(group=lab, municipalities=len(names), events=len(e), events_per_100km2_yr=len(e) / area * 100 / NY,
                     mar_jun_pct=sh.loc[3:6].sum(), jul_sep_pct=sh.loc[7:9].sum(),
                     finn_cropland_area_pct=100 * gv.get(9, 0) / gv.sum(), agriculture_mean=sul[sul.NM_MUN.isin(names)].agriculture.mean()))
T11 = pd.DataFrame(rows)
T11.to_csv(TAB / "sul_agriculture_split.csv", index=False)
L("11 Sul Catarinense split by municipal agriculture fraction (2023):")
L(T11.round(2).to_string(index=False))
gv_meso = rec.groupby(["meso", "GENVEG"]).AREA.sum().unstack(fill_value=0)
L("  FINN cropland (GENVEG 9) share of the area by mesoregion (%): " +
  "; ".join(f"{m} {100 * gv_meso.loc[m].get(9, 0) / gv_meso.loc[m].sum():.1f}" for m in MESOS))
rows = []
for m in ("Oeste Catarinense", "Sul Catarinense", "Serrana"):
    s = LM[LM.mesorregiao == m]
    for f in FR:
        r, p = stats.spearmanr(s.ev_1225_100km2_yr, s[f]); rows.append(dict(mesorregiao=m, n=len(s), cobertura=f, rho=r, p=p))
T11b = pd.DataFrame(rows)
T11b.to_csv(TAB / "oeste_within_landcover.csv", index=False)
L("  within-mesoregion Spearman (mean density 2012-2025 vs fraction):")
L(T11b.round(3).to_string(index=False))

# 12 ------------------------------------------------------------------------------------ land cover 2019 vs 2023
c19 = pd.read_csv(ROOT / INP["landcover2019_classes"])
grp = {"forest": [3, 4, 5, 6, 49], "grassland": [12], "pasture": [15], "agriculture": [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62],
       "silviculture": [9]}
classified = c19[c19.class_id != 0].area_km2.sum()
s19 = {k: 100 * c19[c19.class_id.isin(v)].area_km2.sum() / classified for k, v in grp.items()}
s23 = {k: 100 * (Dl[k] * Dl.AREA_KM2).sum() / Dl.AREA_KM2.sum() for k in grp}
T12 = pd.DataFrame({"group": list(grp), "pct_2019_classified_area": [s19[k] for k in grp], "pct_2023_municipal_area": [s23[k] for k in grp]})
T12["difference_pp"] = T12.pct_2023_municipal_area - T12.pct_2019_classified_area
T12.to_csv(TAB / "landcover_2019_vs_2023.csv", index=False)
L("12 land cover, state shares (%): 2019 (MapBiomas C10, classified area; Figure 1) vs 2023 (municipal fractions, section 2.8):")
L(T12.round(2).to_string(index=False))

# 13 ------------------------------------------------------------------------------- Figure S3 (annual KDE maps)
gp = TAB / "kde_annual_grid.csv.gz"
if gp.is_file():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FuncFormatter
    from pyproj import Transformer
    import shapely
    from finn_sc.cartography import rose_above_bar
    from finn_sc import figcheck
    num = lambda v, d=0: (f"{v:,.{d}f}").replace(",", "X").replace(".", ",").replace("X", ".").replace("-", "−")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    G = pd.read_csv(gp)
    BS = pd.read_csv(TAB / "kde_annual_summary.csv")
    xs = np.sort(G.x.unique()); ys = np.sort(G.y.unique())
    dx = np.median(np.diff(xs)); dy = np.median(np.diff(ys))
    xf = np.arange(xs.min() - dx, xs.max() + 2 * dx, dx); yf = np.arange(ys.min() - dy, ys.max() + 2 * dy, dy)
    ix = np.rint((G.x.values - xf[0]) / dx).astype(int); iy = np.rint((G.y.values - yf[0]) / dy).astype(int)
    XX, YY = np.meshgrid(xf, yf)
    LON, LAT = Transformer.from_crs(31982, 4674, always_xy=True).transform(XX, YY)
    shp = read_shapefile().to_crs(4674)
    shp["meso"] = shp.NM_MUN.map(MESO)
    state = shp.dissolve(); mesog = shp.dissolve(by="meso").reset_index()
    SCg = state.geometry.iloc[0]
    LAT0 = -27.6
    levels = [0, 1, 2, 4, 8, 16, 32, 64]
    years = list(range(y0, y1 + 1))
    fig, axs = plt.subplots(4, 4, figsize=(9.6, 7.6), dpi=200)
    axs = axs.ravel()
    cs = None
    items, problems = {}, []
    for k, yv in enumerate(years):
        ax = axs[k]
        Z = np.full((len(yf), len(xf)), np.nan); Z[iy, ix] = G[f"y{yv}"].values
        cs = ax.contourf(LON, LAT, Z, levels=levels, cmap="magma_r", extend="max")
        mesog.boundary.plot(ax=ax, color="0.35", lw=0.3)
        state.boundary.plot(ax=ax, color="0.2", lw=0.45)
        ax.set_xlim(-54, -48); ax.set_ylim(-29.5, -25.8); ax.set_aspect(1 / math.cos(math.radians(LAT0)))
        ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(''); ax.set_ylabel('')
        for sp in ax.spines.values(): sp.set_color("0.6"); sp.set_linewidth(0.5)
        b = BS[(BS.year == yv) & (BS.meso == "Serrana")].iloc[0]
        ax.set_title(f"{yv} (n = {num(int(b.events))})", loc="left", fontsize=7.2, pad=2)
        L(f"13 Figure S3 {yv}: events {int(b.events)}, max {b.max_density:.1f} ({b.max_mun}), Serrana top 1% share {100 * b.share_top1:.1f}%")
    for ax in axs[len(years):]:
        ax.set_axis_off()
    # colour bar, scale bar and north rose in the empty panels
    cax = fig.add_axes([0.56, 0.135, 0.18, 0.018])
    cb = fig.colorbar(cs, cax=cax, orientation="horizontal", format=FuncFormatter(lambda v, _: num(v)))
    cb.set_label("Eventos de queimada por 100 km²", fontsize=6.8); cb.ax.tick_params(labelsize=6)
    axr = axs[15]; axr.set_xlim(-54, -48); axr.set_ylim(-29.5, -25.8); axr.set_aspect(1 / math.cos(math.radians(LAT0)))
    lat_sb = -28.9; dlon = 100 / (111.32 * math.cos(math.radians(lat_sb))); x1 = -48.6; x0 = x1 - dlon
    from matplotlib.patches import Rectangle
    axr.add_patch(Rectangle((x0, lat_sb), dlon / 2, 0.06, facecolor="k", edgecolor="k", lw=0.4))
    axr.add_patch(Rectangle((x0 + dlon / 2, lat_sb), dlon / 2, 0.06, facecolor="w", edgecolor="k", lw=0.4))
    for j, lab in ((0, "0"), (2, "100 km")):      # middle label left out: too close at this size
        axr.annotate(lab, (x0 + j * dlon / 2, lat_sb + 0.06), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=5.5)
    rose_above_bar(axr, x1, lat_sb + 0.06, 5.5, size=12, align='right')   # right-justified (2026-11-04)
    fig.text(0.02, 0.012, f"FINN MODIS+VIIRS (v2.5 até 2021; v2.5.1 de 2022 a 2025); anomalias térmicas persistentes excluídas; núcleo "
             f"gaussiano com σ fixo de {num(BS.sigma_fixed_m.iloc[0] / 1000, 1)} km em todos os anos; correção de borda de Jones-Diggle;\n"
             "densidade calculada em SIRGAS 2000 / UTM 22S; linhas: limites estadual e das mesorregiões (IBGE).", fontsize=6, va="bottom")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.07, wspace=0.04, hspace=0.16)
    # layout check: titles inside the figure and clear of each other; colour bar and furniture inside their panels
    r = figcheck.renderer(fig)
    lab = {f"title {k}": (figcheck.bbox(axs[k]._left_title, r, pad=1.0), [], "figure") for k in range(len(years))}
    bb = cb.ax.get_tightbbox(r)
    lab["colour bar"] = (shapely.geometry.box(bb.x0 - 1, bb.y0 - 1, bb.x1 + 1, bb.y1 + 1), [], "figure")
    frames = {"figure": shapely.geometry.box(0, 0, fig.bbox.width, fig.bbox.height)}
    prob = figcheck.check(lab, {}, frames)
    L("13 Figure S3 layout problems:", len(prob))
    for pr in prob:
        L("   ", pr)
    fig.savefig(FIG / "FigS3_kde_annual.png", facecolor="white")
    plt.close(fig)
else:
    L("13 Figure S3 not drawn: run R/analysis/kde_sensitivity_annual.R first")
L.save()

#!/usr/bin/env python3
"""a07 - municipal land cover (MapBiomas 2023 fractions) vs fire-event density and vs CO2 per event.

Land cover: data/external/mapbiomas_lulc2023_SC_municipal_fractions_all295.csv (config key landuse_all295): fractions of
2023 for all 295 municipalities, MapBiomas Collection 10.1, written by gee/mapbiomas_lulc_fractions_all295.ipynb (run on
2026-10-07; executed copy gee/mapbiomas_lulc_fractions_all295_run_2026-10-07.ipynb); merged on the IBGE code. Class groups:
forest 1,3,4,5,6,49; grassland 12; pasture 15; agriculture 18-21,36,39-41,46-48,62; silviculture 9 (mean of a binary mask
per municipality at 100 m). If that file is absent, the archived 277-municipality file (config key landuse; merged on the
name) is used, as in versions 2.0.0-2.2.0.
Responses: (i) mean annual density of screened events 2012-2025 (events per 100 km2 per year);
(ii) CO2 per screened event, 2012-2025 pooled (municipalities with >= 14 events).
Methods: Spearman correlations; OLS of log(y) with White SE; spatial error model (ML; spreg) with 6-nearest-neighbour
(UTM 22S centroids) and queen-contiguity weights; Moran's I of the OLS residuals (analytical) and of the SEM filtered
residuals (999 permutations, fixed seed); AIC of both models. Reference category = forest + other classes. Effect of
+10 percentage points = exp(0.1 b) - 1. Municipalities with zero density (log undefined: Governador Celso Ramos, no event
in 2012-2025) are excluded from the log-linear models and listed in the log. History of the specification: CHANGELOG.md.
Outputs: results/tables/landcover_municipal.csv, landcover_spearman.csv, landcover_sem.csv; results/logs/a07_landcover.txt
Manuscript (v3.2): sections 2.8 and 3, Table S8. Inventory report: section 4 (CO2 per event).
"""
import warnings
warnings.filterwarnings("ignore")
from _setup import CFG, ROOT, TAB, Log, path, screened_events, municipalities, read_shapefile, load_records
import numpy as np
import pandas as pd
from scipy import stats

L = Log("a07_landcover")
SEED = CFG["analysis"]["seed"]
y0, y1 = CFG["analysis"]["series_years"]
nyears = y1 - y0 + 1
mu = municipalities()
FR = ["forest", "grassland", "pasture", "agriculture", "silviculture"]
_all = CFG["analysis"]["inputs"].get("landuse_all295")
if _all and (ROOT / _all).is_file():
    lu = pd.read_csv(ROOT / _all).rename(columns={"code_muni": "CD_MUN"})
    lu["CD_MUN"] = lu.CD_MUN.astype(int)
    KEY = "CD_MUN"
    lu = lu.drop(columns=[c for c in ("municipality", "NM_MUN") if c in lu.columns])
    L(f"land-cover file (all municipalities, merged on the IBGE code): {_all}")
else:
    lu = pd.read_csv(path("landuse")).rename(columns={"municipality": "NM_MUN"})
    KEY = "NM_MUN"
    L(f"land-cover file (PROVISIONAL, merged on the name): {path('landuse')}")
L(f"land-cover file: {len(lu)} municipalities (of {len(mu)}); sum of the 5 classes median {lu[FR].sum(axis=1).median():.3f}")
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)]
mb = pd.read_csv(path("mapbiomas_fire"))
D = mu.merge(lu, on=KEY, how="inner")
ev_all = E.groupby("mun_event").size()
ev_y = E[E.year == CFG["analysis"]["report_year"]].groupby("mun_event").size()
D["ev_1225_100km2_yr"] = D.NM_MUN.map(ev_all).fillna(0) / D.AREA_KM2 * 100 / nyears
D["ev25_100km2"] = D.NM_MUN.map(ev_y).fillna(0) / D.AREA_KM2 * 100
D["mb_pct_yr"] = D.CD_MUN.map(mb.groupby("CD_MUN").burned_km2.sum()).fillna(0) / D.AREA_KM2 * 100 / mb.year.nunique()
pe = E.groupby("mun_event").agg(events=("POLYID", "size"), CO2=("CO2", "sum"), area=("area_m2", "sum"))
D["events_1225"] = D.NM_MUN.map(pe.events).fillna(0).astype(int)
D["CO2_per_event"] = D.NM_MUN.map(pe.CO2 / pe.events)
D["area_km2_per_event"] = D.NM_MUN.map(pe.area / pe.events / 1e6)
rec = load_records("MV")
f4 = rec.assign(A4=rec.AREA.where(rec.GENVEG == 4, 0.0)).groupby("NM_MUN")[["A4", "AREA"]].sum()
D["finn_forest4_share"] = D.NM_MUN.map(f4.A4 / f4.AREA)
D.to_csv(TAB / "landcover_municipal.csv", index=False)
L("municipalities in the analysis:", len(D))

rows = []
for yv in ["ev_1225_100km2_yr", "ev25_100km2", "mb_pct_yr"]:
    for xv in FR:
        r, p = stats.spearmanr(D[yv], D[xv])
        rows.append(dict(resposta=yv, cobertura=xv, n=len(D), rho=r, p=p))
Q = D[D.events_1225 >= 14]
for yv in ["CO2_per_event", "area_km2_per_event"]:
    for xv in FR + ["finn_forest4_share"]:
        r, p = stats.spearmanr(Q[yv], Q[xv])
        rows.append(dict(resposta=yv, cobertura=xv, n=len(Q), rho=r, p=p))
LS = pd.DataFrame(rows)
LS.to_csv(TAB / "landcover_spearman.csv", index=False)
L(LS.round(4).to_string(index=False))
r = stats.spearmanr(Q.silviculture, Q.finn_forest4_share)
L(f"silviculture fraction vs FINN temperate-forest share of the municipal FINN area: rho = {r[0]:.2f} (p = {r[1]:.2g}; n = {len(Q)})")

# spatial error models
import libpysal
import spreg
import esda
g = read_shapefile().to_crs(31982)[["CD_MUN", "geometry"]]
g["CD_MUN"] = g.CD_MUN.astype(int)
XN = ["grassland", "pasture", "agriculture", "silviculture"]
RES = []
for resp, sub in (("ev_1225_100km2_yr", D), ("CO2_per_event", Q)):
    G = g.merge(sub, on="CD_MUN", how="inner").reset_index(drop=True)
    zero = G[resp] <= 0
    if zero.any():
        L(f"{resp}: {int(zero.sum())} municipalities with zero value excluded from the log-linear models: "
          f"{', '.join(G.loc[zero, 'NM_MUN'])}")
        G = G[~zero].reset_index(drop=True)
    y = np.log(G[resp].values).reshape(-1, 1)
    X = G[XN].values
    for wname in ("knn6", "queen"):
        if wname == "knn6":
            W = libpysal.weights.KNN.from_dataframe(G.set_geometry(G.centroid), k=6)
        else:
            W = libpysal.weights.Queen.from_dataframe(G, use_index=False)
        W.transform = "r"
        ols = spreg.OLS(y, X, w=W, name_x=XN, robust="white", spat_diag=True, moran=True)
        sem = spreg.ML_Error(y, X, w=W, name_x=XN)
        np.random.seed(SEED)
        mi = esda.Moran(sem.e_filtered.flatten(), W, permutations=999)
        L(f"\n{resp} | W = {wname} | n = {len(G)}: OLS R2 = {ols.r2:.3f}; Moran I (OLS residuals) = {ols.moran_res[0]:.3f} "
          f"(p = {ols.moran_res[2]:.3g}); SEM lambda = {sem.lam:.3f}; Moran I (SEM filtered) = {mi.I:.3f} (p = {mi.p_sim:.3f}); "
          f"AIC OLS = {ols.aic:.1f}, SEM = {sem.aic:.1f}")
        for i, nm in enumerate(["const"] + XN):
            b, se, p = float(sem.betas[i][0]), float(sem.std_err[i]), float(sem.z_stat[i][1])
            eff = 100 * (np.exp(0.1 * b) - 1) if i else np.nan
            RES.append(dict(response=resp, W=wname, term=nm, n=len(G), b_sem=b, se_sem=se, p_sem=p, effect_10pp_pct=eff,
                            b_ols=float(ols.betas[i][0]), p_ols_white=float(ols.t_stat[i][1]), lam=float(sem.lam),
                            r2_ols=float(ols.r2), moran_ols=float(ols.moran_res[0]), p_moran_ols=float(ols.moran_res[2]),
                            moran_sem=float(mi.I), p_moran_sem=float(mi.p_sim),
                            aic_ols=float(ols.aic), aic_sem=float(sem.aic)))
            if i:
                L(f"   {nm:12s} b = {b:+.3f} (SE {se:.3f}) p = {p:.3g} | +10 p.p. -> {eff:+.1f}%")
pd.DataFrame(RES).to_csv(TAB / "landcover_sem.csv", index=False)
L.save()

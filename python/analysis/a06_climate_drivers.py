#!/usr/bin/env python3
"""a06 - interannual association between fire activity and fire-season climate (2012-2025).

Responses: screened events (a01), FINN burned area and CO2 (MODIS+VIIRS records) and MapBiomas mapped
area (2012-2024). Predictors (data/external/era5land_oni_SC_fire_season_2012_2025.csv; built with
gee/era5land_oni_fire_season.py): ERA5-Land state means for July-November (precipitation sum, mean 2 m
temperature, mean vapour-pressure deficit from Tetens, mean volumetric soil water 0-7 cm) and the mean
ONI of JAS, ASO and SON (NOAA CPC). Spearman rho in levels and first differences; Holm-adjusted p
within each response (5 predictors).
Outputs: results/tables/climate_correlations.csv; results/logs/a06_climate_drivers.txt
Manuscript (v3.2): sections 2.8, 3 and 4, Table S7, Figure S2. Inventory report: section 4.
"""
from _setup import CFG, TAB, Log, load_records, screened_events, path
import pandas as pd
from scipy import stats
from finn_sc.stats import holm

L = Log("a06_climate_drivers")
y0, y1 = CFG["analysis"]["series_years"]
rec = load_records("MV")
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)]
mb = pd.read_csv(path("mapbiomas_fire"))
Y = pd.DataFrame({"eventos": E.groupby("year").size(),
                  "area_FINN": rec.groupby("year").AREA.sum() / 1e6,
                  "CO2": rec.groupby("year").CO2.sum(),
                  "area_MapBiomas": mb.groupby("year").burned_km2.sum()}).loc[y0:y1]
X = pd.read_csv(path("climate")).set_index("year")[["precip_mm_fs", "VPD_kPa_fs", "soil_moist_fs", "Tc_fs", "ONI_fs"]].loc[y0:y1]
L("fire-season predictors:")
L(X.round(3).to_string())
rows = []
for yv in Y.columns:
    for xv in X.columns:
        dd = pd.concat([Y[yv], X[xv]], axis=1).dropna()
        r, p = stats.spearmanr(dd.iloc[:, 0], dd.iloc[:, 1])
        fd = dd.diff().dropna()
        r1, p1 = stats.spearmanr(fd.iloc[:, 0], fd.iloc[:, 1])
        rows.append(dict(resposta=yv, preditor=xv, n=len(dd), rho=r, p=p, rho_dif=r1, p_dif=p1))
C = pd.DataFrame(rows)
C["p_holm"] = C.groupby("resposta").p.transform(lambda s: holm(s.values))
C.to_csv(TAB / "climate_correlations.csv", index=False)
L(C.round(4).to_string(index=False))
L("inter-predictor Spearman:")
L(X.corr(method="spearman").round(2).to_string())
L("wettest fire seasons:", X.precip_mm_fs.sort_values(ascending=False).head(2).round(0).to_dict(),
  "| ONI:", X.ONI_fs.loc[X.precip_mm_fs.sort_values(ascending=False).head(2).index].round(1).to_dict())
L.save()

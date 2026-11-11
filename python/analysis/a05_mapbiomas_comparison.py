#!/usr/bin/env python3
"""a05 - FINN burned area vs MapBiomas Fogo Collection 4 mapped burned area (2012-2024).

MapBiomas: annual burned area per municipality extracted in Google Earth Engine with
gee/mapbiomas_fogo_col4_municipal.js (burned mask > 0 binarised, x ee.Image.pixelArea(), sum at
30 m over the IBGE 2024 mesh) -> data/external/mapbiomas_fogo_col4_SC_municipal_km2_2012_2024.csv.
FINN: sum of AREA of the MODIS+VIIRS records (v2.5 to 2021, v2.5.1 from 2022), by the municipality
containing each record. The two quantities are defined differently (FINN: nominal detection areas
summed day by day; MapBiomas: 30 m scars), so the comparison uses ratios and rank/linear correlations.
Outputs: results/tables/mapbiomas_state.csv, mapbiomas_municipal.csv, mapbiomas_agreement_by_year.csv,
         mapbiomas_area_per_event.csv; results/logs/a05_mapbiomas_comparison.txt
Manuscript (v3.2): sections 2.7, 3 and 4, Table S3, Figure S1. Inventory report: sections 2, 4 and 8.
"""
from _setup import TAB, Log, load_records, screened_events, municipalities, path
import numpy as np
import pandas as pd
from scipy import stats

L = Log("a05_mapbiomas_comparison")
mu = municipalities()
mb = pd.read_csv(path("mapbiomas_fire")).rename(columns={"burned_km2": "mb_km2"})
mb = mb.merge(mu[["CD_MUN", "AREA_KM2", "mesorregiao"]], on="CD_MUN", how="left")
L(f"MapBiomas rows {len(mb)}; municipalities {mb.CD_MUN.nunique()}; years {mb.year.min()}-{mb.year.max()}; "
  f"negative values {(mb.mb_km2 < 0).sum()}")
mb["frac"] = mb.mb_km2 / mb.AREA_KM2
L(f"max fraction of a municipality burned in one year: {100 * mb.frac.max():.2f}% "
  f"({mb.loc[mb.frac.idxmax(), 'NM_MUN']}, {int(mb.loc[mb.frac.idxmax(), 'year'])})")

rec = load_records("MV")
rec = rec[rec.year <= mb.year.max()]
fm = rec.groupby(["year", "CD_MUN"]).AREA.sum().div(1e6).rename("finn_km2").reset_index()
j = mb.merge(fm, on=["year", "CD_MUN"], how="left").fillna({"finn_km2": 0.0})
j.to_csv(TAB / "mapbiomas_municipal.csv", index=False)

d = pd.DataFrame({"finn": rec.groupby("year").AREA.sum() / 1e6, "mb": mb.groupby("year").mb_km2.sum()})
d["ratio"] = d.finn / d.mb
d.to_csv(TAB / "mapbiomas_state.csv")
L(d.round(2).to_string())


def corr(a, b, lab):
    pr, sr = stats.pearsonr(a, b), stats.spearmanr(a, b)
    L(f"{lab}: n = {len(a)}; Pearson r = {pr[0]:.3f} (p = {pr[1]:.4f}); Spearman rho = {sr[0]:.3f} (p = {sr[1]:.4f})")


corr(d.finn, d.mb, "state series 2012-2024")
e = d.drop(index=2012)
corr(e.finn, e.mb, "without 2012 (Landsat 7 only)")
L(f"FINN/MapBiomas ratio: median {d.ratio.median():.2f}; range {d.ratio.min():.2f} ({d.ratio.idxmin()}) to "
  f"{d.ratio.max():.2f} ({d.ratio.idxmax()})")
for y0, y1 in ((2020, 2023), (2023, 2024)):
    L(f"change {y0}->{y1}: FINN {100 * (d.finn[y1] / d.finn[y0] - 1):+.1f}%  MapBiomas {100 * (d.mb[y1] / d.mb[y0] - 1):+.1f}%")

rows = []
for y, g in j.groupby("year"):
    sr = stats.spearmanr(g.finn_km2, g.mb_km2)
    top = set(g.nlargest(10, "mb_km2").CD_MUN)
    t10, rest = g[g.CD_MUN.isin(top)], g[~g.CD_MUN.isin(top)]
    rows.append(dict(year=y, n=len(g), spearman=sr[0], p=sr[1],
                     share_mb_top10=100 * t10.mb_km2.sum() / g.mb_km2.sum(),
                     share_finn_top10mb=100 * t10.finn_km2.sum() / g.finn_km2.sum(),
                     ratio_top10=t10.finn_km2.sum() / t10.mb_km2.sum(),
                     ratio_rest=rest.finn_km2.sum() / rest.mb_km2.sum()))
M = pd.DataFrame(rows).set_index("year")
M.to_csv(TAB / "mapbiomas_agreement_by_year.csv")
L(M.round(3).to_string())
L(f"municipal Spearman per year: {M.spearman.min():.2f} to {M.spearman.max():.2f} (all p <= {M.p.max():.1e}); "
  f"top-10 share of MapBiomas area {M.share_mb_top10.min():.0f}-{M.share_mb_top10.max():.0f}%, of FINN area "
  f"{M.share_finn_top10mb.min():.0f}-{M.share_finn_top10mb.max():.0f}%; ratio top-10 {M.ratio_top10.min():.1f}-"
  f"{M.ratio_top10.max():.1f}, rest {M.ratio_rest.min():.0f}-{M.ratio_rest.max():.0f}")
sh = j.groupby("mesorregiao")[["finn_km2", "mb_km2"]].sum()
L("share of 2012-2024 burned area by mesoregion (%):", (100 * sh / sh.sum()).round(1).to_dict())

# mapped area per FINN event (report v2, section 4): is a high CO2 per event matched by larger scars?
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag) & (E.year <= mb.year.max())]
code = dict(zip(mu.NM_MUN, mu.CD_MUN))
E["CD_MUN"] = E.mun_event.map(code)
pe = E.groupby("CD_MUN").agg(events=("POLYID", "size"), CO2=("CO2", "sum"), finn_area=("area_m2", "sum"))
pe = pe.join(mb.groupby("CD_MUN").mb_km2.sum()).join(mu.set_index("CD_MUN")[["NM_MUN"]])
pe["finn_km2_per_event"] = pe.finn_area / 1e6 / pe.events
pe["mb_km2_per_event"] = pe.mb_km2 / pe.events
pe["CO2_t_per_event"] = pe.CO2 / pe.events
pe.to_csv(TAB / "mapbiomas_area_per_event.csv")
q = pe[pe.events >= 13]
r1 = stats.spearmanr(q.finn_km2_per_event, q.mb_km2_per_event)
r2 = stats.spearmanr(q.CO2_t_per_event, q.mb_km2_per_event)
L(f"2012-2024, municipalities with >= 13 events (n = {len(q)}): Spearman FINN area/event vs MapBiomas area/event "
  f"rho = {r1[0]:.2f} (p = {r1[1]:.2g}); CO2/event vs MapBiomas area/event rho = {r2[0]:.2f} (p = {r2[1]:.2g})")
for n in ("São Joaquim", "Lages", "Capão Alto", "Água Doce", "Curitibanos", "Lebon Régis", "São José do Cerrito"):
    r = pe[pe.NM_MUN == n].iloc[0]
    L(f"  {n}: events {int(r.events)}; FINN area/event {r.finn_km2_per_event:.3f} km2; MapBiomas area/event "
      f"{r.mb_km2_per_event:.4f} km2; CO2/event {r.CO2_t_per_event:.0f} t")
L.save()

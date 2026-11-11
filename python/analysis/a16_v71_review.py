#!/usr/bin/env python3
"""a16 - checks asked in the authors' comments on the abstract of the English manuscript v7 (2026-11-07).

Questions and outputs (results/tables, log results/logs/a16_v71_review.txt)
  climate_per_event.csv       do wetter fire seasons have lower emissions per event, or only fewer events? Spearman
                              correlations of events, CO2, CO2 per event and burned area per event (MODIS+VIIRS screened
                              events, 2012-2025) with the July-November (fire-season) precipitation of ERA5-Land.
  area_ratio_screened.csv     FINN area / mapped area with the FINN area of all MODIS+VIIRS records (as in a05, a14) and of
                              the screened events only (persistent thermal anomalies removed), 2012-2024.
  municipal_top_2020_versions.csv  largest CO2 emitters of 2020 in FINN v1.5 (records), FINN v2.5 MODIS and FINN v2.5
                              MODIS+VIIRS (record municipality), to compare the model versions within one year.
"""
import pandas as pd
from scipy import stats
from _setup import ROOT, TAB, Log, load_records

L = Log("a16_v71_review")
EXT = ROOT / "data" / "external"

# 1. emissions per event and fire-season precipitation
E = pd.read_csv(TAB / "events.csv.gz")
E = E[E.sensor == "MODIS+VIIRS"]
E["flag"] = E.flag.astype(str).str.lower().isin(["true", "1"])
S = E[~E.flag].groupby("year").agg(events=("CO2", "size"), CO2=("CO2", "sum"), area_m2=("area_m2", "sum"))
S["CO2_per_event_t"] = S.CO2 / S.events
S["area_per_event_km2"] = S.area_m2 / S.events / 1e6
C = pd.read_csv(EXT / "era5land_oni_SC_fire_season_2012_2025.csv").set_index("year")
S = S.join(C[["precip_mm_fs"]])
rows = []
for v in ("events", "CO2", "CO2_per_event_t", "area_per_event_km2"):
    r = stats.spearmanr(S[v], S.precip_mm_fs)
    rows.append(dict(response=v, predictor="precip_mm_fs (Jul-Nov total)", n=len(S), rho=r.correlation, p=r.pvalue))
R = pd.DataFrame(rows)
S.reset_index().to_csv(TAB / "climate_per_event.csv", index=False)
R.to_csv(TAB / "climate_per_event_spearman.csv", index=False)
L("1. Spearman correlation with July-November precipitation (ERA5-Land, State mean), MODIS+VIIRS screened events, 2012-2025")
for r in rows:
    L(f"   {r['response']:<20} rho = {r['rho']:+.3f}  p = {r['p']:.3f}  n = {r['n']}")
L(f"   CO2 per event: {S.CO2_per_event_t.min():.0f} to {S.CO2_per_event_t.max():.0f} t; "
  f"area per event: {S.area_per_event_km2.min():.3f} to {S.area_per_event_km2.max():.3f} km2")

# 2. FINN / mapped area before and after screening
A = E.groupby("year").area_m2.sum().rename("finn_all_km2") / 1e6
B = E[~E.flag].groupby("year").area_m2.sum().rename("finn_screened_km2") / 1e6
mb = pd.read_csv(TAB / "mapbiomas_state.csv").set_index("year")
mc = pd.read_csv(TAB / "mcd64a1_comparison_state.csv").set_index("year")
K = pd.concat([A, B], axis=1).join(mb[["finn", "mb"]]).join(mc[["mcd_km2"]]).dropna()
assert (K.finn_all_km2 - K.finn).abs().max() < 1e-6, "FINN area of mapbiomas_state.csv must equal all MODIS+VIIRS records"
K["flagged_area_pct"] = 100 * (K.finn_all_km2 - K.finn_screened_km2) / K.finn_all_km2
for lab, col in (("mb", "mb"), ("mcd", "mcd_km2")):
    K[f"ratio_all_{lab}"] = K.finn_all_km2 / K[col]
    K[f"ratio_screened_{lab}"] = K.finn_screened_km2 / K[col]
K.drop(columns="finn").reset_index().to_csv(TAB / "area_ratio_screened.csv", index=False)
L("\n2. FINN area / mapped area, 2012-2024 (all MODIS+VIIRS records vs screened events)")
for lab in ("mb", "mcd"):
    L(f"   {lab}: median all {K[f'ratio_all_{lab}'].median():.2f}, screened {K[f'ratio_screened_{lab}'].median():.2f}; "
      f"screened range {K[f'ratio_screened_{lab}'].min():.1f} to {K[f'ratio_screened_{lab}'].max():.1f}")
L(f"   area of the persistent anomalies: median {K.flagged_area_pct.median():.3f}%, max {K.flagged_area_pct.max():.3f}% "
  f"({int(K.flagged_area_pct.idxmax())}) of the FINN area")

# 3. largest CO2 emitters of 2020 by model version
v15 = pd.read_csv(EXT / "finn15_2020_SC_records.csv", sep=None, engine="python")
v15 = v15.rename(columns=lambda c: c.strip())
rec = load_records()
r20 = rec[rec.year == 2020]
out = []
for lab, d, col in (("FINN v1.5 MODIS", v15, "NM_MUN"),
                    ("FINN v2.5 MODIS", r20[r20.sensor == "MODIS"], "NM_MUN"),
                    ("FINN v2.5 MODIS+VIIRS", r20[r20.sensor == "MODIS+VIIRS"], "NM_MUN")):
    g = d.groupby(col).CO2.sum().sort_values(ascending=False)
    tot = g.sum()
    for k, (m, v) in enumerate(g.head(10).items(), 1):
        out.append(dict(product=lab, rank=k, municipality=m, CO2_t=v, share_pct=100 * v / tot))
    L(f"\n3. {lab} 2020: CO2 {tot / 1e6:.2f} Mt; top 5: " + "; ".join(f"{m} {v / 1e3:.0f} kt" for m, v in g.head(5).items()))
T = pd.DataFrame(out)
T.to_csv(TAB / "municipal_top_2020_versions.csv", index=False)
top = {p: set(T[(T["product"] == p) & (T["rank"] <= 10)].municipality) for p in T["product"].unique()}
L(f"   common to the 10 largest, v1.5 and v2.5 MODIS+VIIRS: {len(top['FINN v1.5 MODIS'] & top['FINN v2.5 MODIS+VIIRS'])}")
g15 = v15.groupby("NM_MUN").CO2.sum(); g25 = r20[r20.sensor == "MODIS+VIIRS"].groupby("NM_MUN").CO2.sum()
j = pd.concat([g15.rename("v15"), g25.rename("v25")], axis=1).fillna(0)
r = stats.spearmanr(j.v15, j.v25)
L(f"   municipal CO2 2020, v1.5 vs v2.5 MODIS+VIIRS: Spearman rho = {r.correlation:.3f} (n = {len(j)})")
L.save()

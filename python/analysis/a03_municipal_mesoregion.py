#!/usr/bin/env python3
"""a03 - municipal and mesoregion results for the report year (2025) and seasonality.

Emissions and burned area: every FINN record, assigned to the municipality that contains its
point (IBGE 2024 mesh). Events: screened events (a01), assigned to the municipality with the
largest share of their AREA. Mesoregions: IBGE (1990) mesoregions, municipality crosswalk in
data/external/sc_municipios_2024_atributos.csv.
Manuscript (v3.2): Table 3, Table S4, Figures 3, 4, 6 and 7 (data), sections 3 and 4.
Outputs: results/tables/municipal_<year>.csv (Table 4 of the report, Table S4 of the manuscript),
         mesoregion_<year>.csv (Table 3), municipal_events_by_year.csv; results/logs/a03_*.txt
"""
from _setup import CFG, TAB, Log, load_records, screened_events, municipalities
import pandas as pd
from finn_sc.events import doy_to_month

L = Log("a03_municipal_mesoregion")
Y = CFG["analysis"]["report_year"]
SP = ["CO2", "CO", "PM25", "OC", "NOXasNO", "CH4", "NH3", "NMOC", "BC", "SO2"]
mu = municipalities()
meso = dict(zip(mu.NM_MUN, mu.mesorregiao))
area_mun = dict(zip(mu.NM_MUN, mu.AREA_KM2))
rec = load_records("MV")
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)]

me = E.groupby(["year", "mun_event"]).size().rename("events").reset_index()
me.to_csv(TAB / "municipal_events_by_year.csv", index=False)

r = rec[rec.year == Y]
M = r.groupby("NM_MUN").agg(records=("GENVEG", "size"), area_km2=("AREA", lambda a: a.sum() / 1e6),
                            **{s: (s, "sum") for s in SP})
ev = me[me.year == Y].set_index("mun_event").events
M = M.join(ev.rename("events"), how="outer").fillna({"events": 0})
M["events"] = M.events.astype(int)
M["NOx_as_NO2"] = M.NOXasNO * 46.0055 / 30.0061
M["mesorregiao"] = M.index.map(meso)
M["pct_area_municipio"] = 100 * M.area_km2 / M.index.map(area_mun)
M.index.name = "municipio"
M.to_csv(TAB / f"municipal_{Y}.csv")
L(f"{Y}: municipalities with records {int((M.records > 0).sum())}; with screened events {int((M.events > 0).sum())}; "
  f"rows in table {len(M)}")

T3 = M.groupby("mesorregiao")[SP + ["area_km2", "events"]].sum()
T3.to_csv(TAB / f"mesoregion_{Y}.csv")
L("Table 3 (t/yr; NOx as NO; COV = NMOC):")
L(T3.round(0).astype("int64").to_string())
sh = 100 * T3[SP] / T3[SP].sum()
so = sh.loc["Serrana"] + sh.loc["Oeste Catarinense"]
L("Serrana share (%):", sh.loc["Serrana"].round(2).to_dict())
L("Serrana + Oeste share (%):", so.round(2).to_dict(), f"| min {so.idxmin()} {so.min():.2f} | max {so.idxmax()} {so.max():.2f}")
L(f"PM2.5 Serrana / Oeste = {T3.PM25['Serrana'] / T3.PM25['Oeste Catarinense']:.2f}; "
  f"Serrana / Vale do Itajaí = {T3.PM25['Serrana'] / T3.PM25['Vale do Itajaí']:.2f}")

area_meso = mu.groupby("mesorregiao").AREA_KM2.sum()
for y in (Y - 1, Y):
    t = me[me.year == y].sort_values(["events", "mun_event"], ascending=[False, True])
    L(f"{y} top-12 events:", [(a, int(b)) for a, b in zip(t.mun_event.head(12), t.events.head(12))])
    L(f"{y}: municipalities with events {len(t)}; >=100 events: {int((t.events >= 100).sum())} {t[t.events >= 100].mun_event.tolist()}")
    em = t.assign(meso=t.mun_event.map(meso)).groupby("meso").events.sum()
    L(f"{y} events by mesoregion:", em.to_dict(), "| total", int(em.sum()),
      "| shares %", (100 * em / em.sum()).round(1).to_dict())
    L(f"{y} events per 100 km2:", (100 * em / area_meso).round(2).to_dict(), "| state", round(100 * em.sum() / area_meso.sum(), 2))
t24 = me[me.year == Y - 1].set_index("mun_event").events
t25 = me[me.year == Y].set_index("mun_event").events
for m in t25.sort_values(ascending=False).head(12).index:
    L(f"  {m}: {Y - 1} {int(t24.get(m, 0))} -> {Y} {int(t25.get(m, 0))} ({100 * (t25.get(m, 0) / t24.get(m) - 1):+.1f}%)")
top3 = t25.sort_values(ascending=False).head(3)
L(f"{Y} top-3 municipalities: {top3.to_dict()} = {top3.sum()} events = {100 * top3.sum() / t25.sum():.1f}% of the state")
dens = (100 * t25 / t25.index.map(area_mun)).sort_values(ascending=False)
L(f"{Y} highest event densities (per 100 km2):", dens.head(8).round(1).to_dict())

for c in SP:
    s = M[c].sort_values(ascending=False)
    L(f"  {Y} leader {c}: {s.index[0]} {s.iloc[0]:.1f} | 2nd {s.index[1]} {s.iloc[1]:.1f}")
pm = M.PM25.sort_values(ascending=False)
k = int((pm > 500).sum())
L(f"{Y} municipalities with PM2.5 > 500 t: {k}:", pm.head(k).round(0).to_dict(), f"| next {pm.index[k]} {pm.iloc[k]:.0f}")
for name in ("Lages", "São Joaquim", "São José do Cerrito", "Água Doce", "Capão Alto"):
    L(f"  {name}: area {M.area_km2[name]:.1f} km2 = {M.pct_area_municipio[name]:.1f}% of the municipality; CO2 {M.CO2[name]:.0f} t; "
      f"PM2.5 {M.PM25[name]:.0f} t; NMOC {M.NMOC[name]:.0f} t; NOXasNO {M.NOXasNO[name]:.0f} t; events {M.events[name]}")
L(f"{Y} state FINN area {M.area_km2.sum():.1f} km2")

# seasonality (screened events, MODIS+VIIRS)
E = E.assign(month=doy_to_month(E.year, E.DAY))
fs = CFG["analysis"]["fire_season_months"]
for lab, sub in ((str(Y), E[E.year == Y]), ("2012-2025", E)):
    mon = sub.month.value_counts().sort_index()
    L(f"{lab} events by month:", mon.to_dict(), f"| Jul-Sep {100 * mon.loc[7:9].sum() / mon.sum():.1f}% "
      f"| Aug {100 * mon.loc[8] / mon.sum():.1f}% | Jul-Nov {100 * mon.loc[fs].sum() / mon.sum():.1f}%")
e = E[E.year == Y]
L(f"{Y} event area (km2): median {e.area_m2.median() / 1e6:.3f}; p90 {e.area_m2.quantile(.9) / 1e6:.2f}; "
  f"detections per event: median {e.n_det.median():.0f}, mean {e.n_det.mean():.2f}")
L.save()

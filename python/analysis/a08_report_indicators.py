#!/usr/bin/env python3
"""a08 - indicators used only in the inventory report (Appendix A box and section 4).

  * coefficient of variation of the annual state CO2 (2012-2025, sample SD);
  * Gini index of municipal CO2 in the report year (municipalities with emissions, and all 295);
  * CO2 and FINN area per screened event by municipality (report year), with the FINN
    temperate-forest share (GENVEG 4) of each municipality's FINN area, and per dominant GENVEG;
  * share of the legacy bounding-box ("grid") records that fall inside SC (pipeline diagnostic).
Outputs: results/tables/intensity_per_event_<year>.csv; results/logs/a08_report_indicators.txt
"""
from _setup import CFG, TAB, Log, load_records, screened_events, municipalities, ROOT
import pandas as pd
from scipy import stats
from finn_sc.stats import cv_percent, gini

L = Log("a08_report_indicators")
Y = CFG["analysis"]["report_year"]
mu = municipalities()
meso = dict(zip(mu.NM_MUN, mu.mesorregiao))
rec = load_records("MV")
co2 = rec.groupby("year").CO2.sum()
L(f"annual CO2 2012-2025: min {co2.min():.0f} ({co2.idxmin()}), max {co2.max():.0f} ({co2.idxmax()}), "
  f"mean {co2.mean():.0f}, CV {cv_percent(co2):.1f}%")

m = rec[rec.year == Y].groupby("NM_MUN").CO2.sum()
allm = m.reindex(mu.NM_MUN).fillna(0.0)
L(f"Gini of municipal CO2 {Y}: {gini(m):.3f} (n = {len(m)} municipalities with emissions); "
  f"{gini(allm):.3f} (n = {len(allm)}, zeros included)")
s = m.sort_values(ascending=False)
cs = s.cumsum() / s.sum()
L(f"top-10 municipalities hold {100 * cs.iloc[9]:.1f}% of the CO2; {int((cs < 0.5).sum()) + 1} municipalities hold half of it")

E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)]
e = E[E.year == Y]
I = e.groupby("mun_event").agg(events=("POLYID", "size"), CO2=("CO2", "sum"), area_km2=("area_m2", lambda a: a.sum() / 1e6),
                               CO2_median=("CO2", "median"), area_median_km2=("area_m2", lambda a: a.median() / 1e6))
I["CO2_per_event"] = I.CO2 / I.events
I["area_km2_per_event"] = I.area_km2 / I.events
r = rec[rec.year == Y]
f4 = r.assign(A4=r.AREA.where(r.GENVEG == 4, 0.0)).groupby("NM_MUN")[["A4", "AREA"]].sum()
I["finn_forest4_share"] = (f4.A4 / f4.AREA).reindex(I.index)
I["mesorregiao"] = I.index.map(meso)
I.index.name = "municipio"
I.to_csv(TAB / f"intensity_per_event_{Y}.csv")
q = I[I.events >= 5]
L(f"{Y}: municipalities with >= 5 screened events: {len(q)}; CO2 per event median {q.CO2_per_event.median():.0f} t "
  f"(IQR {q.CO2_per_event.quantile(.25):.0f}-{q.CO2_per_event.quantile(.75):.0f}); state mean {e.CO2.sum() / len(e):.0f} t; "
  f"Serrana mean {e[e.mun_event.map(meso) == 'Serrana'].CO2.mean():.0f} t")
rho = stats.spearmanr(q.finn_forest4_share, q.CO2_per_event)
L(f"Spearman FINN temperate-forest share vs CO2 per event ({Y}, n = {len(q)}): rho = {rho[0]:.2f} (p = {rho[1]:.2g})")
for n in ("São Joaquim", "Lages", "Capão Alto", "Bom Jardim da Serra", "Painel", "Água Doce",
          "São José do Cerrito", "Curitibanos", "Lebon Régis"):
    x = I.loc[n]
    L(f"  {n}: events {int(x.events)}; CO2 {x.CO2:.0f} t; CO2/event {x.CO2_per_event:.0f} t (median {x.CO2_median:.0f}); "
      f"area/event {x.area_km2_per_event:.3f} km2 (median {x.area_median_km2:.3f}); FINN temperate-forest share "
      f"{100 * x.finn_forest4_share:.1f}%")
dom = r.groupby(["DAY", "POLYID", "GENVEG"]).AREA.sum().reset_index().sort_values(["AREA", "GENVEG"], ascending=[False, True])
dom = dom.drop_duplicates(["DAY", "POLYID"]).rename(columns={"GENVEG": "dom"})[["DAY", "POLYID", "dom"]]
ed = e.merge(dom, on=["DAY", "POLYID"], how="left")
for k, g in ed.groupby("dom"):
    L(f"  {Y} events with dominant GENVEG {k}: n = {len(g)}; CO2 per event median {g.CO2.median():.0f} t, mean {g.CO2.mean():.0f} t; "
      f"area median {g.area_m2.median() / 1e6:.3f} km2")

g = ROOT / "data/external/legacy_bbox_record_counts.csv"
if g.is_file():
    G = pd.read_csv(g)
    st = pd.read_csv(TAB / "state_counts.csv")
    x = G.merge(st, on=["year", "sensor", "version"])
    x = x[x.sensor == "MODIS+VIIRS"]
    x["pct_in_SC"] = 100 * x.records / x.bbox_records
    L("legacy bounding-box records inside SC (%), MODIS+VIIRS:", x.set_index("year").pct_in_SC.round(1).to_dict(),
      f"| range {x.pct_in_SC.min():.1f}-{x.pct_in_SC.max():.1f}, median {x.pct_in_SC.median():.1f}")
L.save()

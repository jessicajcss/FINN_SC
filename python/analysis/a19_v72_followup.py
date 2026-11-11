"""a19_v72_followup.py - follow-up checks asked by the authors on manuscript v7.2 (2026-11-08).

1. FINNv1 two-day rule in the 2020 FINN v1.5 records of Santa Catarina. Wiedinmyer et al. (2011, Sect. 2): between about
   30 N and 30 S each detection is counted for two days, the second at half of its original size; multiple detections of
   the same 1 km pixel on one day are removed ("there can be only one fire per day"). Checks: do continuations coincide
   with a new detection on the same day, and do the detections without a continuation have a new detection the next day?
   FINN v2.5 keeps the rule only between about 23.5 N and 23.5 S (Wiedinmyer et al., 2023, Sect. 2.1), so the FINN v2.5
   MODIS records of 2020 in SC should have no next-day repeats at the same coordinates.
2. Forest class scenario. FINN v2.5 (Wiedinmyer et al., 2023, Table 1) assigns evergreen broadleaf and mixed forests to
   tropical forest only between 23.5 N and 23.5 S and to temperate forest elsewhere, so all forest detections of SC are
   temperate forest (GENVEG 4). Table 2 (South America): fuel loading 26,755 g m-2 for tropical and 7,400 g m-2 for
   temperate forest; Table 4: CO2 emission factor 1,643 and 1,510 g kg-1, CO 93 and 122 g kg-1. The fraction burned is a
   function of tree and herbaceous cover (Sect. 2.4), not of the class, so for the same detection the emissions of the
   tropical class are (26,755 x EF_trop) / (7,400 x EF_temp) times those of the temperate class. The scenario multiplies
   the GENVEG 4 emissions by this factor (upper bound: GENVEG 4 also holds deciduous broadleaf forest, always temperate).
3. NOx of the earlier state inventory against the FINN v1.5 records (data/external/legacy_finn15_lcqar_2020.csv).
Outputs: results/tables/finn15_2020_continuation_rule.csv, forest_class_scenario.csv, forest_class_scenario_annual.csv;
log a19_v72_followup.txt.
"""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from _setup import ROOT, TAB, Log, load_records

L = Log("a19_v72_followup")
EXT = ROOT / "data" / "external"


def xyz(lon, lat):
    lo, la = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)] * 6371.0088


def nearest(a, b):
    """distance (km) from each row of a to the nearest row of b"""
    if len(b) == 0:
        return np.full(len(a), np.inf)
    return cKDTree(xyz(b.LONGI, b.LATI)).query(xyz(a.LONGI, a.LATI), k=1)[0]


# ------------------------------------------------------------------ 1. two-day rule
V = pd.read_csv(TAB / "finn15_v25_2020_records.csv")
o, c = V[V.role == "original"].copy(), V[V.role == "continuation"].copy()
L("1. FINNv1 two-day rule, FINN v1.5 records of 2020 in SC")
L(f"   records {len(V)}; distinct day-location pairs {len(V.drop_duplicates(['DAY', 'LONGI', 'LATI']))}")
c["d_same_day"] = np.concatenate([nearest(g, o[o.DAY == d]) for d, g in c.groupby("DAY")])[np.argsort(np.argsort(
    np.concatenate([g.index.values for _, g in c.groupby("DAY")])))]
key = set(zip(c.DAY - 1, c.LONGI.round(5), c.LATI.round(5)))
o["has_continuation"] = [(d, round(x, 5), round(y, 5)) in key for d, x, y in zip(o.DAY, o.LONGI, o.LATI)]
idx = np.concatenate([g.index.values for _, g in o.groupby("DAY")])
dn = np.concatenate([nearest(g, o[o.DAY == d + 1]) for d, g in o.groupby("DAY")])
o.loc[idx, "d_next_day"] = dn
rows = []
for r_ in (1.0, 1.5, 2.0):
    rows.append(dict(radius_km=r_,
                     continuations_with_same_day_detection=int((c.d_same_day <= r_).sum()),
                     detections_with_continuation_and_next_day_detection=int((o.has_continuation & (o.d_next_day <= r_)).sum()),
                     detections_without_continuation_with_next_day_detection=int((~o.has_continuation & (o.d_next_day <= r_)).sum())))
R = pd.DataFrame(rows)
R["detections"] = len(o); R["continuations"] = len(c); R["detections_without_continuation"] = int((~o.has_continuation).sum())
R.to_csv(TAB / "finn15_2020_continuation_rule.csv", index=False)
L(f"   original detections {len(o)}: {int(o.has_continuation.sum())} with a next-day continuation, "
  f"{int((~o.has_continuation).sum())} without")
for r in R.itertuples():
    L(f"   within {r.radius_km} km: continuations with a new detection on the same day {r.continuations_with_same_day_detection}; "
      f"detections with continuation and a new detection the next day {r.detections_with_continuation_and_next_day_detection}; "
      f"detections without continuation and with a new detection the next day {r.detections_without_continuation_with_next_day_detection}")
m = load_records("MODIS")
m = m[m.year == 2020]
a = m.groupby(["DAY", "LONGI", "LATI"]).CO2.sum().reset_index()
b = a.copy(); b["DAY"] += 1
p = a.merge(b, on=["DAY", "LONGI", "LATI"], suffixes=("", "_prev"))
L(f"   FINN v2.5 MODIS 2020: {len(a)} day-location pairs; same coordinates as on the previous day: {len(p)} "
  f"(CO2 ratio {', '.join(f'{x:.2f}' for x in p.CO2 / p.CO2_prev)})")

# ------------------------------------------------------------------ 2. forest class scenario
FL_TROP, FL_TEMP = 26755.0, 7400.0           # g m-2, South America, Wiedinmyer et al. (2023) Table 2
EF = {"CO2": (1643.0, 1510.0), "CO": (93.0, 122.0)}  # g kg-1, tropical, temperate forest, Table 4
L("2. Forest class scenario (FINN v2.5 parameters, South America)")
out = []
for label, rec in (("2020 MODIS", load_records("MODIS")), ("2020 MODIS+VIIRS", load_records("MV")),
                   ("2025 MODIS+VIIRS", load_records("MV"))):
    yr = int(label[:4]); rec = rec[rec.year == yr]
    for sp, (et, ee) in EF.items():
        f = (FL_TROP * et) / (FL_TEMP * ee)
        tot = rec[sp].sum(); f4 = rec.loc[rec.GENVEG == 4, sp].sum()
        out.append(dict(case=label, species=sp, factor_tropical_vs_temperate=f, total_t=tot, temperate_forest_t=f4,
                        temperate_forest_pct=100 * f4 / tot, scenario_total_t=tot + (f - 1) * f4,
                        scenario_vs_reported=(tot + (f - 1) * f4) / tot))
S = pd.DataFrame(out)
S.to_csv(TAB / "forest_class_scenario.csv", index=False)
mv = load_records("MV")
fco2 = (FL_TROP * EF["CO2"][0]) / (FL_TEMP * EF["CO2"][1])
A = mv.groupby("year").CO2.sum().to_frame("total_t").join(mv[mv.GENVEG == 4].groupby("year").CO2.sum().rename("temperate_forest_t"))
A["temperate_forest_pct"] = 100 * A.temperate_forest_t / A.total_t
A["scenario_vs_reported"] = (A.total_t + (fco2 - 1) * A.temperate_forest_t) / A.total_t
A = A.loc[2012:2025]
A.reset_index().to_csv(TAB / "forest_class_scenario_annual.csv", index=False)
L(f"   MODIS+VIIRS 2012-2025, CO2: temperate forest {A.temperate_forest_pct.min():.1f}% to {A.temperate_forest_pct.max():.1f}% of the annual total; "
  f"scenario / reported {A.scenario_vs_reported.min():.2f} to {A.scenario_vs_reported.max():.2f} (median {A.scenario_vs_reported.median():.2f})")
for r in S.itertuples():
    L(f"   {r.case} {r.species}: factor {r.factor_tropical_vs_temperate:.2f}; temperate forest {r.temperate_forest_pct:.1f}% "
      f"of {r.total_t / 1e3:,.0f} kt; scenario {r.scenario_total_t / 1e3:,.0f} kt ({r.scenario_vs_reported:.2f} x)")

# ------------------------------------------------------------------ 3. NOx of the earlier state inventory
G = pd.read_csv(EXT / "legacy_finn15_lcqar_2020.csv").set_index("source")
f15, lc = G.loc["finn15_sc_records"], G.loc["lcqar_2022_report"]
L("3. Earlier state inventory (LCQAR, 2022, Table 11) against the FINN v1.5 records of 2020")
for col in ("CO2_t", "CO_t", "PM25_t", "NOx_t", "count"):
    L(f"   {col}: records {float(f15[col]):,.1f}; LCQAR {float(lc[col]):,.1f}; difference "
      f"{100 * (float(f15[col]) / float(lc[col]) - 1):+.2f}%")
L(f"   NOx of the records defined as {f15.NOx_definition}")
L.save()

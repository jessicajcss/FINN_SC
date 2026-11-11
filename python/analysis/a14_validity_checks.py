#!/usr/bin/env python3
"""a14 - validity checks of the inventory report v5.2 (2026-10-31).

Three checks asked in the adversarial review of report v5.1 (wildfire/PARECER_adversarial_relatorio_v5.1.md):

A. FINN vegetation class vs MapBiomas land use and land cover at the event location.
   FINN assigns each detection a generic vegetation type (GENVEG, from MODIS MCD12Q1/VCF; Wiedinmyer et al. 2023,
   Table 1). For every screened MODIS+VIIRS event of 2012-2025 the dominant GENVEG (largest FINN area) is crossed with
   the MapBiomas group at the event position (centroid of its detections): pixel under the centroid (~120 m) and, as
   sensitivity, the majority group of the classified pixels in a 5 x 5 window (~600 m, about the VIIRS-MODIS footprint).
   Main map: Collection 10, 2019; sensitivity: nearest map in time (2019 for 2012-2021, Collection 10.1 2023 for
   2022-2025). Groups as in a07/a13. Subsets: State; Profile A (Lages, São Joaquim, Painel) and Profile B (Lebon Régis,
   Curitibanos, São José do Cerrito) of report section 3.5.
B. Emission scenario with the mapped burned area. FINN emissions scale linearly with burned area (Equation 1). The
   State totals of each year 2012-2024 are multiplied by the ratio of the mapped area (MapBiomas Fogo Collection 4, and
   MCD64A1 C6.1) to the FINN area, i.e. the FINN emission per km2 is kept and the area term is replaced. Both products
   omit small and short-lived scars, so the scenario is a lower reference, not a correction.
C. Robustness of the recurrence analysis (a13, 2 km grid): 95 % intervals of the selection ratios by a spatial block
   bootstrap (blocks of 20 km, 999 replicates) and the spatial error model refitted with distance-band weights
   (binary band of 6 and 10 km, row-standardised).
Outputs
  results/tables/finn_genveg_vs_mapbiomas.csv, emission_scenario_mapped_area.csv, recurrence_robustness.csv
  results/logs/a14_validity_checks.txt
"""
import numpy as np
import pandas as pd
from _setup import ROOT, TAB, Log, load_records, screened_events

SEED = 20261031
EXT = ROOT / "data" / "external"
L = Log("a14_validity_checks")
GROUPS = {"forest": [1, 3, 4, 5, 6, 49], "grassland": [12], "pasture": [15],
          "agriculture": [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62], "plantation": [9]}
ORDER = ["forest", "grassland", "pasture", "agriculture", "plantation", "other"]
GV = {1: "savanna_grassland", 2: "woody_savanna", 4: "temperate_forest", 9: "cropland"}
PROFILE = {"A": ["Lages", "São Joaquim", "Painel"], "B": ["Lebon Régis", "Curitibanos", "São José do Cerrito"]}
LUT = np.full(256, len(ORDER) - 1, dtype=np.int8)
for k, g in enumerate(ORDER[:-1]):
    LUT[GROUPS[g]] = k


# ------------------------------------------------------------------ A. vegetation class at the event location
def mapbiomas_at(lon, lat, year, window):
    z = np.load(EXT / f"mapbiomas_c10_lulc{year}_SC_120m.npz")
    a, inside, t = z["a"], z["inside"], z["transform"]
    c = np.floor((lon - t[2]) / t[0]).astype(int)
    r = np.floor((lat - t[5]) / t[4]).astype(int)
    ok = (r >= 0) & (r < a.shape[0]) & (c >= 0) & (c < a.shape[1])
    out = np.full(len(lon), -1, dtype=int)
    h = window // 2
    for i in np.nonzero(ok)[0]:
        blk = a[max(r[i] - h, 0):r[i] + h + 1, max(c[i] - h, 0):c[i] + h + 1]
        cls = blk[blk > 0]
        if window == 1:
            v = a[r[i], c[i]]
            out[i] = LUT[v] if v > 0 else -1
        elif len(cls):
            out[i] = np.bincount(LUT[cls], minlength=len(ORDER)).argmax()
    return out


rec = load_records("MV")
rec = rec[rec.year >= 2012]
key = ["year", "DAY", "POLYID"]
ga = rec.groupby(key + ["GENVEG"]).AREA.sum().reset_index()
# dominant GENVEG = largest FINN area of the event. Ties (the same area in two or more types) go to the lowest GENVEG
# code, the rule of a08, so that the result does not depend on the sorting algorithm of the installed pandas/numpy.
asc = [True] * len(key)
dom = (ga.sort_values(key + ["AREA", "GENVEG"], ascending=asc + [False, True], kind="mergesort")
       .drop_duplicates(key)[key + ["GENVEG"]])
dom_alt = (ga.sort_values(key + ["AREA", "GENVEG"], ascending=asc + [False, False], kind="mergesort")
           .drop_duplicates(key)[key + ["GENVEG"]])          # sensitivity: ties to the highest GENVEG code
n_top = ga[ga.AREA == ga.groupby(key).AREA.transform("max")].groupby(key).size()
tied = n_top[n_top > 1].reset_index()[key].assign(tied=1)
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag) & (E.year >= 2012)].merge(dom, on=key, how="left")
L(f"A. screened MODIS+VIIRS events 2012-2025: {len(E)}; without dominant GENVEG: {E.GENVEG.isna().sum()}")
E["tied"] = E.merge(tied, on=key, how="left").tied.notna().values
L(f"   events whose largest FINN area is shared by two or more GENVEG types: {int(E.tied.sum())} "
  f"({100 * E.tied.mean():.1f}%); assigned to the lowest GENVEG code")
E["mb_px"] = mapbiomas_at(E.lon.values, E.lat.values, 2019, 1)
E["mb_win"] = mapbiomas_at(E.lon.values, E.lat.values, 2019, 5)
near = np.where(E.year.values <= 2021, 2019, 2023)
E["mb_near"] = -1
for y in (2019, 2023):
    m = near == y
    E.loc[m, "mb_near"] = mapbiomas_at(E.lon.values[m], E.lat.values[m], y, 1)
L(f"   events on unclassified pixels (pixel, 2019 map): {(E.mb_px < 0).sum()}")

rows = []
subsets = [("State 2012-2025", E), ("State 2025", E[E.year == 2025]),
           ("Profile A 2012-2025", E[E.mun_event.isin(PROFILE["A"])]),
           ("Profile B 2012-2025", E[E.mun_event.isin(PROFILE["B"])])]
for lab, s in subsets:
    for col, variant in (("mb_px", "pixel 2019"), ("mb_win", "5x5 window 2019"), ("mb_near", "pixel nearest map")):
        s2 = s[s[col] >= 0]
        for gv in (1, 2, 4, 9, "all"):
            q = s2 if gv == "all" else s2[s2.GENVEG == gv]
            if not len(q):
                continue
            n = q.groupby(col).size().reindex(range(len(ORDER)), fill_value=0)
            w = q.groupby(col).CO2.sum().reindex(range(len(ORDER)), fill_value=0.0)
            row = dict(subset=lab, variant=variant, finn_genveg=("all" if gv == "all" else GV[gv]), events=len(q),
                       CO2_t=q.CO2.sum())
            for k, g in enumerate(ORDER):
                row[f"pct_events_{g}"] = 100 * n[k] / n.sum()
                row[f"pct_CO2_{g}"] = 100 * w[k] / w.sum() if w.sum() > 0 else np.nan
            rows.append(row)
X = pd.DataFrame(rows)
X.to_csv(TAB / "finn_genveg_vs_mapbiomas.csv", index=False)
show = ["subset", "finn_genveg", "events"] + [f"pct_events_{g}" for g in ORDER]
for v in ("pixel 2019", "5x5 window 2019", "pixel nearest map"):
    L(f"\nA. MapBiomas group (% of events) by FINN dominant vegetation class; {v}")
    L(X[X.variant == v][show].round(1).to_string(index=False))
Ea = E.drop(columns="GENVEG").merge(dom_alt, on=key, how="left")
for lab, s_ in (("State 2012-2025", Ea), ("Profile B 2012-2025", Ea[Ea.mun_event.isin(PROFILE["B"])])):
    q = s_[(s_.GENVEG == 4) & (s_.mb_px >= 0)]
    n = q.groupby("mb_px").size().reindex(range(len(ORDER)), fill_value=0)
    w = q.groupby("mb_px").CO2.sum().reindex(range(len(ORDER)), fill_value=0.0)
    L(f"   sensitivity (ties to the highest GENVEG code), {lab}, temperate forest, pixel 2019: {len(q)} events; "
      f"forest {100 * n[0] / n.sum():.1f}% of events and {100 * w[0] / w.sum():.1f}% of CO2; "
      f"plantation {100 * n[4] / n.sum():.1f}% of events and {100 * w[4] / w.sum():.1f}% of CO2")
L("\nA. CO2-weighted (pixel 2019): % of CO2 of the events of each FINN class by MapBiomas group")
L(X[X.variant == "pixel 2019"][["subset", "finn_genveg", "CO2_t"] + [f"pct_CO2_{g}" for g in ORDER]].round(1)
  .to_string(index=False))

# event-level use vs availability: share of the events on each group / share of the group in the State's classified area
z = np.load(EXT / "mapbiomas_c10_lulc2019_SC_120m.npz")
a_, ins_, t_ = z["a"], z["inside"], z["transform"]
rr, cc = np.nonzero(ins_ & (a_ > 0))
lat_ = t_[5] + (rr + 0.5) * t_[4]
Rk = 6371007.2
pix_area = (Rk ** 2) * np.radians(t_[0]) * (np.sin(np.radians(lat_) + np.radians(-t_[4]) / 2)
                                           - np.sin(np.radians(lat_) - np.radians(-t_[4]) / 2))
avail = np.bincount(LUT[a_[rr, cc]], weights=pix_area, minlength=len(ORDER))
avail = 100 * avail / avail.sum()
L("\nA. State classified area by group, MapBiomas 2019 (%): " + "; ".join(f"{g} {avail[k]:.1f}" for k, g in enumerate(ORDER)))
sel_rows = []
for lab, s in (("State 2012-2025", E), ("State 2025", E[E.year == 2025])):
    for col, variant in (("mb_px", "pixel 2019"), ("mb_win", "5x5 window 2019")):
        s2 = s[s[col] >= 0]
        n = s2.groupby(col).size().reindex(range(len(ORDER)), fill_value=0)
        pe = 100 * n / n.sum()
        for k, g in enumerate(ORDER):
            sel_rows.append(dict(subset=lab, variant=variant, group=g, pct_events=pe[k], pct_state_area=avail[k],
                                 use_availability_ratio=pe[k] / avail[k]))
        L(f"A. {lab}, {variant}: % of events (ratio to the State area share): "
          + "; ".join(f"{g} {pe[k]:.1f} ({pe[k] / avail[k]:.2f})" for k, g in enumerate(ORDER)))
pd.DataFrame(sel_rows).to_csv(TAB / "event_landcover_use_availability.csv", index=False)

# ------------------------------------------------------------------ B. scenario with the mapped area
mb = pd.read_csv(TAB / "mapbiomas_state.csv").set_index("year")
mc = pd.read_csv(TAB / "mcd64a1_comparison_state.csv").set_index("year")
S = pd.read_csv(TAB / "series_state_all_products.csv")
S = S[S.sensor == "MODIS+VIIRS"].set_index("year")
sc = []
for y in range(2012, 2025):
    f = S.loc[y]
    sc.append(dict(year=y, finn_area_km2=mb.loc[y, "finn"], mb_area_km2=mb.loc[y, "mb"], mcd_area_km2=mc.loc[y, "mcd_km2"],
                   CO2_finn_t=f.CO2, PM25_finn_t=f.PM25,
                   CO2_mb_scenario_t=f.CO2 * mb.loc[y, "mb"] / mb.loc[y, "finn"],
                   PM25_mb_scenario_t=f.PM25 * mb.loc[y, "mb"] / mb.loc[y, "finn"],
                   CO2_mcd_scenario_t=f.CO2 * mc.loc[y, "mcd_km2"] / mb.loc[y, "finn"],
                   PM25_mcd_scenario_t=f.PM25 * mc.loc[y, "mcd_km2"] / mb.loc[y, "finn"]))
SC = pd.DataFrame(sc)
SC.to_csv(TAB / "emission_scenario_mapped_area.csv", index=False)
L("\nB. State CO2 and PM2.5 with the FINN area replaced by the mapped area (t)")
L(SC.round(0).to_string(index=False))
r24 = SC[SC.year == 2024].iloc[0]
L(f"2024: CO2 FINN {r24.CO2_finn_t / 1e6:.2f} Mt; MapBiomas-area scenario {r24.CO2_mb_scenario_t / 1e6:.3f} Mt; "
  f"MCD64A1-area scenario {r24.CO2_mcd_scenario_t / 1e6:.3f} Mt; PM2.5 {r24.PM25_finn_t:.0f} t vs {r24.PM25_mb_scenario_t:.0f} "
  f"and {r24.PM25_mcd_scenario_t:.0f} t")
L(f"2012-2024 range of the MapBiomas-area scenario: CO2 {SC.CO2_mb_scenario_t.min() / 1e6:.3f} to "
  f"{SC.CO2_mb_scenario_t.max() / 1e6:.3f} Mt")

# ------------------------------------------------------------------ C. recurrence robustness
import libpysal
import spreg
G = pd.read_csv(TAB / "recurrence_grid_2km.csv")
rng = np.random.default_rng(SEED)
G["blk"] = (np.floor(G.x_c / 20000).astype(int).astype(str) + "_" + np.floor(G.y_c / 20000).astype(int).astype(str))
blocks = G.blk.unique()
idx = {b: np.nonzero(G.blk.values == b)[0] for b in blocks}
dom = G.dominant.values; hi = G.R.values >= 7


def sel_ratio(ii):
    d, h = dom[ii], hi[ii]
    out = {}
    for g in ORDER:
        pc = (d == g).mean(); ph = (d[h] == g).mean() if h.any() else np.nan
        out[g] = ph / pc if pc > 0 else np.nan
    return out


base = sel_ratio(np.arange(len(G)))
B = []
for _ in range(999):
    pick = rng.choice(blocks, size=len(blocks), replace=True)
    ii = np.concatenate([idx[b] for b in pick])
    B.append(sel_ratio(ii))
B = pd.DataFrame(B)
rows = []
for g in ORDER:
    rows.append(dict(check="selection_ratio_block_bootstrap", term=g, estimate=base[g],
                     lo95=np.nanpercentile(B[g], 2.5), hi95=np.nanpercentile(B[g], 97.5),
                     note=f"{len(blocks)} blocks of 20 km, 999 replicates"))
L(f"\nC. selection ratio (R >= 7), 95 % block-bootstrap interval ({len(blocks)} blocks of 20 km)")
for r in rows:
    L(f"   {r['term']:12s} {r['estimate']:.2f} ({r['lo95']:.2f} to {r['hi95']:.2f})")

XN = ["grassland", "pasture", "agriculture", "plantation", "other"]
y = np.log((G.R.values + 0.5) / (14 - G.R.values + 0.5)).reshape(-1, 1)
Xm = G[XN].values
pts = np.c_[G.x_c.values, G.y_c.values]
for d_km in (6, 10):
    W = libpysal.weights.DistanceBand(pts, threshold=d_km * 1000, binary=True, silence_warnings=True)
    W.transform = "r"
    m = spreg.GM_Error_Het(y, Xm, w=W, name_x=XN)
    names = m.name_x
    for k, nm in enumerate(names):
        if nm in XN:
            b = float(m.betas[k][0]); se = float(np.sqrt(m.vm[k, k]))
            rows.append(dict(check=f"GM_Error_Het distance band {d_km} km", term=nm, estimate=np.exp(0.1 * b),
                             lo95=np.exp(0.1 * (b - 1.96 * se)), hi95=np.exp(0.1 * (b + 1.96 * se)),
                             note=f"odds ratio per +10 p.p.; mean neighbours {W.mean_neighbors:.1f}"))
    L(f"\nC. GM_Error_Het, distance band {d_km} km (mean neighbours {W.mean_neighbors:.1f}): odds ratio per +10 p.p. (95 % CI)")
    for r in rows[-len(XN):]:
        L(f"   {r['term']:12s} {r['estimate']:.2f} ({r['lo95']:.2f} to {r['hi95']:.2f})")
pd.DataFrame(rows).to_csv(TAB / "recurrence_robustness.csv", index=False)
L.save()

#!/usr/bin/env python3
"""a17 - checks asked in the authors' comments on the English manuscript v7.1 (2026-11-08).

1. FINN v1.5 versus v2.5 in 2020, record by record (comments on why the versions differ).
   FINNv1 counts each MODIS detection between about 30 N and 30 S for two days, the second day at half of its
   original size, because MODIS does not observe these latitudes every day (Wiedinmyer et al., 2011, Sect. 2).
   FINN v2.5 has no such rule (one record set per detection and day; Wiedinmyer et al., 2023). Here every FINN v1.5
   record of 2020 is classified as an original detection or a next-day continuation (same coordinates as a record of
   the previous day, CO2 about half of it), the originals are matched to the FINN v2.5 MODIS detections (same day,
   within 2 km), and the difference in CO2 is split into continuation, number of detections, area per detection and
   CO2 per unit area (vegetation class and its parameters).
2. MapBiomas land use and land cover at the event locations by mesoregion (Serrana in particular), as a14 did for
   the State: share of the screened MODIS+VIIRS events of 2012-2025 on each group (pixel of the 2019 map under the
   event centroid) divided by the share of the group in the classified area of the mesoregion.
3. Characterization of the mesoregions and of the municipalities with the largest fire activity in 2025: area,
   population (2022 Census), GDP and agricultural share of the gross value added (IBGE), land cover (MapBiomas 2023)
   and FINN fire indicators.
Outputs (results/tables): finn15_v25_2020_records.csv, finn15_v25_2020_decomposition.csv,
  finn15_v25_2020_genveg_matched.csv, event_landcover_by_mesoregion.csv, mesoregion_profile.csv,
  municipal_profile_top2025.csv; log results/logs/a17_v72_review.txt
"""
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from _setup import ROOT, TAB, Log, load_records

L = Log("a17_v72_review")
EXT = ROOT / "data" / "external"
RK = 6371.0088


def xyz(lon, lat):
    lo, la = np.radians(np.asarray(lon, float)), np.radians(np.asarray(lat, float))
    return np.c_[np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)] * RK


# ============================================================ 1. FINN v1.5 versus v2.5, 2020
v15 = pd.read_csv(EXT / "finn15_2020_SC_records.csv")
v15["DAY"] = v15["DAY"].astype(str).str.split().str[-1].astype(int)       # first field carries the source URL
v15["key"] = v15.LONGI.round(4).astype(str) + "_" + v15.LATI.round(4).astype(str)
prev = v15[["DAY", "key", "CO2", "AREA"]].copy()
prev["DAY"] += 1
v15 = v15.merge(prev.rename(columns={"CO2": "CO2_prev", "AREA": "AREA_prev"}), on=["DAY", "key"], how="left")
v15["ratio_prev"] = v15.CO2 / v15.CO2_prev
v15["role"] = np.where(v15.ratio_prev.between(0.45, 0.55), "continuation", "original")
L("1. FINN v1.5, 2020, Santa Catarina")
L(f"   records {len(v15)}; distinct coordinates {v15.key.nunique()}; records with the same coordinates on the previous "
  f"day {v15.CO2_prev.notna().sum()}")
L(f"   CO2 ratio to the previous-day record at the same coordinates: median {v15.ratio_prev.median():.3f}; "
  f"between 0.45 and 0.55: {v15.ratio_prev.between(0.45, 0.55).sum()}; area ratio median "
  f"{(v15.AREA / v15.AREA_prev).median():.3f}")
o, c = v15[v15.role == "original"], v15[v15.role == "continuation"]
L(f"   originals {len(o)} (CO2 {o.CO2.sum() / 1e6:.2f} Mt; AREA field {o.AREA.sum() / 1e6:.0f} km2); continuations "
  f"{len(c)} (CO2 {c.CO2.sum() / 1e6:.2f} Mt, {100 * c.CO2.sum() / v15.CO2.sum():.1f}% of the total; AREA field "
  f"{c.AREA.sum() / 1e6:.0f} km2, entering the emissions at half: {0.5 * c.AREA.sum() / 1e6:.0f} km2)")
L(f"   CO of the continuations: {100 * c.CO.sum() / v15.CO.sum():.1f}% of the FINN v1.5 CO of 2020")
# continuations whose original is a full detection of the previous day
rec = load_records()
m = rec[(rec.year == 2020) & (rec.sensor == "MODIS")]
det = m.groupby(["DAY", "FIREID"]).agg(LONGI=("LONGI", "first"), LATI=("LATI", "first"), AREA=("AREA", "sum"),
                                      CO2=("CO2", "sum")).reset_index()
mv = rec[(rec.year == 2020) & (rec.sensor == "MODIS+VIIRS")]


def same_day(A, B, tol=2.0, shift=0):
    hit, idx = np.zeros(len(A), bool), np.full(len(A), -1)
    for d in np.unique(A.DAY):
        a = np.nonzero(A.DAY.values == d)[0]
        b = np.nonzero(B.DAY.values == d + shift)[0]
        if len(b) == 0:
            continue
        dist, j = cKDTree(xyz(B.LONGI.values[b], B.LATI.values[b])).query(xyz(A.LONGI.values[a], A.LATI.values[a]))
        hit[a], idx[a] = dist <= tol, np.where(dist <= tol, b[j], -1)
    return hit, idx


h_o, j_o = same_day(o.reset_index(drop=True), det)
h_c, _ = same_day(c.reset_index(drop=True), det, shift=-1)
h_d, _ = same_day(det, o.reset_index(drop=True))
L(f"   FINN v2.5 MODIS 2020: {len(m)} records, {len(det)} detections, area {m.AREA.sum() / 1e6:.0f} km2, "
  f"CO2 {m.CO2.sum() / 1e6:.2f} Mt; MODIS+VIIRS: area {mv.AREA.sum() / 1e6:.0f} km2, CO2 {mv.CO2.sum() / 1e6:.2f} Mt")
L(f"   v1.5 originals with a v2.5 MODIS detection on the same day within 2 km: {h_o.sum()} of {len(o)} "
  f"({100 * h_o.mean():.1f}%); continuations with a v2.5 detection on the previous day: {h_c.sum()} of {len(c)} "
  f"({100 * h_c.mean():.1f}%); v2.5 detections with a v1.5 original: {h_d.sum()} of {len(det)} ({100 * h_d.mean():.1f}%)")
v15.drop(columns=["key"]).to_csv(TAB / "finn15_v25_2020_records.csv", index=False)

# vegetation class of the same detection in each version
oo = o.reset_index(drop=True)
mm = m.groupby(["DAY", "FIREID"]).apply(lambda g: g.loc[g.AREA.idxmax(), "GENVEG"], include_groups=False)
det["GENVEG_dom"] = mm.reindex(pd.MultiIndex.from_frame(det[["DAY", "FIREID"]])).values
pair = pd.DataFrame(dict(gv15=oo.GENVEG.values[h_o], gv25=det.GENVEG_dom.values[j_o[h_o]],
                         co2_15=oo.CO2.values[h_o], area15=oo.AREA.values[h_o],
                         co2_25=det.CO2.values[j_o[h_o]], area25=det.AREA.values[j_o[h_o]]))
G = pair.groupby(["gv15", "gv25"]).agg(n=("co2_15", "size"), CO2_v15_t=("co2_15", "sum"), CO2_v25_t=("co2_25", "sum"),
                                       area_v15_km2=("area15", "sum"), area_v25_km2=("area25", "sum")).reset_index()
G["area_v15_km2"] /= 1e6
G["area_v25_km2"] /= 1e6
G["t_CO2_per_km2_v15"] = G.CO2_v15_t / G.area_v15_km2
G["t_CO2_per_km2_v25"] = G.CO2_v25_t / G.area_v25_km2
G.to_csv(TAB / "finn15_v25_2020_genveg_matched.csv", index=False)
L("   matched detections, vegetation class v1.5 x v2.5 (1 savanna/grassland, 2 woody savanna, 3 tropical forest, "
  "4 temperate forest, 9 cropland):")
L(G.round(1).to_string(index=False))
L(f"   matched: CO2 v1.5 {pair.co2_15.sum() / 1e6:.2f} Mt vs v2.5 {pair.co2_25.sum() / 1e6:.2f} Mt; "
  f"area {pair.area15.sum() / 1e6:.0f} vs {pair.area25.sum() / 1e6:.0f} km2")

# decomposition of v1.5 (all) -> v2.5 MODIS into multiplicative factors
T15, T25 = v15.CO2.sum(), m.CO2.sum()
O15 = o.CO2.sum()
A15, A25 = o.AREA.sum() / 1e6, m.AREA.sum() / 1e6
n15, n25 = len(o), len(det)
steps = [
    ("FINN v1.5, all records", T15),
    ("without next-day continuations", O15),
    ("number of detections as in v2.5 MODIS", O15 * n25 / n15),
    ("area per detection as in v2.5 MODIS", O15 * A25 / A15),
    ("CO2 per km2 as in v2.5 MODIS (= FINN v2.5 MODIS)", T25),
]
D = pd.DataFrame(steps, columns=["step", "CO2_t"])
D["factor_vs_previous"] = D.CO2_t / D.CO2_t.shift(1)
D.loc[2, "factor_vs_previous"] = n25 / n15
D.loc[3, "factor_vs_previous"] = (A25 / n25) / (A15 / n15)
D.loc[4, "factor_vs_previous"] = (T25 / A25) / (O15 / A15)
D.to_csv(TAB / "finn15_v25_2020_decomposition.csv", index=False)
L("   decomposition (each step changes one term; the last step reaches the FINN v2.5 MODIS total):")
for _, r in D.iterrows():
    L(f"     {r.step:<50} {r.CO2_t / 1e6:6.2f} Mt  factor {r.factor_vs_previous:.3f}")
L(f"   CO2 per km2: v1.5 originals {O15 / A15:.0f} t/km2; v2.5 MODIS {T25 / A25:.0f} t/km2; v2.5 MODIS+VIIRS "
  f"{mv.CO2.sum() / (mv.AREA.sum() / 1e6):.0f} t/km2")
# shift-share of the CO2 per km2 between v1.5 originals and v2.5 MODIS: class partition vs class intensity
cls = lambda g: g.map({1: "grass", 2: "wsav", 3: "forest", 4: "forest", 9: "crop"}).fillna("other")
a15 = o.assign(c=cls(o.GENVEG), A_=o.AREA / 1e6).groupby("c").agg(A=("A_", "sum"), C=("CO2", "sum"))
a25 = m.assign(c=cls(m.GENVEG), A_=m.AREA / 1e6).groupby("c").agg(A=("A_", "sum"), C=("CO2", "sum"))
k = a15.index.union(a25.index)
a15, a25 = a15.reindex(k, fill_value=0), a25.reindex(k, fill_value=0)
s15, s25 = a15.A / a15.A.sum(), a25.A / a25.A.sum()
e15 = (a15.C / a15.A).fillna(0)
e25 = (a25.C / a25.A).fillna(0)
I15, I25 = (s15 * e15).sum(), (s25 * e25).sum()
mix = 0.5 * (((s25 - s15) * e15).sum() + ((s25 - s15) * e25).sum())
inten = 0.5 * ((s15 * (e25 - e15)).sum() + (s25 * (e25 - e15)).sum())
L(f"   share of area by class (v1.5 originals / v2.5 MODIS): " + "; ".join(f"{i} {100 * s15[i]:.1f}/{100 * s25[i]:.1f}" for i in k))
L(f"   t CO2/km2 by class (v1.5 / v2.5): " + "; ".join(f"{i} {e15[i]:.0f}/{e25[i]:.0f}" for i in k))
L(f"   area-weighted CO2 per km2 v1.5 originals {I15:.0f}, v2.5 MODIS {I25:.0f}; change {I25 - I15:.0f} t/km2 = class partition {mix:.0f} ({100 * mix / (I25 - I15):.0f}%) + "
  f"CO2 per km2 within classes {inten:.0f} ({100 * inten / (I25 - I15):.0f}%)")

# effective area (continuations enter the emissions at half of their AREA field), forest shares and mesoregions
v15["w"] = np.where(v15.role == "continuation", 0.5, 1.0)
eff = (v15.AREA * v15.w).sum() / 1e6
fo = v15.GENVEG.isin([3, 4])
L(f"   FINN v1.5 effective burned area (continuations at half) {eff:.0f} km2; CO2 per effective km2 "
  f"{v15.CO2.sum() / eff:.0f} t; forest (codes 3 and 4) share: originals {100 * o.AREA[o.GENVEG.isin([3, 4])].sum() / o.AREA.sum():.1f}% "
  f"of area and {100 * o.CO2[o.GENVEG.isin([3, 4])].sum() / o.CO2.sum():.1f}% of CO2; all records (effective) "
  f"{100 * (v15.AREA * v15.w)[fo].sum() / (v15.AREA * v15.w).sum():.1f}% of area and {100 * v15.CO2[fo].sum() / v15.CO2.sum():.1f}% of CO2")
L(f"   FINN v2.5 MODIS forest (code 4) share: {100 * m.AREA[m.GENVEG == 4].sum() / m.AREA.sum():.1f}% of area, "
  f"{100 * m.CO2[m.GENVEG == 4].sum() / m.CO2.sum():.1f}% of CO2")
att0 = pd.read_csv(EXT / "sc_municipios_2024_atributos.csv")
mm_ = att0.set_index("NM_MUN").mesorregiao
ma = att0.groupby("mesorregiao").AREA_KM2.sum()
v15["meso"] = v15.NM_MUN.map(mm_)
ro = v15[v15.role == "original"].groupby("meso").size()
ra = v15.groupby("meso").size()
MV = pd.DataFrame(dict(records=ra, originals=ro, area_km2=ma))
MV["records_per_100km2"] = 100 * MV.records / MV.area_km2
MV["originals_per_100km2"] = 100 * MV.originals / MV.area_km2
MV["pct_records"] = 100 * MV.records / MV.records.sum()
MV["pct_originals"] = 100 * MV.originals / MV.originals.sum()
MV.to_csv(TAB / "finn15_2020_mesoregion.csv")
L(f"   FINN v1.5 2020 by mesoregion (records unassigned: {v15.meso.isna().sum()}):")
L(MV.round(2).sort_values("originals_per_100km2", ascending=False).to_string())
L(f"   State: {100 * len(v15) / ma.sum():.2f} records and {100 * (v15.role == 'original').sum() / ma.sum():.2f} originals per 100 km2")

# ============================================================ 2. land cover at the events by mesoregion
GROUPS = {"forest": [1, 3, 4, 5, 6, 49], "grassland": [12], "pasture": [15],
          "agriculture": [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62], "plantation": [9]}
ORDER = ["forest", "grassland", "pasture", "agriculture", "plantation", "other"]
LUT = np.full(256, len(ORDER) - 1, dtype=np.int8)
for kk, g in enumerate(ORDER[:-1]):
    LUT[GROUPS[g]] = kk
z = np.load(EXT / "mapbiomas_c10_lulc2019_SC_120m.npz")
a, inside, t = z["a"], z["inside"], z["transform"]
import geopandas as gpd                                                     # noqa: E402
from rasterio.features import rasterize                                     # noqa: E402
from affine import Affine                                                   # noqa: E402
att = pd.read_csv(EXT / "sc_municipios_2024_atributos.csv")
mun = gpd.read_file(ROOT / "data" / "inputs" / "SC_Municipios_2024.shp", encoding="cp1252").to_crs(4326)
mun["meso"] = mun.NM_MUN.map(att.set_index("NM_MUN").mesorregiao)
mg = mun.dissolve(by="meso").reset_index()
tr = Affine(t[0], t[1], t[2], t[3], t[4], t[5])
lab = rasterize([(g, i + 1) for i, g in enumerate(mg.geometry)], out_shape=a.shape, transform=tr, fill=0)
lat = t[5] + (np.arange(a.shape[0]) + 0.5) * t[4]
pa = ((RK * 1e3) ** 2) * np.radians(t[0]) * (np.sin(np.radians(lat) + np.radians(-t[4]) / 2)
                                             - np.sin(np.radians(lat) - np.radians(-t[4]) / 2))
pa = np.broadcast_to(pa[:, None], a.shape)
E = pd.read_csv(TAB / "events.csv.gz")
E["flag"] = E.flag.astype(str).str.lower().isin(["true", "1"])
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag) & (E.year >= 2012)].copy()
E["meso"] = E.mun_event.map(att.set_index("NM_MUN").mesorregiao)
c_ = np.floor((E.lon.values - t[2]) / t[0]).astype(int)
r_ = np.floor((E.lat.values - t[5]) / t[4]).astype(int)
ok = (r_ >= 0) & (r_ < a.shape[0]) & (c_ >= 0) & (c_ < a.shape[1])
v = np.full(len(E), 0)
v[ok] = a[r_[ok], c_[ok]]
E["grp"] = np.where(v > 0, LUT[v], -1)
rows = []
for i, name in enumerate(list(mg.meso) + ["State"]):
    cl = inside & (a > 0) & ((lab == i + 1) if name != "State" else (lab > 0))
    av = np.bincount(LUT[a[cl]], weights=pa[cl], minlength=len(ORDER))
    av = 100 * av / av.sum()
    s = E if name == "State" else E[E.meso == name]
    s = s[s.grp >= 0]
    n = s.groupby("grp").size().reindex(range(len(ORDER)), fill_value=0)
    w = s.groupby("grp").CO2.sum().reindex(range(len(ORDER)), fill_value=0.0)
    for kk, g in enumerate(ORDER):
        rows.append(dict(mesoregion=name, group=g, events=int(n[kk]), pct_events=100 * n[kk] / n.sum(),
                         pct_CO2=100 * w[kk] / w.sum(), pct_area_classified=av[kk],
                         use_availability_ratio=(100 * n[kk] / n.sum()) / av[kk] if av[kk] > 0 else np.nan))
X = pd.DataFrame(rows)
X.to_csv(TAB / "event_landcover_by_mesoregion.csv", index=False)
L("\n2. MapBiomas 2019 group under the event centroid, screened MODIS+VIIRS events 2012-2025, by mesoregion")
L("   (% of events / % of CO2 / % of the classified area of the mesoregion / ratio)")
for name in list(mg.meso) + ["State"]:
    q = X[X.mesoregion == name]
    L(f"   {name} ({int(q.events.sum())} events): " + "; ".join(
        f"{r.group} {r.pct_events:.1f}/{r.pct_CO2:.1f}/{r.pct_area_classified:.1f}/{r.use_availability_ratio:.2f}"
        for r in q.itertuples()))

# ============================================================ 3. profiles of mesoregions and municipalities
ib = pd.read_csv(EXT / "ibge_sc_municipal_pop2022_gdp2021_2023.csv", comment="#")
P = att.rename(columns={"NM_MUN": "municipality", "mesorregiao": "mesoregion"}).merge(ib, on="CD_MUN", how="left")
assert P.pop2022.notna().all() and len(P) == 295
lc = pd.read_csv(EXT / "mapbiomas_lulc2023_SC_municipal_fractions_all295.csv").rename(columns={"code_muni": "CD_MUN"})
P = P.merge(lc[["CD_MUN", "forest", "grassland", "pasture", "agriculture", "silviculture"]], on="CD_MUN", how="left")
mun25 = pd.read_csv(TAB / "municipal_2025.csv").rename(columns={"municipio": "municipality"})
P = P.merge(mun25[["municipality", "events", "area_km2", "CO2", "PM25"]].rename(
    columns={"area_km2": "finn_area_km2_2025", "CO2": "CO2_t_2025", "PM25": "PM25_t_2025", "events": "events_2025"}),
    on="municipality", how="left").fillna({"events_2025": 0, "finn_area_km2_2025": 0, "CO2_t_2025": 0, "PM25_t_2025": 0})
ey = pd.read_csv(TAB / "municipal_events_by_year.csv")
ey = ey[(ey.year >= 2012)].groupby("mun_event").events.sum() / 14
P["events_mean_2012_2025"] = P.municipality.map(ey).fillna(0)
for col in ("forest", "grassland", "pasture", "agriculture", "silviculture"):
    P[col + "_km2"] = P[col] * P.AREA_KM2
M = P.groupby("mesoregion").agg(municipalities=("CD_MUN", "size"), area_km2=("AREA_KM2", "sum"),
                                pop2022=("pop2022", "sum"), gdp2021_kBRL=("gdp2021_kBRL", "sum"),
                                vab2021_total=("vab2021_total_kBRL", "sum"), vab2021_agro=("vab2021_agro_kBRL", "sum"),
                                forest_km2=("forest_km2", "sum"), grassland_km2=("grassland_km2", "sum"),
                                pasture_km2=("pasture_km2", "sum"), agriculture_km2=("agriculture_km2", "sum"),
                                silviculture_km2=("silviculture_km2", "sum"), events_2025=("events_2025", "sum"),
                                events_mean_2012_2025=("events_mean_2012_2025", "sum"),
                                finn_area_km2_2025=("finn_area_km2_2025", "sum"), CO2_t_2025=("CO2_t_2025", "sum"),
                                PM25_t_2025=("PM25_t_2025", "sum"))
tot = M.sum()
tot.name = "State"
M = pd.concat([M, tot.to_frame().T])


def prof(M):
    out = pd.DataFrame(index=M.index)
    out["municipalities"] = M.municipalities.astype(int)
    out["area_km2"] = M.area_km2
    out["area_pct_state"] = 100 * M.area_km2 / M.loc["State", "area_km2"] if "State" in M.index else np.nan
    out["pop2022"] = M.pop2022.astype(int)
    out["pop_density_per_km2"] = M.pop2022 / M.area_km2
    out["gdp2021_billion_BRL"] = M.gdp2021_kBRL / 1e6
    out["gdp2021_per_capita_kBRL"] = M.gdp2021_kBRL / M.pop2022
    out["agro_pct_of_vab2021"] = 100 * M.vab2021_agro / M.vab2021_total
    for col in ("forest", "grassland", "pasture", "agriculture", "silviculture"):
        out[col + "_pct_2023"] = 100 * M[col + "_km2"] / M.area_km2
    out["events_2025"] = M.events_2025.astype(int)
    out["events_per_100km2_2025"] = 100 * M.events_2025 / M.area_km2
    out["events_per_100km2_mean_2012_2025"] = 100 * M.events_mean_2012_2025 / M.area_km2
    out["finn_area_pct_2025"] = 100 * M.finn_area_km2_2025 / M.area_km2
    out["CO2_kt_2025"] = M.CO2_t_2025 / 1e3
    out["CO2_t_per_km2_2025"] = M.CO2_t_2025 / M.area_km2
    out["CO2_t_per_capita_2025"] = M.CO2_t_2025 / M.pop2022
    return out


MP = prof(M)
MP.index.name = "mesoregion"
MP.reset_index().to_csv(TAB / "mesoregion_profile.csv", index=False)
L("\n3. Mesoregion profile (MapBiomas fractions are of the municipal polygon area; IBGE 2022 Census, GDP 2021)")
L(MP.round(2).T.to_string())
r25 = P.copy()
top = set(r25.nlargest(5, "events_2025").municipality) | set(r25.nlargest(5, "finn_area_km2_2025").municipality) | \
    set(r25.nlargest(5, "CO2_t_2025").municipality)
Q = P[P.municipality.isin(top)].set_index("municipality")
Q = Q.assign(municipalities=1, area_km2=Q.AREA_KM2)
QP = prof(Q.assign(vab2021_total=Q.vab2021_total_kBRL, vab2021_agro=Q.vab2021_agro_kBRL))
QP.insert(0, "mesoregion", Q.mesoregion)
for col, src in (("rank_events_2025", "events_2025"), ("rank_area_2025", "finn_area_km2_2025"), ("rank_CO2_2025", "CO2_t_2025")):
    QP[col] = r25.set_index("municipality")[src].rank(ascending=False, method="min").reindex(QP.index).astype(int)
QP = QP.drop(columns=["municipalities", "area_pct_state"]).sort_values("CO2_kt_2025", ascending=False)
QP.index.name = "municipality"
QP.reset_index().to_csv(TAB / "municipal_profile_top2025.csv", index=False)
L("\n3b. Municipalities among the five largest in events, FINN area or CO2 in 2025")
L(QP.round(2).T.to_string())
L(f"   these {len(QP)} municipalities: {100 * QP.area_km2.sum() / MP.loc['State', 'area_km2']:.1f}% of the State area, "
  f"{100 * Q.pop2022.sum() / MP.loc['State', 'pop2022']:.1f}% of the population, "
  f"{100 * Q.events_2025.sum() / MP.loc['State', 'events_2025']:.1f}% of the 2025 events and "
  f"{100 * Q.CO2_t_2025.sum() / (MP.loc['State', 'CO2_kt_2025'] * 1e3):.1f}% of the 2025 CO2")
L.save()

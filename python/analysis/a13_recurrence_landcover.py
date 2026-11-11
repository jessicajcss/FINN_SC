#!/usr/bin/env python3
"""a13 - recurrence of fire events in a regular grid and land use and land cover (2026-10-30).

Question (inventory report, round 14): where do fire events recur from year to year, and which land use and land cover
dominates those places?

Data
  events      results/tables/events.csv.gz (a01): FINN MODIS+VIIRS events 2012-2025 (v2.5 until 2021, v2.5.1 from 2022),
              persistent thermal anomalies excluded (flag); event position = centroid of its detections.
  land cover  data/external/mapbiomas_c10_lulc2019_SC_120m.npz (MapBiomas Collection 10, 2019, ~120 m; main) and
              data/external/mapbiomas_c10_lulc2023_SC_120m.npz (Collection 10.1, 2023; sensitivity).
Method
  Grid of square cells in SIRGAS 2000 / UTM 22S (EPSG:31982), origin at multiples of the cell size; main size 2 km
  (larger than the 375 m to 1 km detection footprint and the positional uncertainty of an event centroid; at 5 and 10 km,
  used as sensitivity, most cells have events in most years and the recurrence count saturates).
  A cell enters when classified land (MapBiomas class > 0, inside the IBGE state limit) covers at least half of it.
  Recurrence R = number of years of 2012-2025 with at least one event centroid in the cell (0 to 14).
  Land-cover groups (same classes as the municipal analysis of a07): forest formation (1, 3, 4, 5, 6, 49), grassland (12),
  pasture (15), agriculture (18-21, 36, 39-41, 46-48, 62; includes the mosaic of uses, 21), forest plantation (9), other
  (all remaining classes: wetlands, urban, water, non-vegetated). Pixel areas on the sphere by latitude.
  Descriptive: R by dominant group (largest share in the cell); share of high-recurrence cells (R >= 7, events in at
  least half of the years) by dominant group and its ratio to the share of all cells (selection ratio).
  Association: Spearman rho between R and each fraction; spatial error model (spreg; GMM with heteroskedasticity-robust
  inference, Arraiz et al. 2010, for the 2 km grid, n ~ 24,000; maximum likelihood for the 5 km grid) of the empirical logit
  log((R + 0.5) / (14 - R + 0.5)) on the fractions of grassland, pasture, agriculture, forest plantation and other, with
  forest formation as the reference; W = 8 nearest cell centres, row-standardised; Moran's I of OLS and SEM residuals.
  Effect of +10 percentage points: odds ratio exp(0.1 b) of a year with an event.
  Sensitivity: cell size; events at locations detected on 4 or more days in a year also excluded (possible fixed heat
  sources, finn_sc.events.flag_persistent with min_days = 4); 2023 land-cover map; agreement between the 2012-2021 (v2.5)
  and 2022-2025 (v2.5.1) recurrence (Spearman of the share of years with events, cells of the main grid).
Outputs
  results/tables/recurrence_grid_2km.csv, recurrence_by_landcover.csv, recurrence_sem.csv, recurrence_sensitivity.csv
  results/figures/Fig_recurrence_landcover_pt.png
  results/logs/a13_recurrence_landcover.txt
"""
import numpy as np
import pandas as pd
from pyproj import Transformer
from _setup import ROOT, TAB, FIG, Log, load_records, read_shapefile, mesoregion_of
from finn_sc.events import flag_persistent, EVENT_KEY

SEED = 20261030
EXT = ROOT / "data" / "external"
L = Log("a13_recurrence_landcover")
Y0, Y1 = 2012, 2025
NY = Y1 - Y0 + 1
GROUPS = {"forest": [1, 3, 4, 5, 6, 49], "grassland": [12], "pasture": [15],
          "agriculture": [18, 19, 20, 21, 36, 39, 40, 41, 46, 47, 48, 62], "plantation": [9]}
ORDER = ["forest", "grassland", "pasture", "agriculture", "plantation", "other"]
XN = ["grassland", "pasture", "agriculture", "plantation", "other"]
TO_UTM = Transformer.from_crs(4326, 31982, always_xy=True)


def landcover_pixels(year):
    """centres (UTM), spherical areas (m2) and group index of the classified pixels inside the state"""
    z = np.load(EXT / f"mapbiomas_c10_lulc{year}_SC_120m.npz")
    a, inside, t = z["a"], z["inside"], z["transform"]
    rr, cc = np.nonzero(inside & (a > 0))
    lon = t[2] + (cc + 0.5) * t[0]
    lat = t[5] + (rr + 0.5) * t[4]
    R = 6371007.2
    dl, dp = np.radians(t[0]), np.radians(-t[4])
    area = (R ** 2) * dl * (np.sin(np.radians(lat) + dp / 2) - np.sin(np.radians(lat) - dp / 2))
    lut = np.full(256, len(ORDER) - 1, dtype=np.int8)                   # 'other' by default
    for k, g in enumerate(ORDER[:-1]):
        lut[GROUPS[g]] = k
    grp = lut[a[rr, cc]]
    x, y = TO_UTM.transform(lon, lat)
    return x, y, area, grp


def grid_table(size_m, px, events):
    """cells with >= 50 % classified land: fractions of each group, recurrence and event counts"""
    x, y, area, grp = px
    ix = np.floor(x / size_m).astype(np.int64); iy = np.floor(y / size_m).astype(np.int64)
    key = pd.MultiIndex.from_arrays([ix, iy])
    A = pd.DataFrame({"ix": ix, "iy": iy, "g": grp, "a": area})
    tab = A.pivot_table(index=["ix", "iy"], columns="g", values="a", aggfunc="sum", fill_value=0.0)
    tab.columns = [ORDER[c] for c in tab.columns]
    for g in ORDER:
        if g not in tab:
            tab[g] = 0.0
    tab = tab[ORDER]
    land = tab.sum(axis=1)
    tab = tab[land >= 0.5 * size_m ** 2]
    frac = tab.div(tab.sum(axis=1), axis=0)
    frac["land_km2"] = tab.sum(axis=1).values / 1e6
    ex, ey = TO_UTM.transform(events.lon.values, events.lat.values)
    ev = pd.DataFrame({"ix": np.floor(ex / size_m).astype(np.int64), "iy": np.floor(ey / size_m).astype(np.int64),
                       "year": events.year.values})
    rec = ev.groupby(["ix", "iy"]).year.nunique().rename("R")
    n = ev.groupby(["ix", "iy"]).size().rename("events")
    r1 = ev[ev.year <= 2021].groupby(["ix", "iy"]).year.nunique().rename("R_v25")
    r2 = ev[ev.year >= 2022].groupby(["ix", "iy"]).year.nunique().rename("R_v251")
    out = frac.join(rec, how="left").join(n, how="left").join(r1, how="left").join(r2, how="left").fillna(
        {"R": 0, "events": 0, "R_v25": 0, "R_v251": 0})
    for c in ("R", "events", "R_v25", "R_v251"):
        out[c] = out[c].astype(int)
    out["dominant"] = out[ORDER].idxmax(axis=1)
    out["dominant_share"] = out[ORDER].max(axis=1)
    out = out.reset_index()
    out["x_c"] = (out.ix + 0.5) * size_m; out["y_c"] = (out.iy + 0.5) * size_m
    events_out = len(ev) - int(out.events.sum())
    return out, events_out


def by_dominant(G):
    hi = G.R >= 7
    rows = []
    for g in ORDER:
        s = G[G.dominant == g]
        if not len(s):
            continue
        rows.append(dict(dominant=g, cells=len(s), pct_cells=100 * len(s) / len(G), mean_R=s.R.mean(),
                         median_R=s.R.median(), pct_R0=100 * (s.R == 0).mean(), pct_R_ge7=100 * (s.R >= 7).mean(),
                         pct_of_high_cells=100 * (hi & (G.dominant == g)).sum() / hi.sum(),
                         pct_of_events=100 * s.events.sum() / G.events.sum(), median_dominant_share=s.dominant_share.median()))
    T = pd.DataFrame(rows)
    T["selection_ratio_high"] = T.pct_of_high_cells / T.pct_cells
    return T


def sem_fit(G, label):
    import libpysal, spreg, esda
    y = np.log((G.R.values + 0.5) / (NY - G.R.values + 0.5)).reshape(-1, 1)
    X = G[XN].values
    W = libpysal.weights.KNN(np.c_[G.x_c.values, G.y_c.values], k=8)
    W.transform = "r"
    ols = spreg.OLS(y, X, name_x=XN)                                  # no dense spatial diagnostics (n up to 24,000)
    if len(G) > 10000:     # ML variance needs a dense n x n inverse; GMM estimator of Arraiz et al. (2010), sparse
        sem, est = spreg.GM_Error_Het(y, X, w=W, name_x=XN), "GM_Error_Het"
    else:
        sem, est = spreg.ML_Error(y, X, w=W, name_x=XN), "ML_Error"
    np.random.seed(SEED)
    mo = esda.Moran(ols.u.flatten(), W, permutations=999)
    mi = esda.Moran(sem.e_filtered.flatten(), W, permutations=999)
    ols.moran_res = (mo.I, None, mo.p_sim)
    L(f"{label}: n = {len(G)}; OLS R2 = {ols.r2:.3f}; Moran I (OLS residuals) = {mo.I:.3f} "
      f"(p = {mo.p_sim:.3g}); {est} lambda = {float(np.ravel(sem.betas)[-1] if est == 'GM_Error_Het' else sem.lam):.3f}; "
      f"Moran I (SEM filtered) = {mi.I:.3f} (p = {mi.p_sim:.3f})")
    rows = []
    for i, nm in enumerate(["const"] + XN):
        b, se, p = float(sem.betas[i][0]), float(sem.std_err[i]), float(sem.z_stat[i][1])
        orr = float(np.exp(0.1 * b)) if i else np.nan
        lam = float(np.ravel(sem.betas)[-1]) if est == "GM_Error_Het" else float(sem.lam)
        rows.append(dict(model=label, estimator=est, term=nm, n=len(G), b=b, se=se, p=p, odds_ratio_10pp=orr, lam=lam,
                         r2_ols=float(ols.r2), moran_ols=float(ols.moran_res[0]), p_moran_ols=float(ols.moran_res[2]),
                         moran_sem=float(mi.I), p_moran_sem=float(mi.p_sim)))
        if i:
            L(f"   {nm:12s} b = {b:+.3f} (SE {se:.3f}) p = {p:.3g} | +10 p.p. -> odds x{orr:.3f}")
    return rows


def main():
    E = pd.read_csv(TAB / "events.csv.gz")
    mv = E[(E.sensor == "MODIS+VIIRS") & E.year.between(Y0, Y1) & (~E.flag)].copy()
    L(f"events (MODIS+VIIRS, {Y0}-{Y1}, persistent thermal anomalies excluded): {len(mv)}")
    rec = load_records("MV")
    rec = rec[rec.year.between(Y0, Y1)]
    _, fl4 = flag_persistent(rec, 1.0, 4, sensors=("MODIS+VIIRS",))
    mv = mv.merge(fl4.assign(rec4=True), on=EVENT_KEY, how="left")
    mv["rec4"] = mv.rec4.fillna(False).astype(bool)
    L(f"events also at locations detected on >= 4 days in a year: {int(mv.rec4.sum())} ({100 * mv.rec4.mean():.1f}%)")
    px19 = landcover_pixels(2019)
    px23 = landcover_pixels(2023)
    sens, sem_rows = [], []
    main_G = None
    for size_km in (2, 5, 10):
        for evname, evs in (("all", mv), ("no_recurrent_sites", mv[~mv.rec4])):
            for yr, px in ((2019, px19), (2023, px23)):
                if (size_km != 2 or evname != "all") and yr == 2023:
                    continue
                G, lost = grid_table(size_km * 1000, px, evs)
                label = f"{size_km} km | events {evname} | land cover {yr}"
                T = by_dominant(G)
                hi = T.set_index("dominant")
                L(f"\n{label}: cells {len(G)}; events outside the retained cells {lost} of {len(evs)}; "
                  f"cells with R >= 7: {int((G.R >= 7).sum())} ({100 * (G.R >= 7).mean():.1f}%); R = 0: {100 * (G.R == 0).mean():.1f}%")
                L(T.round(3).to_string(index=False))
                rho = {g: G[["R", g]].corr(method="spearman").iloc[0, 1] for g in ORDER}
                L("Spearman rho (R vs fraction): " + "; ".join(f"{g} {r:+.3f}" for g, r in rho.items()))
                for _, r in T.iterrows():
                    sens.append(dict(cell_km=size_km, events=evname, landcover_year=yr, **r.to_dict(),
                                     cells_total=len(G), rho_R_fraction=rho[r.dominant]))
                if size_km == 2 and evname == "all" and yr == 2019:
                    main_G = G
                    T.to_csv(TAB / "recurrence_by_landcover.csv", index=False)
                if yr == 2019 and size_km in (2, 5):
                    sem_rows += sem_fit(G, label)
    G = main_G
    a = G[(G.R_v25 > 0) | (G.R_v251 > 0)]
    rho = pd.Series(G.R_v25 / 10).corr(pd.Series(G.R_v251 / 4), method="spearman")
    L(f"\nagreement of recurrence between periods (2 km, 2019 map): Spearman rho of the share of years with events, "
      f"2012-2021 (v2.5, 10 years) vs 2022-2025 (v2.5.1, 4 years) = {rho:.3f} (n = {len(G)} cells)")
    hiv = G.R_v25 >= 5
    L(f"cells with events in >= 5 of the 10 years 2012-2021: {int(hiv.sum())}; of these, with events in >= 2 of the 4 years "
      f"2022-2025: {100 * (G.loc[hiv, 'R_v251'] >= 2).mean():.1f}% (all cells: {100 * (G.R_v251 >= 2).mean():.1f}%)")
    meso = mesoregion_of()
    gs = read_shapefile().to_crs(31982)
    gs["meso"] = gs.NM_MUN.map(meso)
    import geopandas as gpd
    pts = gpd.GeoDataFrame(G[["ix", "iy"]], geometry=gpd.points_from_xy(G.x_c, G.y_c), crs=31982)
    j = gpd.sjoin(pts, gs[["meso", "geometry"]], how="left", predicate="within")
    j = j[~j.index.duplicated()]
    G["mesorregiao"] = j.meso.values
    hi = G[G.R >= 7]
    L("cells with R >= 7 by mesoregion (centre of the cell): " +
      "; ".join(f"{k} {v} ({100 * v / len(hi):.1f}%)" for k, v in hi.mesorregiao.value_counts().items()))
    L("all cells by mesoregion: " + "; ".join(f"{k} {100 * v / len(G):.1f}%" for k, v in G.mesorregiao.value_counts().items()))
    G.to_csv(TAB / "recurrence_grid_2km.csv", index=False)
    pd.DataFrame(sens).to_csv(TAB / "recurrence_sensitivity.csv", index=False)
    pd.DataFrame(sem_rows).to_csv(TAB / "recurrence_sem.csv", index=False)
    figure(G)
    L.save()


def figure(G):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Rectangle
    import math
    from finn_sc.cartography import rose_above_bar
    from finn_sc import figcheck as fc
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    gs = read_shapefile().to_crs(4674)
    gs["meso"] = gs.NM_MUN.map(mesoregion_of())
    state = gs.dissolve(); mesog = gs.dissolve(by="meso").reset_index()
    T = pd.read_csv(TAB / "recurrence_by_landcover.csv").set_index("dominant").reindex(ORDER)
    fig = plt.figure(figsize=(9.2, 4.4), dpi=200)
    # map on the left; bar chart on the right, far enough for its category labels to stay clear of the map frame
    ax = fig.add_axes([0.01, 0.12, 0.555, 0.82]); axb = fig.add_axes([0.745, 0.25, 0.235, 0.63])
    bounds = [-0.5, 0.5, 2.5, 4.5, 6.5, 9.5, 14.5]
    cols = ["#f0f0f0", "#fee391", "#fec44f", "#fe9929", "#d95f0e", "#8c2d04"]
    cmap = ListedColormap(cols); norm = BoundaryNorm(bounds, cmap.N)
    s = 2000.0
    to_geo = Transformer.from_crs(31982, 4674, always_xy=True)
    from matplotlib.collections import PolyCollection
    polys = []
    for ix, iy in zip(G.ix, G.iy):
        xs = np.array([ix, ix + 1, ix + 1, ix]) * s; ys = np.array([iy, iy, iy + 1, iy + 1]) * s
        lo, la = to_geo.transform(xs, ys)
        polys.append(np.c_[lo, la])
    pc = PolyCollection(polys, array=G.R.values, cmap=cmap, norm=norm, edgecolors="none")
    ax.add_collection(pc)
    mesog.boundary.plot(ax=ax, color="0.35", lw=0.4)
    state.boundary.plot(ax=ax, color="0.1", lw=0.6)
    ax.set_xlim(-54.0, -48.2); ax.set_ylim(-29.5, -25.8); ax.set_aspect(1 / math.cos(math.radians(-27.6)))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    for sp in ax.spines.values():
        sp.set_color("0.6"); sp.set_linewidth(0.5)
    ttl_a = ax.set_title("a) Recorrência: anos com eventos de queimada (2012 a 2025)", loc="left", fontsize=8)
    ax.apply_aspect(); p = ax.get_position()
    # colour bar over the empty area south of the western part of the State, with its label inside the map frame
    cax = fig.add_axes([p.x0 + 0.035 * p.width, p.y0 + 0.17 * p.height, 0.40 * p.width, 0.028])
    cb = fig.colorbar(pc, cax=cax, orientation="horizontal", ticks=[0, 1.5, 3.5, 5.5, 8, 12])
    cb.ax.set_xticklabels(["0", "1–2", "3–4", "5–6", "7–9", "10–14"], fontsize=6)
    cb.set_label("Anos com ao menos um evento (células de 2 km)", fontsize=6.5)
    # scale bar and north rose over the ocean, clear of the coastline and of the map frame
    lat_sb = -29.36; dlon = 100 / (111.32 * math.cos(math.radians(lat_sb))); x1 = -48.42; x0 = x1 - dlon
    n0 = len(ax.patches)
    ax.add_patch(Rectangle((x0, lat_sb), dlon / 2, 0.06, facecolor="k", edgecolor="k", lw=0.4))
    ax.add_patch(Rectangle((x0 + dlon / 2, lat_sb), dlon / 2, 0.06, facecolor="w", edgecolor="k", lw=0.4))
    bar_patches = ax.patches[n0:]
    sb_labels = [ax.annotate(lab, (x0 + j_ * dlon / 2, lat_sb + 0.06), xytext=(0, 2), textcoords="offset points",
                             ha="center", va="bottom", fontsize=5.5) for j_, lab in ((0, "0"), (2, "100 km"))]
    n1 = len(ax.patches); t1 = len(ax.texts)
    rose_above_bar(ax, x1, lat_sb + 0.06, 5.5, size=12, align='right')   # right-justified (2026-11-04)
    rose = ax.patches[n1:] + ax.texts[t1:]
    names = {"forest": "Formação florestal", "grassland": "Formação campestre", "pasture": "Pastagem",
             "agriculture": "Agricultura e mosaico", "plantation": "Silvicultura", "other": "Outros usos"}
    yy = np.arange(len(ORDER))[::-1]
    axb.barh(yy + 0.18, T.pct_cells.values, height=0.34, color="#bdbdbd", label="Todas as células")
    axb.barh(yy - 0.18, T.pct_of_high_cells.values, height=0.34, color="#d95f0e", label="Células com 7 anos ou mais")
    axb.set_yticks(yy); axb.set_yticklabels([names[g] for g in ORDER], fontsize=6.5)
    axb.set_xlabel("% das células (classe predominante, mapa de 2019)", fontsize=6.5)
    axb.set_xlim(0, 50)
    leg = axb.legend(frameon=False, fontsize=6, loc="lower right")
    for s_ in ("top", "right"):
        axb.spines[s_].set_visible(False)
    ttl_b = axb.set_title("b) Uso e cobertura predominante", loc="left", fontsize=8)
    note = fig.text(0.01, 0.015, "FINN MODIS+VIIRS (v2.5 até 2021; v2.5.1 de 2022 a 2025), centroides dos eventos, excluídas "
                    "as anomalias térmicas persistentes; uso e cobertura: MapBiomas, Coleção 10 (2019);\ngrade de 2 km em "
                    "SIRGAS 2000 / UTM 22S, células com ao menos metade da área em terra classificada; linhas: limites "
                    "estadual e das mesorregiões.", fontsize=5.6, va="bottom")
    # layout check (stdout only): no label over another label, the State, the map frame or the bars
    r = fc.renderer(fig)
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union
    bb = lambda a: fc.bbox(a, r)
    tight = lambda a: (lambda e: sbox(e.x0 - 1, e.y0 - 1, e.x1 + 1, e.y1 + 1))(a.get_tightbbox(r))
    W_, H_ = fig.canvas.get_width_height()
    fig_box = sbox(0, 0, W_, H_)
    map_box = bb(ax)
    feats = {"Estado": fc.to_display(ax, state.geometry.iloc[0]),
             "moldura do mapa": map_box.exterior.buffer(0.5),
             "mapa": map_box,
             "barras": unary_union([bb(b) for b in axb.patches])}
    labels = {"título a": (bb(ttl_a), ["mapa"], None),
              "barra de cores": (tight(cax), ["Estado", "moldura do mapa"], "a"),
              "escala": (unary_union([bb(x) for x in bar_patches + sb_labels]), ["Estado", "moldura do mapa"], "a"),
              "rosa dos ventos": (unary_union([bb(x) for x in rose]), ["Estado", "moldura do mapa"], "a"),
              "rótulos de b": (unary_union([bb(t) for t in axb.get_yticklabels()]), ["mapa", "moldura do mapa"], "fig"),
              "eixo x de b": (tight(axb.xaxis), ["mapa"], "fig"),
              "título b": (bb(ttl_b), ["mapa"], "fig"),
              "legenda de b": (bb(leg), ["barras"], "fig"),
              "nota": (bb(note), ["mapa"], "fig")}
    probs = fc.check(labels, feats, {"a": map_box, "fig": fig_box},
                     ignore_pairs=(("escala", "rosa dos ventos"), ("rótulos de b", "eixo x de b")))
    fc.report("Fig_recurrence_landcover_pt", probs)
    fig.savefig(FIG / "Fig_recurrence_landcover_pt.png", facecolor="white")
    plt.close(fig)
    return probs


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""fig_v71 - Figures 8 and 9 of manuscript v7.1 (2026-11-07), in English and Portuguese (FIG_LANG=en or pt).
Same figures as fig_v7_en.py (manuscript v7); the label of the FINN v1.5 row of Figure 9 no longer refers to the earlier
state inventory, because v7.1 compares FINN v2.5 directly with FINN v1.5.

  results/figures/Fig08_recurrence_landcover_en.png  English version of the a13 recurrence figure (Portuguese version in
      Fig_recurrence_landcover_pt.png, Supplementary Figure S4), with the selection ratio of each class and its 95% block
      bootstrap interval (a14, recurrence_robustness.csv) next to the bars.
  results/figures/Fig09_sensitivity_factors_en.png   CO2 obtained with each alternative methodological choice relative to
      this inventory, next to the year-to-year variation of the inventory itself (a15, sensitivity_factors.csv).
Run after a13, a14 and a15. Prints the layout check of Figure 8 (figcheck) to stdout.
"""
import math
import os
import numpy as np
import pandas as pd
from pyproj import Transformer
from _setup import TAB, FIG, read_shapefile, mesoregion_of

ORDER = ["forest", "grassland", "pasture", "agriculture", "plantation", "other"]
LANG = os.environ.get("FIG_LANG", "en")
NOTES = os.environ.get("FIG_NOTES", "1") != "0"   # FIG_NOTES=0: no note or footer in the image (*_nn*.png; 2026-11-08)
NN = "" if NOTES else "_nn"
TX = {
    "en": dict(
        names={"forest": "Forest formation", "grassland": "Grassland", "pasture": "Pasture",
               "agriculture": "Agriculture and mosaic", "plantation": "Forest plantation", "other": "Other uses"},
        ttl_a="a) Recurrence: years with fire events (2012 to 2025)", cb="Years with at least one event (2 km cells)",
        all_cells="All cells", high="Cells with events in 7 or more years", xb="% of cells (dominant class, 2019 map)",
        hdr="Selection ratio\n(95% interval)", ttl_b="b) Dominant land cover of the cells",
        note=("FINN MODIS+VIIRS (v2.5 until 2021; v2.5.1 from 2022 to 2025), event centroids, persistent "
              "thermal anomalies excluded; land use and land cover: MapBiomas Collection 10 (2019);\n2 km grid in "
              "SIRGAS 2000 / UTM 22S, cells with at least half of their area on classified land; lines: State and "
              "mesoregion boundaries; selection ratio: 20 km block bootstrap."),
        rows=["Interannual variability of this inventory\n(annual CO$_2$ / 2012–2025 mean)",
              "MODIS only instead of MODIS+VIIRS\n(FINN v2.5 and v2.5.1, 2012–2023)",
              "FINN v1.5 instead of v2.5\n(2020)",
              "MapBiomas Fire area instead of FINN area\n(2012–2024)",
              "MCD64A1 area instead of FINN area\n(2012–2024)",
              "Tropical instead of temperate forest class\n(FINN v2.5 parameters, 2012–2025)"],
        xl="CO$_2$ relative to this inventory (log scale; 1 = FINN v2.5/v2.5.1, MODIS+VIIRS, FINN burned area)",
        band="factor-of-two band", rng="range",
        foot="Large dot: median of the years; small dots: individual years; grey band: factor of two around this inventory.",
        dec="."),
    "pt": dict(
        names={"forest": "Formação florestal", "grassland": "Formação campestre", "pasture": "Pastagem",
               "agriculture": "Agricultura e mosaico", "plantation": "Silvicultura", "other": "Outros usos"},
        ttl_a="a) Recorrência: anos com eventos de queimada (2012 a 2025)", cb="Anos com ao menos um evento (células de 2 km)",
        all_cells="Todas as células", high="Células com eventos em 7 anos ou mais", xb="% das células (classe predominante, mapa de 2019)",
        hdr="Razão de seleção\n(intervalo de 95%)", ttl_b="b) Uso e cobertura predominante das células",
        note=("FINN MODIS+VIIRS (v2.5 até 2021; v2.5.1 de 2022 a 2025), centroides dos eventos, anomalias térmicas "
              "persistentes excluídas; uso e cobertura do solo: MapBiomas Coleção 10 (2019);\ngrade de 2 km em "
              "SIRGAS 2000 / UTM 22S, células com ao menos metade da área em terra classificada; linhas: limites do "
              "Estado e das mesorregiões; razão de seleção: bootstrap em blocos de 20 km."),
        rows=["Variabilidade interanual deste inventário\n(CO$_2$ anual / média de 2012–2025)",
              "Somente MODIS em vez de MODIS+VIIRS\n(FINN v2.5 e v2.5.1, 2012–2023)",
              "FINN v1.5 em vez de v2.5\n(2020)",
              "Área do MapBiomas Fogo em vez da área do FINN\n(2012–2024)",
              "Área do MCD64A1 em vez da área do FINN\n(2012–2024)",
              "Floresta tropical em vez de temperada\n(parâmetros do FINN v2.5, 2012–2025)"],
        xl="CO$_2$ relativo a este inventário (escala log; 1 = FINN v2.5/v2.5.1, MODIS+VIIRS, área queimada do FINN)",
        band="faixa de fator dois", rng="intervalo",
        foot="Ponto grande: mediana dos anos; pontos pequenos: anos individuais; faixa cinza: fator dois em torno deste inventário.",
        dec=","),
}[LANG]
NAMES = TX["names"]
SUF = "_" + LANG


def num(x, k):
    return f"{x:.{k}f}".replace(".", TX["dec"])


def fig_recurrence():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Rectangle
    from matplotlib.collections import PolyCollection
    from finn_sc.cartography import rose_above_bar
    from finn_sc import figcheck as fc
    from shapely.geometry import box as sbox
    from shapely.ops import unary_union
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    G = pd.read_csv(TAB / "recurrence_grid_2km.csv")
    gs = read_shapefile().to_crs(4674)
    gs["meso"] = gs.NM_MUN.map(mesoregion_of())
    state = gs.dissolve(); mesog = gs.dissolve(by="meso").reset_index()
    T = pd.read_csv(TAB / "recurrence_by_landcover.csv").set_index("dominant").reindex(ORDER)
    B = pd.read_csv(TAB / "recurrence_robustness.csv")
    B = B[B.check == "selection_ratio_block_bootstrap"].set_index("term").reindex(ORDER)
    fig = plt.figure(figsize=(9.2, 4.4), dpi=400)   # 400 dpi: ACS minimum 300 dpi for colour art (11 Nov 2026)
    ax = fig.add_axes([0.01, 0.12, 0.555, 0.82]); axb = fig.add_axes([0.725, 0.27, 0.165, 0.61])
    bounds = [-0.5, 0.5, 2.5, 4.5, 6.5, 9.5, 14.5]
    cols = ["#f0f0f0", "#fee391", "#fec44f", "#fe9929", "#d95f0e", "#8c2d04"]
    cmap = ListedColormap(cols); norm = BoundaryNorm(bounds, cmap.N)
    s = 2000.0
    to_geo = Transformer.from_crs(31982, 4674, always_xy=True)
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
    ttl_a = ax.set_title(TX["ttl_a"], loc="left", fontsize=8)
    ax.apply_aspect(); p = ax.get_position()
    cax = fig.add_axes([p.x0 + 0.035 * p.width, p.y0 + 0.17 * p.height, 0.40 * p.width, 0.028])
    cb = fig.colorbar(pc, cax=cax, orientation="horizontal", ticks=[0, 1.5, 3.5, 5.5, 8, 12])
    cb.ax.set_xticklabels(["0", "1–2", "3–4", "5–6", "7–9", "10–14"], fontsize=6)
    cb.set_label(TX["cb"], fontsize=6.5)
    lat_sb = -29.36; dlon = 100 / (111.32 * math.cos(math.radians(lat_sb))); x1 = -48.42; x0 = x1 - dlon
    n0 = len(ax.patches)
    ax.add_patch(Rectangle((x0, lat_sb), dlon / 2, 0.06, facecolor="k", edgecolor="k", lw=0.4))
    ax.add_patch(Rectangle((x0 + dlon / 2, lat_sb), dlon / 2, 0.06, facecolor="w", edgecolor="k", lw=0.4))
    bar_patches = ax.patches[n0:]
    sb_labels = [ax.annotate(lab, (x0 + j_ * dlon / 2, lat_sb + 0.06), xytext=(0, 2), textcoords="offset points",
                             ha="center", va="bottom", fontsize=5.5) for j_, lab in ((0, "0"), (2, "100 km"))]
    n1 = len(ax.patches); t1 = len(ax.texts)
    rose_above_bar(ax, x1, lat_sb + 0.06, 5.5, size=12, align='right')
    rose = ax.patches[n1:] + ax.texts[t1:]
    yy = np.arange(len(ORDER))[::-1]
    axb.barh(yy + 0.18, T.pct_cells.values, height=0.34, color="#bdbdbd", label=TX["all_cells"])
    axb.barh(yy - 0.18, T.pct_of_high_cells.values, height=0.34, color="#d95f0e", label=TX["high"])
    axb.set_yticks(yy); axb.set_yticklabels([NAMES[g] for g in ORDER], fontsize=6.5)
    axb.set_xlabel(TX["xb"], fontsize=6.5)
    axb.set_xlim(0, 50)
    ratio_txt = []
    for y_, g in zip(yy, ORDER):
        b = B.loc[g]
        ratio_txt.append(axb.text(51.5, y_, f"{num(b.estimate, 2)}\n({num(b.lo95, 2)}–{num(b.hi95, 2)})", fontsize=5.6,
                                  va="center", ha="left", clip_on=False))
    axb.set_ylim(-0.6, len(ORDER) + 0.15)
    hdr = axb.text(51.5, len(ORDER) - 0.5, TX["hdr"], fontsize=5.8, va="bottom", ha="left",
                   fontweight="bold", clip_on=False)
    leg = axb.legend(frameon=False, fontsize=6, loc="upper left", bbox_to_anchor=(-0.02, -0.17), ncol=1)
    for s_ in ("top", "right"):
        axb.spines[s_].set_visible(False)
    ttl_b = axb.set_title(TX["ttl_b"], loc="left", fontsize=8)
    note = fig.text(0.01, 0.015, TX["note"], fontsize=5.6, va="bottom") if NOTES else None
    r = fc.renderer(fig)
    bb = lambda a: fc.bbox(a, r)
    tight = lambda a: (lambda e: sbox(e.x0 - 1, e.y0 - 1, e.x1 + 1, e.y1 + 1))(a.get_tightbbox(r))
    W_, H_ = fig.canvas.get_width_height()
    fig_box = sbox(0, 0, W_, H_); map_box = bb(ax)
    feats = {"State": fc.to_display(ax, state.geometry.iloc[0]), "map frame": map_box.exterior.buffer(0.5),
             "map": map_box, "bars": unary_union([bb(x) for x in axb.patches])}
    labels = {"title a": (bb(ttl_a), ["map"], None),
              "colour bar": (tight(cax), ["State", "map frame"], "a"),
              "scale": (unary_union([bb(x) for x in bar_patches + sb_labels]), ["State", "map frame"], "a"),
              "north rose": (unary_union([bb(x) for x in rose]), ["State", "map frame"], "a"),
              "labels of b": (unary_union([bb(t) for t in axb.get_yticklabels()]), ["map", "map frame"], "fig"),
              "x axis of b": (tight(axb.xaxis), ["map"], "fig"),
              "title b": (bb(ttl_b), ["map"], "fig"),
              "legend of b": (bb(leg), ["bars"], "fig"),
              "selection ratios": (unary_union([bb(t) for t in ratio_txt + [hdr]]), ["bars"], "fig"),
              **({"note": (bb(note), ["map"], "fig")} if NOTES else {})}
    probs = fc.check(labels, feats, {"a": map_box, "fig": fig_box},
                     ignore_pairs=(("scale", "north rose"), ("labels of b", "x axis of b")))
    fc.report("Fig08_recurrence_landcover" + SUF, probs)
    fig.savefig(FIG / f"Fig08_recurrence_landcover{NN}{SUF}.png", facecolor="white", **({} if NOTES else dict(bbox_inches="tight", pad_inches=0.04)))
    plt.close(fig)


def fig_sensitivity():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import FixedLocator, NullLocator
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
    F = pd.read_csv(TAB / "sensitivity_factors.csv")
    FC = pd.read_csv(TAB / "forest_class_scenario_annual.csv")      # a19 (2026-11-08)
    F = pd.concat([F, pd.DataFrame({"item": "forest_class", "year": FC.year, "value": FC.scenario_vs_reported})])
    rows = [(it, lab, col) for (it, col), lab in zip((("interannual", "#7a7a7a"), ("modis_only", "#2a78d6"), ("finn_v15", "#2a78d6"),
                                                       ("mapbiomas_area", "#2a78d6"), ("mcd64a1_area", "#2a78d6"),
                                                       ("forest_class", "#2a78d6")), TX["rows"])]
    fig, ax = plt.subplots(figsize=(6.6, 3.4), dpi=300)
    fig.subplots_adjust(left=0.36, right=0.86, top=0.88, bottom=0.15 if NOTES else 0.12)
    ax.axvspan(0.5, 2.0, color="#eeeeee", zorder=0, lw=0)
    ax.axvline(1.0, color="0.1", lw=1.0, zorder=1)
    for k, (it, lab, col) in enumerate(rows):
        y = len(rows) - 1 - k
        x = F[F.item == it].value.values
        if len(x) > 1:
            ax.plot([x.min(), x.max()], [y, y], color=col, lw=2.2, solid_capstyle="round", zorder=2)
            ax.scatter(x, np.full(len(x), y), s=9, color="white", edgecolor=col, lw=0.8, zorder=3)
            ax.scatter([np.median(x)], [y], s=30, color=col, zorder=4)
            txt = f"{num(x.min(), 3)}–{num(x.max(), 3)}" if x.max() < 0.1 else f"{num(x.min(), 2)}–{num(x.max(), 2)}"
        else:
            ax.scatter(x, [y], s=30, color=col, zorder=4)
            txt = num(x[0], 2)
        ax.text(3.6, y, txt, va="center", ha="left", fontsize=6.6, color="0.15")
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r_[1] for r_ in rows][::-1], fontsize=6.4)
    ax.set_xscale("log"); ax.set_xlim(0.01, 3.4)
    ticks = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2]
    ax.xaxis.set_major_locator(FixedLocator(ticks)); ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([f"{t:g}".replace(".", TX["dec"]) for t in ticks], fontsize=6.4)
    ax.set_xlabel(TX["xl"],
                  fontsize=6.4)
    ax.set_ylim(-0.6, len(rows) - 0.4)
    for s_ in ("top", "right", "left"):
        ax.spines[s_].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", color="0.88", lw=0.4, zorder=0)
    ax.text(1.0, len(rows) - 0.25, TX["band"], ha="center", va="bottom", fontsize=6, color="0.35")
    ax.text(3.6, len(rows) - 0.25, TX["rng"], ha="left", va="bottom", fontsize=6, color="0.35", fontweight="bold")
    if NOTES:
        fig.text(0.02, 0.025, TX["foot"], fontsize=5.8, color="0.3")
    fig.savefig(FIG / f"Fig09_sensitivity_factors{NN}{SUF}.png", facecolor="white", **({} if NOTES else dict(bbox_inches="tight", pad_inches=0.04)))
    plt.close(fig)
    print(f"Fig09_sensitivity_factors{NN}{SUF} written")


if __name__ == "__main__":
    fig_recurrence()
    fig_sensitivity()

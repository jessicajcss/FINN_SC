#!/usr/bin/env python3
"""tools/study_area_map.py - study-area figure (Santa Catarina, Brazil) with land use and land cover.

Inputs (all in the repository):
  data/external/mapbiomas_c10_lulc<YEAR>_SC_120m.npz   MapBiomas land use and land cover, Santa Catarina window at ~120 m
        (array `a` = MapBiomas class id, `inside` = pixel centre inside the state, `transform` = affine of the window in
        EPSG:4326), extracted by tools/extract_mapbiomas_sc.py; 2023 (default since 2026-10-21; Collection 10.1, the image
        of the land-cover analysis of section 2.8, exported by gee/mapbiomas_lulc2023_figure1.ipynb) or 2019
        (FIG1_YEAR=2019; Collection 10, brazil_coverage_2019.tif; the figure of manuscript versions up to v.6.1)
  data/external/mapbiomas_c10_lulc<YEAR>_SC_class_areas.csv   class areas inside the state (60 m level of the same file)
  data/inputs/SC_Municipios_2024.shp (IBGE), data/external/sc_municipios_2024_atributos.csv (mesoregions),
  data/external/ibge_br_uf_2024_simplified.geojson, data/external/ibge_america_do_sul_2021_simplified.geojson
Outputs: results/figures/Fig01_study_area_pt.png (Portuguese, manuscript Figure 1) and Fig01_study_area_en.png (English);
         with FIG1_YEAR=2019, Fig01_study_area_2019_pt.png and _en.png (inventory report);
         results/tables/landcover<YEAR>_mesoregion.csv (land-cover groups by mesoregion).
Legend colours: MapBiomas Collection 10 legend (class of largest area in each group). Groups follow section 2.8 of the
manuscript for forest (3, 5, 49), grassland (12), pasture (15) and silviculture (9); temporary crops (39, 40, 41) and the
mosaic of uses (21) are shown separately here.
"""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd, geopandas as gpd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter
import shapely
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python'))
from finn_sc import figcheck  # noqa: E402
from finn_sc.cartography import rose_above_bar  # noqa: E402
EXT = ROOT / 'data' / 'external'
FIG = ROOT / 'results' / 'figures'
import os
# year of the land-cover map: 2023 by default since 2026-10-21 (manuscript v.6.2; same image as the land-cover analysis of
# section 2.8, written by gee/mapbiomas_lulc2023_figure1.ipynb); FIG1_YEAR=2019 reproduces the figure of v.6.1 and earlier
YEAR = int(os.environ.get('FIG1_YEAR', '2023'))
COLL = {2019: '10', 2023: '10.1'}[YEAR]          # MapBiomas collection of each file
LAT0 = -27.6

GROUPS = [  # key, class ids, colour (MapBiomas C10), PT label, EN label
    ('forest', [3, 5, 49], '#1f8d49', 'Formação florestal', 'Forest formation'),
    ('grass', [12], '#d6bc74', 'Formação campestre', 'Grassland'),
    ('wet', [11, 29, 32, 50], '#519799', 'Outras formações não florestais', 'Other non-forest formations'),
    ('silv', [9], '#7a5900', 'Silvicultura', 'Forest plantation'),
    ('past', [15], '#edde8e', 'Pastagem', 'Pasture'),
    ('crop', [39, 40, 41], '#f54ca9', 'Lavouras temporárias', 'Temporary crops'),
    ('mosaic', [21], '#ffefc3', 'Mosaico de usos', 'Mosaic of uses'),
    ('urban', [24], '#d4271e', 'Área urbanizada', 'Urban area'),
    ('nonveg', [23, 25, 30, 75], '#ffa07a', 'Outras áreas não vegetadas', 'Other non-vegetated areas'),
    ('water', [33, 31], '#2532e4', 'Água', 'Water'),
]
TXT = {
    'pt': dict(out='Fig01_study_area_pt.png', lon='Longitude (°)', lat='Latitude (°)', legend=f'Uso e cobertura do solo, {YEAR}\n(% da área classificada do Estado)',
               sa='América do Sul', ocean='Oceano Atlântico', capital='Capital', city='Município (sede aproximada)', meso='Limite de mesorregião',
               PR='PR', RS='RS', AR='ARGENTINA', BR='BRASIL',
               note=f'Uso e cobertura do solo: MapBiomas, Coleção {COLL} ({YEAR}). Limites: IBGE (municípios e UF de 2024; América do Sul de 2021).\nMesorregiões: agregação dos municípios. Coordenadas geográficas, SIRGAS 2000.'),
    'en': dict(out='Fig01_study_area_en.png', lon='Longitude (°)', lat='Latitude (°)', legend=f'Land use and land cover, {YEAR}\n(% of the classified state area)',
               sa='South America', ocean='Atlantic Ocean', capital='State capital', city='Municipality (approximate seat)', meso='Mesoregion boundary',
               PR='PR', RS='RS', AR='ARGENTINA', BR='BRAZIL',
               note=f'Land use and land cover: MapBiomas, Collection {COLL} ({YEAR}). Boundaries: IBGE (2024; South America, 2021).\nMesoregions: aggregation of municipalities. Geographic coordinates, SIRGAS 2000.'),
}
CITIES = ['Florianópolis', 'Joinville', 'Blumenau', 'Chapecó', 'Lages', 'Criciúma', 'Caçador', 'São Joaquim']
# Layout revision of 2026-10-16: labels are placed at the first candidate position that touches no boundary line, marker or other label
# (finn_sc.figcheck; the result is checked again after drawing and printed as "LAYOUT ..." on stdout).
# Mesoregion names: preferred anchor (lon, lat) and line breaks; candidates are searched on rings around the anchor.
MESO_LAB = {'Oeste Catarinense': ((-52.55, -26.62), ['Oeste Catarinense']),
            'Norte Catarinense': ((-50.05, -26.42), ['Norte Catarinense', 'Norte\nCatarinense']),
            'Serrana': ((-50.75, -27.62), ['Serrana']),
            'Vale do Itajaí': ((-49.62, -27.18), ['Vale do Itajaí']),
            'Grande Florianópolis': ((-48.93, -27.42), ['Grande\nFlorianópolis']),
            'Sul Catarinense': ((-49.20, -28.42), ['Sul\nCatarinense', 'Sul Catarinense'])}
# city labels: candidate offsets in points (dx, dy, horizontal alignment); the first free one is used
CITY_CAND = [(5, 2, 'left'), (-5, 2, 'right'), (0, 5, 'center'), (0, -11, 'center'), (5, -9, 'left'), (-5, -9, 'right'),
             (7, 7, 'left'), (-7, 7, 'right')]
CITY_FIRST = {'Florianópolis': [(-6, -3, 'right')], 'Joinville': [(-5, 2, 'right')], 'Criciúma': [(-5, 2, 'right')]}
XLIM, YLIM = (-53.95, -48.15), (-29.45, -25.82)
OCEAN, LAND, EDGE = '#dfe9f3', '#ebebeb', '#ffffff'
halo = [pe.withStroke(linewidth=1.6, foreground='white')]


def load():
    z = np.load(EXT / f'mapbiomas_c10_lulc{YEAR}_SC_120m.npz')
    a, inside, t = z['a'], z['inside'], z['transform']
    lut = np.full(256, -1, dtype=int)
    for k, (_, ids, *_r) in enumerate(GROUPS):
        lut[ids] = k
    g = lut[a].astype(float)
    g[(~inside) | (g < 0)] = np.nan          # outside the state, and class 0 (sea inside the IBGE limit), transparent
    extent = (t[2], t[2] + t[0] * a.shape[1], t[5] + t[4] * a.shape[0], t[5])
    areas = pd.read_csv(EXT / f'mapbiomas_c10_lulc{YEAR}_SC_class_areas.csv')
    pct = {key: areas[areas.class_id.isin(ids)].pct_classified.sum() for key, ids, *_r in GROUPS}
    assert abs(sum(pct.values()) - 100) < 0.01, sum(pct.values())
    return g, extent, pct


def main(lang):
    L = TXT[lang]
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 7})
    g, extent, pct = load()
    mun = gpd.read_file(ROOT / 'data' / 'inputs' / 'SC_Municipios_2024.shp', encoding='cp1252').to_crs(4674)
    meso = pd.read_csv(EXT / 'sc_municipios_2024_atributos.csv').set_index('NM_MUN').mesorregiao
    mun['meso'] = mun.NM_MUN.map(meso)
    state = mun.dissolve(); mesog = mun.dissolve(by='meso').reset_index()
    uf = gpd.read_file(EXT / 'ibge_br_uf_2024_simplified.geojson').to_crs(4674)
    sa = gpd.read_file(EXT / 'ibge_america_do_sul_2021_simplified.geojson').to_crs(4674)
    sc = state.geometry.iloc[0]

    fig = plt.figure(figsize=(7.2, 4.25), dpi=400)
    ax = fig.add_axes([0.300, 0.14, 0.690, 0.85])
    ax.set_facecolor(OCEAN)
    sa.plot(ax=ax, color=LAND, edgecolor=EDGE, lw=0.6)
    state.plot(ax=ax, color=OCEAN, lw=0, zorder=1.5)          # bays inside the IBGE limit (no MapBiomas class) appear as water
    uf[uf.SIGLA_UF != 'SC'].plot(ax=ax, color=LAND, edgecolor='#bdbdbd', lw=0.5)
    cmap = ListedColormap([c for _, _, c, *_r in GROUPS])
    ax.imshow(g, extent=extent, cmap=cmap, vmin=-0.5, vmax=len(GROUPS) - 0.5, interpolation='nearest', zorder=2)
    mesog.boundary.plot(ax=ax, color='0.15', lw=0.45, zorder=3)
    state.boundary.plot(ax=ax, color='0.05', lw=0.8, zorder=4)
    pts = mun.set_index('NM_MUN').loc[CITIES].geometry.representative_point()
    for name, p in pts.items():
        cap = name == 'Florianópolis'
        ax.plot(p.x, p.y, marker='*' if cap else 'o', ms=7 if cap else 3.2, mfc='k' if not cap else '#ffd400', mec='k', mew=0.5, zorder=7)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM); ax.set_aspect(1 / math.cos(math.radians(LAT0)))
    deg = FuncFormatter(lambda v, _: (f'{v:g}°').replace('.', ',' if lang == 'pt' else '.').replace('-', '−'))
    ax.xaxis.set_major_formatter(deg); ax.yaxis.set_major_formatter(deg)
    ax.set_xticks(np.arange(-53, -48.5, 1)); ax.set_yticks(np.arange(-29, -25.9, 1))
    ax.tick_params(labelsize=6.5, direction='in', top=True, right=True, length=3)
    ax.grid(color='0.55', lw=0.25, ls=':', zorder=1)
    ax.set_xlabel(L['lon'], fontsize=7, labelpad=2); ax.set_ylabel(L['lat'], fontsize=7, labelpad=2)
    labels = {}
    for lab, (x, y) in ((L['PR'], (-51.3, -25.95)), (L['RS'], (-52.3, -29.25)), (L['AR'], (-53.88, -27.65))):
        labels['region ' + lab] = ax.text(x, y, lab, fontsize=6.5, color='0.45', ha='left', va='center', zorder=5)
    # scale bar over the ocean in the bottom-right corner, with the north rose (finn_sc.cartography) above it (authors'
    # requests of 2026-10-16); the ocean label is placed below, at the free position nearest to its preferred anchor
    lat_sb, x1 = -29.36, -48.40
    dlon = 100 / (111.32 * math.cos(math.radians(lat_sb)))
    x0 = x1 - dlon
    bar = []
    for k in range(4):
        bar.append(ax.add_patch(Rectangle((x0 + k * dlon / 4, lat_sb), dlon / 4, 0.03, facecolor='k' if k % 2 == 0 else 'w',
                                          edgecolor='k', lw=0.4, zorder=8)))
    for k, lab in ((0, '0'), (2, '50'), (4, '100 km')):
        labels[f'scale {lab}'] = ax.annotate(lab, (x0 + k * dlon / 4, lat_sb + 0.03), xytext=(0, 2), textcoords='offset points',
                                             ha='center', va='bottom', fontsize=5.8, zorder=8)
    for name, art in rose_above_bar(ax, x1, lat_sb + 0.03, 5.8, size=14, align='right'):   # right-justified (2026-11-04)
        labels[name] = art
    # inset: South America
    axi = fig.add_axes([0.012, 0.585, 0.255, 0.40])
    axi.set_facecolor(OCEAN)
    sa.plot(ax=axi, color='#d9d9d9', edgecolor='white', lw=0.3)
    uf.plot(ax=axi, color='#bdbdbd', edgecolor='white', lw=0.25)
    uf[uf.SIGLA_UF == 'SC'].plot(ax=axi, color='#c0392b', edgecolor='#c0392b', lw=0.4)
    axi.add_patch(Rectangle((XLIM[0], YLIM[0]), XLIM[1] - XLIM[0], YLIM[1] - YLIM[0], fill=False, edgecolor='k', lw=0.6))
    axi.set_xlim(-82, -34); axi.set_ylim(-56, 13.5); axi.set_aspect(1 / math.cos(math.radians(-20)))
    axi.set_xticks([]); axi.set_yticks([]); axi.set_xlabel(''); axi.set_ylabel('')
    axi.text(0.04, 0.04, L['sa'], transform=axi.transAxes, fontsize=6.3, va='bottom', ha='left')
    axi.text(-52.5, -9.0, L['BR'], fontsize=6, color='0.3', ha='center')
    for s in axi.spines.values():
        s.set_linewidth(0.6)
    # legend with % of the classified state area (long class names on two lines, so the legend stays clear of the map axis)
    axl = fig.add_axes([0.012, 0.05, 0.25, 0.51]); axl.axis('off')
    order = sorted(range(len(GROUPS)), key=lambda k: -pct[GROUPS[k][0]])
    num = (lambda v: f'{v:.1f}'.replace('.', ',')) if lang == 'pt' else (lambda v: f'{v:.1f}')
    wrap = {'Outras formações não florestais': 'Outras formações\nnão florestais', 'Outras áreas não vegetadas': 'Outras áreas\nnão vegetadas',
            'Other non-forest formations': 'Other non-forest\nformations', 'Other non-vegetated areas': 'Other non-vegetated\nareas'}
    handles = []
    for k in order:
        name = GROUPS[k][3] if lang == 'pt' else GROUPS[k][4]
        handles.append(Patch(facecolor=GROUPS[k][2], edgecolor='0.4', lw=0.3, label=f'{wrap.get(name, name)} ({num(pct[GROUPS[k][0]])}%)'))
    from matplotlib.lines import Line2D
    handles += [Line2D([], [], color='0.15', lw=0.6, label=L['meso']),
                Line2D([], [], marker='*', ls='', ms=7, mfc='#ffd400', mec='k', mew=0.5, label=L['capital']),
                Line2D([], [], marker='o', ls='', ms=3.2, mfc='k', mec='k', label=L['city'])]
    leg = axl.legend(handles=handles, loc='upper left', frameon=False, fontsize=6.1, title=L['legend'], title_fontsize=6.5,
                     alignment='left', handlelength=1.6, handleheight=1.0, labelspacing=0.38, borderaxespad=0)
    note = fig.text(0.300, 0.006, L['note'], fontsize=5.6, ha='left', va='bottom', linespacing=1.3)

    # ---- label placement and layout check (display coordinates; finn_sc.figcheck)
    r = figcheck.renderer(fig)
    tr = lambda geom: figcheck.to_display(ax, geom)
    view = box(XLIM[0], YLIM[0], XLIM[1], YLIM[1])
    neigh = shapely.union_all([gm.boundary for gm in uf[uf.SIGLA_UF != 'SC'].geometry] + [gm.boundary for gm in sa.geometry])
    meso_lines = shapely.union_all([gm.boundary for gm in mesog.geometry]).difference(sc.boundary.buffer(0.003))
    feats = {'state boundary': tr(sc.boundary.intersection(view)),
             'mesoregion boundaries': tr(meso_lines.intersection(view)),
             'neighbour boundaries': tr(neigh.intersection(view).difference(sc.buffer(0.03))),
             'land': tr(shapely.union_all(list(sa.geometry)).intersection(view)),
             'Santa Catarina': tr(sc),
             'city markers': figcheck.points_display(ax, [(p.x, p.y) for p in pts], 4.0 * fig.dpi / 72)}
    frames = {'map': figcheck.bbox(ax, r, pad=-2), 'figure': box(0, 0, fig.bbox.width, fig.bbox.height)}
    inner = ['state boundary', 'mesoregion boundaries', 'city markers', 'neighbour boundaries']
    placed = [figcheck.bbox(a_, r, pad=1.5) for a_ in labels.values()] + [figcheck.bbox(b_, r, pad=1.5) for b_ in bar]
    # ocean label: over the Atlantic, clear of the land, the scale bar and the north arrow
    oc = [(tx, x, y) for tx in (L['ocean'], L['ocean'].replace(' ', '\n', 1))
          for y in np.arange(-29.22, -28.20, 0.02) for x in np.arange(-49.30, -48.40, 0.02)]
    oc.sort(key=lambda c: (len(c[0].splitlines()), (c[1] + 48.75) ** 2 + (c[2] + 29.05) ** 2))
    make = lambda c: ax.text(c[1], c[2], c[0], fontsize=6.5, style='italic', color='#3a6a96', ha='center', va='center',
                             zorder=5, linespacing=1.05)
    art, gbox, i = figcheck.place_first_free(make, oc, r, [feats['land']], placed, frames['map'])
    labels['ocean'] = art; placed.append(gbox)
    for name, p in pts.items():
        cands = CITY_FIRST.get(name, []) + CITY_CAND
        make = lambda c, p=p, name=name: ax.annotate(name, (p.x, p.y), xytext=c[:2], textcoords='offset points', fontsize=6.3,
                                                     ha=c[2], va='bottom' if c[1] >= 0 else 'top', zorder=7, path_effects=halo)
        art, gbox, i = figcheck.place_first_free(make, cands, r, [feats[f] for f in inner], placed, frames['map'])
        labels['city ' + name] = art; placed.append(gbox)
    for name, ((lx, ly), texts) in MESO_LAB.items():
        cands = [(tx, lx + dx * 1.13, ly + dy) for tx in texts for dx, dy in figcheck.ring_offsets([0.04, 0.08, 0.12, 0.16, 0.20])]
        make = lambda c: ax.text(c[1], c[2], c[0], fontsize=6.0, style='italic', color='0.1', ha='center', va='center', zorder=6,
                                 path_effects=halo, linespacing=1.05)
        art, gbox, i = figcheck.place_first_free(make, cands, r, [feats[f] for f in inner], placed, frames['map'])
        labels['meso ' + name] = art; placed.append(gbox)
    lab = {}
    for k, art in labels.items():
        if k.startswith(('meso ', 'city ')):
            lab[k] = (figcheck.bbox(art, r, pad=1.5), inner, 'map')
        elif k == 'ocean' or k.startswith('north'):
            lab[k] = (figcheck.bbox(art, r, pad=1.5), ['land'], 'map')
        else:
            lab[k] = (figcheck.bbox(art, r, pad=1.5), ['Santa Catarina', 'neighbour boundaries'], 'map')
    lab['scale bar'] = (shapely.union_all([figcheck.bbox(b_, r, pad=1.0) for b_ in bar]), ['Santa Catarina', 'neighbour boundaries'], 'map')
    lab['legend'] = (figcheck.bbox(leg, r, pad=1.0), [], 'figure')
    lab['inset'] = (figcheck.bbox(axi, r, pad=1.0), [], 'figure')
    lab['source note'] = (figcheck.bbox(note, r, pad=1.0), [], 'figure')
    lab['y label'] = (figcheck.bbox(ax.yaxis.label, r, pad=1.0), [], 'figure')
    for t_ in ax.get_yticklabels():
        if t_.get_text():
            lab['tick ' + t_.get_text()] = (figcheck.bbox(t_, r, pad=0.5), [], 'figure')
    ignore = [(a, b) for a in lab for b in lab if a.startswith('north') and b.startswith('north')] + \
             [('scale bar', k) for k in lab if k.startswith('scale ')]   # pieces of the rose; bar and its labels
    figcheck.report(f'Figure 1 ({lang})', figcheck.check(lab, feats, frames, ignore_pairs=ignore))
    FIG.mkdir(parents=True, exist_ok=True)
    outname = L['out'] if YEAR == 2023 else L['out'].replace('study_area_', f'study_area_{YEAR}_')   # 2019 kept apart
    fig.savefig(FIG / outname, dpi=400, facecolor='white')
    plt.close(fig)
    print('written', FIG / outname, {GROUPS[k][0]: round(pct[GROUPS[k][0]], 2) for k in order})


def mesoregion_table():
    """Share of each land-cover group by mesoregion (120 m window; pixel areas by latitude) ->
    results/tables/landcover<YEAR>_mesoregion.csv (cited in the manuscript, section 2.1)."""
    from rasterio.features import rasterize
    from affine import Affine
    z = np.load(EXT / f'mapbiomas_c10_lulc{YEAR}_SC_120m.npz')
    a, inside, t = z['a'], z['inside'], Affine(*z['transform'])
    mun = gpd.read_file(ROOT / 'data' / 'inputs' / 'SC_Municipios_2024.shp', encoding='cp1252').to_crs(4326)
    mun['meso'] = mun.NM_MUN.map(pd.read_csv(EXT / 'sc_municipios_2024_atributos.csv').set_index('NM_MUN').mesorregiao)
    mg = mun.dissolve(by='meso').reset_index()
    lab = rasterize([(g, k + 1) for k, g in enumerate(mg.geometry)], out_shape=a.shape, transform=t, fill=0)
    R = 6371007.2
    lat = t.f + (np.arange(a.shape[0]) + 0.5) * t.e
    dl, dp = np.radians(t.a), np.radians(-t.e)
    pa = np.broadcast_to(((R ** 2) * dl * (np.sin(np.radians(lat) + dp / 2) - np.sin(np.radians(lat) - dp / 2)))[:, None], a.shape)
    rows = []
    for key, ids, *_r in GROUPS:
        sel = np.isin(a, ids) & inside & (lab > 0)
        tot = pa[sel].sum()
        for k, name in enumerate(mg.meso):
            cl = inside & (lab == k + 1) & (a > 0)
            rows.append(dict(group=key, mesorregiao=name, km2=round(pa[sel & (lab == k + 1)].sum() / 1e6, 1),
                             pct_of_group=round(100 * pa[sel & (lab == k + 1)].sum() / tot, 2),
                             pct_of_mesoregion=round(100 * pa[sel & (lab == k + 1)].sum() / pa[cl].sum(), 2)))
    out = ROOT / 'results' / 'tables' / f'landcover{YEAR}_mesoregion.csv'
    pd.DataFrame(rows).to_csv(out, index=False)
    print('written', out)


if __name__ == '__main__':
    for lang in (sys.argv[1:] or ['pt', 'en']):
        main(lang)
    mesoregion_table()

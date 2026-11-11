#!/usr/bin/env python3
"""a10 - Figures 2 to 7 of the manuscript (v3.2; = Figures 1 to 6 of the inventory report) and supplementary Figures S1, S2.

File names follow the manuscript numbering: Fig02_annual_series.png (report Figure 1),
Fig03_events_municipal_2025.png (report 2), Fig04_events_mesoregion_2025.png (report 3), Fig05_kde_events_2025.png
(report 4), Fig06_burned_area_municipal_2025.png (report 5), Fig07_emissions_municipal_2025.png (report 6). The log
keeps the labels of the analysis code ("Figure 1" ... "Figure 6" = manuscript Figures 2 ... 7). Figure 1 of the
manuscript (study area) is drawn by tools/study_area_map.py.

Style (review round 5): magma_r palette for Figures 2 to 5, without municipal outlines (state outline; mesoregion
lines in Figures 3 and 4), scale bar with the north rose above it, over the ocean in the bottom-right corner
(authors' request of 2026-10-16; in Figure 6, the bottom-right panel; rose right-justified above the bar and, in
Figure 7, bar and labels 30% larger since 2026-11-04), and source note below the frame; Figure 6 in the authors' original layout (4 x 3 panels, one ColorBrewer ramp per pollutant,
Fisher-Jenks classes, no axes).
Layout (revision of 2026-10-16): labels are placed at the first free candidate position and every figure is checked
with finn_sc.figcheck (no label over another label, a boundary line, a marker or the plotted lines; legends, colour
bars, north rose and scale bar clear of Santa Catarina; every label drawn inside a map inside that map's frame). The result is printed as "LAYOUT ..." on stdout and the number of
problems at the end ("layout problems: 0"); the log in results/logs/ is unchanged by the layout.
Inputs : results/tables (a01-a07) and results/tables/kde_<year>_grid.csv + kde_<year>_bandwidths.csv
         (R/analysis/kde_events.R); data/inputs/SC_Municipios_2024.shp.
Outputs: results/figures/Fig02_*.png ... Fig07_*.png, FigS1_finn_vs_mapbiomas.png, FigS2_climate_events.png;
         results/logs/a10_figures.txt (class limits and counts per class).
English version (v2.5.1, 2026-10-22; manuscript in English): FIG_LANG=en python a10_figures.py writes the same figures
with English text and number format as *_en.png; the log is not written in that mode (the Portuguese run writes it).
"""
import math
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter
from matplotlib.colors import ListedColormap, BoundaryNorm
from pyproj import Transformer
import shapely
from _setup import CFG, TAB, FIG, Log, read_shapefile, municipalities
from finn_sc import figcheck
from finn_sc.cartography import rose_above_bar
import os
EN = os.environ.get('FIG_LANG', 'pt') == 'en'
# FIG_NOTES=0 (manuscript v7.2, 2026-11-08): map figures without the source note below each map; the note's content
# is given in the figure caption. Files get the suffix _nn.
NOTES = os.environ.get('FIG_NOTES', '1') != '0'
if not NOTES:   # speed: geopandas calls canvas.draw_idle() after every layer, which redraws the whole Agg figure each time;
    import matplotlib.backend_bases as _mbb   # savefig and the layout checks draw the figure themselves
    _mbb.FigureCanvasBase.draw_idle = lambda self, *a, **k: None
L_ = lambda pt, en: en if EN else pt     # figure text in Portuguese (default) or English

YEAR = CFG["analysis"]["report_year"]
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8})
log = Log('a10_figures')
num = (lambda v, d=0: (f'{v:,.{d}f}').replace('-', '−')) if EN else \
      (lambda v, d=0: (f'{v:,.{d}f}').replace(',', 'X').replace('.', ',').replace('X', '.').replace('-', '−'))
fmt_deg = FuncFormatter((lambda v, _: (f'{v:g}').replace('-', '−')) if EN else (lambda v, _: (f'{v:g}').replace('.', ',').replace('-', '−')))
LAT0 = -27.6
mun = read_shapefile().to_crs(4674)
meso = municipalities().set_index('NM_MUN').mesorregiao
mun['meso'] = mun.NM_MUN.map(meso)
assert mun.meso.notna().all()
state = mun.dissolve()
mesog = mun.dissolve(by='meso').reset_index()
mesog['AREA_KM2'] = mun.groupby('meso').AREA_KM2.sum().values
SC = state.geometry.iloc[0]
MESO_LINES = shapely.union_all([g.boundary for g in mesog.geometry]).difference(SC.boundary.buffer(0.003))
LAYOUT = []   # layout problems found by finn_sc.figcheck (printed at the end; stdout only, the log is unchanged)

SCALE_X1, SCALE_LAT = -48.25, -29.38   # scale bar in the bottom-right corner, over the Atlantic (authors' request, 2026-10-16)

def scale_bar(ax, x1=SCALE_X1, lat_sb=SCALE_LAT, small=False, rose=None, grow=1.0):
    """100 km scale bar ending at longitude x1 (its right end), at latitude lat_sb, with the north rose
    (finn_sc.cartography) above it, right-justified to the end of the bar (authors' requests of 2026-10-16 and
    2026-11-04). grow enlarges the bar height and its labels (Figure 7: 1.3, authors' request of 2026-11-04); the bar
    keeps representing 100 km."""
    dlon = 100 / (111.32 * math.cos(math.radians(lat_sb)))
    x0 = x1 - dlon
    fs = (5.5 if small else 6.5) * grow
    h = 0.035 * grow
    f = [('scale bar 1', ax.add_patch(Rectangle((x0, lat_sb), dlon / 2, h, facecolor='k', edgecolor='k', lw=0.4))),
         ('scale bar 2', ax.add_patch(Rectangle((x0 + dlon / 2, lat_sb), dlon / 2, h, facecolor='w', edgecolor='k', lw=0.4)))]
    for k, lab in enumerate(['0', '50', '100 km']):
        if small and k == 1: continue
        f.append((f'scale {lab}', ax.annotate(lab, (x0 + k * dlon / 2, lat_sb + h), xytext=(0, 2), textcoords='offset points',
                                              ha='center', va='bottom', fontsize=fs)))
    f += rose_above_bar(ax, x1, lat_sb + h, fs, size=rose or (12 if small else 16), align='right')
    ax._furniture = getattr(ax, '_furniture', []) + f

def base(ax, note, small=False):
    """Map frame: geographic axes, scale bar with the north rose above it over the ocean in the bottom-right corner,
    source note below the frame (outside the map, so it never covers features)."""
    ax.set_xlim(-54, -48); ax.set_ylim(-29.5, -25.8); ax.set_aspect(1 / math.cos(math.radians(LAT0)))
    ax.xaxis.set_major_formatter(fmt_deg); ax.yaxis.set_major_formatter(fmt_deg)
    ax.set_xlabel('Longitude (°)'); ax.set_ylabel('Latitude (°)')
    scale_bar(ax, small=small)
    if note and NOTES:
        ax._note = ax.text(0.0, -0.105 if not small else -0.09, note, transform=ax.transAxes, fontsize=6.3, va='top', ha='left')


def check_map(fig, name, axes, extra=None, outside_ok=(), empty_axes=(), cbars=()):
    """Layout check of a map figure: legend, colour bars, north rose, scale bar, source note and any extra labels must not
    cover Santa Catarina (its area, coast or boundaries), and no two labels may overlap (finn_sc.figcheck).
    extra: dict name -> (artist, axes, list of feature names to avoid[, frame]); a label drawn inside a map must stay inside
    that map's frame ('map <i>', the default; 'figure' for labels allowed outside it); cbars: colour bars (ticks, label)."""
    r = figcheck.renderer(fig)
    lab, feats, frames = {}, {}, {'figure': shapely.geometry.box(0, 0, fig.bbox.width, fig.bbox.height)}
    for i, ax in enumerate(axes):
        tr = lambda g, ax=ax: figcheck.to_display(ax, g)
        feats[f'Santa Catarina {i}'] = tr(SC)
        feats[f'mesoregion boundaries {i}'] = tr(MESO_LINES)
        frames[f'map {i}'] = figcheck.bbox(ax, r, pad=0)
        for k, art in getattr(ax, '_furniture', []):
            lab[f'{k} {i}'] = (figcheck.bbox(art, r, pad=1.0), [] if ax in empty_axes else [f'Santa Catarina {i}'], f'map {i}')
        if ax.get_legend() is not None:
            lab[f'legend {i}'] = (figcheck.bbox(ax.get_legend(), r, pad=1.0), [f'Santa Catarina {i}'], 'figure')
        if getattr(ax, '_note', None) is not None:
            lab[f'note {i}'] = (figcheck.bbox(ax._note, r, pad=1.0), [], 'figure')
        if ax.get_title(loc='left'):
            lab[f'title {i}'] = (figcheck.bbox(ax._left_title, r, pad=1.0), [], 'figure')
    for j, cb in enumerate(cbars):
        bb = cb.ax.get_tightbbox(r)
        lab[f'colour bar {j}'] = (shapely.geometry.box(bb.x0 - 1, bb.y0 - 1, bb.x1 + 1, bb.y1 + 1),
                                  [f'Santa Catarina {i}' for i in range(len(axes))], 'figure')
    for k, (art, ax, avoid, *fr) in (extra or {}).items():
        i = list(axes).index(ax)
        lab[k] = (figcheck.bbox(art, r, pad=1.0), [f'{a} {i}' for a in avoid], fr[0] if fr else f'map {i}')
    ignore = [(a, b) for a in lab for b in lab if a.startswith(('scale', 'north')) and a.split()[0] == b.split()[0]
              and a.split()[-1] == b.split()[-1]] + list(outside_ok)   # pieces of the same element (bar, rose)
    LAYOUT.extend(figcheck.report(name, figcheck.check(lab, feats, frames, ignore_pairs=ignore)))

def outlines(ax, meso_lines=False):
    """State outline only (municipal outlines removed in round 5); mesoregion lines on request."""
    if meso_lines:
        mesog.boundary.plot(ax=ax, color='0.35', lw=0.45)
    state.boundary.plot(ax=ax, color='0.2', lw=0.6)

def classes(values, bins, labels, zero_label='0'):
    """bins: list of upper-exclusive limits starting at a value > 0; value 0 -> class 0."""
    v = np.asarray(values, float); c = np.zeros(len(v), int)
    for i in range(len(bins) - 1):
        c[(v > 0) & (v >= bins[i]) & (v < bins[i + 1])] = i + 1
    c[v >= bins[-1]] = len(bins)
    return c

def palette(n):
    cm = plt.get_cmap('magma_r'); return ['#eeeeee'] + [cm(x) for x in np.linspace(0.10, 0.92, n)]

def choropleth(ax, gdf, col, bins, labels, title, note, legend_title, small=False):
    cls = classes(gdf[col].values, bins, labels)
    cols = palette(len(labels) - 1)
    gdf = gdf.assign(_c=cls)
    for k in range(len(labels)):
        sub = gdf[gdf._c == k]
        if len(sub): sub.plot(ax=ax, color=cols[k], edgecolor=cols[k], lw=0.15)   # fill only, no municipal outline
    outlines(ax)
    counts = [int((cls == k).sum()) for k in range(len(labels))]
    hs = [Patch(facecolor=cols[k], edgecolor='0.5', lw=0.3, label=f'{labels[k]} ({counts[k]})') for k in range(len(labels))]
    ax.legend(handles=hs, title=legend_title, loc='lower left', fontsize=5.0 if small else 6.3, title_fontsize=5.4 if small else 6.8,
              frameon=False, bbox_to_anchor=(0.0, 0.02), handlelength=1.4, labelspacing=0.25 if small else 0.4)
    if title: ax.set_title(title, loc='left', fontsize=9)
    base(ax, note, small)
    log(f'{col}: classes {labels} counts {counts}')
    return counts

def check_chart(fig, name, items, lines=None):
    """Layout check of a chart: the given artists (titles, legends, labels, text boxes, markers as Point geometries)
    must not overlap each other, and legends and text boxes must not cover the plotted lines (finn_sc.figcheck)."""
    r = figcheck.renderer(fig)
    lab = {}
    for k, (art, avoid) in items.items():
        g = art if isinstance(art, shapely.Geometry) else figcheck.bbox(art, r, pad=1.0)
        lab[k] = (g, avoid, 'figure')
    feats = dict(lines or {})
    frames = {'figure': shapely.geometry.box(0, 0, fig.bbox.width, fig.bbox.height)}
    ignore = [(a, b) for a in lab for b in lab if a.startswith('marker') and b.startswith('marker')]
    LAYOUT.extend(figcheck.report(name, figcheck.check(lab, feats, frames, ignore_pairs=ignore)))


NOTE_EV = L_(f'FINN v2.5.1 MODIS+VIIRS, {YEAR}; eventos de queimada (polígonos diários de área queimada), excluídas anomalias térmicas persistentes\nMalha municipal IBGE 2024; coordenadas geográficas, SIRGAS 2000',
             f'FINN v2.5.1 MODIS+VIIRS, {YEAR}; fire events (daily burned-area polygons), persistent thermal anomalies excluded\nIBGE 2024 municipal mesh; geographic coordinates, SIRGAS 2000')
NOTE_EM = L_(f'FINN v2.5.1 MODIS+VIIRS, {YEAR}; registros atribuídos ao município por sobreposição (ponto em polígono)\nMalha municipal IBGE 2024; coordenadas geográficas, SIRGAS 2000',
             f'FINN v2.5.1 MODIS+VIIRS, {YEAR}; records assigned to municipalities by point in polygon\nIBGE 2024 municipal mesh; geographic coordinates, SIRGAS 2000')

def out(name):
    name = name if NOTES else name.replace('.png', '_nn.png')
    return name.replace('.png', '_en.png') if EN else name

def save(fig, name):
    fig.savefig(FIG / out(name), bbox_inches='tight', pad_inches=0.08); plt.close(fig)

# ---------------- Figure 2: events per municipality, 2025
ev = pd.read_csv(TAB / 'municipal_events_by_year.csv'); ev25 = ev[ev.year == YEAR].set_index('mun_event').events
g2 = mun.assign(events=mun.NM_MUN.map(ev25).fillna(0))
assert int(g2.events.sum()) == int(ev25.sum()), g2.events.sum()
fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
choropleth(ax, g2, 'events', [1, 10, 25, 50, 100, 200], ['0', '1–9', '10–24', '25–49', '50–99', '100–199', '≥ 200'], None, NOTE_EV,
           L_('Eventos de queimada\n(n.º de municípios)', 'Fire events\n(no. of municipalities)'))
fig.tight_layout(); check_map(fig, 'Figure 3 (events per municipality)', [ax]); save(fig, 'Fig03_events_municipal_2025.png')

# ---------------- Figure 3: mesoregions, 2025
em = g2.groupby('meso').events.sum()
mesog['events'] = mesog.meso.map(em); mesog['dens'] = mesog.events / mesog.AREA_KM2 * 100
log('Figure 3 mesoregions:', mesog[['meso', 'events', 'dens']].round(2).values.tolist())
fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
bnds = [0, 2, 3, 4, 6, 8, 12]; cm = ListedColormap(palette(len(bnds) - 1)[1:]); norm = BoundaryNorm(bnds, cm.N)
mesog.plot(ax=ax, column='dens', cmap=cm, norm=norm, edgecolor='0.25', lw=0.5)
state.boundary.plot(ax=ax, color='0.2', lw=0.6)
sm = plt.cm.ScalarMappable(cmap=cm, norm=norm); cb = fig.colorbar(sm, ax=ax, shrink=0.85, format=FuncFormatter(lambda v, _: num(v)))
cb.set_label(L_('Eventos de queimada por 100 km²', 'Fire events per 100 km²'))
# labels (layout revision of 2026-10-16): each label is placed inside its mesoregion at the first candidate position
# (rings around the preferred anchor) that touches no boundary line, no other label and no map furniture; when the
# mesoregion is too narrow for the three lines, the label goes to the free area over the ocean, with a leader line to
# the centre of the largest circle inscribed in the mesoregion (finn_sc.figcheck).
lab_pos = {'Oeste Catarinense': (-52.55, -26.85), 'Serrana': (-50.45, -27.95), 'Norte Catarinense': (-50.05, -26.42),
           'Vale do Itajaí': (-49.62, -27.15), 'Grande Florianópolis': (-48.91, -27.59), 'Sul Catarinense': (-49.25, -28.55)}
base(ax, NOTE_EV)
fig.tight_layout()
r = figcheck.renderer(fig)
tr = lambda g: figcheck.to_display(ax, g)
lines = tr(shapely.union_all([SC.boundary, MESO_LINES]))
furn = [figcheck.bbox(a_, r, pad=2) for _, a_ in ax._furniture]
frame = figcheck.bbox(ax, r, pad=-3)
cosl = math.cos(math.radians(LAT0))
placed, extra = list(furn), {}
for rr in mesog.sort_values('AREA_KM2', ascending=False).itertuples():
    nm2 = rr.meso.replace('Grande ', 'Grande\n').replace('Sul ', 'Sul\n').replace('Norte ', 'Norte\n')
    ev_w, per_w = L_('eventos', 'events'), L_('por', 'per')
    txts = [f'{rr.meso}\n{num(rr.events)} {ev_w}\n{num(rr.dens, 1)} {per_w} 100 km²']
    if nm2 != rr.meso:
        txts.append(f'{nm2}\n{num(rr.events)} {ev_w}\n{num(rr.dens, 1)} {per_w} 100 km²')
    col = 'white' if rr.dens >= 8 else 'black'
    x0, y0 = lab_pos[rr.meso]
    cands = [(tx, x0 + dx / cosl, y0 + dy) for tx in txts for dx, dy in figcheck.ring_offsets([0.05, 0.10, 0.15, 0.20, 0.25, 0.30])]
    make = lambda c: ax.text(c[1], c[2], c[0], ha='center', va='center', fontsize=6.3, color=col, linespacing=1.15)
    art, gbox, i = figcheck.place_first_free(make, cands, r, [lines], placed, frame, pad=4)
    outside = i is None
    if outside:                                      # over the ocean, with a leader line to the inscribed-circle centre
        art.remove()
        geom_iso = shapely.affinity.scale(rr.geometry, xfact=cosl, yfact=1, origin=(0, 0))
        cx, cy = shapely.get_coordinates(shapely.maximum_inscribed_circle(geom_iso, tolerance=0.001))[0]
        anchor = (cx / cosl, cy)
        out = [(txts[0], x, y) for y in np.arange(-29.25, -26.6, 0.05) for x in np.arange(-48.95, -48.15, 0.05)]
        out.sort(key=lambda c: (c[1] - anchor[0]) ** 2 * cosl ** 2 + (c[2] - anchor[1]) ** 2)
        make = lambda c, anchor=anchor: ax.annotate(c[0], anchor, xytext=(c[1], c[2]), textcoords='data', ha='center', va='center',
                                                    fontsize=6.3, color='black', linespacing=1.15,
                                                    arrowprops=dict(arrowstyle='-', lw=0.6, color='0.15', shrinkA=3, shrinkB=0))
        art, gbox, i = figcheck.place_first_free(make, out, r, [tr(SC.buffer(0.02))], placed, frame)
        ax.plot(*anchor, marker='o', ms=1.8, color='0.15')
        gbox = figcheck.bbox(art, r, pad=1.5)
    placed.append(gbox)
    extra[f'label {rr.meso}'] = (art, ax, ['Santa Catarina'] if outside else ['mesoregion boundaries'])
check_map(fig, 'Figure 4 (mesoregions)', [ax], extra, cbars=[cb])
save(fig, 'Fig04_events_mesoregion_2025.png')

# ---------------- Figure 4: kernel density (grid from R/analysis/kde_events.R)
G = pd.read_csv(TAB / f'kde_{YEAR}_grid.csv')
xs = np.sort(G.x.unique()); ys = np.sort(G.y.unique())
dx = np.median(np.diff(xs)); dy = np.median(np.diff(ys))
xf = np.arange(xs.min() - dx, xs.max() + 2 * dx, dx); yf = np.arange(ys.min() - dy, ys.max() + 2 * dy, dy)
Z = np.full((len(yf), len(xf)), np.nan)
ix = np.rint((G.x.values - xf[0]) / dx).astype(int); iy = np.rint((G.y.values - yf[0]) / dy).astype(int)
Z[iy, ix] = G.ev_100km2.values
XX, YY = np.meshgrid(xf, yf)
LON, LAT = Transformer.from_crs(31982, 4674, always_xy=True).transform(XX, YY)
bw = pd.read_csv(TAB / f'kde_{YEAR}_bandwidths.csv').set_index('selector').sigma_m
fig, ax = plt.subplots(figsize=(8.6, 5.6), dpi=200)
levels = [0, 1, 2, 4, 8, 16, 32, 64]
cs = ax.contourf(LON, LAT, Z, levels=levels, cmap='magma_r')
outlines(ax, meso_lines=True)
cb = fig.colorbar(cs, ax=ax, shrink=0.85, format=FuncFormatter(lambda v, _: num(v)))
cb.set_label(L_('Densidade de eventos de queimada (eventos por 100 km²)', 'Fire event density (events per 100 km²)'))
ax.plot([-49.442], [-28.586], marker='x', color='tab:blue', ms=5, mew=1.2)
base(ax, L_(f'FINN v2.5.1 MODIS+VIIRS, {YEAR} (n = {num(int(ev25.sum()))} eventos de queimada); núcleo gaussiano, σ = {num(bw["ppl"] / 1000, 1)} km; '
            f'correção de borda de Jones-Diggle\ndensidade calculada em SIRGAS 2000 / UTM 22S; linhas: limites estadual e das mesorregiões (IBGE)',
            f'FINN v2.5.1 MODIS+VIIRS, {YEAR} (n = {num(int(ev25.sum()))} fire events); Gaussian kernel, σ = {num(bw["ppl"] / 1000, 1)} km; '
            f'Jones-Diggle edge correction\ndensity computed in SIRGAS 2000 / UTM 22S; lines: State and mesoregion boundaries (IBGE)'))
fig.tight_layout()
# label of the excluded anomaly: over the ocean, inside the map frame, at the free position closest to the anomaly
# (clear of the State, of the scale bar and of the north rose; layout revision of 2026-10-16, finn_sc.figcheck)
r = figcheck.renderer(fig)
cosl = math.cos(math.radians(LAT0))
anom = (-49.442, -28.586)
cands = [(tx, x, y) for tx in L_(('anomalia térmica persistente\n(excluída; Siderópolis)', 'anomalia térmica\npersistente (excluída;\nSiderópolis)',
                                  'anomalia\ntérmica persistente\n(excluída;\nSiderópolis)',
                                  'Siderópolis\n(anomalia\nexcluída)'),   # short form; the caption names the anomaly in full
                                 ('persistent thermal anomaly\n(excluded; Siderópolis)', 'persistent thermal\nanomaly (excluded;\nSiderópolis)',
                                  'persistent\nthermal anomaly\n(excluded;\nSiderópolis)', 'Siderópolis\n(anomaly\nexcluded)'))
         for y in np.arange(-29.35, -27.55, 0.05) for x in np.arange(-49.60, -48.10, 0.05)]
# nearest free position to the anomaly; each extra line of text counts as 0.05 degree of distance
cands.sort(key=lambda c: math.hypot((c[1] - anom[0]) * cosl, c[2] - anom[1]) + 0.05 * (len(c[0].splitlines()) - 2))
make = lambda c: ax.annotate(c[0], anom, xytext=c[1:], textcoords='data', fontsize=6.3,
                             color='tab:blue', ha='left', va='center',
                             arrowprops=dict(arrowstyle='-', color='tab:blue', lw=0.6, shrinkA=2, shrinkB=4))
art, gbox, i = figcheck.place_first_free(make, cands, r, [figcheck.to_display(ax, SC.buffer(0.03))],
                                         [figcheck.bbox(a_, r, pad=2) for _, a_ in ax._furniture], figcheck.bbox(ax, r, pad=-3))
check_map(fig, 'Figure 5 (kernel density)', [ax], {'anomaly label': (art, ax, ['Santa Catarina'])}, cbars=[cb])
save(fig, 'Fig05_kde_events_2025.png')
log('Figure 4: max density', round(np.nanmax(Z), 2), '| sigma ppl (m)', round(bw['ppl']))

# ---------------- Figure 5: FINN area per municipality (km2 and % of municipal area)
mt = pd.read_csv(TAB / f'municipal_{YEAR}.csv').set_index('municipio')
g5 = mun.assign(area_finn=mun.NM_MUN.map(mt.area_km2).fillna(0))
g5['pct'] = g5.area_finn / g5.AREA_KM2 * 100
log('Figure 5: state area', round(g5.area_finn.sum(), 2), '| max pct', g5.sort_values('pct').NM_MUN.iloc[-1], round(g5.pct.max(), 2))
fig, axs = plt.subplots(2, 1, figsize=(8.6, 11.2), dpi=200)
a_ = L_('a', 'to')
choropleth(axs[0], g5, 'area_finn', [0.000001, 1, 5, 10, 25, 50, 100], ['0', '< 1', f'1 {a_} < 5', f'5 {a_} < 10', f'10 {a_} < 25', f'25 {a_} < 50', f'50 {a_} < 100', '≥ 100'],
           L_('a) Área estimada pelo FINN (km²)', 'a) FINN burned area (km²)'), NOTE_EM, L_('km² (n.º de municípios)', 'km² (no. of municipalities)'))
choropleth(axs[1], g5, 'pct', [0.000001, 0.5, 1, 2, 4, 8], L_(['0', '< 0,5', '0,5 a < 1', '1 a < 2', '2 a < 4', '4 a < 8', '≥ 8'],
                                                              ['0', '< 0.5', '0.5 to < 1', '1 to < 2', '2 to < 4', '4 to < 8', '≥ 8']),
           L_('b) Área estimada pelo FINN em relação à área do município (%)', 'b) FINN burned area relative to the municipal area (%)'), NOTE_EM,
           L_('% (n.º de municípios)', '% (no. of municipalities)'))
fig.tight_layout(h_pad=3.0); check_map(fig, 'Figure 6 (burned area)', list(axs)); save(fig, 'Fig06_burned_area_municipal_2025.png')

# ---------------- Figure 6: emissions per municipality (10 pollutants), in the authors' original layout
# (round 5: 4 x 3 panels, one ColorBrewer ramp per pollutant as in the first version of the figure,
#  five classes by Fisher-Jenks natural breaks of the municipalities with emissions, each class including its upper limit;
#  no axes and no municipal outlines; municipalities without FINN records left white)
import mapclassify
RAMPS = {  # colours sampled from the legend swatches of the authors' original Figure 6
    'CO2': ['#fff5f0', '#fcbea5', '#fb7050', '#d32020', '#67000d'], 'CO': ['#fff5eb', '#fdd2a5', '#fd9243', '#df5005', '#7f2704'],
    'NOXasNO': ['#feebe2', '#fbb4b9', '#f768a1', '#c51b8a', '#7a0177'], 'SO2': ['#ffffb2', '#fecc5c', '#fd8d3c', '#f03b20', '#bd0026'],
    'PM25': ['#fafafa', '#bdbdbd', '#808080', '#424242', '#050505'], 'NH3': ['#f1eef6', '#d7b5d8', '#df65b0', '#dd1c77', '#980043'],
    'CH4': ['#f6eff7', '#bdc9e1', '#67a9cf', '#1c9099', '#016c59'], 'NMOC': ['#ffc77f', '#ec955f', '#9d633f', '#674029', '#000000'],
    'OC': ['#ffffff', '#e9e9b5', '#d0ab93', '#9e6666', '#1d0000'], 'BC': ['#fafafa', '#bdbdbd', '#808080', '#424242', '#050505']}
pol = [('CO2', 'CO₂'), ('CO', 'CO'), ('NOXasNO', 'NOₓ'), ('SO2', 'SO₂'), ('PM25', L_('MP₂,₅', 'PM₂.₅')), ('NH3', 'NH₃'),
       ('CH4', 'CH₄'), ('NMOC', L_('COV', 'NMOC')), ('OC', 'OC'), ('BC', 'BC')]
SEP_ = ',' if EN else '.'                      # thousands separator removed from the class limits
def lab6(x, first=False):
    if first:
        return '0' if x < 0.5 else num(x, 0).replace(SEP_, '')
    return num(x, 1) if x < 10 else num(x, 0).replace(SEP_, '')
fig, axs = plt.subplots(4, 3, figsize=(8.6, 8.9), dpi=200)
for ax in axs.ravel():
    ax.set_xlim(-54, -48); ax.set_ylim(-29.5, -25.8); ax.set_aspect(1 / math.cos(math.radians(LAT0))); ax.axis('off')
for ax, (col, lab) in zip(axs.ravel(), pol):
    v = mun.NM_MUN.map(mt[col]).fillna(0).values
    pos = v[v > 0]
    fj = mapclassify.FisherJenks(pos, k=5)
    ub = list(fj.bins)
    cls = np.full(len(v), -1)
    cls[v > 0] = np.searchsorted(ub, v[v > 0], side='left')   # class i holds (ub[i-1], ub[i]]
    gdf = mun.assign(_c=cls)
    for k in range(5):
        sub = gdf[gdf._c == k]
        if len(sub): sub.plot(ax=ax, color=RAMPS[col][k], edgecolor=RAMPS[col][k], lw=0.15)
    z = gdf[gdf._c < 0]
    if len(z):
        with plt.rc_context({'hatch.linewidth': 0.3}): z.plot(ax=ax, facecolor='white', edgecolor='0.55', hatch='////', lw=0)
    state.boundary.plot(ax=ax, color='0.1', lw=0.8)
    lows = [pos.min()] + ub[:-1]
    hs = [Patch(facecolor=RAMPS[col][k], edgecolor='0.45', lw=0.4, label=f'{lab6(lows[k], first=(k == 0))} - {lab6(ub[k])}') for k in range(5)]
    ax.legend(handles=hs, title=f'{lab} ({L_("t ano⁻¹", "t yr⁻¹")})', loc='lower left', bbox_to_anchor=(-0.02, -0.04), frameon=False, fontsize=6.2,
              title_fontsize=8.5, handlelength=1.6, handleheight=0.9, labelspacing=0.28, alignment='left')
    log(f'Figure 6 {col}: Fisher-Jenks upper limits {[round(float(b), 2) for b in ub]}; counts {[int((cls == k).sum()) for k in range(5)]}; zero {int((cls < 0).sum())}')
# cartographic elements and source in the free slots of the last row (same extent and aspect as the maps)
scale_bar(axs[3, 2], x1=-48.45, small=True, rose=16, grow=1.3)   # bottom-right panel, below the note (same extent and aspect as the maps); bar and labels 30% larger (2026-11-04)
note7 = None if not NOTES else axs[3, 2].text(-54.0, -26.4, L_(f'FINN v2.5.1 MODIS+VIIRS, {YEAR}\nNOₓ expresso como massa de NO;\nCOV: campo NMOC\nClasses: quebras naturais (Fisher-Jenks);\ncada classe inclui o limite superior\nHachurado: municípios sem registros\nMalha municipal IBGE 2024; SIRGAS 2000',
                                       f'FINN v2.5.1 MODIS+VIIRS, {YEAR}\nNOₓ expressed as mass of NO;\nNMOC: field NMOC\nClasses: natural breaks (Fisher-Jenks);\neach class includes its upper limit\nHatched: municipalities without records\nIBGE 2024 municipal mesh; SIRGAS 2000'),
               fontsize=6.4, va='top', ha='left')
fig.tight_layout(w_pad=0.2, h_pad=0.2)
check_map(fig, 'Figure 7 (emissions)', list(axs.ravel()), {'note': (note7, axs[3, 2], [], 'figure')} if NOTES else None, empty_axes=(axs[3, 1], axs[3, 2]))
save(fig, 'Fig07_emissions_municipal_2025.png')

# ---------------- Figure 1: annual series (events after screening; area and emissions from all records)
S = pd.read_csv(TAB / 'series_state_all_products.csv')
S = S[~((S.sensor == 'MODIS') & (S.version == 'v2.5.1'))]
groups = [('MODIS', 'v2.5', 'FINN v2.5 MODIS', '#9ecae1'), ('MODIS+VIIRS', 'v2.5', 'FINN v2.5 MODIS+VIIRS', '#08519c'),
          ('MODIS+VIIRS', 'v2.5.1', 'FINN v2.5.1 MODIS+VIIRS', '#e6550d')]
panels = L_([('events', 'a) Eventos de queimada', 1), ('area_km2', 'b) Área queimada estimada pelo FINN (km²)', 1), ('CO', 'c) CO (mil t ano⁻¹)', 1e3),
             ('CO2', 'd) CO₂ (milhões de t ano⁻¹)', 1e6), ('PM25', 'e) MP₂,₅ (mil t ano⁻¹)', 1e3)],
            [('events', 'a) Fire events', 1), ('area_km2', 'b) FINN burned area (km²)', 1), ('CO', 'c) CO (kt yr⁻¹)', 1e3),
             ('CO2', 'd) CO₂ (Mt yr⁻¹)', 1e6), ('PM25', 'e) PM₂.₅ (kt yr⁻¹)', 1e3)])
fmt = FuncFormatter(lambda v, _: num(v) if v >= 100 else ((f'{v:g}') if EN else (f'{v:g}').replace('.', ',')))
years = np.arange(2003, 2026)
fig, axes = plt.subplots(5, 1, figsize=(8.2, 11), dpi=200, sharex=True)
w = 0.4
for ax, (col, title, sc) in zip(axes, panels):
    for sen, ver, lab, colr in groups:
        d = S[(S.sensor == sen) & (S.version == ver)].set_index('year')[col] / sc
        off = -w / 2 if (sen == 'MODIS') else (w / 2 if ver == 'v2.5' else 0)
        ax.bar(d.index + off, d.values, width=w if ver == 'v2.5' else 0.6, color=colr, label=lab, edgecolor='none')
    ax.set_title(title, loc='left', fontsize=10)
    ax.yaxis.set_major_formatter(fmt); ax.grid(axis='y', color='0.9', lw=0.6); ax.set_axisbelow(True)
    for s_ in ('top', 'right'): ax.spines[s_].set_visible(False)
h, l = axes[0].get_legend_handles_labels(); fig.legend(h, l, frameon=False, fontsize=8.5, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.0))
axes[-1].set_xticks(years); axes[-1].set_xticklabels(years, rotation=90, fontsize=8)
fig.tight_layout(rect=(0, 0, 1, 0.975))
items = {'legend': (fig.legends[0], [])}
for i, ax in enumerate(axes):
    items[f'title {i}'] = (ax._left_title, [])
    lo, hi = ax.get_ylim()
    for tl in ax.get_yticklabels():                  # only the tick labels that are drawn (inside the axis limits)
        if tl.get_text() and lo <= tl.get_position()[1] <= hi:
            items[f'ytick {i} {tl.get_text()}'] = (tl, [])
for tl in axes[-1].get_xticklabels():
    items[f'xtick {tl.get_text()}'] = (tl, [])
check_chart(fig, 'Figure 2 (annual series)', items)
fig.savefig(FIG / out('Fig02_annual_series.png')); plt.close(fig)
log('Figure 1 events (MV):', S[S.sensor == 'MODIS+VIIRS'].set_index('year').events.to_dict())

# ---------------- Figure S1: FINN vs MapBiomas Fogo (Collection 4), state series 2012-2024
from scipy import stats
br = lambda x, d=0: num(x, d)
ORANGE, BLUE, INK, MUTED = '#eb6834', '#2a78d6', '#0b0b0b', '#52514e'
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ae', 'axes.labelcolor': INK, 'xtick.color': MUTED, 'ytick.color': MUTED})
C4 = pd.read_csv(TAB / 'mapbiomas_state.csv', index_col=0)
pr, sr = stats.pearsonr(C4.finn, C4.mb), stats.spearmanr(C4.finn, C4.mb)
c2 = C4.drop(index=2012); pr2, sr2 = stats.pearsonr(c2.finn, c2.mb), stats.spearmanr(c2.finn, c2.mb)
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=200, gridspec_kw={'width_ratios': [1.35, 1]})
yrs = C4.index.values
fi = C4.finn / C4.finn.mean() * 100; mi = C4.mb / C4.mb.mean() * 100
a1.axhline(100, color='#d9d8d2', lw=0.8, zorder=0)
a1.plot(yrs, fi, '-o', color=ORANGE, lw=2, ms=5, label=L_('FINN (soma das áreas diárias)', 'FINN (sum of daily areas)'), zorder=3)
a1.plot(yrs, mi, '-o', color=BLUE, lw=2, ms=5, label=L_('MapBiomas Fogo, Coleção 4', 'MapBiomas Fire, Collection 4'), zorder=3)
a1.text(yrs[-1] + 0.25, fi.iloc[-1], 'FINN', color=INK, va='center', fontsize=8)
a1.text(yrs[-1] + 0.25, mi.iloc[-1], 'MapBiomas', color=INK, va='center', fontsize=8)
a1.set_xlim(2011.5, 2025.6); a1.set_xticks(yrs[::2])
a1.set_ylabel(L_('Área anual (% da média 2012-2024)', 'Annual area (% of the 2012-2024 mean)')); a1.set_title(L_('a) Variação interanual', 'a) Interannual variation'), loc='left', fontsize=9.5, color=INK)
a1.legend(frameon=False, fontsize=7.5, loc='upper right'); a1.grid(axis='y', color='#ecebe6', lw=0.6)
a2.scatter(C4.mb, C4.finn, s=34, color=ORANGE, edgecolor='white', linewidth=1.2, zorder=3)
a2.set_xlabel(L_('MapBiomas, Coleção 4 (km²)', 'MapBiomas, Collection 4 (km²)')); a2.set_ylabel('FINN (km²)')
a2.set_title(L_('b) Área anual: FINN × MapBiomas', 'b) Annual area: FINN × MapBiomas'), loc='left', fontsize=9.5, color=INK)
fmt2 = FuncFormatter(lambda v, _: br(v))
a2.xaxis.set_major_formatter(fmt2); a2.yaxis.set_major_formatter(fmt2); a2.grid(color='#ecebe6', lw=0.6)
stats_b = a2.text(0.97, 0.04, f"r = {br(pr[0], 2)}; ρ = {br(sr[0], 2)} (n = {len(C4)})\n{L_('sem 2012', 'without 2012')}: r = {br(pr2[0], 2)}; ρ = {br(sr2[0], 2)}\n"
                   f"{L_('razão mediana FINN/MapBiomas', 'median FINN/MapBiomas ratio')} = {br(C4.ratio.median(), 1)}", transform=a2.transAxes, ha='right', va='bottom',
                   fontsize=7.5, color=INK)
for ax in (a1, a2):
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
fig.tight_layout()
# year labels (layout revision of 2026-10-16): first free position around each point (finn_sc.figcheck);
# the years discussed in the text are labelled
r = figcheck.renderer(fig)
MK = (math.sqrt(34) / 2 + 0.6) * fig.dpi / 72   # marker radius (s = 34 pt², white edge 1.2 pt)
sel = (2012, 2015, 2016, 2019, 2020, 2023, 2024)
arts, boxes, discs, failed = figcheck.place_point_labels(a2, r, list(zip(C4.mb, C4.finn)), [str(y) if y in sel else None for y in yrs],
                                                 avoid_boxes=[figcheck.bbox(stats_b, r, pad=2)], marker_px=MK, fontsize=7, color=MUTED)
items = {'stats b': (stats_b, []), 'legend a': (a1.get_legend(), ['lines a']), 'title a': (a1._left_title, []), 'title b': (a2._left_title, []),
         'end FINN': (a1.texts[0], []), 'end MapBiomas': (a1.texts[1], [])}
items.update({f'year {k}': (g, []) for k, g in enumerate(boxes)})
items.update({f'marker {k}': (d, []) for k, d in enumerate(discs)})
LAYOUT.extend(figcheck.report('Figure S1 point labels', failed) if failed else [])
lines_a = shapely.union_all([shapely.LineString(a1.transData.transform(np.column_stack([yrs, v]))) for v in (fi.values, mi.values)])
check_chart(fig, 'Figure S1', items, {'lines a': lines_a})
fig.savefig(FIG / out('FigS1_finn_vs_mapbiomas.png')); plt.close(fig)

# ---------------- Figure S2: screened events vs fire-season precipitation and ONI
from _setup import path
D = pd.read_csv(path('climate')).set_index('year')
y0, y1 = CFG['analysis']['series_years']; D = D.loc[y0:y1]
CR = pd.read_csv(TAB / 'climate_correlations.csv')
evs = S[S.sensor == 'MODIS+VIIRS'].set_index('year').events
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#b5b4ae', 'xtick.color': MUTED, 'ytick.color': MUTED})
fig, axs = plt.subplots(1, 2, figsize=(9.2, 3.8), dpi=200)
x1 = D.precip_mm_fs; x2 = D.ONI_fs; yv = evs.loc[D.index]
stats = {}
for ax, x, xl, col, key in ((axs[0], x1, L_('Precipitação de julho a novembro (mm)', 'July-November precipitation (mm)'), BLUE, 'precip_mm_fs'),
                            (axs[1], x2, L_('ONI médio (JAS, ASO e SON)', 'Mean ONI (JAS, ASO and SON)'), ORANGE, 'ONI_fs')):
    ax.scatter(x, yv, s=34, color=col, edgecolor='white', linewidth=1.2, zorder=3)
    c = CR[(CR.resposta == 'eventos') & (CR.preditor == key)].iloc[0]
    # without the El Niño years 2015 and 2023 (co-authors' review of 2026-10-19)
    from scipy.stats import spearmanr
    keep = [y for y in D.index if y not in (2015, 2023)]
    r12, p12 = spearmanr(yv.loc[keep], x.loc[keep])
    stats[ax] = ax.text(0.97, 0.97, f'ρ = {br(c.rho, 2)}; p = {br(c.p, 3)}\np (Holm) = {br(c.p_holm, 3)}\n{L_("primeiras diferenças", "first differences")}: ρ = {br(c.rho_dif, 2)}'
                        f'\n{L_("sem 2015 e 2023", "without 2015 and 2023")}: ρ = {br(r12, 2)}; p = {br(p12, 3)}',
            transform=ax.transAxes, ha='right', va='top', fontsize=7.5, color=INK)
    ax.set_xlabel(xl); ax.set_ylabel(L_('Eventos de queimada (n)', 'Fire events (n)'))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v))); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: br(v, 1 if abs(v) < 10 else 0)))
    ax.grid(color='#ecebe6', lw=0.6)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
axs[0].set_title(L_('a) Precipitação da estação de queimadas', 'a) Fire-season precipitation'), loc='left', fontsize=9.5)
axs[1].set_title(L_('b) El Niño-Oscilação Sul', 'b) El Niño-Southern Oscillation'), loc='left', fontsize=9.5)
fig.tight_layout()
# year labels (layout revision of 2026-10-16): first free position around each point, clear of the other points and
# of the statistics box
r = figcheck.renderer(fig)
MK = (math.sqrt(34) / 2 + 0.6) * fig.dpi / 72   # marker radius (s = 34 pt², white edge 1.2 pt)
items = {}
for j, (ax, x) in enumerate(((axs[0], x1), (axs[1], x2))):
    arts, boxes, discs, failed = figcheck.place_point_labels(ax, r, list(zip(x.values, yv.values)), [str(y) for y in D.index],
                                                     avoid_boxes=[figcheck.bbox(stats[ax], r, pad=2)], marker_px=MK, fontsize=6.8, color=MUTED)
    if failed: LAYOUT.extend(figcheck.report(f'Figure S2 point labels {j}', failed))
    items.update({f'stats {j}': (stats[ax], []), f'title {j}': (ax._left_title, [])})
    items.update({f'year {j} {k}': (g, []) for k, g in enumerate(boxes)})
    items.update({f'marker {j} {k}': (d, []) for k, d in enumerate(discs)})
check_chart(fig, 'Figure S2', items)
fig.savefig(FIG / out('FigS2_climate_events.png')); plt.close(fig)
if not EN and NOTES:   # the manuscript variant without notes (FIG_NOTES=0) writes no log
    log.save()
print('layout problems:', len(LAYOUT))

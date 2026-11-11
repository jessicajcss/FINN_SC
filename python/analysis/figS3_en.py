#!/usr/bin/env python3
"""figS3_en - English version of Figure S3 (annual kernel density maps 2012-2025) for the English manuscript
(v2.5.1, 2026-10-22). Same inputs, layout and colours as block 13 of a11_coauthor_review.py, which draws the Portuguese
figure (results/figures/FigS3_kde_annual.png); this script only translates the text and the number format.
Inputs : results/tables/kde_annual_grid.csv.gz and kde_annual_summary.csv (R/analysis/kde_sensitivity_annual.R)
Output : results/figures/FigS3_kde_annual_en.png (no log; the analysis numbers are logged by a11)
"""
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd
from pyproj import Transformer
import shapely
from _setup import CFG, TAB, FIG, read_shapefile, municipalities
from finn_sc.cartography import rose_above_bar
from finn_sc import figcheck

y0, y1 = CFG["analysis"]["series_years"]
MESO = dict(zip(municipalities().NM_MUN, municipalities().mesorregiao))
num = lambda v, d=0: (f"{v:,.{d}f}").replace("-", "−")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 7})
G = pd.read_csv(TAB / "kde_annual_grid.csv.gz")
BS = pd.read_csv(TAB / "kde_annual_summary.csv")
xs = np.sort(G.x.unique()); ys = np.sort(G.y.unique())
dx = np.median(np.diff(xs)); dy = np.median(np.diff(ys))
xf = np.arange(xs.min() - dx, xs.max() + 2 * dx, dx); yf = np.arange(ys.min() - dy, ys.max() + 2 * dy, dy)
ix = np.rint((G.x.values - xf[0]) / dx).astype(int); iy = np.rint((G.y.values - yf[0]) / dy).astype(int)
XX, YY = np.meshgrid(xf, yf)
LON, LAT = Transformer.from_crs(31982, 4674, always_xy=True).transform(XX, YY)
shp = read_shapefile().to_crs(4674)
shp["meso"] = shp.NM_MUN.map(MESO)
state = shp.dissolve(); mesog = shp.dissolve(by="meso").reset_index()
LAT0 = -27.6
levels = [0, 1, 2, 4, 8, 16, 32, 64]
years = list(range(y0, y1 + 1))
fig, axs = plt.subplots(4, 4, figsize=(9.6, 7.6), dpi=200)
axs = axs.ravel()
cs = None
for k, yv in enumerate(years):
    ax = axs[k]
    Z = np.full((len(yf), len(xf)), np.nan); Z[iy, ix] = G[f"y{yv}"].values
    cs = ax.contourf(LON, LAT, Z, levels=levels, cmap="magma_r", extend="max")
    mesog.boundary.plot(ax=ax, color="0.35", lw=0.3)
    state.boundary.plot(ax=ax, color="0.2", lw=0.45)
    ax.set_xlim(-54, -48); ax.set_ylim(-29.5, -25.8); ax.set_aspect(1 / math.cos(math.radians(LAT0)))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(''); ax.set_ylabel('')
    for sp in ax.spines.values(): sp.set_color("0.6"); sp.set_linewidth(0.5)
    b = BS[(BS.year == yv) & (BS.meso == "Serrana")].iloc[0]
    ax.set_title(f"{yv} (n = {num(int(b.events))})", loc="left", fontsize=7.2, pad=2)
for ax in axs[len(years):]:
    ax.set_axis_off()
cax = fig.add_axes([0.56, 0.135, 0.18, 0.018])
cb = fig.colorbar(cs, cax=cax, orientation="horizontal", format=FuncFormatter(lambda v, _: num(v)))
cb.set_label("Fire events per 100 km²", fontsize=6.8); cb.ax.tick_params(labelsize=6)
axr = axs[15]; axr.set_xlim(-54, -48); axr.set_ylim(-29.5, -25.8); axr.set_aspect(1 / math.cos(math.radians(LAT0)))
lat_sb = -28.9; dlon = 100 / (111.32 * math.cos(math.radians(lat_sb))); x1 = -48.6; x0 = x1 - dlon
axr.add_patch(Rectangle((x0, lat_sb), dlon / 2, 0.06, facecolor="k", edgecolor="k", lw=0.4))
axr.add_patch(Rectangle((x0 + dlon / 2, lat_sb), dlon / 2, 0.06, facecolor="w", edgecolor="k", lw=0.4))
for j, lab in ((0, "0"), (2, "100 km")):
    axr.annotate(lab, (x0 + j * dlon / 2, lat_sb + 0.06), xytext=(0, 2), textcoords="offset points", ha="center", va="bottom", fontsize=5.5)
rose_above_bar(axr, x1, lat_sb + 0.06, 5.5, size=12, align='right')   # right-justified (2026-11-04)
fig.text(0.02, 0.012, f"FINN MODIS+VIIRS (v2.5 until 2021; v2.5.1 from 2022 to 2025); persistent thermal anomalies excluded; Gaussian "
         f"kernel with fixed σ of {num(BS.sigma_fixed_m.iloc[0] / 1000, 1)} km in every year; Jones-Diggle edge correction;\n"
         "density computed in SIRGAS 2000 / UTM 22S; lines: State and mesoregion boundaries (IBGE).", fontsize=6, va="bottom")
fig.subplots_adjust(left=0.01, right=0.99, top=0.97, bottom=0.07, wspace=0.04, hspace=0.16)
r = figcheck.renderer(fig)
lab = {f"title {k}": (figcheck.bbox(axs[k]._left_title, r, pad=1.0), [], "figure") for k in range(len(years))}
bb = cb.ax.get_tightbbox(r)
lab["colour bar"] = (shapely.geometry.box(bb.x0 - 1, bb.y0 - 1, bb.x1 + 1, bb.y1 + 1), [], "figure")
frames = {"figure": shapely.geometry.box(0, 0, fig.bbox.width, fig.bbox.height)}
prob = figcheck.check(lab, {}, frames)
print("Figure S3 (en) layout problems:", len(prob))
fig.savefig(FIG / "FigS3_kde_annual_en.png", facecolor="white")
plt.close(fig)

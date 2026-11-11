#!/usr/bin/env python3
"""figures_est_en - English figures for the Environmental Science & Technology submission (v2.5.1, 2026-10-22).

1. results/figures/Fig02_annual_series_4p_en.png: Figure 2 of the ES&T manuscript. Same data, colours and layout
   as Figure 2 of a10_figures.py (Fig02_annual_series_en.png) without the CO panel, because ES&T asks for figures
   with one to four panels; CO stays in Table 1.
2. results/figures/TOC_graphic_est.png: table-of-contents graphic (3.25 x 1.75 in, 600 dpi). Every value is read
   from a results table of this repository:
     interannual range of CO2, 2012-2025  table2_state_emissions_2012_2025.csv (max / min)
     adding VIIRS (CO2), 2012-2021         viirs_effect.csv (1 + CO2_inc_pct/100, v2.5 rows)
     FINN v1.5 / FINN v2.5, 2020 CO2       inventory_comparison_2020.csv
     FINN area / mapped area, 2012-2024    mapbiomas_state.csv and mcd64a1_comparison_state.csv (ranges; medians)
No log is written: the numbers are logged by the scripts that produce the tables.
"""
import numpy as np, pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from _setup import TAB, FIG

num = lambda v, d=0: (f'{v:,.{d}f}').replace('-', '−')

# ---------------------------------------------------------------- Figure 2, four panels
S = pd.read_csv(TAB / 'series_state_all_products.csv')
S = S[~((S.sensor == 'MODIS') & (S.version == 'v2.5.1'))]
groups = [('MODIS', 'v2.5', 'FINN v2.5 MODIS', '#9ecae1'), ('MODIS+VIIRS', 'v2.5', 'FINN v2.5 MODIS+VIIRS', '#08519c'),
          ('MODIS+VIIRS', 'v2.5.1', 'FINN v2.5.1 MODIS+VIIRS', '#e6550d')]
panels = [('events', 'a) Fire events', 1), ('area_km2', 'b) FINN burned area (km²)', 1),
          ('CO2', 'c) CO₂ (Mt yr⁻¹)', 1e6), ('PM25', 'd) PM₂.₅ (kt yr⁻¹)', 1e3)]
fmt = FuncFormatter(lambda v, _: num(v) if v >= 100 else f'{v:g}')
years = np.arange(2003, 2026)
fig, axes = plt.subplots(4, 1, figsize=(8.2, 9.0), dpi=400, sharex=True)   # 400 dpi: ACS minimum 300 dpi for colour art (11 Nov 2026)
w = 0.4
for ax, (col, title, sc) in zip(axes, panels):
    for sen, ver, lab, colr in groups:
        d = S[(S.sensor == sen) & (S.version == ver)].set_index('year')[col] / sc
        off = -w / 2 if (sen == 'MODIS') else (w / 2 if ver == 'v2.5' else 0)
        ax.bar(d.index + off, d.values, width=w if ver == 'v2.5' else 0.6, color=colr, label=lab, edgecolor='none')
    ax.set_title(title, loc='left', fontsize=10)
    ax.yaxis.set_major_formatter(fmt); ax.grid(axis='y', color='0.9', lw=0.6); ax.set_axisbelow(True)
    for s_ in ('top', 'right'):
        ax.spines[s_].set_visible(False)
h, l = axes[0].get_legend_handles_labels()
fig.legend(h, l, frameon=False, fontsize=8.5, ncol=3, loc='upper center', bbox_to_anchor=(0.5, 1.0))
axes[-1].set_xticks(years); axes[-1].set_xticklabels(years, rotation=90, fontsize=8)
fig.tight_layout(rect=(0, 0, 1, 0.97))
fig.savefig(FIG / 'Fig02_annual_series_4p_en.png'); plt.close(fig)

# ---------------------------------------------------------------- TOC graphic
E = pd.read_csv(TAB / 'table2_state_emissions_2012_2025.csv')
f_iav = E.CO2.max() / E.CO2.min()
V = pd.read_csv(TAB / 'viirs_effect.csv'); V = V[V.version == 'v2.5']
f_viirs = (1 + V.CO2_inc_pct.min() / 100, 1 + V.CO2_inc_pct.max() / 100)
C = pd.read_csv(TAB / 'inventory_comparison_2020.csv').set_index('inventory')
f_ver = C.loc['FINN v1.5, 2020', 'CO2_Mt'] / C.loc['FINN v2.5 MODIS+VIIRS, 2020', 'CO2_Mt']
MB = pd.read_csv(TAB / 'mapbiomas_state.csv')
MC = pd.read_csv(TAB / 'mcd64a1_comparison_state.csv')
rows = [('Interannual range of CO₂\n(max/min, 2012–2025)', (f_iav, f_iav), f'×{f_iav:.1f}', '#6b6b6b'),
        ('Adding VIIRS to MODIS\n(CO₂, 2012–2021)', f_viirs, f'×{f_viirs[0]:.1f}–{f_viirs[1]:.1f}', '#08519c'),
        ('FINN v1.5 vs v2.5\n(2020 CO₂, same area)', (f_ver, f_ver), f'×{f_ver:.1f}', '#e6550d'),
        ('FINN area / mapped area\n(MapBiomas, MCD64A1)', (MB.ratio.median(), MC.finn_over_mcd.median()),
         f'×{MB.ratio.median():.0f}–{MC.finn_over_mcd.median():.0f}', '#a63603')]
plt.rcParams.update({'font.family': 'DejaVu Sans'})
fig, ax = plt.subplots(figsize=(3.25, 1.75), dpi=600)
for k, (lab, (lo, hi), txt, col) in enumerate(rows[::-1]):
    ax.barh(k, hi - 1, left=1, height=0.55, color=col, alpha=0.35 if lo != hi else 1.0, edgecolor='none')
    if lo != hi:
        ax.barh(k, lo - 1, left=1, height=0.55, color=col, edgecolor='none')
    ax.text(hi * 1.12, k, txt, va='center', ha='left', fontsize=6.5, color='#222222', fontweight='bold')
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=5.6)
ax.set_xscale('log'); ax.set_xlim(1, 120)
ax.set_xticks([1, 2, 5, 10, 30, 100]); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
ax.tick_params(axis='x', labelsize=5.5, length=2); ax.tick_params(axis='y', length=0)
ax.set_xlabel('Factor (log scale)', fontsize=5.8, labelpad=1)
for s_ in ('top', 'right', 'left'):
    ax.spines[s_].set_visible(False)
fig.tight_layout(pad=0.25, rect=(0, 0, 1, 0.9))
fig.text(0.01, 0.97, 'FINN fire emissions, Santa Catarina (Brazil): method vs. year', fontsize=6.0, ha='left', va='top', fontweight='bold')
fig.savefig(FIG / 'TOC_graphic_est.png', dpi=600); plt.close(fig)
print(f'TOC factors: interannual {f_iav:.2f}; VIIRS {f_viirs[0]:.3f}-{f_viirs[1]:.3f}; version {f_ver:.3f}; '
      f'area MapBiomas median {MB.ratio.median():.2f}; MCD64A1 median {MC.finn_over_mcd.median():.2f}')

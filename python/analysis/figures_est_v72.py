#!/usr/bin/env python3
"""figures_est_v72 - table-of-contents graphic of the ES&T version of manuscript v7.2 (2026-11-09).

results/figures/TOC_graphic_est_v72.png (3.25 x 1.75 in, 600 dpi). Every value is read from a results table:
  interannual range of CO2, 2012-2025            table2_state_emissions_2012_2025.csv (max / min)
  adding VIIRS to MODIS (CO2), 2012-2021          viirs_effect.csv (1 + CO2_inc_pct/100, v2.5 rows)
  FINN v1.5 / FINN v2.5 MODIS, 2020 CO2           inventory_comparison_2020.csv (same MODIS detections)
  tropical instead of temperate forest class      forest_class_scenario_annual.csv (2012-2025)
  FINN area / mapped area, 2012-2024 (medians)    mapbiomas_state.csv and mcd64a1_comparison_state.csv
"""
import pandas as pd, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from _setup import TAB, FIG

E = pd.read_csv(TAB / 'table2_state_emissions_2012_2025.csv')
f_iav = E.CO2.max() / E.CO2.min()
V = pd.read_csv(TAB / 'viirs_effect.csv'); V = V[V.version == 'v2.5']
f_viirs = (1 + V.CO2_inc_pct.min() / 100, 1 + V.CO2_inc_pct.max() / 100)
C = pd.read_csv(TAB / 'inventory_comparison_2020.csv').set_index('inventory')
f_ver = C.loc['FINN v1.5, 2020', 'CO2_Mt'] / C.loc['FINN v2.5 MODIS, 2020', 'CO2_Mt']
F = pd.read_csv(TAB / 'forest_class_scenario_annual.csv')
f_for = (F.scenario_vs_reported.min(), F.scenario_vs_reported.max())
MB = pd.read_csv(TAB / 'mapbiomas_state.csv')
MC = pd.read_csv(TAB / 'mcd64a1_comparison_state.csv')
f_area = (MB.ratio.median(), MC.finn_over_mcd.median())
rows = [('Interannual range of CO₂\n(max/min, 2012–2025)', (f_iav, f_iav), f'×{f_iav:.1f}', '#6b6b6b'),
        ('Adding VIIRS to MODIS\n(CO₂, 2012–2021)', f_viirs, f'×{f_viirs[0]:.1f}–{f_viirs[1]:.1f}', '#08519c'),
        ('FINN v1.5 vs v2.5\n(2020, same MODIS detections)', (f_ver, f_ver), f'×{f_ver:.1f}', '#e6550d'),
        ('Tropical vs temperate\nforest class (2012–2025)', f_for, f'×{f_for[0]:.1f}–{f_for[1]:.1f}', '#31a354'),
        ('FINN area / mapped area\n(MapBiomas, MCD64A1)', f_area, f'×{f_area[0]:.0f}–{f_area[1]:.0f}', '#a63603')]
plt.rcParams.update({'font.family': 'DejaVu Sans'})
fig, ax = plt.subplots(figsize=(3.25, 1.75), dpi=600)
for k, (lab, (lo, hi), txt, col) in enumerate(rows[::-1]):
    ax.barh(k, hi - 1, left=1, height=0.55, color=col, alpha=0.35 if lo != hi else 1.0, edgecolor='none')
    if lo != hi:
        ax.barh(k, lo - 1, left=1, height=0.55, color=col, edgecolor='none')
    ax.text(hi * 1.12, k, txt, va='center', ha='left', fontsize=6.0, color='#222222', fontweight='bold')
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[0] for r in rows[::-1]], fontsize=5.0)
ax.set_xscale('log'); ax.set_xlim(1, 120)
ax.set_xticks([1, 2, 5, 10, 30, 100]); ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f'{v:g}'))
ax.tick_params(axis='x', labelsize=5.2, length=2); ax.tick_params(axis='y', length=0)
ax.set_xlabel('Factor (log scale)', fontsize=5.4, labelpad=1)
for s_ in ('top', 'right', 'left'):
    ax.spines[s_].set_visible(False)
fig.tight_layout(pad=0.25, rect=(0, 0, 1, 0.9))
fig.text(0.01, 0.97, 'FINN fire emissions, Santa Catarina (Brazil): method vs. year', fontsize=6.0, ha='left', va='top',
         fontweight='bold')
fig.savefig(FIG / 'TOC_graphic_est_v72.png', dpi=600); plt.close(fig)
print(f'TOC factors: interannual {f_iav:.2f}; VIIRS {f_viirs[0]:.3f}-{f_viirs[1]:.3f}; version (MODIS) {f_ver:.3f}; '
      f'forest class {f_for[0]:.3f}-{f_for[1]:.3f}; area medians {f_area[0]:.2f}, {f_area[1]:.2f}')

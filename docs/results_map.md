# Where each published number comes from

> 🌐 **English** · [Português (pt-BR)](results_map.pt-BR.md)

> **Note (11 Nov 2026):** the numbering below follows manuscript v3.2. For the version submitted to Environmental Science & Technology, chapter 8 of the tutorial (`TUTORIAL_FINN_SC_en.pdf`) maps each published value to its script, output and test.

M = manuscript v3.2 (`Artigo_Queimadas_v3.2`; sections 2.1 study area, 2.2 FINN model, 2.3 input data, 2.4 processing,
2.5 compounds, 2.6 spatial and temporal analyses, 2.7 comparison with mapped burned area, 2.8 climate and land cover,
2.9 limitations); S = supplementary material v3.1; R = state inventory report v4.1 (`inventario_queimadas_v4.1`). Every row is reproduced by `python python/run_analysis.py` and checked by
the test named in the last column (`python -m pytest -q tests`). Tables are in `results/tables/`, logs in
`results/logs/`, figures in `results/figures/`.

| Result | Where it is published | Script | Output | Test |
|---|---|---|---|---|
| Records, detections and events per product-year; 2025: 8 581 / 5 489 / 5 160; screened 5 121 | M 2.6; R 2–3 | `a01_events_screening.py` | `state_counts.csv` | `test_2025_records_detections_events` |
| Persistent thermal anomalies: 0–61 events per year (≤ 0.9 %, 2021), ≤ 2.5 % of CO₂ (2020); radii 0.75 / 1.5 km ≤ 0.8 / 1.2 %; Siderópolis 2021–2025 | M 2.6; S Table S6; R 2 | `a01_events_screening.py` | `screening_summary.csv`, `screening_flagged_detections.csv` | `test_screening_summary` |
| Screened events 2012–2025 (3 549 to 8 296; mean 5 945; −39.8 %, +8.6 %, −4.5 %; 2022–2025 mean 5 165, SD 180) | M 3, Figure 2; R 3, Figure 1 | `a02_series_trends.py` | `series_state_all_products.csv` | `test_screened_events_series` |
| Table 2 (CO₂ … SO₂, NOx = NOXasNO, COV = NMOC); changes 2023→2024 (+9.8 % NH₃ to +11.2 % NOx) and 2024→2025 (−1.7 % NH₃ to −4.9 % NOx); maxima in 2020 (NOx 2016) | M Table 2, 3–4; R Table 2, 3–4 | `a02_series_trends.py` | `table2_state_emissions_2012_2025.csv` | `test_table2`, `test_emission_changes` |
| Effect of adding VIIRS: events ×3.6–4.8; area +40.7–59.1 %; CO₂ +39.6–56.2 %; v2.5.1 ×3.9 / ×4.0 | M 3; S Table S2; R 3, Appendix A | `a02_series_trends.py` | `viirs_effect.csv` | `test_viirs_effect` |
| Mann–Kendall and Sen (τ −0.12 to −0.03; p ≥ 0.58; slopes −46, −35, −35 265, −123); Hamed–Rao p unchanged for 2012–2025 and 0.042–0.084 for 2012–2021 | M 2.6, 3; S Table S5 | `a02_series_trends.py` | `mann_kendall.csv` | `test_mann_kendall` |
| Lag-1 autocorrelation of the trend series (0.11 to 0.22) | M 2.6 | `a02_series_trends.py` | `mann_kendall.csv` (`r1`) | `test_round6.py::test_lag1_of_trend_series` |
| Municipal events 2025 and 2024; ≥ 100 events: 9 and 10 municipalities; 277 municipalities with events | M 3, Figure 3; R 3–4, Figure 2 | `a03_municipal_mesoregion.py` | `municipal_2025.csv`, `municipal_events_by_year.csv` | `test_municipal_events_2025` |
| Table 3 (mesoregions); Serrana 46.5 % of CO₂; Serrana + Oeste 72.9 % (70.5–75.4 %); events per 100 km² | M Table 3, 3–4, Figure 4; R Table 3, 3–4, Figure 3 | `a03_municipal_mesoregion.py` | `mesoregion_2025.csv` | `test_table3_and_shares` |
| Municipal burned area and leaders per pollutant; PM₂.₅ > 500 t list | M 3–4, Figures 6–7; S Table S4; R 3–4, Table 4, Figures 5–6 | `a03_municipal_mesoregion.py` | `municipal_2025.csv` | `test_area_and_leaders` |
| Seasonality (Jul–Sep 55.8 % in 2025, 60.0 % in 2012–2025; Jul–Nov 72.1 %) | M 2.8, 4; R 3 | `a03_municipal_mesoregion.py` | log `a03_municipal_mesoregion.txt` | — |
| Vegetation partition (GENVEG): area 46.3 / 31.9 / 20.2 / 1.6 %; temperate forest 55.0 % of CO₂, 74.1 % of PM₂.₅; 1.73 vs 0.54 kg m⁻² | M 3; S Table S9; R 4 | `a04_genveg_partition.py` | `genveg_partition.csv` | `test_genveg` |
| FINN vs MapBiomas: ratio 13.3–37.7 (median 17.2); r 0.77, ρ 0.75; municipal ρ 0.47–0.73 | M 2.7, 3, 4; S Table S3, Figure S1; R 2, 4, 8 | `a05_mapbiomas_comparison.py` | `mapbiomas_state.csv`, `mapbiomas_agreement_by_year.csv` | `test_mapbiomas` |
| Mapped area per FINN event (typology check) | R 4 | `a05_mapbiomas_comparison.py` | `mapbiomas_area_per_event.csv` | — |
| Climate: precipitation ρ −0.68 / −0.71 / −0.71 (Holm ≤ 0.035); ONI ρ −0.53 to −0.51; first differences −0.65 to −0.58; VPD 0.48–0.56 | M 3–4; S Table S7, Figure S2; R 4, 8 | `a06_climate_drivers.py` | `climate_correlations.csv` | `test_climate` |
| Land cover vs event density (295 municipalities, Collection 10.1): ρ silviculture 0.42, forest −0.25, grassland 0.13 (p = 0.03); Moran 0.32 → 0.002; SEM (n = 294) effects +37 / +35 / +24 / +15 %; AIC 492.4 → 415.9 | M 2.8, 3; S Table S8; R 4, 8 | `a07_landcover.py` | `landcover_spearman.csv`, `landcover_sem.csv` | `test_landcover` |
| Land cover vs CO₂ per event (SEM: silviculture +27 % per 10 p.p.) | R 4, 8 | `a07_landcover.py` | `landcover_sem.csv` | `test_landcover` |
| Kernel density (σ = 2.8 km; CvL 8.8 km; Scott 21.7 km; max 52.8 per 100 km²; top 1 %: Serrana 93.6 %); Diggle selector 0.75 km, r = 0.63 (log only) | M 2.6, 3, Figure 5; R 3, Figure 4 | `R/analysis/kde_events.R` | `kde_2025_grid.csv`, `kde_2025_bandwidths.csv`, log `kde_2025_summary.txt` | `test_kde` |
| CV of CO₂ 28.3 %; Gini 0.728 (277 municipalities); CO₂ per event (median 478 t; São Joaquim 415 t; Lebon Régis 2 118 t) | R 4, Appendix A | `a08_report_indicators.py` | `intensity_per_event_2025.csv` | `test_report_indicators` |
| Emission factors implied by the records = Wiedinmyer et al. (2023) Table 4 (ratios 0.9986–1.0026) | M 2.4; docs/provenance.md | `a09_emission_factor_check.py` | `emission_factor_check.csv` | `test_emission_factor_check` |
| Route A replication (raw FINN → records) | docs/provenance.md | `python/01`, `02`, `06` | `data/derived/finn_sc_records_rebuilt.csv.gz` | `test_route_a.py` |
| Report-only values: area −4.3 % (2024→2025); CO₂ 2.30–6.63 Mt; Lages + São Joaquim 15.0 % of events, 10.3 % of CO₂, 22.1 % of the Serrana CO₂; top-3 951 events (18.6 %); event densities (São Joaquim 18.0 per 100 km²) | R Summary, 3, 4 | `a02`, `a03` | `series_state_all_products.csv`, `municipal_2025.csv` | `test_report_v2.py` |
| Profiles A/B: CO₂ per event (404–526 t vs 1 046–2 118 t), FINN temperate-forest share, MapBiomas area per FINN event (0.004–0.021 vs 0.054–0.082 km²), medians by dominant vegetation class | R Summary, 4, 7 | `a05`, `a08` | `intensity_per_event_2025.csv`, `mapbiomas_area_per_event.csv`, log `a08_report_indicators.txt` | `test_report_v2.py` |
| CO₂ vs fire-season climate (ρ −0.71 precipitation, −0.70 soil moisture, Holm p 0.022; VPD 0.56; ONI −0.51, first differences −0.65); 2025 vs 2024 precipitation (718 vs 638 mm) | R 4, 7, 8 | `a06` | `climate_correlations.csv` | `test_report_v2.py` |
| CO₂ per event vs land cover (n = 288; ρ 0.85 FINN temperate-forest share, 0.68 silviculture, −0.62 agriculture; SEM +27.6 %/−10.9 % per 10 p.p.; Moran 0.21 → −0.004) | R 4 (box), 8, Appendix A | `a07` | `landcover_spearman.csv`, `landcover_sem.csv` | `test_report_v2.py` |
| Kernel density by mesoregion (10.4 Serrana … 2.3 Grande Florianópolis per 100 km²), sensitivity r 0.83–0.97, maximum inside Lages | R 3, 8 | `R/analysis/kde_events.R` | `kde_2025_grid.csv`, log `kde_2025_summary.txt` | `test_report_v2.py` |
| Report Figure 7 (repository structure) | R Appendix A | `tools/fig7_flowchart.py` | `results/figures/Report_Fig07_repository_structure.png` | — |
| Counting units 2025: events would be +0.8 % (unscreened), +7.2 % (detections), +67.6 % (records); Lages 429 events vs 670 records (+56 %) | M 4; R 3 | `a01`, `a03` | `state_counts.csv`, `municipal_2025.csv` | `test_round5.py::test_counting_units_2025` |
| Events with more than one detection (20 766 of 124 602; MODIS+VIIRS 9 287 of 83 512, 11.1 %; 2025: 267 of 5 160, 5.2 %) | docs/analysis.md (not printed in the manuscript) | `a01` | `events.csv.gz` | `test_round5.py::test_events_with_several_detections` |
| 2020 state inventory (LCQAR, 2022: 12.91 Mt, 4 625 *focos*) vs FINN v1.5 records of 2020 (12.88 Mt, 4 609; ≤ 0.4 %); FINN v2.5 2020: MODIS 4.56 Mt (5 643 records, 1 971 events; −65 %), MODIS+VIIRS 6.63 Mt (15 727 records, 8 212 events; +45 %) | M 4; R 1, 3 | `a01`, `a02`; `data/external/legacy_finn15_lcqar_2020.csv` | `series_state_all_products.csv`, `state_counts.csv` | `test_round5.py::test_lcqar_2020_and_finn_versions` |
| Kernel density west of 52.5° W (2.6 per 100 km²) and Norte Catarinense east of 49.5° W (1.7) vs state mean 5.4 | M 4 | `R/analysis/kde_events.R` | `kde_2025_grid.csv` | `test_round5.py::test_kde_far_west_and_north_coast` |
| Figure 7 classes (Fisher–Jenks; CO₂ 10 329 / 31 410 / 71 909 / 149 038 t; CO 797 / 2 178 / 4 109 / 6 885 t) | M Figure 7; R Figure 6 | `a10_figures.py` | log `a10_figures.txt` | `test_round5.py::test_figure6_fisher_jenks_reproduces_original_breaks` |
| Study-area figure: land-cover shares 2019 (forest 40.2 %, mosaic of uses 17.3 %, temporary crops 13.2 %, silviculture 10.5 %, pasture 9.9 %, grassland 5.2 %, urban 1.9 %) | M Figure 1, 2.1 | `tools/study_area_map.py` | `data/external/mapbiomas_c10_lulc2019_SC_class_areas.csv` | `test_round5.py::test_study_area_land_cover_shares` |
| Land cover by mesoregion, 2019 (Serrana: 97.7 % of the state grassland, 21.6 % of its area; 37.5 % of the silviculture; Oeste: 45.3 % of temporary crops, 41.3 % of the mosaic of uses; forest 62.1 % of Grande Florianópolis and 53.9 % of Vale do Itajaí) | M 2.1 | `tools/study_area_map.py` | `results/tables/landcover2019_mesoregion.csv` | `test_round5.py::test_study_area_mesoregion_land_cover` |

## Comparison with BRAIN, 2019 and 2020 (notebook and tool, not part of `run_analysis.py`)

| Result | Where it is published | Notebook or tool | Output in `results/` |
|---|---|---|---|
| BRAIN = 1.01 × FINN v1.5 annual file in 7 474 of 7 474 cell-days (2019); hourly profile 210 and 19 layers in 2019 and 2020 | M 2.9, Discussion; S S24; R 3.9 | `notebooks/BRAIN_FINN_comparison_SC.ipynb` (2019 run: `BRAIN_FINN_comparison_SC_2019.ipynb`) | `brain_2019/tables/processing_checks.csv`, `brain_20xx/logs/time_profile_check.csv`, `brain_20xx/logs/run_metadata.json` |
| Totals 2019 and ratios FINN v2.5 / BRAIN (CO 0.61 with MODIS+VIIRS, 0.41 with MODIS; NOx 0.36 to SO₂ 1.24) | M Discussion; S Table S24a; R 3.9 | same | `brain_2019/tables/annual_totals_and_ratios.csv` |
| 2019: monthly r 0.998, August peak; daily ρ 0.84 (0.78 to 0.88); cells; municipalities ρ 0.90, 9 of the top 10 | M Discussion; S Table S24b; R 3.9 | same | `brain_2019/tables/monthly_correlations.csv`, `daily_statistics.csv`, `cell_statistics_R1.csv`, `municipal_statistics.csv` |
| Totals 2020 (364 days) and ratios FINN v2.5 / BRAIN (CO 0.69 with MODIS+VIIRS, 0.48 with MODIS; NOx 0.37 to NH₃ 1.40) | M Discussion; S Table S24c; R 3.9 | same, `YEAR = 2020` | `brain_2020/tables/annual_totals_and_ratios.csv` |
| 2020: monthly r 0.969, August peak; daily ρ 0.84 (0.79 to 0.88); cells; municipalities ρ 0.91, 8 of the top 10 | M Discussion; S Table S24d; R 3.9 | same | `brain_2020/tables/monthly_correlations.csv`, `daily_statistics.csv`, `cell_statistics_R1.csv`, `municipal_statistics.csv` |
| FINN version in BRAIN, cell-days in R1: 2020 BRAIN CO on cell-days with FINN v1.5 fire 94.4 %, with FINN v2.5 65.0 % (MODIS) and 67.5 % (MODIS+VIIRS); 2019 control 64.4 % and 66.8 % | M Discussion; S Table S24e; R 3.9 | `tools/brain_cells_and_finn15_check.py --check2019`, `--check2020` | `brain_2019/tables/check_cell_days_R1_finn25.csv`, `brain_2020/tables/check_cell_days_R1_finn15_finn25.csv` |

## Figures

| Manuscript (v3.2) | Report (v4.1) | Script | File in `results/figures/` |
|---|---|---|---|
| Figure 1, study area and land cover 2019 | — | `tools/study_area_map.py` | `Fig01_study_area_pt.png` (English labels: `Fig01_study_area_en.png`) |
| Figure 2, annual series 2003–2025 | Figure 1 | `a10_figures.py` | `Fig02_annual_series.png` |
| Figure 3, events per municipality, 2025 | Figure 2 | `a10_figures.py` | `Fig03_events_municipal_2025.png` |
| Figure 4, events and event density per mesoregion, 2025 | Figure 3 | `a10_figures.py` | `Fig04_events_mesoregion_2025.png` |
| Figure 5, kernel density of events, 2025 | Figure 4 | `a10_figures.py` (grid from `R/analysis/kde_events.R`) | `Fig05_kde_events_2025.png` |
| Figure 6, FINN burned area per municipality, 2025 | Figure 5 | `a10_figures.py` | `Fig06_burned_area_municipal_2025.png` |
| Figure 7, emissions per municipality, 2025 (Fisher–Jenks classes) | Figure 6 | `a10_figures.py` | `Fig07_emissions_municipal_2025.png` |
| Supplementary Figure S1, FINN vs MapBiomas Fogo | — | `a10_figures.py` | `FigS1_finn_vs_mapbiomas.png` |
| Supplementary Figure S2, climate and events | — | `a10_figures.py` | `FigS2_climate_events.png` |
| — | Figure 7, repository structure | `tools/fig7_flowchart.py` | `Report_Fig07_repository_structure.png` |
| quick-look map of the kernel density (not published) | — | `R/analysis/kde_events.R` | `kde_2025_quicklook.png` |

The log of `a10_figures.py` (`results/logs/a10_figures.txt`) still labels the figures with the report numbering
(“Figure 1” = annual series … “Figure 6” = emissions), which is the numbering the test
`test_round5.py::test_figure6_fisher_jenks_reproduces_original_breaks` reads.

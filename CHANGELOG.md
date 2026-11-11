# Changelog

## 2026-11-11: FINN v1.5 2002, 2016 and 2017 from the NCAR annual files; 2002 address; ES&T figure resolution

* `tools/finn15_raw_to_grid.py` (new): cuts a FINN v1.5 GEOS-Chem annual file of NCAR to the SC grid box and converts it to
  tonnes with the factors of the authors' files; on 2015 it reproduces all 3,537 rows of the authors' file.
* `tools/finn15_records.py`: reads the authors' files and, for years whose file is missing (2002) or a copy of another
  year (2016, 2017), the NCAR files; output renamed `data/external/finn15_SC_records_2002_2020*.csv`.
* `a20_finn15_correction.py`, part 7: 2002-2020 (`results/tables/finn15_2002_2020_correction.csv`, formerly
  `finn15_2003_2020_correction.csv`). Next-day continuations: 27.0% to 32.4% of the yearly CO2 in all 19 years (median
  28.7%). Teixeira et al. (2025) Table C.1 equals the sum of all records in 15 of 16 years (2002-2017); 2016: 0.36% below.
* Download addresses: the FINN v1.5 file of 2002 is `FINNv1.5_2002.GEOSCHEM.tar.gz` (the `.txt.gz` address returned 404),
  corrected in `R/utils_finn.R` and `python/finn_sc/download.py`; both note that the FINN page asks for the user's name
  and contact information before the FINN v1.5 downloads. `tools/download_finn15_years.R` (new) downloads and checks
  FINN v1.5 annual files.
* `figures_est_en.py` and `fig_v71.py` (Figure 8): 400 dpi, so that ES&T Figures 2 and 3 meet the ACS minimum of 300 dpi
  for colour art. Content unchanged.
* `tests/test_round22.py`: `test_finn15_2002_2020_correction` replaces `test_finn15_2003_2020_correction`.
* Tutorial: new illustrated tutorial in English and Brazilian Portuguese (`TUTORIAL_FINN_SC_en.pdf`, `_pt.pdf`, 27 pages each), built by `docs/tutorial_v2/build_tutorial.py` (WeasyPrint) from `docs/tutorial_v2/content.py` and the figures in `results/figures/`; it covers a01 to a20, the ES&T results map, the FINN v1.5 tools and the data terms. The sources of the tutorial of 1 Nov 2026 (`docs/tutorial/`) were removed. README: expected 96 tests and 107 manifest files.

## 2026-11-09: FINN v1.5 inventories with and without the next-day continuations

* `python/analysis/a20_finn15_correction.py` (log `results/logs/a20_finn15_correction.txt`):
  `finn15_lcqar_2020_correction.csv`: the earlier state inventory (LCQAR, 2022) equals all 4,609 FINN v1.5 records of
  2020 (CO2, CO and PM2.5 1.0020 times) and is 1.373 times the 2,716 original detections (continuations removed; 27.0% of
  CO2, CO and PM2.5; 41.1% of the records). FINN v1.5 / FINN v2.5 MODIS CO2: 2.823 with all records, 2.059 without the
  continuations; FINN v1.5 / this inventory (MODIS+VIIRS; Figure 9): 1.943 and 1.417.
  `brain2020_finn15_correction.csv`: in the 4 km cells entirely inside SC, BRAIN 2020 CO is 0.875 times the FINN v1.5
  records and 1.199 times the original detections (PM2.5 0.922 and 1.263); 94.4% of the BRAIN CO falls on cell-days with
  FINN v1.5 fire and 68.9% on cell-days with an original detection, so BRAIN 2020 includes the continuations. BRAIN 2019
  equals the FINN v1.5 file x 1.01 in every cell-day; its correction needs the 2019 FINN v1.5 records (not in the
  repository).
  `continuation_check_finn25.csv`: in the FINN v2.5 and v2.5.1 records of this inventory (2003-2025, MODIS and
  MODIS+VIIRS), 37 of 151,443 day-location pairs repeat the coordinates of the previous day and one has half of its CO2
  (0.0009% of the MODIS+VIIRS v2.5 CO2): the inventory has no next-day continuations.
  `teixeira2025_vs_finn25_modis.csv`: FINN v1.5 totals of Teixeira et al. (2025, supplement Table C.1, transcribed to
  `data/external/teixeira2025_tableC1_SC_finn15.csv`) against FINN v2.5 MODIS, 2003-2017: the annual series agree in
  rank (Spearman 0.97-0.98); Teixeira / FINN v2.5 MODIS median 1.72 for CO2 (1.24-2.68), 1.51 for CO and 1.28 for
  PM2.5, against 2.82 (all records) and 2.06 (original detections) for CO2 in 2020. The FINN v1.5 files of 2002-2017
  are not in the repository, so their continuations cannot be removed.
  `finn15_2019_correction.csv`: FINN v1.5 records of 2019 inside SC (new `tools/finn15_2019_records.py` ->
  `data/external/finn15_2019_SC_records.csv`, from the authors' per-year file of June 2025): 3,491 records = 2,042
  original detections + 1,449 continuations (27.5% of CO2). BRAIN 2019 = all records x 1.010 and original detections
  x 1.390 (CO and PM2.5, cells inside SC); 26.9% of the BRAIN CO falls on cell-days without an original detection.
  `legacy_aggregated_check.csv`: the authors' `aggregated_emissions_all.csv` of 5 Feb 2026 (copied to
  `data/external/legacy_aggregated_emissions_all_2026-02-05.csv`). FINN v2.5 and v2.5.1: 8,595 of 8,827
  municipality-year-configuration rows equal this inventory; the 232 rows of MODIS v2.5 2011 are doubled (x 2.000; the
  archived records hold the 2011 file once). FINN v1.5: equal to Table C.1 of Teixeira et al. (2025) to the tonne in
  2003, 2005-2009 and 2011-2015 (2010: +0.01%); 2016 and 2017 are copies of 2015 (Teixeira: 9.59 and 9.77 Mt CO2);
  2002 and 2004 missing; 2019 and 2020 equal to the sum of all FINN v1.5 records in this repository, continuations
  included.
  `finn15_2003_2020_correction.csv` (part 7): FINN v1.5 records 2003-2015 and 2018-2020 (`tools/finn15_records.py` ->
  `data/external/finn15_SC_records_2003_2020.csv`, from the authors' per-year files uploaded on 9 Nov 2026; 2016 and 2017
  excluded because those files are copies of 2015; 2002 missing; 2009 de-duplicated). Teixeira et al. (2025) equal the
  sum of all records, next-day continuations included, in all 13 comparable years (2003-2015; 2010: 0.01%); the
  continuations hold 27.0% to 32.4% of the yearly CO2 (median 28.6%).
* `a20` added to `python/run_analysis.py`; tests `test_finn15_correction_2020`, `test_teixeira2025_vs_finn25`,
  `test_finn15_2019_and_legacy_file` and `test_finn15_2003_2020_correction` (96 tests pass); manifest 107 files.

## 2026-11-09: figures of the ES&T version of the article (v7.2)

* `python/analysis/figures_est_v72.py` writes `results/figures/TOC_graphic_est_v72.png` (3.25 x 1.75 in, 600 dpi): CO2
  factor of five sources of variation, read from `table2_state_emissions_2012_2025.csv` (highest/lowest annual CO2,
  2.88), `viirs_effect.csv` (MODIS+VIIRS/MODIS, 1.396 to 1.562), `inventory_comparison_2020.csv` (FINN v1.5/v2.5 with the
  same MODIS detections, 12.88/4.56 = 2.82), `forest_class_scenario_annual.csv` (tropical/temperate class, 2.424 to
  2.744), and `mapbiomas_state.csv` with `mcd64a1_comparison_state.csv` (median FINN area/mapped area, 17.24 and 34.41).
* `figures_est_en.py` rerun: `Fig02_annual_series_4p_en.png` (events, FINN area, CO2 and PM2.5, 2003-2025).
* `figures_est_v72.py` added to `python/run_analysis.py`.
* The R package that implements the workflow was renamed `open.burning.finnr` (formerly `wildfire.finnr`); FINN_SC is
  unchanged.

## 2026-11-08: checks asked in the authors' comments on the English manuscript v7.1

* `python/analysis/a17_v72_review.py` (log `results/logs/a17_v72_review.txt`) adds:
  `finn15_v25_2020_records.csv`, `finn15_v25_2020_decomposition.csv`, `finn15_v25_2020_genveg_matched.csv` and
  `finn15_2020_mesoregion.csv`. FINNv1 counts each MODIS detection between about 30 N and 30 S for two days, the second
  at half size (Wiedinmyer et al., 2011, Sect. 2): of the 4,609 FINN v1.5 records of 2020 in Santa Catarina, 2,716 are
  original detections and 1,893 next-day continuations (same coordinates as a record of the previous day, CO2 ratio 0.5),
  with 27.0% of the v1.5 CO2. 97.8% of the FINN v2.5 MODIS detections have an original v1.5 detection within 2 km on the
  same day. v1.5 / v2.5 MODIS = 2.82 = continuations (1/0.730) x detections (0.990) x area per detection (1.159) x CO2 per
  km2 (0.423); 704 of the 1,084 matched v1.5 tropical-forest detections are temperate forest in v2.5 (8,535 vs 2,597 t CO2
  km-2). The v1.5 AREA field of the continuations is the full area while their emissions are at half; the effective v1.5
  area is 3,287 km2 (not 4,135).
* `event_landcover_by_mesoregion.csv`: MapBiomas 2019 group under the event centroid by mesoregion (Serrana: 42.8% of the
  events on grassland, 21.6% of its classified area; grassland events 29.6% of its event CO2).
* `mesoregion_profile.csv`, `municipal_profile_top2025.csv`: area, 2022 Census population, GDP and agricultural share of
  the gross value added (2021) from `data/external/ibge_sc_municipal_pop2022_gdp2021_2023.csv` (IBGE SIDRA tables 4709 and
  5938, accessed 8 Nov 2026), MapBiomas 2023 land cover and FINN fire indicators.
* `a10_figures.py`: `FIG_NOTES=0` writes the map figures without the source note below each map (`*_nn.png`,
  `*_nn_en.png`; the note's content goes to the caption) and skips the redundant canvas redraws of geopandas (speed only).
  Both runs added to `python/run_analysis.py`.
* `python/analysis/a18_exports.py` (log `results/logs/a18_exports.txt`) aggregates the Comex Stat file sent by the authors (`data/external/comexstat_SC_municipios_2025.xlsx`) into `exports_2025_by_mesoregion.csv` and `exports_2025_by_municipality.csv`: US$ 14.95 billion FOB in 2025, 57.6% agri-food (HS chapters 01-24) and 11.2% wood, pulp and paper (HS 44, 47, 48); Serrana 5.0% of the state exports, 72.8% of them wood, pulp and paper; the eight municipalities of manuscript Table 4, US$ 451.6 million (3.0%), 68.8% wood, pulp and paper. Comex Stat assigns exports to the tax domicile of the exporting company (Vale do Itajai 50.1% of the state exports), so these values locate exporters, not production. Two Comex Stat spellings are mapped to the IBGE names (Picarras, Presidente Castelo Branco).
* The 2020 FINN v1.5 records reproduce the earlier state inventory (LCQAR, 2022, report read on 8 Nov 2026): CO2 12,883,691 vs 12,909,573 t, CO 698,281 vs 699,668 t, PM2.5 70,586 vs 70,724 t, 4,609 records vs 4,625 "focos", and the AREA field of all records (4,135 km2, continuations at full area) vs "about 4.1 thousand km2".
* `python/analysis/a19_v72_followup.py` (log `results/logs/a19_v72_followup.txt`), answers to the authors' questions of
  8 Nov 2026. `finn15_2020_continuation_rule.csv`: no next-day continuation of FINN v1.5 has a new detection within 1 km
  on the same day (one fire per pixel per day, Wiedinmyer et al., 2011), and 167 of the 823 detections without a
  continuation have a new detection within 1 km on the next day. FINN v2.5 keeps the two-day rule only between about
  23.5 N and 23.5 S (Wiedinmyer et al., 2023, Sect. 2.1); in the 2020 FINN v2.5 MODIS file of Santa Catarina, 2 of 2,689
  day-location pairs repeat the coordinates of the previous day. `forest_class_scenario.csv` and
  `forest_class_scenario_annual.csv`: FINN v2.5 assigns evergreen broadleaf and mixed forests to temperate forest outside
  23.5 N to 23.5 S (Table 1 of that paper); with the South America fuel loadings (tropical 26,755, temperate 7,400 g m-2)
  and the Table 4 emission factors, the tropical class would multiply the CO2 of each forest detection by 3.93 and its CO
  by 2.76, and the annual CO2 of the state by 2.42 to 2.74 (MODIS+VIIRS, 2012-2025; temperate forest 48.5% to 59.5% of
  the CO2); 2020 MODIS: 12,756 kt (2.80 x; FINN v1.5 12,884 kt). Upper bound, since generic type 4 also holds deciduous
  broadleaf forest. The NOx of the earlier state inventory (LCQAR, 2022, Table 11: 38,037 t) differs by 0.20% from the
  NO + NO2 mass of the FINN v1.5 records (37,962 t).
* `fig_v71.py`: `FIG_NOTES=0` writes Figures 8 and 9 without the notes below the panels (`*_nn_{en,pt}.png`; the note
  goes to the caption), and Figure 9 gains the row of the forest-class scenario (2012-2025). Both runs added to
  `python/run_analysis.py`.
* `README.md` and `README.pt-BR.md`: new section on the differences between the FINN v2.5 README of NSF NCAR and the
  files (kg/day units of NOXasNO, NMOC and NMHC; nesting of POLYID and FIREID) and on two model conventions (next-day
  repetition in FINN v1.5 and v2.5; temperate forest class outside 23.5 N to 23.5 S); expected counts of the checks
  updated (92 tests, 99 manifest files).
* `tests/test_round22.py` (8 tests; rounds 20-22: 16 pass). Manifest: 99 files (the 95 files of the previous update
  unchanged; 4 added by a19).

## 2026-11-07: checks asked in the authors' comments on the abstract of manuscript v7

* `python/analysis/a16_v71_review.py` (log `results/logs/a16_v71_review.txt`) adds four tables:
  `climate_per_event.csv` and `climate_per_event_spearman.csv` (events, CO2, CO2 per event and burned area per event
  against the July-November precipitation; wetter seasons had fewer and smaller events, while CO2 per event showed no
  significant association, rho = -0.44, p = 0.12), `area_ratio_screened.csv` (FINN / mapped area with and without the
  persistent thermal anomalies; medians 17.2 and 34.4 in both cases, anomalies 0.11% of the FINN area in the median
  year) and `municipal_top_2020_versions.csv` (largest CO2 emitters of 2020 in FINN v1.5 and v2.5; municipal Spearman
  rho = 0.945 between versions).
* `tests/test_round21.py` checks these values. Manuscript v7.1 compares FINN v2.5 directly with FINN v1.5 instead of
  with the earlier state inventory.
* `python/analysis/fig_v71.py` (run twice from `python/run_analysis.py`, with `FIG_LANG=en` and `FIG_LANG=pt`)
  replaces `fig_v7_en.py` for manuscript Figures 8 and 9 in English and Portuguese
  (`Fig08_recurrence_landcover_{en,pt}.png`, `Fig09_sensitivity_factors_{en,pt}.png`; Portuguese labels use decimal
  commas). In Figure 9 the model-version row now reads "FINN v1.5 instead of v2.5 (2020)".
* `python/run_analysis.py` no longer runs `fig_v7_en.py`, which wrote the same English file names and would have
  overwritten the v7.1 figures. Manifest: 84 files (the 79 previous files unchanged).

## 2026-11-06: robustness checks of the English manuscript v7

* `python/analysis/a15_v7_review.py` (log `results/logs/a15_v7_review.txt`) adds five tables:
  `sen_slope_ci.csv` (exact Mann-Kendall p and 95% confidence interval of the Sen slope), `climate_version_robustness.csv`
  (climate correlations for the FINN v2.5 years alone and partial rank correlations controlling for the version change
  of 2022), `viirs_increment_independent.csv` (VIIRS increment against its own MODIS denominator and against the
  MapBiomas Fire and MCD64A1 burned areas), `emission_scenario_mapped_area_municipal.csv` (mapped-area scenario computed
  municipality by municipality) and `sensitivity_factors.csv` (values of manuscript Figure 9).
* `python/analysis/fig_v7_en.py`: manuscript Figure 8 (`Fig08_recurrence_landcover_en.png`, English version of the
  recurrence figure with the selection ratios and their 95% block-bootstrap intervals) and Figure 9
  (`Fig09_sensitivity_factors_en.png`). Both run from `python/run_analysis.py` after a14.
* `tests/test_round20.py` (5 tests). Manifest: 79 files (the 73 previous files unchanged).
* Findings used in the manuscript: no monotonic trend from 2012 to 2025 (95% intervals of the Sen slopes about -5% to
  +3% of the mean per year); the 2012-2021 v2.5 series has exact Mann-Kendall p of 0.22 to 0.29; the precipitation
  association holds within the v2.5 years (rho -0.65 to -0.71) and controlling for the version (rho -0.59 to -0.64);
  the VIIRS increment is not significantly associated with burned-area measures independent of FINN (rho -0.34 and
  -0.03); the municipal-scale mapped-area scenario is 8% to 23% below the State-scale scenario.

## 2026-11-04: map layout

* North rose aligned to the right end of the scale bar in every map (`finn_sc/cartography.py`, `rose_above_bar(...,
  align='right')`; `a10_figures.py`, `tools/study_area_map.py`, `a11`, `a13`, `figS3_en.py`), at the authors' request.
* Figure 7: scale bar height and labels 30% larger (`scale_bar(..., grow=1.3)`); the bar still represents 100 km.
* Figures 1 and 3 to 7 redrawn in Portuguese and English (`results/figures/`); the layout check reports no overlaps.
  Tables, logs and the manifest are unchanged (73 of 73 files OK). Supplementary Figures S3 and S4 use the same rule
  when their scripts are run again.

## 2026-11-03: comparison with BRAIN extended to 2020

* `notebooks/BRAIN_FINN_comparison_SC.ipynb` (brain_core 1.1.1, `YEAR = 2019` or `2020`) replaces the 2019-only
  notebook, which is kept as the record of the 2026-11-01 run. Version 1.1.1 rejects BRAIN files on another grid
  (the 2020-12-06 file is on the 20 km d01 grid).
* `results/brain_2020/`: outputs for 2020 (364 days). `tools/brain_cells_and_finn15_check.py`: BRAIN daily cells and
  the cell-day check of the FINN version (`--check2019`, `--check2020`).
* Finding: in Santa Catarina the BRAIN fire emissions correspond to FINN v1.5 in both years. In 2019 BRAIN equals the
  FINN v1.5 annual file x 1.01 in every cell-day. In 2020, for which the BRAIN article states FINN v2.5, 94.4 % of
  BRAIN CO lies on cell-days with FINN v1.5 fire, against 65.0 % and 67.5 % with FINN v2.5 MODIS and MODIS+VIIRS
  (64.4 % and 66.8 % in 2019). Used in the article (v6.5), in section S24 of the supplementary material (v3.7) and in
  section 3.9 of the report (Rev 05).

## First public release (2026-11-01)

FINN_SC reproduces every table, statistic and figure of the article on the spatio-temporal variability of
biomass-burning emissions in Santa Catarina (2012-2025) and of the 2025 state inventory report.

Contents of this release:

* Route B (reproduction): `python/run_analysis.py` runs the analysis scripts `a01` to `a14`, the kernel density in R
  (`R/analysis/kde_events.R`, `kde_sensitivity_annual.R`), the study-area maps and the English figures, from the archived
  FINN records of Santa Catarina (`data/derived/`, 258,694 records, 2003-2025) and the archived external data
  (`data/external/`).
* Route A (replication): download, unit conversion, clipping, aggregation and maps of FINN emissions for any region,
  in R (`R/00` to `05`) and in Python (`python/00` to `06`), driven by `config/config.yml`, also as notebooks.
* Google Earth Engine recipes for the external data (`gee/`), with the executed copies of the notebooks.
* Comparison with the BRAIN fire emissions of 2019 (`notebooks/BRAIN_FINN_comparison_SC_2019.ipynb`, Google Colab),
  with the outputs of the published run in `results/brain_2019/`.
* 76 automated tests (`tests/`) and the checksum manifest of the published tables and logs
  (`results/MANIFEST.sha256`, `tools/verify_manifest.py`).
* Bilingual documentation (`docs/`) and an illustrated tutorial in Portuguese and English (`TUTORIAL_FINN_SC_pt.pdf`,
  `TUTORIAL_FINN_SC_en.pdf`; sources and the text-in-box check in `docs/tutorial/`), with a step-by-step run in Google
  Colab and the set-up of an Earth Engine project.

The development history before this release (internal revision rounds of the article, of the supplementary material
and of the report) is not part of the public record.

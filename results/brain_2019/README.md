# `results/brain_2019/`: comparison with BRAIN, 2019

Outputs of `notebooks/BRAIN_FINN_comparison_SC_2019.ipynb`, run in Google Colab on 2026-11-01 (log
`logs/run_metadata.json`), used in section S24 of the supplementary material (Tables S24a, S24b and S24e), in the
discussion of the article and in section 3.9 of the report. The current notebook `notebooks/BRAIN_FINN_comparison_SC.ipynb`
with `YEAR = 2019` reproduces the same outputs (2020: `../brain_2020/`).
The notebook downloads the 365 daily BRAIN fire-emission files of 2019 (FINN v1.5 converted for CMAQ with
finn2cmaq; Hoinaski et al., 2024, https://doi.org/10.5194/essd-16-2385-2024; data set
https://doi.org/10.57760/sciencedb.09886), checks how they were built and compares them with the FINN_SC records
of 2019 (FINN v2.5 MODIS and MODIS+VIIRS) on the same 4 km grid, on the same days and in the same region.

* `tables/annual_totals_and_ratios.csv`: annual totals (t) and ratios, region R1 (7 188 cells entirely inside SC)
  and R2 (whole State; BRAIN weighted by the cell fraction inside SC, with lower and upper bounds).
* `tables/monthly_*.csv`, `tables/daily_*.csv`: monthly and daily totals and correlations (daily Spearman with a
  moving-block bootstrap 95 % interval, blocks of 7 days).
* `tables/cell_*.csv`, `tables/municipal_*.csv`: cell (R1) and municipal comparisons; cell fractions per
  municipality.
* `tables/processing_checks.csv`, `tables/check_v15_annual_over_BRAIN.csv`: BRAIN against the FINN v1.5 2019
  annual file processed with the finn2cmaq rules: 7 474 of 7 474 cell-days in common, ratio BRAIN / FINN v1.5 of
  1.0100 at the median and at the 5th and 95th percentiles. In this run the columns `share_within_1pct_of_factor`
  (0) and `expected_factor` (NaN) are empty because the notebook version used then expected the default layer
  fractions; the BRAIN files use 19 layers in a different shape (`logs/run_metadata.json`), and the current notebook
  takes the factor from this check (1.01).
* `tables/brain_cells_daily_t.csv.gz`: BRAIN daily emissions per cell (t), 7 474 cell-days
  (`tools/brain_cells_and_finn15_check.py --cells 2019 <cache_days>`).
* `tables/check_cell_days_R1_finn25.csv`: `tools/brain_cells_and_finn15_check.py --check2019`, BRAIN against FINN
  v2.5 MODIS and MODIS+VIIRS cell by cell in R1 (64.4 % and 66.8 % of BRAIN CO on cell-days with fire in the product),
  the control for the 2020 check in `../brain_2020/`, since in 2019 BRAIN equals the FINN v1.5 annual file x 1.01.
* `logs/header_first_file.json`: structure, attributes, variables and units of the first BRAIN file.
* `logs/time_profile_check.csv`: hourly profile recognised on each day with fire (finn2cmaq profile 210).
* `figures/`: cell fractions, monthly CO and PM2.5, daily CO, maps of CO per cell and municipal scatter.

These files are not part of `results/MANIFEST.sha256`, because they come from the BRAIN download and not from
`python/run_analysis.py`.

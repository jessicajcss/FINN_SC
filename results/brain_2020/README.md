# `results/brain_2020/`: comparison with BRAIN, 2020

Outputs of `notebooks/BRAIN_FINN_comparison_SC.ipynb` with `YEAR = 2020`, run in Google Colab on 2026-11-02 with
brain_core 1.1.0 and recomputed on 2026-11-03 with brain_core 1.1.1 from the cached daily BRAIN cells of that run,
without new downloads (log `logs/run_metadata.json`). Used in section S24 of the supplementary material (Tables S24c,
S24d and S24e), in the discussion of the article and in section 3.9 of the report.

BRAIN data set: Hoinaski et al. (2024), https://doi.org/10.5194/essd-16-2385-2024; 4 km domain of southern Brazil,
https://doi.org/10.57760/sciencedb.09886. The article states that the 2020 data were produced on the same grid with
FINN v2.5. The 2020 files keep the structure of 2019 (same species, 19 layers with the same relative shape, finn2cmaq
hourly profile 210 on all 311 days with fire in the window, no coarse-PM species), and their cell-days agree with
FINN v1.5, not with FINN v2.5 (`tables/check_cell_days_R1_finn15_finn25.csv`, below).

Days: 2020 has 366 days and the BRAIN list has 365 files (2020-05-24 is missing). The file of 2020-12-06 is on the
20 km d01 grid (257 x 247 cells); brain_core 1.1.1 rejects it, so the comparison uses 364 days, and the same days are
dropped from the FINN_SC records. In the 1.1.0 run that file had been read at wrong cells (0.34 % of the 2020 CO).

* `tables/annual_totals_and_ratios.csv`: annual totals (t) and ratios FINN v2.5 / BRAIN, region R1 (7 188 cells
  entirely inside SC) and R2 (whole State; BRAIN weighted by the cell fraction inside SC, with lower and upper bounds).
* `tables/monthly_*.csv`, `tables/daily_*.csv`: monthly and daily totals and correlations (daily Spearman with a
  moving-block bootstrap 95 % interval, blocks of 7 days, 2 000 resamples).
* `tables/cell_*.csv`, `tables/municipal_*.csv`: cell (R1) and municipal comparisons; cell fractions per municipality.
* `tables/same_version_check_R1.csv`: section 8e of the notebook, BRAIN against FINN v2.5 MODIS and MODIS+VIIRS cell
  by cell (no match: 65.0 % and 67.5 % of BRAIN CO on cell-days with fire in the product).
* `tables/brain_cells_daily_t.csv.gz`: BRAIN daily emissions per cell (t), 7 430 cell-days, written by
  `tools/brain_cells_and_finn15_check.py --cells 2020 <cache_days>`.
* `tables/check_cell_days_R1_finn15_finn25.csv`: `tools/brain_cells_and_finn15_check.py --check2020`, BRAIN against
  the FINN v1.5 records of 2020 inside SC (`data/external/finn15_2020_SC_records.csv`, area < 50 m2 dropped as in
  finn2cmaq) and FINN v2.5 MODIS and MODIS+VIIRS, in R1: 94.4 % of BRAIN CO on cell-days with FINN v1.5 fire,
  275 of 278 BRAIN fire days shared, median ratio 1.04 (5th to 95th percentile 0.12 to 5.95), total ratio 0.88.
  The control for 2019 is in `../brain_2019/tables/check_cell_days_R1_finn25.csv`.
* `logs/header_first_file.json`, `logs/time_profile_check.csv`, `logs/run_metadata.json`, `logs/failures.csv`.
* `figures/`: cell fractions, monthly CO and PM2.5, daily CO, maps of CO per cell and municipal scatter.

These files are not part of `results/MANIFEST.sha256`, because they come from the BRAIN download and not from
`python/run_analysis.py`.

# Data provenance

> 🌐 **English** · [Português (pt-BR)](provenance.pt-BR.md)

Every file read by the analysis layer is listed here with its origin, how it was produced, what was
changed, and its SHA-256 checksum (`sha256sum <file>`). Nothing in `data/` was typed by hand except
where stated. The checksums were checked against the files of this repository on 2026-11-01: every listed file that the repository distributes matches (23 of 24 checksums; the remaining one belongs to a GeoTIFF marked as not distributed).

## 1. FINN records of Santa Catarina — `data/derived/finn_sc_records_2003_2025.csv.gz`

| Item | Value |
|---|---|
| Content | 258 694 FINN "each fire" records (GEOS-Chem speciation) whose point lies inside one of the 295 IBGE 2024 municipalities of SC: MODIS v2.5 2003–2021 (102 788), MODIS v2.5.1 2022–2023 (6 224), MODIS+VIIRS v2.5 2012–2021 (115 183), MODIS+VIIRS v2.5.1 2022–2025 (34 499). FINN v1.5 is not included. |
| Columns | `year, sensor, version, DAY, POLYID, FIREID, GENVEG, LONGI, LATI, AREA (m²), BMASS (kg m⁻²), CO2, CO, CH4, NMOC, NOXasNO, SO2, NH3, PM25, PM10, OC, BC` (tonnes), `CD_MUN, NM_MUN` (IBGE 2024), `source_file` (name of the FINN file the record came from; 548 files). |
| Source | FINN v2.5 / v2.5.1 files from the NSF NCAR Research Data Archive, dataset ds312.9 (2003–2023; Wiedinmyer and Emmons, 2022, https://doi.org/10.5065/XNPA-AF09) and the NCAR near-real-time folder https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt/ (2024–2025). |
| Production | Downloaded and converted to tonnes by the authors' original scripts (Feb 2026 run; those scripts are not part of this repository, and route A, `python/00` to `02` and `06`, rebuilds the records, as `tests/test_route_a.py` shows), clipped to a box around SC (`filtered_points_grid.csv`), then restricted to the SC municipalities by point-in-polygon and written by `tools/build_records_from_legacy.py` (2026-10-03). Exact duplicate rows: 0. |
| Unit check | For all 11 species and every vegetation class, species / (AREA × BMASS) reproduces the emission factors of Wiedinmyer et al. (2023, Table 4) to within 0.3 % (ratios 0.9986–1.0026; `python/analysis/a09_emission_factor_check.py`). NMHC and the speciated VOCs, affected by the old conversion errors (CHANGELOG_2026-10-03.md), are not in this file and are not used. |
| Replication | Route A (maintained pipeline, steps 01, 02 and 06) applied to raw FINN v2.5.1 NRT records of 1 Jan–28 May 2025 reproduces the archived records for those days exactly (2 341 of 2 341 records; maximum relative difference 4 × 10⁻¹⁴; `tests/test_route_a.py`). The other product-years were not re-downloaded in this revision. |
| SHA-256 | `4e23e22344b795ade9ab877089187b169e963be027afc2e1e6abba3e0f01a8dd` |

## 2. Municipal boundaries — `data/inputs/SC_Municipios_2024.*`

IBGE *Malha Municipal* 2024, state of Santa Catarina (295 municipalities; SIRGAS 2000, EPSG:4674;
fields `CD_MUN`, `NM_MUN`, `AREA_KM2`, …). Copy of the file used by the authors
(`FINN_QUEIMADAS_072026/repo/raw_data/`). Source page:
https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html.
The `.dbf` has no `.cpg`; read it as cp1252/latin-1.

| File | SHA-256 |
|---|---|
| `SC_Municipios_2024.shp` | `0b37d4484f9606f905c140f31b78fcd7074312e7f62a6c949d757debb34574da` |
| `SC_Municipios_2024.dbf` | `d24f2863fccee0e9b82d70f73e8f9ac4776207f0e9e31344e59549981144c92b` |
| `SC_Municipios_2024.shx` | `479e72ef8c8a3a8c56252d48465782b3b0e4532fc50cc9b2ec619cc78b55cca5` |
| `SC_Municipios_2024.prj` | `b7fe68a2eb827ea974a1a995a73676e095a366b383a10a66c7498300d1c58153` |

## 3. Municipal attributes and mesoregions — `data/external/sc_municipios_2024_atributos.csv`

`CD_MUN, NM_MUN, AREA_KM2` copied from the IBGE 2024 `.dbf`; `mesorregiao` = IBGE (1990) mesoregion
(Grande Florianópolis 21, Norte Catarinense 26, Oeste Catarinense 118, Serrana 30, Sul Catarinense 46,
Vale do Itajaí 54 municipalities). The crosswalk was derived from the mesoregion polygons of the authors'
project layer (`aggregated_emissions_all_mesorregioes.shp`, field `Mesorregia`) by majority of 400 random
interior points per municipality (`wildfire/analysis/08_table3_and_mapping.py`, 2026-10-02).
**Open item:** confirm against the IBGE crosswalk (IBGE localities API,
`/api/v1/localidades/estados/42/municipios`, fields `microrregiao.mesorregiao`), which could not be
reached from the environment used for this revision.
SHA-256 `a2785b75ae6580429ef0d89444ebedc0221ddc05d055c1010c04fe956258f434`.

## 4. MapBiomas Fogo Collection 4 — `data/external/mapbiomas_fogo_col4_SC_municipal_km2_2012_2024.csv`

Annual burned area (km²) per municipality, 2012–2024 (3 835 rows = 295 × 13). Produced by the authors
with `gee/mapbiomas_fogo_col4_municipal.js` (asset
`projects/mapbiomas-public/assets/brazil/fire/collection4/mapbiomas_fire_collection4_annual_burned_v1`;
burned mask binarised before summing; area from `ee.Image.pixelArea()`; 30 m; IBGE 2024 mesh) on
2026-10-02. The raw Earth Engine export is kept in `data/external/raw/` (its `NM_MUN` has broken accents
in 110 names); the cleaned copy keeps `CD_MUN, year, burned_km2` and takes `NM_MUN` from the IBGE
attributes by `CD_MUN`. References: Alencar et al. (2022); MapBiomas (2025, ATBD of Collection 4).
**Do not use** the older extraction `repo/data/mapbiomas_fire_*_km2.csv` (class codes summed; 14.8–18.6×
too large; review round 2).
SHA-256 (clean) `b0c454b6ce5e654a5f88ff4e29682b2bb80dc8ecdeb841f5cb3ccc22f2d636a9`;
(raw) `06b2fa3af4f0a33cb3fe9a4517aad55ae7c03fd1e34aa52a507d0dff1d64dd00`.

## 5. Fire-season climate — `data/external/era5land_oni_SC_fire_season_2012_2025.csv`

Columns `year, precip_mm_fs, Tc_fs, VPD_kPa_fs, soil_moist_fs, ONI_fs` (July–November). Subset of
`raw/paper2_annual_drivers.csv`, produced by the authors' NotebookB (Google Earth Engine, ERA5-Land
monthly aggregates; NOAA CPC ONI); the recipe is transcribed in `gee/era5land_oni_fire_season.py`.
The SPI column of the raw file is not used (series shorter than the 30 years required; Svoboda et al.,
2012). **Open item:** the access date of the ONI file. SHA-256
`53d18faa8cddfc508c28739cd5b5d412075bf9946b7273f03307045c1d701849`.

## 6. Land-cover fractions — `data/external/mapbiomas_lulc2023_SC_municipal_fractions.csv` (PROVISIONAL)

Fractions of forest, grassland, pasture, agriculture and silviculture in 2023 for **277** municipalities
(those with FINN records in 2025), from `raw/paper2_municipal_landuse_emissions.csv` (only the land-cover
columns are kept; the emission columns of that file used the superseded definitions). Recipe:
`gee/mapbiomas_lulc_fractions.py`. **Open items:** (i) rebuild for all 295 municipalities (the NotebookB
checkpoint `municipal_landuse.csv` on the authors' Google Drive); (ii) record the MapBiomas collection
behind the `lulc/v1` asset. Both are resolved by `gee/mapbiomas_lulc_fractions_all295.ipynb`, which writes
`data/external/mapbiomas_lulc2023_SC_municipal_fractions_all295.csv` (295 municipalities, IBGE code, collection
and version of the image) and is used by `a07` when present. Results that use this file (land-cover Spearman and spatial error models)
must be re-run when the full file is available. SHA-256
`29bbb14d615986a0969ec4537ce99ea1bb14e3d315cbe7598056a2d442dd18c4`.

## 6a. Land-cover fractions, all 295 municipalities — `data/external/mapbiomas_lulc2023_SC_municipal_fractions_all295.csv`

Written by `gee/mapbiomas_lulc_fractions_all295.ipynb`, run by the authors in Google Colab on 2026-10-07 (executed
copy: `gee/mapbiomas_lulc_fractions_all295_run_2026-10-07.ipynb`). Asset `projects/mapbiomas-public/assets/brazil/lulc/v1`,
image of 2023; the asset holds collections 10, 10.1 and 11 for 2023, and the image used (`first()`, as in the archived
run) is **Collection 10.1** (`collection_id` = 10.1, version v1). Municipal polygons: geobr 2022 (295; codes identical to
the IBGE 2024 attribute file). The 277 municipalities of the provisional file are reproduced to floating-point
precision (maximum difference 2.8 × 10⁻¹⁵), so the provisional file also came from Collection 10.1. Used by `a07`
(merge on the IBGE code). SHA-256 `f8ca0995f3574224261e76e11c42af959d45e35c7268459d1159cb016df17654`
(`tests/test_round6.py`).

## 7. Legacy bounding-box counts — `data/external/legacy_bbox_record_counts.csv`

Number of records per product-year in the authors' legacy `filtered_points_grid.csv` (box around SC used
by the original scripts), counted on 2026-10-03; used only for the pipeline diagnostic "share of the box
records that fall inside SC" (report, Appendix A). SHA-256
`cd16d4a44f552e0fe088f362ba06a0e4d32a723858c4e0b49b1db97efbd75e2c`.

## 8. Route-A test input — `tests/data/raw_2025_subset_v2.5.1_MODIS+VIIRS.csv.gz`

Raw FINN v2.5.1 NRT records (native units; format written by step 00) of DAY 1–148 of 2025 (147 daily
files of the NCAR NRT folder): every record of those days inside SC plus a sample of records elsewhere.
SHA-256 `ad67e2f09c8cbc2d009936a02c3f8d83c2a0c6fe4d176433b9aa3d012912eede`.

## 9. 2020 state inventory and FINN v1.5 — `data/external/legacy_finn15_lcqar_2020.csv`

Two rows. `lcqar_2022_report`: the 2020 totals of the state inventory of biomass burning (LCQAR, 2022;
Tabela 11 and the text that follows it: 4 625 *focos de calor*, CO₂ 12 909 573 t, CO 699 668 t, PM₂.₅
70 724 t, NOx 38 037 t), **typed by hand** from the report. The report describes FINN with MODIS detections
(MOD14/MYD14) and the static land-cover maps of FINN v1 and counts each FINN record as a *foco*.
`finn15_sc_records`: the FINN v1.5 (MODIS) records of 2020 whose point lies inside an IBGE 2024 municipality of
SC, from the authors' legacy `filtered_points_grid.csv` (February 2026 run), summed by
`wildfire/analysis/verify_r2/v04_state_series.py` (2026-10-02; output `v04_state_by_year_sensor_version.csv`):
4 609 records, CO₂ 12 883 690.6 t, CO 698 281.3 t, PM₂.₅ 70 585.7 t, NO + NO₂ 37 961.8 t (v1.5 has no
NOXasNO field), area 4 134.6 km²; the 4 609 records fall on 4 609 distinct combinations of day and coordinates, i.e., one record per MODIS detection; 50.2 % of the area and 87.3 % of the CO₂ carry vegetation code 3 and 0.4 % of the area code 4 (counted on 2026-10-06). `tools/legacy_finn15_2020.py` recomputes the row from the legacy file (re-run on 2026-10-06 with identical values). The FINN v1.5 records themselves are not distributed (§1). The file is not
read by the analysis; `tests/test_round5.py` uses it to check that the two rows agree to within 0.4 % and to
compare them with the FINN v2.5 totals of 2020 computed from §1. SHA-256 `e8221ec1dc26d0ab0d59fae76215129ba261ff35c3a758effeaf4c4a4d4ec92e`.

## 10. Study-area figure — MapBiomas land use and land cover 2019 and IBGE outlines

* `data/external/mapbiomas_c10_lulc2019_SC_120m.npz`: Santa Catarina window of MapBiomas Collection 10, year 2019
  (`brazil_coverage_2019.tif`, authors' copy in `inventario/MAPBIOMAS/MEGAN_Fortran_to_R_122025/data/MapBiomas/`), read at
  ~120 m (4 × the native 30 m) by `tools/extract_mapbiomas_sc.py` on 2026-10-06. The authors' copy of the GeoTIFF is
  incomplete at full resolution (tiles south of about 25.9° S cannot be read, consistent with an interrupted download),
  but its internal overviews are complete, and the window was read from them. SHA-256 `45ee0b64258163b30b445686606f3a33c33b4ecac1b1d64f3031c4f896e5c947`.
* `data/external/mapbiomas_c10_lulc2019_SC_class_areas.csv`: class areas inside the state (IBGE 2024 limit) from the
  60 m overview, pixel areas by latitude on the authalic sphere; shares of the classified area (class 0, about 436 km²
  of coastal water inside the IBGE limit, excluded). Shares at 60 m and 120 m agree to within 0.02 percentage points.
  SHA-256 `be8f4009eb139988abb728fd29e32266b0a19745a46e9daecaf466f3592facdb`.
* `data/external/ibge_br_uf_2024_simplified.geojson` (IBGE BR_UF_2024, simplified at 0.01°) and
  `data/external/ibge_america_do_sul_2021_simplified.geojson` (IBGE Lim_america_do_sul_2021, simplified at 0.02°):
  context layers of the figure. SHA-256 `116bb7f2199da9ac5ec230ed17533bbd36891eb086ea2a626e4c1832ca098d87` and `42dd4d114e4deb9e75e88a76a79a3933a4b05528feb08e8e6f5bf68636dbb288`.
* Figure: `tools/study_area_map.py` → `results/figures/Fig01_study_area_pt.png` (Portuguese; manuscript Figure 1) and
  `Fig01_study_area_en.png` (English). Open item: replace 2019 by the year of the land-cover analysis (2023) or the latest year (2024) when the
  complete file is available.

## 11. FINN v1.5 records of 2020 and Earth Engine notebooks of the co-authors' review

* `data/external/finn15_2020_SC_records.csv`: the FINN v1.5 rows of 2020 (version field `v1.5`) of the authors'
  `filtered_points_grid.csv` (run of February 2026; `2026--output/filtered_points_grid.csv`, 14 849 rows of the
  processing grid), clipped to Santa Catarina by point in polygon on the IBGE 2024 mesh on 2026-10-19: 4609 records,
  12 883 690.6 t of CO2 and 4134.6 km2, the totals of section 2 (`legacy_finn15_lcqar_2020.csv`).
  SHA-256 `9412bca12193626e747f0e839099b4a7d3a0d8f0c1d45ca00c5223c0c45c86bc`.
* `gee/mcd64a1_municipal_2012_2024.ipynb`, `gee/era5land_serrana_monthly.ipynb` and `gee/mapbiomas_lulc2023_figure1.ipynb`:
  run by the authors in Colab on 2026-10-21 (section 12).

## 12. Outputs of the Earth Engine notebooks

Run by the authors in Google Colab on 2026-10-21 (Earth Engine project `ee-jessicajcss`); the executed notebooks are
archived as `gee/*_run_2026-10-21.ipynb`. Municipal polygons sent to Earth Engine: `gee/SC_municipios_2024_simplified.gpkg`
(IBGE 2024 mesh, coverage simplification at 0.0005°, area change per municipality ≤ 0.07 %; `tools/simplify_municipios_for_gee.py`).

* `data/external/mcd64a1_SC_municipal_km2_2012_2024.csv`: MODIS Collection 6.1 burned area (`MODIS/061/MCD64A1`, band
  `BurnDate` > 0 in any month of the year, area by `ee.Image.pixelArea()` summed over each municipality in the native
  sinusoidal grid, ~463 m); 295 municipalities × 13 years, 12 monthly images per year. SHA-256
  `48f3c2f94005cdd392c38d2d99d4668a1fa8fb1e788edfd1b33f3b6bd89d7ef4` (identical to the value printed in Colab).
* `data/external/era5land_SC_serrana_monthly_2012_2025.csv`: ERA5-Land monthly aggregates (`ECMWF/ERA5_LAND/MONTHLY_AGGR`)
  averaged over the State and over the union of the 30 municipalities of the Serrana at 11 132 m, 2012-2025 (168 months
  each). The State July-November values reproduce the archived file of section 6 (geobr 2022 polygon) to within
  0.013 mm of precipitation. SHA-256 `f459206e2eb413ffb87376fe1322d5f21a5fff02569e309b9381f5fca7d496e9`.
* `brazil_coverage_2023_SC.tif` (not distributed): MapBiomas land use and land cover, asset
  `projects/mapbiomas-public/assets/brazil/lulc/v1`, first image of 2023 (Collection 10.1, version v1, the image of the
  land-cover analysis of section 2.8 of the manuscript), exported in its native grid over the State bounds ± 0.05°
  (20 815 × 13 094 pixels, LZW). SHA-256 `289c8493fba444c555221b5491894a2f186c96e6a594c93a4c415206da49d6d8`.
* `data/external/mapbiomas_c10_lulc2023_SC_120m.npz`: `tools/extract_mapbiomas_sc.py` on that file with FACTOR 4 on
  2026-10-21; same window and affine as the 2019 file. SHA-256 `801879a0254e401cc07d885ef583f909cb800bbbc14a9c4879f8beba581a1663`.
* `data/external/mapbiomas_c10_lulc2023_SC_class_areas.csv`: class areas inside the State at ~60 m (cell 7 of the
  notebook, run inside the repository; pixel areas by latitude on the authalic sphere). The same method applied to the
  2019 window reproduces the 2019 shares to within 0.01 percentage points. Class 75 (Usina fotovoltaica, beta) named
  from the Collection 10 legend. Collection 10.1 differs from Collection 10 in a few small classes (rocky outcrop
  48 km² in 2019, 0.02 km² in 2023; herbaceous sandbank vegetation 0.04 and 27 km²; class 0 inside the IBGE limit 436 and
  230 km²). SHA-256 `830bf811f245cf7c68b6443b20aca872b2f28b856d30a65704101270f20f672d`.
* Figure 1: `tools/study_area_map.py` with the 2023 files (default); `FIG1_YEAR=2019` reproduces the
  previous figure and `results/tables/landcover2019_mesoregion.csv` byte for byte.

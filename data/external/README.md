# `data/external/` — non-FINN inputs of the analysis layer

| File | Content | Provenance (docs/provenance.md) |
|---|---|---|
| `sc_municipios_2024_atributos.csv` | `CD_MUN, NM_MUN, AREA_KM2` (IBGE 2024) and `mesorregiao` (IBGE 1990) for the 295 municipalities | section 3 |
| `mapbiomas_fogo_col4_SC_municipal_km2_2012_2024.csv` | MapBiomas Fogo Collection 4 burned area per municipality and year (km²) | section 4 |
| `era5land_oni_SC_fire_season_2012_2025.csv` | ERA5-Land July–November precipitation (mm), 2 m temperature (°C), VPD (kPa), soil water (m³ m⁻³); mean ONI of JAS, ASO, SON | section 5 |
| `mapbiomas_lulc2023_SC_municipal_fractions.csv` | MapBiomas 2023 fractions (0–1) of forest, grassland, pasture, agriculture, silviculture — **provisional, 277 municipalities** | section 6 |
| `finn15_2020_SC_records.csv` | the 4609 FINN v1.5 records of 2020 inside SC (DAY, POLYID, FIREID, GENVEG, AREA, BMASS, CO2, CO, PM25, LONGI, LATI, NM_MUN); used by a11 (v2.4.0) | section 11 |
| `mcd64a1_SC_municipal_km2_2012_2024.csv` | MCD64A1 C6.1 burned area (km²) by municipality and year, 2012-2024 (CD_MUN, NM_MUN, year, burned_km2); used by a12 (v2.5.0) | section 12 |
| `era5land_SC_serrana_monthly_2012_2025.csv` | ERA5-Land monthly precipitation, temperature, vapour-pressure deficit and soil moisture of the State and of the Serrana, 2012-2025; used by a12 (v2.5.0) | section 12 |
| `mapbiomas_c10_lulc2023_SC_120m.npz` | MapBiomas Collection 10.1, 2023, State window at ~120 m (Figure 1 since v2.5.0) | section 12 |
| `mapbiomas_c10_lulc2023_SC_class_areas.csv` | class areas inside the State, 2023, at ~60 m (Figure 1 legend; a12) | section 12 |
| `legacy_bbox_record_counts.csv` | records per product-year in the legacy box file (pipeline diagnostic) | section 7 |
| `ibge_sc_municipal_pop2022_gdp2021_2023.csv` | resident population (2022 Census, SIDRA table 4709), GDP 2021 and 2023 and gross value added 2021 by activity (SIDRA table 5938) of the 295 municipalities; read with a browser on 8 Nov 2026 (the header lines give the queries and the state and national totals); used by a17 (v2.6, manuscript v7.2) | section 12 |
| `comexstat_SC_municipios_2025.xlsx` | exports of Santa Catarina in 2025 by municipality, month and HS4 heading (US$ FOB, net kg), exported by the authors from Comex Stat (MDIC/SECEX, https://comexstat.mdic.gov.br) on 8 Nov 2026; Comex Stat assigns each export to the municipality of the tax domicile of the exporting company; used by a18 (v2.6, manuscript v7.2) | section 12 |
| `raw/` | the files as received (Earth Engine export, NotebookB outputs), kept for traceability | sections 4–6 |

## teixeira2025_tableC1_SC_finn15.csv (added 2026-11-09)

Annual fire emissions of Santa Catarina (t yr-1) from FINN v1.5, 2002-2017, transcribed from Table C.1 of the
supplementary material of Teixeira et al. (2025), Air Quality, Atmosphere & Health 18, 953-970,
https://doi.org/10.1007/s11869-024-01681-5 (file `refs/teixeira et al 2024.docx`, Appendix C; the table is a vector
image, read with pdftotext after conversion to PDF). Thousands separators removed. Check: the means of the 16 years
reproduce the "Average" row of the table (CO2 7,818,193; CO 418,649; PM2.5 42,173 t). Column "Nox" kept as NOx_t
(the paper does not state whether NOx is expressed as NO or NO2).

## finn15_SC_records_2002_2020.csv and finn15_SC_records_2002_2020_files.csv (added 2026-11-09; 2002, 2016 and 2017 added 2026-11-11)

FINN v1.5 (MODIS, GEOS-Chem) records inside the 295 IBGE 2024 municipalities of SC, 2002-2020, written by
`tools/finn15_records.py`. Sources: (1) the authors' per-year files `data_finn_<year>/filtered_points_<year>_MODIS_v1.5_
converted_within_grid*.txt` (original R scripts, June 2025; uploaded on 9 Nov 2026; species in tonnes, AREA in m2), for
2003-2015 and 2018-2020; (2) for 2002, 2016 and 2017, the NCAR annual files `FINNv1.5_<year>.GEOSCHEM.tar.gz`
(https://www.acom.ucar.edu/Data/fire/, downloaded by the authors on 11 Nov 2026; members `GLOBALv15_2002_GESOCHEM_
07142014.txt`, `GLOBAL_FINNv15_2016_GEOSCHEM_09022018.txt`, `GLOBAL_FINNv15_2017_GEOSCHEM_01022019.txt`), cut to the grid
box and converted to tonnes by `tools/finn15_raw_to_grid.py`. The authors' file of 2002 is missing and those of 2016 and
2017 are byte-identical to the 2015 file. The same conversion of the NCAR 2015 file (`GLOBAL_FINNv15_2015_GEOSCHEM_
11032016.txt`) reproduced all 3,537 rows of the authors' 2015 file (relative differences below 1e-14) and gives the same
860 records and CO2 in SC (columns check_* of the file table). The file table lists, for each year, the source, the
SHA-256, lines, header, malformed and duplicate lines, records in the grid box and in SC, and the SC CO2. 2009: the
authors' file repeats a block of 7,641 lines and has its header in the middle; exact duplicate lines and one truncated
line were dropped. Check: the SC CO2 equals Table C.1 of Teixeira et al. (2025) to the tonne in 15 of the 16 years of
2002-2017 (2010: 0.01% above); in 2016, Table C.1 is 0.36% below the sum of the records of the NCAR file (cause not
identified). The 2019 and 2020 totals equal finn15_2019_SC_records.csv and finn15_2020_SC_records.csv.

## legacy_aggregated_emissions_all_2026-02-05.csv (added 2026-11-09)

Copy of the authors' `aggregated_emissions_all.csv` (original R scripts, 5 Feb 2026; municipality x year x sensor x
version). Checked in `a20_finn15_correction.py`, part 6; it is not an input of any result of the article.

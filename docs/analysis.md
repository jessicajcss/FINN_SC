# Analysis layer: methods

> 🌐 **English** · [Português (pt-BR)](analysis.pt-BR.md)

This document describes how `python/analysis/` and `R/analysis/` turn the FINN records of Santa
Catarina into every table, statistic and figure of the manuscript (v5) and of the inventory report
(v2). Provenance of each input: [`provenance.md`](provenance.md). Where each number is printed and
which test checks it: [`results_map.md`](results_map.md).

## 1. Two routes

```
Route A (replication from raw FINN)                    Route B (reproduction from the archive)
python/00_download_finn.py   raw FINN files            data/derived/finn_sc_records_2003_2025.csv.gz
python/01_convert_units.py   -> tonnes                          |
python/02_clip_region.py     -> points inside SC                v
python/06_build_sc_records.py -> record table  ---->  python/run_analysis.py
                                (compare: tools/compare_records.py)   a01 ... a09 (Python), kde_events.R (R), a10 (figures)
                                                                       -> results/tables, results/figures, results/logs
                                                       python -m pytest -q tests
```

Route A needs internet access and several GB of FINN files; it was validated on raw FINN v2.5.1 NRT
records of 1 January to 28 May 2025 (`tests/test_route_a.py`). Route B needs only this repository.

## 2. Units and species

FINN v2.5/v2.5.1 "each fire" files give gases in mol day⁻¹, aerosols (OC, BC, PM2.5, PM10) in kg day⁻¹,
and the aggregate fields NOXasNO, NMOC and NMHC in kg day⁻¹ (the README sentence "all gas-phase species
in mole/day" does not hold for these three; the implied emission factors match Wiedinmyer et al., 2023,
Table 4, only when they are read as mass). All species are converted to tonnes (`config/config.yml`,
section `conversion`). In the results, **NOx = NOXasNO** (NOx expressed as NO mass; × 46.0055/30.0061 for
NO₂-equivalent) and **COV (VOC) = NMOC** (identified and unidentified non-methane organic gases;
Wiedinmyer et al., 2023, Table 4, note e). NO and NO₂ are never summed and the speciated VOCs are never
summed (they overlap NMOC). `a09_emission_factor_check.py` verifies the conversion on every archived
record: species / (AREA × BMASS) = Table 4 emission factor (ratios 0.9986–1.0026).

## 3. Counting units

| Unit | Definition | 2025 (MODIS+VIIRS, SC) |
|---|---|---|
| record | one row of the FINN file = one (FIREID, GENVEG) piece | 8 581 |
| detection | distinct (year, sensor, version, DAY, FIREID): one coordinate | 5 489 |
| fire event (*evento de queimada*) | distinct (year, sensor, version, DAY, POLYID): FINN daily burned-area polygon | 5 160 |

FINN merges adjacent or overlapping detections of the same day into one burned-area polygon and splits
each polygon by land-cover class (Wiedinmyer et al., 2023, Sect. 2.2). In the files analysed, POLYID
identifies the daily polygon and FIREID the detection (the README wording is the reverse; verified on the
SC records: 5 of 151 441 FIREIDs have more than one coordinate, 20 766 of 124 602 POLYIDs hold more than
one FIREID). The pieces of a detection share the detection's area, so the subdivision changes counts but
not emissions. Each event is assigned to the municipality that holds the largest share of its AREA (ties:
alphabetical order), so municipal counts add up to the state total; 0.8 % of the 2012–2025 events had
records in more than one municipality. The former *focos* of the draft counted records.

## 4. Persistent thermal anomalies

The MODIS C6/C6.1 active-fire product classifies as static sources the locations detected on 16 or more
days of a calendar year (Giglio et al., 2021, Sect. 5.5, Table 10), and not every static source is
flagged in the product (Sect. 7.2.3). The criterion is applied without a grid: for each detection, the
number of distinct days with detections within 1 km (great-circle distance; KD-tree on the unit sphere,
chord ≤ 2 sin(R/2R_E)) in the same product-year; a detection with ≥ 16 days is flagged, and an event with
any flagged detection is flagged. Sensitivity radii: 0.75 km and 1.5 km. Flagged events are excluded from
event counts, maps and the driver analyses, and kept in area and emission totals (the inventory as
distributed). Implementation: `finn_sc/events.py::flag_persistent`; identical flags to the brute-force
haversine implementation used for the manuscript (281 events).

## 5. Time series and trends (`a02`)

State totals by product-year from all records; events after screening. The MODIS+VIIRS series (v2.5
2012–2021, v2.5.1 2022–2025) is analysed; the MODIS-only series illustrates the effect of adding VIIRS
(ratio of events; % change of area and emissions, same version and year). Monotonic trends: Mann–Kendall
test with tie correction, normal approximation and continuity correction (Mann, 1945), Sen slope (Sen,
1968), for 2012–2025 and 2012–2021 (`finn_sc/stats.py`). The lag-1 autocorrelation r1 of each
series is reported (`mann_kendall.csv`, column `r1`; 0.11 to 0.22 for 2012–2025): positive serial correlation
makes the test reject more often when there is no trend (Hamed and Rao, 1998), so non-significant results do not
depend on the independence assumption.

## 6. Municipal and mesoregion results (`a03`)

Emissions and burned area by municipality: every record assigned to the municipality that contains its
point (IBGE 2024). Events: screened events assigned as in section 3. Mesoregions: IBGE (1990), crosswalk
in `data/external/sc_municipios_2024_atributos.csv` (open item in provenance.md, section 3). Densities use
the IBGE `AREA_KM2`. FINN burned area is a sum of daily nominal detection areas (1 km² MODIS, 0.14 km²
VIIRS, merged per day) and can count the same ground more than once; it exceeds the mapped burned area by a
median factor of 17 (section 8), so municipal "% of territory" values are relative indicators.

## 7. Vegetation partition (`a04`)

Area, CO₂ and PM2.5 by FINN generic vegetation type (GENVEG; Wiedinmyer et al., 2023, Table 1). Burned
biomass per unit area = CO₂ / (AREA × EF_CO₂) (equal to the FINN field BMASS; both are written).

## 8. FINN vs MapBiomas Fogo (`a05`)

State and municipal FINN area (MODIS+VIIRS) vs MapBiomas Fogo Collection 4 mapped area (2012–2024):
ratios, Pearson and Spearman correlations (with and without 2012, the only year mapped with Landsat 7 only),
municipal Spearman per year, shares of the ten municipalities with the largest mapped area, and mapped
area per FINN event by municipality (used in the report to test whether a high CO₂ per event corresponds to
larger mapped scars).

## 9. Climate (`a06`)

Fire-season (July–November; 72.1 % of the 2012–2025 events) ERA5-Land state means (precipitation sum,
2 m temperature, VPD from Tetens, soil water 0–7 cm; Muñoz-Sabater et al., 2021) and mean ONI of JAS, ASO
and SON. Spearman ρ between each predictor and each response (events, FINN area, CO₂, MapBiomas area),
in levels and first differences; Holm (1979) adjustment over the five predictors of each response. The SPI
is not used: fitting it needs at least 30 years of monthly data (Svoboda, Hayes and Wood, 2012) and,
being a monotonic transform of the precipitation of the same period, it has the same Spearman ρ.

## 10. Land cover (`a07`)

MapBiomas 2023 fractions (Souza Junior et al., 2020) per municipality (provisional file, 277
municipalities; provenance.md, section 6; the file of all 295 municipalities written by
`gee/mapbiomas_lulc_fractions_all295.ipynb` is used, merged on the IBGE code, when present). Responses: mean annual density of screened events 2012–2025;
density in 2025; MapBiomas burned fraction; CO₂ per event 2012–2025 (municipalities with ≥ 14 events).
Spearman correlations; OLS (White SE) of the log response (log y; municipalities
with zero density are excluded and listed in the log) on grassland, pasture, agriculture and
silviculture (forest and other classes = reference); spatial error model by maximum likelihood (Anselin,
1988; spreg, Rey and Anselin, 2007) with 6-nearest-neighbour and queen weights; Moran's I of the OLS
residuals and of the SEM filtered residuals (999 permutations, seed 20261003); AIC of both models. Effect of
+10 percentage points = exp(0.1 b) − 1.

## 11. Kernel density (`R/analysis/kde_events.R`)

Events of 2025 (screened) as points at the centroid of their detections, SIRGAS 2000 / UTM 22S, SC window,
Gaussian kernel, Jones–Diggle edge correction (Diggle, 1985; Jones, 1993), 1 km pixels, density in events per
100 km² (its integral equals the number of events). Bandwidth by likelihood cross-validation (bw.ppl; Loader,
1999); sensitivity with bw.CvL (Cronie and van Lieshout, 2018), Scott's rule, bw.diggle and fixed 2, 4, 8 km
(spatstat; Baddeley, Rubak and Turner, 2015). Run R in a UTF-8 locale (e.g. `LC_ALL=C.UTF-8`) so that
accented mesoregion names are written correctly.

## 12. Report indicators (`a08`)

Coefficient of variation of the annual CO₂ (sample SD); Gini index of municipal CO₂ (Lorenz form; with and
without the municipalities without emissions); CO₂ and FINN area per screened event by municipality, with the
FINN temperate-forest share; CO₂ per event by dominant vegetation class; share of the legacy box records that
fall inside SC.

## 12a. Figures (`a10`)

Figure numbers of manuscript v3.2 (the inventory report numbers them one lower; files in
`docs/results_map.md`). Maps in SIRGAS 2000 geographic coordinates with the state outline only (municipal outlines
are not drawn; Figure 5 also draws the mesoregion outlines), scale bar over the Atlantic in the bottom-right
corner with the north rose above it (`finn_sc/cartography.py`; in Figure 7, in the bottom-right panel) and the note on
the data below the frame. Figures 3 and 6 use classes with rounded limits.
Figure 7 (ten pollutants, 2025) uses Fisher–Jenks natural breaks (`mapclassify.FisherJenks`, k = 5) computed on the
municipalities with emission of each pollutant; classes include their upper limit, and municipalities without
records are hatched. The limits are written to `results/logs/a10_figures.txt`.

Labels (layout revision of 2026-10-16): the mesoregion names of Figure 4, the label of the persistent anomaly in
Figure 5 and the year labels of Figures S1 and S2 are placed by `finn_sc.figcheck` at the first candidate position
inside the map or plot frame that touches no boundary line, marker, data point or other label; every figure, Figure 1 included
(`tools/study_area_map.py`), is then checked again, legends, colour bars, north roses, scale bars and notes
included, and the result is printed as `LAYOUT ...` on the screen.

## 13. Tests

`tests/test_stats.py`, `test_events.py`, `test_units.py` (unit tests with analytical answers);
`test_results_golden.py` (every published number, with its published rounding); `test_report_v2.py` (numbers printed only in the inventory report v2); `test_round5.py` (values added in the manuscript v6 and the report v3: counting units, comparison with the 2020 state inventory and FINN v1.5, kernel density in the far west and on the north coast, Figure 6 classes, study-area land-cover shares); `test_route_a.py` (raw FINN →
archived records). Run: `python -m pytest -q tests` after `python python/run_analysis.py`.

## 14. Limitations that remain

* mesoregion crosswalk not checked against IBGE's API; ONI access
  date not recorded (provenance.md).
* Route A was re-run only for January–May 2025; the archived records of the other product-years come from the
  authors' February 2026 download.
* FINN area and emissions carry a large uncertainty in absolute terms (median 17 × the mapped area); relative
  comparisons between years and municipalities are more robust than totals.
* The vegetation class used by FINN (MODIS IGBP; Wiedinmyer et al., 2023, Table 1) does not separate planted
  from native forest, so the land-cover associations describe how the inventory distributes emissions and not
  fire behaviour.

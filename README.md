# FINN_SC: biomass-burning emissions of Santa Catarina, Brazil

> 🌐 **English** · [Português (pt-BR)](README.pt-BR.md)

Code, data and documentation that reproduce the tables, statistics and figures of the article *Variabilidade
espaço-temporal das emissões da queima de biomassa em Santa Catarina (Brasil) entre 2012 e 2025* (spatio-temporal
variability of biomass-burning emissions in Santa Catarina, Brazil, 2012-2025) and of the 2025 state inventory report
of biomass-burning emissions. Both build on the Fire INventory from NCAR (FINN; Wiedinmyer et al., 2011, 2023). The
same code builds a FINN inventory for any other region.

* **Address:** https://github.com/jessicajcss/FINN_SC (a Zenodo DOI will replace this address before publication).
* **Contact:** J. C. dos Santos Silva, jessica.jcss@gmail.com.
* **Licence:** code and documentation under the [MIT](LICENSE) licence. Data follow the terms of their providers
  (FINN/NSF NCAR, MapBiomas, IBGE, NASA LP DAAC, ERA5-Land/Copernicus, NOAA).
* **Illustrated tutorial:** [`TUTORIAL_FINN_SC_en.pdf`](TUTORIAL_FINN_SC_en.pdf) (English) and
  [`TUTORIAL_FINN_SC_pt.pdf`](TUTORIAL_FINN_SC_pt.pdf) (Portuguese), from concepts to commands, including a step-by-step
  run in Google Colab with an Earth Engine project (chapter 12).

---

## Three steps

```bash
git clone https://github.com/jessicajcss/FINN_SC.git
cd FINN_SC

# 1. Install (once)
conda env create -f environment.yml && conda activate finn   # or: python -m pip install -r requirements.txt
Rscript install_r_packages.R                                  # R, only for the kernel density (optional)

# 2. Reproduce the results (route B, no download)
python python/run_analysis.py --no-r     # without --no-r it also runs R (the annual sensitivity takes about 40 min)

# 3. Check
python -m pytest -q tests                # expected: 96 passed
python tools/verify_manifest.py          # expected: 107 files: OK 107
```

Shortcuts: `make reproduce`, `./run_all.sh analysis` (Linux, macOS) or `run_all.bat analysis` (Windows). Outputs go
to `results/tables/`, `results/figures/` and `results/logs/`. The copies kept in the repository are the published
outputs, and `tools/verify_manifest.py` compares yours with them by SHA-256 (`results/MANIFEST.sha256`).

## Two routes

| Route | Starts from | Use it to |
|---|---|---|
| **B, reproduction** | `data/derived/finn_sc_records_2003_2025.csv.gz` (258,694 FINN v2.5 and v2.5.1 records in SC, 2003-2025) and `data/external/` | recompute every number of the article and of the report, offline |
| **A, replication** | FINN files downloaded from NSF NCAR (`python/00` to `02` and `06`) | rebuild the records or build the inventory of another region; `tests/test_route_a.py` replicates the 2,341 records of 1 January to 28 May 2025 |

## Definitions used throughout

* **Record:** one row of a FINN file.
* **Detection:** a day and `FIREID` combination, one active-fire satellite pixel.
* **Fire event:** a FINN daily burned-area polygon (`POLYID`), assigned to the municipality holding most of its area.
* **Persistent thermal anomaly:** a location with detections on 16 or more days of a calendar year within 1 km (the
  MODIS product criterion; Giglio et al., 2021). Removed from counts and maps, kept in the emission totals.
* **NOₓ** = `NOXasNO` (mass of NO). **VOC** = `NMOC`. Emissions in tonnes.

## FINN files: differences from the NCAR README and model conventions

This code follows the FINN files where they differ from the README that NSF NCAR distributes with FINN v2.5
(June 2024; `docs/README_FINNv2.5_June2024.pdf`; Wiedinmyer and Emmons, 2022), and users of FINN should know two model conventions that change regional counts:

* **Units of the aggregate fields.** The README gives gas-phase species in mol day⁻¹, but in the GEOS-Chem files of
  v2.5 and v2.5.1 `NOXasNO`, `NMOC` and `NMHC` are in kg day⁻¹: only then do the emission factors implied by these
  fields match Table 4 of Wiedinmyer et al. (2023). Read as moles, NOXasNO would be about 33 times too low and NMHC about
  14 times too low. `python/finn_sc/convert_units.py` treats the three fields as masses, and
  `python/analysis/a09_emission_factor_check.py` checks every species (`results/tables/emission_factor_check.csv`).
* **Identifiers.** The README describes `POLYID` as the identifier of each fire point and `FIREID` as the fire to which
  points belong. In the files, each `FIREID` has one coordinate (151,436 of 151,441 by product and day) and a `POLYID`
  groups several `FIREID`s (20,766 of 124,602). Detections and fire events follow the files.
* **Next-day repetition.** FINN v1.5 counts each MODIS detection between about 30° N and 30° S also on the next day, at
  half its emissions, unless the pixel is detected again (Wiedinmyer et al., 2011): 1,893 of the 4,609 FINN v1.5 records
  of Santa Catarina in 2020 are such continuations (`python/analysis/a17_v72_review.py`). FINN v2.5 counts fires for two
  days only between about 23.5° N and 23.5° S (Wiedinmyer et al., 2023), outside Santa Catarina; for regions inside that
  band, records, detections and events include repetitions that this code does not separate.
* **Forest class by latitude.** FINN v2.5 classes evergreen broadleaf and mixed forests outside about 23.5° N to 23.5° S
  as temperate forest (Wiedinmyer et al., 2023, Table 1). With the South American fuel loadings and the emission factors
  of tropical forest, each forest detection of Santa Catarina would emit 3.9 times more CO₂, and the state 2.42 to 2.74
  times more CO₂ per year (`python/analysis/a19_v72_followup.py`). The emission-factor check cannot reveal this choice.

## Where things are

```
FINN_SC/
├── README.md, README.pt-BR.md        this page (EN / PT)
├── TUTORIAL_FINN_SC_en.pdf, _pt.pdf  illustrated tutorial (EN / PT; sources in docs/tutorial_v2/)
├── CITATION.cff, LICENSE, CHANGELOG.md, REFERENCES.md, references.bib
├── requirements*.txt, environment.yml, install_r_packages.R, Makefile, run_all.sh, run_all.bat
├── config/config.yml                 every parameter (years, version, sensor, region, molar masses)
├── data/derived/                     archived FINN records of SC (route B input)
├── data/external/                    MapBiomas, MCD64A1, ERA5-Land, ONI, IBGE, 2020 inventory
├── data/inputs/                      IBGE 2024 municipal mesh of SC
├── python/00_… 06_*.py               route A in Python
├── python/analysis/a01_… a20_*.py    route B, one script per group of results
├── python/finn_sc/                   shared functions (units, dates, events, statistics, maps)
├── python/run_analysis.py            route B in one command
├── R/                                route A in R and the kernel density (R/analysis/kde_events.R)
├── gee/                              Google Earth Engine recipes for the external data
├── notebooks/                        route A as notebooks (FINN_SC_Python.ipynb, FINN_SC_R.ipynb) and the
│                                     comparison with BRAIN, 2019 and 2020 (BRAIN_FINN_comparison_SC.ipynb)
├── tools/                            study-area map, flowchart, BRAIN cell-day check, verify_manifest.py
├── tests/                            96 automated tests
├── results/                          published tables, figures and run logs (brain_2019/, brain_2020/: BRAIN)
└── docs/                             methods, provenance, data dictionary, results map
```

## Documentation map

| I want to… | Read |
|---|---|
| learn the method and run everything, locally or in Google Colab | [`TUTORIAL_FINN_SC_en.pdf`](TUTORIAL_FINN_SC_en.pdf) |
| find the script and file behind a published number or figure | [`docs/results_map.md`](docs/results_map.md) |
| read the methods of the analysis layer | [`docs/analysis.md`](docs/analysis.md) |
| understand FINN and route A, with citations | [`docs/methodology.md`](docs/methodology.md) |
| know where each input comes from, with SHA-256 sums | [`docs/provenance.md`](docs/provenance.md) |
| look up a field, a unit or a code | [`docs/data_dictionary.md`](docs/data_dictionary.md) |
| see how the reproduction was tested | [`docs/reproducibility.md`](docs/reproducibility.md) |

## Google Colab and Earth Engine

1. Register a Google Cloud project for Earth Engine at https://console.cloud.google.com/earth-engine (noncommercial use
   needs no billing) and write down its ID.
2. In Colab, clone or unzip the repository into `/content/FINN_SC` and run route B as above (`--no-r`).
3. In each notebook of `gee/`, set `PROJECT = "<your project ID>"` in cell 2 and run all; cell 3 calls
   `ee.Authenticate()` and `ee.Initialize(project=PROJECT)`.

Step by step, with the outputs of each notebook: chapter 12 of the tutorial.

## Another region (route A)

1. Put the region's shapefile in `data/inputs/`.
2. In `config/config.yml`, set `region.boundaries_shp`, `region.region_field` and `region.name`, and choose years,
   version and sensor in the `selection` block.
3. Run `make all-py` (or `./run_all.sh python`, or `run_all.bat python`). The steps also run one by one, from
   `python python/00_download_finn.py` to `python python/05_descriptive_analysis.py`.
4. Open `data/output/aggregated_emissions_all.shp` in QGIS or read `data/output/aggregated_emissions_all.csv`.

Downloading is the slow part, because the annual FINN files are large. Start with one year.

## How to cite

Cite this repository (see [`CITATION.cff`](CITATION.cff)), the FINN paper of the version you used (Wiedinmyer et al.,
2011, for v1.5; Wiedinmyer et al., 2023, for v2.5) and the FINN data set at NSF NCAR (Wiedinmyer and Emmons, 2022,
DOI 10.5065/XNPA-AF09).

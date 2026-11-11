# Methodology

> 🌐 **English** · [Português (pt-BR)](methodology.pt-BR.md)

This document explains (a) how the FINN inventory itself is built (so you can
describe your data source correctly in a paper or report), and (b) what this
pipeline does to turn the global FINN files into a Santa Catarina municipal
emission inventory. Citations use the keys in
[`../references.bib`](../references.bib); full details in
[`../REFERENCES.md`](../REFERENCES.md).

> The statistics, screening and figures of the manuscript and of the inventory report
> (events, persistent thermal anomalies, trends, MapBiomas comparison, climate and land-cover
> associations, kernel density) are described in [`analysis.md`](analysis.md).

---

## 1. How FINN estimates fire emissions

The **Fire INventory from NCAR (FINN)** produces daily, global open-burning
emissions at ~1 km fire-detection resolution (Wiedinmyer et al., 2011, 2023).
For each detected fire, emissions of a species *i* are estimated as a product of
four factors (the classic Seiler–Crutzen form used by FINN):

```
E_i = A × B × FB × EF_i
```

where

- **A** — area burned for the fire point (m²), inferred from the satellite
  active-fire detection;
- **B** — fuel loading / biomass density (kg m⁻²) for the land-cover type;
- **FB** — the fraction of biomass actually burned (combustion completeness);
- **EF_i** — the emission factor for species *i* (g of species per kg of dry
  matter burned).

The land-cover type at each fire (the `GENVEG` class) selects the fuel loading,
combustion completeness and the emission-factor set. FINN's emission factors
draw on compilations such as **Akagi et al. (2011)** and, more recently,
**Andreae (2019)**. Total non-methane VOC emissions are then **speciated** into
model-ready species for three chemical mechanisms (MOZART-T1, SAPRC99,
GEOS-Chem); this pipeline uses the **GEOS-Chem** speciation.

### Satellite inputs

FINN is driven by NASA **FIRMS** active-fire detections:

- **MODIS** Collection 6 active fire (Giglio et al., 2016) — available
  2002–present; the basis of the `MODIS` configuration.
- **VIIRS** 375 m active fire (Schroeder et al., 2014) — available 2012–present;
  combined with MODIS in the `MODIS+VIIRS` configuration (FINN v2.5+).

Because a coarser sensor detects fewer/edge fires than a finer one, the
`MODIS+VIIRS` product generally reports **more** fire points (and often higher
totals) than `MODIS` alone for the same period — keep sensor choice consistent
when comparing years.

### Versions and availability

| Version | Sensor(s) | Temporal coverage | File granularity |
|---------|-----------|-------------------|------------------|
| v1.5 | MODIS | 2002–2020 | annual |
| v2.5 | MODIS | 2003–2021 | annual |
| v2.5 | MODIS+VIIRS | 2012–2021 | annual |
| v2.5.1 | MODIS / MODIS+VIIRS | 2022–2023 | monthly |
| v2.5.1 (NRT) | MODIS+VIIRS | 2024–present | daily (near-real-time) |

Near-real-time (NRT) files are provisional; archive-quality detections are used
for the finalized years (see the FINNv2.5 README). Treat NRT years as
preliminary.

> **Caveats worth stating in a report.** FINN emissions carry substantial
> uncertainty from cloud/overpass gaps in active-fire detection, the
> area-per-detection assumption, fuel-load and combustion-completeness
> estimates, and emission factors. Small/short/understory fires can be missed.
> Cross-checking against an independent inventory such as **GFED4s**
> (van der Werf et al., 2017) and regional studies (e.g., Teixeira et al., 2025
> for Southern Brazil) is good practice.

---

## 2. What this pipeline does

The pipeline turns the raw global FINN text files into an **emission inventory
per region polygon**, in tonnes per period, ready for tables, figures and QGIS.
The region is whatever shapefile you configure — **Santa Catarina municipalities
by default**, but any state, country or polygon works the same way. Steps mirror
the numbered scripts (identical logic in R and Python).

### Step 00 — Download & merge (`00_download_*`)

Builds the exact FINN download URLs for the requested year(s)/version/sensor,
downloads the gzipped GEOS-Chem text files from the UCAR/ACOM and NSF NCAR RDA
servers, merges them, removes duplicate rows, and writes one combined CSV per
year to `data/raw_finn/`. FINN v1.5 files, whose headers are not
self-describing, are given the correct fixed column names; for v2.5+ an optional
`source_url` provenance column is prepended (comma-delimited, so the output is a
clean CSV). FINN v1.5 annual files are distributed as `.tar.gz` archives while
v2.5+/NRT files are `.txt.gz`; the downloader detects and reads both. Because
each annual product is a single file per year, downloading is essentially a
one-time cost — every later step reuses the combined CSV in `data/raw_finn/`.

### Step 01 — Unit conversion (`01_convert_units`)

Converts every emission column from FINN native units to **metric tonnes**:
gases via molar mass (`mol × g mol⁻¹ / 10⁶`) and aerosols via `kg / 1000`
(see [`data_dictionary.md`](data_dictionary.md)). Writes `*_converted.csv` to
`data/interim/`.

*2026-10-03 review.* `NOXasNO`, `NMOC` and `NMHC` are **kg/day mass** fields in
the v2.5/v2.5.1 files (despite the README's "all gas-phase species in
mole/day"): their implied emission factors, species / (`AREA` × `BMASS`),
reproduce Wiedinmyer et al. (2023, Table 4) only as kg/day, so they are
converted with `kg / 1000`. NMHC had been converted as a gas (× 72 g mol⁻¹),
which underestimated it by a factor 1000/72 = 13.9. The molar masses of GLYC
(60.05), GLYX (58.04), HAC (74.08), MGLY (72.06) and H2 (2.016) were corrected
from the molecular formulas. Reporting definitions: **NOx = `NOXasNO`** (NO
mass; `NO` + `NO2` must never be summed as NOx; step 04 adds `NOx_as_NO2` =
`NOXasNO` × 46.0055/30.0061) and **VOC = `NMOC`** (total non-methane organic
gases; the speciated species are not summed, because `NMHC` overlaps the
individual hydrocarbons).

### Step 02 — Clip to the region (`02_clip_region`)

Keeps only fire records inside the region **polygons**: a bounding-box
pre-filter (config `region.bbox`) followed by a point-in-polygon test against
the boundaries shapefile (2026-10-03 review: before, step 02 stopped at the
bounding box, so the point files and the stacked table of step 03 also held
points of neighbouring states, countries and the ocean; the shapefile is now
required here). Bounding-box details:
With `bbox: auto` (default) the box is derived from the configured shapefile's
own extent (+ `bbox_margin_deg`), so the step adapts to any region; `bbox: none`
skips the pre-filter, and explicit degrees are also accepted. This pre-filter
shrinks the global point cloud before the more expensive point-in-polygon join.
It is a **vectorised coordinate comparison** (LONGI/LATI between the bounds) —
exact for a lon/lat rectangle and dramatically faster than building `sf` points
and running `st_within` over millions of records (the approach in the original
scripts), so it stays fast even on the full global cloud. Writes
`filtered_points_<year>_<sensor>_<version>_converted_within_grid.csv`.

### Step 03 — Stack years (optional) (`03_stack_years`)

Concatenates all SC-clipped point files into one long table tagged with
`year`, `sensor`, `version` — convenient for point-level multi-year analysis.

### Step 04 — Aggregate by region polygon (`04_aggregate_region`)

Performs a point-in-polygon **spatial join** of the fire points against the
configured **boundaries shapefile** (`region.boundaries_shp`; default
`data/inputs/SC_Municipios_2024.shp`), sums each FINN species per polygon
(grouping on `region.region_field`, default `NM_MUN`), counts fires, stacks all
years/sensors/versions, joins the totals back onto the polygon geometry, and
writes:

- `data/output/aggregated_emissions_all.csv` — full column names;
- `data/output/aggregated_emissions_all.shp` — for QGIS (10-char field names).

Only recognised FINN species are summed, so extra numeric attributes carried by
the shapefile (population, area, codes) are never mistaken for emissions. The
**Fire counting (2026-10-03 review).** A FINN record is one land-cover
(`GENVEG`) piece of one fire point, so the number of records is not a number
of fires (the old `focos` column, now `n_rows`). In the v2.5/v2.5.1 files
`POLYID` is the daily burned-area polygon (adjacent detections merged; it may
hold several points) and `FIREID` is one point inside it. Step 04 reports
**`events`** = distinct (year, `DAY`, `POLYID`), each assigned to the ONE polygon
that holds the largest share of its `AREA` (ties: first polygon name), and
**`detections`** = distinct (year, `DAY`, `FIREID`), assigned the same way, so
polygon counts add up to the regional total. It also writes `burned_km2` =
Σ`AREA`/10⁶ (the shapefile's `AREA_KM2` is the polygon's own area, not burned
area). FINN v1.5 has no `POLYID`/`FIREID`, so `events`/`detections` are NA there.
**Duplicate guards:** the run stops if two input files resolve to the same
(year, sensor, version) — the mechanism that put the 2011 MODIS v2.5 rows twice
in the old `aggregated_emissions_all.csv` — exact duplicate records are dropped,
and repeated (`source_url`, `DAY`, `POLYID`, `FIREID`, `GENVEG`) keys are only
reported, because FINN legitimately contains distinct records sharing that key.

The temporal grain of each row is set by `aggregation.time_resolution` (`day`,
`month` or `year`) and recorded in a `period` column, with a numeric `year`
column always kept alongside; totals are conserved across resolutions (summing a
polygon's monthly/daily rows reproduces its annual total). The bounding-box
filter (step 02) is coarse and is followed there by a point-in-polygon test;
the polygon assignment here uses the same test (`within`, planar, in R and Python).

### Step 05 — Descriptive analysis (`05_descriptive_analysis`)

Reads the aggregated inventory and produces a 4-panel annual figure (fire
events, burned area `burned_km2`, CO, PM₂.₅), a per-year summary table of key
pollutants (including `NOXasNO`, `NOx_as_NO2`, `NMOC` = VOC, `events`,
`detections`), and,
when several versions/sensors are present, a version × sensor CO₂ comparison. It
also draws a **time series at the configured `aggregation.time_resolution`**
(`timeseries_<res>.png` — region-total CO, PM₂.₅, CO₂ and fire events vs `period`)
with a matching `period_summary_<res>.csv`, so a monthly or daily series comes
out of the box.

---

## 3. Reproducibility notes

- All tunable parameters (years, version, sensor, bounding box, paths,
  molar masses) live in [`../config/config.yml`](../config/config.yml); the
  scripts contain no hard-coded study parameters.
- The R and Python routes read that **same** config and produce the same
  intermediate/final file names, so you can mix routes (e.g., download in R,
  analyze in Python).
- Spatial operations use `sf` in R (Pebesma, 2018) and `geopandas` in Python;
  both reproject points to the shapefile CRS before joining.
- FINN, the IBGE boundaries and (optionally) INPE Programa Queimadas are
  external inputs; their provenance and access URLs are in
  [`../REFERENCES.md`](../REFERENCES.md).

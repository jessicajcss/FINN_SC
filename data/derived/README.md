# `data/derived/` — FINN records of Santa Catarina (input of the analysis layer)

`finn_sc_records_2003_2025.csv.gz` — one row per FINN "each fire" record whose point lies inside an IBGE 2024
municipality of SC (258 694 rows). Provenance, checks and checksum: [`../../docs/provenance.md`](../../docs/provenance.md), section 1.

| Column | Meaning | Unit |
|---|---|---|
| `year`, `sensor`, `version` | FINN product: `MODIS` or `MODIS+VIIRS`; `v2.5` (to 2021) or `v2.5.1` (from 2022) | — |
| `DAY` | day of year (local date; Wiedinmyer et al., 2023, Eq. 2) | — |
| `POLYID` | daily burned-area polygon (**fire event** = distinct year, sensor, version, DAY, POLYID) | — |
| `FIREID` | active-fire detection (single coordinate) | — |
| `GENVEG` | FINN generic vegetation type: 1 grassland/savanna, 2 woody savanna/shrubs, 3 tropical forest, 4 temperate forest, 6 temperate evergreen forest, 9 croplands | — |
| `LONGI`, `LATI` | detection coordinate (WGS84) | degrees |
| `AREA` | FINN burned area of the record | m² |
| `BMASS` | biomass burned per area | kg m⁻² |
| `CO2 CO CH4 NMOC NOXasNO SO2 NH3 PM25 PM10 OC BC` | emissions (NOXasNO = NOx as NO mass; NMOC = total non-methane organic gases) | t |
| `CD_MUN`, `NM_MUN` | IBGE 2024 municipality containing the point | — |
| `source_file` | FINN file of origin | — |

`finn_sc_records_rebuilt.csv.gz` (not shipped) is written by route A (`python/06_build_sc_records.py`).

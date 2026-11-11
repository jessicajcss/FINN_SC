# FINN data dictionary

> 🌐 **English** · [Português (pt-BR)](data_dictionary.pt-BR.md)

Field names, units and coded values for the FINN files this pipeline consumes,
plus the columns the pipeline adds. Authoritative field/unit definitions come
from the official FINN READMEs (copies kept in this folder:
[`README_FINNv2.5_June2024.pdf`](README_FINNv2.5_June2024.pdf) and
[`README_FINNv1_GEOSCHEM.pdf`](README_FINNv1_GEOSCHEM.pdf)) and from
Wiedinmyer et al. (2011, 2023) — see [`../REFERENCES.md`](../REFERENCES.md).

> ⚠️ **Units.** In the *raw* FINN files, gas-phase species are in **mole/day**
> and aerosols (OC, BC, PM25, PM10, TPM, TPC) are in **kg/day**. **Exception
> (2026-10-03 review):** the aggregate gas fields `NOXasNO`, `NMOC` and `NMHC`
> are **kg/day mass** fields in the v2.5/v2.5.1 GEOS-Chem "each fire" files,
> although the README says "all gas-phase species in mole/day": their implied
> emission factors, species / (`AREA` × `BMASS`), reproduce Wiedinmyer et al.
> (2023, Table 4) only when read as kg/day (checked on 200 000 real
> v2.5.1 rows: all 14 species × 7 `GENVEG` classes within 1 %). After
> `01_convert_units`, **every** emission column is in **metric tonnes** per
> reporting period. Always track which stage a file came from.

---

## 1. Identification / geometry fields

| Field    | Meaning | Units | Notes |
|----------|---------|-------|-------|
| `DAY`    | Julian day (day of year) of the detection | 1–365/366 | Present in all versions. |
| `TIME`   | Satellite overpass time | UTC | FINNv1/v1.5 files only. |
| `POLYID` | Daily burned-area polygon (adjacent detections merged; may hold several points) | — | FINNv2.5+. 2026-10-03 review: definition from the files themselves (on the SC records 20 766 of 124 602 daily POLYIDs hold >1 FIREID); the README wording is the reverse. Unit of the `events` count. |
| `FIREID` | One fire point (single coordinate) inside a `POLYID` | — | FINNv2.5+. 151 436 of 151 441 SC FIREIDs have one coordinate. Unit of the `detections` count. |
| `GENVEG` | Generic vegetation (land-cover) class at the fire | code | See §3. |
| `LATI`   | Latitude | decimal degrees (WGS84) | |
| `LONGI`  | Longitude | decimal degrees (WGS84) | |
| `AREA`   | Burned area of the record (one `GENVEG` piece of a point) | m² | Sum `AREA` over records for total burned area (step 04 writes `burned_km2`). |
| `BMASS`  | Biomass burned per unit area | kg/m² | FINNv2.5+. |

## 2. Emission fields (species)

Gas-phase species are emitted as **mole(species)/day**; aerosols as
**kg(species)/day** (official FINN README); `NOXasNO`, `NMOC` and `NMHC` are
**kg/day** (see the units note above). The exact species set depends on
the FINN version and the VOC speciation mechanism (this pipeline uses the
**GEOS-Chem** mechanism). The molar masses below are those applied by
`01_convert_units` (config/config.yml). 2026-10-03 review: checked against the
molecular formulas (standard atomic weights; GEOS-Chem species database);
GLYC, GLYX, HAC, MGLY and H2 were corrected and NMHC moved to the kg/day list
(the original `01-conversao_unidade_FINN.R` used 92.09, 86.09 [spelled
"CLYX", so glyoxal was never converted], 60.05, 74.08, 2.02 and NMHC 72.00).

| Abbrev | Species (EN) | Raw unit | Molar mass (g/mol) |
|--------|--------------|----------|--------------------|
| `CO2`  | Carbon dioxide | mol/day | 44.01 |
| `CO`   | Carbon monoxide | mol/day | 28.01 |
| `CH4`  | Methane | mol/day | 16.04 |
| `H2`   | Molecular hydrogen | mol/day | 2.016 |
| `SO2`  | Sulfur dioxide | mol/day | 64.07 |
| `NH3`  | Ammonia | mol/day | 17.03 |
| `NO`   | Nitric oxide | mol/day | 30.01 |
| `NO2`  | Nitrogen dioxide | mol/day | 46.01 |
| `NMHC` | Non-methane hydrocarbons (aggregate) | **kg/day** | converted via ÷1000 (2026-10-03 review; was ×72/10⁶ → 13.9× too low) |
| `ACET` | Acetone | mol/day | 58.08 |
| `ALD2` | Acetaldehyde | mol/day | 44.05 |
| `ALK4` | C4+ alkanes | mol/day | 58.12 |
| `BENZ` | Benzene | mol/day | 78.11 |
| `C2H2` | Acetylene | mol/day | 26.04 |
| `C2H4` | Ethylene | mol/day | 28.05 |
| `C2H6` | Ethane | mol/day | 30.07 |
| `C3H8` | Propane | mol/day | 44.10 |
| `CH2O` | Formaldehyde | mol/day | 30.03 |
| `GLYC` | Glycolaldehyde (C₂H₄O₂) | mol/day | 60.05 |
| `GLYX` | Glyoxal (C₂H₂O₂) | mol/day | 58.04 |
| `HAC`  | Hydroxyacetone (C₃H₆O₂) | mol/day | 74.08 |
| `MEK`  | Methyl ethyl ketone | mol/day | 72.11 |
| `MGLY` | Methylglyoxal (C₃H₄O₂) | mol/day | 72.06 |
| `PRPE` | Propene | mol/day | 42.08 |
| `TOLU` | Toluene | mol/day | 92.14 |
| `XYLE` | Xylenes | mol/day | 106.17 |
| `OC`   | Organic carbon (aerosol) | **kg/day** | converted via ÷1000 |
| `BC`   | Black carbon (aerosol) | **kg/day** | converted via ÷1000 |
| `PM25` | Particulate matter ≤ 2.5 µm | **kg/day** | converted via ÷1000 |
| `PM10` | Particulate matter ≤ 10 µm | **kg/day** | converted via ÷1000 |

Additional aggregate/mass species (kg/day → tonnes):
`NOXasNO` (NOx expressed as NO mass), `NMOC` (total non-methane organic gases,
identified + unidentified), `TPM` (total particulate matter), `TPC` (total
particulate carbon).

**Reporting definitions (2026-10-03 review).**
- **NOx = `NOXasNO`** (NO mass). `NO` and `NO2` are speciated outputs; never sum
  them as "NOx". Step 04 also writes `NOx_as_NO2` = `NOXasNO` × 46.0055/30.0061
  (NO2-equivalent mass).
- **VOC (COV) = `NMOC`**. Do not sum the speciated GEOS-Chem species to obtain a
  VOC total: `NMHC` overlaps the individual hydrocarbons (double counting) and
  the species list does not cover the unidentified NMOG mass.

> **Conversion recap.**
> Gas: `tonnes = mol × molar_mass[g/mol] / 1 000 000`.
> Aerosol/mass: `tonnes = kg / 1000`.

## 3. `GENVEG` land-cover classes (FINN v2.5)

| Code | Class |
|------|-------|
| 0 | No vegetation |
| 1 | Grasslands and savanna |
| 2 | Woody savanna / shrublands |
| 3 | Tropical forest |
| 4 | Temperate forest |
| 5 | Boreal forest |
| 6 | Temperate evergreen forest |
| 9 | Croplands |

*(FINN v1/v1.5 use a comparable generic-vegetation scheme; consult the v1 README
for that version's exact classes.)*

## 4. VOC speciation mechanisms

Each FINN v2.5 "eachfire" file provides VOC emissions speciated for three
chemical mechanisms: **MOZART-T1** (v2.0), **SAPRC99** (v1.0) and **GEOS-Chem**
(v1.0). This pipeline uses the **GEOS-Chem** speciation throughout, matching the
species table above.

## 5. Columns added by this pipeline

| Column | Added in | Meaning |
|--------|----------|---------|
| `source_url` | `00_download` | Origin URL of each raw record (provenance; optional). |
| `DATE` | `01_convert` | Calendar date `YYYY-MM-DD` (from `DAY` + year). Added **only** when a `start_date`/`end_date` range is set. |
| `year` | `02`/`03`/`04` | Reference year (parsed from the file name). |
| `sensor` | `02`/`03`/`04` | `MODIS` or `MODIS+VIIRS`. |
| `version` | `02`/`03`/`04` | FINN version (`v1.5`, `v2.5`, `v2.5.1`). |
| `n_rows` | `04_aggregate` | Number of FINN records (FIREID × GENVEG pieces) in the polygon — a diagnostic, **not** a number of fires (2026-10-03 review: replaces `focos`). |
| `events` | `04_aggregate` | Fire events = distinct (year, `DAY`, `POLYID`); each event is assigned to the ONE polygon holding the largest share of its `AREA` (ties: first polygon name). NA for FINN v1.5 (no POLYID). |
| `detections` | `04_aggregate` | Distinct (year, `DAY`, `FIREID`), assigned the same way. NA for v1.5. |
| `burned_km2` | `04_aggregate` | Σ `AREA` / 10⁶ (FINN burned area, km²). Not the shapefile's `AREA_KM2`, which is the polygon's own area. |
| `NOx_as_NO2` | `04_aggregate` | `NOXasNO` × 46.0055/30.0061 (config `derived.nox_as_no2`). |
| `period` | `04_aggregate` | Time bucket at `aggregation.time_resolution`: `"2019"` (year), `"2019-06"` (month) or `"2019-06-15"` (day). |
| `region_field` | `04_aggregate` | The grouping attribute from your shapefile (default `NM_MUN`). |
| *(shapefile attrs)* | `04_aggregate` | All attribute columns of the boundaries layer are carried through (for the default IBGE layer: `CD_MUN`, `AREA_KM2` = municipality area, …). |

> The grouping column name is whatever `region.region_field` points to — `NM_MUN`
> for the default IBGE municipalities, or e.g. `NAME` / `shapeName` for a
> country/admin layer. Only recognised FINN species (§2) are summed; other
> numeric attributes of the shapefile are carried through, not aggregated.

> **Shapefile note.** ESRI shapefiles truncate field names to 10 characters.
> `04_aggregate_region` writes both a full-name `.csv` and a truncated
> `.shp`; use the `.csv` when you need the untruncated column names.

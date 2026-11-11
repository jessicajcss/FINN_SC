# `data/inputs/` — external input layers

> ✅ **Shipped (v2.0.0):** `SC_Municipios_2024.shp` (+ `.dbf/.shx/.prj`), IBGE *Malha Municipal* 2024 of Santa Catarina, the exact file used for the published results (SHA-256 checksums in `docs/provenance.md`, section 2). In version 1.x this note said so but only the `.prj`/`.shx` were present. The instructions below are for updating it or using another region.


> 🌐 **English** · [Português (pt-BR)](README.pt-BR.md)

The pipeline needs a **polygon boundaries shapefile** to assign each fire point
to a region (step 04). The **default** is the municipalities of Santa Catarina
(IBGE), but **any polygon layer works** — another Brazilian state, a country, a
group of countries, a biome, a basin. This layer is *not* redistributed here;
place your `.shp` (+ `.dbf/.shx/.prj`) in this folder and point
`region.boundaries_shp` / `region.region_field` at it in `config/config.yml`.

Instructions below are for the **default** (IBGE SC municipalities). For any
other region, download that layer instead (e.g. GADM, Natural Earth,
geoBoundaries for countries/admin units) and set `region.region_field` to its
name attribute (`shapeName`, `NAME`, `ADM0_NAME`, …).

## Municipality boundaries (IBGE Malha Municipal)

1. Go to the IBGE Malha Municipal page:
   <https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html>
2. Download the municipality mesh (*malha municipal*) for the reference year you
   want (the scripts assume **2024**). You can download the Santa Catarina (SC)
   state file directly, or the national file and subset to `SIGLA_UF == "SC"`.
3. Unzip so that this folder contains, at minimum:

   ```
   data/inputs/SC_Municipios_2024.shp
   data/inputs/SC_Municipios_2024.dbf
   data/inputs/SC_Municipios_2024.shx
   data/inputs/SC_Municipios_2024.prj
   ```

   If your download has a different file name, either rename it to
   `SC_Municipios_2024.*` or update `region.boundaries_shp` in
   `config/config.yml`.

## Expected attribute columns

The scripts use these attribute fields (defaults in `config.yml` for the IBGE SC
layer):

| Field     | Meaning                          | Config key                   |
|-----------|----------------------------------|------------------------------|
| `NM_MUN`  | Municipality name                | grouping key (`region.region_field`) |
| `CD_MUN`  | IBGE municipality code           | identifier (`region.code_field`)     |
| `AREA_KM2`| Municipality area (km²)          | optional area normalisation  |

For a **different layer**, set `region.region_field` to whatever attribute holds
the polygon name/id you want to aggregate by (and `region.code_field` to an
optional secondary id, or `~` for none). The step-04 error message lists the
available columns if the configured field is not found.

## Coordinate reference system

FINN coordinates are geographic WGS84 (EPSG:4326). The pipeline reprojects the
points to the shapefile CRS before the spatial join, so any CRS in the IBGE file
is fine.

> Data source citation: IBGE — Instituto Brasileiro de Geografia e Estatística,
> Malha Municipal Digital. See `../../REFERENCES.md`.

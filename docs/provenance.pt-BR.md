# Proveniência dos dados

> 🌐 [English](provenance.md) · **Português (pt-BR)**

Cada arquivo lido pela camada de análise está listado abaixo com sua origem, o modo como foi produzido, o que
foi alterado e a soma de verificação SHA-256 (`sha256sum <arquivo>`). Nenhum valor em `data/` foi digitado à mão,
exceto onde indicado. As somas foram conferidas com os arquivos deste repositório em 1º/11/2026: todos os arquivos listados que o repositório distribui conferem (23 de 24 somas; a restante é de um GeoTIFF marcado como não distribuído).

## 1. Registros do FINN em Santa Catarina — `data/derived/finn_sc_records_2003_2025.csv.gz`

| Item | Valor |
|---|---|
| Conteúdo | 258.694 registros "each fire" do FINN (especiação GEOS-Chem) cujo ponto está em um dos 295 municípios de SC da malha do IBGE de 2024: MODIS v2.5 2003–2021 (102.788), MODIS v2.5.1 2022–2023 (6.224), MODIS+VIIRS v2.5 2012–2021 (115.183) e MODIS+VIIRS v2.5.1 2022–2025 (34.499). O FINN v1.5 não está incluído. |
| Colunas | `year, sensor, version, DAY, POLYID, FIREID, GENVEG, LONGI, LATI, AREA (m²), BMASS (kg m⁻²), CO2, CO, CH4, NMOC, NOXasNO, SO2, NH3, PM25, PM10, OC, BC` (toneladas), `CD_MUN, NM_MUN` (IBGE 2024), `source_file` (nome do arquivo do FINN de origem; 548 arquivos). |
| Fonte | Arquivos do FINN v2.5 / v2.5.1 do Research Data Archive do NSF NCAR, conjunto ds312.9 (2003–2023; Wiedinmyer; Emmons, 2022, https://doi.org/10.5065/XNPA-AF09), e pasta de produtos em tempo quase real do NCAR, https://www.acom.ucar.edu/acresp/MODELING/finn_emis_txt/ (2024–2025). |
| Produção | Download e conversão para toneladas pelos scripts originais dos autores (execução de fevereiro de 2026; esses scripts ficam fora deste repositório, e a rota A, `python/00` a `02` e `06`, reconstrói os registros, como mostra `tests/test_route_a.py`), recorte por uma caixa em torno de SC (`filtered_points_grid.csv`) e restrição aos municípios de SC por ponto em polígono com `tools/build_records_from_legacy.py` (3/10/2026). Linhas duplicadas idênticas: 0. |
| Conferência das unidades | Para as 11 espécies e todas as classes de vegetação, espécie / (AREA × BMASS) reproduz os fatores de emissão de Wiedinmyer et al. (2023, Tabela 4) com diferença de até 0,3% (razões de 0,9986 a 1,0026; `python/analysis/a09_emission_factor_check.py`). O NMHC e as espécies de COV especiadas, afetados pelos erros da conversão antiga (CHANGELOG_2026-10-03.md), ficaram fora deste arquivo e não são usados. |
| Replicação | A rota A (pipeline mantido, etapas 01, 02 e 06), aplicada aos registros brutos do FINN v2.5.1 NRT de 1º de janeiro a 28 de maio de 2025, reproduz exatamente os registros arquivados desses dias (2.341 de 2.341 registros; diferença relativa máxima de 4 × 10⁻¹⁴; `tests/test_route_a.py`). Os demais produtos e anos não foram baixados novamente nesta revisão. |
| SHA-256 | `4e23e22344b795ade9ab877089187b169e963be027afc2e1e6abba3e0f01a8dd` |

## 2. Limites municipais — `data/inputs/SC_Municipios_2024.*`

Malha Municipal do IBGE de 2024 para Santa Catarina (295 municípios; SIRGAS 2000, EPSG:4674; campos `CD_MUN`,
`NM_MUN`, `AREA_KM2` e outros), cópia do arquivo usado pelos autores (`FINN_QUEIMADAS_072026/repo/raw_data/`).
Página de origem: https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html.
O `.dbf` vem sem `.cpg` e deve ser lido como cp1252/latin-1. Somas SHA-256 na versão em inglês deste documento.

## 3. Atributos municipais e mesorregiões — `data/external/sc_municipios_2024_atributos.csv`

`CD_MUN, NM_MUN, AREA_KM2` copiados do `.dbf` do IBGE de 2024; `mesorregiao` = mesorregião do IBGE (1990)
(Grande Florianópolis, 21 municípios; Norte Catarinense, 26; Oeste Catarinense, 118; Serrana, 30; Sul
Catarinense, 46; Vale do Itajaí, 54). A correspondência foi obtida dos polígonos de mesorregião da camada do
projeto (`aggregated_emissions_all_mesorregioes.shp`, campo `Mesorregia`), pela maioria de 400 pontos internos
sorteados em cada município (`wildfire/analysis/08_table3_and_mapping.py`, 2/10/2026). **Pendência:** conferir com
a correspondência oficial do IBGE (API de localidades, `/api/v1/localidades/estados/42/municipios`, campos
`microrregiao.mesorregiao`), inacessível no ambiente usado nesta revisão.

## 4. MapBiomas Fogo, Coleção 4 — `data/external/mapbiomas_fogo_col4_SC_municipal_km2_2012_2024.csv`

Área queimada anual (km²) por município de 2012 a 2024 (3.835 linhas = 295 × 13), produzida pelos autores com
`gee/mapbiomas_fogo_col4_municipal.js` (ativo
`projects/mapbiomas-public/assets/brazil/fire/collection4/mapbiomas_fire_collection4_annual_burned_v1`; máscara de
queimada binarizada antes da soma; área por `ee.Image.pixelArea()`; 30 m; malha do IBGE de 2024) em 2/10/2026. A
exportação original do Earth Engine está em `data/external/raw/` (com acentos corrompidos em 110 nomes); a cópia
limpa mantém `CD_MUN, year, burned_km2` e toma o `NM_MUN` dos atributos do IBGE pelo `CD_MUN`. Referências:
Alencar et al. (2022); MapBiomas (2025, ATBD da Coleção 4). **Não usar** a extração antiga
`repo/data/mapbiomas_fire_*_km2.csv` (soma de códigos de classe; valores 14,8 a 18,6 vezes maiores; segunda rodada
de revisão).

## 5. Clima da estação de queimadas — `data/external/era5land_oni_SC_fire_season_2012_2025.csv`

Colunas `year, precip_mm_fs, Tc_fs, VPD_kPa_fs, soil_moist_fs, ONI_fs` (julho a novembro), subconjunto de
`raw/paper2_annual_drivers.csv`, produzido pelo NotebookB dos autores (Google Earth Engine, agregados mensais do
ERA5-Land; ONI do NOAA CPC); a receita está transcrita em `gee/era5land_oni_fire_season.py`. A coluna de SPI do
arquivo original não é usada (série menor que os 30 anos exigidos; Svoboda; Hayes; Wood, 2012). **Pendência:**
data de acesso ao arquivo do ONI.

## 6. Frações de cobertura da terra — `data/external/mapbiomas_lulc2023_SC_municipal_fractions.csv` (PROVISÓRIO)

Frações de formação florestal, formação campestre, pastagem, agricultura e silvicultura em 2023 para **277**
municípios (os que tiveram registros do FINN em 2025), extraídas de `raw/paper2_municipal_landuse_emissions.csv`
(apenas as colunas de cobertura; as colunas de emissão desse arquivo usavam as definições substituídas). Receita:
`gee/mapbiomas_lulc_fractions.py`. **Pendências:** (i) refazer para os 295 municípios (checkpoint
`municipal_landuse.csv` do NotebookB no Google Drive dos autores); (ii) registrar a coleção do MapBiomas por trás do
ativo `lulc/v1`. As duas pendências são resolvidas por `gee/mapbiomas_lulc_fractions_all295.ipynb`,
que grava `data/external/mapbiomas_lulc2023_SC_municipal_fractions_all295.csv` (295 municípios, código do IBGE,
coleção e versão da imagem), usado pelo `a07` quando presente. Os resultados que usam este arquivo (correlações de Spearman e modelos de erro espacial com a
cobertura da terra) devem ser recalculados quando o arquivo completo estiver disponível.

## 6a. Frações de cobertura do solo dos 295 municípios — `data/external/mapbiomas_lulc2023_SC_municipal_fractions_all295.csv`

Gerado por `gee/mapbiomas_lulc_fractions_all295.ipynb`, executado pelos autores no Google Colab em 7/10/2026 (cópia
executada: `gee/mapbiomas_lulc_fractions_all295_run_2026-10-07.ipynb`). Ativo `projects/mapbiomas-public/assets/brazil/lulc/v1`,
imagem de 2023; o ativo contém as coleções 10, 10.1 e 11 para 2023, e a imagem usada (`first()`, como na execução
arquivada) é a **Coleção 10.1** (`collection_id` = 10.1, versão v1). Polígonos municipais: geobr 2022 (295; códigos
idênticos aos do arquivo de atributos do IBGE de 2024). Os 277 municípios do arquivo provisório são reproduzidos até a
precisão numérica (diferença máxima de 2,8 × 10⁻¹⁵), o que indica que o arquivo provisório também veio da Coleção 10.1.
Usado pelo `a07` (união pelo código do IBGE). SHA-256
`f8ca0995f3574224261e76e11c42af959d45e35c7268459d1159cb016df17654` (`tests/test_round6.py`).

## 7. Contagens da caixa de recorte antiga — `data/external/legacy_bbox_record_counts.csv`

Número de registros por produto e ano no arquivo `filtered_points_grid.csv` dos autores (caixa em torno de SC
usada pelos scripts originais), contado em 3/10/2026; usado apenas no diagnóstico "fração dos registros da caixa
que fica dentro de SC" (relatório, Apêndice A).

## 8. Entrada do teste da rota A — `tests/data/raw_2025_subset_v2.5.1_MODIS+VIIRS.csv.gz`

Registros brutos do FINN v2.5.1 NRT (unidades nativas; formato gravado pela etapa 00) dos dias 1 a 148 de 2025
(147 arquivos diários da pasta NRT do NCAR): todos os registros desses dias dentro de SC e uma amostra de
registros de outras regiões.

## 9. Inventário estadual de 2020 e FINN v1.5 — `data/external/legacy_finn15_lcqar_2020.csv`

Duas linhas. `lcqar_2022_report`: os totais de 2020 do inventário estadual de queima de biomassa (LCQAR, 2022;
Tabela 11 e o texto que a segue: 4.625 focos de calor, CO₂ 12.909.573 t, CO 699.668 t, MP₂,₅ 70.724 t,
NOx 38.037 t), **digitados à mão** a partir do relatório. O relatório descreve o FINN com detecções MODIS
(MOD14/MYD14) e os mapas estáticos de cobertura da terra do FINN v1, e conta cada registro do FINN como um foco.
`finn15_sc_records`: os registros do FINN v1.5 (MODIS) de 2020 cujo ponto está em um município de SC (IBGE 2024),
tirados do arquivo antigo dos autores `filtered_points_grid.csv` (execução de fevereiro de 2026) e somados por
`wildfire/analysis/verify_r2/v04_state_series.py` (2/10/2026; saída `v04_state_by_year_sensor_version.csv`):
4.609 registros, CO₂ 12.883.690,6 t, CO 698.281,3 t, MP₂,₅ 70.585,7 t, NO + NO₂ 37.961,8 t (o v1.5 não tem o
campo NOXasNO), área de 4.134,6 km²; os 4.609 registros correspondem a 4.609 combinações distintas de dia e coordenadas, isto é, um registro por detecção MODIS; 50,2% da área e 87,3% do CO₂ têm o código de vegetação 3, e 0,4% da área, o código 4 (contagem de 6/10/2026). `tools/legacy_finn15_2020.py` recalcula a linha a partir do arquivo antigo (nova execução em 6/10/2026, com valores idênticos). Os registros do FINN v1.5 não são distribuídos (§1). O arquivo não é lido
pela análise; `tests/test_round5.py` o usa para conferir que as duas linhas concordam com diferença de até 0,4%
e para compará-las com os totais do FINN v2.5 de 2020 calculados a partir do §1. SHA-256 `e8221ec1dc26d0ab0d59fae76215129ba261ff35c3a758effeaf4c4a4d4ec92e`.

## 10. Figura da área de estudo — uso e cobertura da terra do MapBiomas de 2019 e limites do IBGE

* `data/external/mapbiomas_c10_lulc2019_SC_120m.npz`: recorte de Santa Catarina da Coleção 10 do MapBiomas, ano de 2019
  (`brazil_coverage_2019.tif`, cópia dos autores em `inventario/MAPBIOMAS/MEGAN_Fortran_to_R_122025/data/MapBiomas/`), lido
  em cerca de 120 m (4 vezes os 30 m nativos) por `tools/extract_mapbiomas_sc.py` em 6/10/2026. A cópia dos autores está
  incompleta na resolução original (os blocos ao sul de cerca de 25,9° S não podem ser lidos, o que indica download
  interrompido), mas as pirâmides internas estão completas, e o recorte foi lido delas. SHA-256 `45ee0b64258163b30b445686606f3a33c33b4ecac1b1d64f3031c4f896e5c947`.
* `data/external/mapbiomas_c10_lulc2019_SC_class_areas.csv`: área de cada classe dentro do estado (limite do IBGE de
  2024), calculada na pirâmide de 60 m, com a área de cada pixel pela latitude na esfera autálica; percentuais sobre a
  área classificada (a classe 0, cerca de 436 km² de águas costeiras dentro do limite do IBGE, foi excluída). Os
  percentuais a 60 m e a 120 m diferem em até 0,02 ponto percentual. SHA-256 `be8f4009eb139988abb728fd29e32266b0a19745a46e9daecaf466f3592facdb`.
* `data/external/ibge_br_uf_2024_simplified.geojson` (BR_UF_2024 do IBGE, simplificado a 0,01°) e
  `data/external/ibge_america_do_sul_2021_simplified.geojson` (Lim_america_do_sul_2021 do IBGE, simplificado a 0,02°):
  camadas de contexto da figura. SHA-256 `116bb7f2199da9ac5ec230ed17533bbd36891eb086ea2a626e4c1832ca098d87` e `42dd4d114e4deb9e75e88a76a79a3933a4b05528feb08e8e6f5bf68636dbb288`.
* Figura: `tools/study_area_map.py` → `results/figures/Fig01_study_area_pt.png` (português; Figura 1 do artigo) e
  `Fig01_study_area_en.png` (inglês). Pendência: trocar 2019 pelo ano da análise de cobertura do solo (2023) ou pelo mais recente (2024) quando o
  arquivo completo estiver disponível.

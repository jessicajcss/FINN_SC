# Dicionário de dados do FINN

> 🌐 [English](data_dictionary.md) · **Português (pt-BR)**

Nomes de campo, unidades e valores codificados dos arquivos FINN que este
pipeline consome, além das colunas que o pipeline adiciona. As definições
oficiais de campo/unidade vêm dos READMEs oficiais do FINN (cópias mantidas nesta
pasta: [`README_FINNv2.5_June2024.pdf`](README_FINNv2.5_June2024.pdf) e
[`README_FINNv1_GEOSCHEM.pdf`](README_FINNv1_GEOSCHEM.pdf)) e de Wiedinmyer et
al. (2011, 2023) — veja [`../REFERENCES.md`](../REFERENCES.md).

> ⚠️ **Unidades.** Nos arquivos FINN *brutos*, as espécies gasosas estão em
> **mol/dia** e os aerossóis (OC, BC, PM25, PM10, TPM, TPC) em **kg/dia**.
> **Exceção (revisão 2026-10-03):** os campos gasosos agregados `NOXasNO`,
> `NMOC` e `NMHC` são campos de **massa em kg/dia** nos arquivos "each fire"
> GEOS-Chem v2.5/v2.5.1, embora o README diga "todas as espécies gasosas em
> mol/dia": os fatores de emissão implícitos, espécie / (`AREA` × `BMASS`),
> reproduzem a Tabela 4 de Wiedinmyer et al. (2023) apenas se lidos como kg/dia
> (verificado em 200 000 linhas reais v2.5.1: 14 espécies × 7 classes `GENVEG`
> dentro de 1 %). Após
> `01_convert_units`, **todas** as colunas de emissão estão em **toneladas
> métricas** por período de referência. Sempre acompanhe de qual etapa o arquivo
> veio.

---

## 1. Campos de identificação / geometria

| Campo    | Significado | Unidades | Observações |
|----------|-------------|----------|-------------|
| `DAY`    | Dia juliano (dia do ano) da detecção | 1–365/366 | Presente em todas as versões. |
| `TIME`   | Horário de passagem do satélite | UTC | Apenas arquivos FINNv1/v1.5. |
| `POLYID` | Polígono diário de área queimada (detecções adjacentes fundidas; pode conter vários pontos) | — | FINNv2.5+. Revisão 2026-10-03: definição obtida dos próprios arquivos (nos registros de SC, 20 766 de 124 602 POLYIDs diários contêm >1 FIREID); o texto do README diz o inverso. Unidade da contagem `events`. |
| `FIREID` | Um ponto de fogo (coordenada única) dentro de um `POLYID` | — | FINNv2.5+. 151 436 de 151 441 FIREIDs de SC têm uma só coordenada. Unidade da contagem `detections`. |
| `GENVEG` | Classe genérica de vegetação (cobertura do solo) no foco | código | Veja §3. |
| `LATI`   | Latitude | graus decimais (WGS84) | |
| `LONGI`  | Longitude | graus decimais (WGS84) | |
| `AREA`   | Área queimada do registro (um pedaço `GENVEG` de um ponto) | m² | Some `AREA` sobre os registros para a área queimada total (a etapa 04 grava `burned_km2`). |
| `BMASS`  | Biomassa queimada por unidade de área | kg/m² | FINNv2.5+. |

## 2. Campos de emissão (espécies)

As espécies gasosas são emitidas como **mol(espécie)/dia**; os aerossóis como
**kg(espécie)/dia** (README oficial do FINN); `NOXasNO`, `NMOC` e `NMHC` estão em
**kg/dia** (veja a nota de unidades acima). O conjunto exato de espécies
depende da versão do FINN e do mecanismo de especiação de COV (este pipeline usa
o mecanismo **GEOS-Chem**). As massas molares abaixo são as aplicadas por
`01_convert_units` (config/config.yml). Revisão 2026-10-03: conferidas com as
fórmulas moleculares (pesos atômicos padrão; banco de espécies do GEOS-Chem);
GLYC, GLYX, HAC, MGLY e H2 foram corrigidas e NMHC passou para a lista kg/dia
(o script original `01-conversao_unidade_FINN.R` usava 92,09, 86,09 [grafado
"CLYX", de modo que o glioxal nunca era convertido], 60,05, 74,08, 2,02 e NMHC 72,00).

| Abrev. | Espécie (PT) | Unidade bruta | Massa molar (g/mol) |
|--------|--------------|---------------|---------------------|
| `CO2`  | Dióxido de carbono | mol/dia | 44,01 |
| `CO`   | Monóxido de carbono | mol/dia | 28,01 |
| `CH4`  | Metano | mol/dia | 16,04 |
| `H2`   | Hidrogênio molecular | mol/dia | 2,016 |
| `SO2`  | Dióxido de enxofre | mol/dia | 64,07 |
| `NH3`  | Amônia | mol/dia | 17,03 |
| `NO`   | Óxido nítrico | mol/dia | 30,01 |
| `NO2`  | Dióxido de nitrogênio | mol/dia | 46,01 |
| `NMHC` | Hidrocarbonetos não metânicos (agregado) | **kg/dia** | convertido via ÷1000 (revisão 2026-10-03; antes ×72/10⁶ → 13,9× menor) |
| `ACET` | Acetona | mol/dia | 58,08 |
| `ALD2` | Acetaldeído | mol/dia | 44,05 |
| `ALK4` | Alcanos C4+ | mol/dia | 58,12 |
| `BENZ` | Benzeno | mol/dia | 78,11 |
| `C2H2` | Acetileno | mol/dia | 26,04 |
| `C2H4` | Etileno | mol/dia | 28,05 |
| `C2H6` | Etano | mol/dia | 30,07 |
| `C3H8` | Propano | mol/dia | 44,10 |
| `CH2O` | Formaldeído | mol/dia | 30,03 |
| `GLYC` | Glicolaldeído (C₂H₄O₂) | mol/dia | 60,05 |
| `GLYX` | Glioxal (C₂H₂O₂) | mol/dia | 58,04 |
| `HAC`  | Hidroxiacetona (C₃H₆O₂) | mol/dia | 74,08 |
| `MEK`  | Metil-etil-cetona | mol/dia | 72,11 |
| `MGLY` | Metilglioxal (C₃H₄O₂) | mol/dia | 72,06 |
| `PRPE` | Propeno | mol/dia | 42,08 |
| `TOLU` | Tolueno | mol/dia | 92,14 |
| `XYLE` | Xilenos | mol/dia | 106,17 |
| `OC`   | Carbono orgânico (aerossol) | **kg/dia** | convertido via ÷1000 |
| `BC`   | Carbono negro (aerossol) | **kg/dia** | convertido via ÷1000 |
| `PM25` | Material particulado ≤ 2,5 µm | **kg/dia** | convertido via ÷1000 |
| `PM10` | Material particulado ≤ 10 µm | **kg/dia** | convertido via ÷1000 |

Espécies agregadas/em massa adicionais (kg/dia → toneladas): `NOXasNO` (NOx
expresso como massa de NO), `NMOC` (total de gases orgânicos não metânicos,
identificados + não identificados), `TPM` (material particulado total), `TPC`
(carbono particulado total).

**Definições de reporte (revisão 2026-10-03).**
- **NOx = `NOXasNO`** (massa como NO). `NO` e `NO2` são saídas especiadas; nunca
  some-as como "NOx". A etapa 04 também grava `NOx_as_NO2` = `NOXasNO` ×
  46,0055/30,0061 (massa equivalente em NO2).
- **COV = `NMOC`**. Não some as espécies especiadas do GEOS-Chem para obter o
  total de COV: `NMHC` se sobrepõe aos hidrocarbonetos individuais (dupla
  contagem) e a lista de espécies não cobre a massa de NMOG não identificada.

> **Resumo da conversão.**
> Gás: `toneladas = mol × massa_molar[g/mol] / 1 000 000`.
> Aerossol/massa: `toneladas = kg / 1000`.

## 3. Classes de cobertura do solo `GENVEG` (FINN v2.5)

| Código | Classe |
|--------|--------|
| 0 | Sem vegetação |
| 1 | Pastagens e savana |
| 2 | Savana lenhosa / arbustos |
| 3 | Floresta tropical |
| 4 | Floresta temperada |
| 5 | Floresta boreal |
| 6 | Floresta perenifólia temperada |
| 9 | Áreas agrícolas (culturas) |

*(FINN v1/v1.5 usam um esquema de vegetação genérica comparável; consulte o
README da v1 para as classes exatas dessa versão.)*

## 4. Mecanismos de especiação de COV

Cada arquivo "eachfire" do FINN v2.5 fornece emissões de COV especiadas para três
mecanismos químicos: **MOZART-T1** (v2.0), **SAPRC99** (v1.0) e **GEOS-Chem**
(v1.0). Este pipeline usa a especiação **GEOS-Chem** em todo o processo,
correspondendo à tabela de espécies acima.

## 5. Colunas adicionadas por este pipeline

| Coluna | Adicionada em | Significado |
|--------|---------------|-------------|
| `source_url` | `00_download` | URL de origem de cada registro bruto (proveniência; opcional). |
| `DATE` | `01_convert` | Data de calendário `YYYY-MM-DD` (de `DAY` + ano). Adicionada **apenas** quando um intervalo `start_date`/`end_date` é definido. |
| `year` | `02`/`03`/`04` | Ano de referência (extraído do nome do arquivo). |
| `sensor` | `02`/`03`/`04` | `MODIS` ou `MODIS+VIIRS`. |
| `version` | `02`/`03`/`04` | Versão do FINN (`v1.5`, `v2.5`, `v2.5.1`). |
| `n_rows` | `04_aggregate` | Número de registros FINN (pedaços FIREID × GENVEG) no polígono — diagnóstico, **não** é número de queimadas (revisão 2026-10-03: substitui `focos`). |
| `events` | `04_aggregate` | Eventos de fogo = (ano, `DAY`, `POLYID`) distintos; cada evento é atribuído a UM polígono, o que contém a maior parcela de sua `AREA` (empate: primeiro nome). NA no FINN v1.5 (sem POLYID). |
| `detections` | `04_aggregate` | (ano, `DAY`, `FIREID`) distintos, atribuídos da mesma forma. NA no v1.5. |
| `burned_km2` | `04_aggregate` | Σ `AREA` / 10⁶ (área queimada FINN, km²). Não é o `AREA_KM2` do shapefile, que é a área do próprio polígono. |
| `NOx_as_NO2` | `04_aggregate` | `NOXasNO` × 46,0055/30,0061 (config `derived.nox_as_no2`). |
| `period` | `04_aggregate` | Balde de tempo na `aggregation.time_resolution`: `"2019"` (ano), `"2019-06"` (mês) ou `"2019-06-15"` (dia). |
| `region_field` | `04_aggregate` | O atributo de agrupamento do seu shapefile (padrão `NM_MUN`). |
| *(atributos do shapefile)* | `04_aggregate` | Todas as colunas de atributo da camada de limites são mantidas (na camada IBGE padrão: `CD_MUN`, `AREA_KM2` = área do município, …). |

> O nome da coluna de agrupamento é o que `region.region_field` indicar — `NM_MUN`
> para os municípios do IBGE padrão, ou p. ex. `NAME` / `shapeName` para uma
> camada de país/administrativa. Apenas espécies FINN reconhecidas (§2) são
> somadas; outros atributos numéricos do shapefile são mantidos, não agregados.

> **Nota sobre shapefile.** Shapefiles ESRI truncam nomes de campo em 10
> caracteres. `04_aggregate_region` grava tanto um `.csv` com nomes
> completos quanto um `.shp` truncado; use o `.csv` quando precisar dos nomes de
> coluna sem truncamento.

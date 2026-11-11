# Metodologia

> 🌐 [English](methodology.md) · **Português (pt-BR)**

Este documento explica (a) como o próprio inventário FINN é construído (para que
você descreva corretamente sua fonte de dados em um artigo ou relatório) e (b) o
que este pipeline faz para transformar os arquivos FINN globais em um inventário
municipal de emissões de Santa Catarina. As citações usam as chaves de
[`../references.bib`](../references.bib); detalhes completos em
[`../REFERENCES.md`](../REFERENCES.md).

> As estatísticas, a triagem e as figuras do artigo e do relatório do inventário
> (eventos, anomalias térmicas persistentes, tendências, comparação com o MapBiomas, associações com o
> clima e com a cobertura da terra, densidade kernel) estão descritas em [`analysis.pt-BR.md`](analysis.pt-BR.md).

---

## 1. Como o FINN estima as emissões de queimadas

O **Fire INventory from NCAR (FINN)** produz emissões diárias e globais de queima
a céu aberto na resolução de detecção de focos (~1 km) (Wiedinmyer et al., 2011,
2023). Para cada foco detectado, as emissões de uma espécie *i* são estimadas
como o produto de quatro fatores (a forma clássica de Seiler–Crutzen usada pelo
FINN):

```
E_i = A × B × FB × EF_i
```

onde

- **A** — área queimada do foco (m²), inferida da detecção de fogo ativo por
  satélite;
- **B** — carga de combustível / densidade de biomassa (kg m⁻²) do tipo de
  cobertura do solo;
- **FB** — a fração da biomassa efetivamente queimada (completude da combustão);
- **EF_i** — o fator de emissão da espécie *i* (g da espécie por kg de matéria
  seca queimada).

O tipo de cobertura do solo em cada foco (a classe `GENVEG`) seleciona a carga de
combustível, a completude da combustão e o conjunto de fatores de emissão. Os
fatores de emissão do FINN se baseiam em compilações como **Akagi et al. (2011)**
e, mais recentemente, **Andreae (2019)**. As emissões totais de COV não metânicos
são então **especiadas** em espécies prontas para modelo, para três mecanismos
químicos (MOZART-T1, SAPRC99, GEOS-Chem); este pipeline usa a especiação
**GEOS-Chem**.

### Entradas de satélite

O FINN é alimentado pelas detecções de fogo ativo do **FIRMS** da NASA:

- **MODIS** Coleção 6 de fogo ativo (Giglio et al., 2016) — disponível de
  2002 até o presente; base da configuração `MODIS`.
- **VIIRS** 375 m de fogo ativo (Schroeder et al., 2014) — disponível de 2012
  até o presente; combinado ao MODIS na configuração `MODIS+VIIRS` (FINN v2.5+).

Como um sensor mais grosseiro detecta menos focos (e focos de borda) do que um
mais fino, o produto `MODIS+VIIRS` geralmente reporta **mais** focos (e
frequentemente totais maiores) do que apenas `MODIS` para o mesmo período —
mantenha a escolha de sensor consistente ao comparar anos.

### Versões e disponibilidade

| Versão | Sensor(es) | Cobertura temporal | Granularidade |
|--------|-----------|--------------------|---------------|
| v1.5 | MODIS | 2002–2020 | anual |
| v2.5 | MODIS | 2003–2021 | anual |
| v2.5 | MODIS+VIIRS | 2012–2021 | anual |
| v2.5.1 | MODIS / MODIS+VIIRS | 2022–2023 | mensal |
| v2.5.1 (NRT) | MODIS+VIIRS | 2024–presente | diária (tempo quase real) |

Os arquivos em tempo quase real (NRT) são provisórios; detecções de qualidade de
arquivo são usadas para os anos finalizados (veja o README do FINNv2.5). Trate os
anos NRT como preliminares.

> **Ressalvas dignas de menção em um relatório.** As emissões do FINN têm
> incerteza substancial devido a lacunas de nuvem/passagem na detecção de fogo
> ativo, à hipótese de área por detecção, às estimativas de carga de combustível
> e completude de combustão, e aos fatores de emissão. Fogos pequenos/curtos ou
> de sub-bosque podem não ser detectados. Comparar com um inventário independente
> como o **GFED4s** (van der Werf et al., 2017) e com estudos regionais (ex.:
> Teixeira et al., 2025, para o Sul do Brasil) é uma boa prática.

---

## 2. O que este pipeline faz

O pipeline transforma os arquivos de texto FINN globais e brutos em um
**inventário de emissões por polígono da região**, em toneladas por período,
pronto para tabelas, figuras e QGIS. A região é qualquer shapefile que você
configurar — **municípios de Santa Catarina, por padrão**, mas qualquer estado,
país ou polígono funciona da mesma forma. As etapas espelham os scripts
numerados (lógica idêntica em R e Python).

### Etapa 00 — Baixar e mesclar (`00_download_*`)

Constrói as URLs exatas de download do FINN para o(s) ano(s)/versão/sensor
solicitados, baixa os arquivos de texto GEOS-Chem compactados dos servidores
UCAR/ACOM e NSF NCAR RDA, mescla-os, remove linhas duplicadas e grava um CSV
combinado por ano em `data/raw_finn/`. Os arquivos FINN v1.5, cujos cabeçalhos
não são autoexplicativos, recebem os nomes de coluna fixos corretos; para v2.5+
uma coluna opcional de proveniência `source_url` é anteposta (delimitada por
vírgula, de modo que a saída é um CSV limpo). Os arquivos anuais do FINN v1.5 são
distribuídos como arquivos `.tar.gz`, enquanto os arquivos v2.5+/NRT são
`.txt.gz`; o downloader detecta e lê ambos. Como cada produto anual é um único
arquivo por ano, o download é essencialmente um custo único — todas as etapas
seguintes reutilizam o CSV combinado em `data/raw_finn/`.

### Etapa 01 — Conversão de unidades (`01_convert_units`)

Converte cada coluna de emissão das unidades nativas do FINN para **toneladas
métricas**: gases via massa molar (`mol × g mol⁻¹ / 10⁶`) e aerossóis via
`kg / 1000` (veja [`data_dictionary.pt-BR.md`](data_dictionary.pt-BR.md)). Grava
`*_converted.csv` em `data/interim/`.

*Revisão 2026-10-03.* `NOXasNO`, `NMOC` e `NMHC` são campos de **massa em
kg/dia** nos arquivos v2.5/v2.5.1 (apesar de o README dizer "todas as espécies
gasosas em mol/dia"): seus fatores de emissão implícitos, espécie / (`AREA` ×
`BMASS`), reproduzem a Tabela 4 de Wiedinmyer et al. (2023) apenas em kg/dia,
então são convertidos com `kg / 1000`. O NMHC era convertido como gás (× 72
g mol⁻¹), o que o subestimava por um fator 1000/72 = 13,9. As massas molares de
GLYC (60,05), GLYX (58,04), HAC (74,08), MGLY (72,06) e H2 (2,016) foram
corrigidas a partir das fórmulas moleculares. Definições de reporte: **NOx =
`NOXasNO`** (massa como NO; `NO` + `NO2` nunca devem ser somados como NOx; a
etapa 04 acrescenta `NOx_as_NO2` = `NOXasNO` × 46,0055/30,0061) e **COV = `NMOC`**
(total de gases orgânicos não metânicos; as espécies especiadas não são somadas,
pois `NMHC` se sobrepõe aos hidrocarbonetos individuais).

### Etapa 02 — Recorte para a região (`02_clip_region`)

Mantém apenas os registros dentro dos **polígonos** da região: um pré-filtro por
caixa delimitadora (config `region.bbox`) seguido de um teste ponto-em-polígono
contra o shapefile de limites (revisão 2026-10-03: antes a etapa 02 parava na
caixa, e os arquivos de pontos e a tabela empilhada da etapa 03 continham pontos
de estados/países vizinhos e do oceano; o shapefile agora é obrigatório aqui).
Detalhes da caixa (config `region.bbox`): Com `bbox: auto` (padrão) a caixa é derivada da própria extensão
do shapefile configurado (+ `bbox_margin_deg`), então a etapa se adapta a
qualquer região; `bbox: none` pula o pré-filtro, e graus explícitos também são
aceitos. Esse pré-filtro reduz a nuvem de pontos global antes da junção
ponto-em-polígono, mais cara. É uma **comparação vetorizada de coordenadas**
(LONGI/LATI entre os limites) — exata para um retângulo lon/lat e drasticamente
mais rápida do que construir pontos `sf` e rodar `st_within` sobre milhões de
registros (a abordagem dos scripts originais), então permanece rápida mesmo na
nuvem global completa. Grava
`filtered_points_<ano>_<sensor>_<versão>_converted_within_grid.csv`.

### Etapa 03 — Empilhar anos (opcional) (`03_stack_years`)

Concatena todos os arquivos de pontos recortados em uma única tabela longa,
rotulada com `year`, `sensor`, `version` — conveniente para análise multianual no
nível de ponto.

### Etapa 04 — Agregar por polígono da região (`04_aggregate_region`)

Realiza uma **junção espacial** ponto-em-polígono dos focos contra o **shapefile
de limites** configurado (`region.boundaries_shp`; padrão
`data/inputs/SC_Municipios_2024.shp`), soma cada espécie FINN por polígono
(agrupando por `region.region_field`, padrão `NM_MUN`), conta as queimadas,
empilha todos os anos/sensores/versões, une os totais de volta à geometria do
polígono e grava:

- `data/output/aggregated_emissions_all.csv` — nomes de coluna completos;
- `data/output/aggregated_emissions_all.shp` — para o QGIS (campos de 10 caracteres).

**Contagem de queimadas (revisão 2026-10-03).** Um registro FINN é um pedaço de
cobertura do solo (`GENVEG`) de um ponto de fogo, portanto o número de registros
não é número de queimadas (a antiga coluna `focos`, agora `n_rows`). Nos arquivos
v2.5/v2.5.1, `POLYID` é o polígono diário de área queimada (detecções adjacentes
fundidas; pode conter vários pontos) e `FIREID` é um ponto dentro dele. A etapa
04 reporta **`events`** = (ano, `DAY`, `POLYID`) distintos, cada um atribuído a UM
polígono, o que contém a maior parcela de sua `AREA` (empate: primeiro nome), e
**`detections`** = (ano, `DAY`, `FIREID`) distintos, atribuídos da mesma forma,
de modo que as contagens por polígono somam o total regional. Grava também
`burned_km2` = Σ`AREA`/10⁶ (o `AREA_KM2` do shapefile é a área do próprio
polígono, não área queimada). O FINN v1.5 não tem `POLYID`/`FIREID`, então
`events`/`detections` são NA nele. **Proteções contra duplicatas:** a execução
para se dois arquivos de entrada corresponderem ao mesmo (ano, sensor, versão) —
o mecanismo que colocou duas vezes as linhas de 2011 MODIS v2.5 no antigo
`aggregated_emissions_all.csv` —, registros idênticos são removidos e chaves
(`source_url`, `DAY`, `POLYID`, `FIREID`, `GENVEG`) repetidas são apenas
relatadas, pois o FINN contém registros distintos que compartilham essa chave.

Apenas espécies FINN reconhecidas são somadas, então atributos numéricos extras
do shapefile (população, área, códigos) nunca são confundidos com emissões. O
grão temporal de cada linha é definido por `aggregation.time_resolution` (`day`,
`month` ou `year`) e registrado em uma coluna `period`, com uma coluna numérica
`year` sempre mantida ao lado; os totais são conservados entre resoluções (somar
as linhas mensais/diárias de um polígono reproduz o seu total anual). O filtro
por caixa delimitadora (etapa 02) é grosseiro e é seguido, na própria etapa 02,
por um teste ponto-em-polígono; a atribuição ao polígono aqui usa o mesmo teste
(`within`, planar, em R e Python).

### Etapa 05 — Análise descritiva (`05_descriptive_analysis`)

Lê o inventário agregado e produz uma figura anual de 4 painéis (eventos de fogo,
área queimada `burned_km2`, CO, PM₂,₅), uma tabela-resumo anual dos principais
poluentes (incluindo `NOXasNO`, `NOx_as_NO2`, `NMOC` = COV, `events`,
`detections`) e,
quando há várias versões/sensores, uma comparação de CO₂ por versão × sensor.
Também desenha uma **série temporal na `aggregation.time_resolution` configurada**
(`timeseries_<res>.png` — CO, PM₂,₅, CO₂ e eventos de fogo totais da região versus
`period`) com um `period_summary_<res>.csv` correspondente, então uma série mensal
ou diária sai pronta.

---

## 3. Notas de reprodutibilidade

- Todos os parâmetros ajustáveis (anos, versão, sensor, caixa delimitadora,
  caminhos, massas molares) ficam em [`../config/config.yml`](../config/config.yml);
  os scripts não têm parâmetros de estudo fixos no código.
- As rotas R e Python leem essa **mesma** configuração e produzem os mesmos nomes
  de arquivo intermediário/final, então você pode misturar rotas (ex.: baixar em
  R, analisar em Python).
- As operações espaciais usam `sf` em R (Pebesma, 2018) e `geopandas` em Python;
  ambas reprojetam os pontos para o CRS do shapefile antes da junção.
- O FINN, os limites do IBGE e (opcionalmente) o Programa Queimadas do INPE são
  entradas externas; sua proveniência e URLs de acesso estão em
  [`../REFERENCES.md`](../REFERENCES.md).

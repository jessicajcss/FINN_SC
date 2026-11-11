# `data/inputs/` — camadas de entrada externas

> ✅ **Incluído (v2.0.0):** `SC_Municipios_2024.shp` (+ `.dbf/.shx/.prj`), Malha Municipal do IBGE de 2024 para Santa Catarina, o mesmo arquivo usado nos resultados publicados (somas SHA-256 em `docs/provenance.md`, seção 2). Na versão 1.x esta nota já dizia isso, mas só o `.prj` e o `.shx` estavam presentes. As instruções abaixo servem para atualizar o arquivo ou usar outra região.


> 🌐 [English](README.md) · **Português (pt-BR)**

O pipeline precisa de um **shapefile de limites (polígonos)** para atribuir cada
foco a uma região (etapa 04). O **padrão** são os municípios de Santa Catarina
(IBGE), mas **qualquer camada de polígonos funciona** — outro estado brasileiro,
um país, um grupo de países, um bioma, uma bacia. Essa camada *não* é
redistribuída aqui; coloque o seu `.shp` (+ `.dbf/.shx/.prj`) nesta pasta e
aponte `region.boundaries_shp` / `region.region_field` para ele em
`config/config.yml`.

As instruções abaixo são para o **padrão** (municípios de SC do IBGE). Para
qualquer outra região, baixe a camada correspondente (ex.: GADM, Natural Earth,
geoBoundaries para países/unidades administrativas) e defina `region.region_field`
para o atributo de nome dela (`shapeName`, `NAME`, `ADM0_NAME`, …).

## Limites municipais (Malha Municipal do IBGE)

1. Acesse a página da Malha Municipal do IBGE:
   <https://www.ibge.gov.br/geociencias/organizacao-do-territorio/malhas-territoriais/15774-malhas.html>
2. Baixe a malha municipal para o ano de referência desejado (os scripts assumem
   **2024**). Você pode baixar diretamente o arquivo do estado de Santa Catarina
   (SC) ou o arquivo nacional e filtrar por `SIGLA_UF == "SC"`.
3. Descompacte de modo que esta pasta contenha, no mínimo:

   ```
   data/inputs/SC_Municipios_2024.shp
   data/inputs/SC_Municipios_2024.dbf
   data/inputs/SC_Municipios_2024.shx
   data/inputs/SC_Municipios_2024.prj
   ```

   Se o seu download tiver outro nome de arquivo, renomeie para
   `SC_Municipios_2024.*` ou atualize `region.boundaries_shp` em
   `config/config.yml`.

## Colunas de atributo esperadas

Os scripts usam estes campos de atributo (padrões em `config.yml` para a camada
SC do IBGE):

| Campo     | Significado                       | Chave de configuração         |
|-----------|-----------------------------------|-------------------------------|
| `NM_MUN`  | Nome do município                 | chave de agrupamento (`region.region_field`) |
| `CD_MUN`  | Código municipal do IBGE          | identificador (`region.code_field`)          |
| `AREA_KM2`| Área do município (km²)           | normalização opcional por área |

Para uma **camada diferente**, defina `region.region_field` para o atributo que
contém o nome/id do polígono pelo qual você quer agregar (e `region.code_field`
para um id secundário opcional, ou `~` para nenhum). A mensagem de erro da etapa
04 lista as colunas disponíveis se o campo configurado não for encontrado.

## Sistema de referência de coordenadas

As coordenadas do FINN são geográficas WGS84 (EPSG:4326). O pipeline reprojeta os
pontos para o CRS do shapefile antes da junção espacial, então qualquer CRS no
arquivo do IBGE serve.

> Citação da fonte de dados: IBGE — Instituto Brasileiro de Geografia e
> Estatística, Malha Municipal Digital. Veja `../../REFERENCES.md`.

# FINN_SC: emissões da queima de biomassa em Santa Catarina

> 🌐 [English](README.md) · **Português (pt-BR)**

Código, dados e documentação que reproduzem as tabelas, as estatísticas e as figuras do artigo *Variabilidade
espaço-temporal das emissões da queima de biomassa em Santa Catarina (Brasil) entre 2012 e 2025* e do relatório
*Inventário das emissões pela queima de biomassa na qualidade do ar em Santa Catarina, ano-base 2025*. A base é o
Fire INventory from NCAR (FINN; Wiedinmyer et al., 2011, 2023). O mesmo código monta um inventário do FINN para
qualquer outra região.

* **Endereço:** https://github.com/jessicajcss/FINN_SC (antes da publicação, o endereço será substituído por um DOI
  do Zenodo).
* **Contato:** J. C. dos Santos Silva, jessica.jcss@gmail.com.
* **Licença:** código e documentação sob a licença [MIT](LICENSE). Os dados seguem os termos dos provedores (FINN/NSF
  NCAR, MapBiomas, IBGE, NASA LP DAAC, ERA5-Land/Copernicus, NOAA).
* **Tutorial ilustrado:** [`TUTORIAL_FINN_SC_pt.pdf`](TUTORIAL_FINN_SC_pt.pdf) (português) e
  [`TUTORIAL_FINN_SC_en.pdf`](TUTORIAL_FINN_SC_en.pdf) (inglês), com execução passo a passo no Google Colab e no
  Earth Engine (capítulo 12), do conceito ao comando, para iniciantes e
  especialistas.

---

## Em três passos

```bash
git clone https://github.com/jessicajcss/FINN_SC.git
cd FINN_SC

# 1. Instalação (uma vez)
conda env create -f environment.yml && conda activate finn   # ou: python -m pip install -r requirements.txt
Rscript install_r_packages.R                                  # R, só para a densidade kernel (opcional)

# 2. Reprodução dos resultados (rota B, sem download)
python python/run_analysis.py --no-r     # sem --no-r, roda também o R (a sensibilidade anual leva cerca de 40 min)

# 3. Conferência
python -m pytest -q tests                # esperado: 96 passed
python tools/verify_manifest.py          # esperado: 107 files: OK 107
```

Atalhos: `make reproduce`, `./run_all.sh analysis` (Linux, macOS) ou `run_all.bat analysis` (Windows). As saídas
ficam em `results/tables/`, `results/figures/` e `results/logs/`. As cópias guardadas no repositório são as saídas
publicadas, e `tools/verify_manifest.py` compara as suas com elas pela soma SHA-256 (`results/MANIFEST.sha256`).

## Duas rotas

| Rota | Parte de | Serve para |
|---|---|---|
| **B, reprodução** | `data/derived/finn_sc_records_2003_2025.csv.gz` (258.694 registros do FINN v2.5 e v2.5.1 em SC, 2003 a 2025) e `data/external/` | refazer cada número do artigo e do relatório, sem internet |
| **A, replicação** | arquivos do FINN baixados do NSF NCAR (`python/00` a `02` e `06`) | reconstruir os registros ou montar o inventário de outra região; `tests/test_route_a.py` replica os 2.341 registros de 1º de janeiro a 28 de maio de 2025 |

## Definições usadas em todo o repositório

* **Registro:** uma linha de um arquivo do FINN.
* **Detecção:** combinação de dia e `FIREID`, um pixel de fogo ativo do satélite.
* **Evento de queimada:** polígono diário de área queimada do FINN (`POLYID`), atribuído ao município com a maior
  parte da sua área.
* **Anomalia térmica persistente:** ponto com detecções em 16 dias ou mais do ano civil num raio de 1 km (critério do
  produto MODIS; Giglio et al., 2021). Sai das contagens e dos mapas e permanece nos totais de emissão.
* **NOₓ** = `NOXasNO` (massa de NO). **COV** = `NMOC`. Unidade das emissões: toneladas.

## Arquivos do FINN: diferenças em relação ao README do NCAR e convenções do modelo

Este código segue os arquivos do FINN nos pontos em que eles diferem do README que o NSF NCAR distribui com o FINN v2.5
(junho de 2024; `docs/README_FINNv2.5_June2024.pdf`; Wiedinmyer e Emmons, 2022), e quem usa o FINN precisa conhecer duas convenções do modelo que alteram as contagens
regionais:

* **Unidades dos campos agregados.** O README informa as espécies gasosas em mol dia⁻¹, mas nos arquivos GEOS-Chem do
  v2.5 e do v2.5.1 os campos `NOXasNO`, `NMOC` e `NMHC` estão em kg dia⁻¹: só assim os fatores de emissão implícitos
  nesses campos coincidem com a Tabela 4 de Wiedinmyer et al. (2023). Lidos como mols, o NOXasNO ficaria cerca de 33
  vezes menor e o NMHC cerca de 14 vezes menor. O `python/finn_sc/convert_units.py` trata os três campos como massa, e o
  `python/analysis/a09_emission_factor_check.py` confere todas as espécies (`results/tables/emission_factor_check.csv`).
* **Identificadores.** O README descreve o `POLYID` como o identificador de cada ponto de fogo e o `FIREID` como o fogo
  ao qual os pontos pertencem. Nos arquivos, cada `FIREID` tem uma só coordenada (151.436 de 151.441 por produto e dia)
  e um `POLYID` reúne vários `FIREID` (20.766 de 124.602). Detecções e eventos de queimada seguem os arquivos.
* **Repetição no dia seguinte.** O FINN v1.5 conta cada detecção MODIS entre cerca de 30° N e 30° S também no dia
  seguinte, com metade das emissões, a menos que o pixel seja detectado de novo (Wiedinmyer et al., 2011): 1.893 dos
  4.609 registros do FINN v1.5 de Santa Catarina em 2020 são essas continuações (`python/analysis/a17_v72_review.py`). O
  FINN v2.5 conta o fogo por dois dias apenas entre cerca de 23,5° N e 23,5° S (Wiedinmyer et al., 2023), faixa que não
  inclui Santa Catarina; em regiões dentro dessa faixa, registros, detecções e eventos incluem repetições que este
  código não separa.
* **Classe florestal pela latitude.** O FINN v2.5 classifica as florestas latifoliadas perenes e as mistas fora da faixa
  de cerca de 23,5° N a 23,5° S como floresta temperada (Wiedinmyer et al., 2023, Tabela 1). Com as cargas de
  combustível da América do Sul e os fatores de emissão da floresta tropical, cada detecção florestal de Santa Catarina
  emitiria 3,9 vezes mais CO₂, e o Estado, de 2,42 a 2,74 vezes mais CO₂ por ano
  (`python/analysis/a19_v72_followup.py`). A conferência dos fatores de emissão não revela essa escolha.

## Onde está cada coisa

```
FINN_SC/
├── README.md, README.pt-BR.md        esta página (EN / PT)
├── TUTORIAL_FINN_SC_pt.pdf, _en.pdf  tutorial ilustrado (PT / EN; fontes em docs/tutorial_v2/)
├── CITATION.cff, LICENSE, CHANGELOG.md, REFERENCES.md, references.bib
├── requirements*.txt, environment.yml, install_r_packages.R, Makefile, run_all.sh, run_all.bat
├── config/config.yml                 todos os parâmetros (anos, versão, sensor, região, massas molares)
├── data/derived/                     registros arquivados do FINN em SC (insumo da rota B)
├── data/external/                    MapBiomas, MCD64A1, ERA5-Land, ONI, IBGE, inventário de 2020
├── data/inputs/                      malha municipal de SC do IBGE de 2024
├── python/00_… 06_*.py               rota A em Python
├── python/analysis/a01_… a20_*.py    rota B, um script por grupo de resultados
├── python/finn_sc/                   funções comuns (unidades, datas, eventos, estatística, mapas)
├── python/run_analysis.py            rota B em um comando
├── R/                                rota A em R e a densidade kernel (R/analysis/kde_events.R)
├── gee/                              receitas do Google Earth Engine para os dados externos
├── notebooks/                        rota A em notebooks (FINN_SC_Python.ipynb, FINN_SC_R.ipynb) e a
│                                     comparação com o BRAIN, 2019 e 2020 (BRAIN_FINN_comparison_SC.ipynb)
├── tools/                            mapa da área de estudo, fluxograma, verificação BRAIN, verify_manifest.py
├── tests/                            96 testes automáticos
├── results/                          tabelas, figuras e registros de execução publicados (brain_2019/, brain_2020/: BRAIN)
└── docs/                             métodos, procedência, dicionário de dados, mapa dos resultados
```

## Mapa da documentação

| Quero… | Leia |
|---|---|
| aprender o método e rodar tudo, no computador ou no Google Colab | [`TUTORIAL_FINN_SC_pt.pdf`](TUTORIAL_FINN_SC_pt.pdf) |
| achar o script e o arquivo de cada número ou figura publicada | [`docs/results_map.pt-BR.md`](docs/results_map.pt-BR.md) |
| ler os métodos da camada de análise | [`docs/analysis.pt-BR.md`](docs/analysis.pt-BR.md) |
| entender o FINN e a rota A, com citações | [`docs/methodology.pt-BR.md`](docs/methodology.pt-BR.md) |
| saber de onde vem cada insumo, com somas SHA-256 | [`docs/provenance.pt-BR.md`](docs/provenance.pt-BR.md) |
| consultar um campo, uma unidade ou um código | [`docs/data_dictionary.pt-BR.md`](docs/data_dictionary.pt-BR.md) |
| ver como a reprodução foi testada | [`docs/reproducibility.pt-BR.md`](docs/reproducibility.pt-BR.md) |

## Google Colab e Earth Engine

1. Registre um projeto do Google Cloud para o Earth Engine em https://console.cloud.google.com/earth-engine (o uso não
   comercial dispensa faturamento) e anote o ID.
2. No Colab, clone ou descompacte o repositório em `/content/FINN_SC` e rode a rota B como acima (`--no-r`).
3. Em cada notebook de `gee/`, troque `PROJECT = "<ID do seu projeto>"` na célula 2 e rode tudo. A célula 3 chama
   `ee.Authenticate()` e `ee.Initialize(project=PROJECT)`.

Passo a passo, com as saídas de cada notebook: capítulo 12 do tutorial.

## Usar outra região (rota A)

1. Coloque o shapefile da região em `data/inputs/`.
2. No `config/config.yml`, ajuste `region.boundaries_shp`, `region.region_field` e `region.name`, e escolha anos,
   versão e sensor no bloco `selection`.
3. Rode `make all-py` (ou `./run_all.sh python`, ou `run_all.bat python`). As etapas também rodam uma a uma, de
   `python python/00_download_finn.py` a `python python/05_descriptive_analysis.py`.
4. Abra `data/output/aggregated_emissions_all.shp` no QGIS ou leia `data/output/aggregated_emissions_all.csv`.

O download é a parte demorada, porque os arquivos anuais do FINN são grandes. Convém começar por um ano.

## Como citar

Cite este repositório (ver [`CITATION.cff`](CITATION.cff)), o artigo do FINN da versão usada (Wiedinmyer et al.,
2011, para a v1.5; Wiedinmyer et al., 2023, para a v2.5) e o conjunto de dados do FINN no NSF NCAR (Wiedinmyer;
Emmons, 2022, DOI 10.5065/XNPA-AF09).

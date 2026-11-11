# Camada de análise: métodos

> 🌐 [English](analysis.md) · **Português (pt-BR)**

Este documento descreve como `python/analysis/` e `R/analysis/` transformam os registros do FINN em Santa
Catarina em cada tabela, estatística e figura do artigo (v5) e do relatório do inventário (v2). A origem de
cada entrada está em [`provenance.pt-BR.md`](provenance.pt-BR.md), e o local onde cada número é publicado,
com o teste que o confere, em [`results_map.pt-BR.md`](results_map.pt-BR.md).

## 1. Duas rotas

```
Rota A (replicação a partir do FINN bruto)             Rota B (reprodução a partir do arquivo)
python/00_download_finn.py   arquivos brutos do FINN   data/derived/finn_sc_records_2003_2025.csv.gz
python/01_convert_units.py   -> toneladas                        |
python/02_clip_region.py     -> pontos dentro de SC              v
python/06_build_sc_records.py -> tabela de registros ---> python/run_analysis.py
                         (comparação: tools/compare_records.py)  a01 ... a09 (Python), kde_events.R (R), a10 (figuras)
                                                                 -> results/tables, results/figures, results/logs
                                                       python -m pytest -q tests
```

A rota A exige acesso à internet e vários GB de arquivos do FINN, e foi validada com os registros brutos do
FINN v2.5.1 NRT de 1º de janeiro a 28 de maio de 2025 (`tests/test_route_a.py`). A rota B usa apenas este
repositório.

## 2. Unidades e espécies

Nos arquivos "each fire" do FINN v2.5/v2.5.1, os gases estão em mol dia⁻¹, os aerossóis (OC, BC, MP2,5 e
MP10) em kg dia⁻¹ e os campos agregados NOXasNO, NMOC e NMHC também em kg dia⁻¹ (a frase do README "all
gas-phase species in mole/day" não vale para esses três campos, cujos fatores de emissão implícitos só
coincidem com os da Tabela 4 de Wiedinmyer et al., 2023, quando lidos como massa). Todas as espécies são
convertidas para toneladas (`config/config.yml`, seção `conversion`). Nos resultados, **NOx = NOXasNO**
(óxidos de nitrogênio expressos como massa de NO; multiplicar por 46,0055/30,0061 para obter o equivalente
em NO₂) e **COV = NMOC** (gases orgânicos não metânicos identificados e não identificados; Wiedinmyer et al.,
2023, Tabela 4, nota e). NO e NO₂ nunca são somados, e as espécies de COV especiadas também não, pois estão
contidas no NMOC. O script `a09_emission_factor_check.py` confere a conversão em todos os registros
arquivados: espécie / (AREA × BMASS) = fator de emissão da Tabela 4 (razões de 0,9986 a 1,0026).

## 3. Unidades de contagem

| Unidade | Definição | 2025 (MODIS+VIIRS, SC) |
|---|---|---|
| registro | uma linha do arquivo do FINN = uma fração (FIREID, GENVEG) | 8.581 |
| detecção | combinação distinta (ano, sensor, versão, DAY, FIREID): uma coordenada | 5.489 |
| evento de queimada | combinação distinta (ano, sensor, versão, DAY, POLYID): polígono diário de área queimada do FINN | 5.160 |

O FINN une as detecções adjacentes ou sobrepostas de um mesmo dia em um polígono de área queimada e divide
cada polígono pelas classes de cobertura da terra (Wiedinmyer et al., 2023, seção 2.2). Nos arquivos
analisados, o POLYID identifica o polígono diário e o FIREID identifica a detecção (o README descreve o
inverso; nos registros de SC, 5 de 151.441 FIREIDs têm mais de uma coordenada e 20.766 de 124.602 POLYIDs
reúnem mais de um FIREID). As frações de uma detecção repartem a área dessa detecção, de modo que a subdivisão
altera as contagens e preserva as emissões. Cada evento é atribuído ao município que detém a maior parte de
sua AREA (empates resolvidos pela ordem alfabética), e as contagens municipais somam o total estadual; 0,8%
dos eventos de 2012 a 2025 tiveram registros em mais de um município. Os antigos "focos" da versão preliminar
contavam registros.

## 4. Anomalias térmicas persistentes

O produto de fogo ativo MODIS C6/C6.1 classifica como fonte estática os locais detectados em 16 dias ou mais
de um ano civil (Giglio et al., 2021, seção 5.5, Tabela 10), e parte das fontes estáticas fica sem essa
marcação no produto (seção 7.2.3). O critério é aplicado sem grade: para cada detecção, conta-se o número de
dias distintos com detecções em um raio de 1 km (distância sobre a esfera; árvore KD na esfera unitária, com
corda ≤ 2 sen(R/2R_T)) no mesmo produto e ano; a detecção com 16 dias ou mais é marcada, e o evento com ao
menos uma detecção marcada também. Raios de 0,75 km e 1,5 km servem de análise de sensibilidade. Os eventos
marcados são excluídos das contagens de eventos, dos mapas e das análises de condicionantes e mantidos nos
totais de área e de emissão (o inventário tal como distribuído). A implementação
(`finn_sc/events.py::flag_persistent`) marca os mesmos 281 eventos da implementação por força bruta com a
fórmula de haversine usada no artigo.

## 5. Séries temporais e tendências (`a02`)

Os totais estaduais por produto e ano vêm de todos os registros, e os eventos, da contagem após a triagem.
A análise usa a série MODIS+VIIRS (v2.5 de 2012 a 2021 e v2.5.1 de 2022 a 2025); a série MODIS ilustra o efeito
da inclusão do VIIRS (razão entre os números de eventos e variação percentual da área e das emissões, na mesma
versão e no mesmo ano). A tendência monotônica é avaliada pelo teste de Mann-Kendall com correção de empates,
aproximação normal e correção de continuidade (Mann, 1945) e pela declividade de Sen (Sen, 1968), para 2012 a
2025 e para 2012 a 2021 (`finn_sc/stats.py`). A autocorrelação de primeira ordem r1 de cada
série é registrada (`mann_kendall.csv`, coluna `r1`; de 0,11 a 0,22 de 2012 a 2025): como a autocorrelação positiva
faz o teste rejeitar a hipótese de ausência de tendência com mais frequência (Hamed; Rao, 1998), os resultados não
significativos não dependem da hipótese de independência entre os anos.

## 6. Resultados municipais e por mesorregião (`a03`)

Emissões e área queimada por município: cada registro é atribuído ao município que contém o seu ponto (IBGE
2024). Eventos: eventos após a triagem, atribuídos como na seção 3. Mesorregiões: divisão do IBGE (1990), com a
correspondência em `data/external/sc_municipios_2024_atributos.csv` (pendência na seção 3 de
`provenance.pt-BR.md`). As densidades usam o `AREA_KM2` do IBGE. A área queimada do FINN soma as áreas nominais
das detecções de cada dia (1 km² no MODIS e 0,14 km² no VIIRS, unidas por dia) e pode contar o mesmo terreno
mais de uma vez; ela supera a área mapeada por um fator mediano de 17 (seção 8), e por isso as frações do
território municipal são indicadores relativos.

## 7. Partição por vegetação (`a04`)

Área, CO₂ e MP2,5 por tipo genérico de vegetação do FINN (GENVEG; Wiedinmyer et al., 2023, Tabela 1). A
biomassa queimada por unidade de área é CO₂ / (AREA × FE_CO₂), igual ao campo BMASS do FINN (os dois valores
são gravados).

## 8. FINN e MapBiomas Fogo (`a05`)

Área estadual e municipal do FINN (MODIS+VIIRS) comparada com a área mapeada pela Coleção 4 do MapBiomas Fogo
(2012 a 2024): razões, correlações de Pearson e de Spearman (com e sem 2012, único ano mapeado só com o Landsat
7), correlação de Spearman municipal por ano, participação dos dez municípios com maior área mapeada e área
mapeada por evento do FINN em cada município (usada no relatório para verificar se uma emissão de CO₂ por
evento elevada corresponde a cicatrizes mapeadas maiores).

## 9. Clima (`a06`)

Médias estaduais do ERA5-Land na estação de queimadas (julho a novembro; 72,1% dos eventos de 2012 a 2025):
precipitação acumulada, temperatura a 2 m, déficit de pressão de vapor pela equação de Tetens e umidade do solo
de 0 a 7 cm (Muñoz-Sabater et al., 2021), além da média do ONI em JAS, ASO e SON. Coeficiente de Spearman entre
cada preditor e cada resposta (eventos, área do FINN, CO₂ e área do MapBiomas), nos níveis e nas primeiras
diferenças, com ajuste de Holm (1979) entre os cinco preditores de cada resposta. O SPI ficou de fora porque o
seu ajuste exige ao menos 30 anos de dados mensais (Svoboda; Hayes; Wood, 2012) e, por ser uma transformação
monotônica da precipitação do mesmo período, teria o mesmo ρ de Spearman.

## 10. Cobertura da terra (`a07`)

Frações municipais de 2023 do MapBiomas (Souza Junior et al., 2020), em arquivo provisório com 277 municípios
(seção 6 de `provenance.pt-BR.md`); quando existe o arquivo dos 295 municípios gerado por
`gee/mapbiomas_lulc_fractions_all295.ipynb`, ele é usado e unido pelo código do IBGE. Respostas: densidade média anual de eventos após a triagem (2012 a 2025);
densidade em 2025; fração queimada segundo o MapBiomas; emissão de CO₂ por evento de 2012 a 2025 (municípios com
14 eventos ou mais). Correlações de Spearman; regressão por mínimos quadrados (erros-padrão de White) do
logaritmo da resposta (log y; municípios com densidade nula são
excluídos e listados no registro) sobre formação campestre, pastagem, agricultura e silvicultura (formação florestal e demais
classes como referência); modelo de erro espacial por máxima verossimilhança (Anselin, 1988; spreg, Rey;
Anselin, 2007) com matriz dos seis vizinhos mais próximos e de contiguidade; índice de Moran dos resíduos da
regressão e dos resíduos filtrados do modelo espacial (999 permutações, semente 20261003); AIC dos dois modelos.
Efeito de +10 pontos percentuais = exp(0,1 b) − 1.

## 11. Densidade kernel (`R/analysis/kde_events.R`)

Eventos de 2025 após a triagem, representados pelo centroide de suas detecções em SIRGAS 2000 / UTM 22S, com o
limite estadual como janela, núcleo gaussiano, correção de borda de Jones-Diggle (Diggle, 1985; Jones, 1993),
pixels de 1 km e densidade em eventos por 100 km² (cuja integral é igual ao número de eventos). Largura de banda
por validação cruzada por verossimilhança (bw.ppl; Loader, 1999) e sensibilidade com bw.CvL (Cronie; van
Lieshout, 2018), regra de Scott, bw.diggle e valores fixos de 2, 4 e 8 km (spatstat; Baddeley; Rubak; Turner,
2015). Execute o R em localidade UTF-8 (por exemplo, `LC_ALL=C.UTF-8`) para gravar corretamente os nomes
acentuados das mesorregiões.

## 12. Indicadores do relatório (`a08`)

Coeficiente de variação do CO₂ anual (desvio-padrão amostral); índice de Gini do CO₂ municipal (forma da curva
de Lorenz; com e sem os municípios sem emissão); CO₂ e área do FINN por evento após a triagem em cada município,
com a fração de floresta temperada atribuída pelo FINN; CO₂ por evento segundo a classe de vegetação dominante;
fração dos registros da caixa de recorte antiga que fica dentro de SC.

## 12a. Figuras (`a10`)

Numeração das figuras do artigo v3.2 (no relatório do inventário, cada uma tem o número anterior; arquivos em
`docs/results_map.pt-BR.md`). Mapas em coordenadas geográficas SIRGAS 2000 apenas com o contorno do Estado (os
limites municipais não são desenhados; a Figura 5 também traz os limites das mesorregiões), barra de escala sobre o
Atlântico, no canto inferior direito, com a rosa dos ventos acima dela (`finn_sc/cartography.py`; na Figura 7, no
painel inferior direito), e a nota sobre os dados abaixo da moldura. As Figuras 3 e 6 usam
classes com limites arredondados. A Figura 7 (dez poluentes, 2025) usa as quebras naturais de Fisher-Jenks
(`mapclassify.FisherJenks`, k = 5), calculadas sobre os municípios com emissão de cada poluente; cada classe
inclui seu limite superior, e os municípios sem registros aparecem hachurados. Os limites são gravados em
`results/logs/a10_figures.txt`.

Rótulos (revisão de 16/10/2026): os nomes das mesorregiões da Figura 4, o rótulo da anomalia persistente da Figura 5 e os rótulos de ano das Figuras S1 e S2 são posicionados por `finn_sc.figcheck` na primeira posição
candidata, dentro da moldura do mapa ou do gráfico, que não toca limites, marcadores, pontos de dados nem outros rótulos; em seguida, todas as figuras,
inclusive a Figura 1 (`tools/study_area_map.py`), são conferidas de novo, com legendas, barras de cores, rosas dos ventos,
barras de escala e notas, e o resultado aparece na tela como `LAYOUT ...`.

## 13. Testes

`tests/test_stats.py`, `test_events.py` e `test_units.py` (testes unitários com resposta analítica);
`test_results_golden.py` (cada número publicado, com o arredondamento usado no texto); `test_report_v2.py` (números publicados apenas no relatório do inventário v2); `test_round5.py` (valores incluídos no artigo v6 e no relatório v3: unidades de contagem, comparação com o inventário estadual de 2020 e o FINN v1.5, densidade kernel no extremo oeste e no litoral norte, classes da Figura 6, percentuais de cobertura da terra da figura da área de estudo); `test_route_a.py` (FINN
bruto → registros arquivados). Execução: `python -m pytest -q tests` depois de `python python/run_analysis.py`.

## 14. Limitações que permanecem

* correspondência das mesorregiões ainda não
  conferida com a API do IBGE; data de acesso ao ONI não registrada (`provenance.pt-BR.md`).
* A rota A foi executada novamente apenas para janeiro a maio de 2025; os registros arquivados dos demais
  produtos e anos vêm do download feito pelos autores em fevereiro de 2026.
* A área e as emissões do FINN têm incerteza elevada em termos absolutos (mediana de 17 vezes a área mapeada);
  as comparações relativas entre anos e municípios são mais robustas que os totais.
* A classe de vegetação usada pelo FINN (IGBP do MODIS; Wiedinmyer et al., 2023, Tabela 1) não separa a floresta
  plantada da nativa, de modo que as associações com a cobertura da terra descrevem como o inventário distribui as
  emissões e não o comportamento do fogo.

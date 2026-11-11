# De onde vem cada número publicado

> 🌐 [English](results_map.md) · **Português (pt-BR)**

> **Nota (11/11/2026):** a numeração abaixo segue o manuscrito v3.2. Para a versão submetida à Environmental Science & Technology, o capítulo 8 do tutorial (`TUTORIAL_FINN_SC_pt.pdf`) relaciona cada valor publicado ao seu script, à saída e ao teste.

M = artigo v3.2 (`Artigo_Queimadas_v3.2`; seções 2.1 área de estudo, 2.2 modelo FINN, 2.3 dados de entrada,
2.4 processamento, 2.5 compostos, 2.6 análises espaciais e temporais, 2.7 comparação com a área queimada mapeada,
2.8 condicionantes climáticos e de cobertura do solo, 2.9 limitações); S = material suplementar v3.1;
R = relatório do inventário estadual v4.1 (`inventario_queimadas_v4.1`). Cada linha é reproduzida por `python python/run_analysis.py` e conferida pelo teste
da última coluna (`python -m pytest -q tests`). As tabelas ficam em `results/tables/`, os registros de execução em
`results/logs/` e as figuras em `results/figures/`.

| Resultado | Onde é publicado | Script | Saída | Teste |
|---|---|---|---|---|
| Registros, detecções e eventos por produto e ano; 2025: 8.581 / 5.489 / 5.160; após a triagem, 5.121 | M 2.6; R 2–3 | `a01_events_screening.py` | `state_counts.csv` | `test_2025_records_detections_events` |
| Anomalias térmicas persistentes: 0 a 61 eventos por ano (até 0,9%, 2021), até 2,5% do CO₂ (2020); raios de 0,75 e 1,5 km com até 0,8% e 1,2%; Siderópolis de 2021 a 2025 | M 2.6; S Tabela S6; R 2 | `a01_events_screening.py` | `screening_summary.csv`, `screening_flagged_detections.csv` | `test_screening_summary` |
| Eventos após a triagem, 2012–2025 (3.549 a 8.296; média de 5.945; −39,8%, +8,6%, −4,5%; média de 2022 a 2025 de 5.165, desvio-padrão de 180) | M 3, Figura 2; R 3, Figura 1 | `a02_series_trends.py` | `series_state_all_products.csv` | `test_screened_events_series` |
| Tabela 2 (CO₂ a SO₂; NOx = NOXasNO; COV = NMOC); variações de 2023 para 2024 (+9,8% NH₃ a +11,2% NOx) e de 2024 para 2025 (−1,7% NH₃ a −4,9% NOx); máximos em 2020 (NOx em 2016) | M Tabela 2, 3–4; R Tabela 2, 3–4 | `a02_series_trends.py` | `table2_state_emissions_2012_2025.csv` | `test_table2`, `test_emission_changes` |
| Efeito do VIIRS: eventos ×3,6 a 4,8; área +40,7% a 59,1%; CO₂ +39,6% a 56,2%; v2.5.1 ×3,9 e ×4,0 | M 3; S Tabela S2; R 3, Apêndice A | `a02_series_trends.py` | `viirs_effect.csv` | `test_viirs_effect` |
| Mann-Kendall e Sen (τ de −0,12 a −0,03; p ≥ 0,58; declividades de −46, −35, −35.265 e −123); p de Hamed e Rao inalterado de 2012 a 2025 e de 0,042 a 0,084 de 2012 a 2021 | M 2.6, 3; S Tabela S5 | `a02_series_trends.py` | `mann_kendall.csv` | `test_mann_kendall` |
| Autocorrelação de primeira ordem das séries de tendência (0,11 a 0,22) | M 2.6 | `a02_series_trends.py` | `mann_kendall.csv` (`r1`) | `test_round6.py::test_lag1_of_trend_series` |
| Eventos municipais em 2025 e 2024; municípios com 100 eventos ou mais: 9 e 10; 277 municípios com eventos | M 3, Figura 3; R 3–4, Figura 2 | `a03_municipal_mesoregion.py` | `municipal_2025.csv`, `municipal_events_by_year.csv` | `test_municipal_events_2025` |
| Tabela 3 (mesorregiões); Serrana com 46,5% do CO₂; Serrana e Oeste com 72,9% (70,5% a 75,4%); eventos por 100 km² | M Tabela 3, 3–4, Figura 4; R Tabela 3, 3–4, Figura 3 | `a03_municipal_mesoregion.py` | `mesoregion_2025.csv` | `test_table3_and_shares` |
| Área queimada municipal e municípios com as maiores emissões de cada poluente; lista de MP2,5 acima de 500 t | M 3–4, Figuras 6–7; S Tabela S4; R 3–4, Tabela 4, Figuras 5–6 | `a03_municipal_mesoregion.py` | `municipal_2025.csv` | `test_area_and_leaders` |
| Sazonalidade (julho a setembro: 55,8% em 2025 e 60,0% em 2012–2025; julho a novembro: 72,1%) | M 2.8, 4; R 3 | `a03_municipal_mesoregion.py` | registro `a03_municipal_mesoregion.txt` | - |
| Partição por vegetação (GENVEG): área de 46,3 / 31,9 / 20,2 / 1,6%; floresta temperada com 55,0% do CO₂ e 74,1% do MP2,5; 1,73 e 0,54 kg m⁻² | M 3; S Tabela S9; R 4 | `a04_genveg_partition.py` | `genveg_partition.csv` | `test_genveg` |
| FINN e MapBiomas: razão de 13,3 a 37,7 (mediana de 17,2); r = 0,77 e ρ = 0,75; ρ municipal de 0,47 a 0,73 | M 2.7, 3, 4; S Tabela S3, Figura S1; R 2, 4, 8 | `a05_mapbiomas_comparison.py` | `mapbiomas_state.csv`, `mapbiomas_agreement_by_year.csv` | `test_mapbiomas` |
| Área mapeada por evento do FINN (verificação da tipologia) | R 4 | `a05_mapbiomas_comparison.py` | `mapbiomas_area_per_event.csv` | - |
| Clima: precipitação, ρ = −0,68 / −0,71 / −0,71 (Holm ≤ 0,035); ONI, ρ de −0,53 a −0,51; primeiras diferenças de −0,65 a −0,58; VPD de 0,48 a 0,56 | M 3–4; S Tabela S7, Figura S2; R 4, 8 | `a06_climate_drivers.py` | `climate_correlations.csv` | `test_climate` |
| Cobertura do solo e densidade de eventos (295 municípios, Coleção 10.1): ρ de 0,42 (silvicultura), −0,25 (formação florestal) e 0,13 (formação campestre, p = 0,03); Moran de 0,32 para 0,002; efeitos (n = 294) de +37 / +35 / +24 / +15%; AIC de 492,4 para 415,9 | M 2.8, 3; S Tabela S8; R 4, 8 | `a07_landcover.py` | `landcover_spearman.csv`, `landcover_sem.csv` | `test_landcover` |
| Cobertura do solo e CO₂ por evento (modelo de erro espacial: silvicultura, +27% a cada 10 p.p.) | R 4, 8 | `a07_landcover.py` | `landcover_sem.csv` | `test_landcover` |
| Densidade kernel (σ = 2,8 km; CvL, 8,8 km; Scott, 21,7 km; máximo de 52,8 por 100 km²; 1% superior: Serrana com 93,6%); seletor de Diggle, 0,75 km, r = 0,63 (só no registro) | M 2.6, 3, Figura 5; R 3, Figura 4 | `R/analysis/kde_events.R` | `kde_2025_grid.csv`, `kde_2025_bandwidths.csv`, registro `kde_2025_summary.txt` | `test_kde` |
| CV do CO₂ de 28,3%; Gini de 0,728 (277 municípios); CO₂ por evento (mediana de 478 t; São Joaquim, 415 t; Lebon Régis, 2.118 t) | R 4, Apêndice A | `a08_report_indicators.py` | `intensity_per_event_2025.csv` | `test_report_indicators` |
| Fatores de emissão implícitos nos registros = Tabela 4 de Wiedinmyer et al. (2023) (razões de 0,9986 a 1,0026) | M 2.4; docs/provenance | `a09_emission_factor_check.py` | `emission_factor_check.csv` | `test_emission_factor_check` |
| Replicação da rota A (FINN bruto → registros) | docs/provenance | `python/01`, `02`, `06` | `data/derived/finn_sc_records_rebuilt.csv.gz` | `test_route_a.py` |
| Valores só do relatório: área −4,3% (2024→2025); CO₂ de 2,30 a 6,63 Mt; Lages e São Joaquim com 15,0% dos eventos, 10,3% do CO₂ e 22,1% do CO₂ da Serrana; três maiores com 951 eventos (18,6%); densidades de eventos (São Joaquim, 18,0 por 100 km²) | R Resumo, 3, 4 | `a02`, `a03` | `series_state_all_products.csv`, `municipal_2025.csv` | `test_report_v2.py` |
| Perfis A e B: CO₂ por evento (404 a 526 t e 1.046 a 2.118 t), fração de floresta temperada do FINN, área do MapBiomas por evento do FINN (0,004 a 0,021 e 0,054 a 0,082 km²), medianas por classe de vegetação dominante | R Resumo, 4, 7 | `a05`, `a08` | `intensity_per_event_2025.csv`, `mapbiomas_area_per_event.csv`, registro `a08_report_indicators.txt` | `test_report_v2.py` |
| CO₂ e clima da estação de queimadas (ρ −0,71 precipitação, −0,70 umidade do solo, Holm p = 0,022; VPD 0,56; ONI −0,51, primeiras diferenças −0,65); precipitação de 2025 e 2024 (718 e 638 mm) | R 4, 7, 8 | `a06` | `climate_correlations.csv` | `test_report_v2.py` |
| CO₂ por evento e cobertura do solo (n = 288; ρ 0,85 floresta temperada do FINN, 0,68 silvicultura, −0,62 agricultura; modelo de erro espacial +27,6% e −10,9% a cada 10 p.p.; Moran 0,21 → −0,004) | R 4 (quadro), 8, Apêndice A | `a07` | `landcover_spearman.csv`, `landcover_sem.csv` | `test_report_v2.py` |
| Densidade kernel por mesorregião (10,4 na Serrana a 2,3 na Grande Florianópolis por 100 km²), sensibilidade r de 0,83 a 0,97, máximo em Lages | R 3, 8 | `R/analysis/kde_events.R` | `kde_2025_grid.csv`, registro `kde_2025_summary.txt` | `test_report_v2.py` |
| Figura 7 do relatório (estrutura do repositório) | R Apêndice A | `tools/fig7_flowchart.py` | `results/figures/Report_Fig07_repository_structure.png` | - |
| Unidades de contagem em 2025: eventos +0,8% (sem triagem), +7,2% (detecções), +67,6% (registros); Lages com 429 eventos e 670 registros (+56%) | M 4; R 3 | `a01`, `a03` | `state_counts.csv`, `municipal_2025.csv` | `test_round5.py::test_counting_units_2025` |
| Eventos com mais de uma detecção (20.766 de 124.602; MODIS+VIIRS 9.287 de 83.512, 11,1%; 2025: 267 de 5.160, 5,2%) | docs/analysis.pt-BR.md (não impresso no artigo) | `a01` | `events.csv.gz` | `test_round5.py::test_events_with_several_detections` |
| Inventário estadual de 2020 (LCQAR, 2022: 12,91 Mt, 4.625 focos) e registros do FINN v1.5 de 2020 (12,88 Mt, 4.609; diferença de até 0,4%); FINN v2.5 em 2020: MODIS 4,56 Mt (5.643 registros, 1.971 eventos; −65%), MODIS+VIIRS 6,63 Mt (15.727 registros, 8.212 eventos; +45%) | M 4; R 1, 3 | `a01`, `a02`; `data/external/legacy_finn15_lcqar_2020.csv` | `series_state_all_products.csv`, `state_counts.csv` | `test_round5.py::test_lcqar_2020_and_finn_versions` |
| Densidade kernel a oeste de 52,5° W (2,6 por 100 km²) e no Norte Catarinense a leste de 49,5° W (1,7), ante a média estadual de 5,4 | M 4 | `R/analysis/kde_events.R` | `kde_2025_grid.csv` | `test_round5.py::test_kde_far_west_and_north_coast` |
| Classes da Figura 7 (Fisher-Jenks; CO₂ 10.329 / 31.410 / 71.909 / 149.038 t; CO 797 / 2.178 / 4.109 / 6.885 t) | M Figura 7; R Figura 6 | `a10_figures.py` | registro `a10_figures.txt` | `test_round5.py::test_figure6_fisher_jenks_reproduces_original_breaks` |
| Figura da área de estudo: percentuais de uso e cobertura do solo em 2019 (formação florestal 40,2%, mosaico de usos 17,3%, lavouras temporárias 13,2%, silvicultura 10,5%, pastagem 9,9%, formação campestre 5,2%, área urbanizada 1,9%) | M Figura 1, 2.1 | `tools/study_area_map.py` | `data/external/mapbiomas_c10_lulc2019_SC_class_areas.csv` | `test_round5.py::test_study_area_land_cover_shares` |
| Uso e cobertura do solo por mesorregião, 2019 (Serrana: 97,7% da formação campestre do Estado, 21,6% de sua área; 37,5% da silvicultura; Oeste: 45,3% das lavouras temporárias e 41,3% do mosaico de usos; formação florestal em 62,1% da Grande Florianópolis e 53,9% do Vale do Itajaí) | M 2.1 | `tools/study_area_map.py` | `results/tables/landcover2019_mesoregion.csv` | `test_round5.py::test_study_area_mesoregion_land_cover` |

## Comparação com o BRAIN, 2019 e 2020 (notebook e ferramenta, fora do `run_analysis.py`)

| Resultado | Onde é publicado | Notebook ou ferramenta | Saída em `results/` |
|---|---|---|---|
| BRAIN = 1,01 × arquivo anual do FINN v1.5 em 7.474 de 7.474 combinações de dia e célula (2019); perfil horário 210 e 19 camadas em 2019 e 2020 | M 2.9, Discussão; S S24; R 3.9 | `notebooks/BRAIN_FINN_comparison_SC.ipynb` (execução de 2019: `BRAIN_FINN_comparison_SC_2019.ipynb`) | `brain_2019/tables/processing_checks.csv`, `brain_20xx/logs/time_profile_check.csv`, `brain_20xx/logs/run_metadata.json` |
| Totais de 2019 e razões FINN v2.5 / BRAIN (CO 0,61 com MODIS e VIIRS, 0,41 com MODIS; de 0,36 nos NOx a 1,24 no SO₂) | M Discussão; S Tabela S24a; R 3.9 | o mesmo | `brain_2019/tables/annual_totals_and_ratios.csv` |
| 2019: r mensal 0,998, máximo em agosto; ρ diário 0,84 (0,78 a 0,88); células; municípios ρ 0,90, 9 dos 10 maiores | M Discussão; S Tabela S24b; R 3.9 | o mesmo | `brain_2019/tables/monthly_correlations.csv`, `daily_statistics.csv`, `cell_statistics_R1.csv`, `municipal_statistics.csv` |
| Totais de 2020 (364 dias) e razões FINN v2.5 / BRAIN (CO 0,69 com MODIS e VIIRS, 0,48 com MODIS; de 0,37 nos NOx a 1,40 no NH₃) | M Discussão; S Tabela S24c; R 3.9 | o mesmo, `YEAR = 2020` | `brain_2020/tables/annual_totals_and_ratios.csv` |
| 2020: r mensal 0,969, máximo em agosto; ρ diário 0,84 (0,79 a 0,88); células; municípios ρ 0,91, 8 dos 10 maiores | M Discussão; S Tabela S24d; R 3.9 | o mesmo | `brain_2020/tables/monthly_correlations.csv`, `daily_statistics.csv`, `cell_statistics_R1.csv`, `municipal_statistics.csv` |
| Versão do FINN no BRAIN, combinações de dia e célula em R1: em 2020, 94,4% do CO do BRAIN em combinações com fogo no FINN v1.5 e 65,0% (MODIS) e 67,5% (MODIS e VIIRS) no FINN v2.5; controle de 2019, 64,4% e 66,8% | M Discussão; S Tabela S24e; R 3.9 | `tools/brain_cells_and_finn15_check.py --check2019`, `--check2020` | `brain_2019/tables/check_cell_days_R1_finn25.csv`, `brain_2020/tables/check_cell_days_R1_finn15_finn25.csv` |

## Figuras

| Artigo (v3.2) | Relatório (v4.1) | Script | Arquivo em `results/figures/` |
|---|---|---|---|
| Figura 1, área de estudo e uso e cobertura do solo em 2019 | - | `tools/study_area_map.py` | `Fig01_study_area_pt.png` (rótulos em inglês: `Fig01_study_area_en.png`) |
| Figura 2, séries anuais de 2003 a 2025 | Figura 1 | `a10_figures.py` | `Fig02_annual_series.png` |
| Figura 3, eventos por município em 2025 | Figura 2 | `a10_figures.py` | `Fig03_events_municipal_2025.png` |
| Figura 4, eventos e densidade de eventos por mesorregião em 2025 | Figura 3 | `a10_figures.py` | `Fig04_events_mesoregion_2025.png` |
| Figura 5, densidade kernel dos eventos em 2025 | Figura 4 | `a10_figures.py` (grade de `R/analysis/kde_events.R`) | `Fig05_kde_events_2025.png` |
| Figura 6, área queimada do FINN por município em 2025 | Figura 5 | `a10_figures.py` | `Fig06_burned_area_municipal_2025.png` |
| Figura 7, emissões por município em 2025 (classes de Fisher-Jenks) | Figura 6 | `a10_figures.py` | `Fig07_emissions_municipal_2025.png` |
| Figura S1 do material suplementar, FINN e MapBiomas Fogo | - | `a10_figures.py` | `FigS1_finn_vs_mapbiomas.png` |
| Figura S2 do material suplementar, clima e eventos | - | `a10_figures.py` | `FigS2_climate_events.png` |
| - | Figura 7, estrutura do repositório | `tools/fig7_flowchart.py` | `Report_Fig07_repository_structure.png` |
| mapa de conferência da densidade kernel (não publicado) | - | `R/analysis/kde_events.R` | `kde_2025_quicklook.png` |

O registro de `a10_figures.py` (`results/logs/a10_figures.txt`) mantém a numeração do relatório ("Figure 1" = séries
anuais … "Figure 6" = emissões), que é a lida pelo teste
`test_round5.py::test_figure6_fisher_jenks_reproduces_original_breaks`.

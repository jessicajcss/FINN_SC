# Testes de reprodutibilidade

> 🌐 [English](reproducibility.md) · **Português (pt-BR)**

## Execução publicada

As tabelas (`results/tables/`) e os registros de execução (`results/logs/`) guardados no repositório são a execução
publicada. A soma SHA-256 de cada um está em `results/MANIFEST.sha256`. As versões exatas das bibliotecas Python
dessa execução estão em `requirements-lock.txt`. As figuras ficam fora do manifesto, porque o arquivo PNG grava a
versão do matplotlib e muda em bytes entre versões mesmo quando o desenho é igual.

## Como conferir uma reprodução

```bash
python python/run_analysis.py --no-r     # recalcula as tabelas, os registros e as figuras
python -m pytest -q tests                # 76 testes: unidades, estatística, valores publicados, rota A
python tools/verify_manifest.py          # compara as tabelas e os registros com a execução publicada
```

O `verify_manifest.py` classifica cada arquivo como OK (idêntico byte a byte), EQUIVALENT (números iguais dentro
da tolerância relativa de 10⁻⁹), DIFFERENT (diferença maior) ou CHANGED (bytes diferentes, sem cópia publicada para
comparar os números, como fora de um clone do git).

## Teste independente de 1º de novembro de 2026

Ambiente diferente do da execução publicada: Linux, Python 3.10.12, pandas 2.3.3, numpy 2.2.6, scipy 1.15.3,
geopandas 1.1.4, matplotlib 3.10.9, shapely 2.1.2, pyproj 3.7.1, spreg 1.9.0, esda 2.7.0 e libpysal 4.13.0.

* Recalculados nesta máquina: `a01` a `a09` e `a11` a `a14`, a partir de uma cópia limpa do repositório. O `a10`
  (figuras) passou do limite de 3 minutos por comando da sessão de teste e não foi recalculado. O R não foi usado
  (opção `--no-r`).
* Resultado: 59 dos 73 arquivos do manifesto ficaram idênticos byte a byte. Nos outros 14, mudaram apenas os
  últimos dígitos de valores calculados em ponto flutuante. As maiores diferenças relativas ocorreram nas saídas do
  modelo de erro espacial: 8 × 10⁻⁵ em `landcover_sem.csv` (I de Moran dos resíduos) e 3 × 10⁻⁵ em
  `recurrence_sem.csv`. Nas demais tabelas, as diferenças ficaram abaixo de 2 × 10⁻⁶. No log do `a13`, mudou o
  último dígito impresso de um valor de p (5,53 × 10⁻⁷¹ e 5,52 × 10⁻⁷¹). Nenhum valor arredondado citado no artigo
  ou no relatório mudou.
* Os 76 testes passaram sobre os resultados recalculados.
* O teste revelou uma dependência do ambiente no `a14`: em 5.030 eventos (6,0%), a maior área do FINN cabe a dois
  ou mais tipos de vegetação, e a escolha do tipo dominante nesses empates dependia do algoritmo de ordenação da
  versão instalada do pandas. O `a14` passou a atribuir os empates ao tipo de menor código, a regra do `a08`, e
  registra no log o número de empates e o resultado com a regra inversa. A tabela
  `finn_genveg_vs_mapbiomas.csv`, o log do `a14`, o teste `test_round15.py` e o manifesto foram atualizados.

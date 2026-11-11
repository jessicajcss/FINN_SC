"""tools/fig7_flowchart.py - structure of the FINN_SC repository (Figure 9 of the state inventory report).
Every number printed in the figure is taken from the repository outputs (results/logs)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

DK, LT, TX, MUT, CODE = "#1f7a33", "#e9f3ea", "#14361d", "#4a5a4e", "#1f6b30"
fig = plt.figure(figsize=(14, 13.2), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 140); ax.set_ylim(0, 132); ax.axis("off")

def box(x, y, w, h, fc, ec=None, r=1.2, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}", fc=fc, ec=ec or fc, lw=lw))

def band(y, title, right):
    box(6, y, 128, 5, DK)
    ax.text(8.5, y + 2.5, title, color="white", fontsize=13.5, weight="bold", va="center")
    ax.text(131.5, y + 2.5, right, color="#d9ecdc", fontsize=10.5, va="center", ha="right")

def wide(y, text, h=5.2, fs=12):
    box(6, y, 128, h, LT, "#c9dccb")
    ax.text(70, y + h / 2, text, color=TX, fontsize=fs, weight="bold", va="center", ha="center")

def card(x, y, w, h, title, lines, code=None, num=None):
    box(x, y, w, h, "white", "#d5e2d7")
    tx = x + 2
    if num is not None:
        ax.add_patch(plt.Circle((x + 3.6, y + h - 3.4), 1.9, color=DK))
        ax.text(x + 3.6, y + h - 3.4, str(num), color="white", fontsize=11.5, weight="bold", ha="center", va="center")
        tx = x + 7
    ax.text(tx, y + h - 3.4, title, color=TX, fontsize=11.5, weight="bold", va="center")
    for k, ln in enumerate(lines):
        ax.text(x + 2, y + h - 7.4 - 2.6 * k, ln, color=MUT, fontsize=9.6, va="center")
    if code:
        ax.text(x + 2, y + 2.4, code, color=CODE, fontsize=8.8, family="DejaVu Sans Mono", va="center")

def arrow(y0, y1):
    ax.annotate("", xy=(70, y1), xytext=(70, y0), arrowprops=dict(arrowstyle="-|>", color="#9fb5a3", lw=2.2))

ax.text(6, 128.2, "Estrutura do repositório FINN_SC: do dado bruto aos resultados",
        color=TX, fontsize=17, weight="bold", va="center")
ax.text(6, 124.6, "Rota A: replicação a partir dos arquivos do FINN · Rota B: reprodução de cada tabela, estatística e figura a partir dos registros arquivados",
        color=MUT, fontsize=10.5, va="center")

wide(116.5, "ENTRADA · arquivos do FINN v2.5 e v2.5.1 (NSF NCAR RDA ds312.9 e pasta NRT do NCAR) · MODIS (1 km) + VIIRS (375 m)")
arrow(116.4, 113.6)
band(108.5, "ROTA A · PIPELINE", "arquivos do FINN → tabela de registros de SC")
cw, gap, cy, ch = 30.5, 2.0, 89.5, 17
cards = [
    ("Download", ["Arquivos do FINN por", "ano, versão e sensor"], "00_download_finn.py"),
    ("Conversão", ["mol/dia e kg/dia → t;", "NOx = NOXasNO; COV = NMOC"], "01_convert_units.py"),
    ("Recorte para SC", ["Ponto em polígono com a malha", "municipal do IBGE de 2024"], "02_clip_region.py"),
    ("Registros de SC", ["Chaves, espécies, área e", "município de cada registro"], "06_build_sc_records.py"),
]
for k, (t, l, c) in enumerate(cards):
    card(6 + k * (cw + gap), cy, cw, ch, t, l, c, num=k + 1)
arrow(89.4, 86.6)
wide(80.5, "REGISTROS ARQUIVADOS · 258.694 registros (2003 a 2025, SHA-256) + MapBiomas Fogo, MCD64A1, ERA5-Land/ONI, cobertura do solo e IBGE", h=5.8, fs=10.8)
arrow(80.4, 77.6)
band(72.5, "ROTA B · ANÁLISE", "python/run_analysis.py e R/analysis/kde_events.R")
rows = [
    [("Eventos e triagem", ["5.121 eventos em 2025;", "anomalias com 16 dias ou mais"], "a01"),
     ("Séries e VIIRS", ["Mann-Kendall, p ≥ 0,58;", "VIIRS: eventos ×3,6 a 4,8"], "a02, a09"),
     ("Municípios e indicadores", ["Tabelas 2, 4 e 5; Serrana:", "46,5% do CO₂; Gini 0,728"], "a03, a04, a08"),
     ("Áreas mapeadas", ["MapBiomas: mediana 17,2;", "MCD64A1: mediana 34,4"], "a05, a12")],
    [("Clima", ["Spearman com ajuste de Holm;", "precipitação: ρ = −0,71"], "a06, a11, a12"),
     ("Cobertura do solo", ["Modelo de erro espacial;", "densidade e CO₂ por evento"], "a07"),
     ("Recorrência e validade", ["Grade de 2 km; classe do FINN", "× MapBiomas; área mapeada"], "a13, a14"),
     ("Densidade kernel", ["spatstat; σ = 2,8 km;", "máximo de 52,8/100 km²"], "kde_events.R")],
]
for r, row in enumerate(rows):
    y = 53.5 - r * 19
    for k, (t, l, c) in enumerate(row):
        card(6 + k * (cw + gap), y, cw, 16.5, t, l, c)
arrow(34.4, 31.6)
wide(25.5, "RESULTADOS · results/tables, results/logs e results/figures (figuras do artigo, do Material Suplementar e do relatório)")
arrow(25.4, 22.6)
band(17.5, "VERIFICAÇÃO", "python -m pytest -q tests")
vw = 41.3
for k, (t, l) in enumerate([("Testes unitários", ["Unidades, contagem, Mann-Kendall,", "Holm, Gini e coeficiente de variação"]),
                           ("Valores publicados", ["Cada número do artigo e do", "relatório, com o arredondamento usado"]),
                           ("Replicação da rota A", ["FINN bruto de jan. a maio de 2025:", "2.341 de 2.341 registros idênticos"])]):
    card(6 + k * (vw + 2.05), 2.5, vw, 13.5, t, l)
from pathlib import Path
out = Path(__file__).resolve().parents[1] / "results" / "figures" / "Report_Fig07_repository_structure.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=150, facecolor="white")
print("ok")

# -*- coding: utf-8 -*-
"""content.py - text of the FINN_SC tutorial in English (en) and Brazilian Portuguese (pt), 11 Nov 2026.
Every number comes from results/ of this repository (script and output named next to it) or from the cited source."""

LABELS = {
    "en": dict(title="FINN_SC tutorial", contents="Contents", chapter="Chapter", reading="reading time",
               tldr="In 30 seconds", learn="After this chapter you will be able to:", quiz="Check yourself"),
    "pt": dict(title="Tutorial FINN_SC", contents="Sumário", chapter="Capítulo", reading="tempo de leitura",
               tldr="Em 30 segundos", learn="Ao final deste capítulo, você conseguirá:", quiz="Teste-se"),
}

FIGS = {
    "en": dict(f1="Fig01_study_area_en.png", f2="Fig02_annual_series_4p_en.png", f3="Fig03_events_municipal_2025_nn_en.png",
               f5="Fig05_kde_events_2025_nn_en.png", f8="Fig08_recurrence_landcover_nn_en.png", f9="Fig09_sensitivity_factors_nn_en.png"),
    "pt": dict(f1="Fig01_study_area_pt.png", f2="Fig02_annual_series_nn.png", f3="Fig03_events_municipal_2025_nn.png",
               f5="Fig05_kde_events_2025_nn.png", f8="Fig08_recurrence_landcover_nn_pt.png", f9="Fig09_sensitivity_factors_nn_pt.png"),
}


def fig(lang, key, caption):
    return (f'<figure><img src="../../results/figures/{FIGS[lang][key]}"><figcaption>{caption}</figcaption></figure>')


def B(kind, label, html):
    from build_tutorial import box
    return box(kind, label, html)


def lab(lang):
    return dict(key=("Key idea", "Ideia-chave"), warn=("Watch out", "Atenção"), do=("Do it", "Faça"),
                deep=("Deep dive (optional)", "Para aprofundar (opcional)"), check=("Check", "Confira"))


def L(lang, k):
    return lab(lang)[k][0 if lang == "en" else 1]


# ----------------------------------------------------------------------------------------------------- diagrams (SVG)
def svg_routes(lang):
    t = {"en": ["ROUTE A · replication", "NCAR FINN files", "00 download", "01 units → tonnes", "02 clip to region",
                "04 aggregate", "05 describe", "ROUTE B · reproduction", "archived records", "SC, 2003–2025",
                "run_analysis.py", "a01 … a20", "results/", "tables · figures · logs", "tests + manifest",
                "96 passed · 107 OK", "archived as", "any region · needs internet", "Santa Catarina · offline"],
         "pt": ["ROTA A · replicação", "arquivos FINN (NCAR)", "00 download", "01 unidades → t", "02 recorte da região",
                "04 agregação", "05 descrição", "ROTA B · reprodução", "registros arquivados", "SC, 2003–2025",
                "run_analysis.py", "a01 … a20", "results/", "tabelas · figuras · logs", "testes + manifesto",
                "96 passam · 107 OK", "arquivados como", "qualquer região · requer internet", "Santa Catarina · offline"]}[lang]
    def bx(x, y, w, a, b="", fill="#e8f1fb", stroke="#1d5fa8"):
        s = f'<rect x="{x}" y="{y}" width="{w}" height="46" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>'
        s += f'<text x="{x + w / 2}" y="{y + (20 if b else 28)}" text-anchor="middle" font-size="11.5" font-weight="bold" fill="#0f1a2b">{a}</text>'
        if b:
            s += f'<text x="{x + w / 2}" y="{y + 36}" text-anchor="middle" font-size="10" fill="#33415a">{b}</text>'
        return s
    def ar(x1, y1, x2, y2, dash=False):
        d = ' stroke-dasharray="5 4"' if dash else ""
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#5b6676" stroke-width="1.6"{d} marker-end="url(#m)"/>'
    s = ['<svg viewBox="0 0 780 300" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">',
         '<defs><marker id="m" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
         '<path d="M0 0 10 5 0 10z" fill="#5b6676"/></marker></defs>',
         f'<text x="6" y="18" font-size="12" font-weight="bold" fill="#1d5fa8">{t[0]}</text>',
         f'<text x="774" y="18" text-anchor="end" font-size="10" fill="#5b6676">{t[17]}</text>']
    xs = [6, 136, 266, 396, 526, 656]
    labels = {"en": [("FINN files", "NSF NCAR"), ("00", "download"), ("01", "units → t"), ("02", "clip to region"),
                     ("04", "aggregate"), ("05", "describe")],
              "pt": [("arquivos FINN", "NSF NCAR"), ("00", "download"), ("01", "unidades → t"), ("02", "recorte"),
                     ("04", "agregação"), ("05", "descrição")]}[lang]
    for i, (x, (a, b)) in enumerate(zip(xs, labels)):
        s.append(bx(x, 30, 118, a, b))
        if i < 5:
            s.append(ar(x + 118, 53, x + 134, 53))
    s.append(f'<text x="6" y="178" font-size="12" font-weight="bold" fill="#2e8b57">{t[7]}</text>')
    s.append(f'<text x="774" y="178" text-anchor="end" font-size="10" fill="#5b6676">{t[18]}</text>')
    g = dict(fill="#e9f6ee", stroke="#2e8b57")
    s.append(bx(6, 190, 170, t[8], t[9], **g)); s.append(ar(176, 213, 200, 213))
    s.append(bx(202, 190, 170, t[10], t[11], **g)); s.append(ar(372, 213, 396, 213))
    s.append(bx(398, 190, 170, t[12], t[13], **g)); s.append(ar(568, 213, 592, 213))
    s.append(bx(594, 190, 180, t[14], t[15], **g))
    s.append(ar(455, 78, 90, 188, dash=True))
    s.append(f'<text x="150" y="146" font-size="10" fill="#5b6676" font-style="italic">{t[16]}</text>')
    s.append("</svg>")
    return '<figure class="diagram">' + "".join(s) + "</figure>"


def svg_units(lang):
    t = {"en": ["record", "one row of a FINN file:", "a detection, or the part of it", "in one vegetation type",
                "detection", "one satellite pixel on one day", "(day + FIREID)", "fire event",
                "the daily burned-area polygon", "(day + POLYID): the unit counted here"],
         "pt": ["registro", "uma linha do arquivo FINN:", "uma detecção, ou a parte dela", "em um tipo de vegetação",
                "detecção", "um pixel de satélite em um dia", "(dia + FIREID)", "evento de queimada",
                "o polígono diário de área queimada", "(dia + POLYID): a unidade contada aqui"]}[lang]
    s = ['<svg viewBox="0 0 780 210" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">',
         '<path d="M40 40 L230 28 L250 120 L160 178 L30 150 Z" fill="#fde7cf" stroke="#e07b00" stroke-width="2"/>',
         '<rect x="70" y="60" width="60" height="60" fill="#f6c28b" stroke="#a45700" stroke-width="1.5"/>',
         '<rect x="140" y="80" width="60" height="60" fill="#f6c28b" stroke="#a45700" stroke-width="1.5"/>',
         '<line x1="170" y1="80" x2="170" y2="140" stroke="#1d5fa8" stroke-width="2" stroke-dasharray="4 3"/>',
         '<rect x="140" y="80" width="30" height="60" fill="#9cc3ea" fill-opacity="0.55"/>']
    def item(y, color, a, b, c):
        return (f'<circle cx="300" cy="{y - 4}" r="7" fill="{color}"/>'
                f'<text x="316" y="{y}" font-size="13" font-weight="bold" fill="#0f1a2b">{a}</text>'
                f'<text x="316" y="{y + 17}" font-size="11" fill="#33415a">{b}</text>'
                f'<text x="316" y="{y + 32}" font-size="11" fill="#33415a">{c}</text>')
    s.append(item(34, "#9cc3ea", t[0], t[1] + " " + t[2], t[3]))
    s.append(item(98, "#f6c28b", t[4], t[5], t[6]))
    s.append(item(162, "#e07b00", t[7], t[8], t[9]))
    s.append("</svg>")
    return '<figure class="diagram">' + "".join(s) + "</figure>"


def svg_twoday(lang):
    t = {"en": ["Day 1", "Day 2", "MODIS detects a fire", "no new detection nearby:", "FINNv1 adds a copy at half size",
                "(the next-day continuation)", "100% of the size", "50%", "FINN v1.5: between about 30° N and 30° S",
                "FINN v2.5: only between 23.5° N and 23.5° S", "Santa Catarina: 26° S to 29.4° S"],
         "pt": ["Dia 1", "Dia 2", "o MODIS detecta um foco", "sem nova detecção próxima:", "o FINNv1 acrescenta uma cópia com metade do tamanho",
                "(a continuação no dia seguinte)", "100% do tamanho", "50%", "FINN v1.5: entre cerca de 30° N e 30° S",
                "FINN v2.5: apenas entre 23,5° N e 23,5° S", "Santa Catarina: 26° S a 29,4° S"]}[lang]
    s = ['<svg viewBox="0 0 780 190" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">',
         '<line x1="30" y1="95" x2="420" y2="95" stroke="#c4ccd8" stroke-width="2"/>',
         f'<text x="95" y="22" font-size="13" font-weight="bold" text-anchor="middle">{t[0]}</text>',
         f'<text x="320" y="22" font-size="13" font-weight="bold" text-anchor="middle">{t[1]}</text>',
         '<circle cx="95" cy="95" r="40" fill="#e07b00"/>',
         f'<text x="95" y="100" text-anchor="middle" font-size="11" fill="white" font-weight="bold">{t[6].split(" ")[0]}</text>',
         '<circle cx="320" cy="95" r="28" fill="#f6c28b" stroke="#e07b00" stroke-width="2" stroke-dasharray="5 3"/>',
         f'<text x="320" y="100" text-anchor="middle" font-size="11" fill="#7a3f00" font-weight="bold">{t[7]}</text>',
         f'<text x="95" y="160" text-anchor="middle" font-size="10.5">{t[2]}</text>',
         f'<text x="320" y="152" text-anchor="middle" font-size="10.5">{t[3]}</text>',
         f'<text x="320" y="166" text-anchor="middle" font-size="10.5">{t[4] if lang == "en" else "cópia com metade do tamanho"}</text>',
         f'<text x="320" y="180" text-anchor="middle" font-size="10.5" fill="#5b6676">{t[5]}</text>',
         '<rect x="450" y="40" width="320" height="110" rx="8" fill="#f2f4f7" stroke="#7a8599"/>',
         f'<text x="462" y="68" font-size="11">{t[8]}</text>',
         f'<text x="462" y="94" font-size="11">{t[9]}</text>',
         f'<text x="462" y="120" font-size="11" font-weight="bold" fill="#c0392b">{t[10]}</text>',
         "</svg>"]
    return '<figure class="diagram">' + "".join(s) + "</figure>"


def svg_equation(lang):
    t = {"en": ["E", "emission", "A", "burned area", "B", "fuel loading", "CF", "fraction burned", "EF", "emission factor",
                "per record, per compound"],
         "pt": ["E", "emissão", "A", "área queimada", "B", "carga de combustível", "CF", "fração queimada", "EF",
                "fator de emissão", "por registro e por composto"]}[lang]
    s = ['<svg viewBox="0 0 780 110" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">']
    xs = [20, 175, 330, 485, 640]
    cols = ["#c0392b", "#e07b00", "#2e8b57", "#6b4fbb", "#1d5fa8"]
    for i, x in enumerate(xs):
        s.append(f'<rect x="{x}" y="15" width="120" height="66" rx="9" fill="white" stroke="{cols[i]}" stroke-width="2.2"/>')
        s.append(f'<text x="{x + 60}" y="50" text-anchor="middle" font-size="22" font-weight="bold" fill="{cols[i]}">{t[2 * i]}</text>')
        s.append(f'<text x="{x + 60}" y="70" text-anchor="middle" font-size="10.5" fill="#33415a">{t[2 * i + 1]}</text>')
    s.append('<text x="157" y="55" text-anchor="middle" font-size="22" fill="#5b6676">=</text>')
    for x in (312, 467, 622):
        s.append(f'<text x="{x}" y="55" text-anchor="middle" font-size="20" fill="#5b6676">×</text>')
    s.append(f'<text x="390" y="104" text-anchor="middle" font-size="10.5" fill="#5b6676">{t[10]}</text></svg>')
    return '<figure class="diagram">' + "".join(s) + "</figure>"


def svg_decomp(lang):
    t = {"en": ["FINN v1.5 / FINN v2.5 MODIS, CO₂ of 2020 in Santa Catarina", "next-day", "continuations", "number of",
                "detections", "area per", "detection", "CO₂ per km²", "(mostly the forest class)", "= 2.82"],
         "pt": ["FINN v1.5 / FINN v2.5 MODIS, CO₂ de 2020 em Santa Catarina", "continuações", "no dia seguinte", "número de",
                "detecções", "área por", "detecção", "CO₂ por km²", "(sobretudo a classe florestal)", "= 2,82"]}[lang]
    v = ["1/0.730", "0.990", "1.159", "0.423"] if lang == "en" else ["1/0,730", "0,990", "1,159", "0,423"]
    s = ['<svg viewBox="0 0 780 150" xmlns="http://www.w3.org/2000/svg" font-family="DejaVu Sans, sans-serif">',
         f'<text x="390" y="18" text-anchor="middle" font-size="12" font-weight="bold">{t[0]}</text>']
    xs = [20, 200, 380, 560]
    cols = ["#e07b00", "#7a8599", "#2e8b57", "#1d5fa8"]
    subs = [(t[1], t[2]), (t[3], t[4]), (t[5], t[6]), (t[7], t[8])]
    for i, x in enumerate(xs):
        s.append(f'<rect x="{x}" y="32" width="150" height="88" rx="9" fill="white" stroke="{cols[i]}" stroke-width="2.2"/>')
        s.append(f'<text x="{x + 75}" y="66" text-anchor="middle" font-size="20" font-weight="bold" fill="{cols[i]}">{v[i]}</text>')
        s.append(f'<text x="{x + 75}" y="88" text-anchor="middle" font-size="10.5">{subs[i][0]}</text>')
        s.append(f'<text x="{x + 75}" y="104" text-anchor="middle" font-size="10" fill="#5b6676">{subs[i][1]}</text>')
        if i < 3:
            s.append(f'<text x="{x + 165}" y="80" text-anchor="middle" font-size="20" fill="#5b6676">×</text>')
    s.append(f'<text x="760" y="140" text-anchor="end" font-size="14" font-weight="bold" fill="#c0392b">{t[9]}</text></svg>')
    return '<figure class="diagram">' + "".join(s) + "</figure>"


# ----------------------------------------------------------------------------------------------------- cover
def cover(lang):
    if lang == "en":
        h, sub = "FINN_SC<br>illustrated tutorial", ("Biomass-burning emissions of Santa Catarina, Brazil, from the Fire INventory "
                                                      "from NCAR: the science, the code and every step to reproduce the results")
        pills = ["for scientists", "for students", "for decision makers", "Python · R · Colab", "version of 11 Nov 2026"]
        foot = ("Repository: https://github.com/jessicajcss/FINN_SC (a Zenodo DOI will replace this address). Companion of the "
                "article submitted to Environmental Science &amp; Technology, of the full-length article v7.2 and of the 2025 "
                "state inventory report. Code and text: MIT licence. Authors: J. C. dos Santos Silva and co-authors (see CITATION.cff).")
    else:
        h, sub = "FINN_SC<br>tutorial ilustrado", ("Emissões da queima de biomassa em Santa Catarina a partir do Fire INventory from "
                                                   "NCAR: a ciência, o código e cada passo para reproduzir os resultados")
        pills = ["para cientistas", "para estudantes", "para gestores", "Python · R · Colab", "versão de 11/11/2026"]
        foot = ("Repositório: https://github.com/jessicajcss/FINN_SC (um DOI do Zenodo substituirá este endereço). Acompanha o "
                "artigo submetido à Environmental Science &amp; Technology, o artigo completo v7.2 e o relatório do inventário "
                "estadual de 2025. Código e texto: licença MIT. Autoria: J. C. dos Santos Silva e coautores (ver CITATION.cff).")
    return (f'<div class="cover"><div class="band"></div><div class="inner"><h1>{h}</h1><div class="sub">{sub}</div>'
            + "".join(f'<span class="pill">{p}</span>' for p in pills) + f'</div><div class="foot">{foot}</div></div>')


# ----------------------------------------------------------------------------------------------------- chapters
def chapters(lang):
    E = lang == "en"
    ch = []

    # 1 ---------------------------------------------------------------- how to use
    legend = "".join(f'<tr><td style="width:34%">{B(k, L(lang, k), "")}</td><td>{d}</td></tr>' for k, d in (
        ("key", "The one idea to keep from the section." if E else "A ideia que vale guardar da seção."),
        ("warn", "A common mistake or a limit of the data." if E else "Um erro comum ou um limite dos dados."),
        ("do", "Commands to type, in order." if E else "Comandos para digitar, na ordem."),
        ("check", "How to know that it worked." if E else "Como saber se deu certo."),
        ("deep", "Extra detail for specialists; safe to skip." if E else "Detalhe extra para especialistas; pode ser pulado.")))
    ch.append(dict(
        title="How to use this tutorial" if E else "Como usar este tutorial", minutes=3,
        **{"for": "everyone" if E else "todos"},
        tldr=("<p>Read chapters 2 to 4 to understand the study, chapters 5 to 7 to run it, and the rest when you need it. "
              "Every chapter opens with this orange box, so you can stop after it and still keep the main point.</p>" if E else
              "<p>Leia os capítulos 2 a 4 para entender o estudo, os capítulos 5 a 7 para executá-lo e os demais quando precisar. "
              "Cada capítulo abre com esta caixa laranja, de modo que você pode parar nela e ainda guardar o essencial.</p>"),
        learn=(["choose your reading path", "recognise the five kinds of boxes", "find any number of the article in the code"] if E else
               ["escolher seu caminho de leitura", "reconhecer os cinco tipos de caixa", "achar no código qualquer número do artigo"]),
        body=(
            (f"<h2>Three reading paths</h2>" if E else "<h2>Três caminhos de leitura</h2>")
            + '<table class="t"><tr><th>' + ("If you want to…" if E else "Se você quer…") + "</th><th>" + ("Read" if E else "Leia") + "</th></tr>"
            + ("<tr><td>know what the study found, in plain words</td><td>2</td></tr>"
               "<tr><td>understand how satellites and FINN estimate emissions</td><td>3 and 4</td></tr>"
               "<tr><td>run everything and check the results</td><td>5, 6 and 7</td></tr>"
               "<tr><td>trace one published number to its code</td><td>8</td></tr>"
               "<tr><td>understand the statistics</td><td>9</td></tr>"
               "<tr><td>compare FINN versions and other inventories</td><td>10</td></tr>"
               "<tr><td>build the inventory of another region</td><td>11 and 12</td></tr>" if E else
               "<tr><td>saber o que o estudo encontrou, em linguagem simples</td><td>2</td></tr>"
               "<tr><td>entender como satélites e o FINN estimam emissões</td><td>3 e 4</td></tr>"
               "<tr><td>executar tudo e conferir os resultados</td><td>5, 6 e 7</td></tr>"
               "<tr><td>rastrear um número publicado até o código</td><td>8</td></tr>"
               "<tr><td>entender a estatística</td><td>9</td></tr>"
               "<tr><td>comparar versões do FINN e outros inventários</td><td>10</td></tr>"
               "<tr><td>montar o inventário de outra região</td><td>11 e 12</td></tr>")
            + "</table>"
            + ("<h2>What each box means</h2>" if E else "<h2>O que cada caixa significa</h2>")
            + f'<table class="legend" style="width:100%">{legend}</table>'
            + B("key", L(lang, "key"),
                "<p>Nothing in this tutorial is new: every number comes from a file in <code>results/</code>, written by a script "
                "of the repository and checked by an automated test. When the text gives a number, the chapter or the table of "
                "chapter 8 tells you where it comes from.</p>" if E else
                "<p>Nada neste tutorial é novo: cada número vem de um arquivo em <code>results/</code>, escrito por um script do "
                "repositório e conferido por um teste automático. Quando o texto traz um número, o capítulo ou a tabela do "
                "capítulo 8 indica de onde ele vem.</p>")),
        quiz=[("Which box can you skip without losing the main point?" if E else "Qual caixa pode ser pulada sem perder o essencial?",
               "The grey “deep dive” box." if E else "A caixa cinza, “para aprofundar”.")]))

    # 2 ---------------------------------------------------------------- the study in one page
    kp = ('<table class="kpis"><tr>'
          + "".join(f'<td><div class="big">{a}</div>{b}</td>' for a, b in (
              (("3,549–8,296", "fire events per year, 2012–2025, with no monotonic trend")
               if E else ("3.549–8.296", "eventos de queimada por ano, 2012 a 2025, sem tendência monotônica")),
              (("3.55 Mt", "CO<sub>2</sub> in 2025 (FINN v2.5.1, MODIS+VIIRS)") if E else ("3,55 Mt", "de CO<sub>2</sub> em 2025 (FINN v2.5.1, MODIS+VIIRS)")),
              (("2.9×", "ratio between the highest (2020) and lowest (2015) annual CO<sub>2</sub>") if E else
               ("2,9×", "razão entre o maior (2020) e o menor (2015) CO<sub>2</sub> anual")),
              (("53.6%", "of grassland-dominated 2 km cells burned in 7 or more of 14 years") if E else
               ("53,6%", "das células de 2 km dominadas por campo queimaram em 7 ou mais dos 14 anos"))))
          + "</tr></table>")
    ch.append(dict(
        title="The study on one page" if E else "O estudo em uma página", minutes=5, **{"for": "everyone" if E else "todos"},
        tldr=("<p>Fire emissions in Santa Catarina vary a lot between years, but <b>three methodological choices change the "
              "totals as much as, or more than, the years do</b>: adding VIIRS detections, the FINN version and the forest "
              "class. Comparisons between years and municipalities hold; absolute totals carry these uncertainties.</p>" if E else
              "<p>As emissões de queimadas em Santa Catarina variam muito entre os anos, mas <b>três escolhas metodológicas alteram "
              "os totais tanto quanto ou mais que os anos</b>: incluir as detecções VIIRS, a versão do FINN e a classe florestal. "
              "As comparações entre anos e municípios se mantêm; os totais absolutos carregam essas incertezas.</p>"),
        learn=(["state the four main findings", "explain why absolute totals need care", "read Figure 4 of the article"] if E else
               ["enunciar os quatro achados principais", "explicar por que os totais absolutos pedem cuidado", "ler a Figura 4 do artigo"]),
        body=(kp
              + ("<h2>Four findings</h2><ol>"
                 "<li><b>Year-to-year variability.</b> Events ranged from 3,549 (2015) to 8,296 (2016) and were fewer in wetter fire "
                 "seasons (Spearman ρ = −0.68 with fire-season precipitation).</li>"
                 "<li><b>Recurrence on the highland grasslands.</b> Fire returns to the same places: 53.6% of the 2 km cells "
                 "dominated by grassland burned in at least 7 of 14 years, mostly on the Serrana plateau.</li>"
                 "<li><b>Methodological choices rival the years.</b> Adding VIIRS raised CO<sub>2</sub> by 40% to 56%. For the same "
                 "2020 MODIS detections, FINN v1.5 gave 2.8 times the FINN v2.5 CO<sub>2</sub>. A tropical forest class would "
                 "multiply the FINN v2.5 CO<sub>2</sub> by 2.4 to 2.7. FINN burned area exceeded the mapped burned area by median "
                 "factors of 17 (MapBiomas Fire) and 34 (MODIS MCD64A1).</li>"
                 "<li><b>Earlier estimates count assumed fires.</b> FINN v1.5 adds a half-size copy of each fire on the next day; "
                 "the earlier state inventory, BRAIN and the FINN v1.5 totals of Teixeira et al. (2025) all include these copies, "
                 "27.0% to 32.4% of the yearly CO<sub>2</sub> in 2002–2020.</li></ol>" if E else
                 "<h2>Quatro achados</h2><ol>"
                 "<li><b>Variabilidade entre anos.</b> Os eventos variaram de 3.549 (2015) a 8.296 (2016) e foram menos numerosos nas "
                 "estações de queimada mais chuvosas (ρ de Spearman = −0,68 com a precipitação da estação).</li>"
                 "<li><b>Recorrência nos campos de altitude.</b> O fogo volta aos mesmos lugares: 53,6% das células de 2 km "
                 "dominadas por campo queimaram em pelo menos 7 de 14 anos, sobretudo no planalto da Serrana.</li>"
                 "<li><b>Escolhas metodológicas rivalizam com os anos.</b> Incluir o VIIRS elevou o CO<sub>2</sub> em 40% a 56%. "
                 "Para as mesmas detecções MODIS de 2020, o FINN v1.5 deu 2,8 vezes o CO<sub>2</sub> do FINN v2.5. Uma classe de "
                 "floresta tropical multiplicaria o CO<sub>2</sub> do FINN v2.5 por 2,4 a 2,7. A área queimada do FINN superou a área "
                 "mapeada por fatores medianos de 17 (MapBiomas Fogo) e 34 (MODIS MCD64A1).</li>"
                 "<li><b>Estimativas anteriores contam focos presumidos.</b> O FINN v1.5 acrescenta uma cópia com metade do tamanho de "
                 "cada foco no dia seguinte; o inventário estadual anterior, o BRAIN e os totais do FINN v1.5 de Teixeira et al. "
                 "(2025) incluem essas cópias, 27,0% a 32,4% do CO<sub>2</sub> anual de 2002 a 2020.</li></ol>")
              + fig(lang, "f9", ("Figure 4 of the ES&amp;T manuscript. Grey: annual CO<sub>2</sub> relative to the 2012–2025 mean. "
                                 "Coloured: CO<sub>2</sub> with each alternative choice relative to the inventory. Script "
                                 "<code>python/analysis/fig_v71.py</code>; values in <code>results/tables/sensitivity_factors.csv</code> "
                                 "(<code>a15_v7_review.py</code>) and <code>forest_class_scenario_annual.csv</code> (<code>a19_v72_followup.py</code>)."
                                 if E else
                                 "Figura 4 do manuscrito da ES&amp;T. Cinza: CO<sub>2</sub> anual em relação à média de 2012 a 2025. Em cor: "
                                 "CO<sub>2</sub> com cada escolha alternativa em relação ao inventário. Script <code>python/analysis/fig_v71.py</code>; "
                                 "valores em <code>results/tables/sensitivity_factors.csv</code> (<code>a15_v7_review.py</code>) e "
                                 "<code>forest_class_scenario_annual.csv</code> (<code>a19_v72_followup.py</code>)."))
              + B("warn", L(lang, "warn"),
                  "<p>“Fire event” here is a FINN daily burned-area polygon, a model unit. It is neither a field-verified fire nor an "
                  "INPE hotspot, so counts from other sources are compared only with the definitions side by side (chapter 3).</p>" if E else
                  "<p>“Evento de queimada” aqui é um polígono diário de área queimada do FINN, uma unidade do modelo. Ele difere de um "
                  "incêndio verificado em campo e de um foco de calor do INPE, por isso contagens de outras fontes só se comparam com "
                  "as definições lado a lado (capítulo 3).</p>")),
        quiz=[(("Which choice changed the 2020 CO<sub>2</sub> the most?" if E else "Qual escolha mais alterou o CO<sub>2</sub> de 2020?"),
               ("The FINN version: FINN v1.5 gave 2.8 times the FINN v2.5 MODIS value." if E else
                "A versão do FINN: o FINN v1.5 deu 2,8 vezes o valor do FINN v2.5 MODIS.")),
              (("Do the rankings of municipalities depend on these choices?" if E else "As posições dos municípios dependem dessas escolhas?"),
               ("Much less than the totals: relative patterns were robust." if E else "Bem menos que os totais: os padrões relativos foram robustos."))]))

    # 3 ---------------------------------------------------------------- the science
    ch.append(dict(
        title="Fire, satellites and emissions" if E else "Fogo, satélites e emissões", minutes=10,
        **{"for": "students and non-specialists" if E else "estudantes e não especialistas"},
        tldr=("<p>Satellites detect the heat of active fires. FINN turns each detection into burned area, multiplies it by "
              "fuel, burned fraction and emission factors, and writes one row (a <b>record</b>) per detection and vegetation "
              "type. We count <b>fire events</b>, the daily burned-area polygons, after removing persistent heat sources.</p>" if E else
              "<p>Satélites detectam o calor dos focos ativos. O FINN transforma cada detecção em área queimada, multiplica-a pela "
              "carga de combustível, pela fração queimada e pelos fatores de emissão e escreve uma linha (um <b>registro</b>) por "
              "detecção e tipo de vegetação. Contamos <b>eventos de queimada</b>, os polígonos diários de área queimada, depois de "
              "remover as fontes de calor persistentes.</p>"),
        learn=(["explain the FINN equation", "tell a record from a detection and an event", "convert FINN units to tonnes"] if E else
               ["explicar a equação do FINN", "distinguir registro, detecção e evento", "converter as unidades do FINN para toneladas"]),
        body=(("<h2>3.1 Why estimate fire emissions</h2><p>Open burning releases CO<sub>2</sub>, CO, fine particles "
               "(PM<sub>2.5</sub>), nitrogen oxides and volatile organic compounds. Air-quality models, health studies and climate "
               "inventories need these emissions by place and day, and ground measurements cannot cover a whole State. Satellite "
               "inventories fill this gap.</p>" if E else
               "<h2>3.1 Por que estimar emissões de queimadas</h2><p>A queima a céu aberto libera CO<sub>2</sub>, CO, partículas finas "
               "(MP<sub>2,5</sub>), óxidos de nitrogênio e compostos orgânicos voláteis. Modelos de qualidade do ar, estudos de saúde "
               "e inventários climáticos precisam dessas emissões por local e por dia, e medições em solo não cobrem um Estado "
               "inteiro. Os inventários por satélite preenchem essa lacuna.</p>")
              + ("<h2>3.2 How satellites see fire</h2><p><b>MODIS</b> (on the Terra and Aqua satellites) detects active fires in 1 km "
                 "pixels; <b>VIIRS</b> (Suomi NPP, NOAA-20) does so in 375 m pixels and sees smaller fires (Giglio et al., 2016; "
                 "Schroeder et al., 2014). Each satellite passes over a place about twice a day, so fires that start and end between "
                 "passes, or under clouds, are missed.</p>" if E else
                 "<h2>3.2 Como os satélites enxergam o fogo</h2><p>O <b>MODIS</b> (satélites Terra e Aqua) detecta focos ativos em pixels "
                 "de 1 km; o <b>VIIRS</b> (Suomi NPP, NOAA-20) faz isso em pixels de 375 m e enxerga focos menores (Giglio et al., "
                 "2016; Schroeder et al., 2014). Cada satélite passa sobre um local cerca de duas vezes ao dia, de modo que focos que "
                 "começam e terminam entre as passagens, ou sob nuvens, ficam de fora.</p>")
              + ("<h2>3.3 The FINN equation</h2>" if E else "<h2>3.3 A equação do FINN</h2>") + svg_equation(lang)
              + ("<p>For each detection, FINN assigns a burned area (A) from the pixel and the vegetation map, the fuel loading (B) "
                 "and the fraction burned (CF) of the vegetation type, and an emission factor (EF) for each compound (Wiedinmyer et "
                 "al., 2011, 2023). The vegetation types are six generic classes (GENVEG): grassland and savanna, woody savanna and "
                 "shrubland, tropical forest, temperate forest, boreal forest and cropland.</p>" if E else
                 "<p>Para cada detecção, o FINN atribui uma área queimada (A) a partir do pixel e do mapa de vegetação, a carga de "
                 "combustível (B) e a fração queimada (CF) do tipo de vegetação e um fator de emissão (EF) para cada composto "
                 "(Wiedinmyer et al., 2011, 2023). Os tipos de vegetação são seis classes genéricas (GENVEG): campo e savana, savana "
                 "arborizada e arbustos, floresta tropical, floresta temperada, floresta boreal e agricultura.</p>")
              + ("<h2>3.4 Record, detection and event</h2>" if E else "<h2>3.4 Registro, detecção e evento</h2>") + svg_units(lang)
              + B("key", L(lang, "key"),
                  "<p>Counts change by unit. In 2025: 8,581 records, 5,489 detections and 5,160 fire events (5,121 after the screening "
                  "below). This repository counts <b>fire events</b>, each assigned to the municipality that holds most of its area "
                  "(<code>a01_events_screening.py</code> → <code>state_counts.csv</code>).</p>" if E else
                  "<p>As contagens mudam com a unidade. Em 2025: 8.581 registros, 5.489 detecções e 5.160 eventos de queimada (5.121 "
                  "após a triagem abaixo). Este repositório conta <b>eventos de queimada</b>, cada um atribuído ao município que contém a "
                  "maior parte de sua área (<code>a01_events_screening.py</code> → <code>state_counts.csv</code>).</p>")
              + ("<h2>3.5 Persistent thermal anomalies</h2><p>Some heat sources are not vegetation fires: industrial plants, mines, "
                 "burning coal waste. A location with detections on 16 or more days of a calendar year within 1 km is treated as a "
                 "persistent thermal anomaly, the criterion of the MODIS product (Giglio et al., 2021). These events are removed from "
                 "counts and maps and kept in the emission totals, where their share is small (at most 2.5% of CO<sub>2</sub>, in "
                 "2020).</p>" if E else
                 "<h2>3.5 Anomalias térmicas persistentes</h2><p>Algumas fontes de calor diferem de queimadas de vegetação: indústrias, "
                 "minas, rejeitos de carvão em combustão. Um local com detecções em 16 ou mais dias de um ano civil, num raio de 1 km, é "
                 "tratado como anomalia térmica persistente, o critério do produto MODIS (Giglio et al., 2021). Esses eventos saem das "
                 "contagens e dos mapas e permanecem nos totais de emissão, onde sua participação é pequena (no máximo 2,5% do "
                 "CO<sub>2</sub>, em 2020).</p>")
              + ("<h2>3.6 Units: from moles per day to tonnes</h2><p>FINN files give gases in mol/day and aerosols (OC, BC, "
                 "PM<sub>2.5</sub>) and a few mass fields in kg/day. Tonnes of a gas = mol × molar mass (g/mol) × 10<sup>−6</sup>; "
                 "tonnes of an aerosol = kg × 10<sup>−3</sup>. In the FINN v2.5 files, <code>NOXasNO</code>, <code>NMOC</code> and "
                 "<code>NMHC</code> are already mass fields (kg/day); NO<sub>x</sub> is reported as the mass of NO and VOC as NMOC "
                 "(<code>python/finn_sc/convert_units.py</code>, checked by <code>a09_emission_factor_check.py</code>).</p>" if E else
                 "<h2>3.6 Unidades: de mol por dia para toneladas</h2><p>Os arquivos do FINN trazem os gases em mol/dia e os aerossóis "
                 "(OC, BC, MP<sub>2,5</sub>) e alguns campos de massa em kg/dia. Toneladas de um gás = mol × massa molar (g/mol) × "
                 "10<sup>−6</sup>; toneladas de um aerossol = kg × 10<sup>−3</sup>. Nos arquivos do FINN v2.5, <code>NOXasNO</code>, "
                 "<code>NMOC</code> e <code>NMHC</code> já são campos de massa (kg/dia); os NO<sub>x</sub> são expressos como massa de NO "
                 "e os COV como NMOC (<code>python/finn_sc/convert_units.py</code>, conferido por <code>a09_emission_factor_check.py</code>).</p>")
              + B("warn", L(lang, "warn"),
                  "<p>FINN burned area is the area assigned to each detection by the model, much larger than the area mapped from "
                  "burn scars: median 17 times MapBiomas Fire and 34 times MCD64A1 in Santa Catarina. Use it as a model term, not as "
                  "mapped burned area.</p>" if E else
                  "<p>A área queimada do FINN é a área atribuída pelo modelo a cada detecção, muito maior que a área mapeada a partir "
                  "de cicatrizes: mediana de 17 vezes a do MapBiomas Fogo e 34 vezes a do MCD64A1 em Santa Catarina. Use-a como termo "
                  "do modelo, e não como área queimada mapeada.</p>")),
        quiz=[(("A detection split between forest and cropland gives how many records?" if E else
                "Uma detecção dividida entre floresta e agricultura gera quantos registros?"), ("Two." if E else "Dois.")),
              (("How many tonnes are 1,000 mol of CO<sub>2</sub>?" if E else "Quantas toneladas são 1.000 mol de CO<sub>2</sub>?"),
               ("1,000 × 44.01 × 10<sup>−6</sup> = 0.044 t." if E else "1.000 × 44,01 × 10<sup>−6</sup> = 0,044 t."))]))

    # 4 ---------------------------------------------------------------- versions and conventions
    ch.append(dict(
        title="FINN versions and their conventions" if E else "Versões do FINN e suas convenções", minutes=8,
        **{"for": "users of FINN data" if E else "usuários de dados do FINN"},
        tldr=("<p>This inventory uses <b>FINN v2.5</b> (2012–2021) and <b>v2.5.1</b> (2022–2025) with MODIS and VIIRS. Two "
              "conventions of the model matter in Santa Catarina: FINN v1.5 adds next-day copies of fires (v2.5 does not, at "
              "these latitudes), and both versions classify the State's forests as <b>temperate</b> because it lies south of "
              "23.5° S.</p>" if E else
              "<p>Este inventário usa o <b>FINN v2.5</b> (2012 a 2021) e o <b>v2.5.1</b> (2022 a 2025) com MODIS e VIIRS. Duas "
              "convenções do modelo pesam em Santa Catarina: o FINN v1.5 acrescenta cópias dos focos no dia seguinte (o v2.5 não faz "
              "isso nestas latitudes), e as duas versões classificam as florestas do Estado como <b>temperadas</b>, porque ele está "
              "ao sul de 23,5° S.</p>"),
        learn=(["pick the right FINN file for a year", "explain the next-day continuation", "explain the forest-class boundary",
                "follow the data terms of NSF NCAR"] if E else
               ["escolher o arquivo do FINN de cada ano", "explicar a continuação no dia seguinte", "explicar o limite da classe florestal",
                "seguir os termos de uso de dados do NSF NCAR"]),
        body=(("<h2>4.1 Which file for which year</h2>" if E else "<h2>4.1 Qual arquivo para cada ano</h2>")
              + '<table class="t"><tr><th>' + ("Version" if E else "Versão") + "</th><th>" + ("Detections" if E else "Detecções")
              + "</th><th>" + ("Years" if E else "Anos") + "</th><th>" + ("File (GEOS-Chem, each fire)" if E else "Arquivo (GEOS-Chem, cada foco)") + "</th></tr>"
              + "<tr><td>v1.5</td><td>MODIS</td><td>2002–2020</td><td><code>FINNv1.5_&lt;year&gt;.GEOSCHEM.tar.gz</code> (" + ("annual, every year" if E else "anual, todos os anos") + ")</td></tr>"
              + "<tr><td>v2.5</td><td>MODIS</td><td>2003–2021</td><td><code>FINNv2.5_mod_GEOSCHEM_&lt;year&gt;_c2021…txt.gz</code></td></tr>"
              + "<tr><td>v2.5</td><td>MODIS+VIIRS</td><td>2012–2021</td><td><code>FINNv2.5_modvrs_GEOSCHEM_&lt;year&gt;_c2021…txt.gz</code></td></tr>"
              + "<tr><td>v2.5.1</td><td>" + ("both" if E else "ambos") + "</td><td>2022–2023</td><td>" + ("monthly files" if E else "arquivos mensais") + "</td></tr>"
              + "<tr><td>v2.5.1 NRT</td><td>MODIS+VIIRS</td><td>2024–</td><td>" + ("daily near-real-time files" if E else "arquivos diários em tempo quase real") + "</td></tr></table>"
              + ("<p>The exact addresses are built by <code>R/utils_finn.R</code> and <code>python/finn_sc/download.py</code>. "
                 "The FINN v1.5 file of 2002 is also a <code>.tar.gz</code> archive; an older <code>.txt.gz</code> address returns "
                 "“404 Not Found” (corrected on 11 Nov 2026).</p>" if E else
                 "<p>Os endereços exatos são montados por <code>R/utils_finn.R</code> e <code>python/finn_sc/download.py</code>. O "
                 "arquivo do FINN v1.5 de 2002 também é um arquivo <code>.tar.gz</code>; um endereço antigo <code>.txt.gz</code> "
                 "retorna “404 Not Found” (corrigido em 11/11/2026).</p>")
              + ("<h2>4.2 The next-day continuation of FINN v1.5</h2>" if E else "<h2>4.2 A continuação no dia seguinte do FINN v1.5</h2>")
              + svg_twoday(lang)
              + ("<p>Because MODIS does not observe low and middle latitudes every day, FINNv1 counts each detection for two days, "
                 "the second at half its size, unless the place is detected again; its authors noted that this assumption had yet "
                 "to be verified (Wiedinmyer et al., 2011). In 2020, 1,893 of the 4,609 FINN v1.5 records in Santa Catarina were such "
                 "continuations, 27.0% of the CO<sub>2</sub> (<code>a17_v72_review.py</code>). FINN v2.5 keeps the rule only between "
                 "23.5° N and 23.5° S (Wiedinmyer et al., 2023), and our FINN v2.5 and v2.5.1 records confirm it: 1 of 151,443 "
                 "day-location pairs has the half-size signature (<code>a20_finn15_correction.py</code>).</p>" if E else
                 "<p>Como o MODIS não observa as latitudes baixas e médias todos os dias, o FINNv1 conta cada detecção por dois dias, o "
                 "segundo com metade do tamanho, a menos que o local seja detectado de novo; seus autores registraram que esse "
                 "pressuposto ainda não havia sido verificado (Wiedinmyer et al., 2011). Em 2020, 1.893 dos 4.609 registros do FINN v1.5 "
                 "em Santa Catarina eram essas continuações, 27,0% do CO<sub>2</sub> (<code>a17_v72_review.py</code>). O FINN v2.5 mantém "
                 "a regra apenas entre 23,5° N e 23,5° S (Wiedinmyer et al., 2023), e nossos registros do FINN v2.5 e v2.5.1 confirmam "
                 "isso: 1 de 151.443 pares dia-local tem a assinatura de metade do tamanho (<code>a20_finn15_correction.py</code>).</p>")
              + ("<h2>4.3 The forest class depends on latitude</h2><p>FINN v2.5 classes evergreen broadleaf and mixed forests as "
                 "tropical forest only between 23.5° N and 23.5° S, and as temperate forest elsewhere (Wiedinmyer et al., 2023, Table "
                 "1). Santa Catarina (25.96° S to 29.36° S) falls outside, although its forests belong to the Atlantic Forest. The "
                 "class sets the fuel loading: in South America, 26,755 g m<sup>−2</sup> for tropical and 7,400 g m<sup>−2</sup> for "
                 "temperate forest. With the tropical class, each forest detection would emit 3.93 times more CO<sub>2</sub>, and the "
                 "State's annual CO<sub>2</sub> would be 2.42 to 2.74 times larger (<code>a19_v72_followup.py</code>), an upper bound "
                 "because the class also holds deciduous forest.</p>" if E else
                 "<h2>4.3 A classe florestal depende da latitude</h2><p>O FINN v2.5 classifica florestas perenifólias latifoliadas e mistas "
                 "como floresta tropical apenas entre 23,5° N e 23,5° S, e como floresta temperada nas demais latitudes (Wiedinmyer et al., "
                 "2023, Tabela 1). Santa Catarina (25,96° S a 29,36° S) fica fora dessa faixa, embora suas florestas pertençam à Mata "
                 "Atlântica. A classe define a carga de combustível: na América do Sul, 26.755 g m<sup>−2</sup> para floresta tropical e "
                 "7.400 g m<sup>−2</sup> para temperada. Com a classe tropical, cada detecção em floresta emitiria 3,93 vezes mais "
                 "CO<sub>2</sub>, e o CO<sub>2</sub> anual do Estado seria 2,42 a 2,74 vezes maior (<code>a19_v72_followup.py</code>), um "
                 "limite superior, porque a classe também inclui florestas decíduas.</p>")
              + ("<h2>4.4 Data terms</h2>" if E else "<h2>4.4 Termos de uso dos dados</h2>")
              + B("warn", L(lang, "warn"),
                  "<ul><li>FINN v1.5: the FINN page of NSF NCAR (https://www.acom.ucar.edu/Data/fire/) asks users to submit their "
                  "name and contact information before downloading. Do this before running any FINN v1.5 download.</li>"
                  "<li>FINN v2.5 and v2.5.1: NSF NCAR Research Data Archive, dataset ds312.9 (Wiedinmyer and Emmons, 2022, "
                  "doi:10.5065/XNPA-AF09). UCAR's data terms grant use under the Creative Commons Attribution 4.0 licence unless "
                  "otherwise stated and ask users to cite the data with the repository's recommended citation.</li>"
                  "<li>Cite the model papers (Wiedinmyer et al., 2011, 2023) in any work that uses FINN.</li></ul>" if E else
                  "<ul><li>FINN v1.5: a página do FINN no NSF NCAR (https://www.acom.ucar.edu/Data/fire/) pede que o usuário informe nome "
                  "e contato antes de baixar os arquivos. Faça isso antes de rodar qualquer download do FINN v1.5.</li>"
                  "<li>FINN v2.5 e v2.5.1: NSF NCAR Research Data Archive, conjunto ds312.9 (Wiedinmyer e Emmons, 2022, "
                  "doi:10.5065/XNPA-AF09). Os termos de dados da UCAR concedem uso sob a licença Creative Commons Atribuição 4.0, "
                  "salvo indicação em contrário, e pedem a citação recomendada pelo repositório.</li>"
                  "<li>Cite os artigos do modelo (Wiedinmyer et al., 2011, 2023) em qualquer trabalho que use o FINN.</li></ul>")),
        quiz=[(("Does FINN v2.5 add next-day continuations in Santa Catarina?" if E else
                "O FINN v2.5 acrescenta continuações no dia seguinte em Santa Catarina?"),
               ("No: only between 23.5° N and 23.5° S; the State is south of that band." if E else
                "Apenas entre 23,5° N e 23,5° S; o Estado fica ao sul dessa faixa, então a resposta é negativa.")),
              (("Why are the State's forests “temperate” in FINN?" if E else "Por que as florestas do Estado são “temperadas” no FINN?"),
               ("Because FINN v2.5 uses the tropical class only within 23.5° of the equator." if E else
                "Porque o FINN v2.5 usa a classe tropical apenas até 23,5° do equador."))]))

    # 5 ---------------------------------------------------------------- the repository
    tree = ("FINN_SC/\n├── README.md, README.pt-BR.md      " + ("start here" if E else "comece aqui")
            + "\n├── TUTORIAL_FINN_SC_en.pdf, _pt.pdf  " + ("this tutorial" if E else "este tutorial")
            + "\n├── config/config.yml               " + ("every parameter (years, version, region)" if E else "todos os parâmetros (anos, versão, região)")
            + "\n├── data/derived/                   " + ("archived FINN records of SC (route B input)" if E else "registros FINN de SC arquivados (entrada da rota B)")
            + "\n├── data/external/                  " + ("MapBiomas, MCD64A1, ERA5-Land, IBGE, FINN v1.5 records" if E else "MapBiomas, MCD64A1, ERA5-Land, IBGE, registros FINN v1.5")
            + "\n├── data/inputs/                    " + ("IBGE 2024 municipal mesh of SC" if E else "malha municipal do IBGE 2024 de SC")
            + "\n├── python/00_ … 06_*.py            " + ("route A in Python" if E else "rota A em Python")
            + "\n├── python/analysis/a01 … a20       " + ("route B: one script per group of results" if E else "rota B: um script por grupo de resultados")
            + "\n├── python/run_analysis.py          " + ("route B in one command" if E else "rota B em um comando")
            + "\n├── R/                              " + ("route A in R; kernel density" if E else "rota A em R; densidade kernel")
            + "\n├── gee/                            " + ("Google Earth Engine recipes" if E else "receitas do Google Earth Engine")
            + "\n├── notebooks/                      " + ("route A notebooks; BRAIN comparison" if E else "notebooks da rota A; comparação com o BRAIN")
            + "\n├── tools/                          " + ("maps, FINN v1.5 tools, manifest check" if E else "mapas, ferramentas do FINN v1.5, conferência do manifesto")
            + "\n├── tests/                          " + ("96 automated tests" if E else "96 testes automáticos")
            + "\n├── results/                        " + ("published tables, figures, logs" if E else "tabelas, figuras e logs publicados")
            + "\n└── docs/                           " + ("methods, provenance, data dictionary" if E else "métodos, procedência, dicionário de dados"))
    ch.append(dict(
        title="Inside the repository" if E else "Por dentro do repositório", minutes=5,
        **{"for": "anyone who will run the code" if E else "quem vai executar o código"},
        tldr=("<p>There are two routes. <b>Route B</b> recomputes every number of the article offline from the archived "
              "records. <b>Route A</b> downloads FINN files from NSF NCAR and builds the records, for Santa Catarina or any other "
              "region.</p>" if E else
              "<p>Há duas rotas. A <b>rota B</b> recalcula offline cada número do artigo a partir dos registros arquivados. A "
              "<b>rota A</b> baixa os arquivos do FINN no NSF NCAR e monta os registros, para Santa Catarina ou qualquer outra "
              "região.</p>"),
        learn=(["find any folder", "choose route A or route B"] if E else ["encontrar qualquer pasta", "escolher entre a rota A e a rota B"]),
        body=(svg_routes(lang) + f"<pre>{tree}</pre>"
              + B("key", L(lang, "key"),
                  "<p>Route B starts from <code>data/derived/finn_sc_records_2003_2025.csv.gz</code>: 258,694 FINN v2.5 and v2.5.1 "
                  "records inside Santa Catarina. It needs no internet and no FINN download.</p>" if E else
                  "<p>A rota B parte de <code>data/derived/finn_sc_records_2003_2025.csv.gz</code>: 258.694 registros do FINN v2.5 e "
                  "v2.5.1 em Santa Catarina. Ela dispensa internet e download do FINN.</p>")
              + ("<h2>What each analysis script answers</h2>" if E else "<h2>O que cada script de análise responde</h2>")
              + '<table class="t"><tr><th>Script</th><th>' + ("Question" if E else "Pergunta") + "</th></tr>"
              + "".join(f"<tr><td><code>{a}</code></td><td>{b}</td></tr>" for a, b in (
                  ([("a01", "How many records, detections and events? Which are persistent anomalies?"),
                    ("a02", "Annual series, Table 2, effect of VIIRS, trend tests"),
                    ("a03", "Municipalities and mesoregions in 2025; seasonality"),
                    ("a04", "Area and emissions by vegetation type (GENVEG)"),
                    ("a05", "FINN area vs MapBiomas Fire"),
                    ("a06", "Fire activity vs fire-season climate"),
                    ("a07", "Municipal land cover vs event density"),
                    ("a08–a09", "Report indicators; unit-conversion check"),
                    ("a10", "Figures of the earlier manuscript and report"),
                    ("a11–a12", "Co-authors' questions; Earth Engine outputs (MCD64A1, ERA5-Land)"),
                    ("a13", "Fire recurrence in 2 km cells and land cover"),
                    ("a14", "Validity checks (FINN vegetation vs MapBiomas, bootstrap)"),
                    ("a15", "Robustness: exact trend tests, VIIRS ratio, sensitivity factors"),
                    ("a16–a17", "FINN v1.5 vs v2.5 in 2020; next-day continuations"),
                    ("a18", "Exports of municipalities and mesoregions (Comex Stat)"),
                    ("a19", "Forest-class scenario; NO<sub>x</sub> of the earlier inventory"),
                    ("a20", "FINN v1.5 inventories with and without the continuations, 2002–2020")] if E else
                   [("a01", "Quantos registros, detecções e eventos? Quais são anomalias persistentes?"),
                    ("a02", "Séries anuais, Tabela 2, efeito do VIIRS, testes de tendência"),
                    ("a03", "Municípios e mesorregiões em 2025; sazonalidade"),
                    ("a04", "Área e emissões por tipo de vegetação (GENVEG)"),
                    ("a05", "Área do FINN vs MapBiomas Fogo"),
                    ("a06", "Atividade de fogo vs clima da estação de queimadas"),
                    ("a07", "Cobertura do solo municipal vs densidade de eventos"),
                    ("a08–a09", "Indicadores do relatório; conferência das unidades"),
                    ("a10", "Figuras do manuscrito e do relatório anteriores"),
                    ("a11–a12", "Perguntas dos coautores; resultados do Earth Engine (MCD64A1, ERA5-Land)"),
                    ("a13", "Recorrência do fogo em células de 2 km e cobertura do solo"),
                    ("a14", "Verificações de validade (vegetação do FINN vs MapBiomas, bootstrap)"),
                    ("a15", "Robustez: testes de tendência exatos, razão do VIIRS, fatores de sensibilidade"),
                    ("a16–a17", "FINN v1.5 vs v2.5 em 2020; continuações no dia seguinte"),
                    ("a18", "Exportações dos municípios e mesorregiões (Comex Stat)"),
                    ("a19", "Cenário da classe florestal; NO<sub>x</sub> do inventário anterior"),
                    ("a20", "Inventários do FINN v1.5 com e sem as continuações, 2002 a 2020")]))) + "</table>"),
        quiz=[(("Which route needs internet?" if E else "Qual rota precisa de internet?"), ("Route A." if E else "A rota A."))]))

    # 6 ---------------------------------------------------------------- run route B
    ch.append(dict(
        title="Hands on: reproduce the results" if E else "Mão na massa: reproduza os resultados", minutes=10,
        **{"for": "anyone with Python" if E else "quem tem Python"},
        tldr=("<p>Three commands: install, run, check. If the tests say <b>96 passed</b> and the manifest says <b>107 files: OK "
              "107</b>, your computer reproduced every published number.</p>" if E else
              "<p>Três comandos: instalar, executar, conferir. Se os testes disserem <b>96 passed</b> e o manifesto disser <b>107 "
              "files: OK 107</b>, seu computador reproduziu todos os números publicados.</p>"),
        learn=(["install the environment", "run route B", "verify the outputs against the published ones"] if E else
               ["instalar o ambiente", "executar a rota B", "conferir as saídas com as publicadas"]),
        body=(B("do", L(lang, "do") + (" · 1. install (once)" if E else " · 1. instalar (uma vez)"),
                "<pre>git clone https://github.com/jessicajcss/FINN_SC.git\ncd FINN_SC\n"
                "conda env create -f environment.yml &amp;&amp; conda activate finn\n"
                + ("<span class=\"c\"># or: python -m pip install -r requirements.txt</span>\n" if E else
                   "<span class=\"c\"># ou: python -m pip install -r requirements.txt</span>\n")
                + "Rscript install_r_packages.R   " + ("<span class=\"c\"># optional: R for the kernel density</span>" if E else
                                                      "<span class=\"c\"># opcional: R para a densidade kernel</span>") + "</pre>")
              + B("do", L(lang, "do") + (" · 2. run route B" if E else " · 2. executar a rota B"),
                  "<pre>python python/run_analysis.py --no-r\n"
                  + ("<span class=\"c\"># without --no-r it also runs R (the annual kernel sensitivity takes about 40 min)</span>" if E else
                     "<span class=\"c\"># sem --no-r também roda o R (a sensibilidade anual da densidade leva cerca de 40 min)</span>")
                  + "</pre><p>" + ("Shortcuts: <code>make reproduce</code>, <code>./run_all.sh analysis</code> (Linux, macOS) or "
                                   "<code>run_all.bat analysis</code> (Windows)." if E else
                                   "Atalhos: <code>make reproduce</code>, <code>./run_all.sh analysis</code> (Linux, macOS) ou "
                                   "<code>run_all.bat analysis</code> (Windows).") + "</p>")
              + B("check", L(lang, "check") + (" · 3. verify" if E else " · 3. conferir"),
                  "<pre>python -m pytest -q tests          <span class=\"c\"># 96 passed</span>\n"
                  "python tools/verify_manifest.py    <span class=\"c\"># 107 files: OK 107</span></pre>"
                  + ("<p>The manifest (<code>results/MANIFEST.sha256</code>) holds the SHA-256 of every published table and log "
                     "(figures are left out, because PNG files carry the library version in their metadata). OK means identical "
                     "bytes; EQUIVALENT means that every number agrees within a relative tolerance of 10<sup>−9</sup>, as happens "
                     "when another library version prints a different last digit. Run the check in a fresh clone and commit nothing "
                     "before it.</p>" if E else
                     "<p>O manifesto (<code>results/MANIFEST.sha256</code>) guarda o SHA-256 de cada tabela e log publicados (as figuras "
                     "ficam de fora, porque os arquivos PNG carregam a versão da biblioteca em seus metadados). OK indica bytes "
                     "idênticos; EQUIVALENT indica que todos os números concordam dentro de uma tolerância relativa de 10<sup>−9</sup>, "
                     "como ocorre quando outra versão de biblioteca imprime um último dígito diferente. Faça a conferência num clone "
                     "recém-baixado, sem commits antes dela.</p>"))
              + ("<h2>Where the outputs go</h2>" if E else "<h2>Para onde vão as saídas</h2>")
              + '<table class="t"><tr><th>' + ("Folder" if E else "Pasta") + "</th><th>" + ("Content" if E else "Conteúdo") + "</th></tr>"
              + ("<tr><td><code>results/tables/</code></td><td>CSV tables, one or more per script</td></tr>"
                 "<tr><td><code>results/figures/</code></td><td>PNG figures (English <code>_en</code>, Portuguese without suffix; "
                 "<code>_nn</code> = no note inside the image)</td></tr>"
                 "<tr><td><code>results/logs/</code></td><td>one text log per script, with every number printed</td></tr>" if E else
                 "<tr><td><code>results/tables/</code></td><td>tabelas CSV, uma ou mais por script</td></tr>"
                 "<tr><td><code>results/figures/</code></td><td>figuras PNG (inglês <code>_en</code>, português sem sufixo; "
                 "<code>_nn</code> = sem nota dentro da imagem)</td></tr>"
                 "<tr><td><code>results/logs/</code></td><td>um log de texto por script, com todos os números impressos</td></tr>")
              + "</table>"
              + B("warn", L(lang, "warn"),
                  "<p>Run the commands from the repository root (the folder that holds <code>README.md</code>). Most errors of "
                  "“file not found” come from running them inside a subfolder.</p>" if E else
                  "<p>Execute os comandos a partir da raiz do repositório (a pasta que contém o <code>README.md</code>). A maioria dos "
                  "erros de “arquivo não encontrado” vem de executá-los dentro de uma subpasta.</p>")),
        quiz=[(("What does “107 files: OK 107” mean?" if E else "O que significa “107 files: OK 107”?"),
               ("Every published output was reproduced byte for byte." if E else "Cada saída publicada foi reproduzida byte a byte."))]))

    # 7 ---------------------------------------------------------------- figures tour
    ch.append(dict(
        title="Reading the main figures" if E else "Lendo as figuras principais", minutes=8, **{"for": "everyone" if E else "todos"},
        tldr=("<p>Four figures tell the story: where the State is (Figure 1), how the years changed (Figure 2), where fire "
              "recurs (Figure 3) and how much the methodological choices weigh (Figure 4, chapter 2).</p>" if E else
              "<p>Quatro figuras contam a história: onde fica o Estado (Figura 1), como os anos variaram (Figura 2), onde o fogo se "
              "repete (Figura 3) e quanto pesam as escolhas metodológicas (Figura 4, capítulo 2).</p>"),
        learn=(["read each panel", "name the script behind each figure"] if E else ["ler cada painel", "dizer qual script gera cada figura"]),
        body=(fig(lang, "f1", ("Figure 1. Santa Catarina, its six mesoregions and land use in 2023 (MapBiomas Collection 10.1). "
                               "Script <code>tools/study_area_map.py</code>." if E else
                               "Figura 1. Santa Catarina, suas seis mesorregiões e o uso do solo em 2023 (MapBiomas Coleção 10.1). "
                               "Script <code>tools/study_area_map.py</code>."))
              + fig(lang, "f2", ("Figure 2. Annual events, FINN burned area, CO<sub>2</sub> and PM<sub>2.5</sub> by FINN "
                                 "configuration. Script <code>python/analysis/figures_est_en.py</code>; data "
                                 "<code>series_state_all_products.csv</code> (a02)." if E else
                                 "Série anual de eventos, área queimada do FINN e emissões por configuração do FINN "
                                 "(versão em português da figura do artigo). Dados <code>series_state_all_products.csv</code> (a02)."))
              + B("key", L(lang, "key"),
                  "<p>Compare years within one colour (one FINN configuration). Jumping between colours mixes the change of the "
                  "fires with the change of the method.</p>" if E else
                  "<p>Compare os anos dentro de uma mesma cor (uma configuração do FINN). Saltar entre cores mistura a mudança dos "
                  "focos com a mudança do método.</p>")
              + fig(lang, "f8", ("Figure 3. (a) Years with fire, 2012–2025, in each 2 km cell; (b) share of cells by dominant land "
                                 "cover. Script <code>python/analysis/fig_v71.py</code>; data from <code>a13_recurrence_landcover.py</code>." if E else
                                 "Figura 3. (a) Anos com fogo, 2012 a 2025, em cada célula de 2 km; (b) proporção de células por cobertura "
                                 "dominante. Script <code>python/analysis/fig_v71.py</code>; dados de <code>a13_recurrence_landcover.py</code>."))
              + fig(lang, "f5", ("Kernel density of the 2025 fire events (Supporting Information). Script "
                                 "<code>R/analysis/kde_events.R</code>." if E else
                                 "Densidade kernel dos eventos de 2025 (material suplementar). Script <code>R/analysis/kde_events.R</code>."))),
        quiz=[(("Which script draws Figure 3?" if E else "Qual script desenha a Figura 3?"), ("<code>python/analysis/fig_v71.py</code>."))]))

    # 8 ---------------------------------------------------------------- results map
    rows = [
        ("3,549–8,296 events per year (2012–2025)", "3.549–8.296 eventos por ano (2012 a 2025)", "a02_series_trends.py", "series_state_all_products.csv"),
        ("3.55 Mt CO<sub>2</sub> in 2025 (Table 2)", "3,55 Mt de CO<sub>2</sub> em 2025 (Tabela 2)", "a02_series_trends.py", "table2_state_emissions_2012_2025.csv"),
        ("CO<sub>2</sub> max/min between years 2.88", "CO<sub>2</sub> máx./mín. entre anos 2,88", "a15_v7_review.py", "log a15_v7_review.txt"),
        ("Spearman ρ = −0.68 with precipitation", "ρ de Spearman = −0,68 com a precipitação", "a06_climate_drivers.py", "climate_correlations.csv"),
        ("53.6% of grassland cells burned ≥ 7 of 14 years", "53,6% das células de campo queimaram ≥ 7 de 14 anos", "a13_recurrence_landcover.py", "recurrence_by_landcover.csv"),
        ("VIIRS: CO<sub>2</sub> +39.6% to +56.2%", "VIIRS: CO<sub>2</sub> +39,6% a +56,2%", "a02_series_trends.py", "viirs_effect.csv"),
        ("FINN v1.5 / v2.5 MODIS = 2.82 (2020)", "FINN v1.5 / v2.5 MODIS = 2,82 (2020)", "a17_v72_review.py", "finn15_v25_2020_decomposition.csv"),
        ("Continuations 27.0% of CO<sub>2</sub> (2020)", "Continuações: 27,0% do CO<sub>2</sub> (2020)", "a17_v72_review.py", "finn15_2020_continuation_rule.csv"),
        ("Tropical forest class: × 2.42 to 2.74", "Classe de floresta tropical: × 2,42 a 2,74", "a19_v72_followup.py", "forest_class_scenario_annual.csv"),
        ("FINN area / MapBiomas Fire: median 17.2", "Área do FINN / MapBiomas Fogo: mediana 17,2", "a05_mapbiomas_comparison.py", "mapbiomas_state.csv"),
        ("FINN area / MCD64A1: median 34.4", "Área do FINN / MCD64A1: mediana 34,4", "a12_gee_review_outputs.py", "mcd64a1_comparison_summary.csv"),
        ("Earlier inventory = all FINN v1.5 records × 1.002", "Inventário anterior = todos os registros do FINN v1.5 × 1,002", "a20_finn15_correction.py", "finn15_lcqar_2020_correction.csv"),
        ("BRAIN 2019 = records × 1.010, originals × 1.390", "BRAIN 2019 = registros × 1,010, originais × 1,390", "a20_finn15_correction.py", "finn15_2019_correction.csv"),
        ("Continuations 27.0–32.4%, 2002–2020; Teixeira = all records", "Continuações 27,0–32,4%, 2002 a 2020; Teixeira = todos os registros", "a20_finn15_correction.py", "finn15_2002_2020_correction.csv"),
        ("Figure 2", "Figura 2", "figures_est_en.py", "Fig02_annual_series_4p_en.png"),
        ("Figures 3 and 4", "Figuras 3 e 4", "fig_v71.py", "Fig08_…, Fig09_…_nn_en.png"),
        ("TOC graphic", "Resumo gráfico (TOC)", "figures_est_v72.py", "TOC_graphic_est_v72.png"),
    ]
    tbl = ('<table class="t"><tr><th>' + ("Published value" if E else "Valor publicado") + "</th><th>Script (python/analysis/)</th><th>"
           + ("Output (results/tables/)" if E else "Saída (results/tables/)") + "</th></tr>"
           + "".join(f"<tr><td>{a if E else b}</td><td><code>{c}</code></td><td><code>{d}</code></td></tr>" for a, b, c, d in rows) + "</table>")
    ch.append(dict(
        title="From a published number to the code" if E else "De um número publicado até o código", minutes=6,
        **{"for": "reviewers and co-authors" if E else "revisores e coautores"},
        tldr=("<p>Every value of the ES&amp;T manuscript has a script, an output file and a log line. The table below lists the "
              "main ones; <code>docs/results_map.md</code> lists the numbers of the earlier manuscript and of the report.</p>" if E else
              "<p>Cada valor do manuscrito da ES&amp;T tem um script, um arquivo de saída e uma linha de log. A tabela abaixo lista os "
              "principais; <code>docs/results_map.md</code> lista os números do manuscrito anterior e do relatório.</p>"),
        learn=(["locate the source of a number in under a minute"] if E else ["localizar a origem de um número em menos de um minuto"]),
        body=(tbl
              + B("do", L(lang, "do") + (": example, the 3.55 Mt of CO<sub>2</sub> in 2025" if E else ": exemplo, os 3,55 Mt de CO<sub>2</sub> de 2025"),
                  "<pre>python -c \"import pandas as pd; t = pd.read_csv('results/tables/table2_state_emissions_2012_2025.csv'); "
                  "print(t.loc[t.year == 2025, 'CO2'])\"\n<span class=\"c\"># 13    3.554771e+06   (tonnes)</span></pre>")
              + B("key", L(lang, "key"),
                  "<p>The tests in <code>tests/</code> assert these values. If a change in the code alters a published number, a "
                  "test fails and names it.</p>" if E else
                  "<p>Os testes em <code>tests/</code> afirmam esses valores. Se uma mudança no código alterar um número publicado, um "
                  "teste falha e indica qual.</p>")),
        quiz=[(("Where is the CO<sub>2</sub> of 2025?" if E else "Onde está o CO<sub>2</sub> de 2025?"),
               ("<code>results/tables/table2_state_emissions_2012_2025.csv</code>, written by a02.")) ]))

    # 9 ---------------------------------------------------------------- statistics
    ch.append(dict(
        title="The statistics, explained" if E else "A estatística, explicada", minutes=12,
        **{"for": "scientists and students" if E else "cientistas e estudantes"},
        tldr=("<p>Rank-based tests (Mann–Kendall, Sen, Spearman) for short, skewed series; Holm correction for multiple tests; "
              "spatial models when neighbouring municipalities are alike; bootstrap by spatial blocks for recurrence; kernel "
              "density with several bandwidths.</p>" if E else
              "<p>Testes baseados em postos (Mann–Kendall, Sen, Spearman) para séries curtas e assimétricas; correção de Holm para "
              "testes múltiplos; modelos espaciais quando municípios vizinhos se parecem; bootstrap por blocos espaciais para a "
              "recorrência; densidade kernel com várias larguras de banda.</p>"),
        learn=(["say what each test answers", "read a p value with care"] if E else ["dizer o que cada teste responde", "ler um valor de p com cuidado"]),
        body=('<table class="t"><tr><th>' + ("Method" if E else "Método") + "</th><th>" + ("Question it answers" if E else "Pergunta que responde")
              + "</th><th>" + ("Where" if E else "Onde") + "</th></tr>"
              + "".join(f"<tr><td>{a}</td><td>{b}</td><td><code>{c}</code></td></tr>" for a, b, c in (
                  ([("Mann–Kendall test and Sen slope (Mann, 1945; Kendall, 1975; Sen, 1968)", "Is there a monotonic trend over the years, and how steep?", "a02, a15"),
                    ("Hamed–Rao correction (Hamed and Rao, 1998)", "Does autocorrelation between years change the trend test?", "a02"),
                    ("Spearman correlation with Holm correction (Holm, 1979)", "Do events follow fire-season climate, testing several variables at once?", "a06"),
                    ("Moran's I and spatial error model (Moran, 1950; Arraiz et al., 2010)", "Is land cover associated with event density once neighbours are accounted for?", "a07, a13"),
                    ("Selection ratio with spatial block bootstrap", "Does fire fall on a land-cover class more than its area would suggest?", "a13, a14"),
                    ("Kernel density (Diggle, 1985; Cronie and van Lieshout, 2018; Baddeley et al., 2015)", "Where are events concentrated in 2025?", "kde_events.R")]) if E else
                  [("Teste de Mann–Kendall e inclinação de Sen (Mann, 1945; Kendall, 1975; Sen, 1968)", "Há tendência monotônica ao longo dos anos, e com que inclinação?", "a02, a15"),
                   ("Correção de Hamed–Rao (Hamed e Rao, 1998)", "A autocorrelação entre anos altera o teste de tendência?", "a02"),
                   ("Correlação de Spearman com correção de Holm (Holm, 1979)", "Os eventos acompanham o clima da estação de queimadas, testando várias variáveis?", "a06"),
                   ("I de Moran e modelo de erro espacial (Moran, 1950; Arraiz et al., 2010)", "A cobertura do solo se associa à densidade de eventos, considerando os vizinhos?", "a07, a13"),
                   ("Razão de seleção com bootstrap por blocos espaciais", "O fogo cai numa classe de cobertura mais do que sua área indicaria?", "a13, a14"),
                   ("Densidade kernel (Diggle, 1985; Cronie e van Lieshout, 2018; Baddeley et al., 2015)", "Onde os eventos de 2025 se concentram?", "kde_events.R")])) + "</table>"
              + B("key", L(lang, "key"),
                  "<p>With 14 years, a trend test has little power: “no significant trend” means the data cannot distinguish a "
                  "trend from year-to-year noise, and the article reports it in these terms.</p>" if E else
                  "<p>Com 14 anos, um teste de tendência tem pouco poder: “sem tendência significativa” quer dizer que os dados não "
                  "distinguem uma tendência da variação entre anos, e o artigo relata o resultado nesses termos.</p>")
              + B("warn", L(lang, "warn"),
                  "<p>Ratios of two counts that share a term can correlate by construction (Kronmal, 1993). For this reason the "
                  "VIIRS increment is analysed as a difference and against independent measures (<code>a15</code>).</p>" if E else
                  "<p>Razões entre duas contagens que compartilham um termo podem se correlacionar por construção (Kronmal, 1993). Por "
                  "isso o incremento do VIIRS é analisado como diferença e contra medidas independentes (<code>a15</code>).</p>")
              + B("deep", L(lang, "deep"),
                  "<p>Kernel density bandwidth: the main map uses σ = 2.8 km; the Cronie–van Lieshout criterion gives 8.8 km and "
                  "Scott's rule 21.7 km. The concentration in the Serrana holds across these bandwidths "
                  "(<code>kde_2025_bandwidths.csv</code>, <code>kde_2025_sensitivity_mesoregion.csv</code>).</p>" if E else
                  "<p>Largura de banda da densidade kernel: o mapa principal usa σ = 2,8 km; o critério de Cronie–van Lieshout dá 8,8 km e "
                  "a regra de Scott, 21,7 km. A concentração na Serrana se mantém com essas larguras "
                  "(<code>kde_2025_bandwidths.csv</code>, <code>kde_2025_sensitivity_mesoregion.csv</code>).</p>")),
        quiz=[(("Why use Spearman instead of Pearson?" if E else "Por que usar Spearman e não Pearson?"),
               ("Fire counts are skewed and the sample is short; ranks are robust to extreme years." if E else
                "As contagens de fogo são assimétricas e a amostra é curta; os postos resistem a anos extremos."))]))

    # 10 --------------------------------------------------------------- versions and other inventories
    ch.append(dict(
        title="FINN v1.5, v2.5 and the other inventories" if E else "FINN v1.5, v2.5 e os outros inventários", minutes=10,
        **{"for": "inventory makers and modellers" if E else "quem faz inventários e modelagem"},
        tldr=("<p>For the same 2020 detections, FINN v1.5 gives 2.82 times the FINN v2.5 CO<sub>2</sub>. The earlier state "
              "inventory, BRAIN and Teixeira et al. (2025) used FINN v1.5 with its next-day continuations; removing them lowers "
              "their totals by 27.0% to 32.4% per year.</p>" if E else
              "<p>Para as mesmas detecções de 2020, o FINN v1.5 dá 2,82 vezes o CO<sub>2</sub> do FINN v2.5. O inventário estadual "
              "anterior, o BRAIN e Teixeira et al. (2025) usaram o FINN v1.5 com suas continuações no dia seguinte; removê-las reduz "
              "seus totais em 27,0% a 32,4% por ano.</p>"),
        learn=(["decompose the difference between versions", "compare an external inventory fairly"] if E else
               ["decompor a diferença entre versões", "comparar um inventário externo de forma justa"]),
        body=(svg_decomp(lang)
              + ("<p>The four factors multiply to the total ratio: the continuations (1/0.730), almost the same number of detections "
                 "(0.990), 16% more area per detection (1.159) and 58% less CO<sub>2</sub> per km² (0.423), mostly because forest "
                 "detections moved from the tropical to the temperate class. A shift-share split puts 75% of the change within "
                 "vegetation classes and 25% in the partition between them (<code>a17_v72_review.py</code>).</p>" if E else
                 "<p>Os quatro fatores se multiplicam até a razão total: as continuações (1/0,730), quase o mesmo número de detecções "
                 "(0,990), 16% mais área por detecção (1,159) e 58% menos CO<sub>2</sub> por km² (0,423), sobretudo porque detecções em "
                 "floresta passaram da classe tropical para a temperada. Uma decomposição estrutural atribui 75% da mudança ao "
                 "interior das classes de vegetação e 25% à partição entre elas (<code>a17_v72_review.py</code>).</p>")
              + '<table class="t"><tr><th>' + ("Study (FINN v1.5)" if E else "Estudo (FINN v1.5)") + "</th><th>"
              + ("What it equals" if E else "A que equivale") + "</th><th>" + ("Without continuations" if E else "Sem continuações") + "</th></tr>"
              + ("<tr><td>LCQAR (2022), SC 2020</td><td>all 4,609 records × 1.002 (its 4,625 “focos” are records)</td><td>1.37 × the 2,716 original detections</td></tr>"
                 "<tr><td>BRAIN 2019 (Hoinaski et al., 2024)</td><td>all records × 1.010</td><td>× 1.390</td></tr>"
                 "<tr><td>BRAIN 2020</td><td>31% of its CO on cell-days without an original detection</td><td>continuations included</td></tr>"
                 "<tr><td>Teixeira et al. (2025), 2002–2017</td><td>sum of all records in 15 of 16 years (2016: 0.36% below)</td><td>27.0–32.4% of yearly CO<sub>2</sub> are continuations</td></tr>" if E else
                 "<tr><td>LCQAR (2022), SC 2020</td><td>todos os 4.609 registros × 1,002 (seus 4.625 “focos” são registros)</td><td>1,37 × as 2.716 detecções originais</td></tr>"
                 "<tr><td>BRAIN 2019 (Hoinaski et al., 2024)</td><td>todos os registros × 1,010</td><td>× 1,390</td></tr>"
                 "<tr><td>BRAIN 2020</td><td>31% do seu CO em células-dia sem detecção original</td><td>inclui as continuações</td></tr>"
                 "<tr><td>Teixeira et al. (2025), 2002 a 2017</td><td>soma de todos os registros em 15 de 16 anos (2016: 0,36% abaixo)</td><td>27,0–32,4% do CO<sub>2</sub> anual são continuações</td></tr>")
              + "</table>"
              + B("deep", L(lang, "deep") + (": rebuilding the FINN v1.5 records" if E else ": refazer os registros do FINN v1.5"),
                  "<p>The FINN v1.5 records of 2002, 2016 and 2017 come from the NCAR annual files. "
                  "<code>tools/download_finn15_years.R</code> downloads and checks them; <code>tools/finn15_raw_to_grid.py</code> "
                  "cuts each file to the State's box and converts it to tonnes; <code>tools/finn15_records.py</code> assigns the "
                  "records to municipalities. On the 2015 file, this route reproduced all 3,537 rows of the earlier processing.</p>"
                  "<pre>Rscript tools/download_finn15_years.R\npython tools/finn15_raw_to_grid.py FINNv1.5_2016.GEOSCHEM.tar.gz 2016 data/raw_finn/finn15\n"
                  "python tools/finn15_records.py &lt;authors_folder&gt; data/raw_finn/finn15</pre>" if E else
                  "<p>Os registros do FINN v1.5 de 2002, 2016 e 2017 vêm dos arquivos anuais do NCAR. "
                  "<code>tools/download_finn15_years.R</code> baixa e confere esses arquivos; <code>tools/finn15_raw_to_grid.py</code> "
                  "recorta cada arquivo na caixa do Estado e converte para toneladas; <code>tools/finn15_records.py</code> atribui os "
                  "registros aos municípios. No arquivo de 2015, essa rota reproduziu todas as 3.537 linhas do processamento anterior.</p>"
                  "<pre>Rscript tools/download_finn15_years.R\npython tools/finn15_raw_to_grid.py FINNv1.5_2016.GEOSCHEM.tar.gz 2016 data/raw_finn/finn15\n"
                  "python tools/finn15_records.py &lt;pasta_dos_autores&gt; data/raw_finn/finn15</pre>")
              + B("warn", L(lang, "warn"),
                  "<p>Compare FINN versions in the text, with their configurations stated. Plotting FINN v1.5 and v2.5 totals on the "
                  "same axis invites a direct comparison that the different conventions do not support.</p>" if E else
                  "<p>Compare as versões do FINN no texto, com suas configurações explícitas. Colocar os totais do FINN v1.5 e do v2.5 no "
                  "mesmo eixo convida a uma comparação direta que as convenções diferentes não sustentam.</p>")),
        quiz=[(("What share of FINN v1.5 CO<sub>2</sub> comes from assumed next-day fires?" if E else
                "Que parcela do CO<sub>2</sub> do FINN v1.5 vem de focos presumidos no dia seguinte?"),
               ("27.0% to 32.4% per year in Santa Catarina, 2002–2020 (median 28.7%)." if E else
                "27,0% a 32,4% por ano em Santa Catarina, 2002 a 2020 (mediana 28,7%)."))]))

    # 11 --------------------------------------------------------------- route A
    ch.append(dict(
        title="Route A: the inventory of your region" if E else "Rota A: o inventário da sua região", minutes=8,
        **{"for": "users in other regions" if E else "usuários de outras regiões"},
        tldr=("<p>Put your boundaries in <code>data/inputs/</code>, edit <code>config/config.yml</code>, run steps 00 to 05. "
              "Start with one year: the global FINN files are large.</p>" if E else
              "<p>Coloque seus limites em <code>data/inputs/</code>, edite o <code>config/config.yml</code> e rode as etapas 00 a 05. "
              "Comece com um ano: os arquivos globais do FINN são grandes.</p>"),
        learn=(["configure a new region", "run route A step by step"] if E else ["configurar uma nova região", "rodar a rota A passo a passo"]),
        body=(B("do", L(lang, "do"),
                "<ol><li>" + ("Copy the region's shapefile to <code>data/inputs/</code>." if E else "Copie o shapefile da região para <code>data/inputs/</code>.")
                + "</li><li>" + ("In <code>config/config.yml</code>, set <code>region.boundaries_shp</code>, <code>region.region_field</code> "
                                 "and <code>region.name</code>, and choose years, version and sensor in <code>selection</code>." if E else
                                 "No <code>config/config.yml</code>, defina <code>region.boundaries_shp</code>, <code>region.region_field</code> e "
                                 "<code>region.name</code>, e escolha anos, versão e sensor em <code>selection</code>.")
                + "</li><li>" + ("Run:" if E else "Execute:") + "</li></ol>"
                "<pre>make all-py            <span class=\"c\"># or ./run_all.sh python, or run_all.bat python</span>\n"
                "python python/00_download_finn.py\npython python/01_convert_units.py\npython python/02_clip_region.py\n"
                "python python/04_aggregate_region.py\npython python/05_descriptive_analysis.py</pre>"
                + ("<p>Open <code>data/output/aggregated_emissions_all.shp</code> in QGIS or read the CSV of the same name.</p>" if E else
                   "<p>Abra <code>data/output/aggregated_emissions_all.shp</code> no QGIS ou leia o CSV de mesmo nome.</p>"))
              + B("check", L(lang, "check"),
                  "<p><code>tests/test_route_a.py</code> replicates the 2,341 records of 1 January to 28 May 2025 in Santa Catarina "
                  "from the NCAR files, so route A is tested against route B.</p>" if E else
                  "<p><code>tests/test_route_a.py</code> replica os 2.341 registros de 1º de janeiro a 28 de maio de 2025 em Santa "
                  "Catarina a partir dos arquivos do NCAR, de modo que a rota A é testada contra a rota B.</p>")
              + B("warn", L(lang, "warn"),
                  "<p>Outside 23.5° S to 23.5° N, FINN v2.5 classes forests as temperate (chapter 4). Report this choice, and the "
                  "detection source, whenever you publish totals for another region.</p>" if E else
                  "<p>Fora da faixa de 23,5° S a 23,5° N, o FINN v2.5 classifica as florestas como temperadas (capítulo 4). Informe essa "
                  "escolha, e a fonte de detecção, sempre que publicar totais de outra região.</p>")),
        quiz=[(("Which file holds every parameter?" if E else "Qual arquivo guarda todos os parâmetros?"), ("<code>config/config.yml</code>."))]))

    # 12 --------------------------------------------------------------- Colab and Earth Engine
    ch.append(dict(
        title="Google Colab and Earth Engine" if E else "Google Colab e Earth Engine", minutes=6,
        **{"for": "users without a local Python" if E else "quem não tem Python local"},
        tldr=("<p>Route B runs in Colab as on any computer. The external datasets (MapBiomas, MCD64A1, ERA5-Land) come from the "
              "Earth Engine notebooks in <code>gee/</code>, which need a registered Google Cloud project.</p>" if E else
              "<p>A rota B roda no Colab como em qualquer computador. Os dados externos (MapBiomas, MCD64A1, ERA5-Land) vêm dos "
              "notebooks do Earth Engine em <code>gee/</code>, que precisam de um projeto registrado no Google Cloud.</p>"),
        learn=(["run route B in Colab", "run an Earth Engine notebook"] if E else ["rodar a rota B no Colab", "rodar um notebook do Earth Engine"]),
        body=(B("do", L(lang, "do"),
                "<ol><li>" + ("Register a Google Cloud project for Earth Engine at https://console.cloud.google.com/earth-engine "
                              "(noncommercial use needs no billing) and note its ID." if E else
                              "Registre um projeto do Google Cloud para o Earth Engine em https://console.cloud.google.com/earth-engine "
                              "(uso não comercial dispensa faturamento) e anote o ID.")
                + "</li><li>" + ("In Colab, clone the repository into <code>/content/FINN_SC</code> and run route B with <code>--no-r</code>." if E else
                                 "No Colab, clone o repositório em <code>/content/FINN_SC</code> e rode a rota B com <code>--no-r</code>.")
                + "</li><li>" + ("In each notebook of <code>gee/</code>, set <code>PROJECT = \"&lt;your project ID&gt;\"</code> in cell 2 "
                                 "and run all; cell 3 calls <code>ee.Authenticate()</code> and <code>ee.Initialize(project=PROJECT)</code>." if E else
                                 "Em cada notebook de <code>gee/</code>, defina <code>PROJECT = \"&lt;ID do seu projeto&gt;\"</code> na célula 2 e "
                                 "rode tudo; a célula 3 chama <code>ee.Authenticate()</code> e <code>ee.Initialize(project=PROJECT)</code>.")
                + "</li></ol><pre>!git clone https://github.com/jessicajcss/FINN_SC.git /content/FINN_SC\n%cd /content/FINN_SC\n"
                  "!pip install -q -r requirements.txt\n!python python/run_analysis.py --no-r\n!python -m pytest -q tests</pre>")
              + B("key", L(lang, "key"),
                  "<p>The notebooks ending in <code>_run_2026-10-21.ipynb</code> keep the outputs of the runs used in the article, "
                  "so you can compare yours cell by cell.</p>" if E else
                  "<p>Os notebooks terminados em <code>_run_2026-10-21.ipynb</code> guardam as saídas das execuções usadas no artigo, "
                  "para você comparar as suas célula a célula.</p>")),
        quiz=[(("Where do you set the Earth Engine project?" if E else "Onde se define o projeto do Earth Engine?"),
               ("In cell 2 of each notebook, variable <code>PROJECT</code>." if E else "Na célula 2 de cada notebook, variável <code>PROJECT</code>."))]))

    # 13 --------------------------------------------------------------- troubleshooting
    probs = ([("<code>ModuleNotFoundError</code>", "Activate the environment (<code>conda activate finn</code>) or install <code>requirements.txt</code>."),
              ("“file not found” for <code>results/</code> or <code>data/</code>", "Run from the repository root."),
              ("A test fails after you changed code", "Read the test name: it says which published number changed."),
              ("<code>verify_manifest.py</code> reports DIFFERENT", "Install the pinned versions of <code>requirements-lock.txt</code> and run again; the script shows the largest differences."),
              ("FINN download returns 404", "Check the address in <code>R/utils_finn.R</code>; FINN v1.5 files are <code>.tar.gz</code> for every year."),
              ("Earth Engine asks for a project", "Register one (chapter 12) and set <code>PROJECT</code>."),
              ("R step is slow", "Use <code>--no-r</code>; the annual kernel sensitivity takes about 40 minutes.")] if E else
             [("<code>ModuleNotFoundError</code>", "Ative o ambiente (<code>conda activate finn</code>) ou instale o <code>requirements.txt</code>."),
              ("“arquivo não encontrado” em <code>results/</code> ou <code>data/</code>", "Execute a partir da raiz do repositório."),
              ("Um teste falha depois de mudar o código", "Leia o nome do teste: ele diz qual número publicado mudou."),
              ("<code>verify_manifest.py</code> acusa DIFFERENT", "Instale as versões fixadas em <code>requirements-lock.txt</code> e rode de novo; o script mostra as maiores diferenças."),
              ("O download do FINN retorna 404", "Confira o endereço em <code>R/utils_finn.R</code>; os arquivos do FINN v1.5 são <code>.tar.gz</code> em todos os anos."),
              ("O Earth Engine pede um projeto", "Registre um (capítulo 12) e defina <code>PROJECT</code>."),
              ("A etapa em R é lenta", "Use <code>--no-r</code>; a sensibilidade anual da densidade kernel leva cerca de 40 minutos.")])
    ch.append(dict(
        title="When something goes wrong" if E else "Quando algo dá errado", minutes=4, **{"for": "everyone" if E else "todos"},
        tldr=("<p>Most problems are the environment, the working folder or a download address. The table gives the fix.</p>" if E else
              "<p>A maioria dos problemas está no ambiente, na pasta de trabalho ou num endereço de download. A tabela traz a solução.</p>"),
        learn=None,
        body=('<table class="t"><tr><th>' + ("Symptom" if E else "Sintoma") + "</th><th>" + ("Fix" if E else "Solução") + "</th></tr>"
              + "".join(f"<tr><td>{a}</td><td>{b}</td></tr>" for a, b in probs) + "</table>"),
        quiz=None))

    # 14 --------------------------------------------------------------- glossary + references + checklist
    gl = ([("Active fire", "heat detected by a satellite pixel at the time of the pass"),
           ("BRAIN", "Brazilian Atmospheric Inventories, a database of emissions for air-quality modelling (Hoinaski et al., 2024)"),
           ("Continuation (next-day)", "the half-size copy of a FINN v1.5 record added on the following day"),
           ("Detection", "one satellite pixel on one day (day + FIREID)"),
           ("Fire event", "a FINN daily burned-area polygon (day + POLYID)"),
           ("GENVEG", "the generic vegetation type of a FINN record"),
           ("Mesoregion", "IBGE grouping of municipalities; Santa Catarina has six"),
           ("NRT", "near-real-time files, produced daily"),
           ("Record", "one row of a FINN file"),
           ("Route A / Route B", "replication from NCAR files / reproduction from the archived records")] if E else
          [("Foco ativo", "calor detectado por um pixel de satélite no momento da passagem"),
           ("BRAIN", "Brazilian Atmospheric Inventories, base de emissões para modelagem da qualidade do ar (Hoinaski et al., 2024)"),
           ("Continuação (no dia seguinte)", "a cópia com metade do tamanho de um registro do FINN v1.5 acrescentada no dia seguinte"),
           ("Detecção", "um pixel de satélite em um dia (dia + FIREID)"),
           ("Evento de queimada", "um polígono diário de área queimada do FINN (dia + POLYID)"),
           ("GENVEG", "o tipo genérico de vegetação de um registro do FINN"),
           ("Mesorregião", "agrupamento de municípios do IBGE; Santa Catarina tem seis"),
           ("NRT", "arquivos em tempo quase real, produzidos diariamente"),
           ("Registro", "uma linha de um arquivo do FINN"),
           ("Rota A / Rota B", "replicação a partir dos arquivos do NCAR / reprodução a partir dos registros arquivados")])
    refs = [
        "Arraiz, I., Drukker, D. M., Kelejian, H. H. and Prucha, I. R. (2010). A spatial Cliff-Ord-type model with heteroskedastic innovations. <i>Journal of Regional Science</i>, 50(2), 592–614.",
        "Baddeley, A., Rubak, E. and Turner, R. (2015). <i>Spatial Point Patterns: Methodology and Applications with R</i>. Chapman and Hall/CRC. doi:10.1201/b19708",
        "Cronie, O. and van Lieshout, M. N. M. (2018). A non-model-based approach to bandwidth selection for kernel estimators of spatial intensity functions. <i>Biometrika</i>, 105(2), 455–462. doi:10.1093/biomet/asy001",
        "Diggle, P. (1985). A kernel method for smoothing point process data. <i>Applied Statistics</i>, 34(2), 138–147. doi:10.2307/2347366",
        "Giglio, L., Schroeder, W. and Justice, C. O. (2016). The collection 6 MODIS active fire detection algorithm and fire products. <i>Remote Sensing of Environment</i>, 178, 31–41. doi:10.1016/j.rse.2016.02.054",
        "Giglio, L., Schroeder, W., Hall, J. V. and Justice, C. O. (2021). MODIS Collection 6 and Collection 6.1 Active Fire Product User's Guide, version 1.0.",
        "Hamed, K. H. and Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. <i>Journal of Hydrology</i>, 204, 182–196. doi:10.1016/S0022-1694(97)00125-X",
        "Hoinaski, L., Will, R. and Ribeiro, C. B. (2024). Brazilian Atmospheric Inventories – BRAIN. <i>Earth System Science Data</i>, 16(5), 2385–2405. doi:10.5194/essd-16-2385-2024",
        "Holm, S. (1979). A simple sequentially rejective multiple test procedure. <i>Scandinavian Journal of Statistics</i>, 6(2), 65–70.",
        "Kendall, M. G. (1975). <i>Rank Correlation Methods</i>, 4th ed. Griffin, London.",
        "Kronmal, R. A. (1993). Spurious correlation and the fallacy of the ratio standard revisited. <i>Journal of the Royal Statistical Society A</i>, 156(3), 379–392. doi:10.2307/2983064",
        "LCQAR (2022). Avaliação do impacto das emissões veiculares, queimadas, industriais e naturais na qualidade do ar em Santa Catarina, ano-base 2021. Laboratório de Controle de Qualidade do Ar (LCQAR).",
        "Mann, H. B. (1945). Nonparametric tests against trend. <i>Econometrica</i>, 13(3), 245–259. doi:10.2307/1907187",
        "Moran, P. A. P. (1950). Notes on continuous stochastic phenomena. <i>Biometrika</i>, 37(1–2), 17–23. doi:10.1093/biomet/37.1-2.17",
        "Schroeder, W., Oliva, P., et al. (2014). The New VIIRS 375 m active fire detection data product. <i>Remote Sensing of Environment</i>, 143, 85–96. doi:10.1016/j.rse.2013.12.008",
        "Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. <i>Journal of the American Statistical Association</i>, 63(324), 1379–1389. doi:10.1080/01621459.1968.10480934",
        "Teixeira, N. C., Chaffe, P. L. B., Chagas, V. B. P., Ribeiro, C. B., Rodrigues, R. R. and Hoinaski, L. (2025). Recent fire occurrence and associated emissions in Southern Brazil. <i>Air Quality, Atmosphere &amp; Health</i>, 18(4), 953–970.",
        "Wiedinmyer, C., Akagi, S. K., Yokelson, R. J., Emmons, L. K., Al-Saadi, J. A., Orlando, J. J. and Soja, A. J. (2011). The Fire INventory from NCAR (FINN). <i>Geoscientific Model Development</i>, 4, 625–641. doi:10.5194/gmd-4-625-2011",
        "Wiedinmyer, C. and Emmons, L. (2022). Fire Inventory from NCAR version 2 Fire Emission [dataset]. NSF NCAR Research Data Archive. doi:10.5065/XNPA-AF09",
        "Wiedinmyer, C. et al. (2023). The Fire Inventory from NCAR version 2.5. <i>Geoscientific Model Development</i>, 16(13), 3873–3891. doi:10.5194/gmd-16-3873-2023",
    ]
    checklist = (["Environment installed and activated", "<code>run_analysis.py</code> finished without error",
                  "Tests: 96 passed", "Manifest: 107 files, OK 107",
                  "FINN data cited (models and dataset DOI)", "Configuration of FINN (version, sensor, forest class) stated with any total"] if E else
                 ["Ambiente instalado e ativado", "<code>run_analysis.py</code> terminou sem erro", "Testes: 96 passed",
                  "Manifesto: 107 files, OK 107", "Dados do FINN citados (modelos e DOI do conjunto)",
                  "Configuração do FINN (versão, sensor, classe florestal) informada junto com qualquer total"])
    ch.append(dict(
        title="Glossary, references and final checklist" if E else "Glossário, referências e lista final", minutes=5,
        **{"for": "everyone" if E else "todos"},
        tldr=("<p>Terms in one line each, the sources cited in this tutorial and a six-item checklist before you report results.</p>" if E else
              "<p>Termos em uma linha cada, as fontes citadas neste tutorial e uma lista de seis itens antes de relatar resultados.</p>"),
        learn=None,
        body=(("<h2>Glossary</h2>" if E else "<h2>Glossário</h2>") + '<table class="t">'
              + "".join(f"<tr><td style='width:30%'><b>{a}</b></td><td>{b}</td></tr>" for a, b in gl) + "</table>"
              + B("check", L(lang, "check") + (": before you report" if E else ": antes de relatar"),
                  '<ul class="learn">' + "".join(f"<li>{x}</li>" for x in checklist) + "</ul>")
              + ("<h2>References</h2>" if E else "<h2>Referências</h2>") + "".join(f'<div class="ref">{r}</div>' for r in refs)),
        quiz=None))
    return ch

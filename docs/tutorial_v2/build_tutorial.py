# -*- coding: utf-8 -*-
"""build_tutorial.py - FINN_SC illustrated tutorial, English and Brazilian Portuguese (version of 11 Nov 2026).

Writes docs/tutorial_v2/tutorial_en.html and tutorial_pt.html from content.py and renders them to the repository root
as TUTORIAL_FINN_SC_en.pdf and TUTORIAL_FINN_SC_pt.pdf with WeasyPrint (pip install weasyprint; needs Pango).
Figures are read from results/figures/ (written by the analysis scripts), so the tutorial shows the published figures.
Usage (from the repository root or from this folder):  python docs/tutorial_v2/build_tutorial.py [--html-only]
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import content as C

CSS = r"""
@page { size: A4; margin: 17mm 16mm 19mm 16mm;
  @bottom-left { content: string(chap); font-family: 'DejaVu Sans', sans-serif; font-size: 7.5pt; color: #7a8599; }
  @bottom-right { content: counter(page) " / " counter(pages); font-family: 'DejaVu Sans', sans-serif; font-size: 7.5pt; color: #7a8599; } }
@page cover { margin: 0; @bottom-left { content: none; } @bottom-right { content: none; } }
html { font-family: 'DejaVu Sans', 'Liberation Sans', sans-serif; font-size: 9.6pt; line-height: 1.55; color: #1f2733; }
body { margin: 0; }
p { margin: 0 0 7pt 0; text-align: left; hyphens: manual; }
b, strong { color: #0f1a2b; }
a { color: #1d5fa8; text-decoration: none; }
code, .mono { font-family: 'DejaVu Sans Mono', monospace; font-size: 8.3pt; background: #eef2f7; padding: 0 2pt; border-radius: 2pt; }
pre { font-family: 'DejaVu Sans Mono', monospace; font-size: 8pt; line-height: 1.45; background: #f3f6fa; border-left: 3pt solid #2e8b57;
  padding: 6pt 8pt; margin: 4pt 0 8pt 0; white-space: pre-wrap; break-inside: avoid; }
pre .c { color: #6b7686; }
h1.chap { break-before: page; font-size: 19pt; line-height: 1.2; margin: 0 0 4pt 0; color: #0f1a2b; }
h1.chap .ttl { string-set: chap content(text); }
h1.chap .num { display: inline-block; width: 26pt; height: 26pt; line-height: 26pt; text-align: center; border-radius: 13pt;
  color: white; font-size: 13pt; margin-right: 7pt; vertical-align: 2pt; }
h2 { font-size: 12.5pt; margin: 12pt 0 4pt 0; color: #0f1a2b; break-after: avoid; }
h2 .tag { font-size: 7.5pt; color: white; background: #7a8599; padding: 1pt 5pt; border-radius: 6pt; margin-left: 5pt; vertical-align: 2pt; font-weight: normal; }
h3 { font-size: 10.5pt; margin: 9pt 0 3pt 0; break-after: avoid; }
.meta { font-size: 8pt; color: #5b6676; margin-bottom: 7pt; }
.progress { margin: 0 0 8pt 0; }
.progress span { display: inline-block; width: 15pt; height: 5pt; border-radius: 3pt; background: #dfe5ee; margin-right: 2.5pt; }
.progress span.on { background: #1d5fa8; }
.progress span.now { background: #e07b00; }
.box { border-radius: 5pt; padding: 7pt 9pt 3pt 9pt; margin: 6pt 0 9pt 0; break-inside: avoid; border-left: 4pt solid; }
.box .lab { font-weight: bold; font-size: 8pt; letter-spacing: 0.4pt; text-transform: uppercase; margin-bottom: 3pt; }
.box .lab svg { width: 10pt; height: 10pt; vertical-align: -1.5pt; margin-right: 3pt; }
.tldr { background: #fff4e5; border-color: #e07b00; } .tldr .lab { color: #a45700; }
.key  { background: #e8f1fb; border-color: #1d5fa8; } .key .lab { color: #1d5fa8; }
.warn { background: #fff8db; border-color: #c99a00; } .warn .lab { color: #8a6a00; }
.do   { background: #e9f6ee; border-color: #2e8b57; } .do .lab { color: #22704a; }
.check{ background: #f1ecfa; border-color: #6b4fbb; } .check .lab { color: #563ea1; }
.deep { background: #f2f4f7; border-color: #7a8599; } .deep .lab { color: #4d5868; }
.learn { margin: 0 0 8pt 0; padding: 0; list-style: none; }
.learn li { margin: 0 0 2pt 0; padding-left: 14pt; position: relative; }
.learn li:before { content: ""; position: absolute; left: 0; top: 3pt; width: 7pt; height: 7pt; border: 1.2pt solid #2e8b57; border-radius: 1.5pt; }
ul, ol { margin: 0 0 7pt 0; padding-left: 15pt; } li { margin-bottom: 2pt; }
table.t { width: 100%; border-collapse: collapse; margin: 4pt 0 9pt 0; font-size: 8.2pt; line-height: 1.35; break-inside: auto; }
table.t th { background: #1f3550; color: white; text-align: left; padding: 3.5pt 5pt; font-weight: bold; }
table.t td { padding: 3.5pt 5pt; border-bottom: 0.6pt solid #dfe5ee; vertical-align: top; }
table.t tr:nth-child(even) td { background: #f6f8fb; }
table.t tr { break-inside: avoid; }
figure { margin: 6pt 0 10pt 0; break-inside: avoid; text-align: center; }
figure img { max-width: 100%; max-height: 118mm; }
figure.diagram svg { width: 100%; height: auto; }
figcaption { font-size: 8pt; color: #4d5868; text-align: left; margin-top: 3pt; line-height: 1.4; }
.big { font-size: 22pt; font-weight: bold; color: #1d5fa8; line-height: 1.1; }
.kpis { width: 100%; border-collapse: separate; border-spacing: 5pt; margin: 2pt -5pt 6pt -5pt; }
.kpis td { background: #f3f6fa; border-radius: 5pt; padding: 7pt; vertical-align: top; width: 25%; font-size: 8pt; line-height: 1.35; }
.qa { counter-reset: q; margin: 0; padding-left: 0; list-style: none; }
.qa li { margin-bottom: 4pt; }
.qa .a { color: #4d5868; font-size: 8.3pt; }
.cover { page: cover; height: 297mm; position: relative; background: #0f2236; color: white; }
.cover .band { position: absolute; left: 0; right: 0; top: 0; height: 9mm; background: #e07b00; }
.cover .inner { position: absolute; left: 20mm; right: 20mm; top: 52mm; }
.cover h1 { font-size: 34pt; line-height: 1.08; margin: 0 0 8mm 0; color: white; }
.cover .sub { font-size: 14pt; line-height: 1.35; color: #cfe0f3; margin-bottom: 12mm; }
.cover .pill { display: inline-block; border: 1pt solid #8fb4dc; color: #cfe0f3; border-radius: 9pt; padding: 2pt 8pt; margin: 0 4pt 4pt 0; font-size: 8.5pt; }
.cover .foot { position: absolute; left: 20mm; right: 20mm; bottom: 20mm; font-size: 8.5pt; color: #9fb6cf; line-height: 1.5; }
.toc { list-style: none; padding: 0; margin: 4pt 0; }
.toc li { padding: 3pt 0; border-bottom: 0.5pt dotted #c4ccd8; }
.toc li a { color: #1f2733; }
.toc li a::after { content: target-counter(attr(href), page); float: right; color: #5b6676; }
.toc .n { display: inline-block; width: 16pt; height: 16pt; line-height: 16pt; border-radius: 8pt; color: white; text-align: center; font-size: 8pt; margin-right: 6pt; }
.legend td { vertical-align: top; }
.small { font-size: 8pt; color: #4d5868; }
.ref { font-size: 8pt; line-height: 1.4; margin-bottom: 4pt; padding-left: 12pt; text-indent: -12pt; }
"""

ICONS = {
    "tldr": '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4.5" fill="#e07b00"/><path d="M5 2.2v3.2l2 1.2" stroke="white" stroke-width="1.1" fill="none"/></svg>',
    "key": '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4.5" fill="#1d5fa8"/><rect x="4.4" y="4.2" width="1.2" height="3.6" fill="white"/><circle cx="5" cy="2.9" r="0.75" fill="white"/></svg>',
    "warn": '<svg viewBox="0 0 10 10"><path d="M5 0.6 9.6 9.2H0.4z" fill="#c99a00"/><rect x="4.45" y="3.4" width="1.1" height="3.2" fill="white"/><circle cx="5" cy="7.7" r="0.65" fill="white"/></svg>',
    "do": '<svg viewBox="0 0 10 10"><rect x="0.5" y="0.5" width="9" height="9" rx="2" fill="#2e8b57"/><path d="M2.3 3.4 4 5 2.3 6.6M4.9 6.8h2.8" stroke="white" stroke-width="1" fill="none"/></svg>',
    "check": '<svg viewBox="0 0 10 10"><circle cx="5" cy="5" r="4.5" fill="#6b4fbb"/><path d="M2.7 5.2 4.3 6.8 7.4 3.4" stroke="white" stroke-width="1.2" fill="none"/></svg>',
    "deep": '<svg viewBox="0 0 10 10"><rect x="1" y="1.2" width="8" height="7.6" rx="1" fill="#7a8599"/><path d="M5 1.6v6.8M2.2 3.4h2M2.2 5h2M5.8 3.4h2M5.8 5h2" stroke="white" stroke-width="0.7"/></svg>',
}
COLORS = ["#1d5fa8", "#2e8b57", "#e07b00", "#6b4fbb", "#c0392b", "#16809a", "#8a6a00", "#1f3550",
          "#2e8b57", "#1d5fa8", "#6b4fbb", "#e07b00", "#16809a", "#c0392b", "#1f3550"]


def box(kind, label, html):
    return f'<div class="box {kind}"><div class="lab">{ICONS[kind]}{label}</div>{html}</div>'


def build(lang):
    L = C.LABELS[lang]
    chapters = C.chapters(lang)
    n = len(chapters)
    out = [f'<!DOCTYPE html><html lang="{"pt-BR" if lang == "pt" else "en"}"><head><meta charset="utf-8">'
           f'<title>{L["title"]}</title><style>{CSS}</style></head><body>']
    out.append(C.cover(lang))
    # how-to-read + contents page
    toc = "".join(f'<li><a href="#ch{i}"><span class="n" style="background:{COLORS[i % len(COLORS)]}">{i}</span>'
                  f'{c["title"]}</a></li>' for i, c in enumerate(chapters, start=1))
    out.append(f'<h1 class="chap" id="toc"><span class="ttl">{L["contents"]}</span></h1><ul class="toc">{toc}</ul>')
    for i, c in enumerate(chapters, start=1):
        prog = "".join(f'<span class="{"now" if k == i else ("on" if k < i else "")}"></span>' for k in range(1, n + 1))
        out.append(f'<h1 class="chap" id="ch{i}"><span class="num" style="background:{COLORS[i % len(COLORS)]}">{i}</span>'
                   f'<span class="ttl">{c["title"]}</span></h1>')
        out.append(f'<div class="progress">{prog}</div>')
        out.append(f'<div class="meta">{L["chapter"]} {i} / {n} · {L["reading"]}: {c["minutes"]} min · {c["for"]}</div>')
        out.append(box("tldr", L["tldr"], c["tldr"]))
        if c.get("learn"):
            out.append(f'<p><b>{L["learn"]}</b></p><ul class="learn">' + "".join(f"<li>{x}</li>" for x in c["learn"]) + "</ul>")
        out.append(c["body"])
        if c.get("quiz"):
            qs = "".join(f'<li><b>{q}</b><br><span class="a">{a}</span></li>' for q, a in c["quiz"])
            out.append(box("check", L["quiz"], f'<ul class="qa">{qs}</ul>'))
    out.append("</body></html>")
    return "".join(out)


def main():
    html_only = "--html-only" in sys.argv
    for lang in ("en", "pt"):
        html = build(lang)
        fn = os.path.join(HERE, f"tutorial_{lang}.html")
        with open(fn, "w", encoding="utf-8") as f:
            f.write(html)
        print("written", os.path.relpath(fn, ROOT))
        if not html_only:
            from weasyprint import HTML
            pdf = os.path.join(ROOT, f"TUTORIAL_FINN_SC_{lang}.pdf")
            HTML(filename=fn, base_url=HERE).write_pdf(pdf)
            print("written", os.path.relpath(pdf, ROOT))


if __name__ == "__main__":
    main()

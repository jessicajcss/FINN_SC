"""a18_exports.py - exports of the municipalities and mesoregions of Santa Catarina in 2025 (Comex Stat).

Input: data/external/comexstat_SC_municipios_2025.xlsx, exported by the authors from Comex Stat (MDIC/SECEX,
http://comexstat.mdic.gov.br) on 2026-11-08: exports, Jan-Dec 2025, by municipality, month and HS4 heading,
US$ FOB and net kg ('Detalhamento' sheet of the file).
Comex Stat assigns each export to the municipality of the tax domicile of the exporting company, which is not always the
producer of the goods (SECEX, Panorama dos Municipios Brasileiros no Comercio Exterior). The municipal values below are
therefore descriptive and do not locate production.

Groups (HS chapter = first two digits of the HS4 heading):
  agri-food      HS chapters 01-24 (Harmonized System Sections I-IV: animal products, vegetable products, fats and oils,
                 prepared foodstuffs, beverages and tobacco)
  wood/pulp/paper HS chapters 44, 47, 48
Outputs (results/tables): exports_2025_by_mesoregion.csv, exports_2025_by_municipality.csv; log a18_exports.txt.
"""
import unicodedata

import pandas as pd
from _setup import ROOT, TAB, Log

L = Log("a18_exports")
EXT = ROOT / "data" / "external"


def norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return " ".join(s.replace("'", " ").replace("-", " ").split())


X = pd.read_excel(EXT / "comexstat_SC_municipios_2025.xlsx", sheet_name="Resultado")
X.columns = ["month", "uf", "mun", "hs4", "hs4_desc", "usd_fob", "kg"]
L("a18 exports 2025, Comex Stat, Santa Catarina")
L(f"   rows {len(X)}; UF values {sorted(X.uf.unique())}; municipalities {X.mun.nunique()}; months {X.month.nunique()}")
X["name"] = X.mun.str.replace(r"\s*-\s*SC$", "", regex=True)
att = pd.read_csv(EXT / "sc_municipios_2024_atributos.csv")
key = {norm(n): n for n in att.NM_MUN}
ALIAS = {"picarras": "Balneário Piçarras", "presidente castelo branco": "Presidente Castello Branco"}  # Comex Stat spellings
X["NM_MUN"] = X.name.map(lambda n: key.get(norm(n), ALIAS.get(norm(n))))
miss = sorted(X.loc[X.NM_MUN.isna(), "name"].unique())
L(f"   names without match in the IBGE 2024 municipal table: {miss}")
X["ch"] = X.hs4.astype(int) // 100
X["agri"] = X.ch.between(1, 24)
X["wood"] = X.ch.isin([44, 47, 48])

M = X.groupby("NM_MUN").agg(usd=("usd_fob", "sum")).join(
    X[X.agri].groupby("NM_MUN").usd_fob.sum().rename("usd_agri")).join(
    X[X.wood].groupby("NM_MUN").usd_fob.sum().rename("usd_wood")).fillna(0.0)
M = att.set_index("NM_MUN")[["CD_MUN", "mesorregiao", "AREA_KM2"]].join(M).fillna({"usd": 0, "usd_agri": 0, "usd_wood": 0})
tot = M.usd.sum()
L(f"   state total US$ {tot / 1e9:.3f} billion FOB; agri-food (HS 01-24) {100 * M.usd_agri.sum() / tot:.1f}%; "
  f"wood/pulp/paper (HS 44, 47, 48) {100 * M.usd_wood.sum() / tot:.1f}%; municipalities with exports {int((M.usd > 0).sum())} of {len(M)}")
top = X.groupby("ch").usd_fob.sum().sort_values(ascending=False).head(8)
L("   largest HS chapters in the state: " + "; ".join(f"{c:02d} {100 * v / tot:.1f}%" for c, v in top.items()))
M["pct_state"] = 100 * M.usd / tot
M["agri_pct"] = 100 * M.usd_agri / M.usd.where(M.usd > 0)
M["wood_pct"] = 100 * M.usd_wood / M.usd.where(M.usd > 0)
M.reset_index().to_csv(TAB / "exports_2025_by_municipality.csv", index=False)

G = M.groupby("mesorregiao")[["usd", "usd_agri", "usd_wood"]].sum()
G.loc["State"] = G.sum()
G["pct_state"] = 100 * G.usd / tot
G["agri_pct"] = 100 * G.usd_agri / G.usd
G["wood_pct"] = 100 * G.usd_wood / G.usd
G["pct_state_agri"] = 100 * G.usd_agri / G.loc["State", "usd_agri"]
G["usd_million"] = G.usd / 1e6
G.to_csv(TAB / "exports_2025_by_mesoregion.csv")
L("   by mesoregion: US$ million, % of state exports, agri-food % of own exports, wood/pulp/paper %, % of state agri-food")
for k, r in G.iterrows():
    L(f"     {k}: {r.usd_million:,.1f}; {r.pct_state:.1f}%; {r.agri_pct:.1f}%; {r.wood_pct:.1f}%; {r.pct_state_agri:.1f}%")

P = pd.read_csv(TAB / "municipal_profile_top2025.csv")
L("   municipalities of Table 4 (US$ million; % of state; agri-food %; wood/pulp/paper %; main HS chapters):")
for n in P.municipality:
    r = M.loc[n]
    sub = X[X.NM_MUN == n].groupby("ch").usd_fob.sum().sort_values(ascending=False)
    main = "; ".join(f"{c:02d} {100 * v / sub.sum():.0f}%" for c, v in sub.head(3).items()) if len(sub) else "none"
    L(f"     {n}: {r.usd / 1e6:,.2f}; {r.pct_state:.2f}%; "
      f"{r.agri_pct:.1f}%; {r.wood_pct:.1f}%; {main}")
S = M.loc[P.municipality]
L(f"   the {len(P)} municipalities together: US$ {S.usd.sum() / 1e6:,.1f} million, {100 * S.usd.sum() / tot:.2f}% of the state; "
  f"agri-food {100 * S.usd_agri.sum() / S.usd.sum():.1f}% and wood/pulp/paper {100 * S.usd_wood.sum() / S.usd.sum():.1f}% of their exports")
L.save()

#!/usr/bin/env python3
"""a04 - partition of FINN burned area and emissions by generic vegetation type (GENVEG).

MODIS+VIIRS records, 2012-2025 and the report year. Burned biomass per unit area implied by the
records = CO2 / (AREA x EF_CO2), with EF_CO2 from Wiedinmyer et al. (2023, Table 4); the FINN field
BMASS (kg m-2) gives the same value (logged as a check). GENVEG classes: Wiedinmyer et al. (2023), Table 1.
Outputs: results/tables/genveg_partition.csv; results/logs/a04_genveg_partition.txt
Manuscript (v3.2): sections 3 and 4, Table S9. Inventory report: section 4.
"""
from _setup import CFG, TAB, Log, load_records, screened_events
import pandas as pd

L = Log("a04_genveg_partition")
Y = CFG["analysis"]["report_year"]
EF_CO2 = {1: 1686, 2: 1681, 3: 1643, 4: 1510, 5: 1565, 6: 1623, 9: 1444}     # g/kg, Wiedinmyer et al. (2023) Table 4
NAME = {1: "Savana e campo", 2: "Savana arborizada", 3: "Floresta tropical", 4: "Floresta temperada",
        5: "Floresta boreal", 6: "Floresta temperada perene", 9: "Lavouras"}
d = load_records("MV")
rows = []
for lab, s in (("2012-2025", d), (str(Y), d[d.year == Y])):
    g = s.groupby("GENVEG")[["AREA", "CO2", "PM25"]].sum()
    bm = s.assign(B=s.AREA * s.BMASS).groupby("GENVEG").B.sum()
    sh = 100 * g / g.sum()
    for k in g.index:
        rows.append(dict(period=lab, GENVEG=int(k), classe=NAME[int(k)], area_km2=g.loc[k, "AREA"] / 1e6,
                         area_pct=sh.loc[k, "AREA"], CO2_pct=sh.loc[k, "CO2"], PM25_pct=sh.loc[k, "PM25"],
                         biomassa_kg_m2=g.loc[k, "CO2"] * 1e6 / EF_CO2[int(k)] / g.loc[k, "AREA"],
                         biomassa_BMASS_kg_m2=bm.loc[k] / g.loc[k, "AREA"]))
T = pd.DataFrame(rows)
T.to_csv(TAB / "genveg_partition.csv", index=False)
L(T.round(3).to_string(index=False))
E = screened_events()
E = E[(E.sensor == "MODIS+VIIRS") & (~E.flag)]
ng = d.groupby(["year", "DAY", "POLYID"]).GENVEG.nunique().rename("ng").reset_index()
E = E.merge(ng, on=["year", "DAY", "POLYID"], how="left")
L(f"screened events: {len(E)}")
L(f"events with >1 GENVEG (%): 2012-2025 {100 * (E.ng > 1).mean():.1f} | {Y} {100 * (E[E.year == Y].ng > 1).mean():.1f}")
L(f"events with records in >1 municipality (%): 2012-2025 {100 * (E.n_mun > 1).mean():.2f} | {Y} {100 * (E[E.year == Y].n_mun > 1).mean():.2f}")
L.save()

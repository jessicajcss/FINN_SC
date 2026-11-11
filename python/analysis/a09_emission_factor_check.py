#!/usr/bin/env python3
"""a09 - unit-conversion check: emission factors implied by the archived records.

For every record, EF_implied (g/kg) = species (t) x 1e6 / (AREA (m2) x BMASS (kg m-2)). If the
conversion from FINN native units (mol/day for gases, kg/day for aerosols and for the mass fields
NOXasNO and NMOC) to tonnes is correct, the median implied EF of each generic vegetation type equals
the emission factor of Wiedinmyer et al. (2023, GMD 16:3873, Table 4).
Outputs: results/tables/emission_factor_check.csv; results/logs/a09_emission_factor_check.txt
Manuscript (v3.2): section 2.4 (check of the unit conversion).
"""
from _setup import TAB, Log, load_records
import pandas as pd

L = Log("a09_emission_factor_check")
G = [1, 2, 3, 4, 5, 6, 9]
# Wiedinmyer et al. (2023), Table 4 (g kg-1), columns GENVEG 1, 2, 3, 4, 5, 6, 9
EF = {"CO2": [1686, 1681, 1643, 1510, 1565, 1623, 1444], "CO": [63, 67, 93, 122, 111, 112, 91],
      "CH4": [2, 3, 5.1, 5.61, 6, 3.4, 5.82], "NMOC": [28.2, 24.8, 51.9, 56, 48.5, 49.3, 51.4],
      "NOXasNO": [3.9, 3.65, 2.6, 1.04, 0.95, 1.96, 2.43], "SO2": [0.9, 0.68, 0.4, 1.1, 1, 1.1, 0.4],
      "PM25": [7.17, 7.1, 9.9, 15, 18.4, 17.9, 6.43], "OC": [2.6, 3.7, 4.7, 7.6, 7.8, 7.6, 2.66],
      "BC": [0.37, 1.31, 0.52, 0.56, 0.2, 0.56, 0.51], "NH3": [0.56, 1.2, 1.3, 2.47, 1.8, 1.17, 2.12],
      "PM10": [7.2, 11.4, 18.5, 16.97, 18.4, 18.4, 7.02]}
d = load_records()
d = d[(d.AREA > 0) & (d.BMASS > 0)]
bio = d.AREA * d.BMASS
rows = []
for s, ef in EF.items():
    imp = d[s] * 1e6 / bio
    med = imp.groupby(d.GENVEG).median()
    for k, v in med.items():
        rows.append(dict(species=s, GENVEG=int(k), n=int((d.GENVEG == k).sum()), ef_implied_median=v,
                         ef_table4=ef[G.index(int(k))], ratio=v / ef[G.index(int(k))]))
T = pd.DataFrame(rows)
T.to_csv(TAB / "emission_factor_check.csv", index=False)
L(T.round(4).to_string(index=False))
L(f"ratio implied/Table 4 over all species and classes: {T.ratio.min():.4f} to {T.ratio.max():.4f}")
L.save()

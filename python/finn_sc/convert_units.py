"""Unit conversion (Python port of 01_convert_units.R).

FINN native units (official README + empirical check of the v2.5/v2.5.1 files):
    gas-phase species          -> mole(species) / day
    aerosols (OC, BC, PM25, PM10, TPM, TPC) -> kg(species) / day
    NOXasNO, NMOC, NMHC        -> kg / day (mass fields)
# 2026-10-03 review: NMHC is a kg/day mass field (implied EFs match
# Wiedinmyer et al. 2023, Table 4, only as kg/day); it was previously converted
# as a gas with 72 g/mol, i.e. underestimated 13.9x. The species lists and
# molar masses live in config/config.yml (conversion section).

Convert everything to metric tonnes per reporting period:
    gas   : tonnes = mol * molar_mass[g/mol] / 1e6
    mass  : tonnes = kg / 1000
"""
from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def convert_finn_units(df: pd.DataFrame, cfg: Dict[str, Any]) -> pd.DataFrame:
    """Return a copy of ``df`` with emission columns rescaled to tonnes.

    Columns absent from ``df`` are silently skipped, so the same function works
    for FINNv1.5 and FINNv2.5 files (which carry different species sets).
    """
    out = df.copy()
    # 2026-10-03 review: FINN v2.5 headers contain padded names (e.g. " ACET");
    # pandas keeps the blank, so " ACET" was never converted nor summed. Strip.
    out.columns = [str(c).strip() for c in out.columns]
    conv = cfg["conversion"]
    molar = conv["molar_mass_g_per_mol"]
    mass_species = conv["mass_species_kg"]
    # 2026-10-03 review: a species listed as both kg/day and mol/day would be
    # converted twice; refuse such a config.
    both = set(mass_species) & set(molar)
    if both:
        raise ValueError(f"Species listed both as kg/day and mol/day in config: {sorted(both)}")

    # Aerosols / mass species: kg/day -> tonnes/day
    for col in mass_species:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce") / 1000.0

    # Gas-phase species: mol/day -> tonnes/day via molar mass
    for col, mw in molar.items():
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce") * float(mw) / 1e6

    return out

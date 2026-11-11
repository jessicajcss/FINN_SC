"""Unit conversion: FINN native units -> tonnes (config/config.yml, section conversion)."""
import pandas as pd
import pytest
from finn_sc import load_config, convert_finn_units


def test_conversion_gas_and_mass_fields():
    cfg = load_config()
    df = pd.DataFrame({" CO2": [1e6], "CO": [1e6], "NMHC": [1000.0], "NMOC": [1000.0], "NOXasNO": [1000.0], "PM25": [1000.0]})
    out = convert_finn_units(df, cfg)
    assert "CO2" in out.columns                                  # padded header stripped
    assert out.CO2[0] == pytest.approx(44.01)                    # 1e6 mol x 44.01 g/mol = 44.01 t
    assert out.CO[0] == pytest.approx(28.01)
    for c in ("NMHC", "NMOC", "NOXasNO", "PM25"):                # kg/day mass fields -> t
        assert out[c][0] == pytest.approx(1.0)


def test_species_not_listed_twice():
    cfg = load_config()
    assert not set(cfg["conversion"]["mass_species_kg"]) & set(cfg["conversion"]["molar_mass_g_per_mol"])

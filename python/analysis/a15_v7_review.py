#!/usr/bin/env python3
"""a15 - robustness checks added in the adversarial review of the English manuscript v7 (2026-11-06).

Questions and outputs (results/tables, log results/logs/a15_v7_review.txt)
  sen_slope_ci.csv                 Mann-Kendall test with the exact null distribution of S (Kendall 1975; no ties) and
                                   Sen slope with its 95% confidence interval (Sen 1968; ranks from the normal
                                   approximation of Var(S)), MODIS+VIIRS series 2012-2025 and FINN v2.5 only (2012-2021).
  climate_version_robustness.csv   the FINN version changed in 2022 and the v2.5.1 years (2022-2025) were wetter on
                                   average: Spearman correlations of the responses with the fire-season climate for the
                                   v2.5 years alone, and rank-based partial correlations controlling for the version
                                   (Pearson correlation of the residuals of the ranks regressed on a v2.5.1 indicator;
                                   t test with n - 3 degrees of freedom).
  viirs_increment_independent.csv  the VIIRS increment (MODIS+VIIRS / MODIS - 1) shares the MODIS value with its own
                                   denominator, so its correlation with the MODIS count is biased towards negative values
                                   (spurious correlation of a ratio with its denominator; Kronmal 1993). The increment is
                                   also correlated with activity measures independent of FINN (MapBiomas Fire and MCD64A1
                                   burned area) and with fire-season precipitation.
  emission_scenario_mapped_area_municipal.csv  mapped-area scenario of a14 computed municipality by municipality (FINN CO2
                                   per km2 of FINN area of each municipality x mapped area of the municipality; the State
                                   rate where a municipality has mapped area and no FINN area), next to the State-scale
                                   scenario of a14.
  sensitivity_factors.csv          values of manuscript Figure 9: annual CO2 relative to the 2012-2025 mean, and the CO2
                                   that each alternative choice gives relative to this inventory (FINN v2.5/v2.5.1
                                   MODIS+VIIRS with the FINN burned area).
"""
import numpy as np
import pandas as pd
from scipy import stats
from _setup import ROOT, TAB, Log

L = Log("a15_v7_review")
EXT = ROOT / "data" / "external"


def mahonian(n):
    """number of permutations of n items with k inversions, k = 0..n(n-1)/2 (exact null of Kendall's S)"""
    d = np.array([1], dtype=object)
    for k in range(1, n + 1):
        nd = np.zeros(len(d) + k - 1, dtype=object)
        for j in range(k):
            nd[j:j + len(d)] += d
        d = nd
    return d


def mk_exact(x):
    n = len(x)
    S = int(sum(np.sign(x[j] - x[i]) for i in range(n) for j in range(i + 1, n)))
    d = mahonian(n); N = n * (n - 1) // 2
    sv = np.array([N - 2 * i for i in range(len(d))])
    p = float(sum(c for s, c in zip(sv, d) if abs(s) >= abs(S)) / sum(d))
    return S, p


def sen_ci(x, alpha=0.05):
    n = len(x)
    sl = np.sort([(x[j] - x[i]) / (j - i) for i in range(n) for j in range(i + 1, n)])
    N = len(sl); C = stats.norm.ppf(1 - alpha / 2) * np.sqrt(n * (n - 1) * (2 * n + 5) / 18)
    m1 = int(round((N - C) / 2)); m2 = int(round((N + C) / 2)) + 1      # Gilbert (1987) ranks, 1-based
    return float(np.median(sl)), float(sl[m1 - 1]), float(sl[m2 - 1])


def spear(a, b):
    r, p = stats.spearmanr(a, b)
    return float(r), float(p)


def main():
    s = pd.read_csv(TAB / "series_state_all_products.csv")
    mv = s[(s.sensor == "MODIS+VIIRS") & (s.year >= 2012)].set_index("year").sort_index()
    L("a15 - robustness checks of the English manuscript v7")
    # 1. interannual variability
    for c in ("events", "area_km2", "CO2", "PM25"):
        x = mv[c].astype(float)
        L(f"interannual {c} 2012-2025: mean {x.mean():.6g}; SD {x.std(ddof=1):.6g}; CV {100 * x.std(ddof=1) / x.mean():.1f}%; "
          f"max/min {x.max() / x.min():.3f} ({x.idxmax()}/{x.idxmin()})")
    # 2. exact Mann-Kendall and Sen slope CI
    rows = []
    for c in ("events", "area_km2", "CO2", "PM25"):
        for a, b in ((2012, 2025), (2012, 2021)):
            x = mv.loc[a:b, c].astype(float).values
            S, p = mk_exact(x); sen, lo, hi = sen_ci(x); m = x.mean()
            rows.append(dict(variable=c, period=f"{a}-{b}", n=len(x), S=S, p_exact=p, sen=sen, ci_low=lo, ci_high=hi,
                             sen_pct_mean=100 * sen / m, ci_low_pct_mean=100 * lo / m, ci_high_pct_mean=100 * hi / m))
            L(f"MK {c} {a}-{b}: n {len(x)}; S {S}; exact p {p:.3f}; Sen {sen:.4g} (95% CI {lo:.4g} to {hi:.4g}); "
              f"{100 * sen / m:.2f}% of the mean per year (CI {100 * lo / m:.2f} to {100 * hi / m:.2f})")
    pd.DataFrame(rows).to_csv(TAB / "sen_slope_ci.csv", index=False)
    # 3. climate correlations and the version change
    cl = pd.read_csv(EXT / "era5land_oni_SC_fire_season_2012_2025.csv").set_index("year")
    d = mv.join(cl); d["v251"] = (d.version == "v2.5.1").astype(int)
    L(f"Jul-Nov precipitation, mean of the v2.5 years (2012-2021) {d[d.v251 == 0].precip_mm_fs.mean():.0f} mm; "
      f"v2.5.1 years (2022-2025) {d[d.v251 == 1].precip_mm_fs.mean():.0f} mm")
    rows = []
    for y in ("events", "area_km2", "CO2"):
        for xv in ("precip_mm_fs", "soil_moist_fs", "VPD_kPa_fs", "ONI_fs"):
            sub = d[d.v251 == 0]; r, p = spear(sub[xv], sub[y])
            rows.append(dict(response=y, predictor=xv, test="Spearman, FINN v2.5 years 2012-2021", n=len(sub), rho=r, p=p))
            rk = d[[y, xv]].rank(); X = np.c_[np.ones(len(d)), d.v251]
            res = lambda v: v - X @ np.linalg.lstsq(X, v, rcond=None)[0]
            pr = float(np.corrcoef(res(rk[y].values), res(rk[xv].values))[0, 1]); n = len(d)
            pp = float(2 * stats.t.sf(abs(pr * np.sqrt((n - 3) / (1 - pr ** 2))), n - 3))
            rows.append(dict(response=y, predictor=xv, test="partial rank correlation controlling for version, 2012-2025",
                             n=n, rho=pr, p=pp))
            L(f"climate {y} vs {xv}: v2.5 only rho {r:.3f} (p {p:.3f}); partial (version) rho {pr:.3f} (p {pp:.3f})")
    pd.DataFrame(rows).to_csv(TAB / "climate_version_robustness.csv", index=False)
    # 4. VIIRS increment against its own denominator and against independent activity measures
    vi = pd.read_csv(TAB / "viirs_increment.csv")
    mb = pd.read_csv(TAB / "mapbiomas_state.csv")[["year", "mb"]]
    mcd = pd.read_csv(TAB / "mcd64a1_comparison_state.csv")[["year", "mcd_km2"]]
    vi = vi.merge(mb, on="year").merge(mcd, on="year")
    rows = []
    for lab, sub in (("2012-2023 (v2.5 and v2.5.1)", vi), ("2012-2021 (v2.5)", vi[vi.version == "v2.5"])):
        for xv, xl in (("modis_events", "MODIS events (shared denominator)"), ("mb", "MapBiomas Fire area"),
                       ("mcd_km2", "MCD64A1 area"), ("precip_mm_fs", "Jul-Nov precipitation")):
            for yv in ("CO2_inc_pct", "events_ratio", "area_km2_inc_pct"):
                r, p = spear(sub[xv], sub[yv])
                rows.append(dict(years=lab, x=xl, y=yv, n=len(sub), rho=r, p=p))
            L(f"VIIRS CO2 increment vs {xl}, {lab}: rho {rows[-3]['rho']:.3f} (p {rows[-3]['p']:.3f}; n {len(sub)})")
    pd.DataFrame(rows).to_csv(TAB / "viirs_increment_independent.csv", index=False)
    m = s[(s.sensor == "MODIS") & (s.year.between(2012, 2023))].set_index("year")
    v = s[(s.sensor == "MODIS+VIIRS") & (s.year.between(2012, 2023))].set_index("year")
    for c in ("CO2", "events"):
        sl = stats.linregress(np.log(m[c]), np.log(v[c]))
        L(f"log(MODIS+VIIRS {c}) on log(MODIS {c}), 2012-2023: slope {sl.slope:.3f} (SE {sl.stderr:.3f})")
    # 5. mapped-area scenario municipality by municipality
    e = pd.read_csv(TAB / "events.csv.gz")
    e = e[e.sensor == "MODIS+VIIRS"]
    g = e.groupby(["year", "mun_event"]).agg(CO2=("CO2", "sum"), A=("area_m2", "sum")).reset_index()
    g["A"] = g.A / 1e6
    mbm = pd.read_csv(TAB / "mapbiomas_municipal.csv")
    mcdm = pd.read_csv(EXT / "mcd64a1_SC_municipal_km2_2012_2024.csv")
    rows = []
    for yr in range(2012, 2025):
        gy = g[g.year == yr].set_index("mun_event")
        rate_state = gy.CO2.sum() / gy.A.sum()
        out = dict(year=yr, CO2_finn_t=gy.CO2.sum(), finn_area_km2=gy.A.sum())
        for lab, M, col in (("mb", mbm, "mb_km2"), ("mcd", mcdm, "burned_km2")):
            mm = M[M.year == yr].set_index("NM_MUN")[col]
            miss = sorted(set(gy.index) - set(mm.index))
            assert not miss, f"municipality names without mapped-area rows: {miss[:5]}"
            j = pd.DataFrame({"mapped": mm}).join(gy, how="left").fillna(0.0)
            rate = np.where(j.A > 0, j.CO2 / j.A.where(j.A > 0, 1.0), rate_state)
            out[f"CO2_{lab}_state_scale_t"] = rate_state * j.mapped.sum()
            out[f"CO2_{lab}_municipal_scale_t"] = float((rate * j.mapped).sum())
            out[f"{lab}_area_km2"] = j.mapped.sum()
        rows.append(out)
    S = pd.DataFrame(rows)
    S["mb_municipal_over_state"] = S.CO2_mb_municipal_scale_t / S.CO2_mb_state_scale_t
    S["mcd_municipal_over_state"] = S.CO2_mcd_municipal_scale_t / S.CO2_mcd_state_scale_t
    S.to_csv(TAB / "emission_scenario_mapped_area_municipal.csv", index=False)
    for _, r in S.iterrows():
        L(f"scenario {int(r.year)}: FINN {r.CO2_finn_t / 1e6:.3f} Mt; MapBiomas state {r.CO2_mb_state_scale_t / 1e6:.3f} / "
          f"municipal {r.CO2_mb_municipal_scale_t / 1e6:.3f} Mt; MCD64A1 state {r.CO2_mcd_state_scale_t / 1e6:.3f} / "
          f"municipal {r.CO2_mcd_municipal_scale_t / 1e6:.3f} Mt")
    L(f"municipal / State scale, MapBiomas {S.mb_municipal_over_state.min():.3f} to {S.mb_municipal_over_state.max():.3f}; "
      f"MCD64A1 {S.mcd_municipal_over_state.min():.3f} to {S.mcd_municipal_over_state.max():.3f}")
    # 6. values of Figure 9
    rows = []
    mean = mv.CO2.mean()
    for yr, x in mv.CO2.items():
        rows.append(dict(item="interannual", year=yr, value=x / mean))
    for yr in range(2012, 2024):
        rows.append(dict(item="modis_only", year=yr, value=m.loc[yr, "CO2"] / v.loc[yr, "CO2"]))
    ic = pd.read_csv(TAB / "inventory_comparison_2020.csv")
    v15 = float(ic.loc[ic.version == "v1.5", "CO2_Mt"].iloc[0]); v25 = float(mv.loc[2020, "CO2"]) / 1e6
    rows.append(dict(item="finn_v15", year=2020, value=v15 / v25))
    sc = pd.read_csv(TAB / "emission_scenario_mapped_area.csv")
    for _, r in sc.iterrows():
        rows.append(dict(item="mapbiomas_area", year=int(r.year), value=r.CO2_mb_scenario_t / r.CO2_finn_t))
        rows.append(dict(item="mcd64a1_area", year=int(r.year), value=r.CO2_mcd_scenario_t / r.CO2_finn_t))
    F = pd.DataFrame(rows); F.to_csv(TAB / "sensitivity_factors.csv", index=False)
    for it, x in F.groupby("item").value:
        L(f"Figure 9 {it}: {x.min():.3f} to {x.max():.3f} (median {x.median():.3f}; n {len(x)})")
    L.save()


if __name__ == "__main__":
    main()

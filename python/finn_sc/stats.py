"""Small, dependency-light statistics used by the analysis layer.

Every function here is deterministic and covered by tests/test_stats.py.

References
----------
Mann, H. B. (1945) Econometrica 13, 245-259.          (Mann-Kendall test)
Sen, P. K. (1968) JASA 63, 1379-1389.                  (Sen slope)
Holm, S. (1979) Scand. J. Statist. 6, 65-70.           (Holm step-down adjustment)
Hamed, K. H.; Rao, A. R. (1998) J. Hydrol. 204, 182-196. (positive serial correlation inflates the
                                                       Mann-Kendall rejection rate; lag-1 check)
"""
from __future__ import annotations

import math
from typing import Dict, Iterable

import numpy as np


def mann_kendall(y: Iterable[float]) -> Dict[str, float]:
    """Mann-Kendall trend test with tie correction, normal approximation and
    continuity correction, plus the Sen slope (median of pairwise slopes).

    Returns n, S, tau (S / (n(n-1)/2)), z, two-sided p, sen (units per step) and
    sen_pct_mean (Sen slope as % of the series mean).
    """
    y = np.asarray(list(y), float)
    n = len(y)
    s = 0.0
    for i in range(n - 1):
        s += np.sign(y[i + 1:] - y[i]).sum()
    _, t = np.unique(y, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(k * (k - 1) * (2 * k + 5) for k in t)) / 18.0
    if s > 0:
        z = (s - 1) / math.sqrt(var)
    elif s < 0:
        z = (s + 1) / math.sqrt(var)
    else:
        z = 0.0
    p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))
    slopes = [(y[j] - y[i]) / (j - i) for i in range(n - 1) for j in range(i + 1, n)]
    sen = float(np.median(slopes))
    return dict(n=n, S=int(s), tau=s / (n * (n - 1) / 2), z=z, p=p, sen=sen,
                sen_pct_mean=sen / y.mean() * 100)


def lag1_autocorrelation(y: Iterable[float]) -> float:
    """Sample lag-1 autocorrelation r1 = sum_t (y_t - m)(y_{t+1} - m) / sum_t (y_t - m)^2.

    Used to check the independence assumption of the Mann-Kendall test: positive serial correlation
    increases the probability of detecting a trend when none exists (Hamed and Rao, 1998).
    """
    y = np.asarray(list(y), float)
    d = y - y.mean()
    return float((d[:-1] * d[1:]).sum() / (d * d).sum())


def holm(pvalues: Iterable[float]) -> np.ndarray:
    """Holm (1979) step-down adjusted p-values, in the original order."""
    p = np.asarray(list(pvalues), float)
    m = len(p)
    order = np.argsort(p)
    adj = np.minimum(1.0, np.maximum.accumulate(p[order] * (m - np.arange(m))))
    out = np.empty(m)
    out[order] = adj
    return out


def gini(x: Iterable[float]) -> float:
    """Gini index of non-negative values (0 = equal, -> 1 = concentrated).

    G = (n + 1 - 2 * sum_i C_i / C_n) / n with C the cumulative sum of the
    values sorted in ascending order (Lorenz-curve form)."""
    v = np.sort(np.asarray(list(x), float))
    if (v < 0).any():
        raise ValueError("Gini index requires non-negative values")
    n = len(v)
    c = np.cumsum(v)
    return float((n + 1 - 2 * np.sum(c) / c[-1]) / n)


def cv_percent(x: Iterable[float]) -> float:
    """Coefficient of variation (%) with the sample standard deviation (ddof = 1)."""
    v = np.asarray(list(x), float)
    return float(np.std(v, ddof=1) / np.mean(v) * 100)

"""Unit tests of finn_sc.stats (known analytical values)."""
import math
import numpy as np
import pytest
from finn_sc.stats import mann_kendall, holm, gini, cv_percent


def test_mann_kendall_monotonic_series():
    m = mann_kendall(range(1, 11))                 # strictly increasing, n = 10, no ties
    assert m["S"] == 45 and m["tau"] == 1.0        # S = n(n-1)/2
    var = 10 * 9 * 25 / 18.0
    assert m["z"] == pytest.approx((45 - 1) / math.sqrt(var))
    assert m["sen"] == 1.0 and m["p"] < 0.001


def test_mann_kendall_ties_and_sign():
    m = mann_kendall([3, 3, 2, 2, 1, 1])
    assert m["S"] < 0 and m["sen"] < 0
    # tie correction: three groups of size 2 -> var = (6*5*17 - 3*2*1*9)/18
    var = (6 * 5 * 17 - 3 * (2 * 1 * 9)) / 18.0
    assert m["z"] == pytest.approx((m["S"] + 1) / math.sqrt(var))


def test_holm_known_example():
    # Holm (1979) step-down: sorted p * (m - rank), cumulative maximum, capped at 1
    p = [0.01, 0.04, 0.03, 0.005]
    adj = holm(p)
    assert adj == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_gini_extremes():
    assert gini([5, 5, 5, 5]) == pytest.approx(0.0)
    assert gini([0, 0, 0, 1]) == pytest.approx(0.75)    # (n - 1) / n for one non-zero value
    with pytest.raises(ValueError):
        gini([1, -1])


def test_cv_percent():
    x = np.array([2.0, 4.0, 6.0])
    assert cv_percent(x) == pytest.approx(np.std(x, ddof=1) / 4.0 * 100)

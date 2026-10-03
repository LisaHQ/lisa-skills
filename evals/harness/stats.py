"""Small statistics for paired comparisons of skill versions (standard library only)."""
from __future__ import annotations

import math
import statistics

# Two-sided 95% critical values of Student's t by degrees of freedom; a
# missing df uses the next smaller listed df, which is conservative.
T95 = {1: 12.71, 2: 4.30, 3: 3.18, 4: 2.78, 5: 2.57, 6: 2.45, 7: 2.36, 8: 2.31, 9: 2.26, 10: 2.23,
       11: 2.20, 12: 2.18, 13: 2.16, 14: 2.14, 15: 2.13, 16: 2.12, 17: 2.11, 18: 2.10, 19: 2.09, 20: 2.09,
       25: 2.06, 30: 2.04, 40: 2.02, 60: 2.00, 120: 1.98}


def t95(df: int) -> float:
    if df < 1:
        return float("nan")
    return T95[max(k for k in T95 if k <= df)] if df < 1000 else 1.96


def sign_test(wins: int, losses: int) -> float:
    """Exact two-sided sign-test p value, ties excluded."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n)


def paired(diffs: list[float], clusters: list[str] | None = None) -> dict:
    """Mean paired difference with its standard error and 95% interval.

    With clusters (one scenario id per difference) spanning repeated
    scenarios, also computes the scenario-clustered (CR1) SE of the same mean
    and bases the interval on the larger of the two, with k-1 degrees of
    freedom for k scenarios.
    """
    n = len(diffs)
    out = {"n": n, "mean": statistics.fmean(diffs) if diffs else float("nan"),
           "wins": sum(d > 1e-9 for d in diffs), "losses": sum(d < -1e-9 for d in diffs)}
    out["ties"] = n - out["wins"] - out["losses"]
    out["se"] = statistics.stdev(diffs) / math.sqrt(n) if n > 1 else float("nan")
    df = n - 1
    if clusters and len(set(clusters)) < n:
        resid: dict[str, float] = {}
        for c, d in zip(clusters, diffs):
            resid[c] = resid.get(c, 0.0) + d - out["mean"]
        k = len(resid)
        out["se_clustered"] = (math.sqrt(k / (k - 1) * sum(r * r for r in resid.values())) / n
                               if k > 1 else float("nan"))
        if k > 1 and not out["se_clustered"] < out["se"]:
            out["se"], df = out["se_clustered"], k - 1
    half = t95(df) * out["se"] if n > 1 else float("nan")
    out["low"], out["high"] = out["mean"] - half, out["mean"] + half
    out["p_sign"] = sign_test(out["wins"], out["losses"])
    return out


def paired_line(label: str, diffs: list[float], clusters: list[str] | None = None) -> str:
    if not diffs:
        return f"{label}: no paired outcomes"
    r = paired(diffs, clusters)
    verdict = ("" if r["n"] < 2 else "  -> no spread; decide from W/T/L and sign-p" if r["se"] == 0
               else "  -> interval excludes 0" if r["low"] > 0 or r["high"] < 0 else "  -> inconclusive")
    return (f"{label}: n={r['n']} diff={r['mean']:+.2f} se={r['se']:.2f} 95% [{r['low']:+.2f}, {r['high']:+.2f}] "
            f"W/T/L={r['wins']}/{r['ties']}/{r['losses']} sign-p={r['p_sign']:.2f}{verdict}")

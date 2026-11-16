"""Shared functions for the GBM mini project notebooks."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"
FIG_DIR = ROOT / "figures"
TAB_DIR = ROOT / "tables"


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------
def set_style() -> None:
    """One consistent matplotlib style for every figure in the project.

    Sized so text stays legible when a figure is shrunk to half a page width.
    """
    mpl.rcParams.update({
        "figure.figsize": (6.0, 3.4),
        "figure.dpi": 110,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.size": 11,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "legend.frameon": False,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": "#d9d9d9",
        "grid.linewidth": 0.6,
        "axes.axisbelow": True,
        "lines.linewidth": 1.2,
        "pdf.fonttype": 42,
    })


def savefig(fig: plt.Figure, name: str) -> None:
    """Save a figure to figures/ as PNG (300 dpi) and PDF."""
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIG_DIR / f"{name}.png", dpi=300)
    fig.savefig(FIG_DIR / f"{name}.pdf")


def shade_period(ax: plt.Axes, start: str, end: str, label: str | None = None) -> None:
    """Grey vertical band marking a date range (e.g. the COVID crash)."""
    ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color="0.6", alpha=0.25,
               lw=0, label=label)


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
def load_or_download_prices(tickers: list[str], start: str, end: str,
                            download_date: str) -> tuple[pd.DataFrame, bool]:
    """Return the raw yfinance download, cached in data/raw/.

    The exact call is
    ``yf.download(tickers, start=start, end=end, auto_adjust=False,
    actions=True, progress=False)``. The result is saved untouched (wide
    format, one column per field/ticker) to data/raw/prices_<download_date>.csv
    and read back from there on later runs.

    Returns (raw, downloaded_now).
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"prices_{download_date}.csv"
    if path.exists():
        raw = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
        return raw, False

    import yfinance as yf
    raw = yf.download(tickers, start=start, end=end, auto_adjust=False,
                      actions=True, progress=False)
    raw.to_csv(path)
    raw = pd.read_csv(path, header=[0, 1], index_col=0, parse_dates=True)
    return raw, True


def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Daily log returns X_k = ln(S_k / S_{k-1}); first row dropped."""
    return np.log(prices).diff().iloc[1:]


def max_run_of_repeats(s: pd.Series) -> int:
    """Longest run of consecutive identical values (1 = no repeats)."""
    same = s.eq(s.shift())
    runs = same.groupby((~same).cumsum()).sum()
    return int(runs.max()) + 1 if len(runs) else 1


# ---------------------------------------------------------------------------
# Diagnostics (notebook 02)
# ---------------------------------------------------------------------------
def aggregate_returns(rets: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Sum daily log returns into calendar periods (e.g. 'W-FRI', 'ME').

    The sum of daily log returns over a period is the log return over that
    period. The first and last periods are dropped because the sample starts
    and ends part-way through them.
    """
    g = rets.resample(rule)
    agg = g.sum()[g.count().min(axis=1) > 0]
    return agg.iloc[1:-1]


def describe_returns(x: pd.Series, lb_lag: int) -> dict:
    """Moments and GBM test statistics for one return series."""
    from scipy import stats
    from statsmodels.stats.diagnostic import acorr_ljungbox

    x = x.dropna().to_numpy()
    jb = stats.jarque_bera(x)
    lb = acorr_ljungbox(x, lags=[lb_lag])["lb_pvalue"].iloc[0]
    lb2 = acorr_ljungbox(x**2, lags=[lb_lag])["lb_pvalue"].iloc[0]
    return {
        "n": len(x),
        "mean": x.mean(),
        "std": x.std(ddof=1),
        "skewness": stats.skew(x, bias=False),
        "excess kurtosis": stats.kurtosis(x, fisher=True, bias=False),
        "JB p-value": jb.pvalue,
        "LB lag": lb_lag,
        "LB p-value (returns)": lb,
        "LB p-value (squared returns)": lb2,
    }


def tail_counts(x: pd.Series, ks=(3, 4)) -> dict:
    """Observed vs GBM-expected number of |standardised return| > k."""
    from scipy import stats

    x = x.dropna()
    z = (x - x.mean()) / x.std(ddof=1)
    out = {}
    for k in ks:
        out[f"|z|>{k} observed"] = int((z.abs() > k).sum())
        out[f"|z|>{k} expected"] = len(z) * 2 * stats.norm.sf(k)
    return out


def variance_ratio(x: pd.Series, q: int) -> tuple[float, float, float]:
    """Lo-MacKinlay (1988) variance ratio with overlapping q-period sums.

    VR(q) = Var(q-period return) / (q * Var(1-period return)); VR = 1 under
    i.i.d. returns (variance linear in horizon). Returns (VR, z*, p-value),
    where z* is the heteroskedasticity-robust statistic.
    """
    from scipy import stats

    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = len(x)
    mu = x.mean()
    d = x - mu
    var_a = (d @ d) / (n - 1)
    sums = np.convolve(x, np.ones(q), mode="valid")          # n - q + 1 overlapping sums
    m = q * (n - q + 1) * (1 - q / n)
    var_c = ((sums - q * mu) ** 2).sum() / m
    vr = var_c / var_a
    d2 = d**2
    denom = d2.sum() ** 2
    theta = 0.0
    for j in range(1, q):
        delta = n * (d2[j:] @ d2[:-j]) / denom
        theta += (2 * (q - j) / q) ** 2 * delta
    z = np.sqrt(n) * (vr - 1) / np.sqrt(theta)             # sqrt(n)(VR - 1) -> N(0, theta)
    return vr, z, 2 * stats.norm.sf(abs(z))

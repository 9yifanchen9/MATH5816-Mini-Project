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


# ---------------------------------------------------------------------------
# Window-size analysis (notebook 02). Vectorised over windows (rows).
# ---------------------------------------------------------------------------
def make_windows(x, L: int) -> np.ndarray:
    """Non-overlapping windows of length L from the start; leftover tail dropped."""
    x = np.asarray(x, dtype=float)
    m = len(x) // L
    return x[: m * L].reshape(m, L)


def jb_pvalues(xw: np.ndarray) -> np.ndarray:
    """Jarque-Bera p-value for each row (same statistic as scipy.stats.jarque_bera)."""
    from scipy import stats

    d = xw - xw.mean(axis=1, keepdims=True)
    m2 = (d**2).mean(axis=1)
    s = (d**3).mean(axis=1) / m2**1.5
    k = (d**4).mean(axis=1) / m2**2
    jb = xw.shape[1] / 6 * (s**2 + (k - 3) ** 2 / 4)
    return stats.chi2.sf(jb, 2)


def lb_pvalues(xw: np.ndarray, h: int) -> np.ndarray:
    """Ljung-Box(h) p-value for each row (same statistic as statsmodels acorr_ljungbox)."""
    from scipy import stats

    L = xw.shape[1]
    d = xw - xw.mean(axis=1, keepdims=True)
    denom = (d**2).sum(axis=1)
    q = np.zeros(len(xw))
    for k in range(1, h + 1):
        r = (d[:, k:] * d[:, :-k]).sum(axis=1) / denom
        q += r**2 / (L - k)
    return stats.chi2.sf(L * (L + 2) * q, h)


def window_pvalues(xw: np.ndarray, h: int) -> dict:
    """p-values of the three i.i.d.-normal checks for each window."""
    return {"normality (JB)": jb_pvalues(xw),
            f"independence (LB({h}))": lb_pvalues(xw, h),
            f"constant volatility (LB({h}) on squares)": lb_pvalues(xw**2, h)}


# ---------------------------------------------------------------------------
# Bayesian analysis (notebook 03b)
# ---------------------------------------------------------------------------
def gbm_posterior_draws(X: np.ndarray, n_draws: int, rng) -> tuple[np.ndarray, np.ndarray]:
    """Draws from the posterior of (m, V) for X_k iid N_d(m, V) under the
    Jeffreys prior p(m, V) ∝ |V|^{-(d+1)/2}:

        V | X ~ Inv-Wishart(n - 1, S),   m | V, X ~ N(xbar, V / n),

    with S the centred sum of squares (Gelman et al., BDA3, Sec. 3.6).
    Returns m (n_draws x d) and V (n_draws x d x d), per-period units.
    """
    from scipy import stats

    X = np.asarray(X, dtype=float)
    n, d = X.shape
    xbar = X.mean(axis=0)
    S = (X - xbar).T @ (X - xbar)
    V = stats.invwishart(df=n - 1, scale=S).rvs(n_draws, random_state=rng).reshape(n_draws, d, d)
    z = rng.standard_normal((n_draws, d, 1))
    m = xbar + (np.linalg.cholesky(V / n) @ z)[..., 0]
    return m, V


def t_log_posterior(theta, x, df_shape, df_rate):
    """Log posterior of the i.i.d. Student-t model x = a + s * t_df on
    theta = (a, log s, log df). Priors: flat on a, p(s) ∝ 1/s (flat on log s),
    df ~ Gamma(shape, rate) (Jacobian for log df included).
    """
    from scipy import stats

    a, log_s, log_df = theta
    df = np.exp(log_df)
    if not (0.1 < df < 1e4):
        return -np.inf
    ll = stats.t.logpdf(x, df, loc=a, scale=np.exp(log_s)).sum()
    lp = stats.gamma.logpdf(df, df_shape, scale=1 / df_rate) + log_df
    return ll + lp


def metropolis(logpost, start: np.ndarray, cov: np.ndarray, n_iter: int, rng) -> tuple[np.ndarray, float]:
    """Random-walk Metropolis with Gaussian proposal covariance `cov`.
    Returns (draws n_iter x p, acceptance rate)."""
    p = len(start)
    chol = np.linalg.cholesky(cov)
    cur, cur_lp = np.array(start, float), logpost(start)
    out = np.empty((n_iter, p))
    acc = 0
    for i in range(n_iter):
        prop = cur + chol @ rng.standard_normal(p)
        lp = logpost(prop)
        if np.log(rng.uniform()) < lp - cur_lp:
            cur, cur_lp = prop, lp
            acc += 1
        out[i] = cur
    return out, acc / n_iter


def split_rhat(chains: np.ndarray) -> float:
    """Split-R-hat for one parameter; chains shape (n_chains, n_draws)."""
    half = chains.shape[1] // 2
    c = np.concatenate([chains[:, :half], chains[:, half: 2 * half]])
    n = c.shape[1]
    W = c.var(axis=1, ddof=1).mean()
    B = n * c.mean(axis=1).var(ddof=1)
    return float(np.sqrt(((n - 1) / n * W + B / n) / W))


def ess(chains: np.ndarray) -> float:
    """Effective sample size for one parameter (Geyer initial positive sequence
    on the chain-averaged autocorrelation); chains shape (n_chains, n_draws)."""
    m, n = chains.shape
    c = chains - chains.mean(axis=1, keepdims=True)
    f = np.fft.rfft(c, 2 * n, axis=1)
    ac = np.fft.irfft(f * np.conj(f), axis=1)[:, :n]
    rho = (ac / ac[:, :1]).mean(axis=0)
    # tau = -1 + 2 * sum_k (rho_{2k} + rho_{2k+1}), stopping at the first negative pair
    tau = -1.0
    for t in range(0, n - 1, 2):
        pair = rho[t] + rho[t + 1]
        if pair < 0:
            break
        tau += 2 * pair
    return float(m * n / tau)


def waic(loglik: np.ndarray) -> tuple[float, np.ndarray]:
    """WAIC (deviance scale) from a draws x observations log-likelihood matrix.
    Returns (WAIC, pointwise contributions)."""
    from scipy.special import logsumexp

    lppd = logsumexp(loglik, axis=0) - np.log(loglik.shape[0])
    p_waic = loglik.var(axis=0, ddof=1)
    point = -2 * (lppd - p_waic)
    return float(point.sum()), point


# ---------------------------------------------------------------------------
# Estimation (notebook 03). Annual units: dt in years per period.
# ---------------------------------------------------------------------------
def gbm_estimates(x, dt: float, level: float = 0.95) -> dict:
    """MLE of GBM parameters from log returns x sampled every dt years,
    with i.i.d. confidence intervals.

    nu = xbar/dt; sigma^2 = s^2/dt (n-1 divisor); mu = nu + sigma^2/2.
    CIs: t-interval for nu (SE = s/sqrt(n)/dt = sigma/sqrt(T));
    chi-square interval for sigma; delta method for mu
    (Var(mu) = SE(nu)^2 + sigma^4 / (2(n-1))). Also SE(sigma) ~ sigma/sqrt(2n).
    """
    from scipy import stats

    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = len(x)
    s = x.std(ddof=1)
    nu = x.mean() / dt
    sig = s / np.sqrt(dt)
    mu = nu + sig**2 / 2
    se_nu = sig / np.sqrt(n * dt)
    se_sig = sig / np.sqrt(2 * n)
    se_mu = np.sqrt(se_nu**2 + sig**4 / (2 * (n - 1)))
    a = 1 - level
    tq, zq = stats.t.ppf(1 - a / 2, n - 1), stats.norm.ppf(1 - a / 2)
    return {
        "n": n, "T": n * dt,
        "nu": nu, "se_nu": se_nu, "nu_lo": nu - tq * se_nu, "nu_hi": nu + tq * se_nu,
        "mu": mu, "se_mu": se_mu, "mu_lo": mu - zq * se_mu, "mu_hi": mu + zq * se_mu,
        "sigma": sig, "se_sigma": se_sig,
        "sigma_lo": np.sqrt((n - 1) * s**2 / stats.chi2.ppf(1 - a / 2, n - 1) / dt),
        "sigma_hi": np.sqrt((n - 1) * s**2 / stats.chi2.ppf(a / 2, n - 1) / dt),
    }


def fisher_ci(r: float, n: int, level: float = 0.95) -> tuple[float, float]:
    """Fisher z-transform confidence interval for a correlation."""
    from scipy import stats

    z = stats.norm.ppf(1 - (1 - level) / 2)
    return np.tanh(np.arctanh(r) - z / np.sqrt(n - 3)), np.tanh(np.arctanh(r) + z / np.sqrt(n - 3))


def newey_west_lags(n: int) -> int:
    """Newey-West (1994) rule of thumb: floor(4 (n/100)^(2/9))."""
    return int(np.floor(4 * (n / 100) ** (2 / 9)))


def hac_se_mean(x, lags: int) -> float:
    """Newey-West (Bartlett kernel) standard error of the sample mean."""
    x = np.asarray(pd.Series(x).dropna(), dtype=float)
    n = len(x)
    d = x - x.mean()
    lrv = d @ d / n
    for j in range(1, lags + 1):
        lrv += 2 * (1 - j / (lags + 1)) * (d[j:] @ d[:-j]) / n
    return float(np.sqrt(lrv / n))


def block_bootstrap_indices(n: int, block: int, B: int, rng) -> np.ndarray:
    """Moving-block bootstrap: B x n index array built from blocks of
    `block` consecutive observations with uniformly random start points."""
    k = int(np.ceil(n / block))
    starts = rng.integers(0, n - block + 1, size=(B, k))
    idx = (starts[:, :, None] + np.arange(block)).reshape(B, k * block)
    return idx[:, :n]


def bootstrap_gbm_stats(X: np.ndarray, dt: float, block: int, B: int, rng, chunk: int = 250) -> pd.DataFrame:
    """Joint moving-block bootstrap of a bivariate return array X (n x 2).
    Rows of both series are resampled together, keeping their correlation.
    Returns B rows of annual nu, sigma, mu for each column, rho and the
    drift difference nu_1 - nu_0."""
    n = len(X)
    out = []
    for start in range(0, B, chunk):
        b = min(chunk, B - start)
        Xb = X[block_bootstrap_indices(n, block, b, rng)]          # (b, n, 2)
        m = Xb.mean(axis=1)
        s = Xb.std(axis=1, ddof=1)
        c = ((Xb - m[:, None, :]).prod(axis=2)).sum(axis=1) / (n - 1)
        out.append(np.column_stack([m / dt, s / np.sqrt(dt), c / (s[:, 0] * s[:, 1])]))
    a = np.vstack(out)
    df = pd.DataFrame({"nu_0": a[:, 0], "nu_1": a[:, 1], "sigma_0": a[:, 2], "sigma_1": a[:, 3], "rho": a[:, 4]})
    df["mu_0"] = df.nu_0 + df.sigma_0**2 / 2
    df["mu_1"] = df.nu_1 + df.sigma_1**2 / 2
    df["nu_1 - nu_0"] = df.nu_1 - df.nu_0
    return df

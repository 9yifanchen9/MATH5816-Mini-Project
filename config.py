"""Project-wide settings for the GBM mini project.

Every value set by hand lives here with a note on where it comes from.
Every hand-set value below cites its source.
"""

import math

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------
# Both ETFs are ASX-listed and priced in AUD. VGS is currency-unhedged.
TICKERS = {"AU": "VAS.AX", "GL": "VGS.AX"}
LABELS = {"AU": "Australia (VAS)", "GL": "Global ex-AU (VGS)"}

# yfinance call: start well before either listing so the full history is kept;
# the analysis START is the first common trading day, found from the data in
# notebook 01 (VGS listed on the ASX in Nov 2014).
DOWNLOAD_START = "2000-01-01"

# Date the raw data was downloaded. The raw CSV is saved as
# data/raw/prices_<DOWNLOAD_DATE>.csv and re-used on every rerun, so results
# are reproducible. Delete the file (or change the date) to re-download.
DOWNLOAD_DATE = "2026-11-10"

# yfinance `end` is EXCLUSIVE. Setting END = DOWNLOAD_DATE drops the download
# day itself, whose bar was still intraday (download at ~12:45 pm AEDT, during
# ASX trading hours). The last observation is therefore the previous close.
END = DOWNLOAD_DATE

# Price field: Adj Close (adjusted for distributions and splits, so it
# approximates a total-return series; franking credits are NOT included).
PRICE_FIELD = "Adj Close"

# Threshold for flagging large daily moves for inspection (absolute log return).
OUTLIER_THRESHOLD = 0.10

# COVID-19 crash window used for shading figures: S&P/ASX 200 peak on
# 20 Feb 2020 and trough on 23 Mar 2020 (global markets peaked 19-20 Feb and
# bottomed 23 Mar 2020).
COVID_CRASH = ("2020-02-20", "2020-03-23")

# ---------------------------------------------------------------------------
# Model conventions
# ---------------------------------------------------------------------------
TRADING_DAYS = 252          # annualisation convention: dt = 1/252 years
DT = 1.0 / TRADING_DAYS

# Risk-free rate, annual, continuously compounded.
# RBA cash rate target 4.85% p.a., effective 4 Nov 2026 (Reserve Bank of Australia,
# cash rate target; RBA statistical table F1). Value as supplied by the author.
# Converted to continuous compounding: r = ln(1 + 0.0485).
R_SIMPLE = 0.0485
R_ANNUAL = math.log(1 + R_SIMPLE)
R_SOURCE = "RBA cash rate target 4.85% p.a., effective 4 Nov 2026"

SEED = 5816                 # all simulations
HORIZONS = [1, 5, 10, 20, 30]   # years
W0 = 10_000                 # initial wealth, AUD

BLOCK_LENGTH = 20           # block bootstrap block length (trading days)
N_BOOT = 5_000              # bootstrap resamples (notebook 03)
N_PATHS = 100_000           # Monte Carlo paths (notebook 04)

# ---------------------------------------------------------------------------
# Portfolios (notebook 04). pi = equity fraction, w = AU share of equities.
# ---------------------------------------------------------------------------
# Home-biased: 1/3 Australian, 2/3 international equities. This is the optimal
# lifecycle split (average 34% domestic / 66% international stocks at all ages)
# in Anarkulova, A., Cederburg, S. and O'Doherty, M. S. (2026), "Beyond the
# Status Quo: A Critical Assessment of Lifecycle Investment Advice", working
# paper dated 27 Aug 2026, SSRN abstract 4590406, Sec. 5.1 and Table III Panel A
# (p. 22). It is a model-optimal allocation for a household in a developed
# market, not an observed average holding; it is home-biased relative to the
# market-cap weight below.
W_HOME_BIASED = 1 / 3
W_HOME_BIASED_SOURCE = ("Anarkulova, Cederburg and O'Doherty (2026), SSRN 4590406: "
                        "optimal split ~1/3 domestic, 2/3 international equities")

# Market-cap weight: Australia's share of the MSCI World index, 1.6%. From MSCI
# index factsheets, data as of 30 Oct 2026 (msci.com): index market cap of
# MSCI World (AUD) A$127,379,863.77m and MSCI World ex Australia (AUD)
# A$125,341,964.77m, so Australia = 1 - 125,341,964.77 / 127,379,863.77 = 1.60%.
# MSCI World ex Australia is the index VGS tracks, so w = 1.6% in VAS plus
# 98.4% in VGS reproduces MSCI World.
W_MARKET_CAP = 0.016
W_MARKET_CAP_SOURCE = "MSCI World vs MSCI World ex Australia (AUD) index factsheets, 30 Oct 2026: 1.60%"

# ---------------------------------------------------------------------------
# Plot colours (Okabe-Ito, colourblind-safe). Same colour per asset throughout.
# ---------------------------------------------------------------------------
COLORS = {"AU": "#0072B2", "GL": "#D55E00", "SAV": "#009E73"}

# ---------------------------------------------------------------------------
# Diagnostics (notebook 02)
# ---------------------------------------------------------------------------
FREQ_RULES = {"daily": None, "weekly": "W-FRI", "monthly": "ME"}  # pandas resample rules
ACF_LAGS = 20                # ACF plotted for lags 1-20
LB_LAGS = {"daily": 20, "weekly": 10, "monthly": 6}  # Ljung-Box lag per frequency
ROLL_VOL_WINDOW = 63         # rolling volatility window (trading days, ~3 months)
ROLL_CORR_WINDOW = 126       # rolling correlation window (trading days, ~6 months)
VR_HORIZONS = [2, 5, 10, 21, 63]  # variance-ratio horizons q (trading days)

# Window-size analysis (notebook 02): non-overlapping windows, trading days
WINDOW_LENGTHS = [63, 126, 252, 504, 756, 1008, 1512]   # 3m, 6m, 1y, 2y, 3y, 4y, 6y
LB_WINDOW_LAG = 10           # Ljung-Box lag used inside every window
N_SIM_WINDOWS = 5_000        # simulated GBM windows per length (benchmark rejection rate)

# ---------------------------------------------------------------------------
# Bayesian analysis (notebook 03b)
# ---------------------------------------------------------------------------
N_POST = 20_000              # posterior draws, GBM model (exact conjugate sampling)
N_PPC = 2_000                # posterior predictive replicated samples
# Prior on Student-t degrees of freedom: Gamma(shape 2, rate 0.1), mean 20,
# from Juarez & Steel (2010), J. Business & Economic Statistics 28(1), 52-66.
T_DF_PRIOR = (2.0, 0.1)
MCMC_CHAINS = 4
MCMC_ITER = 6_000            # per chain, after a separate pilot run
MCMC_BURN = 1_000            # discarded from the start of each chain

# ---------------------------------------------------------------------------
# Estimation (notebook 03)
# ---------------------------------------------------------------------------
NW_LAGS = None               # Newey-West lags; None = rule floor(4 (n/100)^(2/9)) (Newey & West, 1994)
MIN_DAYS_PER_YEAR = 126      # calendar years with fewer trading days are left out of the yearly estimates
ROLL_EST_WINDOW = 504        # rolling estimation window (trading days, 2 years)
N_SIM_CHECK = 1_000          # simulated GBM samples for the estimator check
N_SIM_CORR = 1_000           # simulated constant-correlation Gaussian pairs (rolling-correlation benchmark)

# ---------------------------------------------------------------------------
# Application (notebook 04)
# ---------------------------------------------------------------------------
N_BOOT_PATHS = 100_000       # block-bootstrap wealth paths (model-risk check)
# Portfolio colours: savings, all-AU and market-cap (~global) reuse the asset colours;
# home-biased uses Okabe-Ito reddish purple; minimum variance dark grey with dashed lines.
PORT_COLORS = {"Savings": "#009E73", "All Australian": "#0072B2", "Home-biased": "#CC79A7",
               "Market-cap": "#D55E00", "Minimum variance": "#4D4D4D"}

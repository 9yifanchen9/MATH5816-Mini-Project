"""Project-wide settings for the GBM mini project.

Every value set by hand lives here with a note on where it comes from.
Values marked TODO must be filled in (with a source) before the notebook
that uses them is run.
"""

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
# TODO: fill in by hand from the RBA cash rate target or 90-day bank bill
# rate (RBA statistical table F1), state the date, and convert to continuous
# compounding: r = ln(1 + r_simple). Required from notebook 04.
R_ANNUAL = None
R_SOURCE = "TODO: source and date"

SEED = 5816                 # all simulations
HORIZONS = [1, 5, 10, 20, 30]   # years
W0 = 10_000                 # initial wealth, AUD

BLOCK_LENGTH = 20           # block bootstrap block length (trading days)
N_BOOT = 5_000              # bootstrap resamples (notebook 03)
N_PATHS = 100_000           # Monte Carlo paths (notebook 04)

# ---------------------------------------------------------------------------
# Portfolios (notebook 04). pi = equity fraction, w = AU share of equities.
# ---------------------------------------------------------------------------
# TODO: set from cited sources before running notebook 04.
W_HOME_BIASED = None        # typical Australian investor's AU share of equities
W_HOME_BIASED_SOURCE = "TODO: source"
W_MARKET_CAP = None         # Australia's share of world equity market cap (~2%)
W_MARKET_CAP_SOURCE = "TODO: source"

# ---------------------------------------------------------------------------
# Plot colours (Okabe-Ito, colourblind-safe). Same colour per asset throughout.
# ---------------------------------------------------------------------------
COLORS = {"AU": "#0072B2", "GL": "#D55E00", "SAV": "#009E73"}

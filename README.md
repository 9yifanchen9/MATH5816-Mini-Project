# MATH5816 mini project: GBM on Australian and global equity ETFs

Tests geometric Brownian motion on VAS.AX (Australian shares) and VGS.AX (global ex-Australia shares,
unhedged), estimates its parameters, and compares savings, home-biased and globally diversified
portfolios for an Australian investor. See `PLAN.md` for the full plan.

## Rerun everything

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cd notebooks
for nb in 01_data 02_diagnostics 03_estimation 03b_bayesian 04_application; do
  jupyter nbconvert --to notebook --execute --inplace "$nb.ipynb"
done
```

Notebook 01 reads the cached raw download `data/raw/prices_<DOWNLOAD_DATE>.csv` if it exists, so results
are reproducible. To refresh the data, change `DOWNLOAD_DATE`/`END` in `config.py` (or delete the CSV).

## Layout

| Path | Contents |
| --- | --- |
| `config.py` | Tickers, dates, Δt convention, r, seed, horizons, portfolio weights (hand-set values cite a source) |
| `src/gbm_utils.py` | Shared functions (plot style, data loading, returns) |
| `data/raw/` | Untouched yfinance download |
| `data/clean/` | Aligned prices and daily log returns |
| `notebooks/` | `01_data`, `02_diagnostics`, `03_estimation`, `03b_bayesian`, `04_application` — run in order (03b needs only 01) |
| `figures/` | Figures as PNG (300 dpi) and PDF |
| `tables/` | Tables as CSV and LaTeX |

## Reproducibility details

- Data: Yahoo Finance via `yfinance`, `yf.download(["VAS.AX", "VGS.AX"], start="2000-01-01", end=END, auto_adjust=False, actions=True)`; `end` is exclusive. Price field: Adj Close (franking credits not included).
- Δt = 1/252 years; seed 5816; block bootstrap block length 20 trading days.
- Risk-free rate and portfolio weights: see `config.py` for values and sources.
- Bayesian analysis (03b): Jeffreys prior for the GBM parameters (exact conjugate sampling, 20,000 draws); Student-t model with df ~ Gamma(2, 0.1) (Juárez and Steel, 2010), random-walk Metropolis, 4 chains; seed 5816.

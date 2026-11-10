# GBM Mini Project — Claude Code Plan

Nov 10, 2026 · @Yifan

## Purpose and how to use this plan

Claude Code should build four Jupyter notebooks that test geometric Brownian motion (GBM) on Australian and global equity ETFs, estimate its parameters, and compare savings, home-biased and globally diversified portfolios for an Australian investor.

The outputs feed a 6-page report for MATH5816 (due 24 Nov 2026, 2:00 pm AEDT). The analysis should be transparent and reproducible, not elaborate.

How to use it:

1. Export this doc as Markdown and save it in the project root as `PLAN.md`.
2. In Claude Code, prompt: *"Read PLAN.md. Set up the project and build notebook 01. Stop after it runs and show me the figures."*
3. Review each notebook before asking for the next one. Check every number you put in the report.
4. Log the prompts you use (see the last section) for the AI-use declaration.

Ground rules for Claude Code:

- Use Jupyter notebooks (`.ipynb`), one per stage, run top to bottom without errors.
- Put reusable functions in `src/gbm_utils.py` and import them; keep notebooks readable.
- Every figure gets a title, labelled axes with units, a legend where needed, and is saved to `figures/` as PNG (300 dpi) and PDF.
- Fix the random seed for all simulations.
- Never hard-code a result into markdown cells; print it from code.
- Do not invent parameter values. Any value set by hand (e.g. the risk-free rate) goes in `config.py` with a comment citing its source.

## Project setup

One folder, one virtual environment, four notebooks run in order.

```
gbm-project/
├── PLAN.md
├── config.py              # tickers, dates, r, seed, horizons
├── requirements.txt
├── src/gbm_utils.py       # shared functions
├── data/raw/              # untouched downloads (CSV)
├── data/clean/            # aligned log returns
├── notebooks/
│   ├── 01_data.ipynb
│   ├── 02_diagnostics.ipynb
│   ├── 03_estimation.ipynb
│   └── 04_application.ipynb
├── figures/
└── tables/                # CSV + LaTeX tables for the report
```

Packages: `yfinance`, `pandas`, `numpy`, `scipy`, `statsmodels`, `matplotlib`, `jupyter`. Pin versions in `requirements.txt`.

`config.py` holds:

| Setting | Value | Note |
| --- | --- | --- |
| `TICKERS` | `{"AU": "VAS.AX", "GL": "VGS.AX"}` | Both ASX-listed, priced in AUD; VGS unhedged |
| `START`, `END` | First common trading day of both ETFs → latest close | Confirm VGS listing date from the data |
| `TRADING_DAYS` | 252 | Annualisation convention |
| `R_ANNUAL` | RBA cash rate or 90-day bank bill rate, continuously compounded | Fill in by hand with source and date |
| `SEED` | 5816 | All simulations |
| `HORIZONS` | 1, 5, 10, 20, 30 years | Application |
| `W0` | 10,000 AUD | Initial wealth |

Matplotlib style: one consistent style for all figures, colourblind-safe palette, font size readable when shrunk to half a page width. Use the same colour for Australia, global and savings throughout.

## Notebook 01: data download and cleaning

Goal: a clean, aligned table of daily log returns for VAS.AX and VGS.AX, with every cleaning step documented for Task 1.

Steps:

1. Download daily data with `yfinance` using `auto_adjust=False` so both Close and Adj Close are kept. Save the raw download to `data/raw/` with the download date in the filename.
2. Record metadata in a printed cell and in `tables/data_summary.csv`: ticker, download date, first/last date, number of observations.
3. Use Adj Close (adjusts for distributions and splits, so it approximates total return). Note in markdown that franking credits are not included.
4. Align the two series on common ASX trading days (inner join). Report how many rows were dropped and why.
5. Check for and report: missing values, zero or repeated prices, duplicated dates, and any absolute daily log return above 10%. Inspect outliers against known events rather than deleting them.
6. Compute daily log returns:

```latex
X_k = \ln\left(\frac{S_{t_k}}{S_{t_{k-1}}}\right)
```

7. Save `data/clean/log_returns.csv`.

Figures:

- **Fig 1:** price paths of both ETFs rebased to 100 at the start date, log scale on the y-axis. Shade the COVID crash (Feb–Mar 2020).
- **Fig 2:** daily log returns over time, two stacked panels sharing the x-axis.

Table: summary of the data (ticker, period, N, cleaning notes).

## Notebook 02: GBM diagnostics

Goal: test each implication of GBM against the data for both ETFs, and report what holds and what fails.

Under GBM, log returns over a step Δt are i.i.d. normal, and the two Brownian motions have constant correlation:

```latex
X_k \overset{\text{iid}}{\sim} \mathcal{N}\left(\left(\mu - \tfrac{1}{2}\sigma^2\right)\Delta t,\ \sigma^2 \Delta t\right), \qquad \operatorname{Corr}(X^{A}_k, X^{G}_k) = \rho
```

Each implication gets one check:

| GBM implication | Check | Output |
| --- | --- | --- |
| Normal log returns | Histogram with fitted normal density; QQ plot; skewness, excess kurtosis, Jarque–Bera test | Fig 3, Table 2 |
| Independent returns | ACF of returns, lags 1–20; Ljung–Box test | Fig 4 (left) |
| Constant volatility | ACF of squared (or absolute) returns; Ljung–Box on squared returns; 63-day rolling annualised volatility | Fig 4 (right), Fig 5 |
| Constant correlation | 126-day rolling correlation between AU and GL returns | Fig 6 |
| Scaling with horizon | Repeat normality stats on weekly and monthly log returns; check variance grows linearly with horizon (variance ratio) | Table 2 |
| Tail behaviour | Count days beyond ±3 and ±4 standard deviations vs the number GBM predicts | Table 2 |

Figures:

- **Fig 3:** 2×2 grid. Top row: histograms of daily log returns with fitted normal overlaid (AU, GL). Bottom row: QQ plots against the normal.
- **Fig 4:** 2×2 grid. ACF of returns and ACF of squared returns for each ETF, with 95% confidence bands.
- **Fig 5:** rolling 63-day annualised volatility for both ETFs on one axis, with the full-sample estimate as a dashed line.
- **Fig 6:** rolling 126-day correlation, with the full-sample ρ as a dashed line.

Table 2: one column per ETF (and per frequency: daily, weekly, monthly). Rows: mean, std dev, skewness, excess kurtosis, Jarque–Bera p-value, Ljung–Box p-values (returns, squared returns), tail counts observed vs expected.

Markdown cells should state in one or two sentences what each figure shows. Leave interpretation for the report to the user.

## Notebook 03: parameter estimation and precision

Goal: estimate μ, σ for each ETF and ρ between them, in annual units, and show how precise and stable each estimate is.

Time unit: years, with Δt = 1/252 for daily data. Let n be the number of returns and T = nΔt the sample length in years.

Maximum likelihood estimators (equivalent to sample moments of log returns):

```latex
\hat\nu = \frac{\bar X}{\Delta t}, \qquad \hat\sigma^2 = \frac{1}{(n-1)\Delta t}\sum_{k=1}^{n}(X_k - \bar X)^2, \qquad \hat\mu = \hat\nu + \tfrac{1}{2}\hat\sigma^2
```

where ν = μ − σ²/2 is the drift of log price. Report both ν̂ and μ̂ and say which one each later calculation uses.

Standard errors under GBM:

```latex
\operatorname{SE}(\hat\nu) \approx \frac{\hat\sigma}{\sqrt{T}}, \qquad \operatorname{SE}(\hat\sigma) \approx \frac{\hat\sigma}{\sqrt{2n}}
```

The first depends only on the length of the sample in years, not the sampling frequency. The second shrinks as sampling gets finer. Print both and make this contrast explicit; it is the central point of the precision discussion.

Steps:

1. Point estimates and 95% confidence intervals for ν, μ, σ (both ETFs), and ρ (Fisher z-transform interval).
2. Robust check: recompute SE(ν̂) with Newey–West (HAC) standard errors, and confidence intervals with a block bootstrap (block length about 20 days, 5,000 resamples). Compare with the i.i.d. intervals; differences reflect the failures found in notebook 02.
3. Test whether the Australian and global drifts differ: estimate the difference in daily log returns, its HAC standard error, and the p-value.
4. Frequency check: re-estimate σ from weekly and monthly returns. Under GBM all three should agree.
5. Stability: estimates by calendar year, and over rolling 2-year windows.
6. Save all estimates to `tables/estimates.csv` and a LaTeX version to `tables/estimates.tex`.

Figures:

- **Fig 7:** annual estimates of μ (left) and σ (right) for both ETFs, each a point with a 95% CI whisker, full-sample estimate as a dashed line. This shows wide, unstable μ against tight σ.
- **Fig 8 (optional):** bootstrap distributions of μ̂ for AU and GL overlaid.

Table 3: parameter, estimate, i.i.d. 95% CI, HAC/bootstrap 95% CI, for ν, μ, σ (each ETF) and ρ.

## Notebook 04: application — savings vs home-biased vs global

Goal: compare long-run wealth outcomes for an Australian investor holding savings, a home-biased equity portfolio, or a globally diversified one, under the real-world measure ℙ, and test how sensitive the conclusions are to estimation error and to GBM itself.

Setup: a fraction π of wealth in equities, split w in Australia and 1 − w global, the rest in savings at constant rate r, rebalanced continuously. Wealth is then a GBM with

```latex
\mu_p = r + \pi\big(w\mu_A + (1-w)\mu_G - r\big), \qquad \sigma_p^2 = \pi^2\big(w^2\sigma_A^2 + (1-w)^2\sigma_G^2 + 2w(1-w)\rho\,\sigma_A\sigma_G\big)
```

so that

```latex
\ln\frac{W_T}{W_0} \sim \mathcal{N}\left(\left(\mu_p - \tfrac12\sigma_p^2\right)T,\ \sigma_p^2 T\right), \qquad \mathbb{P}\left(W_T < W_0 e^{rT}\right) = \Phi\left(-\frac{\left(\mu_p - r - \tfrac12\sigma_p^2\right)\sqrt{T}}{\sigma_p}\right)
```

Portfolios to compare (weights in `config.py`):

| Portfolio | π | w (AU share of equities) | Note |
| --- | --- | --- | --- |
| Savings | 0 | — | Benchmark |
| All Australian | 1 | 1 | Extreme home bias |
| Home-biased | 1 | Typical Australian investor share | User sets value from a cited source |
| Market-cap weight | 1 | Australia's share of world equity | User sets value from a cited source (about 2%) |
| Minimum variance | 1 | w\* from notebook 03 estimates | Computed |

Steps:

1. Analytic results for each portfolio: μ\_p, σ\_p, median terminal wealth, 5th and 95th percentiles, and shortfall probability vs savings at each horizon in `HORIZONS`.
2. Monte Carlo check: simulate correlated GBM paths with daily steps and daily rebalancing (100,000 paths, fixed seed). Confirm results match the analytic formulas.
3. Estimation risk: recompute shortfall probabilities with μ\_A and μ\_G at the ends of their 95% confidence intervals from notebook 03, holding σ and ρ fixed.
4. Model risk: block bootstrap of historical daily returns (block length about 20 days) to simulate terminal wealth without assuming GBM. Compare the left tail (5th and 1st percentiles) with the GBM version.
5. Drawdowns: for each portfolio, maximum drawdown in simulated GBM paths vs historical maximum drawdown.
6. Measure note: add a markdown cell stating that all results are under ℙ. Under the risk-neutral measure ℚ every portfolio drifts at r, so shortfall probabilities under ℚ say nothing about investor outcomes.

Figures:

- **Fig 9:** annualised portfolio volatility σ\_p against Australian weight w (0 to 1), with markers for market-cap weight, home-biased, and minimum-variance portfolios. This is the diversification picture.
- **Fig 10:** wealth fan chart over 30 years from W0 = 10,000 AUD: median line and 5th–95th percentile band for savings, home-biased and global portfolios. Log scale y-axis.
- **Fig 11:** shortfall probability vs horizon (1–30 years), one line per portfolio, with shaded bands from the μ confidence intervals.
- **Fig 12:** 10-year terminal wealth distribution, GBM vs block bootstrap, for the home-biased and global portfolios. Highlight the left tail.

Table 4: for each portfolio at 10 and 30 years: μ\_p, σ\_p, median, 5th percentile, shortfall probability (point and range).

## Figure and table list

About six figures and three tables fit in six pages. Generate all of them, then choose; the "Report" column is a starting suggestion.

| Item | Notebook | Shows | Report task | Report |
| --- | --- | --- | --- | --- |
| Fig 1 | 01 | Rebased prices, log scale | 1 | Yes (small) |
| Fig 2 | 01 | Daily log returns over time | 3 | Merge with Fig 5 or cut |
| Fig 3 | 02 | Histograms + QQ plots | 3 | Yes |
| Fig 4 | 02 | ACF of returns and squared returns | 3 | Yes |
| Fig 5 | 02 | Rolling volatility | 3 | Yes |
| Fig 6 | 02 | Rolling correlation | 3, 5 | Yes (can pair with Fig 5) |
| Fig 7 | 03 | Yearly μ and σ estimates with CIs | 4 | Yes |
| Fig 8 | 03 | Bootstrap distributions of μ̂ | 4 | Cut |
| Fig 9 | 04 | Portfolio volatility vs Australian weight | 5 | Yes |
| Fig 10 | 04 | Wealth fan chart | 5 | Yes |
| Fig 11 | 04 | Shortfall probability vs horizon | 5 | Yes |
| Fig 12 | 04 | GBM vs bootstrap left tail | 5 | Yes, or table |
| Table 1 | 01 | Data summary | 1 | Yes |
| Table 2 | 02 | Descriptive and test statistics | 3 | Yes |
| Table 3 | 03 | Parameter estimates and CIs | 4 | Yes |
| Table 4 | 04 | Portfolio outcomes | 5 | Yes |

To save space, ask Claude Code to combine figures into multi-panel layouts (e.g. Fig 5 and 6 side by side, Fig 10 and 11 side by side) sized for a single report column.

## Checks, reproducibility and AI-use logging

Check the code before trusting any number in the report.

Verification tasks for Claude Code:

- [ ] Simulate a GBM with known μ, σ, ρ, then run the notebook 03 estimators on it. Estimates should land within their confidence intervals.
- [ ] Confirm the Monte Carlo results in notebook 04 match the analytic formulas to within simulation error.
- [ ] Confirm annualisation is consistent: daily σ × √252 matches σ estimated from monthly returns × √12 to within sampling error.
- [ ] Restart the kernel and run all four notebooks in order with no errors.

Checks for you:

- [ ] Re-derive the portfolio μ\_p, σ\_p and shortfall formulas by hand.
- [ ] Spot-check two numbers per table against the notebook output.
- [ ] Check every figure has labelled axes, units and a caption-ready title.

Reproducibility (for the 2-page appendix):

- Python and package versions from `requirements.txt`.
- Tickers, download date, and the exact `yfinance` call.
- Value and source of r, Δt convention, seed, bootstrap block length.
- Ask Claude Code to write a `README.md` listing how to rerun everything.

AI-use log: keep `ai_log.md` in the project. For each session, note the tool (Claude Code, Claude chat), what it was used for, one or two material prompts, and how you checked the output. This becomes the declaration the brief requires.

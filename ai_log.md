# AI-use log

| Date | Tool | Used for | Material prompt(s) | How the output was checked |
| --- | --- | --- | --- | --- |
| 2026-11-10 | Claude Code | Project setup (`config.py`, `src/gbm_utils.py`, requirements, README) and notebook 01 (download, cleaning, Figs 1–2, Table 1) | Uploaded PLAN.md; "Set up the project and build notebook 01. Stop after it runs and show me the figures." | TODO: e.g. spot-check first/last dates and N against the raw CSV; check the 2024-05-10 gap on the ASX/Vanguard site |
| 2026-11-16 | Claude Code | Notebook 02 (GBM diagnostics: Figs 3–6, Table 2, variance-ratio table); diagnostic functions in `src/gbm_utils.py` | "Build notebook 02" | Claude Code tested the variance-ratio function on simulated data (rejection rate ≈5% on i.i.d. data, detects AR(1)); this caught and fixed a missing √n in the z-statistic. TODO: your own spot-checks of Table 2 |

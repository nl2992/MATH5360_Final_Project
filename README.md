# MATH GR5360 Final Project

Trend-following futures research project for Columbia University, Spring 2026.

The repo is now organized around a shared Python engine plus segmented notebooks. The engine holds the formulas and backtest logic; the notebooks are presentation layers for diagnostics, walk-forward testing, performance reporting, and the two-market narrative we want to show in the final project.

## What We Implemented

- A shared research package in `mafn_engine/`
- Segmented notebooks for the original staged workflow
- A one-click master notebook
- A second pair of story notebooks for the professor-facing `TY -> BTC` narrative
- Trend-following strategy implementation for `Channel WithDDControl`
- Statistical diagnostics:
  - Variance Ratio on signed price changes
  - Log-return VR as an appendix check
  - Push-Response diagrams
- Walk-forward optimization and OOS stitching
- Ledger-based performance metrics
- Extended drawdown metrics:
  - `MaxDD`
  - `AvgDD`
  - `CDD(alpha)`
  - drawdown duration
  - recovery time

## Core Narrative

This project is presented as a trend-following project.

The diagnostics are used to locate the time scale of the inefficiency rather than to decide whether the final strategy should be mean-reversion or trend-following.

The intended story is:

- `TY` can look mean-reverting or mixed at short horizons.
- At longer horizons, especially around the professor reference horizon, the variance-ratio curve should be interpreted as bending upward or recovering relative to the earlier decline.
- That longer-horizon behavior is the trend-following property we want to highlight for Treasury futures.
- `BTC` should show a clearer and faster trend-following signature.
- Therefore, `TY` should use slower / longer holding-period trend-following than `BTC`.

Professor reference horizons currently wired into the engine:

- `TY`: `tau = 1440` bars
- `BTC`: `tau = 1152` bars

## Repository Structure

```text
MATH5360_Final_Project/
├── README.md
├── data/
│   ├── TY-5minHLV.csv
│   ├── BTC-5minHLV.csv
│   └── ...
├── mafn_engine/
│   ├── __init__.py
│   ├── config.py
│   ├── diagnostics.py
│   ├── metrics.py
│   ├── strategies.py
│   ├── walkforward.py
│   └── workflow.py
├── notebooks/
│   ├── 00_Master_Pipeline.ipynb
│   ├── 01_Data_and_Statistical_Tests.ipynb
│   ├── 02_Strategy_and_WalkForward.ipynb
│   ├── 03_Performance_Metrics_Extended.ipynb
│   ├── 04_Two_Market_Diagnostics_Story.ipynb
│   ├── 05_Two_Market_Trend_Following_Story.ipynb
│   └── strategy_lib.py
└── tests/
    └── test_engine_smoke.py
```

## Engine Modules

### `mafn_engine/config.py`

- market metadata
- PV / slippage / session settings
- annualization helpers
- default TF / MR grids
- professor reference horizons

### `mafn_engine/diagnostics.py`

- OHLC loading and validation
- session filtering
- variance-ratio test suite
- dense VR curves
- push-response diagrams
- trend-profile summaries

### `mafn_engine/strategies.py`

- `Channel WithDDControl`
- MR backtest support retained internally
- trade ledger construction
- backtest result packaging

### `mafn_engine/walkforward.py`

- IS/OOS splitting
- parameter search
- OOS equity stitching
- walk-forward parameter tables
- extended `T / tau` surface

### `mafn_engine/metrics.py`

- drawdown family calculations
- ledger-based performance metrics

### `mafn_engine/workflow.py`

- reusable story bundles
- `build_market_story(...)`
- `build_pair_story(...)`
- TY-first, BTC-second notebook workflow support

## Notebook Guide

### `00_Master_Pipeline.ipynb`

Runs the main pipeline end to end for one market:

- load data
- run diagnostics
- run TF walk-forward
- compute OOS and full-sample metrics

### `01_Data_and_Statistical_Tests.ipynb`

Main diagnostics notebook.

Use this for:

- data validation
- variance-ratio tables
- push-response tables
- professor-style TY / BTC diagnostic story

### `02_Strategy_and_WalkForward.ipynb`

Main strategy notebook.

Use this for:

- TF sanity checks
- walk-forward parameter selection
- OOS parameter tables

### `03_Performance_Metrics_Extended.ipynb`

Main performance notebook.

Use this for:

- OOS performance metrics
- drawdown family metrics
- full-sample modal TF run
- `T / tau` surface analysis

### `04_Two_Market_Diagnostics_Story.ipynb`

Professor-facing story notebook for diagnostics.

Runs:

1. `TY`
2. `BTC`

and shows:

- dense VR curves
- short-horizon vs reference-horizon push-response figures
- cross-market narrative tables

### `05_Two_Market_Trend_Following_Story.ipynb`

Professor-facing story notebook for the implementation layer.

Runs:

1. `TY`
2. `BTC`

and shows:

- TF walk-forward outputs
- selected TF lookbacks
- OOS equity curves
- full-sample TF summaries

## Recommended Run Order

For the original segmented workflow:

1. `01_Data_and_Statistical_Tests.ipynb`
2. `02_Strategy_and_WalkForward.ipynb`
3. `03_Performance_Metrics_Extended.ipynb`

For the story / presentation workflow:

1. `04_Two_Market_Diagnostics_Story.ipynb`
2. `05_Two_Market_Trend_Following_Story.ipynb`

For an all-in-one single-market run:

1. `00_Master_Pipeline.ipynb`

## Configuration Notes

Common notebook switches:

- `MARKET_SELECT = 'TY'` or `'BTC'`
- `QUICK_TEST = True` for faster dev runs
- `QUICK_TEST = False` for heavier research runs
- `RUN_EXTENDED_SURFACE = True` only when you want the expensive `T / tau` sweep

Current presentation default is trend-following:

- visible notebook workflow uses TF
- the diagnostics still preserve the short-horizon MR / long-horizon TF Treasury interpretation

## Verification Status

Current quick health checks that pass:

- Python modules compile
- notebooks compile cell-by-cell
- smoke tests pass from `tests/test_engine_smoke.py`

These checks cover:

- direct CSV loading
- OOS equity stitching
- drawdown-family sign conventions
- modal config selection
- TF ledger reconciliation
- story-workflow bundle generation

## Known Practical Notes

- Full-history dense diagnostics can be slow, especially for `TY` and `BTC`.
- The story notebooks are designed so the logic lives in the engine and the notebook only renders the artifacts.
- There are generated `__pycache__/` files in the tree right now; if this is going into git cleanly, add or update `.gitignore`.

## References

- Course materials:
  - `Final Project MATH GR5360.pdf`
  - `BasicTradingSystems.doc`
  - `PNL Formula.doc`
  - `DrawDown Measure.pdf`
  - lecture slides, including the variance-ratio and push-response material
- Lo and MacKinlay variance-ratio framework

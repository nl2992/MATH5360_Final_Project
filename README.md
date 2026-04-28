# MATH GR5360 Final Project

Trend-following futures research project for Columbia University, Spring 2026.

This repository now contains:

- a shared Python research engine in `mafn_engine/`
- segmented notebooks for diagnostics, walk-forward testing, and performance analysis
- a C++ trend-following backtester for `TY` and `BTC`
- rendered CSV, figure, and markdown outputs for report-writing

## Assignment Focus

The final project asks us to:

1. understand the chosen futures markets
2. run both statistical Random Walk tests discussed in class:
   - Variance Ratio
   - Push-Response
3. identify the type and approximate time-scale of inefficiency in each market
4. implement the trend-following system `Channel WithDDControl`
5. run a rolling walk-forward experiment:
   - `T = 4 years` in-sample
   - `tau = 1 quarter` out-of-sample
6. record OOS equity and trade-by-trade outputs
7. measure performance and compare OOS vs in-sample / full-sample behavior
8. repeat the process on the secondary market

Primary assignment prompt in the repo:

- [Final Project MATH GR5360.pdf](Final%20Project%20MATH%20GR5360.pdf)

## What We Implemented

### Shared engine

- `mafn_engine/config.py`
  - market metadata
  - point values
  - slippage defaults
  - session filters
  - default parameter grids
- `mafn_engine/diagnostics.py`
  - OHLC loading
  - session filtering
  - Variance Ratio test
  - Push-Response diagrams
  - trend-profile summaries
- `mafn_engine/strategies.py`
  - `Channel WithDDControl`
  - trade ledger construction
  - bar-by-bar equity and drawdown
- `mafn_engine/walkforward.py`
  - rolling `4y -> 1Q` walk-forward optimization
  - OOS stitching
  - parameter tables
- `mafn_engine/metrics.py`
  - performance metrics
  - drawdown-family metrics including `MaxDD`, `AvgDD`, and `CDD(alpha)`
- `mafn_engine/reference_backtest.py`
  - Matlab-parity reference split mode
  - continuous equity / continuous drawdown evaluation
  - fixed `barsBack` support

### Notebook workflow

- `00_Master_Pipeline.ipynb`
- `01_Data_and_Statistical_Tests.ipynb`
- `02_Strategy_and_WalkForward.ipynb`
- `03_Performance_Metrics_Extended.ipynb`
- `04_Two_Market_Diagnostics_Story.ipynb`
- `05_Two_Market_Trend_Following_Story.ipynb`

### C++ workflow

- `cpp/tf_backtest_treasury_btc.cpp`

Modes:

- `walkforward`
- `reference`
- `both`

### Post-processing / report generation

- `scripts/render_cpp_backtest_report.py`

This script reads the C++ outputs and produces:

- growth-of-$1 plots
- underwater plots
- cost / turnover plots
- derived stats tables
- report markdowns

## Core Research Questions And Answers

### 1. What inefficiency are we trying to identify?

Trend-following inefficiency.

The assignment is explicitly trend-following at the strategy level, but the statistical tests still matter because they tell us **where** that trend-following behavior appears in time scale.

### 2. What is the story for Treasury futures (`TY`)?

Short-horizon `TY` behavior can look mean-reverting or mixed.

At longer horizons, the professor’s intended interpretation is that the Variance Ratio curve bends upward / recovers as the horizon gets larger, and Push-Response becomes more trend-consistent. That is the longer-horizon trend-following property we want to highlight.

This is why the Treasury strategy should use slower / longer holding-period trend-following than `BTC`.

### 3. What is the story for Bitcoin futures (`BTC`)?

`BTC` shows a stronger and faster trend-following signature, so the system naturally prefers shorter lookbacks and much faster holding periods than `TY`.

### 4. Did we implement the strategy the way the project requires?

Yes.

We implemented `Channel WithDDControl` in both Python and C++.

We also aligned the engine with the professor’s provided Matlab logic in a separate reference mode:

- one continuous run
- fixed date slices
- fixed `barsBack`
- continuous drawdown carried through OOS
- Matlab-style trade-event counting

### 5. What is the exact OOS workflow?

Rolling walk-forward:

- optimize on the previous `4` years
- apply the best parameter pair to the immediately adjacent next quarter
- record only the OOS equity and OOS trade table
- roll forward one quarter
- repeat

That is the assignment-required structure.

## Current Results Summary

The headline results below come from the canonical official-cost C++ run in `results_cpp_official_quick/`.

Canonical result folders:

- [results_cpp_official_quick/tf_backtest_summary.csv](results_cpp_official_quick/tf_backtest_summary.csv)
- [results_cpp_official_quick_report/final_report_extract.md](results_cpp_official_quick_report/final_report_extract.md)
- [results_cpp_official_quick_report/report_core_metrics.csv](results_cpp_official_quick_report/report_core_metrics.csv)

Legacy mirrored report files under `results_cpp_report/` are kept in sync for convenience, but the `results_cpp_official_quick*` folders are the source of truth.

Master summary table:

- [results_cpp_official_quick/tf_backtest_summary.csv](results_cpp_official_quick/tf_backtest_summary.csv)

Detailed extracted summary:

- [results_cpp_official_quick_report/final_report_extract.md](results_cpp_official_quick_report/final_report_extract.md)
- [results_cpp_official_quick_report/report_core_metrics.csv](results_cpp_official_quick_report/report_core_metrics.csv)
- [results_cpp_official_quick_report/finalReporting.md](results_cpp_official_quick_report/finalReporting.md)

### Walk-forward OOS

| Market | OOS Periods | Modal `L` | Modal `S` | Net Profit | Net MaxDD | Net RoA | Closed Trades |
|---|---:|---:|---:|---:|---:|---:|---:|
| `TY` | 153 | 1440 | 0.01 | $47,618.66 | $30,234.59 | 1.575 | 403 |
| `BTC` | 6 | 288 | 0.01 | $490,398.00 | $138,408.75 | 3.543 | 1005 |

### Full-sample comparison

| Market | `L` | `S` | Net Profit | Net MaxDD | Net RoA | Closed Trades |
|---|---:|---:|---:|---:|---:|---:|
| `TY` | 1440 | 0.01 | $85,134.72 | $15,273.13 | 5.574 | 719 |
| `BTC` | 288 | 0.01 | $1,727,344.50 | $138,408.75 | 12.480 | 4881 |

### OOS decay vs full-sample

| Market | OOS / Full Net Profit | OOS / Full Net RoA |
|---|---:|---:|
| `TY` | 0.559 | 0.283 |
| `BTC` | 0.284 | 0.284 |

Interpretation:

- `TY` remains profitable OOS, but its OOS quality is much weaker than the full-history benchmark.
- `BTC` remains strongly profitable OOS, but still decays materially out of sample.

## Parameter Behavior

### TY

Most common quarterly selections:

- `L = 1440, S = 0.01` selected `19` times
- `L = 1920, S = 0.04` selected `18` times
- `L = 1920, S = 0.03` selected `13` times

Takeaway:

- Treasury futures favor slower trend horizons.
- The dominant lookbacks are in the `1440` to `1920` bar region, which is consistent with the “longer-horizon trend-following” narrative from class.

### BTC

Most common quarterly selections:

- `L = 288, S = 0.01` selected `4` times
- `L = 576, S = 0.01` selected `1` time
- `L = 1152, S = 0.01` selected `1` time

Takeaway:

- Bitcoin trend-following appears at much shorter horizons than Treasury futures.

## Reporting Caveat

The walk-forward OOS equity curve is marked to market bar by bar.

The OOS trade table contains only closed trades.

That means quarter-end unrealized P&L can make equity-curve performance measures differ from trade-table summaries. For the assignment, the main headline numbers should therefore come from the **OOS equity curve**:

- Net Profit
- Worst / Max Drawdown
- RoA
- return volatility
- Sharpe

Trade-level metrics should be presented as complementary diagnostics:

- win rate
- average winner / loser
- profit factor
- duration
- trade count

## Key Artifacts

### Raw result folders

- [results_cpp_official_quick/TY](results_cpp_official_quick/TY)
- [results_cpp_official_quick/BTC](results_cpp_official_quick/BTC)

### Rendered report folders

- [results_cpp_official_quick_report/TY](results_cpp_official_quick_report/TY)
- [results_cpp_official_quick_report/BTC](results_cpp_official_quick_report/BTC)

### Embedded figure gallery

These are the rendered report figures that support the main narrative:

- `TY`: slower, longer-horizon trend-following with weaker but still positive OOS behavior.
- `BTC`: faster, stronger trend-following with much larger gross and net moves, but still meaningful OOS decay.

#### TY figures

| Growth of $1 | Underwater |
|---|---|
| ![TY growth of $1](results_cpp_official_quick_report/TY/TY_reference_growth_of_1.png) | ![TY underwater](results_cpp_official_quick_report/TY/TY_reference_underwater.png) |

| Costs and turnover | Reference OOS growth of $1 |
|---|---|
| ![TY costs and turnover](results_cpp_official_quick_report/TY/TY_reference_costs_turnover.png) | ![TY reference OOS growth of $1](results_cpp_official_quick_report/TY/TY_reference_oos_growth_of_1.png) |

| Reference OOS underwater |
|---|
| ![TY reference OOS underwater](results_cpp_official_quick_report/TY/TY_reference_oos_underwater.png) |

#### BTC figures

| Growth of $1 | Underwater |
|---|---|
| ![BTC growth of $1](results_cpp_official_quick_report/BTC/BTC_reference_growth_of_1.png) | ![BTC underwater](results_cpp_official_quick_report/BTC/BTC_reference_underwater.png) |

| Costs and turnover | Reference OOS growth of $1 |
|---|---|
| ![BTC costs and turnover](results_cpp_official_quick_report/BTC/BTC_reference_costs_turnover.png) | ![BTC reference OOS growth of $1](results_cpp_official_quick_report/BTC/BTC_reference_oos_growth_of_1.png) |

| Reference OOS underwater |
|---|
| ![BTC reference OOS underwater](results_cpp_official_quick_report/BTC/BTC_reference_oos_underwater.png) |

## Recommended Run Order

### Diagnostics and story

1. `04_Two_Market_Diagnostics_Story.ipynb`
2. `05_Two_Market_Trend_Following_Story.ipynb`

### Original staged workflow

1. `01_Data_and_Statistical_Tests.ipynb`
2. `02_Strategy_and_WalkForward.ipynb`
3. `03_Performance_Metrics_Extended.ipynb`

### C++ backtest and report render

```bash
cd "/Users/nigelli/Desktop/Columbia MAFN/26Spring/MATH5360/Final Project/MATH5360_Final_Project"

g++ -std=c++17 -O2 -Wall -Wextra -pedantic cpp/tf_backtest_treasury_btc.cpp -o cpp/tf_backtest_treasury_btc

./cpp/tf_backtest_treasury_btc --mode both --out-dir results_cpp_official_quick

python scripts/render_cpp_backtest_report.py --input-dir results_cpp_official_quick --output-dir results_cpp_official_quick_report --run-kind auto --markets TY,BTC

python scripts/build_official_report_extract.py
```

## Sources And References

### Project sources

- [Final Project MATH GR5360.pdf](Final%20Project%20MATH%20GR5360.pdf)
- professor-provided `main.m` and `ezread.m` reference logic
- lecture material on:
  - Variance Ratio
  - Push-Response
  - drawdown-family risk measures

### Transaction-cost / contract references used in the canonical official run

- [CME Treasury contract specifications](https://www.cmegroup.com/education/courses/introduction-to-treasuries/understand-treasuries-contract-specifications.hideHeader.hideFooter.hideSubnav.hideAddThisExt.educationIframe.html.html)
- [BIS paper on Treasury market liquidity](https://www.bis.org/publ/cgfs11flem.pdf)
- [CME Bitcoin futures rulebook](https://www.cmegroup.com/content/dam/cmegroup/rulebook/CME/IV/350/350.pdf)
- [CME Bitcoin liquidity materials](https://www.cmegroup.com/education/bitcoin/futures-liquidity-report.html)
- [CME fee / clearing references](https://www.cmegroup.com/company/clearing-fees.html)

Important note:

- The assignment itself says the final slippage should come from the project futures-parameter tables.
- The current canonical C++ runs already use the verified official values:
  - `TY`: `$18.625` round-turn
  - `BTC`: `$25.00` round-turn
- If you regenerate older report folders, use `scripts/build_official_report_extract.py` afterward so the mirrored markdown and CSV summaries stay aligned with the canonical official run.

## Current Status

Working now:

- shared Python engine
- professor-parity reference mode
- strict trend-following notebook workflow
- rolling `4y -> 1Q` OOS backtest
- C++ TY / BTC backtester
- rendered report artifacts

Still worth doing for the final presentation:

- final `T` / `tau` sweep across more values
- final PowerPoint packaging and narrative polish

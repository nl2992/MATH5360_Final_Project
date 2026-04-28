# Final Reporting

This file is the exhaustive pick-and-choose reporting layer for the canonical official-cost run. It is intentionally broader than the shorter extracted summary so the group can lift visuals, tables, and exact language directly into slides.

## 1. Fundamental Questions Answered

- `Does Python match C++?` Yes on the canonical parity checks shown below. The engines agree exactly on the full-sample and Matlab-style reference-split checks for both `TY` and `BTC`.
- `What inefficiency do we see?` `TY` is mixed or mean-reverting at short horizons but becomes more trend-consistent at longer horizons; `BTC` is faster and more volatile, with a stronger trend-following implementation outcome and a cleaner longer-horizon showcase PR panel.
- `What is the canonical result set?` The source of truth is [results_cpp_official_quick/tf_backtest_summary.csv](../results_cpp_official_quick/tf_backtest_summary.csv) together with the figures and tables in this folder.
- `What should headline the presentation?` Equity-curve metrics first, trade-table metrics second, because the OOS equity curve is marked to market bar by bar while the trade table contains only closed trades.

## 2. Canonical Run Assumptions

| Market   | Description      | Exchange   |   Point Value |   Round-Turn Cost |   Bars / Session |   Bars / Year | Session Filter      |
|:---------|:-----------------|:-----------|--------------:|------------------:|-----------------:|--------------:|:--------------------|
| TY       | 10-Year Treasury | CBOT-CME   |          1000 |            18.625 |               80 |         20160 | Liquid session only |
| BTC      | Bitcoin          | CME        |             5 |            25     |              288 |        105120 | Full series         |

Important reporting note:

- Walk-forward structure: `4 years` in-sample, `1 quarter` immediately adjacent out-of-sample, rolled forward one quarter at a time.
- Optimization target: `Net Profit / Max Drawdown` (`RoA`).
- `TY` uses the liquid-session filter; `BTC` uses the full 24-hour series.
- Official round-turn costs in the canonical run: `TY = $18.625`, `BTC = $25.00`.

## 3. Python/C++ Parity Checks

| Market   | Check                   | Python Profit   | Cpp Profit    | Python MaxDD   | Cpp MaxDD   |   Python RoA |   Cpp RoA | Python Trades/Units   | Cpp Trades/Units   | Match Profit   | Match MaxDD   | Match RoA   | Match Trades/Units   | All Match   |
|:---------|:------------------------|:----------------|:--------------|:---------------|:------------|-------------:|----------:|:----------------------|:-------------------|:---------------|:--------------|:------------|:---------------------|:------------|
| TY       | full_sample             | $85,134.72      | $85,134.72    | $15,273.13     | $15,273.12  |        5.574 |     5.574 | 719.0                 | 719.0              | True           | True          | True        | True                 | True        |
| TY       | reference_in_sample     | $60,509.44      | $60,509.44    | $12,333.16     | $12,333.16  |        4.906 |     4.906 | 563.0                 | 563.0              | True           | True          | True        | True                 | True        |
| TY       | reference_out_of_sample | $32,191.25      | $32,191.25    | $13,650.44     | $13,650.44  |        2.358 |     2.358 | 185.0                 | 185.0              | True           | True          | True        | True                 | True        |
| BTC      | full_sample             | $1,727,344.50   | $1,727,344.50 | $138,408.75    | $138,408.75 |       12.48  |    12.48  | 4,881.0               | 4,881.0            | True           | True          | True        | True                 | True        |
| BTC      | reference_in_sample     | $717,618.00     | $717,618.00   | $24,366.25     | $24,366.25  |       29.451 |    29.451 | 2,274.0               | 2,274.0            | True           | True          | True        | True                 | True        |
| BTC      | reference_out_of_sample | $421,692.25     | $421,692.25   | $99,860.25     | $99,860.25  |        4.223 |     4.223 | 913.5                 | 913.5              | True           | True          | True        | True                 | True        |

Every row above matched exactly within floating-point tolerance on the rerun parity checks.

### Rolling walk-forward replay check

| Market   |   PythonPeriods |   CppPeriods | PythonNetProfit   | CppNetProfit   | PythonNetMaxDD   | CppNetMaxDD   |   PythonNetRoA |   CppNetRoA |   PythonTrades |   CppTrades |   PythonSharpe |   CppSharpe | ProfitErrPct   | MaxDDErrPct   | RoAErrPct   | TradesErrPct   | SharpeErrPct   | Within10Pct   |
|:---------|----------------:|-------------:|:------------------|:---------------|:-----------------|:--------------|---------------:|------------:|---------------:|------------:|---------------:|------------:|:---------------|:--------------|:------------|:---------------|:---------------|:--------------|
| TY       |             153 |          153 | $47,618.66        | $47,618.66     | $30,234.59       | $30,234.59    |          1.575 |       1.575 |            403 |         403 |          0.228 |       0.228 | 0.000000%      | 0.000000%     | 0.000026%   | 0.000000%      | 0.000483%      | True          |
| BTC      |               6 |            6 | $490,398.00       | $490,398.00    | $138,408.75      | $138,408.75   |          3.543 |       3.543 |           1005 |        1005 |          2.979 |       2.98  | 0.000000%      | 0.000000%     | 0.000004%   | 0.000000%      | 0.005191%      | True          |

This check replays the exact C++ quarterly parameter table in Python and compares the stitched OOS result. Both markets are comfortably within the requested `10%` tolerance; in practice they are essentially exact.

## 4. Diagnostics Story

### Reference-horizon composite

![Reference diagnostics](../results_diagnostics_story/two_market_diagnostics_reference.png)

### Showcase composite

![Showcase diagnostics](../results_diagnostics_story/two_market_diagnostics_showcase.png)

### Additional diagnostics visuals

![VR recovery summary](overview/vr_recovery_summary.png)

![Push-response rho summary](overview/push_response_rho_summary.png)

Variance-ratio recovery summary:

| Market   |   Trough q |   Trough VR |   Reference q |   Reference VR |   Showcase q |   Showcase VR |   Last q |   Last VR |   Recovery to Reference |   Recovery to Showcase |   Recovery to Last |
|:---------|-----------:|------------:|--------------:|---------------:|-------------:|--------------:|---------:|----------:|------------------------:|-----------------------:|-------------------:|
| TY       |        800 |       0.888 |          1440 |          0.911 |         1440 |         0.911 |     4800 |     0.949 |                   0.023 |                  0.023 |              0.061 |
| BTC      |       2474 |       0.817 |          1152 |          0.835 |         3456 |         0.841 |     5760 |     0.889 |                   0.018 |                  0.024 |              0.072 |

Push-response summary:

| Ticker   | Kind      |   TauBars | TauScale   |    Rho |   PValue | Pattern     |
|:---------|:----------|----------:|:-----------|-------:|---------:|:------------|
| TY       | short     |        80 | 1.0sess    |  0.082 |    0.811 | trend       |
| TY       | reference |      1440 | 18.0sess   |  0.591 |    0.056 | trend       |
| TY       | showcase  |      1440 | 18.0sess   |  0.591 |    0.056 | trend       |
| BTC      | short     |       288 | 1.0d       | -0.382 |    0.247 | mean_revert |
| BTC      | reference |      1152 | 4.0d       | -0.464 |    0.151 | mean_revert |
| BTC      | showcase  |      3456 | 12.0d      |  0.673 |    0.023 | trend       |

- `TY`: the VR curve bottoms near `q = 800` and recovers by `+0.023` by the professor reference horizon `q = 1440`. Reference-horizon push-response is positive with `rho = 0.591`, supporting the slower long-horizon TF story. The canonical walk-forward run then settles on modal `L = 1440`, `S = 0.01`.
- `BTC`: short-horizon PR is mixed, but the longer showcase horizon `tau = 3456` bars produces `rho = 0.673` while the VR curve recovers `+0.024` from its trough. The C++ walk-forward run still prefers a much faster TF configuration, modal `L = 288`, `S = 0.01`.

## 5. Headline Backtest Results

| Market   | RunType         |    L |    S | NetProfit     | NetMaxDD    |   NetRoA | NetAnnReturn   | NetAnnVol   |   NetAnnSharpe |   ClosedTrades |
|:---------|:----------------|-----:|-----:|:--------------|:------------|---------:|:---------------|:------------|---------------:|---------------:|
| TY       | walkforward_oos | 1440 | 0.01 | $47,618.66    | $30,234.59  |    1.575 | 1.02%          | 5.02%       |          0.228 |            403 |
| TY       | full_sample     | 1440 | 0.01 | $85,134.72    | $15,273.12  |    5.574 | 1.47%          | 3.87%       |          0.396 |            719 |
| BTC      | walkforward_oos |  288 | 0.01 | $490,398.00   | $138,408.75 |    3.543 | 226.68%        | 42.77%      |          2.98  |           1005 |
| BTC      | full_sample     |  288 | 0.01 | $1,727,344.50 | $138,408.75 |   12.48  | 67.75%         | 11.18%      |          4.684 |           4881 |

### High-level comparison visuals

![OOS decay ratios](overview/oos_decay_ratios.png)

![Reference vs walkforward comparison](overview/reference_vs_walkforward.png)

![Transaction-cost burden](overview/transaction_cost_burden.png)

![Drawdown family comparison](overview/drawdown_family_comparison.png)

Drawdown-family table:

| Market   | RunKind     | MaxDD       | AvgDD      | CDD         |   DD Duration (bars) |   Recovery (bars) |
|:---------|:------------|:------------|:-----------|:------------|---------------------:|------------------:|
| TY       | walkforward | $30,234.59  | $9,130.60  | $26,358.60  |               261355 |            113175 |
| TY       | fullsample  | $15,273.12  | $4,973.39  | $13,432.92  |               226951 |             68994 |
| BTC      | walkforward | $138,408.75 | $28,276.61 | $120,312.91 |                39053 |             25756 |
| BTC      | fullsample  | $138,408.75 | $8,368.66  | $73,181.28  |                24166 |             10869 |

Out-of-sample decay table:

| Market   |   Profit Ratio OOS/Full |   RoA Ratio OOS/Full |   Sharpe Ratio OOS/Full |   Trades Ratio OOS/Full |
|:---------|------------------------:|---------------------:|------------------------:|------------------------:|
| TY       |                   0.559 |                0.283 |                   0.576 |                   0.561 |
| BTC      |                   0.284 |                0.284 |                   0.636 |                   0.206 |

## 6. TY Deep Dive

- `TY` is the slower market. The diagnostics argue for longer-horizon TF, and the walk-forward selections cluster around `L = 1440` to `1920` bars.
- This is the market where the professor’s “VR falls first, then bends upward at longer horizons” story is most important.

![TY walkforward growth](TY/TY_walkforward_growth_of_1.png)

![TY walkforward underwater](TY/TY_walkforward_underwater.png)

![TY walkforward costs and turnover](TY/TY_walkforward_costs_turnover.png)

![TY quarterly OOS panel](TY/TY_walkforward_quarterly_panel.png)

![TY parameter stability](TY/TY_walkforward_parameter_stability.png)

![TY parameter frequency](TY/TY_walkforward_parameter_frequency.png)

![TY parameter heatmap](TY/TY_walkforward_parameter_heatmap.png)

![TY reference growth](TY/TY_reference_growth_of_1.png)

![TY reference OOS growth](TY/TY_reference_oos_growth_of_1.png)

## 7. BTC Deep Dive

- `BTC` is the faster market. The implementation outcome is much stronger, but the diagnostics still matter because short-horizon PR is mixed and the cleaner TF case emerges at the later showcase horizon.
- The canonical walk-forward run selects `L = 288` most often, with `576` and `1152` appearing in the stronger later periods.

![BTC walkforward growth](BTC/BTC_walkforward_growth_of_1.png)

![BTC walkforward underwater](BTC/BTC_walkforward_underwater.png)

![BTC walkforward costs and turnover](BTC/BTC_walkforward_costs_turnover.png)

![BTC quarterly OOS panel](BTC/BTC_walkforward_quarterly_panel.png)

![BTC parameter stability](BTC/BTC_walkforward_parameter_stability.png)

![BTC parameter frequency](BTC/BTC_walkforward_parameter_frequency.png)

![BTC parameter heatmap](BTC/BTC_walkforward_parameter_heatmap.png)

![BTC reference growth](BTC/BTC_reference_growth_of_1.png)

![BTC reference OOS growth](BTC/BTC_reference_oos_growth_of_1.png)

## 8. Cost Sensitivity

![Combined cost sensitivity](overview/cost_sensitivity_overview.png)

### TY cost-sensitivity assets

![TY profit sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_profit.png)

![TY RoA sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_roa.png)

![TY Sharpe sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_sharpe.png)

### BTC cost-sensitivity assets

![BTC profit sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_profit.png)

![BTC RoA sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_roa.png)

![BTC Sharpe sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_sharpe.png)

Cost sensitivity summary:

| Ticker   |   CostMultiplier | Total Profit   |   Sharpe Ratio |   Return on Account |
|:---------|-----------------:|:---------------|---------------:|--------------------:|
| TY       |              0   | $56,195.47     |          0.262 |               2.014 |
| TY       |              0.5 | $51,907.06     |          0.245 |               1.787 |
| TY       |              1   | $47,618.66     |          0.228 |               1.575 |
| TY       |              2   | $39,041.84     |          0.193 |               1.198 |
| BTC      |              0   | $515,535.50    |          3.127 |               3.779 |
| BTC      |              0.5 | $502,966.75    |          3.053 |               3.66  |
| BTC      |              1   | $490,398.00    |          2.979 |               3.543 |
| BTC      |              2   | $465,260.50    |          2.833 |               3.314 |

## 9. Quarterly Extremes And Parameter Behavior

| Market   | Label   |   Period | OOSStart         | OOSEnd           |    L |    S | NetProfit   | NetMaxDD    |   NetRoA |   ClosedTrades |
|:---------|:--------|---------:|:-----------------|:-----------------|-----:|-----:|:------------|:------------|---------:|---------------:|
| TY       | best    |       44 | 07/07/1998 13:30 | 10/06/1998 12:05 | 1920 | 0.03 | $7,347.06   | $1,781.25   |    4.125 |              1 |
| TY       | worst   |      105 | 12/26/2013 07:55 | 03/27/2014 10:20 | 3200 | 0.04 | -$5,109.06  | $5,365.38   |   -0.952 |              2 |
| BTC      | best    |        6 | 09/24/2025 11:50 | 02/08/2026 23:15 | 1152 | 0.01 | $130,296.25 | $18,668.75  |    6.979 |             99 |
| BTC      | worst   |        5 | 05/14/2025 02:50 | 09/24/2025 11:45 |  288 | 0.01 | -$66,023.75 | $138,408.75 |   -0.477 |            146 |

## 10. Asset Index

This table is meant to help the group choose which visuals to keep in the final deck.

| Asset                                     | Section     | Purpose                                                                 | Suggested Slide Use          |
|:------------------------------------------|:------------|:------------------------------------------------------------------------|:-----------------------------|
| two_market_diagnostics_reference.png      | Diagnostics | Reference-horizon VR + Push-Response panels for TY and BTC.             | Time-series story            |
| two_market_diagnostics_showcase.png       | Diagnostics | Showcase-horizon diagnostics emphasizing the later cleaner BTC PR view. | Time-series story / appendix |
| overview/vr_recovery_summary.png          | Overview    | VR curves with trough and marked longer-horizon recovery points.        | Explain TY long-horizon TF   |
| overview/push_response_rho_summary.png    | Overview    | Short/reference/showcase push-response rho values.                      | Explain PR sign changes      |
| overview/oos_decay_ratios.png             | Overview    | OOS/full decay for profit, RoA, Sharpe, and trades.                     | Performance summary          |
| overview/reference_vs_walkforward.png     | Overview    | Compare the single reference split with the rolling assignment OOS run. | Methodology comparison       |
| overview/transaction_cost_burden.png      | Overview    | Total cost and cost share of gross profit across canonical runs.        | Cost framing                 |
| overview/drawdown_family_comparison.png   | Overview    | MaxDD, AvgDD, and CDD across TY/BTC and OOS/full sample.                | Risk framing                 |
| overview/cost_sensitivity_overview.png    | Overview    | Profit, RoA, and Sharpe under 0x/0.5x/1x/2x cost assumptions.           | Robustness                   |
| TY/TY_walkforward_quarterly_panel.png     | TY          | Quarter-by-quarter TY OOS profit and RoA.                               | Quarter dynamics             |
| TY/TY_walkforward_parameter_heatmap.png   | TY          | Frequency heatmap of chosen TY L/S pairs.                               | Parameter behavior           |
| BTC/BTC_walkforward_quarterly_panel.png   | BTC         | Quarter-by-quarter BTC OOS profit and RoA.                              | Quarter dynamics             |
| BTC/BTC_walkforward_parameter_heatmap.png | BTC         | Frequency heatmap of chosen BTC L/S pairs.                              | Parameter behavior           |

## 11. Supporting Files

- Core metrics: [report_core_metrics.csv](report_core_metrics.csv)
- Short extracted summary: [final_report_extract.md](final_report_extract.md)
- Overview table from the C++ renderer: [cpp_backtest_report_overview.csv](cpp_backtest_report_overview.csv)
- Walk-forward summary: [../results_cpp_official_quick/tf_backtest_summary.csv](../results_cpp_official_quick/tf_backtest_summary.csv)
- Overview asset manifest: [overview/asset_manifest.csv](overview/asset_manifest.csv)
- Parity check table: [overview/parity_check.csv](overview/parity_check.csv)
- Walk-forward replay comparison: [overview/walkforward_python_cpp_comparison.csv](overview/walkforward_python_cpp_comparison.csv)
- Drawdown family summary: [overview/drawdown_family_summary.csv](overview/drawdown_family_summary.csv)
- Quarter extremes: [overview/quarter_extremes.csv](overview/quarter_extremes.csv)

## 12. Sources

- [Final Project MATH GR5360.pdf](../Final%20Project%20MATH%20GR5360.pdf)
- professor-provided `main.m` and `ezread.m`
- course lecture material on Variance Ratio, Push-Response, and drawdown-family measures
- official course parameter sheets used for transaction-cost assumptions
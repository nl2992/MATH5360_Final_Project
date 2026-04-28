# Final Report Extract

## 1. Experimental Setup

- Strategy: `Channel WithDDControl` trend-following system.
- Markets:
  - Primary: `TY` (10-Year Treasury Note futures)
  - Secondary: `BTC` (CME Bitcoin futures)
- Data frequency: `5-minute` OHLC bars.
- Session handling:
  - `TY` uses the project liquid-session filter already embedded in the engine.
  - `BTC` uses the full 24-hour series.
- Walk-forward assignment experiment:
  - In-sample window `T = 4 years`
  - Out-of-sample window `tau = 1 quarter`
  - Each quarter is optimized on the immediately preceding 4 years and then traded on the adjacent next quarter.
- Optimization target: `Net Profit / Max Drawdown` (`RoA`).
- Transaction-cost assumptions used in the canonical official run:
  - `TY`: `$18.625` round-turn per contract
  - `BTC`: `$25.00` round-turn per contract
- Important reporting note:
  - The walk-forward OOS equity curve is marked to market bar by bar.
  - The OOS trade table contains only closed trades.
  - Therefore, quarter-end unrealized P&L can make equity-curve performance measures stronger or weaker than trade-table summaries in a given run.
  - For the assignment, the primary headline comparison should therefore use the OOS equity-curve statistics (`Net Profit`, `Max Drawdown`, `RoA`, return volatility, Sharpe), with trade-level metrics presented as complementary diagnostics.

## 2. Walk-Forward Out-of-Sample Results

### TY walk-forward OOS

- Date range: `06/29/1987 12:40` to `03/18/2026 11:15`
- OOS periods: `153`
- Story / modal configuration: `L = 1440`, `S = 0.01`
- Net Profit: `$47,618.66`
- Net Max Drawdown: `$30,234.59`
- Net RoA: `1.575`
- Annualized net return: `1.02%`
- Annualized net volatility: `5.02%`
- Annualized net Sharpe: `0.228`
- Closed trades: `403`
- Win rate: `31.27%`
- Average winner: `$1,176.62`
- Average loser: `-920.53`
- Profit factor: `0.581`
- Average trade duration: `922.9` bars
- Total transaction cost paid: `$8,576.81`
- Turnover: `921.0` contracts

### BTC walk-forward OOS

- Date range: `11/19/2023 21:05` to `02/08/2026 23:15`
- OOS periods: `6`
- Story / modal configuration: `L = 288`, `S = 0.01`
- Net Profit: `$490,398.00`
- Net Max Drawdown: `$138,408.75`
- Net RoA: `3.543`
- Annualized net return: `226.68%`
- Annualized net volatility: `42.77%`
- Annualized net Sharpe: `2.980`
- Closed trades: `1,005`
- Win rate: `41.79%`
- Average winner: `$4,446.57`
- Average loser: `-2,357.00`
- Profit factor: `1.354`
- Average trade duration: `33.0` bars
- Total transaction cost paid: `$25,137.50`
- Turnover: `2,011.0` contracts

## 3. Full-Sample Comparison

### TY full-sample

- Full-sample configuration: `L = 1440`, `S = 0.01`
- Net Profit: `$85,134.72`
- Net Max Drawdown: `$15,273.12`
- Net RoA: `5.574`
- Annualized net return: `1.47%`
- Annualized net volatility: `3.87%`
- Annualized net Sharpe: `0.396`
- Closed trades: `719`
- Win rate: `41.31%`
- Average winner: `$1,168.21`
- Average loser: `-620.43`
- Profit factor: `1.325`

### BTC full-sample

- Full-sample configuration: `L = 288`, `S = 0.01`
- Net Profit: `$1,727,344.50`
- Net Max Drawdown: `$138,408.75`
- Net RoA: `12.480`
- Annualized net return: `67.75%`
- Annualized net volatility: `11.18%`
- Annualized net Sharpe: `4.684`
- Closed trades: `4,881`
- Win rate: `44.27%`
- Average winner: `$2,161.78`
- Average loser: `-1,082.98`
- Profit factor: `1.586`

## 4. OOS vs Full-Sample Decay

### TY

- OOS / full-sample net profit ratio: `0.559`
- OOS / full-sample net RoA ratio: `0.283`
- OOS / full-sample trade-count ratio: `0.561`

### BTC

- OOS / full-sample net profit ratio: `0.284`
- OOS / full-sample net RoA ratio: `0.284`
- OOS / full-sample trade-count ratio: `0.206`

## 5. Parameter Behavior by Quarter

### TY

- Most frequent quarterly selections:
  - `L = 1440, S = 0.01` selected `19` times
  - `L = 1920, S = 0.04` selected `18` times
  - `L = 1920, S = 0.03` selected `13` times

### BTC

- Most frequent quarterly selections:
  - `L = 288, S = 0.01` selected `4` times
  - `L = 576, S = 0.01` selected `1` times
  - `L = 1152, S = 0.01` selected `1` times

## 6. Best and Worst OOS Quarters

### TY

- Best OOS quarter by net objective:
  - Period `44`
  - `07/07/1998 13:30` to `10/06/1998 12:05`
  - `L = 1920`, `S = 0.030`
  - Net Profit: `$7,347.06`
  - Net MaxDD: `$1,781.25`
  - Net Objective: `4.125`

- Worst OOS quarter by net objective:
  - Period `105`
  - `12/26/2013 07:55` to `03/27/2014 10:20`
  - `L = 3200`, `S = 0.040`
  - Net Profit: `-$5,109.06`
  - Net MaxDD: `$5,365.38`
  - Net Objective: `-0.952`

### BTC

- Best OOS quarter by net objective:
  - Period `6`
  - `09/24/2025 11:50` to `02/08/2026 23:15`
  - `L = 1152`, `S = 0.010`
  - Net Profit: `$130,296.25`
  - Net MaxDD: `$18,668.75`
  - Net Objective: `6.979`

- Worst OOS quarter by net objective:
  - Period `5`
  - `05/14/2025 02:50` to `09/24/2025 11:45`
  - `L = 288`, `S = 0.010`
  - Net Profit: `-$66,023.75`
  - Net MaxDD: `$138,408.75`
  - Net Objective: `-0.477`

## 7. Matlab-Parity Reference Split Appendix

### TY reference split

- Auto split:
  - In-sample: `12/12/1983 10:40` to `06/26/2013 13:55`
  - OOS: `06/27/2013 07:25` to `04/10/2026 13:55`
  - `barsBack = 17001`
- Best reference configuration: `L = 1280`, `S = 0.01`
- Reference OOS net profit: `$32,191.25`
- Reference OOS net max drawdown: `$13,650.44`
- Reference OOS net RoA: `2.358`

### BTC reference split

- Auto split:
  - In-sample: `03/15/2018 23:15` to `10/12/2023 23:55`
  - OOS: `10/13/2023 00:00` to `04/10/2026 16:00`
  - `barsBack = 17001`
- Best reference configuration: `L = 576`, `S = 0.01`
- Reference OOS net profit: `$421,692.25`
- Reference OOS net max drawdown: `$99,860.25`
- Reference OOS net RoA: `4.223`

## 8. Supporting Files

- Core metrics table: [report_core_metrics.csv](report_core_metrics.csv)
- C++ master summary: [tf_backtest_summary.csv](results_cpp_official_quick/tf_backtest_summary.csv)
- Overview report table: [cpp_backtest_report_overview.csv](cpp_backtest_report_overview.csv)

## 9. Sources And Assumptions

- [Final Project MATH GR5360.pdf](../Final%20Project%20MATH%20GR5360.pdf)
- professor-provided `main.m` and `ezread.m`
- course lecture material on Variance Ratio, Push-Response, and drawdown-family measures
- Official `TF Data` sheet values used in the canonical run:
  - `TY` slippage = `$18.625` round-turn
  - `BTC` slippage = `$25.00` round-turn

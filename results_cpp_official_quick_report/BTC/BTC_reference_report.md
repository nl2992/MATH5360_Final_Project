# BTC C++ Backtest Report

- Market: BTC
- Run kind: reference
- Gross series: bar-by-bar PnL before transaction costs.
- Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.
- Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.
- Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.
- Round-turn cost per contract: 25.000000
- Cost note: Official TF Data BTC round-turn cost = $25.00 per contract.
- Reference split: IS 12/18/2017 to 10/12/2023, OOS 10/13/2023 to 04/10/2026, barsBack=17001.
- Reference date source: auto_dates.
- Best reference TF parameters: L=576, S=0.010000.

## Headline Metrics (Equity Curve)

| Market   | RunKind   | StartTime           | EndTime             |   Bars |   GrossProfit |   NetProfit |   TotalCost |   TurnoverContracts |   TurnoverNotional |   GrossMaxDD |   NetMaxDD |   TradeUnits |   GrossAnnVol |   NetAnnVol |   GrossSharpe |   NetSharpe |   GrossCAGR |   NetCAGR |   RoundTurnCost | CostNote                                                    |   GrossRoA |   NetRoA |   GrossStDevCpp |   NetStDevCpp |
|:---------|:----------|:--------------------|:--------------------|-------:|--------------:|------------:|------------:|--------------------:|-------------------:|-------------:|-----------:|-------------:|--------------:|------------:|--------------:|------------:|------------:|----------:|----------------:|:------------------------------------------------------------|-----------:|---------:|----------------:|--------------:|
| BTC      | reference | 2017-12-18 00:35:00 | 2026-04-10 16:00:00 | 590436 |     1.219e+06 | 1.13931e+06 |     79687.5 |                6375 |        1.24176e+09 |      98485.2 |    99860.2 |       3187.5 |      0.105571 |    0.112588 |       4.40257 |     4.03632 |    0.582886 |   0.56541 |              25 | Official TF Data BTC round-turn cost = $25.00 per contract. |    32.7246 |  29.4513 |          146.76 |       146.807 |

These are the headline metrics because the equity curve is marked to market bar by bar. Closed-trade statistics are useful, but secondary.

## Secondary Trade Metrics

|   TotalTrades |   WinRatePct |   AvgWinner |   AvgLoser |   ProfitFactor |   AvgDurationBars |
|--------------:|-------------:|------------:|-----------:|---------------:|------------------:|
|          3187 |       44.305 |     2244.31 |   -1144.32 |        1.56105 |           21.4766 |

## Files

- Growth of $1: `BTC_reference_growth_of_1.png`
- Underwater: `BTC_reference_underwater.png`
- Costs and turnover: `BTC_reference_costs_turnover.png`
- Parameter stability: `BTC_walkforward_parameter_stability.png`
- Parameter frequency: `BTC_walkforward_parameter_frequency.png`
- Reference OOS growth: `BTC_reference_oos_growth_of_1.png`
- Reference OOS underwater: `BTC_reference_oos_underwater.png`
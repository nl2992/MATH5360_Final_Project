# TY C++ Backtest Report

- Market: TY
- Run kind: walkforward
- Gross series: bar-by-bar PnL before transaction costs.
- Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.
- Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.
- Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.
- Round-turn cost per contract: 18.625000
- Cost note: Official TF Data TY round-turn cost = $18.625 per contract.

## Headline Metrics (Equity Curve)

| Market   | RunKind     | StartTime           | EndTime             |   Bars |   GrossProfit |   NetProfit |   TotalCost |   TurnoverContracts |   TurnoverNotional |   GrossMaxDD |   NetMaxDD |   TradeUnits |   GrossAnnVol |   NetAnnVol |   GrossSharpe |   NetSharpe |   GrossCAGR |   NetCAGR |   RoundTurnCost | CostNote                                                    |   GrossRoA |   NetRoA |   GrossStDevCpp |   NetStDevCpp |
|:---------|:------------|:--------------------|:--------------------|-------:|--------------:|------------:|------------:|--------------------:|-------------------:|-------------:|-----------:|-------------:|--------------:|------------:|--------------:|------------:|------------:|----------:|----------------:|:------------------------------------------------------------|-----------:|---------:|----------------:|--------------:|
| TY       | walkforward | 1987-06-29 12:40:00 | 2026-03-18 11:15:00 | 771120 |       56195.5 |     47618.7 |     8576.81 |                 921 |        1.05428e+08 |      27903.1 |    30234.6 |        460.5 |      0.048979 |   0.0502144 |      0.262333 |    0.227813 |   0.0117205 |  0.010234 |          18.625 | Official TF Data TY round-turn cost = $18.625 per contract. |    2.01395 |  1.57497 |         41.8536 |       41.8713 |

These are the headline metrics because the equity curve is marked to market bar by bar. Closed-trade statistics are useful, but secondary.

## Secondary Trade Metrics

|   TotalTrades |   WinRatePct |   AvgWinner |   AvgLoser |   ProfitFactor |   AvgDurationBars |
|--------------:|-------------:|------------:|-----------:|---------------:|------------------:|
|           403 |      31.2655 |     1176.62 |    -920.53 |        0.58142 |           922.873 |

## Files

- Growth of $1: `TY_walkforward_growth_of_1.png`
- Underwater: `TY_walkforward_underwater.png`
- Costs and turnover: `TY_walkforward_costs_turnover.png`
- Parameter stability: `TY_walkforward_parameter_stability.png`
- Parameter frequency: `TY_walkforward_parameter_frequency.png`
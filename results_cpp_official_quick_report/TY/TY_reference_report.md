# TY C++ Backtest Report

- Market: TY
- Run kind: reference
- Gross series: bar-by-bar PnL before transaction costs.
- Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.
- Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.
- Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.
- Round-turn cost per contract: 18.625000
- Cost note: Official TF Data TY round-turn cost = $18.625 per contract.
- Reference split: IS 01/03/1983 to 06/26/2013, OOS 06/27/2013 to 04/10/2026, barsBack=17001.
- Reference date source: auto_dates.
- Best reference TF parameters: L=1280, S=0.010000.

## Headline Metrics (Equity Curve)

| Market   | RunKind   | StartTime           | EndTime             |   Bars |   GrossProfit |   NetProfit |   TotalCost |   TurnoverContracts |   TurnoverNotional |   GrossMaxDD |   NetMaxDD |   TradeUnits |   GrossAnnVol |   NetAnnVol |   GrossSharpe |   NetSharpe |   GrossCAGR |   NetCAGR |   RoundTurnCost | CostNote                                                    |   GrossRoA |   NetRoA |   GrossStDevCpp |   NetStDevCpp |
|:---------|:----------|:--------------------|:--------------------|-------:|--------------:|------------:|------------:|--------------------:|-------------------:|-------------:|-----------:|-------------:|--------------:|------------:|--------------:|------------:|------------:|----------:|----------------:|:------------------------------------------------------------|-----------:|---------:|----------------:|--------------:|
| TY       | reference | 1983-01-03 08:05:00 | 2026-04-10 13:55:00 | 853091 |        106632 |     92700.7 |     13931.5 |                1496 |        1.65355e+08 |      12179.1 |    13650.4 |          748 |     0.0374719 |   0.0391187 |       0.47622 |    0.415582 |   0.0172963 |  0.015619 |          18.625 | Official TF Data TY round-turn cost = $18.625 per contract. |    5.94499 |  4.90624 |         39.3954 |       39.4224 |

These are the headline metrics because the equity curve is marked to market bar by bar. Closed-trade statistics are useful, but secondary.

## Secondary Trade Metrics

|   TotalTrades |   WinRatePct |   AvgWinner |   AvgLoser |   ProfitFactor |   AvgDurationBars |
|--------------:|-------------:|------------:|-----------:|---------------:|------------------:|
|           748 |      41.1765 |     1183.49 |   -617.762 |        1.34104 |            635.67 |

## Files

- Growth of $1: `TY_reference_growth_of_1.png`
- Underwater: `TY_reference_underwater.png`
- Costs and turnover: `TY_reference_costs_turnover.png`
- Parameter stability: `TY_walkforward_parameter_stability.png`
- Parameter frequency: `TY_walkforward_parameter_frequency.png`
- Reference OOS growth: `TY_reference_oos_growth_of_1.png`
- Reference OOS underwater: `TY_reference_oos_underwater.png`
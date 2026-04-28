# BTC C++ Backtest Report

- Market: BTC
- Run kind: walkforward
- Gross series: bar-by-bar PnL before transaction costs.
- Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.
- Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.
- Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.
- Round-turn cost per contract: 25.000000
- Cost note: Official TF Data BTC round-turn cost = $25.00 per contract.

## Headline Metrics (Equity Curve)

| Market   | RunKind     | StartTime           | EndTime             |   Bars |   GrossProfit |   NetProfit |   TotalCost |   TurnoverContracts |   TurnoverNotional |   GrossMaxDD |   NetMaxDD |   TradeUnits |   GrossAnnVol |   NetAnnVol |   GrossSharpe |   NetSharpe |   GrossCAGR |   NetCAGR |   RoundTurnCost | CostNote                                                    |   GrossRoA |   NetRoA |   GrossStDevCpp |   NetStDevCpp |
|:---------|:------------|:--------------------|:--------------------|-------:|--------------:|------------:|------------:|--------------------:|-------------------:|-------------:|-----------:|-------------:|--------------:|------------:|--------------:|------------:|------------:|----------:|----------------:|:------------------------------------------------------------|-----------:|---------:|----------------:|--------------:|
| BTC      | walkforward | 2023-11-19 21:05:00 | 2026-02-08 23:15:00 | 157680 |        515536 |      490398 |     25137.5 |                2011 |        8.07362e+08 |       136434 |     138409 |       1005.5 |      0.414702 |    0.427681 |       3.12675 |     2.97955 |     2.35876 |   2.26684 |              25 | Official TF Data BTC round-turn cost = $25.00 per contract. |    3.77865 |  3.54311 |          396.87 |       396.975 |

These are the headline metrics because the equity curve is marked to market bar by bar. Closed-trade statistics are useful, but secondary.

## Secondary Trade Metrics

|   TotalTrades |   WinRatePct |   AvgWinner |   AvgLoser |   ProfitFactor |   AvgDurationBars |
|--------------:|-------------:|------------:|-----------:|---------------:|------------------:|
|          1005 |       41.791 |     4446.57 |      -2357 |        1.35443 |            32.999 |

## Files

- Growth of $1: `BTC_walkforward_growth_of_1.png`
- Underwater: `BTC_walkforward_underwater.png`
- Costs and turnover: `BTC_walkforward_costs_turnover.png`
- Parameter stability: `BTC_walkforward_parameter_stability.png`
- Parameter frequency: `BTC_walkforward_parameter_frequency.png`
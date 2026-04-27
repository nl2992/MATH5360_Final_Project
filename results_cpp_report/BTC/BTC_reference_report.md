# BTC C++ Backtest Report

- Market: BTC
- Run kind: reference
- Gross series: bar-by-bar PnL before transaction costs.
- Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.
- Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.
- Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.
- Round-turn cost per contract: 50.000000
- Cost note: Default BTC round-turn cost = $50.00 = two CME BTC ticks ($25 each), a conservative liquid-hours baseline.
- Reference split: IS 12/18/2017 to 10/12/2023, OOS 10/13/2023 to 04/10/2026, barsBack=17001.
- Reference date source: auto_dates.
- Best reference TF parameters: L=576, S=0.010000.

## Derived Stats

| Market   | RunKind   | StartTime           | EndTime             |   Bars |   GrossProfit |   NetProfit |   TotalCost |   TurnoverContracts |   TurnoverNotional |   GrossMaxDD |   NetMaxDD |   TradeUnits |   GrossAnnVol |   NetAnnVol |   GrossSharpe |   NetSharpe |   GrossCAGR |   NetCAGR |   RoundTurnCost | CostNote                                                                                                   |   GrossRoA |   NetRoA |   GrossStDevCpp |   NetStDevCpp |
|:---------|:----------|:--------------------|:--------------------|-------:|--------------:|------------:|------------:|--------------------:|-------------------:|-------------:|-----------:|-------------:|--------------:|------------:|--------------:|------------:|------------:|----------:|----------------:|:-----------------------------------------------------------------------------------------------------------|-----------:|---------:|----------------:|--------------:|
| BTC      | reference | 2017-12-18 00:35:00 | 2026-04-10 16:00:00 | 590436 |     1.219e+06 | 1.05962e+06 |      159375 |                6375 |        1.24176e+09 |      98485.2 |     101235 |       3187.5 |      0.105571 |    0.120731 |       4.40257 |     3.67374 |    0.582886 |  0.546978 |              50 | Default BTC round-turn cost = $50.00 = two CME BTC ticks ($25 each), a conservative liquid-hours baseline. |    32.7246 |  26.3609 |          146.76 |       146.866 |

## Embedded Figures

### Full reference-sample growth of $1

![BTC growth of $1](BTC_reference_growth_of_1.png)

### Full reference-sample underwater curve

![BTC underwater](BTC_reference_underwater.png)

### Transaction costs and turnover

![BTC costs and turnover](BTC_reference_costs_turnover.png)

### Reference OOS growth of $1

![BTC reference OOS growth of $1](BTC_reference_oos_growth_of_1.png)

### Reference OOS underwater curve

![BTC reference OOS underwater](BTC_reference_oos_underwater.png)

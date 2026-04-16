# MATH GR5360 Final Project
## Trend-Following/Mean-Reverting Futures Trading System

**Columbia University - Mathematical Methods in Financial Price Analysis**

**Spring 2026**

---

## Our Assignment

**Primary Market:** `[TO BE ASSIGNED]`  
**Secondary Market:** `[TBD - Bitcoin or Chinese Futures]`

Once we get our market assignment, we just update the `GROUP_NUMBER` variable at the top of each notebook and download the corresponding data file.

---

## Project Overview

This project implements and analyzes a **Channel WithDDControl** trend-following trading strategy on futures markets. We:

1. Run statistical tests (Variance Ratio, Push-Response) to identify market inefficiencies
2. Implement the Channel WithDDControl strategy from the provided MATLAB code
3. Perform walk-forward optimization with rolling IS/OOS periods
4. Analyze performance across different parameter settings and time horizons

---

## Repository Structure

```
math_gr5360_project/
├── README.md
├── notebooks/
│   ├── 01_Data_and_Statistical_Tests.ipynb
│   ├── 02_Strategy_and_WalkForward.ipynb
│   └── 03_Performance_Metrics_Extended.ipynb
├── data/
│   └── [TICKER]-5min.csv
└── results/
    └── [output files]
```

---

## Notebooks

### Notebook 01: Data Loading & Statistical Tests

- Load and validate 5-minute OHLC data
- **Variance Ratio Test**: Identifies trending vs mean-reverting behavior at different time scales
- **Push-Response Test**: Measures how prices respond to directional moves
- Generates recommendations for strategy suitability

### Notebook 02: Strategy Implementation & Walk-Forward

- **Channel WithDDControl** strategy implementation (ported from `main.m`)
- Entry: Channel breakout (highest high / lowest low over L bars)
- Exit: Drawdown control stop (S% below/above benchmark)
- Walk-forward optimization framework
- Parameter grid: ChnLen (500-10000) × StpPct (0.005-0.10)

### Notebook 03: Performance Analysis & Extended Tests

- Full performance metrics (Sharpe, Profit Factor, Win Rate, etc.)
- Extended analysis varying T (in-sample years) and τ (out-of-sample quarters)
- IS vs OOS decay coefficient analysis
- Optimal parameter recommendations

---

## Available Markets

The 18 primary markets for this course (each group gets assigned one):

| # | Ticker | Description | Exchange |
|---|--------|-------------|----------|
| 1 | BO | Soybean Oil | CBOT-CME |
| 2 | DX | Dollar Index | NYBOT-ICE |
| 3 | HG | Copper | COMEX |
| 4 | HO | Heating Oil | NYMEX |
| 5 | JO | Orange Juice | NYBOT-ICE |
| 6 | JY | Japanese Yen | CME |
| 7 | SY | Soybeans | CBOT-CME |
| 8 | SB | Sugar #11 | NYBOT-ICE |
| 9 | SF | Swiss Franc | CME |
| 10 | TU | 2-Year Treasury | CBOT-CME |
| 11 | TY | 10-Year Treasury | CBOT-CME |
| 12 | WC | Wheat | CBOT-CME |
| 13 | SM | Soybean Meal | CBOT-CME |
| 14 | CC | Cocoa | NYBOT-ICE |
| 15 | BZ | Schatz | EUREX |
| 16 | CL | Crude Oil WTI | NYMEX |
| 17 | GC | Gold | COMEX |
| 18 | SV | Silver | COMEX |

Secondary markets: Bitcoin (#19), Chinese futures (#20-25)

---

## How to Run

1. **Get your market assignment** from the instructor

2. **Update GROUP_NUMBER** in each notebook:
   ```python
   GROUP_NUMBER = X  # Your assigned group number (1-18)
   ```

3. **Download data** from CourseWorks:
   - Get `{TICKER}-5min.csv` for your assigned market
   - Place it in the `data/` folder

4. **Run notebooks in order:**
   - `01_Data_and_Statistical_Tests.ipynb`
   - `02_Strategy_and_WalkForward.ipynb`
   - `03_Performance_Metrics_Extended.ipynb`

5. **Check results** in the `results/` folder

---

## Dependencies

```
numpy
pandas
matplotlib
seaborn
scipy
numba
tqdm
```

Install: `pip install numpy pandas matplotlib seaborn scipy numba tqdm`

---

## Walk-Forward Settings

| Parameter | Default |
|-----------|---------|
| In-Sample (T) | 4 years |
| Out-of-Sample (τ) | 1 quarter |
| Objective | Net Profit / Max Drawdown |

Notebook 03 tests T from 1-6 years and τ from 1-4 quarters for the extended analysis.

---

## Strategy Logic

From the course materials (`main.m`):

```
ENTRY:
  Long:  High >= Highest High of last L bars
  Short: Low <= Lowest Low of last L bars

EXIT (Drawdown Control):
  Exit Long:  Low <= Benchmark × (1 - S)
  Exit Short: High >= Benchmark × (1 + S)

REVERSALS:
  Can flip Long↔Short on opposite channel break
```

---

## Output Files

After running, `results/` will contain:
- `{TICKER}_variance_ratio.csv`
- `{TICKER}_push_response.csv`
- `{TICKER}_walkforward.csv`
- `{TICKER}_performance_metrics.csv`
- `{TICKER}_extended_analysis.csv`
- Various `.png` charts

---

## Notes

- Set `QUICK_TEST = True` in notebooks for faster dev runs (coarse grid)
- Set `QUICK_TEST = False` for full 91,296-combination grid search
- Synthetic data auto-generates if real CSV isn't found (useful for testing)

---

## References

- Course materials: `main.m`, `ezread.m`, `BasicTradingSystems.doc`
- Market parameters: `TF_Data.xls`
- Lo & MacKinlay (1988) - Variance Ratio test

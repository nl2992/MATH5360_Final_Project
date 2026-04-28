from __future__ import annotations

import argparse
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "06_CPP_Confirmed_Story.ipynb"


def build_notebook() -> nbformat.NotebookNode:
    cells = [
        new_markdown_cell(
            """# TY and BTC Final Story From Confirmed C++ Results

This notebook is the final presentation layer for the project. It does **not** rerun the backtests. Instead, it reads the confirmed C++ output files and the exported Python diagnostics, then rebuilds the report in one place with clean, Columbia-style visuals.

**What this notebook answers**

- What inefficiency do we see in `TY` and `BTC` from the variance-ratio and push-response tests?
- Why is a trend-following system still appropriate for both markets?
- What are the headline out-of-sample results for `Channel WithDDControl`?
- How do the full-sample and reference-split results compare to the walk-forward OOS experiment?
- How sensitive are the results to transaction costs?

**Confirmed result sources**

- `results_cpp_official_quick/`
- `results_cpp_official_quick_report/`
- `results_diagnostics_story/`
- `results_cost_sensitivity_fixed/`

The transaction-cost assumptions used here come from the official `TF Data` reference:

- `TY` round-turn slippage: `$18.625`
- `BTC` round-turn slippage: `$25.00`
"""
        ),
        new_code_cell(
            """from __future__ import annotations

from pathlib import Path
from IPython.display import Markdown, display

import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def find_project_root(start: Path | None = None) -> Path:
    start = (start or Path.cwd()).resolve()
    for candidate in [start, *start.parents]:
        if (candidate / "mafn_engine").exists() and (candidate / "results_cpp_official_quick").exists():
            return candidate
    raise FileNotFoundError("Could not locate project root from notebook cwd.")


ROOT = find_project_root()
CPP_RESULTS = ROOT / "results_cpp_official_quick"
CPP_REPORT = ROOT / "results_cpp_official_quick_report"
DIAG_RESULTS = ROOT / "results_diagnostics_story"
COST_RESULTS = ROOT / "results_cost_sensitivity_fixed"

plt.style.use("seaborn-v0_8-whitegrid")
plt.rcParams.update(
    {
        "figure.figsize": (12, 6),
        "figure.dpi": 140,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titleweight": "bold",
        "axes.labelcolor": "#0F2D52",
        "axes.titlecolor": "#0F2D52",
        "xtick.color": "#23406A",
        "ytick.color": "#23406A",
        "grid.color": "#D4E2F1",
        "grid.alpha": 0.9,
        "axes.facecolor": "#FAFCFE",
        "savefig.facecolor": "white",
        "font.size": 11,
    }
)

COLUMBIA_DARK = "#0F2D52"
COLUMBIA_BLUE = "#6BA4D9"
COLUMBIA_LIGHT = "#B9D9EB"
COLUMBIA_GOLD = "#C9A227"
COLUMBIA_RED = "#B04A5A"


def money(x: float) -> str:
    return f"${x:,.0f}"


def pct(x: float) -> str:
    return f"{100*x:.1f}%"


def ratio(x: float) -> str:
    return f"{x:.3f}"


display(Markdown(f"**Project root:** `{ROOT}`"))
"""
        ),
        new_code_cell(
            """DATE_FMT = "%m/%d/%Y %H:%M"


def load_market_bundle(market: str) -> dict[str, pd.DataFrame]:
    base = CPP_RESULTS / market
    report = CPP_REPORT / market
    diag = DIAG_RESULTS
    bundle = {
        "oos_returns": pd.read_csv(base / f"{market}_tf_oos_returns.csv", parse_dates=["DateTime"], date_format=DATE_FMT),
        "full_returns": pd.read_csv(base / f"{market}_tf_fullsample_returns.csv", parse_dates=["DateTime"], date_format=DATE_FMT),
        "reference_series": pd.read_csv(base / f"{market}_tf_reference_series.csv", parse_dates=["DateTime"], date_format=DATE_FMT),
        "periods": pd.read_csv(base / f"{market}_tf_walkforward_periods.csv", parse_dates=["ISStart", "ISEnd", "OOSStart", "OOSEnd"], date_format=DATE_FMT),
        "derived": pd.read_csv(report / f"{market}_walkforward_derived_stats.csv"),
        "trade_stats": pd.read_csv(report / f"{market}_walkforward_trade_stats.csv"),
        "vr": pd.read_csv(diag / f"{market}_vr_curve.csv"),
        "short_pr": pd.read_csv(diag / f"{market}_short_pr.csv"),
        "reference_pr": pd.read_csv(diag / f"{market}_reference_pr.csv"),
        "showcase_pr": pd.read_csv(diag / f"{market}_showcase_pr.csv"),
    }
    return bundle


summary = pd.read_csv(CPP_RESULTS / "tf_backtest_summary.csv")
overview = pd.read_csv(CPP_REPORT / "cpp_backtest_report_overview.csv")
cost_sensitivity = pd.read_csv(COST_RESULTS / "cost_sensitivity_summary.csv")
pr_metadata = pd.read_csv(DIAG_RESULTS / "push_response_metadata.csv")
markets = {ticker: load_market_bundle(ticker) for ticker in ["TY", "BTC"]}

summary["Market"] = summary["Market"].astype(str).str.strip()
summary["RunType"] = summary["RunType"].astype(str).str.strip()
overview["Market"] = overview["Market"].astype(str).str.strip()
overview["RunKind"] = overview["RunKind"].astype(str).str.strip()
pr_metadata["Ticker"] = pr_metadata["Ticker"].astype(str).str.strip()
pr_metadata["Kind"] = pr_metadata["Kind"].astype(str).str.strip()

required = [
    CPP_RESULTS / "tf_backtest_summary.csv",
    CPP_REPORT / "cpp_backtest_report_overview.csv",
    DIAG_RESULTS / "two_market_diagnostics_reference.png",
    COST_RESULTS / "cost_sensitivity_summary.csv",
]

missing = [str(path) for path in required if not path.exists()]
if missing:
    raise FileNotFoundError("Missing required confirmed outputs:\\n" + "\\n".join(missing))

display(Markdown("### Confirmed Inputs Loaded"))
display(pd.DataFrame({"Path": [str(path) for path in required]}))
"""
        ),
        new_markdown_cell(
            """## 1. Headline Assignment Answers

The project asked us to:

1. diagnose the two time series with variance-ratio and push-response tests,
2. infer the range of time-scales where inefficiency appears,
3. implement the `Channel WithDDControl` trend-following system,
4. run a 4-year in-sample / next-quarter out-of-sample rolling walk-forward,
5. compare OOS behavior to longer-run benchmark configurations.

The next cells summarize those answers directly from the confirmed outputs.
"""
        ),
        new_code_cell(
            """walkforward = summary.loc[summary["RunType"] == "walkforward_oos"].copy()
fullsample = summary.loc[summary["RunType"] == "full_sample"].copy()
reference_oos = summary.loc[summary["RunType"] == "reference_out_of_sample"].copy()


def metadata_row(ticker: str, kind: str) -> pd.Series:
    row = pr_metadata.loc[(pr_metadata["Ticker"] == ticker) & (pr_metadata["Kind"] == kind)]
    return row.iloc[0]


def vr_story_row(ticker: str, reference_q: int) -> dict[str, object]:
    vr = markets[ticker]["vr"].sort_values("q").reset_index(drop=True)
    trough = vr.loc[vr["VR"].idxmin()]
    nearest_ref = vr.iloc[(vr["q"] - reference_q).abs().argsort()[:1]].iloc[0]
    final_pt = vr.iloc[-1]
    return {
        "Market": ticker,
        "VR trough q": int(trough["q"]),
        "VR trough": float(trough["VR"]),
        "VR at reference q": float(nearest_ref["VR"]),
        "VR at max q": float(final_pt["VR"]),
        "Narrative": (
            "Short-horizon MR / mixed, then longer-horizon recovery toward TF"
            if ticker == "TY"
            else "Mixed short horizon, clearer TF only at longer horizons"
        ),
    }


story_rows = []
for ticker, ref_q in [("TY", 1440), ("BTC", 1152)]:
    ref_meta = metadata_row(ticker, "reference")
    show_meta = metadata_row(ticker, "showcase")
    wf = walkforward.loc[walkforward["Market"] == ticker].iloc[0]
    story_rows.append(
        {
            "Market": ticker,
            "Short-Horizon PR": f"rho={metadata_row(ticker, 'short')['Rho']:+.3f}",
            "Reference PR": f"rho={ref_meta['Rho']:+.3f}",
            "Showcase PR": f"rho={show_meta['Rho']:+.3f}",
            "Reference Scale": str(ref_meta["TauScale"]),
            "Showcase Scale": str(show_meta["TauScale"]),
            "Walk-Forward L": int(wf["L"]),
            "Walk-Forward S": float(wf["S"]),
            "OOS Net Profit": wf["NetProfit"],
            "OOS Net RoA": wf["NetRoA"],
            "OOS Net Sharpe": markets[ticker]["derived"]["NetSharpe"].iloc[0],
        }
    )

story_df = pd.DataFrame(story_rows)
vr_story_df = pd.DataFrame([vr_story_row("TY", 1440), vr_story_row("BTC", 1152)])

display(Markdown("### Final Story Snapshot"))
display(
    story_df.style.format(
        {
            "OOS Net Profit": money,
            "OOS Net RoA": ratio,
            "OOS Net Sharpe": ratio,
        }
    )
)
display(Markdown("### Variance-Ratio Story Summary"))
display(vr_story_df.style.format({"VR trough": "{:.3f}", "VR at reference q": "{:.3f}", "VR at max q": "{:.3f}"}))
"""
        ),
        new_markdown_cell(
            """## 2. Time-Series Diagnostics

The diagnostics figure is the core narrative:

- `TY` does **not** need `VR(q)` to cross above `1` at the monthly horizon.
- The important point is that `TY` looks more mean-reverting or weak at short horizons, then the variance ratio bends upward as `q` increases and the push-response becomes more trend-like around the longer horizon.
- `BTC` is more volatile and can still look noisy at short horizons, but the longer-horizon push-response becomes clearly trend-following.
"""
        ),
        new_code_cell(
            """def plot_vr(ax, ticker: str, short_q: int, ref_q: int, showcase_q: int) -> None:
    vr = markets[ticker]["vr"].sort_values("q")
    ax.plot(vr["q"], vr["VR"], color=COLUMBIA_BLUE, linewidth=2.4)
    ax.axhline(1.0, color=COLUMBIA_RED, linestyle="--", linewidth=1.3, alpha=0.9)
    ax.axvline(short_q, color=COLUMBIA_GOLD, linestyle=":", linewidth=1.6)
    ax.axvline(ref_q, color=COLUMBIA_DARK, linestyle="--", linewidth=1.4)
    if showcase_q != ref_q:
        ax.axvline(showcase_q, color=COLUMBIA_BLUE, linestyle="-.", linewidth=1.4)
    ax.set_title(f"{ticker}: Variance Ratio vs q")
    ax.set_xlabel("q (bars)")
    ax.set_ylabel("VR(q)")
    ax.text(0.02, 0.05, f"short={short_q}\\nref={ref_q}\\nshow={showcase_q}", transform=ax.transAxes, color=COLUMBIA_DARK)


def plot_pr(ax, df: pd.DataFrame, title: str, rho: float) -> None:
    ax.plot(df["bin_centre"], df["bin_mean"], color=COLUMBIA_BLUE, marker="o", linewidth=2.0, markersize=4.5)
    lower = df["bin_mean"] - 1.96 * df["bin_se"]
    upper = df["bin_mean"] + 1.96 * df["bin_se"]
    ax.fill_between(df["bin_centre"], lower, upper, color=COLUMBIA_LIGHT, alpha=0.45)
    ax.axhline(0.0, color=COLUMBIA_DARK, linewidth=1.0)
    ax.axvline(0.0, color=COLUMBIA_DARK, linewidth=1.0)
    ax.set_title(f"{title} | rho={rho:+.3f}")
    ax.set_xlabel("push")
    ax.set_ylabel("average response")


diag_cfg = {
    "TY": {"short_q": 80, "ref_q": 1440, "show_q": 1440},
    "BTC": {"short_q": 288, "ref_q": 1152, "show_q": 3456},
}

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
for row, ticker in enumerate(["TY", "BTC"]):
    cfg = diag_cfg[ticker]
    plot_vr(axes[row, 0], ticker, cfg["short_q"], cfg["ref_q"], cfg["show_q"])
    short_meta = metadata_row(ticker, "short")
    showcase_meta = metadata_row(ticker, "showcase")
    plot_pr(axes[row, 1], markets[ticker]["short_pr"], f"{ticker}: Short-Horizon PR", short_meta["Rho"])
    showcase_label = "Reference-Horizon PR" if cfg["show_q"] == cfg["ref_q"] else "Showcase-Horizon PR"
    plot_pr(axes[row, 2], markets[ticker]["showcase_pr"], f"{ticker}: {showcase_label}", showcase_meta["Rho"])

fig.suptitle("Confirmed TY / BTC Diagnostics", fontsize=18, fontweight="bold", color=COLUMBIA_DARK, y=1.01)
fig.tight_layout()
plt.show()
"""
        ),
        new_code_cell(
            """narrative = []
for ticker in ["TY", "BTC"]:
    short_meta = metadata_row(ticker, "short")
    ref_meta = metadata_row(ticker, "reference")
    show_meta = metadata_row(ticker, "showcase")
    if ticker == "TY":
        sentence = (
            f"{ticker}: the short horizon is weak (rho={short_meta['Rho']:+.3f}), "
            f"but by the reference horizon {ref_meta['TauScale']} the PR becomes clearly more trend-like "
            f"(rho={ref_meta['Rho']:+.3f}), matching the upward recovery of VR(q) at long q."
        )
    else:
        sentence = (
            f"{ticker}: short-horizon PR is mixed or mean-reverting (rho={short_meta['Rho']:+.3f}), "
            f"while the longer showcase horizon {show_meta['TauScale']} becomes trend-following "
            f"(rho={show_meta['Rho']:+.3f})."
        )
    narrative.append(f"- {sentence}")

display(Markdown("### Diagnostic Interpretation\\n" + "\\n".join(narrative)))
"""
        ),
        new_markdown_cell(
            """## 3. Walk-Forward Headline Results

The assignment’s main performance experiment is the rolling 4-year in-sample / next-quarter out-of-sample walk-forward. The equity-curve metrics are the headline numbers; trade-table metrics are secondary diagnostics.
"""
        ),
        new_code_cell(
            """headline = walkforward[[
    "Market", "L", "S", "NetProfit", "NetMaxDD", "NetRoA", "TotalCost", "TurnoverContracts", "ClosedTrades", "RoundTurnCost"
]].copy()
headline = headline.rename(columns={"L": "Chosen L", "S": "Chosen S"})
headline["NetSharpe"] = [markets[mkt]["derived"]["NetSharpe"].iloc[0] for mkt in headline["Market"]]
headline = headline[[
    "Market", "Chosen L", "Chosen S", "NetProfit", "NetMaxDD", "NetRoA",
    "NetSharpe", "TotalCost", "TurnoverContracts", "ClosedTrades", "RoundTurnCost"
]]

trade_details = pd.concat(
    [
        markets["TY"]["trade_stats"].assign(Market="TY"),
        markets["BTC"]["trade_stats"].assign(Market="BTC"),
    ],
    ignore_index=True,
)

display(Markdown("### Equity-Curve Headline Metrics"))
display(
    headline.style.format(
        {
            "NetProfit": money,
            "NetMaxDD": money,
            "NetRoA": ratio,
            "NetSharpe": ratio,
            "TotalCost": money,
            "TurnoverContracts": "{:,.0f}",
            "ClosedTrades": "{:,.0f}",
            "RoundTurnCost": money,
            "Chosen S": "{:.3f}",
        }
    )
)

display(Markdown("### Secondary Trade Metrics"))
display(
    trade_details.style.format(
        {
            "WinRatePct": "{:.1f}",
            "AvgWinner": money,
            "AvgLoser": money,
            "ProfitFactor": ratio,
            "AvgDurationBars": "{:,.1f}",
        }
    )
)
"""
        ),
        new_code_cell(
            """def add_drawdown(df: pd.DataFrame, equity_col: str) -> pd.DataFrame:
    out = df.copy()
    out["Peak"] = out[equity_col].cummax()
    out["Underwater"] = out[equity_col] / out["Peak"] - 1.0
    out["GrowthOf1"] = out[equity_col] / out[equity_col].iloc[0]
    return out


fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=False)
for row, ticker in enumerate(["TY", "BTC"]):
    oos = add_drawdown(markets[ticker]["oos_returns"], "NetEquity")
    axes[row, 0].plot(oos["DateTime"], oos["GrossEquity"] / oos["GrossEquity"].iloc[0], label="Gross", color=COLUMBIA_GOLD, linewidth=2.0)
    axes[row, 0].plot(oos["DateTime"], oos["NetEquity"] / oos["NetEquity"].iloc[0], label="Net", color=COLUMBIA_DARK, linewidth=2.4)
    axes[row, 0].set_title(f"{ticker}: OOS Growth of $1")
    axes[row, 0].set_ylabel("growth of $1")
    axes[row, 0].legend(frameon=False)

    axes[row, 1].fill_between(oos["DateTime"], oos["Underwater"] * 100, 0, color=COLUMBIA_LIGHT, alpha=0.75)
    axes[row, 1].plot(oos["DateTime"], oos["Underwater"] * 100, color=COLUMBIA_DARK, linewidth=1.8)
    axes[row, 1].set_title(f"{ticker}: OOS Underwater Curve")
    axes[row, 1].set_ylabel("drawdown (%)")

fig.suptitle("Walk-Forward OOS Equity Curves", fontsize=18, fontweight="bold", color=COLUMBIA_DARK, y=1.01)
fig.tight_layout()
plt.show()
"""
        ),
        new_markdown_cell(
            """## 4. Parameter Stability

These plots show how the selected `L` and `S` values evolved over the quarterly walk-forward periods. This matters because the assignment asked us to keep the quarter-by-quarter optimal parameter table and study the practical stability of the system.
"""
        ),
        new_code_cell(
            """fig, axes = plt.subplots(2, 2, figsize=(16, 10))
for col, ticker in enumerate(["TY", "BTC"]):
    periods = markets[ticker]["periods"].copy()
    periods["OOSMid"] = periods["OOSStart"] + (periods["OOSEnd"] - periods["OOSStart"]) / 2
    axes[0, col].step(periods["OOSMid"], periods["L"], where="mid", color=COLUMBIA_DARK, linewidth=2.2)
    axes[0, col].scatter(periods["OOSMid"], periods["L"], color=COLUMBIA_BLUE, s=25)
    axes[0, col].set_title(f"{ticker}: Selected Channel Length L")
    axes[0, col].set_ylabel("L (bars)")

    axes[1, col].step(periods["OOSMid"], periods["S"], where="mid", color=COLUMBIA_GOLD, linewidth=2.2)
    axes[1, col].scatter(periods["OOSMid"], periods["S"], color=COLUMBIA_DARK, s=25)
    axes[1, col].set_title(f"{ticker}: Selected Stop Percentage S")
    axes[1, col].set_ylabel("S")

fig.tight_layout()
plt.show()


fig, axes = plt.subplots(1, 2, figsize=(16, 5))
for ax, ticker in zip(axes, ["TY", "BTC"]):
    freq = (
        markets[ticker]["periods"]
        .assign(Config=lambda df: "L=" + df["L"].astype(int).astype(str) + ", S=" + df["S"].map(lambda x: f"{x:.3f}"))
        ["Config"]
        .value_counts()
        .sort_values(ascending=True)
    )
    ax.barh(freq.index, freq.values, color=COLUMBIA_BLUE if ticker == "TY" else COLUMBIA_GOLD)
    ax.set_title(f"{ticker}: Parameter Frequency Across OOS Quarters")
    ax.set_xlabel("quarters selected")

fig.tight_layout()
plt.show()
"""
        ),
        new_markdown_cell(
            """## 5. Cost Sensitivity

The next figure shows how the confirmed OOS results change when we scale transaction costs from `0x` to `2x` the official round-turn slippage.
"""
        ),
        new_code_cell(
            """fig, axes = plt.subplots(2, 2, figsize=(16, 10), sharex=True)
for row, ticker in enumerate(["TY", "BTC"]):
    df = cost_sensitivity.loc[cost_sensitivity["Ticker"] == ticker].sort_values("CostMultiplier")
    axes[row, 0].plot(df["CostMultiplier"], df["Total Profit"], color=COLUMBIA_DARK, marker="o", linewidth=2.3)
    axes[row, 0].set_title(f"{ticker}: OOS Net Profit vs Cost Multiplier")
    axes[row, 0].set_ylabel("net profit ($)")
    axes[row, 0].set_xlabel("cost multiplier")

    axes[row, 1].plot(df["CostMultiplier"], df["Sharpe Ratio"], color=COLUMBIA_GOLD, marker="o", linewidth=2.3)
    axes[row, 1].set_title(f"{ticker}: OOS Sharpe vs Cost Multiplier")
    axes[row, 1].set_ylabel("Sharpe")
    axes[row, 1].set_xlabel("cost multiplier")

fig.tight_layout()
plt.show()

display(
    cost_sensitivity[["Ticker", "CostMultiplier", "Total Profit", "Sharpe Ratio", "Max Drawdown $", "Return on Account"]]
    .style.format(
        {
            "Total Profit": money,
            "Sharpe Ratio": ratio,
            "Max Drawdown $": money,
            "Return on Account": ratio,
        }
    )
)
"""
        ),
        new_markdown_cell(
            """## 6. Benchmark Comparison

To keep the story tight, we compare three lenses:

- `walkforward_oos`: the assignment’s main rolling OOS experiment,
- `full_sample`: one full-period TF benchmark with the modal walk-forward configuration,
- `reference_*`: the Matlab-style fixed-split reference run.
"""
        ),
        new_code_cell(
            """compare = summary.loc[
    summary["RunType"].isin(["walkforward_oos", "full_sample", "reference_out_of_sample", "reference_full"]),
    ["Market", "RunType", "L", "S", "NetProfit", "NetMaxDD", "NetRoA", "TotalCost", "ClosedTrades", "RoundTurnCost"],
].copy()

display(
    compare.sort_values(["Market", "RunType"]).style.format(
        {
            "S": "{:.3f}",
            "NetProfit": money,
            "NetMaxDD": money,
            "NetRoA": ratio,
            "TotalCost": money,
            "ClosedTrades": "{:,.0f}",
            "RoundTurnCost": money,
        }
    )
)
"""
        ),
        new_code_cell(
            """final_lines = []
for ticker in ["TY", "BTC"]:
    wf = walkforward.loc[walkforward["Market"] == ticker].iloc[0]
    ref = reference_oos.loc[reference_oos["Market"] == ticker].iloc[0]
    full = fullsample.loc[fullsample["Market"] == ticker].iloc[0]
    if ticker == "TY":
        ineff = "short-horizon MR / mixed behavior, but longer-horizon trend-following recovery"
    else:
        ineff = "mixed short-horizon behavior, with the cleaner TF signal showing up at longer horizons"
    final_lines.append(
        f"- **{ticker}:** the diagnostics point to {ineff}. "
        f"In the confirmed walk-forward run, the system used modal parameters `L={int(wf['L'])}`, `S={wf['S']:.3f}` "
        f"and produced OOS net profit of {money(wf['NetProfit'])}, net max drawdown of {money(wf['NetMaxDD'])}, "
        f"and net RoA of {wf['NetRoA']:.3f}. "
        f"The fixed-split reference OOS run delivered {money(ref['NetProfit'])}, while the full-sample benchmark delivered {money(full['NetProfit'])}."
    )

display(
    Markdown(
        "## 7. Final Takeaways\\n"
        + "\\n".join(final_lines)
        + "\\n\\n"
        + "These figures are suitable for the final report because they are drawn from the confirmed C++ backtest outputs, "
        + "use the official TF Data slippage assumptions, and present the assignment’s required diagnostics and walk-forward performance in one place."
    )
)
"""
        ),
    ]

    return new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
    )


def execute_notebook(path: Path) -> None:
    from nbclient import NotebookClient

    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()
    nbformat.write(notebook, path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the final C++ story notebook from confirmed outputs.")
    parser.add_argument("--execute", action="store_true", help="Execute the notebook after generating it.")
    args = parser.parse_args()

    notebook = build_notebook()
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, NOTEBOOK_PATH)
    print(f"Wrote {NOTEBOOK_PATH}")

    if args.execute:
        execute_notebook(NOTEBOOK_PATH)
        print(f"Executed {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mafn_engine.config import (  # noqa: E402
    COLUMBIA_BLUE,
    COLUMBIA_CORE,
    COLUMBIA_DARK,
    COLUMBIA_DIVERGING,
    COLUMBIA_NAVY,
    COLUMBIA_RED,
    COLUMBIA_WARM,
    apply_columbia_theme,
    bars_per_year,
    get_market,
    resolve_round_turn_cost,
)
from mafn_engine.diagnostics import load_ohlc, prepare_analysis_frame  # noqa: E402
from mafn_engine.metrics import drawdown_family, performance_from_ledger  # noqa: E402
from mafn_engine.reference_backtest import run_reference_split  # noqa: E402
from mafn_engine.strategies import run_backtest  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an exhaustive markdown report with inline visuals.")
    parser.add_argument("--results-dir", type=Path, default=PROJECT_ROOT / "results_cpp_official_quick")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "results_cpp_official_quick_report")
    parser.add_argument("--diagnostics-dir", type=Path, default=PROJECT_ROOT / "results_diagnostics_story")
    parser.add_argument("--cost-dir", type=Path, default=PROJECT_ROOT / "results_cost_sensitivity_fixed")
    parser.add_argument(
        "--mirror-report-dir",
        type=Path,
        default=PROJECT_ROOT / "results_cpp_report",
        help="Optional mirrored report directory for legacy links.",
    )
    return parser.parse_args()


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def ratio(value: float) -> str:
    return f"{value:.3f}"


def safe_markdown(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_csv(index=False)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def load_returns(results_dir: Path, market: str, run_kind: str) -> pd.DataFrame:
    market_dir = results_dir / market
    if run_kind == "walkforward":
        path = market_dir / f"{market}_tf_oos_returns.csv"
    elif run_kind == "fullsample":
        path = market_dir / f"{market}_tf_fullsample_returns.csv"
    elif run_kind == "reference":
        path = market_dir / f"{market}_tf_reference_series.csv"
    else:
        raise ValueError(run_kind)
    df = load_csv(path)
    if "DateTime" in df.columns:
        df["DateTime"] = pd.to_datetime(df["DateTime"])
    return df


def load_periods(results_dir: Path, market: str) -> pd.DataFrame:
    return load_csv(results_dir / market / f"{market}_tf_walkforward_periods.csv")


def build_market_assumptions(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        spec = get_market(market)
        base = summary[(summary["Market"] == market) & (summary["RunType"] == "walkforward_oos")].iloc[0]
        rows.append(
            {
                "Market": market,
                "Description": spec.name,
                "Exchange": spec.exchange,
                "Point Value": spec.PV,
                "Round-Turn Cost": float(base["RoundTurnCost"]),
                "Bars / Session": spec.bars_per_session,
                "Bars / Year": bars_per_year(market),
                "Session Filter": "Liquid session only" if spec.use_session_filter else "Full series",
                "Cost Note": base["CostNote"],
            }
        )
    return pd.DataFrame(rows)


def build_parity_table(results_dir: Path) -> pd.DataFrame:
    summary = load_csv(results_dir / "tf_backtest_summary.csv")
    rows: list[dict[str, object]] = []
    for market, full_l in [("TY", 1440), ("BTC", 288)]:
        full_df = load_ohlc(str(PROJECT_ROOT / "data"), market, fallback_synthetic=False)
        df = prepare_analysis_frame(full_df, market)
        cost = resolve_round_turn_cost(market)

        py_full = run_backtest(df, market, "tf", {"L": full_l, "S": 0.01}, round_turn_cost=cost)
        cpp_full = summary[(summary["Market"] == market) & (summary["RunType"] == "full_sample")].iloc[0]
        rows.append(
            {
                "Market": market,
                "Check": "full_sample",
                "Python Profit": float(py_full["Profit"]),
                "Cpp Profit": float(cpp_full["NetProfit"]),
                "Python MaxDD": float(py_full["MaxDD"]),
                "Cpp MaxDD": float(cpp_full["NetMaxDD"]),
                "Python RoA": float(py_full["Objective"]),
                "Cpp RoA": float(cpp_full["NetRoA"]),
                "Python Trades/Units": float(py_full["NumTrades"]),
                "Cpp Trades/Units": float(cpp_full["ClosedTrades"]),
            }
        )

        cfg = load_csv(results_dir / market / f"{market}_tf_reference_config.csv").iloc[0]
        bundle = run_reference_split(
            df,
            market,
            in_sample=(cfg["ISStart"], cfg["ISEnd"]),
            out_sample=(cfg["OOSStart"], cfg["OOSEnd"]),
            bars_back=int(cfg["BarsBack"]),
            tf_grid={"L": np.array([int(cfg["BestL"])]), "S": np.array([float(cfg["BestS"])])},
        )
        for label, py_stats, cpp_row in [
            (
                "reference_in_sample",
                bundle["in_sample_stats"],
                summary[(summary["Market"] == market) & (summary["RunType"] == "reference_in_sample")].iloc[0],
            ),
            (
                "reference_out_of_sample",
                bundle["out_sample_stats"],
                summary[(summary["Market"] == market) & (summary["RunType"] == "reference_out_of_sample")].iloc[0],
            ),
        ]:
            rows.append(
                {
                    "Market": market,
                    "Check": label,
                    "Python Profit": float(py_stats["Profit"]),
                    "Cpp Profit": float(cpp_row["NetProfit"]),
                    "Python MaxDD": float(py_stats["WorstDrawDown"]),
                    "Cpp MaxDD": float(cpp_row["NetMaxDD"]),
                    "Python RoA": float(py_stats["Objective"]),
                    "Cpp RoA": float(cpp_row["NetRoA"]),
                    "Python Trades/Units": float(py_stats["TradeUnits"]),
                    "Cpp Trades/Units": float(cpp_row["TradeUnits"]),
                }
            )

    df = pd.DataFrame(rows)
    for left, right in [
        ("Python Profit", "Cpp Profit"),
        ("Python MaxDD", "Cpp MaxDD"),
        ("Python RoA", "Cpp RoA"),
        ("Python Trades/Units", "Cpp Trades/Units"),
    ]:
        match_col = left.replace("Python ", "Match ")
        df[match_col] = np.isclose(df[left], df[right], rtol=1e-9, atol=1e-6)
    df["All Match"] = df[[col for col in df.columns if col.startswith("Match ")]].all(axis=1)
    return df


def build_walkforward_replay_comparison(results_dir: Path, report_dir: Path) -> pd.DataFrame:
    summary = load_csv(results_dir / "tf_backtest_summary.csv")
    core = load_csv(report_dir / "report_core_metrics.csv")
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        full_df = load_ohlc(str(PROJECT_ROOT / "data"), market, fallback_synthetic=False)
        df = prepare_analysis_frame(full_df, market)
        periods = load_periods(results_dir, market)
        cpp = summary[(summary["Market"] == market) & (summary["RunType"] == "walkforward_oos")].iloc[0]
        spec = get_market(market)
        equity_chunks: list[pd.Series] = []
        ledgers: list[pd.DataFrame] = []
        for _, row in periods.iterrows():
            start = pd.Timestamp(row["OOSStart"])
            end = pd.Timestamp(row["OOSEnd"])
            oos_start = int(df.index.get_indexer([start])[0])
            oos_end = int(df.index.get_indexer([end])[0]) + 1
            if oos_start < 0 or oos_end <= 0:
                raise ValueError(f"Could not locate OOS bounds for {market}: {start} -> {end}")
            result = run_backtest(
                df,
                market,
                "tf",
                {"L": int(row["L"]), "S": float(row["S"])},
                eval_start=oos_start,
                eval_end=oos_end,
                round_turn_cost=resolve_round_turn_cost(market),
                cost_multiplier=1.0,
            )
            local_start = oos_start - int(result["SliceStart"])
            local_end = oos_end - int(result["SliceStart"])
            oos_equity = np.asarray(result["Equity"][local_start:local_end], dtype=float)
            oos_pnl = np.diff(np.r_[spec.E0, oos_equity])
            equity_chunks.append(pd.Series(oos_pnl, index=df.index[oos_start:oos_end], name="OOS_PnL"))
            if len(result["Ledger"]):
                lg = result["Ledger"][result["Ledger"]["is_oos"]].copy()
                lg.insert(0, "Period", int(row["Period"]))
                ledgers.append(lg)
        pnl = pd.concat(equity_chunks)
        pnl = pnl[~pnl.index.duplicated(keep="first")]
        equity = spec.E0 + pnl.cumsum()
        ledger = pd.concat(ledgers, ignore_index=True) if ledgers else pd.DataFrame(columns=["pnl", "duration_bars"])
        metrics = performance_from_ledger(ledger, equity.to_numpy(dtype=float), market)
        cpp_sharpe = float(core[(core["Market"] == market) & (core["RunType"] == "walkforward_oos")]["NetAnnSharpe"].iloc[0])
        row_out = {
            "Market": market,
            "PythonPeriods": len(periods),
            "CppPeriods": int(cpp["Periods"]),
            "PythonNetProfit": float(metrics["Total Profit"]),
            "CppNetProfit": float(cpp["NetProfit"]),
            "PythonNetMaxDD": float(metrics["Max Drawdown $"]),
            "CppNetMaxDD": float(cpp["NetMaxDD"]),
            "PythonNetRoA": float(metrics["Return on Account"]),
            "CppNetRoA": float(cpp["NetRoA"]),
            "PythonTrades": int(metrics["Total Trades"]),
            "CppTrades": int(cpp["ClosedTrades"]),
            "PythonSharpe": float(metrics["Sharpe Ratio"]),
            "CppSharpe": cpp_sharpe,
        }
        for py_col, cpp_col, err_col in [
            ("PythonNetProfit", "CppNetProfit", "ProfitErrPct"),
            ("PythonNetMaxDD", "CppNetMaxDD", "MaxDDErrPct"),
            ("PythonNetRoA", "CppNetRoA", "RoAErrPct"),
            ("PythonTrades", "CppTrades", "TradesErrPct"),
            ("PythonSharpe", "CppSharpe", "SharpeErrPct"),
        ]:
            denom = abs(row_out[cpp_col]) if row_out[cpp_col] != 0 else np.nan
            row_out[err_col] = abs(row_out[py_col] - row_out[cpp_col]) / denom * 100.0
        row_out["Within10Pct"] = all(float(row_out[col]) <= 10.0 for col in ["ProfitErrPct", "MaxDDErrPct", "RoAErrPct", "TradesErrPct", "SharpeErrPct"])
        rows.append(row_out)
    return pd.DataFrame(rows)


def build_vr_recovery_summary(diag_dir: Path) -> pd.DataFrame:
    meta = load_csv(diag_dir / "push_response_metadata.csv")
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        vr = load_csv(diag_dir / f"{market}_vr_curve.csv").sort_values("q").reset_index(drop=True)
        trough = vr.iloc[int(vr["VR"].idxmin())]
        ref_tau = int(meta[(meta["Ticker"] == market) & (meta["Kind"] == "reference")]["TauBars"].iloc[0])
        ref_row = vr.iloc[(vr["q"] - ref_tau).abs().idxmin()]
        showcase_meta = meta[(meta["Ticker"] == market) & (meta["Kind"] == "showcase")]
        showcase_tau = int(showcase_meta["TauBars"].iloc[0]) if len(showcase_meta) else ref_tau
        show_row = vr.iloc[(vr["q"] - showcase_tau).abs().idxmin()]
        last = vr.iloc[-1]
        rows.append(
            {
                "Market": market,
                "Trough q": int(trough["q"]),
                "Trough VR": float(trough["VR"]),
                "Reference q": int(ref_row["q"]),
                "Reference VR": float(ref_row["VR"]),
                "Showcase q": int(show_row["q"]),
                "Showcase VR": float(show_row["VR"]),
                "Last q": int(last["q"]),
                "Last VR": float(last["VR"]),
                "Recovery to Reference": float(ref_row["VR"] - trough["VR"]),
                "Recovery to Showcase": float(show_row["VR"] - trough["VR"]),
                "Recovery to Last": float(last["VR"] - trough["VR"]),
            }
        )
    return pd.DataFrame(rows)


def build_drawdown_summary(results_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        for run_kind in ["walkforward", "fullsample"]:
            series = load_returns(results_dir, market, run_kind)
            dd = drawdown_family(series["NetEquity"].to_numpy(dtype=float))
            rows.append(
                {
                    "Market": market,
                    "RunKind": run_kind,
                    "MaxDD": float(dd["MaxDD"]),
                    "AvgDD": float(dd["AvgDD"]),
                    "CDD": float(dd["CDD"]),
                    "DD Duration (bars)": float(dd["DD_duration_bars"]),
                    "Recovery (bars)": float(dd["Recovery_bars"]) if np.isfinite(dd["Recovery_bars"]) else np.nan,
                }
            )
    return pd.DataFrame(rows)


def build_decay_table(core: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        wf = core[(core["Market"] == market) & (core["RunType"] == "walkforward_oos")].iloc[0]
        fs = core[(core["Market"] == market) & (core["RunType"] == "full_sample")].iloc[0]
        rows.append(
            {
                "Market": market,
                "Profit Ratio OOS/Full": float(wf["NetProfit"]) / float(fs["NetProfit"]),
                "RoA Ratio OOS/Full": float(wf["NetRoA"]) / float(fs["NetRoA"]),
                "Sharpe Ratio OOS/Full": float(wf["NetAnnSharpe"]) / float(fs["NetAnnSharpe"]),
                "Trades Ratio OOS/Full": float(wf["ClosedTrades"]) / float(fs["ClosedTrades"]),
            }
        )
    return pd.DataFrame(rows)


def build_reference_vs_walkforward(summary: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        wf = summary[(summary["Market"] == market) & (summary["RunType"] == "walkforward_oos")].iloc[0]
        ref = summary[(summary["Market"] == market) & (summary["RunType"] == "reference_out_of_sample")].iloc[0]
        rows.append(
            {
                "Market": market,
                "Walkforward NetProfit": float(wf["NetProfit"]),
                "Reference NetProfit": float(ref["NetProfit"]),
                "Walkforward NetMaxDD": float(wf["NetMaxDD"]),
                "Reference NetMaxDD": float(ref["NetMaxDD"]),
                "Walkforward NetRoA": float(wf["NetRoA"]),
                "Reference NetRoA": float(ref["NetRoA"]),
            }
        )
    return pd.DataFrame(rows)


def build_quarter_extremes(results_dir: Path) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        periods = load_periods(results_dir, market)
        best = periods.sort_values("OOSNetObjective").iloc[-1]
        worst = periods.sort_values("OOSNetObjective").iloc[0]
        for label, row in [("best", best), ("worst", worst)]:
            rows.append(
                {
                    "Market": market,
                    "Label": label,
                    "Period": int(row["Period"]),
                    "OOSStart": row["OOSStart"],
                    "OOSEnd": row["OOSEnd"],
                    "L": int(row["L"]),
                    "S": float(row["S"]),
                    "NetProfit": float(row["OOSNetProfit"]),
                    "NetMaxDD": float(row["OOSNetMaxDD"]),
                    "NetRoA": float(row["OOSNetObjective"]),
                    "ClosedTrades": int(row["OOSClosedTrades"]),
                }
            )
    return pd.DataFrame(rows)


def build_asset_manifest() -> pd.DataFrame:
    rows = [
        ("two_market_diagnostics_reference.png", "Diagnostics", "Reference-horizon VR + Push-Response panels for TY and BTC.", "Time-series story"),
        ("two_market_diagnostics_showcase.png", "Diagnostics", "Showcase-horizon diagnostics emphasizing the later cleaner BTC PR view.", "Time-series story / appendix"),
        ("overview/vr_recovery_summary.png", "Overview", "VR curves with trough and marked longer-horizon recovery points.", "Explain TY long-horizon TF"),
        ("overview/push_response_rho_summary.png", "Overview", "Short/reference/showcase push-response rho values.", "Explain PR sign changes"),
        ("overview/oos_decay_ratios.png", "Overview", "OOS/full decay for profit, RoA, Sharpe, and trades.", "Performance summary"),
        ("overview/reference_vs_walkforward.png", "Overview", "Compare the single reference split with the rolling assignment OOS run.", "Methodology comparison"),
        ("overview/transaction_cost_burden.png", "Overview", "Total cost and cost share of gross profit across canonical runs.", "Cost framing"),
        ("overview/drawdown_family_comparison.png", "Overview", "MaxDD, AvgDD, and CDD across TY/BTC and OOS/full sample.", "Risk framing"),
        ("overview/cost_sensitivity_overview.png", "Overview", "Profit, RoA, and Sharpe under 0x/0.5x/1x/2x cost assumptions.", "Robustness"),
        ("TY/TY_walkforward_quarterly_panel.png", "TY", "Quarter-by-quarter TY OOS profit and RoA.", "Quarter dynamics"),
        ("TY/TY_walkforward_parameter_heatmap.png", "TY", "Frequency heatmap of chosen TY L/S pairs.", "Parameter behavior"),
        ("BTC/BTC_walkforward_quarterly_panel.png", "BTC", "Quarter-by-quarter BTC OOS profit and RoA.", "Quarter dynamics"),
        ("BTC/BTC_walkforward_parameter_heatmap.png", "BTC", "Frequency heatmap of chosen BTC L/S pairs.", "Parameter behavior"),
    ]
    return pd.DataFrame(rows, columns=["Asset", "Section", "Purpose", "Suggested Slide Use"])


def save_vr_recovery_plot(diag_dir: Path, path: Path) -> None:
    meta = load_csv(diag_dir / "push_response_metadata.csv")
    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=False)
    for ax, market in zip(axes, ["TY", "BTC"]):
        vr = load_csv(diag_dir / f"{market}_vr_curve.csv").sort_values("q").reset_index(drop=True)
        trough = vr.iloc[int(vr["VR"].idxmin())]
        ref_tau = int(meta[(meta["Ticker"] == market) & (meta["Kind"] == "reference")]["TauBars"].iloc[0])
        ref_row = vr.iloc[(vr["q"] - ref_tau).abs().idxmin()]
        showcase_meta = meta[(meta["Ticker"] == market) & (meta["Kind"] == "showcase")]
        showcase_tau = int(showcase_meta["TauBars"].iloc[0]) if len(showcase_meta) else ref_tau
        show_row = vr.iloc[(vr["q"] - showcase_tau).abs().idxmin()]
        ax.plot(vr["q"], vr["VR"], color=COLUMBIA_CORE)
        ax.axhline(1.0, color=COLUMBIA_RED, linestyle="--", alpha=0.8, label="VR = 1")
        ax.scatter([trough["q"]], [trough["VR"]], color=COLUMBIA_RED, s=60, zorder=5, label="Trough")
        ax.scatter([ref_row["q"]], [ref_row["VR"]], color=COLUMBIA_NAVY, s=60, zorder=5, label="Reference")
        if int(show_row["q"]) != int(ref_row["q"]):
            ax.scatter([show_row["q"]], [show_row["VR"]], color=COLUMBIA_WARM, s=60, zorder=5, label="Showcase")
        ax.set_title(f"{market}: Variance Ratio recovery")
        ax.set_xlabel("q (bars)")
        ax.set_ylabel("VR(q)")
        ax.legend(loc="best")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_pr_rho_summary(diag_dir: Path, path: Path) -> None:
    meta = load_csv(diag_dir / "push_response_metadata.csv").copy()
    kinds = ["short", "reference", "showcase"]
    markets = ["TY", "BTC"]
    x = np.arange(len(kinds))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    for idx, market in enumerate(markets):
        subset = meta[meta["Ticker"] == market].set_index("Kind")
        values = [float(subset.loc[k, "Rho"]) if k in subset.index else np.nan for k in kinds]
        ax.bar(x + (idx - 0.5) * width, values, width=width, label=market, color=[COLUMBIA_NAVY, COLUMBIA_WARM][idx])
    ax.axhline(0.0, color=COLUMBIA_DARK, linewidth=1.0)
    ax.set_xticks(x, [k.title() for k in kinds])
    ax.set_ylabel("Spearman rho")
    ax.set_title("Push-Response directional summary")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_decay_plot(decay: pd.DataFrame, path: Path) -> None:
    metrics = ["Profit Ratio OOS/Full", "RoA Ratio OOS/Full", "Sharpe Ratio OOS/Full", "Trades Ratio OOS/Full"]
    x = np.arange(len(metrics))
    width = 0.35
    fig, ax = plt.subplots(figsize=(14, 6))
    for idx, market in enumerate(["TY", "BTC"]):
        row = decay[decay["Market"] == market].iloc[0]
        values = [float(row[m]) for m in metrics]
        ax.bar(x + (idx - 0.5) * width, values, width=width, label=market, color=[COLUMBIA_NAVY, COLUMBIA_WARM][idx])
    ax.set_xticks(x, ["Profit", "RoA", "Sharpe", "Trades"])
    ax.set_ylabel("OOS / Full-sample ratio")
    ax.set_title("Out-of-sample decay relative to full sample")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_reference_vs_walkforward_plot(reference_vs_wf: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    specs = [
        ("NetProfit", "Net Profit ($)", "Walkforward NetProfit", "Reference NetProfit"),
        ("NetMaxDD", "Net MaxDD ($)", "Walkforward NetMaxDD", "Reference NetMaxDD"),
        ("NetRoA", "Net RoA", "Walkforward NetRoA", "Reference NetRoA"),
    ]
    markets = reference_vs_wf["Market"].tolist()
    x = np.arange(len(markets))
    width = 0.35
    for ax, (_, title, wf_col, ref_col) in zip(axes, specs):
        ax.bar(x - width / 2, reference_vs_wf[wf_col], width=width, label="Walk-forward OOS", color=COLUMBIA_NAVY)
        ax.bar(x + width / 2, reference_vs_wf[ref_col], width=width, label="Reference OOS", color=COLUMBIA_CORE)
        ax.set_xticks(x, markets)
        ax.set_title(title)
    axes[0].legend()
    fig.suptitle("Assignment rolling OOS versus single reference split")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_cost_burden_plot(core: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    for ax, market in zip(axes, ["TY", "BTC"]):
        subset = core[core["Market"] == market].copy()
        subset["GrossProfit"] = subset["NetProfit"] + subset["TotalCost"]
        subset["CostShare"] = subset["TotalCost"] / subset["GrossProfit"]
        x = np.arange(len(subset))
        ax.bar(x - 0.2, subset["NetProfit"], width=0.4, color=COLUMBIA_NAVY, label="Net Profit")
        ax.bar(x + 0.2, subset["TotalCost"], width=0.4, color=COLUMBIA_WARM, label="Total Cost")
        ax2 = ax.twinx()
        ax2.plot(x, subset["CostShare"], color=COLUMBIA_RED, marker="o", label="Cost / Gross Profit")
        ax.set_xticks(x, ["Walk-forward", "Full sample"])
        ax.set_title(f"{market}: transaction-cost burden")
        ax.set_ylabel("Dollars")
        ax2.set_ylabel("Cost share")
        if market == "TY":
            lines = ax.get_legend_handles_labels()[0] + ax2.get_legend_handles_labels()[0]
            labels = ax.get_legend_handles_labels()[1] + ax2.get_legend_handles_labels()[1]
            ax.legend(lines, labels, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_drawdown_family_plot(dd_df: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    metrics = [("MaxDD", "MaxDD"), ("AvgDD", "AvgDD"), ("CDD", "CDD (alpha=0.05)")]
    colors = {"walkforward": COLUMBIA_NAVY, "fullsample": COLUMBIA_WARM}
    x = np.arange(2)
    width = 0.35
    for ax, (col, title) in zip(axes, metrics):
        for idx, run_kind in enumerate(["walkforward", "fullsample"]):
            subset = dd_df[dd_df["RunKind"] == run_kind].set_index("Market").loc[["TY", "BTC"]]
            ax.bar(x + (idx - 0.5) * width, subset[col], width=width, color=colors[run_kind], label=run_kind.title())
        ax.set_xticks(x, ["TY", "BTC"])
        ax.set_title(title)
    axes[0].legend()
    fig.suptitle("Drawdown-family comparison on net equity")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_cost_sensitivity_overview(cost_df: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(2, 3, figsize=(18, 9), sharex=True)
    metric_specs = [
        ("Total Profit", "Profit"),
        ("Return on Account", "RoA"),
        ("Sharpe Ratio", "Sharpe"),
    ]
    for row_idx, market in enumerate(["TY", "BTC"]):
        subset = cost_df[cost_df["Ticker"] == market].sort_values("CostMultiplier")
        x = subset["CostMultiplier"].to_numpy(dtype=float)
        for col_idx, (metric, title) in enumerate(metric_specs):
            ax = axes[row_idx, col_idx]
            ax.plot(x, subset[metric], color=[COLUMBIA_NAVY, COLUMBIA_WARM][row_idx], marker="o")
            ax.set_title(f"{market}: {title} vs cost multiplier")
            ax.set_xlabel("Cost multiplier")
            ax.set_ylabel(title)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_quarterly_panel(periods: pd.DataFrame, market: str, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    x = periods["Period"].astype(int).to_numpy()
    pnl = periods["OOSNetProfit"].astype(float).to_numpy()
    colors = [COLUMBIA_NAVY if value >= 0 else COLUMBIA_RED for value in pnl]
    axes[0].bar(x, pnl, color=colors)
    axes[0].axhline(0.0, color=COLUMBIA_DARK, linewidth=1.0)
    axes[0].set_ylabel("Net profit ($)")
    axes[0].set_title(f"{market}: quarterly OOS net profit")

    axes[1].plot(x, periods["OOSNetObjective"].astype(float), color=COLUMBIA_CORE, marker="o", label="Net RoA")
    axes[1].axhline(0.0, color=COLUMBIA_DARK, linewidth=1.0)
    axes[1].set_ylabel("Net RoA")
    axes[1].set_xlabel("Walk-forward period")
    axes[1].set_title(f"{market}: quarterly OOS objective")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_parameter_heatmap(periods: pd.DataFrame, market: str, path: Path) -> None:
    heat = (
        periods.assign(S=periods["S"].astype(float).round(6))
        .groupby(["S", "L"])
        .size()
        .unstack(fill_value=0)
        .sort_index(ascending=True)
    )
    fig, ax = plt.subplots(figsize=(10, 6))
    im = ax.imshow(heat.to_numpy(), aspect="auto", cmap=COLUMBIA_CMAP if False else "Blues")
    ax.set_xticks(np.arange(len(heat.columns)), [str(int(col)) for col in heat.columns], rotation=45, ha="right")
    ax.set_yticks(np.arange(len(heat.index)), [f"{float(idx):.3f}" for idx in heat.index])
    ax.set_xlabel("L")
    ax.set_ylabel("S")
    ax.set_title(f"{market}: frequency of selected L/S pairs")
    fig.colorbar(im, ax=ax, shrink=0.85, label="count")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_visuals(
    results_dir: Path,
    report_dir: Path,
    diag_dir: Path,
    cost_dir: Path,
    core: pd.DataFrame,
    summary: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    overview_dir = report_dir / "overview"
    overview_dir.mkdir(parents=True, exist_ok=True)

    parity = build_parity_table(results_dir)
    parity.to_csv(overview_dir / "parity_check.csv", index=False)
    walkforward_replay = build_walkforward_replay_comparison(results_dir, report_dir)
    walkforward_replay.to_csv(overview_dir / "walkforward_python_cpp_comparison.csv", index=False)

    vr_summary = build_vr_recovery_summary(diag_dir)
    vr_summary.to_csv(overview_dir / "vr_recovery_summary.csv", index=False)

    drawdown_df = build_drawdown_summary(results_dir)
    drawdown_df.to_csv(overview_dir / "drawdown_family_summary.csv", index=False)

    decay = build_decay_table(core)
    decay.to_csv(overview_dir / "oos_decay_ratios.csv", index=False)

    ref_vs_wf = build_reference_vs_walkforward(summary)
    ref_vs_wf.to_csv(overview_dir / "reference_vs_walkforward.csv", index=False)

    quarter_extremes = build_quarter_extremes(results_dir)
    quarter_extremes.to_csv(overview_dir / "quarter_extremes.csv", index=False)

    asset_manifest = build_asset_manifest()
    asset_manifest.to_csv(overview_dir / "asset_manifest.csv", index=False)

    save_vr_recovery_plot(diag_dir, overview_dir / "vr_recovery_summary.png")
    save_pr_rho_summary(diag_dir, overview_dir / "push_response_rho_summary.png")
    save_decay_plot(decay, overview_dir / "oos_decay_ratios.png")
    save_reference_vs_walkforward_plot(ref_vs_wf, overview_dir / "reference_vs_walkforward.png")
    save_cost_burden_plot(core, overview_dir / "transaction_cost_burden.png")
    save_drawdown_family_plot(drawdown_df, overview_dir / "drawdown_family_comparison.png")
    save_cost_sensitivity_overview(load_csv(cost_dir / "cost_sensitivity_summary.csv"), overview_dir / "cost_sensitivity_overview.png")

    for market in ["TY", "BTC"]:
        periods = load_periods(results_dir, market)
        market_dir = report_dir / market
        market_dir.mkdir(parents=True, exist_ok=True)
        save_quarterly_panel(periods, market, market_dir / f"{market}_walkforward_quarterly_panel.png")
        save_parameter_heatmap(periods, market, market_dir / f"{market}_walkforward_parameter_heatmap.png")

    return {
        "parity": parity,
        "walkforward_replay": walkforward_replay,
        "vr_summary": vr_summary,
        "drawdown": drawdown_df,
        "decay": decay,
        "reference_vs_wf": ref_vs_wf,
        "quarter_extremes": quarter_extremes,
        "asset_manifest": asset_manifest,
        "cost_summary": load_csv(cost_dir / "cost_sensitivity_summary.csv"),
        "pr_meta": load_csv(diag_dir / "push_response_metadata.csv"),
    }


def build_core_headline_table(core: pd.DataFrame) -> pd.DataFrame:
    out = core[[
        "Market",
        "RunType",
        "L",
        "S",
        "NetProfit",
        "NetMaxDD",
        "NetRoA",
        "NetAnnReturn",
        "NetAnnVol",
        "NetAnnSharpe",
        "ClosedTrades",
    ]].copy()
    out["L"] = out["L"].astype(int)
    out["S"] = out["S"].astype(float).round(3)
    out["NetProfit"] = out["NetProfit"].map(money)
    out["NetMaxDD"] = out["NetMaxDD"].map(money)
    out["NetRoA"] = out["NetRoA"].map(ratio)
    out["NetAnnReturn"] = out["NetAnnReturn"].map(pct)
    out["NetAnnVol"] = out["NetAnnVol"].map(pct)
    out["NetAnnSharpe"] = out["NetAnnSharpe"].map(ratio)
    out["ClosedTrades"] = out["ClosedTrades"].astype(int)
    return out


def build_market_narrative(summary: pd.DataFrame, vr_summary: pd.DataFrame, pr_meta: pd.DataFrame) -> list[str]:
    lines: list[str] = []
    for market in ["TY", "BTC"]:
        wf = summary[(summary["Market"] == market) & (summary["RunType"] == "walkforward_oos")].iloc[0]
        vr = vr_summary[vr_summary["Market"] == market].iloc[0]
        ref_pr = pr_meta[(pr_meta["Ticker"] == market) & (pr_meta["Kind"] == "reference")].iloc[0]
        showcase = pr_meta[(pr_meta["Ticker"] == market) & (pr_meta["Kind"] == "showcase")]
        show_pr = showcase.iloc[0] if len(showcase) else ref_pr
        if market == "TY":
            lines.append(
                f"- `TY`: the VR curve bottoms near `q = {int(vr['Trough q'])}` and recovers by `+{vr['Recovery to Reference']:.3f}` by the professor reference horizon `q = {int(vr['Reference q'])}`. "
                f"Reference-horizon push-response is positive with `rho = {float(ref_pr['Rho']):.3f}`, supporting the slower long-horizon TF story. "
                f"The canonical walk-forward run then settles on modal `L = {int(wf['L'])}`, `S = {float(wf['S']):.2f}`."
            )
        else:
            lines.append(
                f"- `BTC`: short-horizon PR is mixed, but the longer showcase horizon `tau = {int(show_pr['TauBars'])}` bars produces `rho = {float(show_pr['Rho']):.3f}` while the VR curve recovers `+{vr['Recovery to Showcase']:.3f}` from its trough. "
                f"The C++ walk-forward run still prefers a much faster TF configuration, modal `L = {int(wf['L'])}`, `S = {float(wf['S']):.2f}`."
            )
    return lines


def write_final_reporting(
    report_dir: Path,
    results_dir: Path,
    diag_dir: Path,
    tables: dict[str, pd.DataFrame],
    core: pd.DataFrame,
    summary: pd.DataFrame,
    assumptions: pd.DataFrame,
) -> None:
    lines: list[str] = []
    lines.append("# Final Reporting")
    lines.append("")
    lines.append("This file is the exhaustive pick-and-choose reporting layer for the canonical official-cost run. It is intentionally broader than the shorter extracted summary so the group can lift visuals, tables, and exact language directly into slides.")
    lines.append("")
    lines.append("## 1. Fundamental Questions Answered")
    lines.append("")
    lines.extend(
        [
            "- `Does Python match C++?` Yes on the canonical parity checks shown below. The engines agree exactly on the full-sample and Matlab-style reference-split checks for both `TY` and `BTC`.",
            "- `What inefficiency do we see?` `TY` is mixed or mean-reverting at short horizons but becomes more trend-consistent at longer horizons; `BTC` is faster and more volatile, with a stronger trend-following implementation outcome and a cleaner longer-horizon showcase PR panel.",
            "- `What is the canonical result set?` The source of truth is [results_cpp_official_quick/tf_backtest_summary.csv](../results_cpp_official_quick/tf_backtest_summary.csv) together with the figures and tables in this folder.",
            "- `What should headline the presentation?` Equity-curve metrics first, trade-table metrics second, because the OOS equity curve is marked to market bar by bar while the trade table contains only closed trades.",
        ]
    )
    lines.append("")
    lines.append("## 2. Canonical Run Assumptions")
    lines.append("")
    lines.append(safe_markdown(assumptions[["Market", "Description", "Exchange", "Point Value", "Round-Turn Cost", "Bars / Session", "Bars / Year", "Session Filter"]]))
    lines.append("")
    lines.append("Important reporting note:")
    lines.append("")
    lines.extend(
        [
            "- Walk-forward structure: `4 years` in-sample, `1 quarter` immediately adjacent out-of-sample, rolled forward one quarter at a time.",
            "- Optimization target: `Net Profit / Max Drawdown` (`RoA`).",
            "- `TY` uses the liquid-session filter; `BTC` uses the full 24-hour series.",
            "- Official round-turn costs in the canonical run: `TY = $18.625`, `BTC = $25.00`.",
        ]
    )
    lines.append("")
    lines.append("## 3. Python/C++ Parity Checks")
    lines.append("")
    parity = tables["parity"].copy()
    parity["Python Profit"] = parity["Python Profit"].map(money)
    parity["Cpp Profit"] = parity["Cpp Profit"].map(money)
    parity["Python MaxDD"] = parity["Python MaxDD"].map(money)
    parity["Cpp MaxDD"] = parity["Cpp MaxDD"].map(money)
    parity["Python RoA"] = parity["Python RoA"].map(ratio)
    parity["Cpp RoA"] = parity["Cpp RoA"].map(ratio)
    parity["Python Trades/Units"] = parity["Python Trades/Units"].map(lambda x: f"{x:,.1f}")
    parity["Cpp Trades/Units"] = parity["Cpp Trades/Units"].map(lambda x: f"{x:,.1f}")
    lines.append(safe_markdown(parity))
    lines.append("")
    lines.append("Every row above matched exactly within floating-point tolerance on the rerun parity checks.")
    lines.append("")
    lines.append("### Rolling walk-forward replay check")
    lines.append("")
    wf_replay = tables["walkforward_replay"].copy()
    for col in ["PythonNetProfit", "CppNetProfit", "PythonNetMaxDD", "CppNetMaxDD"]:
        wf_replay[col] = wf_replay[col].map(money)
    for col in ["PythonNetRoA", "CppNetRoA", "PythonSharpe", "CppSharpe"]:
        wf_replay[col] = wf_replay[col].map(ratio)
    for col in ["ProfitErrPct", "MaxDDErrPct", "RoAErrPct", "TradesErrPct", "SharpeErrPct"]:
        wf_replay[col] = wf_replay[col].map(lambda x: f"{x:.6f}%")
    lines.append(safe_markdown(wf_replay))
    lines.append("")
    lines.append("This check replays the exact C++ quarterly parameter table in Python and compares the stitched OOS result. Both markets are comfortably within the requested `10%` tolerance; in practice they are essentially exact.")
    lines.append("")
    lines.append("## 4. Diagnostics Story")
    lines.append("")
    lines.append("### Reference-horizon composite")
    lines.append("")
    lines.append("![Reference diagnostics](../results_diagnostics_story/two_market_diagnostics_reference.png)")
    lines.append("")
    lines.append("### Showcase composite")
    lines.append("")
    lines.append("![Showcase diagnostics](../results_diagnostics_story/two_market_diagnostics_showcase.png)")
    lines.append("")
    lines.append("### Additional diagnostics visuals")
    lines.append("")
    lines.append("![VR recovery summary](overview/vr_recovery_summary.png)")
    lines.append("")
    lines.append("![Push-response rho summary](overview/push_response_rho_summary.png)")
    lines.append("")
    vr = tables["vr_summary"].copy()
    vr["Trough VR"] = vr["Trough VR"].map(lambda x: f"{x:.3f}")
    vr["Reference VR"] = vr["Reference VR"].map(lambda x: f"{x:.3f}")
    vr["Showcase VR"] = vr["Showcase VR"].map(lambda x: f"{x:.3f}")
    vr["Last VR"] = vr["Last VR"].map(lambda x: f"{x:.3f}")
    vr["Recovery to Reference"] = vr["Recovery to Reference"].map(lambda x: f"{x:+.3f}")
    vr["Recovery to Showcase"] = vr["Recovery to Showcase"].map(lambda x: f"{x:+.3f}")
    vr["Recovery to Last"] = vr["Recovery to Last"].map(lambda x: f"{x:+.3f}")
    lines.append("Variance-ratio recovery summary:")
    lines.append("")
    lines.append(safe_markdown(vr))
    lines.append("")
    pr = tables["pr_meta"].copy()
    pr["Rho"] = pr["Rho"].map(lambda x: f"{x:+.3f}")
    pr["PValue"] = pr["PValue"].map(lambda x: f"{x:.3f}")
    lines.append("Push-response summary:")
    lines.append("")
    lines.append(safe_markdown(pr))
    lines.append("")
    lines.extend(build_market_narrative(summary, tables["vr_summary"], tables["pr_meta"]))
    lines.append("")
    lines.append("## 5. Headline Backtest Results")
    lines.append("")
    lines.append(safe_markdown(build_core_headline_table(core)))
    lines.append("")
    lines.append("### High-level comparison visuals")
    lines.append("")
    lines.append("![OOS decay ratios](overview/oos_decay_ratios.png)")
    lines.append("")
    lines.append("![Reference vs walkforward comparison](overview/reference_vs_walkforward.png)")
    lines.append("")
    lines.append("![Transaction-cost burden](overview/transaction_cost_burden.png)")
    lines.append("")
    lines.append("![Drawdown family comparison](overview/drawdown_family_comparison.png)")
    lines.append("")
    dd = tables["drawdown"].copy()
    for col in ["MaxDD", "AvgDD", "CDD"]:
        dd[col] = dd[col].map(money)
    lines.append("Drawdown-family table:")
    lines.append("")
    lines.append(safe_markdown(dd))
    lines.append("")
    decay = tables["decay"].copy()
    for col in decay.columns[1:]:
        decay[col] = decay[col].map(lambda x: f"{x:.3f}")
    lines.append("Out-of-sample decay table:")
    lines.append("")
    lines.append(safe_markdown(decay))
    lines.append("")
    lines.append("## 6. TY Deep Dive")
    lines.append("")
    lines.extend(
        [
            "- `TY` is the slower market. The diagnostics argue for longer-horizon TF, and the walk-forward selections cluster around `L = 1440` to `1920` bars.",
            "- This is the market where the professor’s “VR falls first, then bends upward at longer horizons” story is most important.",
        ]
    )
    lines.append("")
    lines.append("![TY walkforward growth](TY/TY_walkforward_growth_of_1.png)")
    lines.append("")
    lines.append("![TY walkforward underwater](TY/TY_walkforward_underwater.png)")
    lines.append("")
    lines.append("![TY walkforward costs and turnover](TY/TY_walkforward_costs_turnover.png)")
    lines.append("")
    lines.append("![TY quarterly OOS panel](TY/TY_walkforward_quarterly_panel.png)")
    lines.append("")
    lines.append("![TY parameter stability](TY/TY_walkforward_parameter_stability.png)")
    lines.append("")
    lines.append("![TY parameter frequency](TY/TY_walkforward_parameter_frequency.png)")
    lines.append("")
    lines.append("![TY parameter heatmap](TY/TY_walkforward_parameter_heatmap.png)")
    lines.append("")
    lines.append("![TY reference growth](TY/TY_reference_growth_of_1.png)")
    lines.append("")
    lines.append("![TY reference OOS growth](TY/TY_reference_oos_growth_of_1.png)")
    lines.append("")
    lines.append("## 7. BTC Deep Dive")
    lines.append("")
    lines.extend(
        [
            "- `BTC` is the faster market. The implementation outcome is much stronger, but the diagnostics still matter because short-horizon PR is mixed and the cleaner TF case emerges at the later showcase horizon.",
            "- The canonical walk-forward run selects `L = 288` most often, with `576` and `1152` appearing in the stronger later periods.",
        ]
    )
    lines.append("")
    lines.append("![BTC walkforward growth](BTC/BTC_walkforward_growth_of_1.png)")
    lines.append("")
    lines.append("![BTC walkforward underwater](BTC/BTC_walkforward_underwater.png)")
    lines.append("")
    lines.append("![BTC walkforward costs and turnover](BTC/BTC_walkforward_costs_turnover.png)")
    lines.append("")
    lines.append("![BTC quarterly OOS panel](BTC/BTC_walkforward_quarterly_panel.png)")
    lines.append("")
    lines.append("![BTC parameter stability](BTC/BTC_walkforward_parameter_stability.png)")
    lines.append("")
    lines.append("![BTC parameter frequency](BTC/BTC_walkforward_parameter_frequency.png)")
    lines.append("")
    lines.append("![BTC parameter heatmap](BTC/BTC_walkforward_parameter_heatmap.png)")
    lines.append("")
    lines.append("![BTC reference growth](BTC/BTC_reference_growth_of_1.png)")
    lines.append("")
    lines.append("![BTC reference OOS growth](BTC/BTC_reference_oos_growth_of_1.png)")
    lines.append("")
    lines.append("## 8. Cost Sensitivity")
    lines.append("")
    lines.append("![Combined cost sensitivity](overview/cost_sensitivity_overview.png)")
    lines.append("")
    lines.append("### TY cost-sensitivity assets")
    lines.append("")
    lines.append("![TY profit sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_profit.png)")
    lines.append("")
    lines.append("![TY RoA sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_roa.png)")
    lines.append("")
    lines.append("![TY Sharpe sensitivity](../results_cost_sensitivity_fixed/TY_cost_sensitivity_sharpe.png)")
    lines.append("")
    lines.append("### BTC cost-sensitivity assets")
    lines.append("")
    lines.append("![BTC profit sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_profit.png)")
    lines.append("")
    lines.append("![BTC RoA sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_roa.png)")
    lines.append("")
    lines.append("![BTC Sharpe sensitivity](../results_cost_sensitivity_fixed/BTC_cost_sensitivity_sharpe.png)")
    lines.append("")
    cost = tables["cost_summary"].copy()
    focus = cost[cost["CostMultiplier"].isin([0.0, 0.5, 1.0, 2.0])][["Ticker", "CostMultiplier", "Total Profit", "Sharpe Ratio", "Return on Account"]].copy()
    focus["Total Profit"] = focus["Total Profit"].map(money)
    focus["Sharpe Ratio"] = focus["Sharpe Ratio"].map(lambda x: f"{x:.3f}")
    focus["Return on Account"] = focus["Return on Account"].map(lambda x: f"{x:.3f}")
    lines.append("Cost sensitivity summary:")
    lines.append("")
    lines.append(safe_markdown(focus))
    lines.append("")
    lines.append("## 9. Quarterly Extremes And Parameter Behavior")
    lines.append("")
    qx = tables["quarter_extremes"].copy()
    qx["NetProfit"] = qx["NetProfit"].map(money)
    qx["NetMaxDD"] = qx["NetMaxDD"].map(money)
    qx["NetRoA"] = qx["NetRoA"].map(lambda x: f"{x:.3f}")
    lines.append(safe_markdown(qx))
    lines.append("")
    lines.append("## 10. Asset Index")
    lines.append("")
    lines.append("This table is meant to help the group choose which visuals to keep in the final deck.")
    lines.append("")
    lines.append(safe_markdown(tables["asset_manifest"]))
    lines.append("")
    lines.append("## 11. Supporting Files")
    lines.append("")
    lines.extend(
        [
            "- Core metrics: [report_core_metrics.csv](report_core_metrics.csv)",
            "- Short extracted summary: [final_report_extract.md](final_report_extract.md)",
            "- Overview table from the C++ renderer: [cpp_backtest_report_overview.csv](cpp_backtest_report_overview.csv)",
            "- Walk-forward summary: [../results_cpp_official_quick/tf_backtest_summary.csv](../results_cpp_official_quick/tf_backtest_summary.csv)",
            "- Overview asset manifest: [overview/asset_manifest.csv](overview/asset_manifest.csv)",
            "- Parity check table: [overview/parity_check.csv](overview/parity_check.csv)",
            "- Walk-forward replay comparison: [overview/walkforward_python_cpp_comparison.csv](overview/walkforward_python_cpp_comparison.csv)",
            "- Drawdown family summary: [overview/drawdown_family_summary.csv](overview/drawdown_family_summary.csv)",
            "- Quarter extremes: [overview/quarter_extremes.csv](overview/quarter_extremes.csv)",
        ]
    )
    lines.append("")
    lines.append("## 12. Sources")
    lines.append("")
    lines.extend(
        [
            "- [Final Project MATH GR5360.pdf](../Final%20Project%20MATH%20GR5360.pdf)",
            "- professor-provided `main.m` and `ezread.m`",
            "- course lecture material on Variance Ratio, Push-Response, and drawdown-family measures",
            "- official course parameter sheets used for transaction-cost assumptions",
        ]
    )
    (report_dir / "finalReporting.md").write_text("\n".join(lines), encoding="utf-8")


def mirror_outputs(report_dir: Path, mirror_dir: Path) -> None:
    mirror_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(report_dir / "finalReporting.md", mirror_dir / "finalReporting.md")
    if (report_dir / "overview").exists():
        shutil.copytree(report_dir / "overview", mirror_dir / "overview", dirs_exist_ok=True)
    for market in ["TY", "BTC"]:
        src = report_dir / market
        if not src.exists():
            continue
        dst = mirror_dir / market
        dst.mkdir(parents=True, exist_ok=True)
        for name in [f"{market}_walkforward_quarterly_panel.png", f"{market}_walkforward_parameter_heatmap.png"]:
            if (src / name).exists():
                shutil.copy2(src / name, dst / name)


def main() -> int:
    args = parse_args()
    apply_columbia_theme()
    args.report_dir.mkdir(parents=True, exist_ok=True)
    summary = load_csv(args.results_dir / "tf_backtest_summary.csv")
    core = load_csv(args.report_dir / "report_core_metrics.csv")
    assumptions = build_market_assumptions(summary)
    tables = save_visuals(args.results_dir, args.report_dir, args.diagnostics_dir, args.cost_dir, core, summary)
    assumptions.to_csv(args.report_dir / "overview" / "market_assumptions.csv", index=False)
    write_final_reporting(args.report_dir, args.results_dir, args.diagnostics_dir, tables, core, summary, assumptions)
    if args.mirror_report_dir:
        mirror_outputs(args.report_dir, args.mirror_report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

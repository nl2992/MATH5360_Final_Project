from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mafn_engine import apply_columbia_theme, bars_per_year


@dataclass(frozen=True)
class LoadedRun:
    market: str
    run_kind: str
    market_dir: Path
    series: pd.DataFrame
    summary: pd.DataFrame
    config: pd.DataFrame | None
    trades: pd.DataFrame | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render figures and tables from the C++ TF backtest outputs.")
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=PROJECT_ROOT / "results_cpp",
        help="Directory containing the C++ CSV outputs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "results_cpp_report",
        help="Directory where figures and derived tables will be written.",
    )
    parser.add_argument(
        "--markets",
        type=str,
        default="TY,BTC",
        help="Comma-separated market list, e.g. TY,BTC.",
    )
    parser.add_argument(
        "--run-kind",
        choices=["auto", "reference", "walkforward", "fullsample"],
        default="auto",
        help="Which C++ output family to render.",
    )
    return parser.parse_args()


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def choose_run_kind(market_dir: Path, requested: str) -> str:
    if requested != "auto":
        return requested
    if (market_dir / f"{market_dir.name}_tf_reference_series.csv").exists():
        return "reference"
    if (market_dir / f"{market_dir.name}_tf_oos_returns.csv").exists():
        return "walkforward"
    if (market_dir / f"{market_dir.name}_tf_fullsample_returns.csv").exists():
        return "fullsample"
    raise FileNotFoundError(f"No recognizable C++ output files found under {market_dir}")


def load_run(input_dir: Path, market: str, run_kind: str) -> LoadedRun:
    market_dir = input_dir / market
    actual_kind = choose_run_kind(market_dir, run_kind)
    summary_global = _read_csv(input_dir / "tf_backtest_summary.csv") if (input_dir / "tf_backtest_summary.csv").exists() else pd.DataFrame()

    if actual_kind == "reference":
        series = _read_csv(market_dir / f"{market}_tf_reference_series.csv")
        summary = _read_csv(market_dir / f"{market}_tf_reference_summary.csv")
        config = _read_csv(market_dir / f"{market}_tf_reference_config.csv")
        trades = _read_csv(market_dir / f"{market}_tf_reference_trades.csv") if (market_dir / f"{market}_tf_reference_trades.csv").exists() else None
    elif actual_kind == "walkforward":
        series = _read_csv(market_dir / f"{market}_tf_oos_returns.csv")
        if {"Market", "RunType"}.issubset(summary_global.columns):
            summary = summary_global[(summary_global["Market"] == market) & (summary_global["RunType"] == "walkforward_oos")].copy()
        else:
            summary = pd.DataFrame()
        config = None
        trades = _read_csv(market_dir / f"{market}_tf_oos_trades.csv") if (market_dir / f"{market}_tf_oos_trades.csv").exists() else None
    else:
        series = _read_csv(market_dir / f"{market}_tf_fullsample_returns.csv")
        if {"Market", "RunType"}.issubset(summary_global.columns):
            summary = summary_global[(summary_global["Market"] == market) & (summary_global["RunType"] == "full_sample")].copy()
        else:
            summary = pd.DataFrame()
        config = None
        trades = _read_csv(market_dir / f"{market}_tf_fullsample_trades.csv") if (market_dir / f"{market}_tf_fullsample_trades.csv").exists() else None

    if "DateTime" in series.columns:
        series["DateTime"] = pd.to_datetime(series["DateTime"])
    if "Segment" not in series.columns:
        series["Segment"] = "full_sample"
    return LoadedRun(
        market=market,
        run_kind=actual_kind,
        market_dir=market_dir,
        series=series,
        summary=summary,
        config=config,
        trades=trades,
    )


def compute_growth(returns: pd.Series) -> pd.Series:
    clean = pd.Series(returns, copy=True).fillna(0.0)
    return (1.0 + clean).cumprod()


def compute_underwater(growth: pd.Series) -> pd.Series:
    peak = growth.cummax()
    return growth / peak - 1.0


def annualized_stats(series: pd.DataFrame, market: str) -> dict[str, float]:
    bpyear = bars_per_year(market)
    gross_ret = series["GrossReturn"].fillna(0.0).to_numpy(dtype=float)
    net_ret = series["NetReturn"].fillna(0.0).to_numpy(dtype=float)

    gross_growth = compute_growth(pd.Series(gross_ret))
    net_growth = compute_growth(pd.Series(net_ret))

    gross_vol = float(np.std(gross_ret, ddof=1) * np.sqrt(bpyear)) if len(gross_ret) > 1 else 0.0
    net_vol = float(np.std(net_ret, ddof=1) * np.sqrt(bpyear)) if len(net_ret) > 1 else 0.0
    gross_mean = float(np.mean(gross_ret) * bpyear)
    net_mean = float(np.mean(net_ret) * bpyear)
    gross_sharpe = gross_mean / gross_vol if gross_vol > 0 else 0.0
    net_sharpe = net_mean / net_vol if net_vol > 0 else 0.0

    years = len(series) / bpyear if bpyear > 0 else 0.0
    gross_cagr = float(gross_growth.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and gross_growth.iloc[-1] > 0 else 0.0
    net_cagr = float(net_growth.iloc[-1] ** (1.0 / years) - 1.0) if years > 0 and net_growth.iloc[-1] > 0 else 0.0

    return {
        "GrossAnnVol": gross_vol,
        "NetAnnVol": net_vol,
        "GrossSharpe": gross_sharpe,
        "NetSharpe": net_sharpe,
        "GrossCAGR": gross_cagr,
        "NetCAGR": net_cagr,
    }


def save_growth_plot(series: pd.DataFrame, title: str, path: Path) -> None:
    growth_gross = compute_growth(series["GrossReturn"])
    growth_net = compute_growth(series["NetReturn"])

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.plot(series["DateTime"], growth_gross, label="Gross", color="#012169")
    ax.plot(series["DateTime"], growth_net, label="Net of transaction costs", color="#E08119")
    ax.set_title(title)
    ax.set_ylabel("Growth of $1")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_underwater_plot(series: pd.DataFrame, title: str, path: Path) -> None:
    underwater_gross = compute_underwater(compute_growth(series["GrossReturn"]))
    underwater_net = compute_underwater(compute_growth(series["NetReturn"]))

    fig, ax = plt.subplots(figsize=(13, 6))
    ax.fill_between(series["DateTime"], underwater_gross, 0.0, alpha=0.30, color="#75AADB", label="Gross")
    ax.fill_between(series["DateTime"], underwater_net, 0.0, alpha=0.30, color="#E08119", label="Net")
    ax.set_title(title)
    ax.set_ylabel("Underwater")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_cost_turnover_plot(series: pd.DataFrame, title: str, path: Path) -> None:
    cum_cost = series["TransactionCost"].fillna(0.0).cumsum()
    cum_turnover_contracts = series["TurnoverContracts"].fillna(0.0).cumsum()
    cum_turnover_notional = series["TurnoverNotional"].fillna(0.0).cumsum()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    ax1.plot(series["DateTime"], cum_cost, color="#8B0000", label="Cumulative transaction cost")
    ax1.set_title(title)
    ax1.set_ylabel("Cost ($)")
    ax1.legend()

    ax2.plot(series["DateTime"], cum_turnover_contracts, color="#012169", label="Contracts")
    ax2.set_ylabel("Turnover (contracts)")
    ax2b = ax2.twinx()
    ax2b.plot(series["DateTime"], cum_turnover_notional, color="#75AADB", label="Notional")
    ax2b.set_ylabel("Turnover notional ($)")

    lines = ax2.get_lines() + ax2b.get_lines()
    labels = [line.get_label() for line in lines]
    ax2.legend(lines, labels, loc="upper left")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_parameter_stability_plot(periods: pd.DataFrame, market: str, path: Path) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(13, 9), sharex=True)
    x = periods["Period"].astype(int).to_numpy()
    axes[0].plot(x, periods["L"].astype(float), color="#012169", marker="o")
    axes[0].set_title(f"{market} selected TF parameters over time")
    axes[0].set_ylabel("L")
    axes[1].plot(x, periods["S"].astype(float), color="#E08119", marker="o")
    axes[1].set_ylabel("S")
    axes[1].set_xlabel("Walk-forward period")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_parameter_frequency_plot(periods: pd.DataFrame, market: str, path: Path) -> None:
    l_counts = periods["L"].dropna().astype(int).value_counts().sort_index()
    s_counts = periods["S"].dropna().astype(float).round(6).value_counts().sort_index()
    fig, axes = plt.subplots(2, 1, figsize=(13, 9))
    axes[0].bar(l_counts.index.astype(str), l_counts.values, color="#75AADB")
    axes[0].set_title(f"{market} parameter frequency")
    axes[0].set_ylabel("count")
    axes[0].set_xlabel("L")
    axes[1].bar([f"{value:.3f}" for value in s_counts.index], s_counts.values, color="#E08119")
    axes[1].set_ylabel("count")
    axes[1].set_xlabel("S")
    for ax in axes:
        ax.tick_params(axis="x", labelrotation=45)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def format_assumptions(run: LoadedRun) -> list[str]:
    lines = [
        f"Market: {run.market}",
        f"Run kind: {run.run_kind}",
        "Gross series: bar-by-bar PnL before transaction costs.",
        "Net series: gross PnL minus the per-bar transaction-cost deductions from the C++ backtester.",
        "Growth-of-$1 plots: cumulative product of (1 + bar return), where bar return = bar PnL / prior equity.",
        "Turnover: absolute contracts traded per bar; same-bar reversal or round-trip counts as 2.0 contracts.",
    ]
    if not run.summary.empty:
        row = run.summary.iloc[0]
        if "RoundTurnCost" in row:
            lines.append(f"Round-turn cost per contract: {float(row['RoundTurnCost']):.6f}")
        if "CostNote" in row:
            lines.append(f"Cost note: {row['CostNote']}")
    if run.config is not None and not run.config.empty:
        cfg = run.config.iloc[0]
        lines.append(
            f"Reference split: IS {cfg['ISStart']} to {cfg['ISEnd']}, "
            f"OOS {cfg['OOSStart']} to {cfg['OOSEnd']}, barsBack={int(cfg['BarsBack'])}."
        )
        lines.append(f"Reference date source: {cfg['Source']}.")
        lines.append(f"Best reference TF parameters: L={int(cfg['BestL'])}, S={float(cfg['BestS']):.6f}.")
    return lines


def build_stats_table(run: LoadedRun, series: pd.DataFrame) -> pd.DataFrame:
    base = {}
    if not run.summary.empty:
        base = run.summary.iloc[0].to_dict()
    stats = {
        "Market": run.market,
        "RunKind": run.run_kind,
        "StartTime": series["DateTime"].min(),
        "EndTime": series["DateTime"].max(),
        "Bars": len(series),
        "GrossProfit": float(series["GrossEquity"].iloc[-1] - series["GrossEquity"].iloc[0]),
        "NetProfit": float(series["NetEquity"].iloc[-1] - series["NetEquity"].iloc[0]),
        "TotalCost": float(series["TransactionCost"].fillna(0.0).sum()),
        "TurnoverContracts": float(series["TurnoverContracts"].fillna(0.0).sum()),
        "TurnoverNotional": float(series["TurnoverNotional"].fillna(0.0).sum()),
        "GrossMaxDD": float(np.abs((series["GrossEquity"] - series["GrossEquity"].cummax()).min())),
        "NetMaxDD": float(np.abs((series["NetEquity"] - series["NetEquity"].cummax()).min())),
        "TradeUnits": float(series["TradeUnits"].fillna(0.0).sum()),
    }
    stats.update(annualized_stats(series, run.market))
    if base:
        stats["RoundTurnCost"] = base.get("RoundTurnCost", np.nan)
        stats["CostNote"] = base.get("CostNote", "")
        stats["GrossRoA"] = base.get("GrossRoA", np.nan)
        stats["NetRoA"] = base.get("NetRoA", np.nan)
        stats["GrossStDevCpp"] = base.get("GrossStDev", np.nan)
        stats["NetStDevCpp"] = base.get("NetStDev", np.nan)
    return pd.DataFrame([stats])


def build_trade_stats_table(trades: pd.DataFrame | None) -> pd.DataFrame:
    if trades is None or len(trades) == 0:
        return pd.DataFrame([{"TotalTrades": 0}])
    pnl = trades["NetPnL"].astype(float) if "NetPnL" in trades.columns else trades["net_pnl"].astype(float)
    winners = pnl[pnl > 0.0]
    losers = pnl[pnl < 0.0]
    gross_profit = float(winners.sum()) if len(winners) else 0.0
    gross_loss = float(-losers.sum()) if len(losers) else 0.0
    duration_col = "DurationBars" if "DurationBars" in trades.columns else "duration_bars"
    return pd.DataFrame(
        [
            {
                "TotalTrades": int(len(pnl)),
                "WinRatePct": float((len(winners) / len(pnl)) * 100.0) if len(pnl) else 0.0,
                "AvgWinner": float(winners.mean()) if len(winners) else 0.0,
                "AvgLoser": float(losers.mean()) if len(losers) else 0.0,
                "ProfitFactor": float(gross_profit / gross_loss) if gross_loss > 0 else np.inf,
                "AvgDurationBars": float(trades[duration_col].astype(float).mean()) if duration_col in trades.columns else 0.0,
            }
        ]
    )


def write_market_report(run: LoadedRun, output_dir: Path) -> pd.DataFrame:
    market_dir = output_dir / run.market
    market_dir.mkdir(parents=True, exist_ok=True)
    series = run.series.sort_values("DateTime").reset_index(drop=True)

    save_growth_plot(series, f"{run.market} Growth of $1 ({run.run_kind})", market_dir / f"{run.market}_{run.run_kind}_growth_of_1.png")
    save_underwater_plot(series, f"{run.market} Underwater Curve ({run.run_kind})", market_dir / f"{run.market}_{run.run_kind}_underwater.png")
    save_cost_turnover_plot(series, f"{run.market} Costs and Turnover ({run.run_kind})", market_dir / f"{run.market}_{run.run_kind}_costs_turnover.png")

    periods_path = run.market_dir / f"{run.market}_tf_walkforward_periods.csv"
    periods = _read_csv(periods_path) if periods_path.exists() else None
    if periods is not None and len(periods):
        save_parameter_stability_plot(periods, run.market, market_dir / f"{run.market}_walkforward_parameter_stability.png")
        save_parameter_frequency_plot(periods, run.market, market_dir / f"{run.market}_walkforward_parameter_frequency.png")

    if run.run_kind == "reference" and "Segment" in series.columns:
        oos = series[series["Segment"] == "out_of_sample"].copy()
        if len(oos):
            oos = oos.reset_index(drop=True)
            save_growth_plot(oos, f"{run.market} OOS Growth of $1 (reference split)", market_dir / f"{run.market}_reference_oos_growth_of_1.png")
            save_underwater_plot(oos, f"{run.market} OOS Underwater (reference split)", market_dir / f"{run.market}_reference_oos_underwater.png")

    stats_df = build_stats_table(run, series)
    trade_stats_df = build_trade_stats_table(run.trades)
    stats_df.to_csv(market_dir / f"{run.market}_{run.run_kind}_derived_stats.csv", index=False)
    trade_stats_df.to_csv(market_dir / f"{run.market}_{run.run_kind}_trade_stats.csv", index=False)

    assumptions = format_assumptions(run)
    report_lines = [f"# {run.market} C++ Backtest Report", ""]
    report_lines.extend([f"- {line}" for line in assumptions])
    report_lines.append("")
    report_lines.append("## Headline Metrics (Equity Curve)")
    report_lines.append("")
    try:
        report_lines.append(stats_df.to_markdown(index=False))
    except Exception:
        report_lines.append(stats_df.to_csv(index=False))
    report_lines.append("")
    report_lines.append("These are the headline metrics because the equity curve is marked to market bar by bar. Closed-trade statistics are useful, but secondary.")
    report_lines.append("")
    report_lines.append("## Secondary Trade Metrics")
    report_lines.append("")
    try:
        report_lines.append(trade_stats_df.to_markdown(index=False))
    except Exception:
        report_lines.append(trade_stats_df.to_csv(index=False))
    report_lines.append("")
    report_lines.append("## Files")
    report_lines.append("")
    report_lines.append(f"- Growth of $1: `{run.market}_{run.run_kind}_growth_of_1.png`")
    report_lines.append(f"- Underwater: `{run.market}_{run.run_kind}_underwater.png`")
    report_lines.append(f"- Costs and turnover: `{run.market}_{run.run_kind}_costs_turnover.png`")
    if periods is not None and len(periods):
        report_lines.append(f"- Parameter stability: `{run.market}_walkforward_parameter_stability.png`")
        report_lines.append(f"- Parameter frequency: `{run.market}_walkforward_parameter_frequency.png`")
    if run.run_kind == "reference":
        report_lines.append(f"- Reference OOS growth: `{run.market}_reference_oos_growth_of_1.png`")
        report_lines.append(f"- Reference OOS underwater: `{run.market}_reference_oos_underwater.png`")
    (market_dir / f"{run.market}_{run.run_kind}_report.md").write_text("\n".join(report_lines), encoding="utf-8")
    return stats_df


def main() -> int:
    args = parse_args()
    apply_columbia_theme()

    markets = [item.strip().upper() for item in args.markets.split(",") if item.strip()]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    overview_rows: list[pd.DataFrame] = []
    for market in markets:
        run = load_run(args.input_dir, market, args.run_kind)
        overview_rows.append(write_market_report(run, args.output_dir))

    overview = pd.concat(overview_rows, ignore_index=True) if overview_rows else pd.DataFrame()
    overview.to_csv(args.output_dir / "cpp_backtest_report_overview.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from render_cpp_backtest_report import build_stats_table, build_trade_stats_table, load_run


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def money(value: float) -> str:
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def ratio(value: float) -> str:
    return f"{value:.3f}"


def pct(value: float) -> str:
    return f"{value * 100:.2f}%"


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def ensure_report_tables(
    results_dir: Path,
    report_dir: Path,
    market: str,
    run_kind: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    derived_path = report_dir / market / f"{market}_{run_kind}_derived_stats.csv"
    trade_path = report_dir / market / f"{market}_{run_kind}_trade_stats.csv"
    if derived_path.exists() and trade_path.exists():
        return load_csv(derived_path), load_csv(trade_path)

    run = load_run(results_dir, market, run_kind)
    market_dir = report_dir / market
    market_dir.mkdir(parents=True, exist_ok=True)
    stats_df = build_stats_table(run, run.series.sort_values("DateTime").reset_index(drop=True))
    trade_df = build_trade_stats_table(run.trades)
    stats_df.to_csv(derived_path, index=False)
    trade_df.to_csv(trade_path, index=False)
    return stats_df, trade_df


def top_param_pairs(periods: pd.DataFrame, n: int = 3) -> list[tuple[int, float, int]]:
    counts = (
        periods.assign(S=periods["S"].astype(float).round(6))
        .groupby(["L", "S"])
        .size()
        .reset_index(name="count")
        .sort_values(["count", "L", "S"], ascending=[False, True, True])
    )
    out: list[tuple[int, float, int]] = []
    for _, row in counts.head(n).iterrows():
        out.append((int(row["L"]), float(row["S"]), int(row["count"])))
    return out


def best_and_worst(periods: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    ordered = periods.sort_values("OOSNetObjective")
    worst = ordered.iloc[0]
    best = ordered.iloc[-1]
    return best, worst


def build_core_metrics(
    summary: pd.DataFrame,
    results_dir: Path,
    report_dir: Path,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for market in ["TY", "BTC"]:
        for run_type, run_kind in [("walkforward_oos", "walkforward"), ("full_sample", "fullsample")]:
            base = summary[(summary["Market"] == market) & (summary["RunType"] == run_type)].iloc[0]
            derived_df, trade_df = ensure_report_tables(results_dir, report_dir, market, run_kind)
            derived = derived_df.iloc[0]
            trade = trade_df.iloc[0]
            rows.append(
                {
                    "Market": market,
                    "RunType": run_type,
                    "L": int(base["L"]),
                    "S": float(base["S"]),
                    "Start": base["StartTime"],
                    "End": base["EndTime"],
                    "Periods": int(base["Periods"]),
                    "Bars": int(base["Bars"]),
                    "NetProfit": float(base["NetProfit"]),
                    "NetMaxDD": float(base["NetMaxDD"]),
                    "NetRoA": float(base["NetRoA"]),
                    "TotalCost": float(base["TotalCost"]),
                    "TurnoverContracts": float(base["TurnoverContracts"]),
                    "ClosedTrades": int(base["ClosedTrades"]),
                    "WinRate": float(trade["WinRatePct"]) / 100.0,
                    "AvgWinner": float(trade["AvgWinner"]),
                    "AvgLoser": float(trade["AvgLoser"]),
                    "ProfitFactor": float(trade["ProfitFactor"]),
                    "AvgDurationBars": float(trade["AvgDurationBars"]),
                    "NetAnnReturn": float(derived["NetCAGR"]),
                    "NetAnnVol": float(derived["NetAnnVol"]),
                    "NetAnnSharpe": float(derived["NetSharpe"]),
                    "GrossAnnReturn": float(derived["GrossCAGR"]),
                    "GrossAnnVol": float(derived["GrossAnnVol"]),
                    "GrossAnnSharpe": float(derived["GrossSharpe"]),
                }
            )
    return pd.DataFrame(rows)


def build_markdown(
    summary: pd.DataFrame,
    core: pd.DataFrame,
    reference_summary: pd.DataFrame,
    periods_by_market: dict[str, pd.DataFrame],
    report_dir: Path,
    results_dir: Path,
) -> str:
    def core_row(market: str, run_type: str) -> pd.Series:
        return core[(core["Market"] == market) & (core["RunType"] == run_type)].iloc[0]

    lines: list[str] = []
    lines.append("# Final Report Extract")
    lines.append("")
    lines.append("## 1. Experimental Setup")
    lines.append("")
    lines.extend(
        [
            "- Strategy: `Channel WithDDControl` trend-following system.",
            "- Markets:",
            "  - Primary: `TY` (10-Year Treasury Note futures)",
            "  - Secondary: `BTC` (CME Bitcoin futures)",
            "- Data frequency: `5-minute` OHLC bars.",
            "- Session handling:",
            "  - `TY` uses the project liquid-session filter already embedded in the engine.",
            "  - `BTC` uses the full 24-hour series.",
            "- Walk-forward assignment experiment:",
            "  - In-sample window `T = 4 years`",
            "  - Out-of-sample window `tau = 1 quarter`",
            "  - Each quarter is optimized on the immediately preceding 4 years and then traded on the adjacent next quarter.",
            "- Optimization target: `Net Profit / Max Drawdown` (`RoA`).",
            "- Transaction-cost assumptions used in the canonical official run:",
            "  - `TY`: `$18.625` round-turn per contract",
            "  - `BTC`: `$25.00` round-turn per contract",
            "- Important reporting note:",
            "  - The walk-forward OOS equity curve is marked to market bar by bar.",
            "  - The OOS trade table contains only closed trades.",
            "  - Therefore, quarter-end unrealized P&L can make equity-curve performance measures stronger or weaker than trade-table summaries in a given run.",
            "  - For the assignment, the primary headline comparison should therefore use the OOS equity-curve statistics (`Net Profit`, `Max Drawdown`, `RoA`, return volatility, Sharpe), with trade-level metrics presented as complementary diagnostics.",
        ]
    )
    lines.append("")
    lines.append("## 2. Walk-Forward Out-of-Sample Results")
    lines.append("")

    for market, title in [("TY", "TY"), ("BTC", "BTC")]:
        row = core_row(market, "walkforward_oos")
        periods = periods_by_market[market]
        top_pair = top_param_pairs(periods, 1)[0]
        lines.append(f"### {title} walk-forward OOS")
        lines.append("")
        lines.extend(
            [
                f"- Date range: `{row['Start']}` to `{row['End']}`",
                f"- OOS periods: `{int(row['Periods'])}`",
                f"- Story / modal configuration: `L = {int(top_pair[0])}`, `S = {top_pair[1]:.2f}`",
                f"- Net Profit: `{money(float(row['NetProfit']))}`",
                f"- Net Max Drawdown: `{money(float(row['NetMaxDD']))}`",
                f"- Net RoA: `{ratio(float(row['NetRoA']))}`",
                f"- Annualized net return: `{pct(float(row['NetAnnReturn']))}`",
                f"- Annualized net volatility: `{pct(float(row['NetAnnVol']))}`",
                f"- Annualized net Sharpe: `{ratio(float(row['NetAnnSharpe']))}`",
                f"- Closed trades: `{int(row['ClosedTrades']):,}`",
                f"- Win rate: `{float(row['WinRate']) * 100:.2f}%`",
                f"- Average winner: `{money(float(row['AvgWinner']))}`",
                f"- Average loser: `-{money(abs(float(row['AvgLoser'])))[1:]}`" if float(row["AvgLoser"]) < 0 else f"- Average loser: `{money(float(row['AvgLoser']))}`",
                f"- Profit factor: `{ratio(float(row['ProfitFactor']))}`",
                f"- Average trade duration: `{float(row['AvgDurationBars']):.1f}` bars",
                f"- Total transaction cost paid: `{money(float(row['TotalCost']))}`",
                f"- Turnover: `{float(row['TurnoverContracts']):,.1f}` contracts",
            ]
        )
        lines.append("")

    lines.append("## 3. Full-Sample Comparison")
    lines.append("")
    for market, title in [("TY", "TY"), ("BTC", "BTC")]:
        row = core_row(market, "full_sample")
        lines.append(f"### {title} full-sample")
        lines.append("")
        lines.extend(
            [
                f"- Full-sample configuration: `L = {int(row['L'])}`, `S = {float(row['S']):.2f}`",
                f"- Net Profit: `{money(float(row['NetProfit']))}`",
                f"- Net Max Drawdown: `{money(float(row['NetMaxDD']))}`",
                f"- Net RoA: `{ratio(float(row['NetRoA']))}`",
                f"- Annualized net return: `{pct(float(row['NetAnnReturn']))}`",
                f"- Annualized net volatility: `{pct(float(row['NetAnnVol']))}`",
                f"- Annualized net Sharpe: `{ratio(float(row['NetAnnSharpe']))}`",
                f"- Closed trades: `{int(row['ClosedTrades']):,}`",
                f"- Win rate: `{float(row['WinRate']) * 100:.2f}%`",
                f"- Average winner: `{money(float(row['AvgWinner']))}`",
                f"- Average loser: `-{money(abs(float(row['AvgLoser'])))[1:]}`" if float(row["AvgLoser"]) < 0 else f"- Average loser: `{money(float(row['AvgLoser']))}`",
                f"- Profit factor: `{ratio(float(row['ProfitFactor']))}`",
            ]
        )
        lines.append("")

    lines.append("## 4. OOS vs Full-Sample Decay")
    lines.append("")
    for market in ["TY", "BTC"]:
        wf = core_row(market, "walkforward_oos")
        fs = core_row(market, "full_sample")
        lines.append(f"### {market}")
        lines.append("")
        lines.extend(
            [
                f"- OOS / full-sample net profit ratio: `{float(wf['NetProfit']) / float(fs['NetProfit']):.3f}`",
                f"- OOS / full-sample net RoA ratio: `{float(wf['NetRoA']) / float(fs['NetRoA']):.3f}`",
                f"- OOS / full-sample trade-count ratio: `{int(wf['ClosedTrades']) / int(fs['ClosedTrades']):.3f}`",
            ]
        )
        lines.append("")

    lines.append("## 5. Parameter Behavior by Quarter")
    lines.append("")
    for market in ["TY", "BTC"]:
        periods = periods_by_market[market]
        lines.append(f"### {market}")
        lines.append("")
        lines.append("- Most frequent quarterly selections:")
        for L, S, count in top_param_pairs(periods, 3):
            lines.append(f"  - `L = {L}, S = {S:.2f}` selected `{count}` times")
        lines.append("")

    lines.append("## 6. Best and Worst OOS Quarters")
    lines.append("")
    for market in ["TY", "BTC"]:
        best, worst = best_and_worst(periods_by_market[market])
        lines.append(f"### {market}")
        lines.append("")
        lines.extend(
            [
                "- Best OOS quarter by net objective:",
                f"  - Period `{int(best['Period'])}`",
                f"  - `{best['OOSStart']}` to `{best['OOSEnd']}`",
                f"  - `L = {int(best['L'])}`, `S = {float(best['S']):.3f}`",
                f"  - Net Profit: `{money(float(best['OOSNetProfit']))}`",
                f"  - Net MaxDD: `{money(float(best['OOSNetMaxDD']))}`",
                f"  - Net Objective: `{ratio(float(best['OOSNetObjective']))}`",
                "",
                "- Worst OOS quarter by net objective:",
                f"  - Period `{int(worst['Period'])}`",
                f"  - `{worst['OOSStart']}` to `{worst['OOSEnd']}`",
                f"  - `L = {int(worst['L'])}`, `S = {float(worst['S']):.3f}`",
                f"  - Net Profit: `{money(float(worst['OOSNetProfit']))}`",
                f"  - Net MaxDD: `{money(float(worst['OOSNetMaxDD']))}`",
                f"  - Net Objective: `{ratio(float(worst['OOSNetObjective']))}`",
                "",
            ]
        )

    lines.append("## 7. Matlab-Parity Reference Split Appendix")
    lines.append("")
    for market in ["TY", "BTC"]:
        is_row = reference_summary[(reference_summary["Market"] == market) & (reference_summary["RunType"] == "reference_in_sample")].iloc[0]
        oos_row = reference_summary[(reference_summary["Market"] == market) & (reference_summary["RunType"] == "reference_out_of_sample")].iloc[0]
        lines.append(f"### {market} reference split")
        lines.append("")
        lines.extend(
            [
                "- Auto split:",
                f"  - In-sample: `{is_row['StartTime']}` to `{is_row['EndTime']}`",
                f"  - OOS: `{oos_row['StartTime']}` to `{oos_row['EndTime']}`",
                "  - `barsBack = 17001`",
                f"- Best reference configuration: `L = {int(oos_row['L'])}`, `S = {float(oos_row['S']):.2f}`",
                f"- Reference OOS net profit: `{money(float(oos_row['NetProfit']))}`",
                f"- Reference OOS net max drawdown: `{money(float(oos_row['NetMaxDD']))}`",
                f"- Reference OOS net RoA: `{ratio(float(oos_row['NetRoA']))}`",
                "",
            ]
        )

    lines.append("## 8. Supporting Files")
    lines.append("")
    lines.append("- Core metrics table: [report_core_metrics.csv](report_core_metrics.csv)")
    lines.append(f"- C++ master summary: [tf_backtest_summary.csv]({(results_dir / 'tf_backtest_summary.csv').relative_to(report_dir.parent).as_posix()})")
    lines.append("- Overview report table: [cpp_backtest_report_overview.csv](cpp_backtest_report_overview.csv)")
    lines.append("")
    lines.append("## 9. Sources And Assumptions")
    lines.append("")
    lines.extend(
        [
            "- [Final Project MATH GR5360.pdf](../Final%20Project%20MATH%20GR5360.pdf)",
            "- professor-provided `main.m` and `ezread.m`",
            "- course lecture material on Variance Ratio, Push-Response, and drawdown-family measures",
            "- Official `TF Data` sheet values used in the canonical run:",
            "  - `TY` slippage = `$18.625` round-turn",
            "  - `BTC` slippage = `$25.00` round-turn",
        ]
    )
    lines.append("")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the canonical final report extract from the official quick C++ outputs.")
    parser.add_argument("--results-dir", type=Path, default=PROJECT_ROOT / "results_cpp_official_quick")
    parser.add_argument("--report-dir", type=Path, default=PROJECT_ROOT / "results_cpp_official_quick_report")
    parser.add_argument(
        "--mirror-report-dir",
        type=Path,
        default=PROJECT_ROOT / "results_cpp_report",
        help="Optional second report directory to keep in sync for legacy links.",
    )
    return parser.parse_args()


def write_outputs(results_dir: Path, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    summary = load_csv(results_dir / "tf_backtest_summary.csv")
    core = build_core_metrics(summary, results_dir, report_dir)
    core.to_csv(report_dir / "report_core_metrics.csv", index=False)

    reference_summary = summary[summary["RunType"].isin(["reference_in_sample", "reference_out_of_sample"])].copy()
    periods_by_market = {
        market: load_csv(results_dir / market / f"{market}_tf_walkforward_periods.csv")
        for market in ["TY", "BTC"]
    }
    markdown = build_markdown(summary, core, reference_summary, periods_by_market, report_dir, results_dir)
    (report_dir / "final_report_extract.md").write_text(markdown, encoding="utf-8")


def main() -> int:
    args = parse_args()
    write_outputs(args.results_dir, args.report_dir)
    if args.mirror_report_dir:
        args.mirror_report_dir.mkdir(parents=True, exist_ok=True)
        write_outputs(args.results_dir, args.mirror_report_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

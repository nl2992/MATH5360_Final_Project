from __future__ import annotations

import argparse
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

from mafn_engine import (
    COLUMBIA_CORE,
    COLUMBIA_WARM,
    apply_columbia_theme,
    get_market,
    load_ohlc,
    performance_from_ledger,
    prepare_analysis_frame,
    run_backtest,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Replay walk-forward OOS periods at multiple cost levels using fixed selected parameters.")
    parser.add_argument("--input-dir", type=Path, default=PROJECT_ROOT / "results_cpp_official_quick")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results_cost_sensitivity_fixed")
    parser.add_argument("--markets", type=str, default="TY,BTC")
    parser.add_argument("--multipliers", type=str, default="0,0.5,1,2")
    return parser.parse_args()


def _concat_equity(e0: float, chunks: list[pd.Series]) -> pd.DataFrame:
    if not chunks:
        return pd.DataFrame(columns=["OOS_PnL_cum", "OOS_Equity"])
    pnl = pd.concat(chunks)
    pnl = pnl[~pnl.index.duplicated(keep="first")]
    cum_pnl = pnl.cumsum()
    return pd.DataFrame({"OOS_PnL_cum": cum_pnl, "OOS_Equity": e0 + cum_pnl})


def replay_period_table(
    analysis_df: pd.DataFrame,
    ticker: str,
    periods_df: pd.DataFrame,
    cost_multiplier: float,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, float]]:
    spec = get_market(ticker)
    chunks: list[pd.Series] = []
    ledgers: list[pd.DataFrame] = []
    start_col = "OOS_start" if "OOS_start" in periods_df.columns else "OOSStart"
    end_col = "OOS_end" if "OOS_end" in periods_df.columns else "OOSEnd"

    for _, row in periods_df.iterrows():
        oos_start = pd.to_datetime(row[start_col])
        oos_end = pd.to_datetime(row[end_col])
        start_idx = int(analysis_df.index.get_indexer([oos_start])[0])
        end_lookup = int(analysis_df.index.get_indexer([oos_end])[0])
        if start_idx < 0 or end_lookup < 0:
            raise KeyError(f"Could not align OOS window {oos_start} -> {oos_end} in {ticker} analysis frame.")
        end_idx = end_lookup + 1
        result = run_backtest(
            analysis_df,
            ticker,
            "tf",
            {"L": int(row["L"]), "S": float(row["S"])},
            eval_start=start_idx,
            eval_end=end_idx,
            round_turn_cost=spec.slpg,
            cost_multiplier=cost_multiplier,
        )
        local_start = start_idx - int(result["SliceStart"])
        local_end = end_idx - int(result["SliceStart"])
        oos_equity = np.asarray(result["Equity"][local_start:local_end], dtype=float)
        oos_pnl = np.diff(np.r_[spec.E0, oos_equity])
        chunks.append(pd.Series(oos_pnl, index=analysis_df.index[start_idx:end_idx], name="OOS_PnL"))
        ledger = result["Ledger"]
        if len(ledger):
            ledger = ledger[ledger["is_oos"]].copy()
            ledger.insert(0, "Period", int(row["Period"]))
            ledgers.append(ledger)

    equity = _concat_equity(spec.E0, chunks)
    ledger_df = pd.concat(ledgers, ignore_index=True) if ledgers else pd.DataFrame()
    metrics = performance_from_ledger(
        ledger_df,
        equity["OOS_Equity"].to_numpy(dtype=float) if len(equity) else np.array([spec.E0]),
        ticker,
    )
    return equity, ledger_df, metrics


def save_metric_plot(df: pd.DataFrame, market: str, metric: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["CostMultiplier"], df[metric], marker="o", color=COLUMBIA_CORE if metric != "Total Profit" else COLUMBIA_WARM)
    ax.set_title(f"{market} {metric} vs cost multiplier")
    ax.set_xlabel("cost multiplier")
    ax.set_ylabel(metric)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    apply_columbia_theme()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    multipliers = [float(item.strip()) for item in args.multipliers.split(",") if item.strip()]
    markets = [item.strip().upper() for item in args.markets.split(",") if item.strip()]

    overview_rows: list[dict[str, float | str]] = []
    for ticker in markets:
        full_df = load_ohlc(str(args.data_dir), ticker, fallback_synthetic=False)
        analysis_df = prepare_analysis_frame(full_df, ticker)
        periods_df = pd.read_csv(args.input_dir / ticker / f"{ticker}_tf_walkforward_periods.csv")
        market_dir = args.output_dir / ticker
        market_dir.mkdir(parents=True, exist_ok=True)

        for multiplier in multipliers:
            equity, ledger, metrics = replay_period_table(analysis_df, ticker, periods_df, multiplier)
            scenario = f"cost_{str(multiplier).replace('.', 'p')}x"
            if len(equity):
                equity.to_csv(market_dir / f"{ticker}_{scenario}_equity.csv", index_label="DateTime")
            if len(ledger):
                ledger.to_csv(market_dir / f"{ticker}_{scenario}_trades.csv", index=False)
            row = {"Ticker": ticker, "CostMultiplier": multiplier}
            row.update(metrics)
            overview_rows.append(row)

    overview = pd.DataFrame(overview_rows)
    overview.to_csv(args.output_dir / "cost_sensitivity_summary.csv", index=False)
    for ticker in markets:
        market_df = overview[overview["Ticker"] == ticker].sort_values("CostMultiplier")
        save_metric_plot(market_df, ticker, "Total Profit", args.output_dir / f"{ticker}_cost_sensitivity_profit.png")
        save_metric_plot(market_df, ticker, "Sharpe Ratio", args.output_dir / f"{ticker}_cost_sensitivity_sharpe.png")
        save_metric_plot(market_df, ticker, "Return on Account", args.output_dir / f"{ticker}_cost_sensitivity_roa.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

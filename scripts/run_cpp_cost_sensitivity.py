from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mafn_engine import COLUMBIA_CORE, COLUMBIA_NAVY, COLUMBIA_WARM, apply_columbia_theme, get_market


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run zero / half / base / double cost sensitivity for the C++ TF backtester.")
    parser.add_argument("--binary", type=Path, default=PROJECT_ROOT / "cpp" / "tf_backtest_treasury_btc")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--out-root", type=Path, default=PROJECT_ROOT / "results_cpp_cost_sensitivity")
    parser.add_argument("--markets", type=str, default="TY,BTC")
    parser.add_argument("--mode", choices=["walkforward", "reference", "both"], default="both")
    parser.add_argument("--grid-mode", choices=["quick", "strict"], default="quick")
    parser.add_argument("--is-years", type=int, default=4)
    parser.add_argument("--oos-quarters", type=int, default=1)
    parser.add_argument("--multipliers", type=str, default="0,0.5,1,2")
    return parser.parse_args()


def scenario_name(multiplier: float) -> str:
    return f"cost_{str(multiplier).replace('.', 'p')}x"


def run_scenario(args: argparse.Namespace, multiplier: float) -> Path:
    out_dir = args.out_root / scenario_name(multiplier)
    out_dir.mkdir(parents=True, exist_ok=True)
    ty_cost = get_market("TY").slpg * multiplier
    btc_cost = get_market("BTC").slpg * multiplier
    cmd = [
        str(args.binary),
        "--data-root",
        str(args.data_dir),
        "--out-dir",
        str(out_dir),
        "--mode",
        args.mode,
        "--grid-mode",
        args.grid_mode,
        "--markets",
        args.markets,
        "--is-years",
        str(args.is_years),
        "--oos-quarters",
        str(args.oos_quarters),
        "--ty-rt-cost",
        str(ty_cost),
        "--btc-rt-cost",
        str(btc_cost),
    ]
    subprocess.run(cmd, check=True, cwd=str(PROJECT_ROOT))
    return out_dir


def save_metric_plot(df: pd.DataFrame, market: str, metric: str, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df["CostMultiplier"], df[metric], marker="o", color=COLUMBIA_CORE if metric != "TotalCost" else COLUMBIA_WARM)
    ax.set_title(f"{market} {metric} vs slippage multiplier")
    ax.set_xlabel("slippage multiplier")
    ax.set_ylabel(metric)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def main() -> int:
    args = parse_args()
    apply_columbia_theme()
    args.out_root.mkdir(parents=True, exist_ok=True)
    multipliers = [float(item.strip()) for item in args.multipliers.split(",") if item.strip()]

    frames: list[pd.DataFrame] = []
    for multiplier in multipliers:
        out_dir = run_scenario(args, multiplier)
        summary = pd.read_csv(out_dir / "tf_backtest_summary.csv")
        summary.insert(0, "Scenario", scenario_name(multiplier))
        summary.insert(1, "CostMultiplier", multiplier)
        frames.append(summary)

    combined = pd.concat(frames, ignore_index=True)
    combined.to_csv(args.out_root / "combined_cost_sensitivity_summary.csv", index=False)

    markets = [item.strip().upper() for item in args.markets.split(",") if item.strip()]
    for market in markets:
        market_df = combined[(combined["Market"] == market) & (combined["RunType"] == "walkforward_oos")].copy()
        if not len(market_df):
            continue
        market_df = market_df.sort_values("CostMultiplier")
        save_metric_plot(market_df, market, "NetProfit", args.out_root / f"{market}_cost_sensitivity_net_profit.png")
        save_metric_plot(market_df, market, "NetRoA", args.out_root / f"{market}_cost_sensitivity_net_roa.png")
        save_metric_plot(market_df, market, "TotalCost", args.out_root / f"{market}_cost_sensitivity_total_cost.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

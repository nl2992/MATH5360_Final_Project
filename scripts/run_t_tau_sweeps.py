from __future__ import annotations

import argparse
from pathlib import Path
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mafn_engine import (
    COLUMBIA_CMAP,
    apply_columbia_theme,
    load_ohlc,
    prepare_analysis_frame,
    walk_forward_surface,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run T/tau walk-forward sweeps for TY and BTC.")
    parser.add_argument("--data-dir", type=Path, default=PROJECT_ROOT / "data")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "results_t_tau_sweeps")
    parser.add_argument("--markets", type=str, default="TY,BTC")
    parser.add_argument("--grid-mode", choices=["quick", "strict"], default="quick")
    parser.add_argument("--cost-multiplier", type=float, default=1.0)
    parser.add_argument("--skip-quarters", action="store_true")
    parser.add_argument("--skip-months", action="store_true")
    return parser.parse_args()


def save_heatmap(surface_df: pd.DataFrame, value_col: str, title: str, path: Path) -> None:
    pivot = surface_df.pivot(index="T", columns="tau", values=value_col).sort_index().sort_index(axis=1)
    fig, ax = plt.subplots(figsize=(10, 7))
    im = ax.imshow(pivot.to_numpy(dtype=float), aspect="auto", cmap=COLUMBIA_CMAP, origin="lower")
    ax.set_title(title)
    ax.set_xlabel("tau")
    ax.set_ylabel("T (years)")
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([str(col) for col in pivot.columns])
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels([str(idx) for idx in pivot.index])
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    fig.savefig(path, dpi=220)
    plt.close(fig)


def run_surface_for_market(
    ticker: str,
    data_dir: Path,
    output_dir: Path,
    grid_mode: str,
    tau_unit: str,
    tau_values: list[int],
    cost_multiplier: float,
) -> pd.DataFrame:
    full_df = load_ohlc(str(data_dir), ticker, fallback_synthetic=False)
    analysis_df = prepare_analysis_frame(full_df, ticker)
    surface_df = walk_forward_surface(
        analysis_df,
        ticker,
        mode="tf",
        T_values=list(range(1, 11)),
        tau_values=tau_values,
        tau_unit=tau_unit,
        quick=(grid_mode == "quick"),
        verbose=False,
        cost_multiplier=cost_multiplier,
    )
    market_dir = output_dir / ticker
    market_dir.mkdir(parents=True, exist_ok=True)
    csv_path = market_dir / f"{ticker}_surface_{tau_unit}.csv"
    surface_df.to_csv(csv_path, index=False)
    clean = surface_df[~surface_df["error"]].copy() if "error" in surface_df.columns else surface_df.copy()
    if len(clean):
        save_heatmap(clean, "avg_oos", f"{ticker} avg OOS objective ({tau_unit})", market_dir / f"{ticker}_{tau_unit}_avg_oos.png")
        save_heatmap(clean, "decay", f"{ticker} OOS/IS decay ({tau_unit})", market_dir / f"{ticker}_{tau_unit}_decay.png")
        save_heatmap(clean, "total_oos", f"{ticker} total OOS profit ({tau_unit})", market_dir / f"{ticker}_{tau_unit}_total_oos.png")
    return surface_df


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    apply_columbia_theme()

    markets = [item.strip().upper() for item in args.markets.split(",") if item.strip()]
    frames: list[pd.DataFrame] = []
    for ticker in markets:
        if not args.skip_quarters:
            quarter_df = run_surface_for_market(
                ticker,
                args.data_dir,
                args.output_dir,
                args.grid_mode,
                "quarters",
                [1, 2, 3, 4],
                args.cost_multiplier,
            )
            quarter_df.insert(0, "Ticker", ticker)
            frames.append(quarter_df)
        if not args.skip_months:
            month_df = run_surface_for_market(
                ticker,
                args.data_dir,
                args.output_dir,
                args.grid_mode,
                "months",
                list(range(1, 13)),
                args.cost_multiplier,
            )
            month_df.insert(0, "Ticker", ticker)
            frames.append(month_df)

    if frames:
        pd.concat(frames, ignore_index=True).to_csv(args.output_dir / "combined_surface_sweeps.csv", index=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

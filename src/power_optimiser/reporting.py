from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def write_summary(summary_df: pd.DataFrame, output_dir: str) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / "scenario_summary.csv"
    summary_df.to_csv(output_path, index=False)
    return output_path


def save_savings_chart(summary_df: pd.DataFrame, output_dir: str) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    for rte, group in summary_df.groupby("round_trip_efficiency"):
        ordered = group.sort_values("capacity_kwh")
        ax.plot(
            ordered["capacity_kwh"],
            ordered["savings_vs_no_battery_gbp"],
            marker="o",
            label=f"RTE {int(rte * 100)}%",
        )

    ax.set_title("Battery size vs annual savings")
    ax.set_xlabel("Usable battery capacity (kWh)")
    ax.set_ylabel("Annual savings vs no battery (£)")
    ax.grid(True, alpha=0.3)
    ax.legend()

    chart_path = out_dir / "battery_size_vs_savings.png"
    fig.tight_layout()
    fig.savefig(chart_path, dpi=150)
    plt.close(fig)
    return chart_path

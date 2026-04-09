from __future__ import annotations

from pathlib import Path

import pandas as pd

from power_optimiser.battery import optimise_battery_dispatch
from power_optimiser.config import load_config
from power_optimiser.data import ensure_database, load_input_data
from power_optimiser.reporting import save_savings_chart, write_summary
from power_optimiser.tariffs import baseline_costs


def run_model(config_path: str, csv_path: str, use_live_agile_prices: bool = False) -> pd.DataFrame:
    """Run scenario analysis and write outputs.

    Args:
        config_path: Path to YAML run configuration.
        csv_path: Path to half-hourly input CSV.
        use_live_agile_prices: Reserved flag for live Agile integration.

    Returns:
        DataFrame with one row per scenario and baseline comparison metrics.
    """
    _ = use_live_agile_prices

    config = load_config(config_path)
    ensure_database(config.db_path, csv_path, config.input_table)
    df = load_input_data(config.db_path, config.input_table)

    base = baseline_costs(df)
    no_battery_agile_cost = base["agile_cost_gbp"]

    results: list[dict[str, float | str]] = []

    for scenario in config.build_scenarios():
        result, dispatch = optimise_battery_dispatch(df, scenario, config.interval_hours)
        results.append(result.to_dict())

        dispatch_path = Path(config.output_dir) / f"dispatch_{scenario.name}.csv"
        dispatch_path.parent.mkdir(parents=True, exist_ok=True)
        dispatch.to_csv(dispatch_path, index=False)

    summary_df = pd.DataFrame(results)
    summary_df["no_battery_agile_cost_gbp"] = no_battery_agile_cost
    summary_df["flexible_cost_gbp"] = base["flexible_cost_gbp"]
    summary_df["agile_vs_flexible_saving_gbp"] = base["agile_vs_flexible_saving_gbp"]
    summary_df["agile_vs_flexible_saving_pct"] = base["agile_vs_flexible_saving_pct"]

    write_summary(summary_df, config.output_dir)
    save_savings_chart(summary_df, config.output_dir)

    return summary_df

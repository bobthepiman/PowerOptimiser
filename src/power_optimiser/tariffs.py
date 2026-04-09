from __future__ import annotations

import pandas as pd


def calculate_import_cost_pence(consumption_kwh: pd.Series, import_price_p_per_kwh: pd.Series) -> float:
    return float((consumption_kwh * import_price_p_per_kwh).sum())


def baseline_costs(df: pd.DataFrame) -> dict[str, float]:
    flexible_cost_p = calculate_import_cost_pence(df["consumption_kwh"], df["flexible_import_p_per_kwh"])
    agile_cost_p = calculate_import_cost_pence(df["consumption_kwh"], df["agile_import_p_per_kwh"])

    return {
        "flexible_cost_gbp": flexible_cost_p / 100.0,
        "agile_cost_gbp": agile_cost_p / 100.0,
        "agile_vs_flexible_saving_gbp": (flexible_cost_p - agile_cost_p) / 100.0,
        "agile_vs_flexible_saving_pct": ((flexible_cost_p - agile_cost_p) / flexible_cost_p * 100.0)
        if flexible_cost_p > 0
        else 0.0,
    }

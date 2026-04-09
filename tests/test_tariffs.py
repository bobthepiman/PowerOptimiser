from __future__ import annotations

import pandas as pd

from power_optimiser.tariffs import baseline_costs, calculate_import_cost_pence


def test_calculate_import_cost_pence() -> None:
    consumption = pd.Series([1.0, 2.0, 0.5])
    price = pd.Series([10.0, 20.0, 30.0])
    assert calculate_import_cost_pence(consumption, price) == 65.0


def test_baseline_costs_agile_cheaper() -> None:
    df = pd.DataFrame(
        {
            "consumption_kwh": [1.0, 1.0],
            "agile_import_p_per_kwh": [10.0, 20.0],
            "flexible_import_p_per_kwh": [30.0, 30.0],
        }
    )
    costs = baseline_costs(df)
    assert costs["flexible_cost_gbp"] == 0.6
    assert costs["agile_cost_gbp"] == 0.3
    assert costs["agile_vs_flexible_saving_gbp"] == 0.3

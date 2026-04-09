from __future__ import annotations

import pandas as pd

from power_optimiser.battery import optimise_battery_dispatch
from power_optimiser.config import BatteryScenario


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01", periods=4, freq="30min", tz="UTC"),
            "consumption_kwh": [1.0, 1.0, 1.0, 1.0],
            "agile_import_p_per_kwh": [10.0, 10.0, 40.0, 40.0],
        }
    )


def test_soc_constraints_respected() -> None:
    scenario = BatteryScenario(
        name="test",
        capacity_kwh=2.0,
        max_charge_kw=2.0,
        max_discharge_kw=2.0,
        round_trip_efficiency=0.85,
        initial_soc_kwh=1.0,
    )
    _, dispatch = optimise_battery_dispatch(_sample_df(), scenario, interval_hours=0.5)

    assert dispatch["soc_kwh_start"].between(0.0, scenario.capacity_kwh).all()
    assert dispatch["soc_kwh_end"].between(0.0, scenario.capacity_kwh).all()


def test_battery_reduces_cost_when_spread_exists() -> None:
    scenario = BatteryScenario(
        name="test_spread",
        capacity_kwh=2.0,
        max_charge_kw=2.0,
        max_discharge_kw=2.0,
        round_trip_efficiency=0.85,
        initial_soc_kwh=0.0,
    )
    result, dispatch = optimise_battery_dispatch(_sample_df(), scenario, interval_hours=0.5)

    baseline_gbp = float((_sample_df()["consumption_kwh"] * _sample_df()["agile_import_p_per_kwh"]).sum() / 100.0)
    assert result.annual_cost_gbp < baseline_gbp
    assert (dispatch["grid_import_kwh"] >= 0).all()

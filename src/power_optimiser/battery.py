from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd
import pulp

from power_optimiser.config import BatteryScenario


@dataclass(frozen=True)
class BatteryResult:
    scenario_name: str
    capacity_kwh: float
    round_trip_efficiency: float
    annual_cost_gbp: float
    savings_vs_no_battery_gbp: float
    value_per_installed_kwh_gbp: float
    equivalent_full_cycles: float

    def to_dict(self) -> dict[str, float | str]:
        return asdict(self)


def optimise_battery_dispatch(
    df: pd.DataFrame,
    scenario: BatteryScenario,
    interval_hours: float,
) -> tuple[BatteryResult, pd.DataFrame]:
    n = len(df)
    eta_c = scenario.round_trip_efficiency ** 0.5
    eta_d = scenario.round_trip_efficiency ** 0.5

    model = pulp.LpProblem(f"dispatch_{scenario.name}", pulp.LpMinimize)

    charge = pulp.LpVariable.dicts("charge", range(n), lowBound=0)
    discharge = pulp.LpVariable.dicts("discharge", range(n), lowBound=0)
    soc = pulp.LpVariable.dicts("soc", range(n + 1), lowBound=0, upBound=scenario.capacity_kwh)

    model += soc[0] == scenario.initial_soc_kwh

    max_charge_kwh_per_interval = scenario.max_charge_kw * interval_hours
    max_discharge_kwh_per_interval = scenario.max_discharge_kw * interval_hours

    for t in range(n):
        load = float(df.iloc[t]["consumption_kwh"])
        model += charge[t] <= max_charge_kwh_per_interval
        model += discharge[t] <= max_discharge_kwh_per_interval
        model += discharge[t] <= load
        model += soc[t + 1] == soc[t] + (eta_c * charge[t]) - (discharge[t] / eta_d)

    objective_terms = []
    for t in range(n):
        price = float(df.iloc[t]["agile_import_p_per_kwh"])
        load = float(df.iloc[t]["consumption_kwh"])
        grid_import = load - discharge[t] + charge[t]
        objective_terms.append(price * grid_import)

    model += pulp.lpSum(objective_terms)

    status = model.solve(pulp.PULP_CBC_CMD(msg=False))
    if pulp.LpStatus[status] != "Optimal":
        raise RuntimeError(f"Battery optimisation did not converge for {scenario.name}")

    dispatch = df[["timestamp", "consumption_kwh", "agile_import_p_per_kwh"]].copy()
    dispatch["charge_kwh"] = [float(charge[t].value()) for t in range(n)]
    dispatch["discharge_kwh"] = [float(discharge[t].value()) for t in range(n)]
    dispatch["soc_kwh_start"] = [float(soc[t].value()) for t in range(n)]
    dispatch["soc_kwh_end"] = [float(soc[t + 1].value()) for t in range(n)]
    dispatch["grid_import_kwh"] = (
        dispatch["consumption_kwh"] - dispatch["discharge_kwh"] + dispatch["charge_kwh"]
    )
    dispatch["cost_pence"] = dispatch["grid_import_kwh"] * dispatch["agile_import_p_per_kwh"]

    no_battery_cost_gbp = float((df["consumption_kwh"] * df["agile_import_p_per_kwh"]).sum() / 100.0)
    with_battery_cost_gbp = float(dispatch["cost_pence"].sum() / 100.0)
    savings = no_battery_cost_gbp - with_battery_cost_gbp
    full_cycles = (
        float(dispatch["discharge_kwh"].sum() / scenario.capacity_kwh) if scenario.capacity_kwh > 0 else 0.0
    )

    result = BatteryResult(
        scenario_name=scenario.name,
        capacity_kwh=scenario.capacity_kwh,
        round_trip_efficiency=scenario.round_trip_efficiency,
        annual_cost_gbp=with_battery_cost_gbp,
        savings_vs_no_battery_gbp=savings,
        value_per_installed_kwh_gbp=(savings / scenario.capacity_kwh) if scenario.capacity_kwh > 0 else 0.0,
        equivalent_full_cycles=full_cycles,
    )

    return result, dispatch

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class BatteryScenario:
    name: str
    capacity_kwh: float
    max_charge_kw: float
    max_discharge_kw: float
    round_trip_efficiency: float
    initial_soc_kwh: float


@dataclass(frozen=True)
class RunConfig:
    db_path: str
    input_table: str
    output_dir: str
    interval_hours: float
    battery_capacities_kwh: list[float]
    round_trip_efficiencies: list[float]
    max_charge_kw: float
    max_discharge_kw: float
    initial_soc_fraction: float

    def build_scenarios(self) -> list[BatteryScenario]:
        scenarios: list[BatteryScenario] = []
        for rte in self.round_trip_efficiencies:
            for capacity in self.battery_capacities_kwh:
                scenarios.append(
                    BatteryScenario(
                        name=f"battery_{int(capacity)}kwh_rte_{int(rte*100)}",
                        capacity_kwh=capacity,
                        max_charge_kw=self.max_charge_kw,
                        max_discharge_kw=self.max_discharge_kw,
                        round_trip_efficiency=rte,
                        initial_soc_kwh=capacity * self.initial_soc_fraction,
                    )
                )
        return scenarios


def load_config(path: str | Path) -> RunConfig:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw: dict[str, Any] = yaml.safe_load(handle)

    return RunConfig(
        db_path=raw["data"]["db_path"],
        input_table=raw["data"]["input_table"],
        output_dir=raw["outputs"]["output_dir"],
        interval_hours=float(raw["model"]["interval_hours"]),
        battery_capacities_kwh=[float(x) for x in raw["model"]["battery_capacities_kwh"]],
        round_trip_efficiencies=[float(x) for x in raw["model"]["round_trip_efficiencies"]],
        max_charge_kw=float(raw["model"]["max_charge_kw"]),
        max_discharge_kw=float(raw["model"]["max_discharge_kw"]),
        initial_soc_fraction=float(raw["model"]["initial_soc_fraction"]),
    )

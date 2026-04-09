from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from power_optimiser.web import app


@dataclass
class _FakeConfig:
    output_dir: str


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_endpoint_returns_summary_rows_and_output_paths(monkeypatch, tmp_path: Path) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    chart_path = output_dir / "battery_size_vs_savings.png"
    chart_path.write_bytes(b"png-bytes")

    captured: dict[str, object] = {}

    def _fake_run_model(config_path: str, csv_path: str, use_live_agile_prices: bool = False) -> pd.DataFrame:
        captured["config_path"] = config_path
        captured["csv_path"] = csv_path
        captured["use_live_agile_prices"] = use_live_agile_prices
        return pd.DataFrame([
            {"scenario": "battery_5kwh_rte_85", "savings_vs_no_battery_gbp": 123.45}
        ])

    def _fake_load_config(_: str) -> _FakeConfig:
        return _FakeConfig(output_dir=str(output_dir))

    monkeypatch.setattr("power_optimiser.web.run_model", _fake_run_model)
    monkeypatch.setattr("power_optimiser.web.load_config", _fake_load_config)

    client = TestClient(app)
    response = client.post(
        "/run",
        json={
            "config_path": "configs/default.yaml",
            "input_csv": "data/sample_half_hourly_input.csv",
            "use_live_agile_prices": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["summary_rows"][0]["scenario"] == "battery_5kwh_rte_85"
    assert payload["output_files"]["summary_csv"].endswith("scenario_summary.csv")
    assert payload["output_files"]["chart"].endswith("battery_size_vs_savings.png")
    assert captured == {
        "config_path": "configs/default.yaml",
        "csv_path": "data/sample_half_hourly_input.csv",
        "use_live_agile_prices": True,
    }

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from power_optimiser.config import load_config
from power_optimiser.main import run_model

DEFAULT_CONFIG_PATH = "configs/default.yaml"
DEFAULT_INPUT_CSV = "data/sample_half_hourly_input.csv"

app = FastAPI(title="Power Optimiser API", version="0.1.0")


class RunRequest(BaseModel):
    config_path: str | None = None
    input_csv: str | None = None
    use_live_agile_prices: bool | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(
    payload: RunRequest | None = None,
    config_path: str | None = Query(default=None),
    input_csv: str | None = Query(default=None),
    use_live_agile_prices: bool | None = Query(default=None),
) -> dict[str, Any]:
    body = payload or RunRequest()
    final_config_path = body.config_path or config_path or DEFAULT_CONFIG_PATH
    final_input_csv = body.input_csv or input_csv or DEFAULT_INPUT_CSV
    final_use_live = (
        body.use_live_agile_prices
        if body.use_live_agile_prices is not None
        else (use_live_agile_prices if use_live_agile_prices is not None else False)
    )

    try:
        summary_df = run_model(
            config_path=final_config_path,
            csv_path=final_input_csv,
            use_live_agile_prices=final_use_live,
        )
        config = load_config(final_config_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    output_dir = Path(config.output_dir)
    summary_path = output_dir / "scenario_summary.csv"
    chart_path = output_dir / "battery_size_vs_savings.png"

    outputs: dict[str, str | None] = {
        "summary_csv": str(summary_path),
        "chart": str(chart_path) if chart_path.exists() else None,
    }

    return {
        "status": "ok",
        "summary_rows": summary_df.to_dict(orient="records"),
        "output_files": outputs,
    }

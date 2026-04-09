# Power Optimiser

## Purpose
This project models UK domestic electricity import costs at half-hourly resolution and answers three staged questions:
1. How much cheaper would Octopus Agile have been than Octopus Flexible for the same historical demand?
2. How much additional value can battery-only import arbitrage unlock under Agile?
3. How does value change with battery size and round-trip efficiency assumptions?

The current implementation focuses on battery-only arbitrage against household demand and is structured to add PV, export, EV flexibility, and hot-water diversion later.

## Project layout

```text
.
├── configs/default.yaml                 # Scenario assumptions and run settings
├── data/                                # Raw and generated data files
├── outputs/                             # Generated outputs (summary, dispatch, charts)
├── src/power_optimiser/
│   ├── battery.py                       # Battery LP dispatch model
│   ├── cli.py                           # Command-line entry point
│   ├── config.py                        # Config and scenario loading
│   ├── data.py                          # DuckDB load/query helpers
│   ├── main.py                          # Orchestration
│   ├── reporting.py                     # CSV + chart output
│   └── tariffs.py                       # Tariff backtest calculations
├── tests/
│   ├── test_battery.py
│   └── test_tariffs.py
└── scripts_generate_sample_data.py      # Synthetic half-hourly data generator
```

## Data model
Expected table columns (minimum):
- `timestamp`
- `consumption_kwh`
- `agile_import_p_per_kwh`
- `flexible_import_p_per_kwh`

Optional future-compatible columns are already supported in the sample CSV schema:
- `pv_kwh`
- `export_p_per_kwh`
- `ev_flexible_kwh`
- `hot_water_flexible_kwh`

DuckDB is used for local storage and querying. The CLI loads CSV into a configured DuckDB table before running scenarios.

## Core assumptions and scenarios
Assumptions are parameterised in `configs/default.yaml`:
- half-hour interval length (`interval_hours: 0.5`)
- battery capacities (`5, 10, 15, 20, 25 kWh`)
- round-trip efficiencies (`70%, 85%`)
- power limits and initial SOC fraction

This keeps scenario edits auditable and isolated from modelling code.

## Optimisation approach and trade-off
Battery dispatch is solved as a linear program (PuLP with CBC):
- objective: minimise total import cost under Agile
- decision variables: charge/discharge energy each interval and SOC trajectory
- constraints: SOC bounds, power limits, demand-limited discharge, SOC continuity with efficiency losses

Why LP instead of a custom greedy policy?
- **Pros:** deterministic optimum for the model assumptions, transparent constraints, easy extension for future assets.
- **Cons:** adds a solver dependency and slightly more implementation complexity.

For maintainability and auditability, this repo uses LP now; if dependency minimisation later becomes critical, a simpler deterministic rule-based dispatch can be substituted and benchmarked against LP results.

## Quick start

```bash
python -m pip install -e .[dev]
python scripts_generate_sample_data.py
python -m power_optimiser.cli --config configs/default.yaml --input-csv data/sample_half_hourly_input.csv --use-live-agile-prices
pytest
```

## Outputs
Running the model generates:
- `outputs/scenario_summary.csv` (scenario-level metrics)
- `outputs/dispatch_<scenario>.csv` (interval dispatch trace per scenario)
- `outputs/battery_size_vs_savings.png` (chart)

Summary metrics include:
- annual no-battery Agile and Flexible costs
- annual with-battery Agile cost
- savings vs no battery
- value per installed kWh
- equivalent full cycles

## Adding real Octopus data
1. Prepare a half-hourly CSV with required columns.
2. Keep units exactly as:
   - kWh for energy columns
   - p/kWh for tariff columns
3. Run:
   ```bash
   python -m power_optimiser.cli --config configs/default.yaml --input-csv /absolute/path/to/your_data.csv
   ```
4. Inspect `outputs/scenario_summary.csv` for side-by-side scenario comparisons.

## Extension path
Planned extension points:
- Add PV and export by expanding grid balance constraints and objective terms.
- Add EV/hot-water flexible loads as shiftable demand variables.
- Add tariff-specific constraints or reserve-SOC strategies via config.
- Add multiple tariff backtests and side-by-side strategy comparisons.

The current code separates data ingestion, assumptions, optimisation, and reporting to keep this path straightforward.


## Run as a Render Web Service

This repository now includes a FastAPI server at `power_optimiser.web:app` while keeping the existing CLI unchanged.

### Render service settings
- **Service type:** Web Service
- **Build Command:** `pip install -U pip && pip install -e .`
- **Start Command:** `uvicorn power_optimiser.web:app --host 0.0.0.0 --port $PORT`

The start command binds to `0.0.0.0` and uses Render's assigned `$PORT`.

### Required environment variables
- `OCTOPUS_API_KEY` (if your config/data flow uses live Octopus pricing).

### API endpoints
- `GET /health`
  - Returns `{"status":"ok"}`
- `POST /run`
  - Triggers the existing `run_model(...)` pipeline.
  - Accepts optional JSON body (or query params):
    - `config_path` (default: `configs/default.yaml`)
    - `input_csv` (default: `data/sample_half_hourly_input.csv`)
    - `use_live_agile_prices` (default: `false`)

### Example curl commands

Health check:

```bash
curl -s http://localhost:8000/health
```

Run model with defaults:

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{}'
```

Run model with explicit paths and live-price flag:

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "config_path": "configs/default.yaml",
    "input_csv": "data/sample_half_hourly_input.csv",
    "use_live_agile_prices": true
  }'
```

For local API development:

```bash
uvicorn power_optimiser.web:app --host 0.0.0.0 --port 8000
```

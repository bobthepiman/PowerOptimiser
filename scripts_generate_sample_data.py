from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def build_sample_data(days: int = 28) -> pd.DataFrame:
    intervals = days * 48
    ts = pd.date_range("2026-01-01", periods=intervals, freq="30min", tz="UTC")

    base_kw = 0.55
    hour = ts.hour + ts.minute / 60
    morning_peak = ((hour >= 6) & (hour < 9)).astype(float) * 0.7
    evening_peak = ((hour >= 17) & (hour < 22)).astype(float) * 1.1
    weekend_factor = (ts.dayofweek >= 5).astype(float) * 0.1
    seasonal_noise = np.sin(np.linspace(0, 8 * np.pi, intervals)) * 0.1

    demand_kw = base_kw + morning_peak + evening_peak + weekend_factor + seasonal_noise
    consumption_kwh = demand_kw * 0.5

    agile_price = 19 + 8 * np.sin((hour - 13) / 24 * 2 * np.pi) + 3 * np.cos(np.linspace(0, 6 * np.pi, intervals))
    agile_price = np.clip(agile_price, 5, 45)
    flexible_price = np.full(intervals, 27.5)

    return pd.DataFrame(
        {
            "timestamp": ts,
            "consumption_kwh": np.round(consumption_kwh, 4),
            "agile_import_p_per_kwh": np.round(agile_price, 3),
            "flexible_import_p_per_kwh": np.round(flexible_price, 3),
            "pv_kwh": 0.0,
            "export_p_per_kwh": 0.0,
            "ev_flexible_kwh": 0.0,
            "hot_water_flexible_kwh": 0.0,
        }
    )


def main() -> None:
    out_path = Path("data/sample_half_hourly_input.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df = build_sample_data()
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows to {out_path}")


if __name__ == "__main__":
    main()

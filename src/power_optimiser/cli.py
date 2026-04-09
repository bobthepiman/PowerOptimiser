from __future__ import annotations

import argparse

from power_optimiser.main import run_model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run tariff and battery arbitrage model")
    parser.add_argument("--config", default="configs/default.yaml", help="Path to config YAML")
    parser.add_argument(
        "--input-csv",
        default="data/sample_half_hourly_input.csv",
        help="Input CSV containing half-hourly data",
    )
    parser.add_argument(
        "--use-live-agile-prices",
        action="store_true",
        help="Use live Agile prices if the configured data source supports it",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    summary = run_model(
        config_path=args.config,
        csv_path=args.input_csv,
        use_live_agile_prices=args.use_live_agile_prices,
    )
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()

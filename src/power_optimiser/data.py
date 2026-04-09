from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

REQUIRED_COLUMNS = [
    "timestamp",
    "consumption_kwh",
    "agile_import_p_per_kwh",
    "flexible_import_p_per_kwh",
]


def ensure_database(db_path: str, csv_path: str, table_name: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = duckdb.connect(db_path)
    try:
        conn.execute(
            f"""
            CREATE OR REPLACE TABLE {table_name} AS
            SELECT *
            FROM read_csv_auto(?, HEADER=TRUE)
            """,
            [csv_path],
        )
    finally:
        conn.close()


def load_input_data(db_path: str, table_name: str) -> pd.DataFrame:
    conn = duckdb.connect(db_path)
    try:
        df = conn.execute(f"SELECT * FROM {table_name} ORDER BY timestamp").fetchdf()
    finally:
        conn.close()

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    return df

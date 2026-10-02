"""
Seeds Supabase with real NISR data:
  1. One `zones` row per district (30 total), using approximate district
     centroids from app/db/rwanda_districts.py.
  2. One `agri_metrics` row per (district, crop, season) from the real SAS
     2026 Season A/B extraction (1,253 rows: 30 districts x 23 crops x 2
     seasons).

Safe to re-run: zones are looked up by district before insert, and
agri_metrics rows are upserted on (zone_id, season, crop) - see the
`unique` constraint added in app/db/schema.sql. Run schema.sql in the
Supabase SQL editor FIRST (or the migration block at its top, if the
tables already existed) before running this script.

Usage:
    cd agri-menya/backend
    python -m scripts.seed_real_data [path/to/agri_menya_real_data.csv]
"""
import sys
from pathlib import Path

import pandas as pd

from app.db import crud
from app.db.rwanda_districts import DISTRICT_LOOKUP

DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "agri_menya_real_data.csv"


def get_or_create_zone(district: str) -> str:
    """Returns the zone id for a district, creating it (with its real
    centroid) if it doesn't exist yet."""
    existing = crud.list_zones(district=district)
    if existing:
        return existing[0]["id"]

    centroid = DISTRICT_LOOKUP.get(district)
    if not centroid:
        raise ValueError(
            f"No centroid found for district '{district}' in rwanda_districts.py "
            f"- add it before seeding."
        )
    zone = crud.create_zone({
        "district": district,
        "sector": None,
        "cell": None,
        "latitude": centroid["latitude"],
        "longitude": centroid["longitude"],
        "crop_type": None,   # district zone covers many crops - see agri_metrics.crop instead
        "season": None,
    })
    return zone["id"]


def seed(data_path: Path = DEFAULT_DATA_PATH) -> None:
    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows from {data_path}")

    districts = sorted(df["district"].unique())
    zone_ids = {}
    for district in districts:
        zone_ids[district] = get_or_create_zone(district)
    print(f"Ensured {len(zone_ids)} district zones exist.")

    # Seed in batches with retry/backoff to tolerate transient network errors
    seeded, skipped = 0, 0
    batch_size = 100
    batch = []

    def flush_batch(b):
        # Each record upserted individually but with retries to avoid large
        # transaction rollbacks on intermittent network failures.
        for rec in b:
            attempts = 0
            while True:
                try:
                    crud.upsert_agri_metric(rec)
                    break
                except Exception as e:
                    attempts += 1
                    if attempts >= 3:
                        print(f"Failed to upsert after {attempts} attempts: {e}")
                        raise
                    wait = 0.5 * (2 ** (attempts - 1))
                    print(f"Transient error upserting, retry {attempts}/3 after {wait}s: {e}")
                    import time

                    time.sleep(wait)

    for _, row in df.iterrows():
        if pd.isna(row["yield_kg_ha"]):
            skipped += 1
            continue
        record = {
            "zone_id": zone_ids[row["district"]],
            "season": row["season"],
            "crop": row["crop"],
            "yield_actual": float(row["yield_kg_ha"]),
            "production_mt": float(row["production_mt"]) if pd.notna(row["production_mt"]) else None,
            "area_cultivated": float(row["cultivated_area_ha"]) if pd.notna(row["cultivated_area_ha"]) else None,
        }
        batch.append(record)
        seeded += 1
        if len(batch) >= batch_size:
            flush_batch(batch)
            batch = []

    if batch:
        flush_batch(batch)

    print(f"Seeded/updated {seeded} agri_metrics rows ({skipped} skipped for missing yield).")


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_DATA_PATH
    seed(path)

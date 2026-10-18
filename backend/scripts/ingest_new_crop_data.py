"""Validate and append direct extension-survey yield observations.

Input CSV columns: district, season, yield_kg_ha. Supply the crop and its
already-classified category on the command line; no area/production values are
fabricated. Extension values are stored separately as unweighted observations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import sys
from pathlib import Path

import pandas as pd

from app.db.rwanda_districts import RWANDA_DISTRICTS
from app.ml.features import DEFAULT_TRAINING_TABLE
from scripts.build_yield_baseline import OUT_PATH, build as build_baselines
import json

MAX_YIELD_KG_HA = 1_000_000.0
SEASON_RE = re.compile(r"^(?:(\d{4})\s+)?season\s*([abc])(?:\s+(\d{4}))?$", re.I)


def canonical_season(value: str) -> tuple[str, str, int]:
    match = SEASON_RE.fullmatch(value.strip())
    if not match:
        raise ValueError(f"invalid season {value!r}; expected '2026 Season A' or 'Season A 2026'")
    year = int(match.group(1) or match.group(3) or 0)
    if year < 2000 or year > 2100:
        raise ValueError(f"season year outside supported range: {year}")
    code = match.group(2).upper()
    return f"{year} Season {code}", code, year


def validate_source(path: Path, crop: str, category: str, table: pd.DataFrame) -> pd.DataFrame:
    source = pd.read_csv(path)
    required = {"district", "season", "yield_kg_ha"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"input is missing columns: {', '.join(sorted(missing))}")
    districts = {entry["district"].casefold(): entry["district"] for entry in RWANDA_DISTRICTS}
    known = table.district.dropna().astype(str).str.casefold().unique()
    districts = {key: value for key, value in districts.items() if key in set(known)}
    records = []
    for row_number, row in enumerate(source.to_dict("records"), start=2):
        raw_district = str(row["district"]).strip()
        district = districts.get(raw_district.casefold())
        if district is None:
            raise ValueError(f"row {row_number}: unknown Rwanda district {raw_district!r}")
        season, code, year = canonical_season(str(row["season"]))
        try:
            value = float(row["yield_kg_ha"])
        except (TypeError, ValueError):
            raise ValueError(f"row {row_number}: yield_kg_ha must be numeric") from None
        if not math.isfinite(value) or not 0 < value <= MAX_YIELD_KG_HA:
            raise ValueError(f"row {row_number}: yield must be in (0, {MAX_YIELD_KG_HA:g}] kg/ha")
        key = (district.casefold(), season.casefold())
        if key in {(str(r["district"]).casefold(), str(r["season"]).casefold()) for r in records}:
            raise ValueError(f"row {row_number}: duplicate district/season observation")
        records.append({"district": district, "season": season, "season_code": code, "year": year,
                        "crop": crop.strip(), "crop_category": category.strip(), "yield_kg_ha": value,
                        "data_source": "extension_survey"})
    return pd.DataFrame(records)


def ingest(source_path: Path, crop: str, category: str, table_path: Path = DEFAULT_TRAINING_TABLE,
           baseline_path: Path = OUT_PATH) -> dict:
    table = pd.read_csv(table_path)
    additions = validate_source(source_path, crop, category, table)
    existing = table[(table.crop.astype(str).str.casefold() == crop.casefold()) &
                     table.district.astype(str).str.casefold().isin(additions.district.str.casefold())]
    existing_keys = {(str(r.district).casefold(), str(r.season).casefold()) for r in existing.itertuples()}
    duplicates = [(r.district, r.season) for r in additions.itertuples()
                  if (r.district.casefold(), r.season.casefold()) in existing_keys]
    if duplicates:
        raise ValueError(f"observations already exist for crop/district/season: {duplicates}")
    for column in table.columns:
        if column not in additions:
            additions[column] = pd.NA
    if "data_source" not in table:
        table["data_source"] = "nisr"
    additions = additions.reindex(columns=table.columns)
    combined = pd.concat([table, additions], ignore_index=True)
    if "n_districts_for_crop" in combined:
        counts = combined.groupby("crop").district.transform("nunique")
        combined["n_districts_for_crop"] = counts
    baseline_payload = build_baselines(combined.fillna("").to_dict("records"))
    # Both writes are prepared only after all rows and baseline calculations validate.
    temp_table = table_path.with_suffix(table_path.suffix + ".tmp")
    temp_baseline = baseline_path.with_suffix(baseline_path.suffix + ".tmp")
    combined.to_csv(temp_table, index=False)
    digest_builder = hashlib.sha256()
    with temp_table.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest_builder.update(chunk)
    digest = digest_builder.hexdigest()
    baseline_payload["training_data_sha256"] = digest
    temp_baseline.write_text(json.dumps(baseline_payload, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    temp_table.replace(table_path)
    temp_baseline.replace(baseline_path)
    return {"crop": crop, "rows_added": len(additions),
            "districts_observed": int(combined[combined.crop == crop].district.nunique()),
            "thin": int(combined[combined.crop == crop].district.nunique()) < 10,
            "baseline_path": str(baseline_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--crop", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--training-table", type=Path, default=DEFAULT_TRAINING_TABLE)
    parser.add_argument("--baseline-output", type=Path, default=OUT_PATH)
    args = parser.parse_args()
    result = ingest(args.csv, args.crop, args.category, args.training_table, args.baseline_output)
    print(f"Added {result['rows_added']} {result['crop']} observations; now {result['districts_observed']} districts; thin={result['thin']}.")
    print(f"Updated extension baseline at {result['baseline_path']} (direct yield means are unweighted).")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, pd.errors.ParserError, csv.Error) as exc:
        print(f"INGEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)

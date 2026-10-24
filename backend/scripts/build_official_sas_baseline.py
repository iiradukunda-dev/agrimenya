"""Build a runtime-ready baseline input from published overall NISR SAS tables.

This consumes the official district yield and harvested-area workbooks and
creates one auditable row per district/crop/season. It deliberately excludes
SITE subgroup tables and community observations.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / "data"
OUTPUT = DATA / "nisr_official_yields_2022_2026.csv"
REPORT = DATA / "eval" / "nisr_baseline_coverage_2022_2026.json"
PARSER_PATH = Path(__file__).with_name("build_sas_2024_training_experiment.py")

spec = importlib.util.spec_from_file_location("sas_official_tables", PARSER_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load the validated SAS workbook parser")
sas = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sas)


def workbook_rows(sources: list[tuple[int, str, Path]]) -> tuple[list[dict[str, str]], dict]:
    records: dict[tuple[str, str, str], dict[str, str]] = {}
    source_hashes = {}
    coverage = {}
    for year, season_scope, path in sources:
        if not path.is_file():
            raise FileNotFoundError(f"SAS workbook not found: {path}")
        source_hashes[f"{year}-{season_scope}"] = hashlib.sha256(path.read_bytes()).hexdigest()
        if season_scope == "Annual":
            table, counts, sheets = sas.district_yield_tables(path, year)
            selected = table.items()
        else:
            code = season_scope[-1]
            table, counts, sheets = sas.district_yield_tables(path, year)
            selected = ((key, value) for key, value in table.items() if key[0] == code)
        row_count = 0
        crops: set[str] = set()
        districts: set[str] = set()
        for (code, district, crop), values in selected:
            yield_value = float(values["yield_kg_ha"])
            harvested = float(values["harvested_area_ha"])
            if yield_value <= 0 or harvested <= 0:
                continue
            season = f"{year} Season {code}"
            key = (district.casefold(), crop.casefold(), season.casefold())
            if key in records:
                raise ValueError(f"Duplicate official observation across workbooks: {key}")
            record = {
                "district": district,
                "crop": crop,
                "season": season,
                "season_code": code,
                "year": str(year),
                "yield_kg_ha": f"{yield_value:.6f}",
                "production_mt": f"{yield_value * harvested / 1000.0:.9f}",
                "harvested_area_ha": f"{harvested:.6f}",
                "cultivated_area_ha": (
                    f"{float(values['cultivated_area_ha']):.6f}"
                    if values.get("cultivated_area_ha") else ""
                ),
            }
            records[key] = record
            row_count += 1
            crops.add(crop)
            districts.add(district)
        coverage[f"{year}-{season_scope}"] = {
            "source_filename": path.name,
            "yield_cells": counts["yield_cells"],
            "harvested_area_cells": counts["harvested_area_cells"],
            "usable_rows": row_count,
            "district_count": len(districts),
            "crop_count": len(crops),
            "source_sheets": sheets,
        }
    ordered = sorted(records.values(), key=lambda row: (int(row["year"]), row["season_code"], row["district"], row["crop"]))
    return ordered, {"coverage": coverage, "source_workbook_sha256": source_hashes}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sas-2022", type=Path, required=True)
    parser.add_argument("--sas-2023", type=Path, required=True)
    parser.add_argument("--sas-2024", type=Path, required=True)
    parser.add_argument("--sas-2025", type=Path, required=True)
    parser.add_argument("--sas-2026-a", type=Path, required=True)
    parser.add_argument("--sas-2026-b", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()
    sources = [
        (2022, "Annual", args.sas_2022), (2023, "Annual", args.sas_2023),
        (2024, "Annual", args.sas_2024), (2025, "Annual", args.sas_2025),
        (2026, "Season A", args.sas_2026_a), (2026, "Season B", args.sas_2026_b),
    ]
    rows, source_report = workbook_rows(sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "district", "crop", "season", "season_code", "year", "yield_kg_ha",
            "production_mt", "harvested_area_ha", "cultivated_area_ha",
        ])
        writer.writeheader()
        writer.writerows(rows)
    per_year = defaultdict(int)
    for row in rows:
        per_year[row["year"]] += 1
    report = {
        "purpose": "Official NISR SAS baseline source data. Used only as a historical fallback when no matching database release exists.",
        "source_note": "Overall district tables only. SITE subgroup estimates and farmer-submitted reports are excluded. Production is calculated as published yield times harvested area divided by 1,000.",
        "row_count": len(rows),
        "rows_by_year": dict(sorted(per_year.items())),
        "seasons": sorted({row["season"] for row in rows}),
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        **source_report,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {len(rows)} official NISR rows from {len(report['seasons'])} seasons to {args.output}")
    print(f"Coverage and source hashes: {args.report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

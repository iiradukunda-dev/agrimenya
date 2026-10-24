"""Build area-weighted, season-aware yield baselines from the NISR table.

Input must contain district, crop, season_code, yield_kg_ha,
harvested_area_ha, and production_mt. By default this reads the
source-derived data/training_table.csv.

Run from backend: python -m scripts.build_yield_baseline [csv-path]
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "training_table.csv"
ARTIFACT_DIR = ROOT / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = ARTIFACT_DIR / "yield_baselines.json"


def _number(row: dict[str, str], name: str) -> float | None:
    raw = row.get(name, "")
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if math.isfinite(value) else None


def _weighted_yield(totals: tuple[float, float]) -> float | None:
    production_kg, harvested_area_ha = totals
    if harvested_area_ha <= 0:
        return None
    return round(production_kg / harvested_area_ha, 1)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build(rows: list[dict[str, str]]) -> dict:
    required = {"district", "crop", "season_code", "yield_kg_ha", "harvested_area_ha", "production_mt"}
    missing = required.difference(rows[0] if rows else {})
    if missing:
        raise ValueError(f"Input is missing required NISR-derived columns: {', '.join(sorted(missing))}")

    weighted: dict[tuple[str, ...], list[float]] = defaultdict(lambda: [0.0, 0.0])
    legacy: dict[tuple[str, str], list[float]] = defaultdict(list)
    extension: dict[tuple[str, ...], list[float]] = defaultdict(list)
    weighted_by_year: dict[tuple[str, ...], list[float]] = defaultdict(lambda: [0.0, 0.0])
    years: set[int] = set()
    for row in rows:
        district = (row.get("district") or "").strip()
        crop = (row.get("crop") or "").strip()
        season = (row.get("season_code") or "").strip().upper()
        year_value = _number(row, "year")
        if year_value is None:
            match = re.search(r"20\d{2}", row.get("season", ""))
            year_value = float(match.group(0)) if match else None
        year = int(year_value) if year_value is not None and year_value.is_integer() else None
        if not district or not crop or season not in {"A", "B", "C"}:
            continue
        if year is not None:
            years.add(year)
        yield_value = _number(row, "yield_kg_ha")
        if (row.get("data_source") or "").strip() == "extension_survey" and yield_value is not None and yield_value > 0:
            extension[(district, crop, season)].append(yield_value)
            extension[(district, crop)].append(yield_value)
            extension[(crop, season)].append(yield_value)
            extension[(crop,)].append(yield_value)
        area = _number(row, "harvested_area_ha")
        production_mt = _number(row, "production_mt")
        if yield_value is not None and yield_value >= 0:
            legacy[(district, crop)].append(yield_value)
        if area is None or area <= 0 or production_mt is None or production_mt < 0:
            continue
        # NISR production is metric tonnes; convert it to kg to match kg/ha.
        production_kg = production_mt * 1000.0
        for key in ((district, crop, season), (district, crop), (crop, season), (crop,), ("__overall__",)):
            weighted[key][0] += production_kg
            weighted[key][1] += area
        if year is not None:
            for key in ((district, crop, season, str(year)), (district, crop, str(year)),
                        (crop, season, str(year)), (crop, str(year))):
                weighted_by_year[key][0] += production_kg
                weighted_by_year[key][1] += area

    district_crop_season = {
        "|".join(key): value for key, totals in weighted.items()
        if len(key) == 3 and (value := _weighted_yield(tuple(totals))) is not None
    }
    district_crop = {
        "|".join(key): value for key, totals in weighted.items()
        if len(key) == 2 and key[1] not in {"A", "B", "C"}
        and (value := _weighted_yield(tuple(totals))) is not None
    }
    crop_season = {
        "|".join(key): value for key, totals in weighted.items()
        if len(key) == 2 and key[0] not in {"__overall__"}
        and key[1] in {"A", "B", "C"}
        and (value := _weighted_yield(tuple(totals))) is not None
    }
    crop_weighted = {
        key[0]: value for key, totals in weighted.items()
        if len(key) == 1 and key[0] != "__overall__"
        and (value := _weighted_yield(tuple(totals))) is not None
    }
    overall = _weighted_yield(tuple(weighted[("__overall__",)]))
    year_averages = {"|".join(key): value for key, totals in weighted_by_year.items()
                     if (value := _weighted_yield(tuple(totals))) is not None}
    legacy_means = {
        f"{district}|{crop}": round(sum(vals) / len(vals), 1)
        for (district, crop), vals in legacy.items() if vals
    }
    extension_means = {"|".join(key): round(sum(values) / len(values), 1)
                       for key, values in extension.items() if values}
    return {
        "schema_version": 2,
        "yield_units": "kg/ha",
        "weighted_yield_definition": "sum(production_mt * 1000) / sum(harvested_area_ha)",
        "district_crop_season_weighted_averages": district_crop_season,
        "district_crop_weighted_averages": district_crop,
        "crop_season_weighted_averages": crop_season,
        "crop_weighted_averages": crop_weighted,
        "district_crop_season_year_weighted_averages": {
            key: value for key, value in year_averages.items() if key.count("|") == 3
        },
        "district_crop_year_weighted_averages": {
            key: value for key, value in year_averages.items()
            if key.count("|") == 2 and key.split("|")[-1].isdigit()
        },
        "crop_season_year_weighted_averages": {
            key: value for key, value in year_averages.items()
            if key.count("|") == 2 and key.split("|")[-1].isdigit()
            and key.split("|")[1] in {"A", "B", "C"}
        },
        "crop_year_weighted_averages": {
            key: value for key, value in year_averages.items()
            if key.count("|") == 1 and key.split("|")[-1].isdigit()
        },
        "data_years": sorted(years),
        "official_observation_rows": len(rows),
        "overall_weighted_average": overall,
        "legacy_simple_mean_district_crop_averages": legacy_means,
        "extension_observation_definition": "arithmetic mean of direct extension-survey kg/ha observations; not area weighted",
        "extension_district_crop_season_averages": {k: v for k, v in extension_means.items() if k.count("|") == 2},
        "extension_district_crop_averages": {k: v for k, v in extension_means.items() if k.count("|") == 1 and k.split("|")[0] not in {"A", "B", "C"}},
        "extension_crop_season_averages": {k: v for k, v in extension_means.items() if k.count("|") == 1 and k.rsplit("|", 1)[-1] in {"A", "B", "C"}},
        "extension_crop_averages": {k: v for k, v in extension_means.items() if "|" not in k},
        # Compatibility keys for existing clients during migration.
        "district_crop_averages": district_crop,
        "crop_averages": crop_weighted,
        "overall_average": overall,
    }


def main() -> int:
    with DATA_CSV.open(newline="", encoding="utf-8-sig") as source:
        rows = list(csv.DictReader(source))
    if not rows:
        raise ValueError(f"No rows found in {DATA_CSV}")
    payload = build(rows)
    payload["training_data_sha256"] = _sha256_file(DATA_CSV)
    with OUT_PATH.open("w", encoding="utf-8") as output:
        json.dump(payload, output, indent=2, ensure_ascii=False, sort_keys=True)

    old = payload["legacy_simple_mean_district_crop_averages"]
    new = payload["district_crop_weighted_averages"]
    disagreements = []
    for key, old_value in old.items():
        if key in new:
            disagreements.append((abs(old_value - new[key]), key, old_value, new[key]))
    print(f"Wrote {len(payload['district_crop_season_weighted_averages'])} district/crop/season baselines, "
          f"{len(payload['crop_season_weighted_averages'])} crop/season fallbacks to {OUT_PATH}")
    print("Top 15 district/crop differences (absolute kg/ha):")
    print(f"{'District | Crop':48} {'Old simple mean':>16} {'New weighted':>14} {'Difference':>12}")
    for difference, key, old_value, new_value in sorted(disagreements, reverse=True)[:15]:
        print(f"{key:48} {old_value:16.1f} {new_value:14.1f} {difference:12.1f}")
    if not disagreements:
        print("No district/crop pairs have both valid legacy and weighted estimates.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error) as exc:
        print(f"BASELINE BUILD FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)

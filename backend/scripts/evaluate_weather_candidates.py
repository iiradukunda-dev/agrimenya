"""Evaluate yield candidates with prior-season ERA5 weather context.

This is an opt-in, evaluation-only experiment. It fetches district-point
historical weather from Open-Meteo's ERA5 archive, shifts all weather inputs
back one completed Rwanda agricultural season, and runs the same grouped
Prompt M5 folds. It never writes or replaces serving model artifacts.

Run from ``backend`` with ``python -m scripts.evaluate_weather_candidates``.
"""
from __future__ import annotations

import hashlib
import json
import time
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd

from app.db.rwanda_districts import DISTRICT_LOOKUP
from app.ml import train_yield_model as trainer
from app.ml.validation import _valid_rows

BACKEND = Path(__file__).resolve().parents[1]
INPUT_PATH = BACKEND / "data" / "training_table.csv"
DAILY_PATH = BACKEND / "data" / "external" / "open_meteo_era5_daily.csv"
SEASON_PATH = BACKEND / "data" / "external" / "open_meteo_era5_district_season.csv"
EVAL_PATH = BACKEND / "data" / "eval" / "weather_model_experiment.json"
OOF_PATH = BACKEND / "data" / "eval" / "weather_oof_predictions.csv"
API_URL = "https://archive-api.open-meteo.com/v1/archive"
WEATHER_COLUMNS = (
    "previous_season_precipitation_mm",
    "previous_season_temperature_midpoint_mean_c",
    "previous_season_et0_mm",
    "previous_season_dry_day_share",
)
SEASON_ORDER = {"A": 0, "B": 1, "C": 2}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _season_bounds(year: int, code: str) -> tuple[date, date]:
    if code == "A":
        return date(year - 1, 9, 1), date(year, 2, 28)
    if code == "B":
        return date(year, 3, 1), date(year, 6, 30)
    if code == "C":
        return date(year, 7, 1), date(year, 9, 30)
    raise ValueError(f"Unsupported Rwanda season code: {code}")


def _decode_ordinal(ordinal: int) -> tuple[int, str]:
    year, index = divmod(ordinal, 3)
    return year, ("A", "B", "C")[index]


def _district_coordinates(district: str) -> tuple[float, float]:
    lookup = {name.casefold(): value for name, value in DISTRICT_LOOKUP.items()}
    row = lookup.get(district.strip().casefold())
    if row is None:
        raise ValueError(f"No recorded district coordinate for {district!r}; refusing to invent one")
    return float(row["latitude"]), float(row["longitude"])


def _fetch_daily(district: str, latitude: float, longitude: float,
                 start: date, end: date) -> pd.DataFrame:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        "daily": "precipitation_sum,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration",
        "timezone": "Africa/Kigali",
        "models": "era5",
    }
    with httpx.Client(timeout=45.0, follow_redirects=True) as client:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = client.get(API_URL, params=params)
                response.raise_for_status()
                payload = response.json()
                daily = payload.get("daily") or {}
                required = ("time", "precipitation_sum", "temperature_2m_max",
                            "temperature_2m_min", "et0_fao_evapotranspiration")
                if any(key not in daily for key in required):
                    raise ValueError(f"Weather API response omitted a requested daily field for {district}")
                frame = pd.DataFrame({key: daily[key] for key in required})
                frame["district"] = district
                frame["requested_latitude"] = latitude
                frame["requested_longitude"] = longitude
                frame["grid_latitude"] = payload.get("latitude")
                frame["grid_longitude"] = payload.get("longitude")
                frame["temperature_midpoint_c"] = (
                    pd.to_numeric(frame.temperature_2m_max, errors="coerce")
                    + pd.to_numeric(frame.temperature_2m_min, errors="coerce")
                ) / 2.0
                return frame.rename(columns={
                    "time": "date",
                    "precipitation_sum": "precipitation_mm",
                    "et0_fao_evapotranspiration": "et0_mm",
                })
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Historical weather request failed for district {district}: {last_error}")


def fetch_weather(input_path: Path = INPUT_PATH, refresh: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    source = _valid_rows(pd.read_csv(input_path))
    targets = sorted({
        (int(row.year), str(row.season_code).upper())
        for row in source[["year", "season_code"]].itertuples(index=False)
    })
    prior_ordinals = sorted({year * 3 + SEASON_ORDER[code] - 1 for year, code in targets})
    prior_groups = [_decode_ordinal(value) for value in prior_ordinals]
    bounds = [_season_bounds(year, code) for year, code in prior_groups]
    start, end = min(left for left, _ in bounds), max(right for _, right in bounds)

    if not refresh and DAILY_PATH.is_file() and SEASON_PATH.is_file():
        daily = pd.read_csv(DAILY_PATH)
        seasonal = pd.read_csv(SEASON_PATH)
        if set(daily.district.astype(str).str.casefold()) >= set(source.district.astype(str).str.casefold()):
            return daily, seasonal

    districts = sorted(source.district.dropna().astype(str).unique())
    chunks = []
    for index, district in enumerate(districts, start=1):
        lat, lon = _district_coordinates(district)
        print(f"Fetching ERA5 historical weather for {district} ({index}/{len(districts)})")
        chunks.append(_fetch_daily(district, lat, lon, start, end))

    daily = pd.concat(chunks, ignore_index=True)
    daily["date"] = pd.to_datetime(daily.date, errors="coerce")
    rows: list[dict[str, Any]] = []
    for district, district_daily in daily.groupby("district", sort=True):
        for (year, code), (season_start, season_end) in zip(prior_groups, bounds):
            selected = district_daily[
                district_daily.date.between(pd.Timestamp(season_start), pd.Timestamp(season_end))
            ]
            precipitation = pd.to_numeric(selected.precipitation_mm, errors="coerce").dropna()
            temperatures = pd.to_numeric(selected.temperature_midpoint_c, errors="coerce").dropna()
            et0 = pd.to_numeric(selected.et0_mm, errors="coerce").dropna()
            if selected.empty or not len(precipitation):
                raise ValueError(f"No complete weather observations for {district}, {year} Season {code}")
            rows.append({
                "district": district,
                "weather_year": year,
                "weather_season_code": code,
                "weather_start_date": season_start.isoformat(),
                "weather_end_date": season_end.isoformat(),
                "weather_days_available": int(selected.date.nunique()),
                "precipitation_mm": float(precipitation.sum()),
                "temperature_midpoint_mean_c": float(temperatures.mean()) if len(temperatures) else None,
                "et0_mm": float(et0.sum()) if len(et0) else None,
                "dry_day_share": float((precipitation < 1.0).mean()),
                "grid_latitude": float(selected.grid_latitude.iloc[0]),
                "grid_longitude": float(selected.grid_longitude.iloc[0]),
                "weather_source": "Open-Meteo Historical Weather API, ERA5 reanalysis",
            })
    seasonal = pd.DataFrame(rows)
    DAILY_PATH.parent.mkdir(parents=True, exist_ok=True)
    daily.to_csv(DAILY_PATH, index=False)
    seasonal.to_csv(SEASON_PATH, index=False)
    return daily, seasonal


def with_lagged_weather(input_path: Path, seasonal: pd.DataFrame) -> pd.DataFrame:
    frame = _valid_rows(pd.read_csv(input_path)).copy()
    frame["_weather_ordinal"] = (
        pd.to_numeric(frame.year, errors="coerce").astype(int) * 3
        + frame.season_code.astype(str).str.upper().map(SEASON_ORDER)
        - 1
    )
    seasonal = seasonal.copy()
    seasonal["_weather_ordinal"] = (
        seasonal.weather_year.astype(int) * 3
        + seasonal.weather_season_code.astype(str).map(SEASON_ORDER)
    )
    lookup = seasonal.set_index([seasonal.district.astype(str).str.casefold(), "_weather_ordinal"])
    for column in WEATHER_COLUMNS:
        frame[column] = np.nan
    for index, row in frame.iterrows():
        key = (str(row.district).casefold(), int(row._weather_ordinal))
        if key not in lookup.index:
            continue
        weather = lookup.loc[key]
        frame.at[index, WEATHER_COLUMNS[0]] = weather.precipitation_mm
        frame.at[index, WEATHER_COLUMNS[1]] = weather.temperature_midpoint_mean_c
        frame.at[index, WEATHER_COLUMNS[2]] = weather.et0_mm
        frame.at[index, WEATHER_COLUMNS[3]] = weather.dry_day_share
    return frame.drop(columns="_weather_ordinal")


def evaluate(input_path: Path = INPUT_PATH, refresh: bool = False) -> dict[str, Any]:
    daily, seasonal = fetch_weather(input_path, refresh)
    frame = with_lagged_weather(input_path, seasonal)
    grouped = trainer._all_oof(frame)
    EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    split_metrics: dict[str, Any] = {}
    all_rows = []
    for split_name, rows in grouped["predictions"].items():
        split_metrics[split_name] = trainer._print_table(split_name, rows, grouped["splits"][split_name])
        all_rows.extend(rows)
    winner, decision = trainer._decision(split_metrics)
    pd.DataFrame(all_rows).to_csv(OOF_PATH, index=False, na_rep="")
    report = {
        "experiment": "prior-season ERA5 weather features",
        "winner_for_experiment_only": winner,
        "deployment_status": "not_deployed; serving integration and re-evaluation are required",
        "decision": decision,
        "features": list(WEATHER_COLUMNS),
        "weather_source": "Open-Meteo Historical Weather API using ERA5 reanalysis",
        "weather_api_terms": [
            "The free API is limited to non-commercial use and data attribution requirements apply.",
            "Do not add a production dependency without confirming an appropriate license or API plan.",
        ],
        "weather_source_limitations": [
            "Reanalysis values are modeled estimates, not station observations.",
            "District coordinates are approximate district-town points, not crop-area-weighted centroids.",
            "Only prior completed-season weather is used to avoid same-season look-ahead leakage.",
        ],
        "input": {"path": str(input_path.resolve()), "sha256": _sha256(input_path),
                  "rows": len(frame), "districts": int(frame.district.nunique()),
                  "crops": int(frame.crop.nunique())},
        "weather_artifacts": {
            "daily_path": str(DAILY_PATH.resolve()), "daily_sha256": _sha256(DAILY_PATH),
            "season_path": str(SEASON_PATH.resolve()), "season_sha256": _sha256(SEASON_PATH),
            "daily_rows": len(daily), "district_season_rows": len(seasonal),
        },
        "versions": trainer._versions(),
        "splits": split_metrics,
        "artifacts": {"oof_predictions": str(OOF_PATH.resolve())},
    }
    EVAL_PATH.write_text(json.dumps(trainer._json_safe(report), indent=2), encoding="utf-8")
    print(f"\nExperiment winner: {winner}. No serving model artifact was changed.")
    print(f"Saved weather experiment report: {EVAL_PATH}")
    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--refresh", action="store_true", help="Fetch the API data again rather than use the local cache")
    args = parser.parse_args()
    evaluate(args.input, args.refresh)

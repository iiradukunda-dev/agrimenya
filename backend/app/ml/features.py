"""Shared, target-free feature construction for yield model training/serving.

`build_features` never reads yield, production, or harvested-area values. The
previous-season target lag is deliberately separate and requires the fold's
training frame explicitly.
"""
from __future__ import annotations

from collections.abc import Mapping
import math
import re
from pathlib import Path

import pandas as pd

TARGET_COLUMNS = {"yield_kg_ha", "production_mt", "harvested_area_ha"}
IDENTIFIER_COLUMNS = {"season", "season_code", "year", "district", "crop", "crop_category"}
FORBIDDEN_FEATURE_PARTS = ("yield", "production", "harvested_area")
SEASON_ORDER = {"A": 0, "B": 1, "C": 2}
DEFAULT_TRAINING_TABLE = Path(__file__).resolve().parents[2] / "data" / "training_table.csv"
_TRAINING_TABLE_CACHE: tuple[int, pd.DataFrame] | None = None


def feature_categories(frame: pd.DataFrame) -> dict[str, list[str]]:
    """Return the categorical vocabularies to persist with a fitted model."""
    fields = [name for name in ("district", "crop", "crop_category", "season_code") if name in frame]
    return {name: sorted(frame[name].dropna().astype(str).unique().tolist()) for name in fields}


def build_features(
    df: pd.DataFrame,
    known_categories: Mapping[str, list[str]] | None = None,
    district_area_reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build consistent target-free inputs; unseen categories become NaN.

    `district` identifies the row and is retained as a categorical feature.
    District aggregates use only cultivated area (an input feature), never
    target values. District-level NISR columns are carried through by name.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError("build_features expects a pandas DataFrame")
    source = df.copy(deep=True)
    output = pd.DataFrame(index=source.index)

    for name in ("district", "crop", "crop_category", "season_code"):
        if name in source:
            values = source[name].astype("string").str.strip()
            if known_categories is not None and name in known_categories:
                valid = {str(value) for value in known_categories[name]}
                values = values.where(values.isna() | values.isin(valid), pd.NA)
            output[name] = values

    if "year" in source:
        output["year"] = pd.to_numeric(source["year"], errors="coerce")
    if "cultivated_area_ha" in source:
        area = pd.to_numeric(source["cultivated_area_ha"], errors="coerce")
        positive = area.where(area > 0)
        output["log_cultivated_area"] = positive.map(math.log)
        if {"district", "season_code", "year"}.issubset(source.columns):
            reference = source if district_area_reference is None else district_area_reference
            ref_area = pd.to_numeric(reference["cultivated_area_ha"], errors="coerce")
            ref_groups = [reference["district"], reference["season_code"], reference["year"]]
            totals = ref_area.groupby(ref_groups, dropna=False).sum(min_count=1)
            keys = pd.MultiIndex.from_arrays([source["district"], source["season_code"], source["year"]])
            district_total = pd.Series([totals.get(key, float("nan")) for key in keys], index=source.index)
            output["district_total_cultivated_area_ha"] = district_total
            output["district_cultivated_area_share"] = area.div(district_total.where(district_total > 0))

    excluded = TARGET_COLUMNS | IDENTIFIER_COLUMNS | {"cultivated_area_ha", "n_districts_for_crop"}
    for column in source.columns:
        lowered = str(column).casefold()
        if column in excluded or any(part in lowered for part in FORBIDDEN_FEATURE_PARTS):
            continue
        if column not in output:
            output[column] = pd.to_numeric(source[column], errors="coerce")

    # Stable output ordering makes serialized pipelines and feature reports reproducible.
    return output.reindex(sorted(output.columns), axis=1)


def build_serving_features(
    district: str | None,
    crop: str,
    season: str | None,
    cultivated_area_ha: float | None = None,
    known_categories: Mapping[str, list[str]] | None = None,
    table_path: Path = DEFAULT_TRAINING_TABLE,
) -> pd.DataFrame:
    """Build one serving row from the latest matching sourced NISR features.

    If a district/season source row is unavailable, district features remain
    missing; no values are borrowed from another season or fabricated.
    """
    global _TRAINING_TABLE_CACHE
    if not table_path.is_file():
        raise FileNotFoundError(f"NISR feature table is unavailable: {table_path}")
    modified = table_path.stat().st_mtime_ns
    if _TRAINING_TABLE_CACHE is None or _TRAINING_TABLE_CACHE[0] != modified:
        _TRAINING_TABLE_CACHE = (modified, pd.read_csv(table_path))
    table = _TRAINING_TABLE_CACHE[1]
    if not {"district", "crop", "season_code", "year"}.issubset(table.columns):
        raise ValueError("NISR training table lacks district/crop/season_code/year keys")

    code = _parse_season_code(season)
    match = table[table["district"].astype(str).str.casefold() == str(district or "").strip().casefold()]
    if code:
        match = match[match["season_code"].astype(str).str.upper() == code]
    if not match.empty:
        match = match.sort_values("year", ascending=False, kind="stable")
        base = match.iloc[0].to_dict()
        crop_matches = match[match["crop"].astype(str).str.casefold() == crop.strip().casefold()]
        if crop_matches.empty:
            all_crop_matches = table[table["crop"].astype(str).str.casefold() == crop.strip().casefold()]
            base["crop_category"] = all_crop_matches.iloc[0]["crop_category"] if not all_crop_matches.empty else pd.NA
        else:
            base["crop_category"] = crop_matches.iloc[0].get("crop_category", pd.NA)
    else:
        base = {column: pd.NA for column in table.columns}
    base.update({"district": district, "crop": crop, "season": season, "season_code": code})
    if cultivated_area_ha is not None:
        base["cultivated_area_ha"] = cultivated_area_ha
    reference = match.copy()
    if not reference.empty and cultivated_area_ha is not None:
        crop_mask = reference["crop"].astype(str).str.casefold() == crop.strip().casefold()
        if crop_mask.any():
            reference.loc[reference.index[crop_mask][0], "cultivated_area_ha"] = cultivated_area_ha
    return build_features(pd.DataFrame([base]), known_categories, reference)


def _parse_season_code(season: str | None) -> str | None:
    if season is None:
        return None
    value = str(season).strip().casefold()
    match = re.search(r"season\s*([abc])|\b([abc])\b", value)
    if match:
        return (match.group(1) or match.group(2)).upper()
    short = re.search(r"\bs([123])\b", value)
    return {"1": "A", "2": "B", "3": "C"}.get(short.group(1)) if short else None


def build_previous_season_yield_lag(
    training_frame: pd.DataFrame,
    prediction_frame: pd.DataFrame,
) -> pd.Series:
    """Return a lag using only the explicitly supplied training fold.

    Seasons are ordered A, B, C within a year; Season A follows Season C of
    the previous year. The exact prior season must be present in `training_frame`.
    """
    required = {"district", "crop", "season_code", "year", "yield_kg_ha"}
    prediction_required = required - {"yield_kg_ha"}
    if not required.issubset(training_frame.columns) or not prediction_required.issubset(prediction_frame.columns):
        raise ValueError("training_frame and prediction_frame need district, crop, season_code, and year; training also needs yield_kg_ha")

    prior_values: dict[tuple[str, str, int], list[float]] = {}
    for _, row in training_frame.iterrows():
        code = str(row["season_code"]).strip().upper()
        year_value = pd.to_numeric(pd.Series([row["year"]]), errors="coerce").iloc[0]
        yield_value = pd.to_numeric(pd.Series([row["yield_kg_ha"]]), errors="coerce").iloc[0]
        if code not in SEASON_ORDER or pd.isna(year_value) or pd.isna(yield_value):
            continue
        ordinal = int(year_value) * 3 + SEASON_ORDER[code]
        key = (str(row["district"]).strip(), str(row["crop"]).strip(), ordinal)
        prior_values.setdefault(key, []).append(float(yield_value))

    # A target-fold row in the preceding season means that season was not
    # wholly available to training, so no lag from it is permitted.
    blocked_ordinals: set[int] = set()
    for _, row in prediction_frame.iterrows():
        code = str(row["season_code"]).strip().upper()
        year_value = pd.to_numeric(pd.Series([row["year"]]), errors="coerce").iloc[0]
        if code in SEASON_ORDER and not pd.isna(year_value):
            blocked_ordinals.add(int(year_value) * 3 + SEASON_ORDER[code])

    result = []
    for _, row in prediction_frame.iterrows():
        code = str(row["season_code"]).strip().upper()
        year_value = pd.to_numeric(pd.Series([row["year"]]), errors="coerce").iloc[0]
        if code not in SEASON_ORDER or pd.isna(year_value):
            result.append(float("nan"))
            continue
        ordinal = int(year_value) * 3 + SEASON_ORDER[code] - 1
        if ordinal in blocked_ordinals:
            result.append(float("nan"))
            continue
        key = (str(row["district"]).strip(), str(row["crop"]).strip(), ordinal)
        values = prior_values.get(key, [])
        result.append(sum(values) / len(values) if values else float("nan"))
    return pd.Series(result, index=prediction_frame.index, name="previous_season_yield_kg_ha", dtype="float64")

"""
Yield prediction and priority classification.

Serving calculates season-aware NISR baselines from the current database
observations. With no season it uses the district/crop all-season estimate.
When no matching observations exist, the service reports missing data instead
of substituting a fixed yield. Model training and evaluation remain offline.
"""
import json
import hashlib
import pickle
import logging
import math
import re
import threading
import time
import numpy as np
from pathlib import Path
from statistics import mean
from typing import List

from app.ml.priority import apply_stability, classify_components

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
YIELD_MODEL_PATH = ARTIFACTS_DIR / "yield_model.pkl"
MODEL_CARD_PATH = ARTIFACTS_DIR / "model_card.json"
EVALUATION_REPORT_PATH = Path(__file__).resolve().parents[2] / "data" / "eval" / "yield_model_evaluation.json"
MIN_CROP_DISTRICTS = 10


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def crop_observation_stats(crop: str, season: str | None = None) -> dict:
    """Report sourced district coverage without counting repeated seasons twice."""
    try:
        rows = _live_yield_evidence(None, crop)
        code = _season_code(season)
        if code:
            rows = [row for row in rows if _season_code(row.get("season")) == code]
            requested_year = re.search(r"20\d{2}", str(season or ""))
            exact_year = ([row for row in rows if requested_year.group(0) in str(row.get("season", ""))]
                          if requested_year else [])
            rows = exact_year or rows
        count = len({str(row.get("district", "")).casefold() for row in rows if row.get("district")})
    except Exception:
        logging.exception("Unable to read live yield evidence coverage")
        count = 0
    return {"district_observations": count, "thin": count < MIN_CROP_DISTRICTS}


def _category_proxy_mean(category: str, season: str | None) -> tuple[float | None, int]:
    # Category-level proxies are disabled until uploaded database observations
    # carry a reviewed crop-category mapping; a local training CSV is not a
    # serving-time evidence source.
    return None, 0


def _load_yield_model():
    """Attempt to load the serialized yield model. If loading fails (for
    example because the file is corrupted), move the artifact aside and
    return None so the service falls back to baselines.
    """
    if not YIELD_MODEL_PATH.exists():
        return None
    try:
        with open(YIELD_MODEL_PATH, "rb") as f:
            bundle = pickle.load(f)
        # Schema 2 is the shared, target-free feature pipeline. Older pickles
        # cannot be safely served by the current feature builder.
        if not isinstance(bundle, dict) or bundle.get("feature_schema_version") != 2:
            logging.warning("Ignoring incompatible yield model artifact; using NISR baseline")
            return None
        return bundle
    except Exception as exc:
        logging.exception("Failed to load yield model artifact: %s", exc)
        # try to move the corrupted file to a timestamped backup so it
        # doesn't repeatedly crash the app on import.
        try:
            ts = int(time.time())
            backup = YIELD_MODEL_PATH.with_name(f"yield_model.pkl.corrupted.{ts}")
            YIELD_MODEL_PATH.rename(backup)
            logging.warning("Moved corrupted yield model to %s", backup)
        except Exception:
            logging.exception("Unable to move corrupted yield model file")
        return None


def _load_model_card() -> dict | None:
    try:
        with MODEL_CARD_PATH.open(encoding="utf-8") as stream:
            card = json.load(stream)
        if not isinstance(card, dict):
            raise ValueError("model card must be a JSON object")
        return card
    except FileNotFoundError:
        return None
    except Exception:
        logging.exception("Failed to load yield model card; model will not be activated")
        return None


def load_model_artifacts() -> dict | None:
    """Load only a schema-compatible model accompanied by its model card."""
    card = _load_model_card()
    if card is None:
        logging.warning("Yield model has no readable model_card.json; using NISR baseline")
        return None
    if not YIELD_MODEL_PATH.is_file():
        return None
    try:
        digest = _sha256_file(YIELD_MODEL_PATH)
    except OSError:
        logging.exception("Unable to verify yield model artifact; using NISR baseline")
        return None
    if card.get("model_sha256") != digest:
        logging.error("Yield model and model card integrity hashes do not match; using NISR baseline")
        return None
    card_data_hash = (card.get("input") or {}).get("sha256")
    if not card_data_hash:
        logging.error("Yield model card has no training-data provenance hash; using NISR database baseline")
        return None
    bundle = _load_yield_model()
    if bundle is None:
        return None
    if card.get("model_version") != bundle.get("model_version"):
        logging.error("Yield model and model card versions do not match; using NISR baseline")
        return None
    bundle["model_card"] = card
    return bundle


def model_provenance() -> dict:
    return {
        "model_version": "nisr-database-baseline",
        "basis": "baseline",
        "model_trained_on": {"data_hash": None, "date": None},
    }


def get_model_info() -> dict:
    """Describe the active database baseline and retained offline evaluation."""
    try:
        report = json.loads(EVALUATION_REPORT_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        report = {}
    span = report.get("training_data_span")
    return {"active_basis": "baseline", "model_version": "nisr-database-baseline",
            "winner": report.get("winner", "KEEP BASELINE"), "metrics": report.get("splits", {}),
            "training_data_span": span,
            "features": report.get("feature_list", []),
            "known_limitations": ["Baseline predictions are observational aggregates and do not account for unmeasured local conditions.",
                                  "Current prediction baselines are calculated from yield observations stored in the database; district, crop, and season coverage varies."],
            "date": None, "data_hash": None}


def _match_model_class(value: str, classes) -> str | None:
    """Match UI labels to trained encoder labels despite case/word order."""
    normalized = str(value).strip().casefold()
    for candidate in classes:
        candidate_text = str(candidate)
        if candidate_text.strip().casefold() == normalized:
            return candidate_text
        if set(candidate_text.casefold().split()) == set(normalized.split()):
            return candidate_text
    return None


def _season_code(season: str | None) -> str | None:
    if season is None:
        return None
    match = re.search(r"season\s*([abc])|\b([abc])\b", str(season), flags=re.IGNORECASE)
    if match:
        return (match.group(1) or match.group(2)).upper()
    short = re.search(r"\bs([123])\b", str(season), flags=re.IGNORECASE)
    return {"1": "A", "2": "B", "3": "C"}.get(short.group(1)) if short else None


def _district_crop_baseline(district: str, crop: str, season: str | None) -> float | None:
    try:
        rows = _live_yield_evidence(district, crop)
    except Exception:
        logging.exception("Unable to read database yield baseline for %s / %s", district, crop)
        return None
    return _aggregate_yield_evidence(rows, season)


def _aggregate_yield_evidence(rows: list[dict], season: str | None = None) -> float | None:
    """Compute an area-weighted observed yield from current database evidence."""
    selected = list(rows)
    code = _season_code(season)
    if code:
        matching = [row for row in selected if _season_code(row.get("season")) == code]
        requested_year = re.search(r"20\d{2}", str(season or ""))
        if requested_year:
            exact_year = [row for row in matching if requested_year.group(0) in str(row.get("season", ""))]
            selected = exact_year or matching
        else:
            selected = matching
    if not selected:
        return None
    weighted_production = 0.0
    weighted_area = 0.0
    for row in selected:
        try:
            production = float(row.get("production_mt"))
            area = float(row.get("cultivated_area_ha"))
        except (TypeError, ValueError):
            continue
        if math.isfinite(production) and production >= 0 and math.isfinite(area) and area > 0:
            weighted_production += production * 1000.0
            weighted_area += area
    if weighted_area > 0:
        return round(weighted_production / weighted_area, 1)
    yields = []
    for row in selected:
        try:
            value = float(row.get("yield_kg_ha"))
            if math.isfinite(value) and value > 0:
                yields.append(value)
        except (TypeError, ValueError):
            continue
    return round(mean(yields), 1) if yields else None


_yield_model_bundle = None
_yield_model_lock = threading.Lock()
_yield_evidence_cache: dict[tuple[str | None, str], tuple[float, list[dict]]] = {}
_yield_evidence_cache_lock = threading.Lock()


def _live_yield_evidence(district: str | None, crop: str) -> list[dict]:
    key = (district.casefold() if district else None, crop.casefold())
    now = time.monotonic()
    with _yield_evidence_cache_lock:
        cached = _yield_evidence_cache.get(key)
        if cached and now - cached[0] < 60:
            return cached[1]
    from app.db import crud
    rows = crud.get_yield_evidence(district, crop)
    with _yield_evidence_cache_lock:
        _yield_evidence_cache[key] = (now, rows)
    return rows


def invalidate_yield_evidence_cache() -> None:
    with _yield_evidence_cache_lock:
        _yield_evidence_cache.clear()


def _get_yield_model_bundle():
    """Load the model once, even when several requests arrive concurrently."""
    global _yield_model_bundle
    if _yield_model_bundle is None:
        with _yield_model_lock:
            if _yield_model_bundle is None:
                _yield_model_bundle = load_model_artifacts()
    return _yield_model_bundle


def _estimate_yield_per_ha(district: str | None, crop: str, season: str | None,
                            area_cultivated: float) -> tuple[float | None, float, str]:
    """Returns (yield_per_ha, confidence, model_version)."""
    # The model's current feature builder depends on the offline training CSV.
    # Keep inference on live database observations until that feature pipeline
    # is migrated to the versioned NISR import tables as well.
    bundle = None

    if bundle is not None and season is not None and bundle.get("feature_schema_version") == 1:
        try:
            import pandas as pd
            from app.ml.features import build_serving_features
            features = build_serving_features(
                district, crop, season, area_cultivated, bundle.get("known_categories")
            )
            yield_per_ha = float(bundle["model"].predict(features)[0])
            if math.isfinite(yield_per_ha):
                return round(yield_per_ha, 1), 0.85, bundle["model_version"]
        except Exception:
            pass  # fall through to baseline lookup below

    if district and crop:
        value = _district_crop_baseline(district, crop, season)
        if value is not None:
            return value, 0.65, "district-crop-season-weighted-nisr"

    crop_avg = crop_mean(crop, season)
    if crop_avg is not None:
        return crop_avg, 0.55, "crop-season-weighted-nisr"

    return None, 0.0, "no-yield-data"


def predict_with_interval(district: str | None, crop: str, season: str | None = None,
                          features=None, allow_category_proxy: bool = False,
                          crop_category: str | None = None) -> dict:
    """Predict kg/ha with an 80% crop-stratified conformal interval.

    ``features`` may be a serving-ready one-row DataFrame; otherwise sourced
    NISR features are assembled by the shared feature builder. Thin crops use
    at least the global interval width and are explicitly flagged.
    """
    from app.ml.intervals import log_interval

    # Serve the database baseline. Offline model artifacts remain available
    # for retraining/evaluation, but inference does not read CSVs.
    bundle = None
    stats = crop_observation_stats(crop, season)
    basis = "district_crop_baseline"
    version = "nisr-database-baseline"
    point = None
    if point is None or not math.isfinite(point) or point <= 0:
        if district:
            point = _district_crop_baseline(district, crop, season)
            if point is not None:
                basis = "district_crop_baseline"
        if point is None:
            point = crop_mean(crop, season)
            if point is not None:
                basis = "crop_baseline"
        if point is None and allow_category_proxy and crop_category:
            point, proxy_rows = _category_proxy_mean(crop_category, season)
            if point is not None:
                basis = "category_proxy"
                version = "category-proxy"
                # Broad log-space interval explicitly reflects category-only evidence.
                calibration = (bundle or {}).get("interval_calibration", {})
                q = max(float(calibration.get("global_quantile_log", math.log(3.0))), math.log(3.0))
                low, high = math.exp(math.log(point) - q), math.exp(math.log(point) + q)
                return {"point": round(point, 1), "low": round(low, 1), "high": round(high, 1),
                        "interval_level": 0.8, "basis": basis, "insufficient_data": True,
                        "warning": f"Category proxy for {crop_category}; assumed from {proxy_rows} yield records. This is not crop-specific evidence.",
                        "model_version": version, **stats}
        if point is None:
            # Unknown crops remain unknown unless the caller explicitly opts into a proxy.
            return {"point": None, "low": None, "high": None, "interval_level": None,
                    "basis": "no_data", "insufficient_data": True,
                    "warning": f"No yield observations are available for {crop}; priority is Unknown.",
                    "model_version": "no-yield-data", **stats}
    if point is None or not math.isfinite(point) or point <= 0:
        basis = "district_crop_baseline"
        point = _district_crop_baseline(district, crop, season) if district else None
        if point is None:
            basis = "crop_baseline"
            point = crop_mean(crop, season)
        if point is None:
            return {"point": None, "low": None, "high": None, "interval_level": None,
                    "basis": "no_data", "insufficient_data": True,
                    "warning": f"No yield observations are available for {crop}.",
                    "model_version": "no-yield-data", **stats}
        version = "nisr-baseline"

    calibration = (bundle or {}).get("interval_calibration")
    if calibration is None:
        path = ARTIFACTS_DIR / "yield_intervals.json"
        try:
            with path.open(encoding="utf-8") as stream:
                calibration = json.load(stream)
        except (OSError, json.JSONDecodeError):
            calibration = {}
    category = (bundle or {}).get("crop_categories", {}).get(crop)
    category = category or calibration.get("crop_category_by_crop", {}).get(crop)
    category_data = calibration.get("by_crop_category", {}).get(category, {})
    source_count = stats.get("district_observations", 0)
    global_q = float(calibration.get("global_quantile_log", math.log(3.0)))
    crop_q = float(category_data.get("quantile_log", global_q))
    # Conservative widening for sparse categories/crops; never estimate a
    # narrow tail interval from fewer than ten source districts.
    q = max(global_q, crop_q) if source_count < int(calibration.get("minimum_districts", 10)) else crop_q
    low, high = log_interval(float(point), q)
    return {"point": round(float(point), 1), "low": round(low, 1), "high": round(high, 1),
            "interval_level": float(calibration.get("interval_level", 0.8)), "basis": basis,
            "insufficient_data": source_count < int(calibration.get("minimum_districts", 10)),
            "model_version": version, **stats, "warning": None}


def known_crops() -> List[str]:
    """Return crops with live database observations."""
    crops: set[str] = set()
    try:
        from app.db import crud
        crops.update(crud.get_yield_crop_names())
    except Exception:
        logging.exception("Unable to load crop list from database yield evidence")
    return sorted(crops)


def has_data() -> bool:
    return bool(known_crops())


def crop_mean(crop: str, season: str | None = None) -> float | None:
    try:
        rows = _live_yield_evidence(None, crop)
    except Exception:
        logging.exception("Unable to read database crop baseline for %s", crop)
        return None
    return _aggregate_yield_evidence(rows, season)


def get_yield_per_hectare(district: str | None, crop: str, season: str | None = None) -> float | None:
    """Best-effort yield per hectare for a district+crop using baselines."""
    if district and crop:
        v = _district_crop_baseline(district, crop, season)
        if v is not None:
            return float(v)
    v = crop_mean(crop, season)
    if v is not None:
        return float(v)
    return None


def _values_for_crop_across_districts(crop: str, season: str | None = None) -> List[float]:
    try:
        rows = _live_yield_evidence(None, crop)
    except Exception:
        logging.exception("Unable to load district yield observations for %s", crop)
        return []
    districts = sorted({str(row["district"]) for row in rows if row.get("district")})
    values = [_aggregate_yield_evidence([row for row in rows if row.get("district") == district], season)
              for district in districts]
    return sorted(float(value) for value in values if value is not None)


def _percentile_from_sorted(sorted_vals: List[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    # p in [0,100]
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals)-1) * (p/100.0)
    lo = int(k)
    hi = min(lo+1, len(sorted_vals)-1)
    frac = k - lo
    return sorted_vals[lo] * (1-frac) + sorted_vals[hi] * frac


def get_yield_percentile(district: str, crop: str, season: str | None = None) -> float | None:
    """Return the percentile (0-100) of the district's yield among peers for the crop.
    Lower percentile means lower-performing district.
    """
    vals = _values_for_crop_across_districts(crop, season)
    if not vals:
        return None
    district_val = _district_crop_baseline(district, crop, season)
    if district_val is None:
        return None
    # percentile rank: percentage of values strictly below district_val
    below = len([v for v in vals if v < district_val])
    # include ties roughly in middle; normalized to 0-100
    return (below / len(vals)) * 100.0


def get_yield_index(district: str, crop: str, season: str | None = None) -> float | None:
    """district yield / crop mean, or None if crop mean missing."""
    y = get_yield_per_hectare(district, crop, season)
    cm = crop_mean(crop, season)
    if cm is None or cm == 0:
        return None
    return float(y / cm) if y is not None else None


def get_yield_gap(district: str, crop: str, season: str | None = None) -> dict:
    """Return a dict with yield_per_ha, benchmark_yield_per_ha (75th pct), yield_gap_kg_ha."""
    y = get_yield_per_hectare(district, crop, season)
    vals = _values_for_crop_across_districts(crop, season)
    benchmark = _percentile_from_sorted(vals, 75) if vals else None
    gap = None
    if benchmark is not None and y is not None:
        gap = round(max(0.0, benchmark - y), 1)
    return {
        "yield_per_ha": round(y, 1) if y is not None else None,
        "benchmark_yield_per_ha": round(benchmark, 1) if benchmark is not None else None,
        "yield_gap_kg_ha": gap,
    }


def predict_yield(district: str | None, crop: str, season: str | None = None,
                  rainfall_mm: float | None = None, area_cultivated: float | None = None,
                  household_size: float | None = None, allow_category_proxy: bool = False,
                  crop_category: str | None = None) -> tuple[float | None, float, str]:
    """
    Returns (predicted_yield, confidence, model_version). predicted_yield is
    the total predicted output for the given cultivated area (kg); divide by
    area to get yield per hectare (see classify_priority).
    """
    area = float(area_cultivated) if area_cultivated is not None and area_cultivated > 0 else None
    interval = predict_with_interval(district, crop, season, allow_category_proxy=allow_category_proxy,
                                     crop_category=crop_category)
    if interval["point"] is None:
        return None, 0.0, "no-yield-data"
    yield_per_ha = interval["point"]
    relative_width = (interval["high"] - interval["low"]) / max(2.0 * yield_per_ha, 1e-9)
    confidence = min(1.0, max(0.0, 1.0 / (1.0 + relative_width)))
    model_version = interval.get("model_version") or interval["basis"]

    if area is None:
        # A total harvest cannot be stated without an observed area.
        return None, confidence, model_version
    predicted_total = round(yield_per_ha * area, 1)
    return predicted_total, confidence, model_version


def _priority_stability(district: str | None, crop: str) -> list[str] | None:
    # Fold stability is not recalculated from an uploaded release yet. Avoid
    # carrying an old CSV-derived stability result into current decisions.
    return None


def classify_priority(predicted_yield: float, area_cultivated: float | None,
                      district: str | None = None, crop: str | None = None,
                      season: str | None = None) -> dict:
    """Classify urgency and return measured components and fold stability.

    Cultivated area is used as a proxy for how many farmers may be affected;
    it is an exposure stand-in, not a household count.
    """
    import pandas as pd

    area = float(area_cultivated) if area_cultivated is not None and area_cultivated > 0 else None
    yield_per_ha = float(predicted_yield) / area if area else float(predicted_yield)
    bundle = None
    model_available = False
    actual = None
    expected = None
    crop_district_count = 0
    top_quartile = None
    area_percentile = None
    observed_area = area
    residual_se = None
    yield_index = None

    if crop:
        try:
            evidence = _live_yield_evidence(None, crop)
        except Exception:
            logging.exception("Unable to load database observations for priority context")
            evidence = []
        data = pd.DataFrame([{
            "district": row.get("district"),
            "season": row.get("season"),
            "yield_kg_ha": row.get("yield_kg_ha"),
            "cultivated_area_ha": row.get("cultivated_area_ha"),
            "year": int(match.group(0)) if (match := re.search(r"20\d{2}", str(row.get("season", "")))) else 0,
            "season_code": _season_code(row.get("season")),
        } for row in evidence if row.get("district")])
    else:
        data = pd.DataFrame()
    if not data.empty:
        crop_district_count = int(data.district.nunique())
        code = _season_code(season)
        if code:
            data = data[data.season_code.astype(str).str.upper() == code]
        if "year" in data.columns:
            data = data.sort_values("year", kind="stable").drop_duplicates("district", keep="last")
        district_rows = data[data.district.astype(str).str.casefold() == str(district or "").casefold()]
        if not district_rows.empty:
            latest = district_rows.sort_values("year", kind="stable").iloc[-1]
            actual = float(latest.yield_kg_ha) if np.isfinite(float(latest.yield_kg_ha)) else None
            if observed_area is None and np.isfinite(float(latest.get("cultivated_area_ha", np.nan))):
                observed_area = float(latest["cultivated_area_ha"])
        peer_yields = pd.to_numeric(data.yield_kg_ha, errors="coerce").dropna()
        if len(peer_yields):
            top_quartile = float(peer_yields.quantile(0.75))
        crop_mean_value = crop_mean(crop, season)
        reference_yield = actual if actual is not None else yield_per_ha
        if crop_mean_value and crop_mean_value > 0:
            yield_index = reference_yield / crop_mean_value
        areas = pd.to_numeric(data.get("cultivated_area_ha"), errors="coerce").dropna()
        if observed_area is not None and len(areas):
            area_percentile = float((areas <= observed_area).mean())
        if model_available:
            try:
                expected = float(predict_with_interval(district, crop, season)["point"])
            except (TypeError, ValueError, KeyError):
                expected = None

    observed = actual if actual is not None else yield_per_ha
    if model_available:
        result = classify_components(
            observed_yield=observed, expected_yield=expected, residual_se=residual_se,
            top_quartile_yield=top_quartile, cultivated_area_ha=observed_area,
            area_percentile=area_percentile, yield_index=yield_index,
            crop_district_count=crop_district_count, model_available=True,
        )
    elif crop_district_count < 10:
        result = classify_components(
            observed_yield=observed, expected_yield=None, residual_se=None,
            top_quartile_yield=top_quartile, cultivated_area_ha=observed_area,
            area_percentile=area_percentile, yield_index=yield_index,
            crop_district_count=crop_district_count, model_available=False,
        )
    else:
        result = classify_components(
            observed_yield=observed, expected_yield=None, residual_se=None,
            top_quartile_yield=top_quartile, cultivated_area_ha=observed_area,
            area_percentile=area_percentile, yield_index=yield_index,
            crop_district_count=max(crop_district_count, 10), model_available=False,
        )
    return apply_stability(result, _priority_stability(district, crop or ""))

"""Association-based explanations for NISR yield estimates.

Explanations use a district-held-out linear surrogate on sourced NISR rows.
The surrogate is explanatory only; it does not replace the serving baseline.
All reported values are associations in district-level survey data, not causes.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import threading
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.features import build_features, _parse_season_code

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "training_table.csv"
INTERPRETATION_NOTE = (
    "These factors are associations in district-level NISR survey data, not proven causes. "
    "The expected yield comes from a district-held-out explanatory model and may differ from the serving prediction."
)
MINIMUM_ROWS = 30
MATERIAL_GAP = 0.15

# Fixed language templates. Values and comparison figures are populated only
# from observed training-table fields and yield-ranked peer districts.
FEATURE_COPY = {
    "farmers_using_improved_seeds_pct": (
        "Improved seed use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_using_organic_fertilizer_pct": (
        "Organic fertilizer use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_using_inorganic_fertilizer_pct": (
        "Inorganic fertilizer use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_using_pesticides_pct": (
        "Pesticide use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_practicing_irrigation_pct": (
        "Irrigation use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_protecting_against_erosion_pct": (
        "Erosion protection is reported on {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_practicing_agroforestry_pct": (
        "Agroforestry is reported on {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "farmers_using_mechanization_pct": (
        "Mechanization use is {here:.1f}% here versus {peers:.1f}% in higher-yield districts."
    ),
    "agricultural_area_inorganic_fertilizer_share": (
        "Inorganic fertilizer is used on {here:.1f}% of cultivated area here versus {peers:.1f}% in higher-yield districts."
    ),
    "agricultural_area_organic_fertilizer_share": (
        "Organic fertilizer is used on {here:.1f}% of cultivated area here versus {peers:.1f}% in higher-yield districts."
    ),
    "modern_irrigated_area_share": (
        "Modern irrigation covers {here:.1f}% of cultivated area here versus {peers:.1f}% in higher-yield districts."
    ),
}


@dataclass(frozen=True)
class FittedExplanation:
    model: Pipeline
    feature_names: tuple[str, ...]
    numeric_features: tuple[str, ...]
    numeric_means: dict[str, float]
    numeric_scales: dict[str, float]
    coefficients: dict[str, float]
    intercept: float
    training_rows: int


class ExplanationService:
    """Cached, district-held-out Ridge contributions over sourced NISR data."""

    def __init__(self, data_path: Path = DATA_PATH):
        self.data_path = data_path
        self._lock = threading.RLock()
        self._cache_key: tuple[int, str] | None = None
        self._frame: pd.DataFrame | None = None
        self._fitted: dict[tuple[str, str], FittedExplanation | None] = {}

    def explain(self, district: str | None, crop: str, season: str | None,
                features: dict[str, Any] | pd.DataFrame | None = None) -> dict[str, Any]:
        if not district:
            return self._unavailable("District is required to compare sourced peers.")
        frame = self._load()
        code = _parse_season_code(season)
        if frame is None or code is None:
            return self._unavailable("Sourced district, crop, and season features are unavailable.")

        peers = frame[(frame.crop.astype(str).str.casefold() == crop.strip().casefold()) &
                      (frame.season_code.astype(str).str.upper() == code)].copy()
        if peers.empty:
            return self._unavailable("No NISR peer rows match this crop and season.")
        peers = peers.sort_values("year", kind="stable").drop_duplicates("district", keep="last")
        district_mask = peers.district.astype(str).str.casefold() == district.strip().casefold()
        actual_rows = peers[district_mask].sort_values("year", kind="stable")
        actual = float(actual_rows.iloc[-1].yield_kg_ha) if not actual_rows.empty and pd.notna(actual_rows.iloc[-1].yield_kg_ha) else None
        target = actual_rows.iloc[-1].copy() if not actual_rows.empty else None
        if features is not None:
            if isinstance(features, pd.DataFrame):
                if not features.empty:
                    supplied = features.iloc[0].to_dict()
            else:
                supplied = dict(features)
            if target is None:
                target = pd.Series({"district": district, "crop": crop, "season_code": code,
                                    "year": int(pd.to_numeric(frame.year, errors="coerce").max()) if "year" in frame else 0})
                crop_rows = frame[frame.crop.astype(str).str.casefold() == crop.strip().casefold()]
                if not crop_rows.empty:
                    target["crop_category"] = crop_rows.iloc[0]["crop_category"]
            target_values = target.to_dict() if isinstance(target, pd.Series) else dict(target)
            target_values.update(supplied)
            target = pd.Series(target_values)
        if target is None:
            return self._unavailable("No sourced feature row exists for this district, crop, and season.", actual)

        fitted = self._fit_excluding_district(frame, crop, district)
        if fitted is None:
            return self._unavailable("Too few complete NISR rows to fit a district-held-out explanation.", actual)
        target_frame = pd.DataFrame([target])
        known = {name: sorted(frame[name].dropna().astype(str).unique())
                 for name in ("district", "crop", "crop_category", "season_code") if name in frame}
        target_features = self._features(target_frame, known, frame)
        expected_log = float(fitted.model.predict(target_features)[0])
        expected = math.exp(expected_log)
        crop_peer_mean = float(pd.to_numeric(peers.yield_kg_ha, errors="coerce").dropna().mean())
        gap = ((actual - expected) / expected) if actual is not None and expected > 0 else None
        input_gap = (expected - crop_peer_mean) / crop_peer_mean if crop_peer_mean > 0 else None
        if gap is not None and gap <= -MATERIAL_GAP:
            diagnosis = "management_or_local_conditions"
            diagnosis_text = "Actual yield is materially below the explanatory expectation given the recorded inputs; investigate local conditions and management."
        elif input_gap is not None and input_gap <= -MATERIAL_GAP:
            diagnosis = "input_access"
            diagnosis_text = "Recorded inputs are associated with a lower expected yield than the crop-season peer average; review access to relevant inputs."
        elif actual is None:
            diagnosis = "actual_yield_unavailable"
            diagnosis_text = "Actual yield is not available for this district, crop, and season, so the gap type cannot be assessed."
        else:
            diagnosis = "no_material_gap_identified"
            diagnosis_text = "The available data do not show a material gap attributable to recorded inputs or a residual shortfall."

        contributions = self._contributions(fitted, target_features, expected_log)
        enriched = self._add_peer_language(contributions, target, peers, district)
        factors = enriched[:3]
        return {
            "expected_yield_given_inputs_kg_ha": round(expected, 1),
            "actual_yield_kg_ha": round(actual, 1) if actual is not None else None,
            "crop_season_peer_mean_kg_ha": round(crop_peer_mean, 1),
            "yield_gap_vs_expected_pct": round(gap * 100, 1) if gap is not None else None,
            "diagnosis": diagnosis,
            "diagnosis_text": diagnosis_text,
            "factors": factors,
            "explanation_model": "district_held_out_ridge_association_surrogate",
            "interpretation_note": INTERPRETATION_NOTE,
            "data_status": "sourced" if factors else "no_explainable_sourced_features",
        }

    @staticmethod
    def _unavailable(reason: str, actual: float | None = None) -> dict[str, Any]:
        return {"expected_yield_given_inputs_kg_ha": None,
                "actual_yield_kg_ha": round(actual, 1) if actual is not None else None,
                "crop_season_peer_mean_kg_ha": None, "yield_gap_vs_expected_pct": None,
                "diagnosis": "insufficient_data", "diagnosis_text": reason, "factors": [],
                "explanation_model": "district_held_out_ridge_association_surrogate",
                "interpretation_note": INTERPRETATION_NOTE, "data_status": "insufficient_data"}

    def _load(self) -> pd.DataFrame | None:
        if not self.data_path.is_file():
            return None
        key = (self.data_path.stat().st_mtime_ns, str(self.data_path.resolve()))
        with self._lock:
            if self._cache_key != key:
                data = pd.read_csv(self.data_path)
                required = {"district", "crop", "season_code", "yield_kg_ha", "crop_category"}
                if not required.issubset(data.columns):
                    return None
                data["yield_kg_ha"] = pd.to_numeric(data["yield_kg_ha"], errors="coerce")
                data = data[data.yield_kg_ha.gt(0)].copy()
                self._frame = data
                self._cache_key = key
                self._fitted.clear()
            return self._frame

    @staticmethod
    def _features(frame: pd.DataFrame, known: dict[str, list[str]],
                  area_reference: pd.DataFrame | None = None) -> pd.DataFrame:
        result = build_features(frame, known_categories=known, district_area_reference=area_reference)
        for col in result.select_dtypes(include=["string", "object"]).columns:
            result[col] = result[col].astype(object).where(result[col].notna(), np.nan)
        return result

    def _fit_excluding_district(self, frame: pd.DataFrame, crop: str, district: str) -> FittedExplanation | None:
        cache_key = (crop.casefold(), district.casefold())
        with self._lock:
            if cache_key in self._fitted:
                return self._fitted[cache_key]
        train = frame[(frame.district.astype(str).str.casefold() != district.casefold()) &
                      (frame.crop.astype(str).str.casefold() == crop.casefold()) & frame.yield_kg_ha.gt(0)].copy()
        if len(train) < MINIMUM_ROWS or train.district.nunique() < 2:
            with self._lock:
                self._fitted[cache_key] = None
            return None
        known = {name: sorted(train[name].dropna().astype(str).unique())
                 for name in ("district", "crop", "crop_category", "season_code") if name in train}
        x = self._features(train, known, frame)
        categorical = [c for c in ("district", "crop", "crop_category", "season_code") if c in x]
        numeric = [c for c in x.columns if c not in categorical]
        transform = ColumnTransformer([
            ("categorical", Pipeline([("imputer", SimpleImputer(strategy="most_frequent")),
                                       ("onehot", OneHotEncoder(handle_unknown="ignore"))]), categorical),
            ("numeric", Pipeline([("imputer", SimpleImputer(strategy="median", keep_empty_features=True)),
                                  ("scale", StandardScaler())]), numeric),
        ], remainder="drop")
        model = Pipeline([("features", transform), ("ridge", Ridge(alpha=25.0, solver="lsqr"))])
        model.fit(x, np.log(train.yield_kg_ha.astype(float)))
        transformed = model.named_steps["features"]
        names = transformed.get_feature_names_out().tolist()
        coefs = model.named_steps["ridge"].coef_
        numeric_pipeline = transformed.named_transformers_["numeric"]
        imputer = numeric_pipeline.named_steps["imputer"]
        scaler = numeric_pipeline.named_steps["scale"]
        numeric_names = tuple(numeric)
        numeric_means = {name: float(mean) for name, mean in zip(numeric_names, imputer.statistics_)}
        numeric_scales = {name: float(scale) if scale else 1.0 for name, scale in zip(numeric_names, scaler.scale_)}
        offset = len(transformed.named_transformers_["categorical"].named_steps["onehot"].get_feature_names_out(categorical))
        coefficients = {name: float(coefs[offset + idx] / numeric_scales[name]) for idx, name in enumerate(numeric_names)}
        fitted = FittedExplanation(model, tuple(names), numeric_names, numeric_means, numeric_scales,
                                  coefficients, float(model.named_steps["ridge"].intercept_), len(train))
        with self._lock:
            self._fitted[cache_key] = fitted
        return fitted

    @staticmethod
    def _contributions(fitted: FittedExplanation, target: pd.DataFrame, expected_log: float) -> list[dict[str, Any]]:
        features = target.iloc[0]
        factors = []
        for name in fitted.numeric_features:
            value = pd.to_numeric(pd.Series([features.get(name)]), errors="coerce").iloc[0]
            if pd.isna(value) or name not in FEATURE_COPY:
                continue
            effect_log = fitted.coefficients[name] * (float(value) - fitted.numeric_means[name])
            if not math.isfinite(effect_log) or abs(effect_log) < 1e-8:
                continue
            contribution = math.exp(expected_log) - math.exp(expected_log - effect_log)
            factors.append({"feature": name, "direction": "above_expected" if effect_log > 0 else "below_expected",
                            "contribution_kg_ha": round(contribution, 1), "_effect": effect_log})
        factors.sort(key=lambda item: abs(item["contribution_kg_ha"]), reverse=True)
        return factors

    @staticmethod
    def _add_peer_language(factors: list[dict[str, Any]], target: pd.Series,
                           peers: pd.DataFrame, district: str) -> list[dict[str, Any]]:
        peer = peers.copy()
        peer["yield_kg_ha"] = pd.to_numeric(peer.yield_kg_ha, errors="coerce")
        peer = peer.dropna(subset=["yield_kg_ha"]).sort_values("yield_kg_ha", ascending=False)
        peer = peer[peer.district.astype(str).str.casefold() != district.casefold()]
        top_n = max(1, int(math.ceil(len(peer) * 0.25)))
        top = peer.head(top_n)
        result = []
        for factor in factors:
            name = factor["feature"]
            here = pd.to_numeric(pd.Series([target.get(name)]), errors="coerce").iloc[0]
            peer_values = pd.to_numeric(top.get(name, pd.Series(dtype=float)), errors="coerce").dropna()
            if pd.isna(here) or peer_values.empty:
                continue
            peer_value = float(peer_values.mean())
            # Keep percentage-valued features in percentage points, shares as
            # percent for readable but source-faithful comparisons.
            if name.endswith("_share"):
                here, peer_value = float(here) * 100.0, peer_value * 100.0
            else:
                here, peer_value = float(here), peer_value
            factor["plain_language"] = FEATURE_COPY[name].format(here=here, peers=peer_value)
            factor["peer_direction"] = "below_peers" if here < peer_value else "at_or_above_peers"
            factor["peer_value"] = round(peer_value, 1)
            factor["district_value"] = round(here, 1)
            factor.pop("_effect", None)
            result.append(factor)
        return result


_service = ExplanationService()


def explain_prediction(district: str | None, crop: str, season: str | None,
                       features: dict[str, Any] | pd.DataFrame | None = None) -> dict[str, Any]:
    """Explain only when feature observations are available in the live store.

    The former surrogate read a bundled CSV at request time. Until NISR import
    records include the feature columns required by that explanation model, do
    not present a file-derived explanation beside a database-derived baseline.
    """
    return _service._unavailable(
        "Explanatory feature evidence is not yet stored with the active database release."
    )

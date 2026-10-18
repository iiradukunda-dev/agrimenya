from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeClassifier

from app.ml.vision_disease_model import predict_vision_disease, vision_model_status

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "disease_model.pkl"

SYMPTOM_KEYWORDS = {
    "yellowing": ["yellow", "chlorosis", "yellowing"],
    "brown_lesions": ["brown lesion", "brown spot", "lesion", "necrotic", "dry patch", "patches"],
    "wilting": ["wilting", "drooping", "curling", "leaf curl"],
    "powdery": ["powdery", "white dust", "white coating", "mildew"],
    "rust": ["rust", "orange pustule", "reddish spores"],
    "water_soaked": ["water soaked", "wet patch", "dark lesion", "tissue decay"],
    "leaf_drop": ["leaf drop", "defoliation", "falling leaves"],
    "stunting": ["stunted", "short plant", "poor growth"],
}

DISEASE_ACTIONS = {
    "leaf_blight": [
        "Remove and destroy infected leaves immediately.",
        "Improve airflow and reduce excess leaf moisture.",
        "Apply a registered preventive fungicide if disease pressure is high.",
    ],
    "powdery_mildew": [
        "Prune crowded foliage to increase air circulation.",
        "Apply a sulfur- or potassium-bicarbonate-based treatment when necessary.",
        "Reduce overhead watering to keep leaves dry.",
    ],
    "rust": [
        "Avoid planting susceptible varieties in the same field repeatedly.",
        "Apply a rust-targeted fungicide early at the first suspicion.",
        "Inspect neighboring fields for spread and isolate infected plants.",
    ],
    "bacterial_spot": [
        "Avoid working in wet fields to reduce spread between plants.",
        "Use disease-free seeds and clean tools before each operation.",
        "Rotate with a non-host crop for the next season.",
    ],
    "healthy": [
        "Maintain the current agronomic plan and continue field monitoring.",
        "Keep routine scouting and soil health checks on schedule.",
    ],
}


def _normalize_crop(crop: str | None) -> str:
    if not crop:
        return "maize"
    value = str(crop).strip().lower()
    aliases = {
        "maize": "maize",
        "corn": "maize",
        "bean": "beans",
        "beans": "beans",
        "potato": "potato",
        "irish potato": "potato",
        "tomato": "tomato",
        "wheat": "wheat",
        "rice": "rice",
        "cassava": "cassava",
        "sweet potato": "sweet_potato",
    }
    return aliases.get(value, value.replace(" ", "_"))


def _build_symptom_features(text: str | None) -> dict[str, int]:
    combined = (text or "").lower()
    features = {name: 0 for name in SYMPTOM_KEYWORDS}
    for name, keywords in SYMPTOM_KEYWORDS.items():
        features[name] = 1 if any(keyword in combined for keyword in keywords) else 0
    return features


def _build_training_rows() -> list[dict]:
    rows = [
        {"crop": "maize", "yellowing": 1, "brown_lesions": 1, "wilting": 1, "powdery": 0, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 1, "label": "leaf_blight"},
        {"crop": "maize", "yellowing": 1, "brown_lesions": 0, "wilting": 0, "powdery": 1, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 0, "label": "powdery_mildew"},
        {"crop": "maize", "yellowing": 0, "brown_lesions": 0, "wilting": 0, "powdery": 0, "rust": 1, "water_soaked": 0, "leaf_drop": 0, "stunting": 0, "label": "rust"},
        {"crop": "beans", "yellowing": 1, "brown_lesions": 1, "wilting": 1, "powdery": 0, "rust": 0, "water_soaked": 1, "leaf_drop": 0, "stunting": 0, "label": "bacterial_spot"},
        {"crop": "beans", "yellowing": 0, "brown_lesions": 0, "wilting": 0, "powdery": 1, "rust": 0, "water_soaked": 0, "leaf_drop": 1, "stunting": 0, "label": "powdery_mildew"},
        {"crop": "potato", "yellowing": 1, "brown_lesions": 1, "wilting": 1, "powdery": 0, "rust": 0, "water_soaked": 1, "leaf_drop": 1, "stunting": 1, "label": "leaf_blight"},
        {"crop": "tomato", "yellowing": 1, "brown_lesions": 1, "wilting": 0, "powdery": 0, "rust": 0, "water_soaked": 1, "leaf_drop": 0, "stunting": 0, "label": "bacterial_spot"},
        {"crop": "wheat", "yellowing": 1, "brown_lesions": 0, "wilting": 0, "powdery": 0, "rust": 1, "water_soaked": 0, "leaf_drop": 0, "stunting": 0, "label": "rust"},
        {"crop": "rice", "yellowing": 1, "brown_lesions": 1, "wilting": 1, "powdery": 0, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 1, "label": "leaf_blight"},
        {"crop": "cassava", "yellowing": 1, "brown_lesions": 1, "wilting": 1, "powdery": 0, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 1, "label": "leaf_blight"},
        {"crop": "maize", "yellowing": 0, "brown_lesions": 0, "wilting": 0, "powdery": 0, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 0, "label": "healthy"},
        {"crop": "beans", "yellowing": 0, "brown_lesions": 0, "wilting": 0, "powdery": 0, "rust": 0, "water_soaked": 0, "leaf_drop": 0, "stunting": 0, "label": "healthy"},
    ]
    return rows


def _load_or_train_model():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    if MODEL_PATH.exists():
        with MODEL_PATH.open("rb") as fh:
            return pickle.load(fh)

    training_df = pd.DataFrame(_build_training_rows())
    X = training_df.drop(columns=["label"])
    y = training_df["label"]

    pipeline = Pipeline([
        (
            "preprocess",
            ColumnTransformer(
                transformers=[
                    ("crop", OneHotEncoder(handle_unknown="ignore"), ["crop"]),
                    ("symptoms", "passthrough", [
                        "yellowing",
                        "brown_lesions",
                        "wilting",
                        "powdery",
                        "rust",
                        "water_soaked",
                        "leaf_drop",
                        "stunting",
                    ]),
                ]
            ),
        ),
        ("classifier", DecisionTreeClassifier(max_depth=4, random_state=42)),
    ])

    pipeline.fit(X, y)
    with MODEL_PATH.open("wb") as fh:
        pickle.dump(pipeline, fh)
    return pipeline


def detect_crop_disease(crop: str | None, symptoms: str | None, image_description: str | None = None, image_bytes: bytes | None = None) -> dict:
    if image_bytes:
        status = vision_model_status()
        if status["trained"]:
            vision_result = predict_vision_disease(image_bytes, crop_hint=crop)
            if vision_result.get("model_status") == "trained":
                return {
                    "predicted_disease": str(vision_result["predicted_disease"]).replace("_", " ").title(),
                    "confidence": float(vision_result["confidence"]),
                    "risk_level": vision_result["risk_level"],
                    "recommended_actions": vision_result["recommended_actions"],
                    "crop": (crop or "Crop").strip().title(),
                    "source": "vision-cnn",
                    "confidence_basis": "uncalibrated_model_score",
                    "interpretation_note": "Experimental image association only; not a diagnosis. Confirm with an RAB or district agronomist before treatment.",
                    "recommended_actions": ["Request an in-person assessment from an RAB or district agronomist before treatment."],
                }
    normalized_crop = _normalize_crop(crop)
    return {
        "predicted_disease": "Unconfirmed",
        "confidence": None,
        "risk_level": "Unknown",
        "recommended_actions": ["Request an in-person assessment from an RAB or district agronomist before treatment."],
        "crop": normalized_crop.replace("_", " ").title(),
        "source": "insufficient_validated_symptom_data",
        "interpretation_note": "Symptoms alone are insufficient for a validated diagnosis. These district-level tools are not a substitute for field inspection.",
    }

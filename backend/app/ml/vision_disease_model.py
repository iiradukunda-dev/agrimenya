from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import numpy as np

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None

try:
    import torch
    from torchvision import transforms
    from torchvision.models import resnet50
except Exception:  # pragma: no cover - optional dependency for future CNN training
    torch = None
    transforms = None
    resnet50 = None

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
VISION_MODEL_DIR = ARTIFACTS_DIR / "vision_disease"
MODEL_PATH = VISION_MODEL_DIR / "model.pth"
CONFIG_PATH = VISION_MODEL_DIR / "config.json"
LABELS_PATH = VISION_MODEL_DIR / "labels.json"

DEFAULT_LABELS = [
    "healthy",
    "maize_leaf_blight",
    "maize_rust",
    "bean_bacterial_spot",
    "potato_early_blight",
    "tomato_leaf_mold",
]


def ensure_model_metadata() -> dict[str, Any]:
    VISION_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    config = {
        "model_name": "resnet50",
        "image_size": 224,
        "num_classes": len(DEFAULT_LABELS),
        "labels": DEFAULT_LABELS,
        "trained": MODEL_PATH.exists(),
    }
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
    elif MODEL_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text())
        config["trained"] = True
        CONFIG_PATH.write_text(json.dumps(config, indent=2))
    if not LABELS_PATH.exists():
        LABELS_PATH.write_text(json.dumps(DEFAULT_LABELS, indent=2))
    return config


def vision_model_status() -> dict[str, Any]:
    config = ensure_model_metadata()
    labels = json.loads(LABELS_PATH.read_text()) if LABELS_PATH.exists() else DEFAULT_LABELS
    available = torch is not None and resnet50 is not None and Image is not None
    trained = MODEL_PATH.exists() and available
    return {
        "available": available,
        "trained": trained,
        "model_path": str(MODEL_PATH),
        "artifact_dir": str(VISION_MODEL_DIR),
        "labels": labels,
        "config": config,
        "message": "Vision model ready" if trained else "Vision model not trained yet",
    }


def load_vision_model() -> tuple[Any | None, list[str], dict[str, Any]]:
    status = vision_model_status()
    config = status["config"]
    labels = status["labels"]

    if not status["trained"]:
        return None, labels, config

    try:
        model = resnet50(weights=None)
        in_features = model.fc.in_features
        model.fc = torch.nn.Linear(in_features, len(labels))
        state = torch.load(MODEL_PATH, map_location="cpu")
        if isinstance(state, dict) and "model_state_dict" in state:
            model.load_state_dict(state["model_state_dict"])
        else:
            model.load_state_dict(state)
        model.eval()
        return model, labels, config
    except Exception:
        return None, labels, config


def preprocess_image_for_vision(image_bytes: bytes, image_size: int = 224) -> np.ndarray:
    if torch is None or transforms is None or Image is None:
        return np.zeros((image_size, image_size, 3), dtype=np.uint8)

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    tensor = transform(image)
    return tensor.unsqueeze(0).numpy()


def predict_vision_disease(image_bytes: bytes, crop_hint: str | None = None) -> dict[str, Any]:
    labels = json.loads(LABELS_PATH.read_text()) if LABELS_PATH.exists() else DEFAULT_LABELS
    model, labels, config = load_vision_model()

    if model is None or torch is None:
        fallback = {
            "predicted_disease": "vision model not trained yet",
            "confidence": 0.0,
            "risk_level": "Low",
            "recommended_actions": [
                "Collect labeled plant disease photos and train the CNN model.",
                "Use the symptom-based model until the image model is available.",
            ],
            "labels": labels,
            "model_status": "not_trained",
        }
        if crop_hint:
            fallback["crop_hint"] = crop_hint
        return fallback

    tensor = preprocess_image_for_vision(image_bytes, image_size=config.get("image_size", 224))
    with torch.no_grad():
        logits = model(torch.tensor(tensor))
        probs = torch.softmax(logits, dim=1)[0]
        idx = int(torch.argmax(probs).item())
        confidence = float(probs[idx].item())
        disease = labels[idx]

    result = {
        "predicted_disease": disease,
        "confidence": round(confidence, 3),
        "risk_level": "High" if confidence >= 0.75 else "Medium" if confidence >= 0.6 else "Low",
        "recommended_actions": [
            "Inspect the affected plants immediately and mark the spread area.",
            "Apply the appropriate crop-protection treatment for the predicted disease.",
            "Schedule a follow-up scouting visit within 7 days.",
        ],
        "labels": labels,
        "model_status": "trained",
    }
    if crop_hint:
        result["crop_hint"] = crop_hint
    return result

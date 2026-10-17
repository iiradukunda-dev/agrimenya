from __future__ import annotations

import io
import json
import logging
import threading
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
logger = logging.getLogger(__name__)
_MODEL_CACHE: tuple[Any | None, list[str], dict[str, Any]] | None = None
_MODEL_LOCK = threading.Lock()


def ensure_model_metadata() -> dict[str, Any]:
    config = {
        "model_name": "resnet50",
        "image_size": 224,
        "num_classes": len(DEFAULT_LABELS),
        "labels": DEFAULT_LABELS,
        "trained": MODEL_PATH.exists(),
    }
    try:
        if CONFIG_PATH.exists():
            loaded = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
        if LABELS_PATH.exists():
            labels = json.loads(LABELS_PATH.read_text(encoding="utf-8"))
            if isinstance(labels, list) and labels and all(isinstance(label, str) for label in labels):
                config["labels"] = labels
    except (OSError, json.JSONDecodeError):
        logger.exception("Invalid vision model metadata; image model will not be available")
        config["trained"] = False
    config["trained"] = bool(config.get("trained") and MODEL_PATH.is_file())
    return config


def vision_model_status() -> dict[str, Any]:
    config = ensure_model_metadata()
    labels = config.get("labels", DEFAULT_LABELS)
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
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    with _MODEL_LOCK:
        if _MODEL_CACHE is not None:
            return _MODEL_CACHE
        _MODEL_CACHE = _load_vision_model_once()
    return _MODEL_CACHE


def _load_vision_model_once() -> tuple[Any | None, list[str], dict[str, Any]]:
    status = vision_model_status()
    config = status["config"]
    labels = status["labels"]

    if not status["trained"]:
        return None, labels, config

    try:
        model = resnet50(weights=None)
        in_features = model.fc.in_features
        model.fc = torch.nn.Linear(in_features, len(labels))
        state = torch.load(MODEL_PATH, map_location="cpu", weights_only=True)
        if isinstance(state, dict) and "model_state_dict" in state:
            model.load_state_dict(state["model_state_dict"])
        else:
            model.load_state_dict(state)
        model.eval()
        return model, labels, config
    except Exception:
        logger.exception("Could not load the vision model; image inference is disabled")
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
            "predicted_disease": "Unconfirmed",
            "confidence": None,
            "risk_level": "Unknown",
            "recommended_actions": ["Request an in-person assessment from an RAB or district agronomist before treatment."],
            "labels": labels,
            "model_status": "not_trained",
            "interpretation_note": "No validated image model is available. Confirm crop symptoms with an RAB or district agronomist.",
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
        "risk_level": "Unknown",
        "recommended_actions": ["Request an in-person assessment from an RAB or district agronomist before treatment."],
        "labels": labels,
        "model_status": "trained",
        "confidence_basis": "uncalibrated_model_score",
        "interpretation_note": "Experimental image association only; not a diagnosis. Confirm with an RAB or district agronomist before treatment.",
    }
    if crop_hint:
        result["crop_hint"] = crop_hint
    return result

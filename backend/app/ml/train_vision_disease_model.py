"""
Train a crop disease CNN on labeled image folders.

Expected dataset structure:
    data/plant_disease_dataset/
      train/
        healthy/
        maize_leaf_blight/
        maize_rust/
        ...
      val/
        healthy/
        maize_leaf_blight/
        ...

This is the real next-step model for the project: once the dataset is ready,
this script trains a ResNet50 fine-tuned model and saves it to:
    app/ml/artifacts/vision_disease/model.pth

It is intentionally lightweight and production-friendly, using only torchvision,
Pillow, and PyTorch.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    import torch
    from torch import nn
    from torch.optim import AdamW
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms
    from torchvision.models import resnet50
except Exception as exc:  # pragma: no cover - environment-specific
    raise RuntimeError(
        "Vision training requires torch and torchvision to be installed. "
        "Install the runtime with: pip install torch torchvision pillow"
    ) from exc

from app.ml.vision_disease_model import DEFAULT_LABELS, MODEL_PATH, VISION_MODEL_DIR

DATASET_ROOT = Path(__file__).resolve().parents[2] / "data" / "plant_disease_dataset"


def build_transforms(image_size: int = 224):
    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def train(dataset_root: str | Path = DATASET_ROOT, epochs: int = 8, batch_size: int = 16, learning_rate: float = 1e-4) -> dict:
    dataset_root = Path(dataset_root)
    if not dataset_root.exists():
        raise FileNotFoundError(
            f"Disease dataset not found at {dataset_root}. "
            "Add a labeled plant-disease dataset before training the CNN."
        )

    train_dir = dataset_root / "train"
    val_dir = dataset_root / "val"
    if not train_dir.exists() or not val_dir.exists():
        raise FileNotFoundError(
            "Expected dataset structure: <root>/train and <root>/val with class folders."
        )

    train_dataset = datasets.ImageFolder(str(train_dir), transform=build_transforms())
    val_dataset = datasets.ImageFolder(str(val_dir), transform=build_transforms())

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

    model = resnet50(weights="IMAGENET1K_V1")
    model.fc = nn.Linear(model.fc.in_features, len(train_dataset.classes))
    model.train()

    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=learning_rate)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)

        train_loss = running_loss / len(train_dataset)
        val_loss = 0.0
        correct = 0
        total = 0
        model.eval()
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                logits = model(images)
                loss = criterion(logits, labels)
                val_loss += loss.item() * images.size(0)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)
        val_loss = val_loss / len(val_dataset)
        accuracy = correct / total if total else 0.0
        print(f"Epoch {epoch + 1}/{epochs} | train_loss={train_loss:.4f} | val_loss={val_loss:.4f} | val_acc={accuracy:.3f}")

    VISION_MODEL_DIR.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)

    config = {
        "model_name": "resnet50",
        "image_size": 224,
        "num_classes": len(train_dataset.classes),
        "labels": train_dataset.classes,
        "trained": True,
        "dataset_root": str(dataset_root),
    }
    (VISION_MODEL_DIR / "config.json").write_text(json.dumps(config, indent=2))
    (VISION_MODEL_DIR / "labels.json").write_text(json.dumps(train_dataset.classes, indent=2))
    return config


if __name__ == "__main__":
    train()

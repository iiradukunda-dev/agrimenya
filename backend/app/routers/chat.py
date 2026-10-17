from uuid import UUID
from io import BytesIO

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from typing import Literal

from app.db import crud
from app.core.auth import require_user
from app.core.config import settings
from app.services.ai_assistant import ask_assistant_with_source, enforce_request_limit
from app.services.disease_detector import detect_crop_disease

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., max_length=500)


class ChatRequest(BaseModel):
    zone_id: UUID
    question: str = Field(..., min_length=1, max_length=500)
    crop: str | None = Field(default=None, min_length=1, max_length=50)
    season: str | None = Field(default=None, min_length=1, max_length=80)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)


class ChatResponse(BaseModel):
    zone_id: UUID
    question: str
    answer: str
    source: str = "grounded-context"
    district: str | None = None


class DiseaseDetectionRequest(BaseModel):
    zone_id: UUID
    crop: str = Field(..., min_length=1, max_length=50)
    symptoms: str = Field(..., min_length=1, max_length=1000)
    image_description: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)


class DiseaseDetectionResponse(BaseModel):
    zone_id: UUID
    crop: str
    predicted_disease: str
    confidence: float | None = None
    risk_level: str
    recommended_actions: list[str]
    source: str = "insufficient_validated_symptom_data"
    interpretation_note: str | None = None


@router.post("")
def chat(request: ChatRequest, http_request: Request, _: dict = Depends(require_user)):
    client_id = http_request.client.host if http_request.client else "unknown"
    enforce_request_limit(client_id)
    answer, source, district = ask_assistant_with_source(request.zone_id, request.question,
                                               request.crop, request.season,
                                               [turn.model_dump() for turn in request.history])
    return ChatResponse(
        zone_id=request.zone_id,
        question=request.question,
        answer=answer,
        source=source,
        district=district,
    )


@router.post("/disease-detect")
def disease_detect(request: DiseaseDetectionRequest, _: dict = Depends(require_user)):
    zone = crud.get_zone(request.zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    result = detect_crop_disease(request.crop, request.symptoms, request.image_description)
    return DiseaseDetectionResponse(
        zone_id=request.zone_id,
        crop=result["crop"],
        predicted_disease=result["predicted_disease"],
        confidence=result["confidence"],
        risk_level=result["risk_level"],
        recommended_actions=result["recommended_actions"],
        source=result.get("source", "symptom-model"),
        interpretation_note=result.get("interpretation_note"),
    )


@router.post("/disease-detect-upload")
async def disease_detect_upload(
    zone_id: UUID = Form(...),
    crop: str = Form(...),
    symptoms: str = Form(...),
    image_description: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
    _: dict = Depends(require_user),
):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    description = image_description or ""
    image_bytes = None
    if image and image.filename:
        if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
            raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
        image_bytes = await image.read(settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024 + 1)
        if len(image_bytes) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(status_code=413, detail=f"Image exceeds {settings.MAX_UPLOAD_SIZE_MB} MB")
        try:
            from PIL import Image, UnidentifiedImageError

            with Image.open(BytesIO(image_bytes)) as decoded:
                if decoded.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(status_code=415, detail="Image content must be JPEG, PNG, or WebP")
                if decoded.width * decoded.height > 20_000_000:
                    raise HTTPException(status_code=413, detail="Image dimensions are too large")
                decoded.verify()
        except ImportError:
            valid_signature = (
                image_bytes.startswith(b"\x89PNG\r\n\x1a\n")
                or image_bytes.startswith(b"\xff\xd8\xff")
                or (image_bytes.startswith(b"RIFF") and image_bytes[8:12] == b"WEBP")
            )
            if not valid_signature:
                raise HTTPException(status_code=422, detail="Uploaded file is not a valid image")
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise HTTPException(status_code=422, detail="Uploaded file is not a valid image") from exc
        description = f"{description} Uploaded image: {image.filename}.".strip()

    result = detect_crop_disease(crop, symptoms, description, image_bytes=image_bytes)
    return DiseaseDetectionResponse(
        zone_id=zone_id,
        crop=result["crop"],
        predicted_disease=result["predicted_disease"],
        confidence=result["confidence"],
        risk_level=result["risk_level"],
        recommended_actions=result["recommended_actions"],
        source=result.get("source", "symptom-model"),
        interpretation_note=result.get("interpretation_note"),
    )

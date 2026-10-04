from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.db import crud
from app.services.ai_assistant import ask_assistant
from app.services.disease_detector import detect_crop_disease

router = APIRouter(prefix="/chat", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    zone_id: UUID
    question: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    zone_id: UUID
    question: str
    answer: str
    source: str = "grounded-context"


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
    confidence: float
    risk_level: str
    recommended_actions: list[str]
    source: str = "trained-disease-model"


@router.post("")
def chat(request: ChatRequest):
    answer = ask_assistant(request.zone_id, request.question)
    return ChatResponse(
        zone_id=request.zone_id,
        question=request.question,
        answer=answer,
        source="grounded-context",
    )


@router.post("/disease-detect")
def disease_detect(request: DiseaseDetectionRequest):
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
    )


@router.post("/disease-detect-upload")
async def disease_detect_upload(
    zone_id: UUID = Form(...),
    crop: str = Form(...),
    symptoms: str = Form(...),
    image_description: str | None = Form(default=None),
    image: UploadFile | None = File(default=None),
):
    zone = crud.get_zone(zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    description = image_description or ""
    image_bytes = None
    if image and image.filename:
        image_bytes = await image.read()
        description = f"{description} Uploaded image: {image.filename}.".strip()

    result = detect_crop_disease(crop, symptoms, description, image_bytes=image_bytes)
    return DiseaseDetectionResponse(
        zone_id=zone_id,
        crop=result["crop"],
        predicted_disease=result["predicted_disease"],
        confidence=result["confidence"],
        risk_level=result["risk_level"],
        recommended_actions=result["recommended_actions"],
    )

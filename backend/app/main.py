from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers import decision, planification, segmentation, communication, chat, alignment, admin, live_data

@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.APP_ENV == "production":
        settings.validate_production()
    yield


app = FastAPI(
    title="Agri-Menya API",
    description="Decision and Planning Support System for agricultural productivity in Rwanda.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url=None if settings.APP_ENV == "production" else "/docs",
    redoc_url=None if settings.APP_ENV == "production" else "/redoc",
    openapi_url=None if settings.APP_ENV == "production" else "/openapi.json",
)

if settings.APP_ENV == "production":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decision.router)
app.include_router(planification.router)
app.include_router(segmentation.router)
app.include_router(communication.router)
app.include_router(chat.router)
app.include_router(alignment.router)
app.include_router(admin.router)
app.include_router(live_data.router)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if settings.APP_ENV == "production":
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# Configure logging early and mount debug router in non-production
LOG_PATH = configure_logging()
import logging
logging.getLogger(__name__).info("Application starting up, logs -> %s", LOG_PATH)
if settings.APP_ENV != "production":
    from app.routers import debug

    app.include_router(debug.router)


@app.get("/health")
def health_check():
    # Include lightweight model/artifact presence information for ops.
    try:
        from app.ml import predict as _predict

        model_bundle = _predict._load_yield_model()
        baselines = _predict._load_baselines()
    except Exception:
        model_bundle = None
        baselines = {}

    database_status = "unavailable"
    try:
        from app.core.supabase_client import get_supabase

        get_supabase().table("zones").select("id").limit(1).execute()
        database_status = "ok"
    except Exception:
        logging.getLogger(__name__).exception("Health check database probe failed")

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "env": settings.APP_ENV,
        "database_status": database_status,
        "model_present": bool(model_bundle),
        "model_version": model_bundle.get("model_version") if model_bundle else None,
        "baselines_present": bool(baselines),
        "baselines_overall_average": baselines.get("overall_average") if baselines else None,
    }


@app.get("/")
def root():
    return {
        "message": "Agri-Menya API is running.",
        "docs": "/docs" if settings.APP_ENV != "production" else None,
        "health": "/health",
    }

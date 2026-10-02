from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers import (
    alignment,
    chat,
    communication,
    decision,
    planification,
    segmentation,
)
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML models on startup
    import logging
    logger = logging.getLogger(__name__)
    try:
        from app.ml import predict as _predict
        app.state.model_bundle = _predict._load_yield_model()
        app.state.baselines = _predict._load_baselines()
        logger.info("ML models and baselines loaded successfully.")
    except Exception as e:
        app.state.model_bundle = None
        app.state.baselines = {}
        logger.error(f"Failed to load ML models during startup: {e}")
    yield
    # Cleanup on shutdown
    app.state.model_bundle = None
    app.state.baselines = {}

app = FastAPI(
    title="agrimenya API",
    description="Decision and Planning Support System for agricultural productivity in Rwanda.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(decision.router, tags=["Decision"])
app.include_router(planification.router, tags=["Planification"])
app.include_router(segmentation.router, tags=["Segmentation"])
app.include_router(communication.router, tags=["Communication"])
app.include_router(chat.router, tags=["AI Chat"])
app.include_router(alignment.router, tags=["Alignment"])

# Configure logging early and mount debug router in non-production
LOG_PATH = configure_logging()
import logging
logging.getLogger(__name__).info("Application starting up, logs -> %s", LOG_PATH)

if settings.APP_ENV != "production":
    from app.routers import debug
    app.include_router(debug.router, tags=["Debug"])


@app.get("/health", tags=["System"])
def health_check(request: Request):
    model_bundle = getattr(request.app.state, "model_bundle", None)
    baselines = getattr(request.app.state, "baselines", {})

    return {
        "status": "ok",
        "env": settings.APP_ENV,
        "model_present": bool(model_bundle),
        "model_version": model_bundle.get("model_version") if model_bundle else None,
        "baselines_present": bool(baselines),
        "baselines_overall_average": baselines.get("overall_average") if baselines else None,
    }


@app.get("/")
def root():
    return {
        "message": "Agri-Menya API is running.",
        "docs": "/docs",
        "health": "/health",
    }

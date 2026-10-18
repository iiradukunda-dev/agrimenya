from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import settings
from app.core.logging import configure_logging
from app.routers import decision, planification, segmentation, communication, community, chat, alignment, admin, live_data, whatsapp_admin, webhooks, admin_auth

DEVELOPMENT_ENVIRONMENTS = {"development", "test"}
IS_DEVELOPMENT = settings.APP_ENV in DEVELOPMENT_ENVIRONMENTS

@asynccontextmanager
async def lifespan(_: FastAPI):
    settings.validate_whatsapp()
    if not IS_DEVELOPMENT:
        settings.validate_production()
    import logging
    logging.getLogger(__name__).info("Yield serving basis: NISR database observations")
    yield


app = FastAPI(
    title="Agri-Menya API",
    description="Decision and Planning Support System for agricultural productivity in Rwanda.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs" if IS_DEVELOPMENT else None,
    redoc_url="/redoc" if IS_DEVELOPMENT else None,
    openapi_url="/openapi.json" if IS_DEVELOPMENT else None,
)

if not IS_DEVELOPMENT:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Role"],
)

app.include_router(decision.router)
app.include_router(planification.router)
app.include_router(segmentation.router)
app.include_router(communication.router)
app.include_router(whatsapp_admin.router)
app.include_router(webhooks.router)
app.include_router(chat.router)
app.include_router(alignment.router)
app.include_router(admin.router)
app.include_router(admin_auth.router)
app.include_router(community.router)
app.include_router(live_data.router)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    if not IS_DEVELOPMENT:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


# Configure logging early and mount debug router in non-production
LOG_PATH = configure_logging()
import logging
logging.getLogger(__name__).info("Application starting up, logs -> %s", LOG_PATH)
if IS_DEVELOPMENT:
    from app.routers import debug

    app.include_router(debug.router)


@app.get("/health")
def health_check():
    database_status = "unavailable"
    try:
        from app.core.supabase_client import get_supabase

        sb = get_supabase()
        sb.table("zones").select("id").limit(1).execute()
        database_status = "ok"
        has_baseline_rows = bool(sb.table("agri_metrics").select("id").limit(1).execute().data)
        try:
            has_baseline_rows = has_baseline_rows or bool(
                sb.table("nisr_yield_records").select("id").limit(1).execute().data
            )
        except Exception:
            # Migration 0007 is optional until the NISR import workflow is enabled.
            pass
    except Exception:
        logging.getLogger(__name__).exception("Health check database probe failed")
        has_baseline_rows = False

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "env": settings.APP_ENV,
        "database_status": database_status,
        "model_present": False,
        "model_version": None,
        "baselines_present": has_baseline_rows,
        "yield_source": "database observations" if has_baseline_rows else "unavailable",
        "baselines_overall_average": None,
    }


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness_check():
    from fastapi import HTTPException
    state = health_check()
    if state["database_status"] != "ok" or not state["baselines_present"]:
        raise HTTPException(status_code=503, detail={"status": "not_ready", **state})
    return {"status": "ready", **state}


@app.get("/")
def root():
    return {
        "message": "Agri-Menya API is running.",
        "docs": "/docs" if IS_DEVELOPMENT else None,
        "health": "/health",
    }

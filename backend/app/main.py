from contextlib import asynccontextmanager
from pathlib import Path

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
    logging.getLogger(__name__).info("Yield serving basis: database observations with official SAS historical fallback")
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

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
            "error": True,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": jsonable_encoder(exc.errors()),
            "status_code": 422,
            "error": True,
            "message": "Validation error in request payload or parameters.",
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger(__name__).exception("Unhandled exception processing %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred.",
            "status_code": 500,
            "error": True,
        },
    )


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
    return {"status": "alive"}


@app.get("/health/live")
def liveness_check():
    return {"status": "alive"}


def _system_health_status() -> dict:
    database_status = "unavailable"
    bundled_baseline = Path(__file__).resolve().parent.parent / "data" / "nisr_official_yields_2022_2026.csv"
    has_baseline_rows = bundled_baseline.is_file() and bundled_baseline.stat().st_size > 0
    try:
        from app.core.supabase_client import get_supabase

        sb = get_supabase()
        sb.table("zones").select("id").limit(1).execute()
        database_status = "ok"
        has_baseline_rows = has_baseline_rows or bool(sb.table("agri_metrics").select("id").limit(1).execute().data)
        try:
            has_baseline_rows = has_baseline_rows or bool(
                sb.table("nisr_yield_records").select("id").limit(1).execute().data
            )
        except Exception:
            # Migration 0007 is optional until the NISR import workflow is enabled.
            pass
    except Exception:
        logging.getLogger(__name__).exception("Health check database probe failed")
        pass

    return {
        "status": "ok" if database_status == "ok" else "degraded",
        "env": settings.APP_ENV,
        "database_status": database_status,
        "model_present": False,
        "model_version": None,
        "baselines_present": has_baseline_rows,
        "yield_source": ("database observations with official NISR SAS historical fallback"
                         if database_status == "ok" and has_baseline_rows else
                         "official NISR SAS historical fallback; database unavailable"
                         if has_baseline_rows else "unavailable"),
        "baselines_overall_average": None,
    }


@app.get("/health/status")
def system_health_status():
    return _system_health_status()


@app.get("/health/deep")
def deep_health_check():
    import psycopg

    if not settings.SUPABASE_DB_URL:
        logging.getLogger(__name__).warning("Deep health database probe is not configured")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "unreachable"},
        )

    try:
        with psycopg.connect(
            settings.SUPABASE_DB_URL,
            connect_timeout=5,
            options="-c statement_timeout=5000",
        ) as connection:
            connection.execute("SELECT 1").fetchone()
    except psycopg.Error as exc:
        logging.getLogger(__name__).warning(
            "Deep health database probe failed: %s", type(exc).__name__
        )
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "database": "unreachable"},
        )
    return {"status": "healthy", "database": "reachable"}


@app.get("/health/ready")
def readiness_check():
    from fastapi import HTTPException
    state = _system_health_status()
    if state["database_status"] != "ok" or not state["baselines_present"]:
        raise HTTPException(status_code=503, detail={"status": "not_ready", **state})
    return {**state, "status": "ready"}


@app.get("/")
def root():
    return {
        "message": "Agri-Menya API is running.",
        "docs": "/docs" if IS_DEVELOPMENT else None,
        "health": "/health",
    }

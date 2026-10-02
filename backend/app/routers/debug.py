from fastapi import APIRouter, HTTPException
from pathlib import Path
from app.core.config import settings

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/logs")
def tail_logs(lines: int = 200):
    if settings.APP_ENV == "production":
        raise HTTPException(status_code=403, detail="Logs endpoint disabled in production")

    # Resolve to backend/logs/app.log (same base used by app.core.logging)
    log_path = Path(__file__).resolve().parents[2] / "logs" / "app.log"
    if not log_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    # Read the last N lines
    with log_path.open("r", encoding="utf-8", errors="ignore") as f:
        content = f.read().splitlines()

    return {"path": str(log_path), "lines": content[-lines:]}

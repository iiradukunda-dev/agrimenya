import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Request


AUDIT_LOG_PATH = Path(__file__).resolve().parents[2] / "logs" / "admin_audit.log"
AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger("admin.audit")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(AUDIT_LOG_PATH)
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)


def audit_admin_action(action: str, resource: str, payload: dict, request: Request | None = None):
    """Record admin actions in a dedicated audit log.

    This keeps sensitive admin mutations traceable without exposing secret
    values to the application logs.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "resource": resource,
        "payload": payload,
        "client": request.client.host if request and request.client else None,
    }
    logger.info(json.dumps(entry, default=str))

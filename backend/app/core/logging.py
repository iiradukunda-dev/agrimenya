import logging
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


def configure_logging(level: int = logging.INFO) -> Path:
    """Configure root logging with a rotating file handler and console.

    Returns the Path to the log file used so callers (endpoints) can read it.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # Log directory at repo/backend/logs
    LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOG_DIR / "app.log"

    # Rotating file handler
    fh = RotatingFileHandler(str(log_path), maxBytes=5 * 1024 * 1024, backupCount=3)
    fh.setLevel(level)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    fh.setFormatter(fmt)
    root.addHandler(fh)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    return log_path

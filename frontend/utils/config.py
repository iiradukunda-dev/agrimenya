import os

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USER_API_KEY = os.getenv("USER_API_KEY", "")
DEMO_MODE = os.getenv("AGRI_MENYA_DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}

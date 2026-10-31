import os

from dotenv import load_dotenv

load_dotenv()

# BACKEND_URL is the deployment contract; retain API_BASE_URL/API_HOST for local compatibility.
api_host = os.getenv("API_HOST")
if os.getenv("BACKEND_URL"):
    API_BASE_URL = os.getenv("BACKEND_URL", "").rstrip("/")
elif os.getenv("API_BASE_URL"):
    API_BASE_URL = os.getenv("API_BASE_URL", "").rstrip("/")
elif api_host:
    if not api_host.startswith("http://") and not api_host.startswith("https://"):
        api_host = f"https://{api_host}"
    API_BASE_URL = api_host.rstrip("/")
else:
    API_BASE_URL = "http://localhost:8000"

USER_API_KEY = os.getenv("USER_API_KEY", "")
USE_MOCK_DATA = False # Set to False when backend is ready

import os

from dotenv import load_dotenv

load_dotenv()

# Check explicit API_BASE_URL or BACKEND_URL first, then fallback to API_HOST (provided by Render)
api_host = os.getenv("API_HOST")
if api_host and not os.getenv("API_BASE_URL") and not os.getenv("BACKEND_URL"):
    if not api_host.startswith("http://") and not api_host.startswith("https://"):
        api_host = f"https://{api_host}"
    API_BASE_URL = api_host
else:
    API_BASE_URL = os.getenv("API_BASE_URL") or os.getenv("BACKEND_URL") or "http://localhost:8000"

USER_API_KEY = os.getenv("USER_API_KEY", "")
USE_MOCK_DATA = False # Set to False when backend is ready

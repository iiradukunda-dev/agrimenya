import os

from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
USER_API_KEY = os.getenv("USER_API_KEY", "")
USE_MOCK_DATA = False # Set to False when backend is ready

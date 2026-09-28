from pathlib import Path
from dotenv import load_dotenv
import os
import httpx

# Load .env from backend folder
env_path = Path(__file__).resolve().parents[1] / ".env"
if env_path.exists():
    load_dotenv(env_path)

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Missing SUPABASE_URL or SUPABASE_KEY in .env')
    raise SystemExit(1)

try:
    headers = {'apikey': SUPABASE_KEY, 'Authorization': f'Bearer {SUPABASE_KEY}'}
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/zones?select=id"
    print('Requesting', url)
    r = httpx.get(url, headers=headers, timeout=20)
    print('Status:', r.status_code)
    print('Body (first 1000 chars):')
    print(r.text[:1000])
except Exception as e:
    print('Exception during request:')
    import traceback
    traceback.print_exc()

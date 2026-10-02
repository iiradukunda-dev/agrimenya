"""
Single shared Supabase client. Import `get_supabase()` wherever you need
to query the database instead of creating new clients everywhere.
"""
from functools import lru_cache

from supabase import Client, create_client

from app.core.config import settings


@lru_cache
def get_supabase() -> Client:
    settings.validate()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

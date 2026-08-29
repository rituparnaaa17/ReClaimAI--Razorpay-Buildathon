"""
Supabase client — singleton pattern with service role key for backend operations.
"""
from supabase import create_client, Client
from app.config import get_settings
from functools import lru_cache

settings = get_settings()


@lru_cache()
def get_supabase() -> Client:
    """Returns a Supabase client using the service role key (full access)."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_anon() -> Client:
    """Returns a Supabase client using the anon key (respects RLS)."""
    return create_client(settings.supabase_url, settings.supabase_anon_key)

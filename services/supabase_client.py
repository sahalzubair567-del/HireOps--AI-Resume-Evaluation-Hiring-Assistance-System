from typing import Optional

import httpx
from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions

from config import SUPABASE_KEY, SUPABASE_URL


def _init_client() -> Client:
  if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
      "SUPABASE_URL and SUPABASE_KEY must be set in the .env file before using the database."
    )
  # Use longer timeout for stability
  options = ClientOptions(postgrest_client_timeout=120, storage_client_timeout=120)
  return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)


supabase: Optional[Client] = None

try:
  supabase = _init_client()
except Exception as exc:
  # Fail fast with a clear error when the app actually tries to use Supabase.
  # This keeps local development predictable if env vars are missing.
  raise RuntimeError(f"Failed to initialize Supabase client: {exc}") from exc


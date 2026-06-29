import os

from dotenv import load_dotenv

load_dotenv()

FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-me")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MAX_RESUMES_PER_UPLOAD = 20
ALLOWED_EXTENSIONS = {"pdf", "docx"}
GPT_MODEL = "gpt-4.1-nano"


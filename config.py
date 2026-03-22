import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
DATABASE_URL = os.getenv("DATABASE")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not TOKEN:
    raise ValueError("TOKEN не найден в .env файле")

if not DATABASE_URL:
    raise ValueError("DATABASE не найден в .env файле")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY не найден в .env файле")

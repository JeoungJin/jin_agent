"""환경설정 (.env). 코드에 값을 직접 쓰지 않고 이 모듈에서 읽는다."""
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# CORS: React(5173), SpringBoot(8000)
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:8000",
]

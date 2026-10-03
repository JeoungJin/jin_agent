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

# SpringBoot 내부 API (계좌조회 Tool 이 서버 간 호출). 하드코딩하지 않고 여기서만 읽는다.
SPRING_API_BASE_URL = os.getenv("SPRING_API_BASE_URL", "http://localhost:8000")
SPRING_API_TIMEOUT = float(os.getenv("SPRING_API_TIMEOUT", "5"))   # Spring 게이트웨이 타임아웃(10초)보다 짧게

# yfinance 시세 조회
STOCK_CACHE_TTL = float(os.getenv("STOCK_CACHE_TTL", "60"))         # 초
STOCK_FETCH_TIMEOUT = float(os.getenv("STOCK_FETCH_TIMEOUT", "5"))  # 초 (9종목 병렬 조회 전체 대기)

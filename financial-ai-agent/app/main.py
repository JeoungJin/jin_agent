from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import config
from app.routers import chat, route
from app.services.llm_service import LLMUnavailableError

app = FastAPI(title="금융 AI Agent API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(route.router)


@app.exception_handler(LLMUnavailableError)
async def llm_unavailable_handler(_: Request, exc: LLMUnavailableError):
    """get_llm_client 의존성에서 키가 없을 때 등: 일반 JSON 에러(503)로 응답한다."""
    return JSONResponse(status_code=503, content={"detail": "AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요."})


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

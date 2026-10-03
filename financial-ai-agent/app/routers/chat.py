"""POST /api/v1/chat : 일반 대화 (분류 없이 LLM 에 그대로 질문)."""
from fastapi import APIRouter, Depends, HTTPException

from app.schemas import AnswerResponse, QuestionRequest
from app.services.llm_service import LLMUnavailableError, ask_llm, get_llm_client

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=AnswerResponse, summary="일반 대화")
def chat(req: QuestionRequest, client=Depends(get_llm_client)) -> AnswerResponse:
    try:
        answer = ask_llm(req.question, client)
    except LLMUnavailableError:
        raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.")
    return AnswerResponse(question=req.question, answer=answer, category="GENERAL")

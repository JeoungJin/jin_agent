"""POST /api/v1/route : 질문 분류 + Tool 실행 (Tool 이 필요 없으면 LLM)."""
from fastapi import APIRouter, Depends, HTTPException

from app.schemas import AnswerResponse, QuestionRequest
from app.services.llm_service import LLMUnavailableError, get_llm_client
from app.services.route_service import answer_by_route

router = APIRouter(prefix="/api/v1", tags=["route"])


@router.post("/route", response_model=AnswerResponse, summary="질문 분류 + Tool 실행")
def route(req: QuestionRequest, client=Depends(get_llm_client)) -> AnswerResponse:
    try:
        category, answer = answer_by_route(req.question, client)
    except LLMUnavailableError:
        raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.")
    return AnswerResponse(question=req.question, answer=answer, category=category)

from fastapi import APIRouter

from app.schemas import AnswerResponse, QuestionRequest
from app.services.route_service import route_question

router = APIRouter(prefix="/api/v1", tags=["chat"])


@router.post("/chat", response_model=AnswerResponse)
def chat(req: QuestionRequest) -> AnswerResponse:
    """질문을 분류(stock/account/general)해 Tool 또는 LLM으로 처리한다."""
    return route_question(req.question)

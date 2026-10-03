"""POST /api/v1/route : 질문 분류 + Tool 실행 (Tool 이 필요 없으면 LLM)."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import AnswerResponse, QuestionRequest
from app.services.llm_service import LLMUnavailableError, get_llm_client
from app.services.route_service import answer_by_route

router = APIRouter(prefix="/api/v1", tags=["route"])

# Swagger 의 Authorize 버튼. 토큰은 선택 입력이다 (계좌조회 질문에서만 필요).
bearer = HTTPBearer(auto_error=False)


@router.post("/route", response_model=AnswerResponse, summary="질문 분류 + Tool 실행")
def route(
    req: QuestionRequest,
    client=Depends(get_llm_client),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
) -> AnswerResponse:
    try:
        access_token = credentials.credentials if credentials else None
        category, answer = answer_by_route(req.question, req.user_id, access_token, client)
    except LLMUnavailableError:
        raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.")
    return AnswerResponse(question=req.question, answer=answer, category=category)

"""POST /api/v1/route : 질문 분류 + Tool 실행 — SSE(text/event-stream) 스트리밍 응답.

이벤트 약속 (프론트엔드와 동일, 이름 변경 금지)
  category : 질문 분류 직후, 맨 처음 1번   {"question": "...", "category": "..."}
  token    : 답변 조각마다 (여러 번)       {"text": "..."}
  done     : 정상 종료 시 마지막 1번       {}
  error    : 스트림 시작 후 오류           {"message": "..."}   (이 경우 done 은 보내지 않는다)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.schemas import QuestionRequest
from app.services.llm_service import LLMUnavailableError, ensure_llm_ready, get_llm_client
from app.services.question_classifier import route_question
from app.services.route_service import TOOL_CATEGORIES, stream_by_route
from app.services.sse import sse

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["route"])

# Swagger 의 Authorize 버튼. 토큰은 선택 입력이다 (계좌조회 질문에서만 필요).
bearer = HTTPBearer(auto_error=False)

SSE_HEADERS = {
    "Cache-Control": "no-cache",       # 중간 캐시가 응답을 모아두지 않게 함
    "X-Accel-Buffering": "no",         # Nginx 등 프록시가 버퍼링하지 않게 함 (버퍼링되면 스트리밍 효과가 사라진다)
}

ERROR_MESSAGE = "답변을 생성하는 중 문제가 발생했습니다. 잠시 후 다시 시도해주세요."


def event_stream(question, user_id, access_token, client):
    try:
        for event, data in stream_by_route(question, user_id, access_token, client):
            yield sse(event, data)
        yield sse("done", {})
    except Exception:
        # 이미 200 OK 를 보낸 뒤라 상태코드를 바꿀 수 없다 → error 이벤트로 알리고 종료한다.
        log.exception("스트리밍 도중 오류")          # 상세 예외는 로그에만 남기고 응답에는 넣지 않는다
        yield sse("error", {"message": ERROR_MESSAGE})


@router.post("/route", summary="질문 분류 + Tool 실행 (SSE 스트리밍)")
def route(
    req: QuestionRequest,
    client=Depends(get_llm_client),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    # 시작 전 오류(요청 검증 실패는 422, API 키 없음은 503)는 일반 JSON 에러 응답으로 알린다.
    if route_question(req.question) not in TOOL_CATEGORIES:
        try:
            ensure_llm_ready(client)
        except LLMUnavailableError:
            raise HTTPException(status_code=503, detail="AI 서비스를 사용할 수 없습니다. 잠시 후 다시 시도해주세요.")

    access_token = credentials.credentials if credentials else None
    return StreamingResponse(
        event_stream(req.question, req.user_id, access_token, client),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )

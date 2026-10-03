# 금융 AI 에이전트 (React → Spring Boot → FastAPI)

```
[React :5173] --POST /api/ai/route--> [Spring Boot :8000] --WebClient--> [FastAPI :9000] --> Tool 또는 LLM
   (axios, 한 번에 응답)               POST /api/v1/chat 호출               (분류 후 처리, AnswerResponse)
                                       (검증, 3초 타임아웃, fallback)
```

현재 단계(2일차)는 일반 JSON(Mono) 응답입니다. SSE 스트리밍(Flux)은 3일차에 추가합니다.


| 디렉터리 | 역할 | 핵심 파일 |
|---|---|---|
| `fastapi-agent/` | 질문 분류 후 Tool/LLM 처리(`/api/v1/chat`). 에이전트 루프는 `/api/v1/agent/*` | `routers/chat.py`, `services/route_service.py`, `tools.py` |
| `spring-gateway/` | 브라우저와 AI 사이의 관문. 입력 검증, FastAPI 호출(Mono), 장애 시 fallback | `AiGatewayService.java`, `AiRouteController.java` |
| `react-ui/` | axios로 한 번에 응답을 받아 표시하는 채팅 UI | `ChatPanel.tsx`, `api.ts` |

## 실행 (터미널 3개)

```bash
# 1) FastAPI  (Python 3.11+)
cd fastapi-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 9000          # Swagger: http://localhost:9000/docs

# 2) Spring Boot  (JDK 17+)
cd spring-gateway && gradle bootRun

# 3) React  (Node 18+)
cd react-ui && npm install && npm run dev  # http://localhost:5173
```

`OPENAI_API_KEY`를 환경변수로 주면 OpenAI(`gpt-4o-mini`)를, 비워 두면 키 없이 동작하는 `MockLLM`을 씁니다.

## 테스트

```bash
cd fastapi-agent && pytest          # /api/v1/chat 분류·검증, 에이전트 루프
cd spring-gateway && gradle test    # MockWebServer로 FastAPI를 흉내내 프록시/fallback 검증
cd react-ui && npm test             # axios 호출 모듈
```

## 에이전트 동작 원리 (수업 포인트)

1. 사용자 메시지 + 세션 기록을 LLM에 전달
2. LLM이 `tool_calls`를 반환하면 → 서버가 tool 실행 → 결과를 `role: tool`로 기록에 추가 → 다시 LLM 호출
3. tool 호출이 없으면 최종 답변. `MAX_STEPS`로 무한 루프 방지
4. 각 단계는 SSE 이벤트(`tool_call` → `tool_result` → `token` → `done`)로 React에 전달

## 확장 과제

- ★☆☆ 새 Tool 추가: `get_exchange_rate` (`tools.py`의 REGISTRY와 TOOL_SCHEMAS 두 곳 수정)
- ★★☆ 세션 메모리를 인메모리 dict → Redis로 교체 / Spring에서 JWT의 고객 ID를 `customer_id`로 전달
- ★★★ RAG: 금융 상품 약관을 ChromaDB에 넣고 `search_product_docs` Tool 추가

# 금융 AI 에이전트 (React → Spring Boot → FastAPI)

```
[React :5173] --POST /api/chat/stream--> [Spring Boot :8080] --WebClient--> [FastAPI :8000] --> LLM + Tools
   (SSE 렌더링)                          (게이트웨이, CORS, 검증, fallback)   (에이전트 루프, 세션 메모리)
```

| 디렉터리 | 역할 | 핵심 파일 |
|---|---|---|
| `fastapi-agent/` | 에이전트 본체. LLM이 Tool을 고르고 결과를 받아 답변하는 루프 | `services/agent.py`, `tools.py`, `services/llm.py` |
| `spring-gateway/` | 브라우저와 AI 사이의 관문. 입력 검증, FastAPI 호출, 장애 시 fallback | `AiGatewayService.java` |
| `react-ui/` | 스트리밍 채팅 UI (tool 호출 흔적 표시) | `ChatPanel.tsx`, `sse.ts` |

## 실행 (터미널 3개)

```bash
# 1) FastAPI  (Python 3.11+)
cd fastapi-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --port 8000          # Swagger: http://localhost:8000/docs

# 2) Spring Boot  (JDK 17+)
cd spring-gateway && gradle bootRun

# 3) React  (Node 18+)
cd react-ui && npm install && npm run dev  # http://localhost:5173
```

`OPENAI_API_KEY`를 환경변수로 주면 OpenAI(`gpt-4o-mini`)를, 비워 두면 키 없이 동작하는 `MockLLM`을 씁니다.

## 테스트

```bash
cd fastapi-agent && pytest          # 에이전트 루프, tool, SSE 이벤트 순서
cd spring-gateway && gradle test    # MockWebServer로 FastAPI를 흉내내 프록시/fallback 검증
cd react-ui && npm test             # SSE 파서
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

# 금융 AI 에이전트 (React → Spring Boot → FastAPI)

3일 교육 과정(Day1~Day3 교안)을 순서대로 구현한 예제입니다. 교안 검증 결과는 [docs/교안-검증-리포트.md](docs/교안-검증-리포트.md) 를 보세요.

```
[React :5173] --POST /api/ai/route (SSE)--> [Spring Boot :8000] --WebClient Flux--> [FastAPI :9000] --> Tool / OpenAI / yfinance
  fetch+ReadableStream                       JWT HttpOnly 쿠키, 검증, fallback          category → token… → done | error
  GET /api/ai/portfolio  --------------->    중계(Mono)  ------------------------->   GET /api/v1/portfolio
```

| 디렉터리 | 내용 |
|---|---|
| `financial-ai-agent/day1/` | Day1 터미널 Assistant (router, 더미 Tool, 테스트 20개) |
| `financial-ai-agent/app/` | FastAPI: `/api/v1/chat`(LLM), `/api/v1/route`(SSE), `/api/v1/portfolio`, Tool(stock·exchange·account) |
| `spring-gateway/` | Spring Boot: JWT 쿠키 인증, AiGatewayService(SSE 중계·fallback), 계좌 내부 API, 포트폴리오 프록시 |
| `react-ui/` | React+TS+Vite+Tailwind v4: 로그인, 스트리밍 채팅(AiChatPanel), Recharts 대시보드 |
| `docs/` | 개념 그림과 Vibe Coding 문구 |

## 실행 (터미널 3개)
```bash
# 1) FastAPI (Python 3.11+)
cd financial-ai-agent && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY=sk-...          # Tool 질문(잔액·주가·환율)은 키 없이도 동작
uvicorn app.main:app --port 9000      # Swagger: http://localhost:9000/docs

# 2) Spring Boot (JDK 17+)
cd spring-gateway && gradle bootRun    # http://localhost:8000

# 3) React (Node 20+)
cd react-ui && npm install && npm run dev   # http://localhost:5173  (이메일 아무거나 입력해 로그인)
```

## 테스트
```bash
cd financial-ai-agent && pytest                    # 53개 (day1 은 day1/ 에서 별도 실행: 20개)
cd spring-gateway && gradle test                   # 31개
cd react-ui && npm test                            # 5개
```

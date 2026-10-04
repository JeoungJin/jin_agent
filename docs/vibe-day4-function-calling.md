# Day4 Vibe Coding — Function Calling 에이전트 (FastAPI)

> 도구: VSCode + Copilot (FastAPI 프로젝트만 수정). Spring · React 는 변경 없음.
> 원칙: 한 번에 만들지 않는다. **① 비스트리밍(/route) → ② 스트리밍(/route-stream)** 순서로 두 번에 나눠 바이브한다.

---

## ① Function Calling 루프 (비스트리밍, POST /api/v1/route)

```
[범위] 이 프로젝트(FastAPI)만 수정합니다. SpringBoot, React 코드는 만들지 않습니다.
(호출자는 SpringBoot 하나입니다. 요청/응답 형식은 아래 [계약]을 그대로 유지합니다.)

[계약 (변경 금지)]
- POST /api/v1/route   요청 { question, user_id? }  헤더 Authorization: Bearer <JWT> (선택)
                       응답 { question, category, answer }
- POST /api/v1/route-stream  (이번 단계에서는 수정하지 않는다)
- Spring 내부 API: GET /internal/api/accounts/{userId}/balance (기존 account_tool 이 이미 호출)

[FastAPI] 규칙 기반 Router 대신, LLM 이 Tool 을 고르는 Function Calling 방식으로 /api/v1/route 를 바꿔 주세요.

1. Tool 정의 (src/app/tools/registry.py 한 곳에 모은다)
   - get_stock_price(name: str)        기존 stock_tool.get_stock_price 재사용
   - get_per(name: str)                신규. yfinance Ticker.info 의 trailingPE. 값이 없으면 "PER 정보를 확인할 수 없습니다"
   - get_exchange_rate(currency: str)  기존 exchange_tool 재사용
   - get_account_balance()             인자 없음. user_id 와 토큰은 LLM 이 아니라 서버(요청)에서 주입
   - 각 Tool 은 OpenAI tools 형식(type=function, name, description, parameters=JSON Schema)으로 정의
   - description 에 "언제 이 Tool 을 쓰는지"를 한국어로 분명히 적는다 (모호하면 LLM 이 잘못 고른다)
   - Tool 실행 함수는 기존 규칙대로 예외를 던지지 않고 한국어 문자열을 반환

2. 실행 루프 (service/agent_service.py)
   - messages = [system, user]. system: "금융 도우미. 시세·환율·잔액은 반드시 Tool 로 조회하고 추측하지 않는다.
     투자 권유는 하지 않는다. 한국어로 간결히 답한다."
   - 반복 (최대 MAX_TOOL_ROUNDS 회, config 값, 기본 3):
       1) LLM 호출 (tools 전달, tool_choice="auto")
       2) 응답에 tool_calls 가 없으면 그 content 가 최종 답변 → 종료
       3) 있으면 각 호출의 arguments(JSON 문자열)를 json.loads 로 파싱해 Tool 실행
          · 여러 개면 병렬 실행 (기존 ThreadPoolExecutor 방식), 실행 시간 제한은 config
          · 알 수 없는 Tool 이름 / JSON 파싱 실패 / 필수 인자 누락 → 예외 대신 오류 문자열을 결과로 사용
       4) messages 에 assistant(tool_calls) 와, 호출마다 {role:"tool", tool_call_id, content} 를 추가하고 다음 반복
   - 최대 횟수에 도달하면 "요청을 처리하지 못했습니다" 안내 문구를 answer 로 반환
   - 사용자 id 는 서버가 주입한다: get_account_balance 실행 시 요청의 user_id/토큰을 사용, LLM 이 만든 인자는 쓰지 않는다

3. 응답 category
   - 호출된 Tool 이 없으면 "GENERAL", 있으면 "AGENT" (고정값, 프론트 배지용)

4. 기존 코드
   - question_classifier / route_service 는 삭제하지 말고 남겨 둔다 (/route-stream 이 아직 사용)
   - OpenAI 모델·키·타임아웃은 config.py 값 사용 (하드코딩 금지)

5. 테스트 (OpenAI 는 모킹, 네트워크 호출 없음)
   - 복합 질문 "삼성전자 주가와 PER을 함께 알려줘" → get_stock_price 와 get_per 가 모두 실행되고 answer 반환
   - Tool 이 필요 없는 질문 → tool_calls 없이 바로 답변
   - 잘못된 arguments JSON → 오류 문자열이 tool 결과로 전달되고 서버가 죽지 않음
   - 최대 반복 횟수 초과 → 안내 문구
   - 계좌 Tool: LLM 이 user_id 인자를 만들어도 무시하고 요청의 user_id 사용

[확인 (Swagger)]
- "삼성전자 주가와 PER을 함께 알려줘" → 두 값이 모두 들어간 답변
- "달러 환율과 내 잔액 알려줘" → 환율 + 잔액 (user_id, Authorize 토큰 필요)
- "예금과 적금의 차이" → Tool 없이 답변, category=GENERAL
```

---

## ② 스트리밍 + `tool` 이벤트 (POST /api/v1/route-stream)

```
[범위] 이 프로젝트(FastAPI)만 수정합니다. 이전 단계의 agent_service(Tool 정의·실행 함수)를 재사용합니다.

[계약 (기존 이벤트는 이름·형식 변경 금지)]
event: category {question, category} → [event: tool {name, status}]* → event: token {text}* → event: done {}
오류: event: error {message} 1개 후 종료 (done 없음)
- 새 이벤트 tool: status 는 "start" | "done". 프론트는 알 수 없는 이벤트를 무시하므로 하위 호환.

[FastAPI] /api/v1/route-stream 을 Function Calling 으로 바꾸고 SSE 로 내보내 주세요.

1. 흐름 (제너레이터에서 yield)
   - 시작: category 이벤트 (category 는 "AGENT" 고정)
   - 반복 (최대 MAX_TOOL_ROUNDS):
       · LLM 을 stream=True 로 호출
       · delta.content 가 오면 즉시 token 이벤트로 yield
       · delta.tool_calls 는 index 별로 name 과 arguments 조각을 이어 붙여 모은다
         (arguments 는 JSON 문자열 조각이라 스트림이 끝난 뒤에 한 번에 json.loads 한다)
       · 스트림이 끝났을 때 tool_calls 가 없으면 → done 이벤트 후 종료
       · 있으면 호출마다 tool {name, status:"start"} yield → 병렬 실행 → tool {name, status:"done"} yield
         → messages 에 assistant(tool_calls) + role:"tool" 결과를 추가하고 다음 반복
   - 최대 횟수 초과 시 안내 문구를 token 으로 보내고 done

2. 오류 규칙 (기존과 동일)
   - 스트림 시작 전 확인 가능한 오류(API 키 없음 등)는 일반 HTTP 에러
   - 시작 후 예외는 logger.exception 으로 로그만 남기고 error 이벤트(고정 문구) 1개 후 종료, done 은 보내지 않는다
   - Tool 하나가 실패하면 실패 문자열을 tool 결과로 LLM 에 전달해 나머지로 답하게 한다

3. 응답 헤더·SSE 포맷은 기존 sse_event 함수와 동일 (Cache-Control: no-cache, X-Accel-Buffering: no)

4. 테스트 (OpenAI 스트림은 가짜 chunk 로 모킹)
   - tool_calls 의 arguments 가 여러 chunk 로 쪼개져 와도 정상 파싱
   - 이벤트 순서: category → tool(start)… → tool(done)… → token… → done
   - Tool 호출이 없으면 tool 이벤트 없이 category → token… → done
   - 도중 예외 → error 이벤트로 끝나고 done 이 없음

[확인 (curl -N)]
curl -N -X POST http://localhost:9000/api/v1/route-stream -H "Content-Type: application/json" \
  -d '{"question":"삼성전자 주가와 PER을 함께 알려줘"}'
- tool start/done 이벤트가 먼저 오고, 그 뒤 token 이 조금씩 도착한다
```

---

## ③ (선택) React 에서 tool 이벤트 표시

```
[범위] React 프로젝트만 수정합니다. 백엔드 계약은 변경하지 않습니다.
- SSE 이벤트 tool {name, status} 를 처리한다: start → "○○ 조회 중…" 칩 표시, done → 칩을 완료 표시로 변경
- Tool 이름은 화면용 한국어로 매핑 (get_stock_price → 주가, get_per → PER, get_exchange_rate → 환율, get_account_balance → 잔액)
- token 이 오기 시작하면 칩은 흐리게 유지, done/error 에서 정리
- 기존 category/token/done/error 처리는 그대로 둔다
```

## 확인 체크리스트

- ☐ 복합 질문에서 규칙 기반 Router가 못 하던 "주가 + PER"이 한 답변에 나온다
- ☐ Tool이 필요 없는 질문은 Tool 호출 없이 답한다
- ☐ 스트리밍에서 `tool` 이벤트 → `token` 순서로 도착한다
- ☐ `user_id`를 LLM이 정하지 못한다 (다른 id를 요청해도 본인 계좌만 조회)
- ☐ 최대 반복 횟수와 타임아웃이 설정값으로 동작한다

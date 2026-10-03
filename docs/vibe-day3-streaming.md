# 3일차 스트리밍(SSE) — Vibe Coding 문구 (HttpOnly 쿠키 인증 전제)

관련 그림: `streaming-compare.png` · `streaming-flow.png` · `streaming-events-errors.png` · `streaming-consistency.png`
선행 문구: `vibe-day2-jwt-cookie.md` (JWT 쿠키 인증), `vibe-day2-account-tool.md` (계좌조회 Tool)

구현 순서: ① FastAPI → ② Spring → ③ React

## 세 문구가 공유하는 약속 (일관성 점검표)

그림: `streaming-consistency.png`
**이벤트 이름과 시점은 `streaming-events-errors.png`의 ④ 이벤트 종류(프론트엔드와의 약속) 표가 기준이며, 그대로 사용한다.**

| 항목 | 약속 내용 | 적용되는 곳 |
|---|---|---|
| FastAPI 스트리밍 엔드포인트 | `POST /api/v1/route` (SSE). `/api/v1/chat`은 JSON 응답 그대로 유지 | FastAPI · Spring |
| Spring 엔드포인트 | `POST /api/ai/route` (`text/event-stream`) | Spring · React |
| 이벤트 이름 · 시점 | ④ 표 그대로: `category` · `token` · `done` · `error` (`tool_call` · `tool_result`는 이번에 미사용) | FastAPI · Spring · React |
| 이벤트 data 형식 | category `{question, category}` / token `{text}` / done `{}` / error `{message}` | FastAPI · React |
| 종료 규칙 | 정상: `done` / 오류: `error` 후 종료 (`done`은 보내지 않음). `done`/`error` 없이 끝나도 로딩 해제 | FastAPI · Spring · React |
| 브라우저 ↔ Spring 인증 | HttpOnly 쿠키 자동 전송 (`fetch`는 `credentials: "include"`, Authorization 헤더 불필요) | Spring · React |
| Spring → FastAPI 인증 | `Authorization: Bearer <토큰 원문>` + body에 `user_id` | Spring · FastAPI |
| `user_id` 출처 | 서버가 로그인 사용자로 결정. React는 `user_id`를 보내지 않음 (body는 `question`만) | Spring · React |
| 응답 헤더 | `Cache-Control: no-cache`, `X-Accel-Buffering: no` (프록시 버퍼링 방지) | FastAPI · Spring |
| Spring Security | `ASYNC` · `ERROR` 디스패치 `permitAll` (SSE 비동기 재디스패치 오류 방지) | Spring |
| 스트림 시작 전 오류 | 일반 HTTP 에러 응답 (400 · 401 · 422). 4xx는 fallback 없이 상태코드 그대로 전파 | Spring · React |

---

## ① FastAPI

```text
FastAPI에 실제 SSE 스트리밍 엔드포인트 POST /api/v1/route를 구현해 주세요.
/api/v1/chat은 JSON 응답 그대로 유지하고 건드리지 마세요.

[1. 응답 방식]
- StreamingResponse + media_type="text/event-stream"
- 응답 헤더: Cache-Control: no-cache, X-Accel-Buffering: no
- SSE 한 건의 형식: "event: <이름>\ndata: <JSON>\n\n"
- data는 문자열을 직접 이어 붙이지 말고 json.dumps(..., ensure_ascii=False)로 직렬화

[2. 이벤트 약속 (프론트엔드와 동일하게 사용, 이름 변경 금지)]
| 이벤트   | 시점                          | data                                  |
| category | 질문 분류 직후, 맨 처음 1번   | {"question": "...", "category": "..."} |
| token    | 답변 조각마다 (여러 번)       | {"text": "청크 내용"}                  |
| done     | 정상 종료 시 마지막 1번       | {}                                    |
| error    | 스트림 시작 후 오류 발생 시   | {"message": "사용자용 안내 문구"}      |
- 정상 순서: category → token(여러 번) → done
- 오류 시: error를 보내고 스트림 종료 (done은 보내지 않음)
- tool_call / tool_result는 이번에 사용하지 않음 (선택 이벤트)

[3. 입력]
- 요청 스키마는 기존 그대로 유지하되, 2일차 계좌조회와 같이 body의 user_id와
  Authorization: Bearer 토큰(Swagger Authorize, 선택 입력)을 받는다

[4. 답변 생성]
- 일반(LLM) 질문: OpenAI stream=True로 생성되는 텍스트 청크를 즉시 token으로 전달
  (답변을 모아서 한 번에 보내지 않음)
  · delta.content가 None이거나 choices가 비어 있는 chunk는 건너뜀
- STOCK / EXCHANGE / ACCOUNT Tool: 기존 동기 방식 유지,
  결과 문자열 전체를 token 이벤트 1개로 전송
  (ACCOUNT는 user_id와 토큰을 account_tool에 그대로 전달)

[5. 오류 처리]
- 스트림 시작 전 오류(요청 검증 실패 등): 기존 관례대로 일반 HTTP 에러 응답
- 시작 후 오류(OpenAI 장애, 타임아웃, Tool 예외): error 이벤트로 전송 후 종료
- 내부 예외 상세와 스택트레이스는 응답에 넣지 않고 로그에만 기록

[6. 유지할 것]
- 기존 분류 로직(분류 결과값 그대로 사용), 요청 스키마, CORS 설정, 오류 처리 관례

[7. 확인 (curl -N)]
- 일반 질문 → category, token 여러 개, done
- Tool 질문 → category, token 1개, done
- OpenAI 오류 → error 후 종료
- /api/v1/chat 응답은 변경 없음
```

---

## ② Spring

```text
어제 만든 AiGatewayService를 SSE 스트리밍 중계용으로 바꿔 주세요.

[1. FastAPI 호출]
- WebClient로 POST http://localhost:9000/api/v1/route 호출 (base URL 설정은 기존 그대로)
- 요청 body는 { question, user_id }, 헤더는 Authorization: Bearer <토큰>
  (2일차와 동일: user_id는 로그인 사용자 ID, 토큰은 필터가 보관한 원문)
- 요청에 Accept: text/event-stream 지정
- 응답은 .bodyToFlux(new ParameterizedTypeReference<ServerSentEvent<String>>() {})로
  Flux<ServerSentEvent<String>>으로 수신
- collectList(), block(), Mono 변환 금지

[2. 중계 방식]
- 수신한 이벤트를 모으지 않고, 받는 즉시 React로 그대로 전달
- event 이름과 data는 수정하지 않는다 (category / token / done / error)

[3. 타임아웃]
- application.yml의 기존 설정값과 키를 그대로 사용
- Flux에서는 "이벤트 사이 최대 대기시간"으로 적용 (.timeout(Duration))

[4. 실패 처리]
- FastAPI 4xx: fallback하지 않고 상태코드 그대로 전파 (기존 규칙 유지)
- 연결 거부 · 타임아웃 · FastAPI 5xx · 스트림 도중 오류:
  · log.warn으로 예외 타입, 메시지, question 기록
  · fallback으로 event: error, data {"message": "현재 AI 서비스가 원활하지 않습니다. 잠시 후 다시 시도해주세요"} 1개를 전송하고 종료 (done은 보내지 않음)

[5. Controller]
- POST /api/ai/route를 produces = MediaType.TEXT_EVENT_STREAM_VALUE로 변경
- 기존 @Valid 입력 검증(빈 질문 400)은 유지, 요청 body는 { question }만 받는다
- Controller와 Service의 반환 타입을 Flux<ServerSentEvent<String>>으로 통일
- 응답 헤더 Cache-Control: no-cache, X-Accel-Buffering: no 설정

[6. Spring Security]
- SecurityConfig에 ASYNC · ERROR 디스패치 타입 permitAll 추가
  (SSE는 비동기 응답이라 재디스패치에서 인증이 다시 검사되어 오류가 날 수 있음)
- 쿠키 인증과 resolveToken 동작은 그대로 유지

[7. 확인 (curl -N -b cookies.txt)]
- 정상: category → token 여러 개 → done이 순서대로 도착
- 쿠키 없음: 401
- FastAPI 중지: error 이벤트 1개 후 종료
- FastAPI 4xx: fallback 없이 같은 상태코드
- 빈 질문: 400
```

---

## ③ React (새 앱)

```text
React + TypeScript + Vite로 AI 채팅 앱을 새로 만들어 주세요. (핵심 컴포넌트: AiChatPanel.tsx)

[1. 프로젝트 구성]
- Vite + React + TypeScript, axios
- Tailwind CSS v4: @tailwindcss/vite 플러그인, tailwind.config.js 없음, index.css에 @import "tailwindcss";
- vite.config.ts 개발용 프록시: /api → http://localhost:8000 (SpringBoot)
  (프록시를 거치면 같은 출처로 요청되어 쿠키가 그대로 오가고 CORS 설정이 필요 없음)

[2. 파일 구성]
- src/api/httpClient.ts   axios 인스턴스 (withCredentials: true) + 401 응답 인터셉터
- src/api/authApi.ts      login(email), logout(), fetchMe()
- src/lib/parseSse.ts     SSE 파서 (순수 함수)
- src/components/LoginForm.tsx, AiChatPanel.tsx
- src/App.tsx             로그인 상태에 따라 LoginForm / AiChatPanel 전환

[3. 로그인 · 인증 상태]
- 토큰은 서버가 HttpOnly 쿠키로 관리한다. JS에서 읽거나 저장하지 않는다. (localStorage 사용 금지)
- POST /api/auth/login, 요청 LoginRequest { email: string }, 응답 LoginResponse { id: number, email: string }
- 앱 시작 시 GET /api/ai/me로 로그인 상태 확인 (확인 중에는 로딩 표시)
  · 200 → 채팅 화면, 401 → 로그인 폼
- 로그인 성공 → 채팅 화면 / 로그아웃 버튼 → POST /api/auth/logout 후 로그인 폼
- axios 응답 인터셉터: 401을 받으면 로그인 화면으로 전환

[4. 스트리밍 요청]
- fetch로 POST /api/ai/route, body { "question": string } (user_id는 보내지 않는다. 서버가 결정),
  credentials: "include", 헤더 Content-Type: application/json, Accept: text/event-stream
  (fetch는 axios 인터셉터를 타지 않지만, 쿠키는 브라우저가 자동으로 보냄. Authorization 헤더 불필요)
- 먼저 res.ok 확인: 401 → 로그인 화면 전환, 400 → 응답의 message 표시
- res.body.getReader() + TextDecoder({ stream: true })로 읽기
- AbortController: 컴포넌트 언마운트 시 취소 (선택: 중지 버튼)

[5. SSE 파서 (parseSse)]
- 표준 SSE: "event: 이름\ndata: JSON\n\n", 이벤트는 빈 줄로 구분 (\r\n은 \n으로 정규화)
- 청크 경계에서 이벤트가 잘려도 미완성 부분은 버퍼에 남겼다가 다음 청크와 이어 붙임
- 완성된 이벤트만 { event, data }로 반환하고 data는 JSON.parse
- 순수 함수로 분리하고 vitest로 테스트 (잘린 청크, \r\n, 한 청크에 여러 이벤트)

[6. 이벤트 처리 (백엔드와의 약속, 이름 변경 금지)]
- category: 분류 배지 표시 (data: { question, category })
- token:    assistant 메시지 뒤에 data.text를 도착 즉시 이어 붙임
- done:     로딩 종료, 입력창 활성화
- error:    data.message를 오류로 표시하고 로딩 종료 (이 경우 done은 오지 않음)
- 알 수 없는 이벤트는 무시, 스트림이 done/error 없이 끝나도 로딩 해제 (finally)

[7. UI]
- 메시지 목록 useState (role: "user" | "assistant"), 로딩 인디케이터
- 입력창 + 전송 버튼, Enter(Shift 없이)로 전송
  · 한글 입력 중 Enter 방지: e.nativeEvent.isComposing이면 전송하지 않음
- 응답 중에는 입력과 전송 비활성화, 새 메시지가 오면 맨 아래로 스크롤
```

---

## 면접 대비 보충 (쿠키 방식 기준)

- 왜 `EventSource` 대신 `fetch`인가: `EventSource`는 **GET만** 지원해 질문 본문을 POST로 보낼 수 없다.
  (쿠키 방식에서는 인증 헤더 때문이 아니라 이 이유가 핵심)
- 왜 React가 `user_id`를 보내지 않는가: 클라이언트가 보낸 값은 조작될 수 있으므로,
  서버가 토큰의 사용자로 결정하고 계좌 접근 시 토큰 사용자와 `userId`를 다시 대조한다 (403).

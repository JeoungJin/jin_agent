# Day5 Vibe Coding — 멀티턴 대화 (맥락을 기억하는 챗봇)

> 설계: **대화 기록은 Spring 이 보관**하고, FastAPI 는 요청마다 받은 `history` 로만 일한다(무상태). React 는 `conversationId` 만 보낸다.
> 진행 순서: ① FastAPI (history 받기) → ② Spring (기록 보관·전달) → ③ React (conversationId·새 대화).
> 도구: FastAPI·React = VSCode + Copilot, Spring = IntelliJ + Claude. 각 문구는 **자기 프로젝트만** 수정한다.

## 계약 (세 문구 공통, 변경 금지)

| 구간 | 요청 | 비고 |
|---|---|---|
| React → Spring | `POST /api/ai/route`, `POST /api/ai/route-stream` 본문 `{ question, conversationId? }` | `conversationId` 는 UUID 문자열, 생략하면 이전처럼 **기억 없는 단발 질문** |
| (선택) React → Spring | `DELETE /api/ai/conversations/{conversationId}` → 204 | "새 대화" 시 서버 기록 삭제 |
| Spring → FastAPI | `POST /api/v1/route`, `/api/v1/route-stream` 본문 `{ question, user_id, history }` | `history` = `[{ role: "user" \| "assistant", content }]`, **현재 질문 제외**, 생략 시 `[]` |
| 응답 | 기존과 동일 (JSON `{question, category, answer}` / SSE `category, tool, token, done, error`) | 변경 없음 |

---

## ① FastAPI (VSCode + Copilot)

```
[범위] 이 프로젝트(FastAPI)만 수정합니다. SpringBoot, React 코드는 만들지 않습니다.
(호출자는 SpringBoot 하나입니다. 대화 기록 보관은 Spring 의 일이며, FastAPI 는 기록을 저장하지 않습니다.)

[계약 (변경 금지)]
- POST /api/v1/route, POST /api/v1/route-stream
  요청 { question, user_id?, history? }  history = [{ role: "user" | "assistant", content: string }]
  history 는 "이번 질문 이전"의 대화이며 생략하면 빈 목록
- 응답 형식과 SSE 이벤트(category, tool, token, done, error)는 그대로 유지

[FastAPI] 이전 대화(history)를 LLM 에 함께 전달해 맥락을 이해하도록 바꿔 주세요.

1. 스키마 (schemas)
   - RouteRequest 에 history: list[HistoryMessage] = [] 추가
   - HistoryMessage { role: Literal["user","assistant"], content: str(최대 4000자) }
   - history 최대 개수는 config 의 MAX_HISTORY_MESSAGES(기본 20). 초과·잘못된 role("system" 등)은 422
   - 기존 요청(history 없음)은 그대로 동작해야 한다

2. 메시지 구성 (agent_service 의 messages 만드는 곳 한 군데)
   - messages = [system] + history + [{role:"user", content: 현재 질문}]
   - /route, /route-stream 둘 다 같은 함수를 사용 (복붙 금지)
   - Tool 호출 중간 과정(tool_calls, role:"tool")은 이번 요청 안에서만 쓰고 history 로 되돌려 주지 않는다

3. system 프롬프트에 추가
   - "이전 대화를 참고해 '그럼', '아까 그 종목' 같은 표현을 해석한다."
   - "이전 대화에 나온 시세·잔액·환율은 오래됐을 수 있으니, 숫자가 필요하면 도구로 다시 조회한다."

4. 테스트 (OpenAI 는 모킹)
   - history 가 있으면 LLM 호출 messages 순서가 [system, ...history, 현재 질문] 이다
   - history 없이 호출해도 기존 테스트가 모두 통과한다
   - role "system" 을 history 에 넣으면 422, 개수 초과 422
   - 스트리밍과 JSON 모두 같은 messages 로 호출한다

[확인 (Swagger)]
- history 없이: "그럼 PER은?" → 어떤 종목인지 되묻는 답변
- history [{"role":"user","content":"삼성전자 주가 알려줘"},{"role":"assistant","content":"삼성전자 현재가 71,000원입니다."}]
  + "그럼 PER은?" → 삼성전자의 PER 로 답변 (get_per("삼성전자") 호출)
```

---

## ② Spring (IntelliJ + Claude)

```
[범위] 이 프로젝트(SpringBoot)만 수정합니다. FastAPI, React 코드는 만들지 않습니다.

[계약 (변경 금지)]
- React → Spring: POST /api/ai/route, /api/ai/route-stream 본문 { question, conversationId? }
- Spring → FastAPI: 본문 { question, user_id, history }  history = [{ role: "user"|"assistant", content }] (현재 질문 제외)
- 응답 형식은 변경 없음

[SpringBoot] 대화 기록을 보관하고 FastAPI 호출 시 history 로 전달해 주세요.

1. 요청 DTO
   - AiRouteRequest 에 conversationId (선택) 추가. 값이 있으면 UUID 형식 검증, 틀리면 400 { status, message }
   - conversationId 가 없으면 기억 없이 기존 방식 그대로 동작 (저장하지 않음)

2. ConversationStore (@Component, 인메모리)
   - key = userId + ":" + conversationId  (userId 는 JWT 에서 온 값. 요청 본문의 값은 신뢰하지 않는다)
   - 값: 메시지 목록 (role, content) 과 마지막 사용 시각
   - 메서드: history(userId, conversationId) → 최근 N개 복사본, append(userId, conversationId, question, answer), delete(...)
   - 설정은 application.yml (하드코딩 금지):
     conversation.max-messages: 10 (최근 N개만 유지, 오래된 것부터 삭제),
     conversation.ttl: 30m (유휴 시간이 지나면 만료), conversation.max-per-user: 20, conversation.max-chars: 4000
   - 스레드 안전 (ConcurrentHashMap + 대화별 동기화), 만료 정리는 주기 작업 또는 접근 시 정리

3. AiGatewayService
   - FastAPI 요청에 history 포함 (FastApiRouteRequest 에 history 필드 추가, 없으면 빈 목록)
   - /api/ai/route (Mono): FastAPI 가 정상 응답했을 때만 질문+answer 저장. fallback 응답과 오류는 저장하지 않는다
   - /api/ai/route-stream (Flux): token 이벤트의 text 를 모아 두었다가 done 이벤트를 받았을 때만 저장.
     error 이벤트, 연결 오류, 타임아웃, 클라이언트 취소 시에는 저장하지 않는다 (user/assistant 가 항상 짝을 이루게)
   - 이벤트는 모으지 않고 즉시 중계하는 기존 방식 유지 (collectList, block 금지)

4. 삭제 API
   - DELETE /api/ai/conversations/{conversationId} → 본인 대화만 삭제, 204 (없어도 204)

5. 테스트 (MockWebServer 사용)
   - 같은 conversationId 로 두 번째 요청을 보내면 FastAPI 요청 본문의 history 에 첫 번째 질문·답변이 들어 있다
   - 다른 사용자가 같은 conversationId 를 써도 history 가 비어 있다
   - max-messages 를 넘으면 오래된 메시지부터 잘린다
   - FastAPI 5xx / fallback / 스트림 error 에서는 저장되지 않는다
   - 스트림이 done 으로 끝나면 token 을 합친 답변이 저장된다
   - conversationId 가 UUID 가 아니면 400, 없으면 history 는 빈 목록

[확인 (curl)]
- 같은 conversationId 로 "삼성전자 주가 알려줘" → "그럼 PER은?" (JSON 과 스트리밍 모두) → 두 번째 답변이 삼성전자 PER
- 다른 계정으로 같은 conversationId → 기억 없음
- Spring 재시작 후 같은 conversationId → 기억 없음 (메모리 저장의 한계)
```

---

## ③ React (VSCode + Copilot)

```
[범위] 이 프로젝트(React)만 수정합니다. 백엔드 계약은 변경하지 않습니다.

[계약 (변경 금지)]
- POST /api/ai/route, /api/ai/route-stream 본문에 { question, conversationId } 를 보낸다 (user_id 는 보내지 않는다)
- (선택) DELETE /api/ai/conversations/{conversationId} → 204

[React] 이전 대화를 기억하는 채팅으로 바꿔 주세요.

1. conversationId
   - AiChatPanel 이 conversationId 상태를 가진다. 초기값 crypto.randomUUID()
   - JSON 요청(aiApi.routeQuestion)과 스트리밍 요청(fetch) 모두 본문에 conversationId 를 포함한다
   - localStorage/sessionStorage 에 저장하지 않는다 (새로고침하면 새 대화)

2. 새 대화
   - 헤더에 "새 대화" 버튼. 응답 중에는 비활성화
   - 클릭 시: 화면 messages 비우기, conversationId 를 새 UUID 로 교체,
     이전 conversationId 는 DELETE /api/ai/conversations/{id} 로 지우기 (실패해도 화면에는 영향 없음)

3. UI
   - 스트리밍 체크박스를 바꿔도 같은 conversationId 를 사용해 맥락이 이어진다
   - 입력창 위나 헤더에 작은 문구 "이전 대화를 기억하며 답변합니다"
   - 기존 규칙(401 처리, isComposing, 중지 버튼, 언마운트 취소)은 그대로 유지

[확인 (브라우저)]
- "삼성전자 주가 알려줘" → "그럼 PER은?" → 삼성전자 PER 로 답한다 (스트리밍 ON/OFF 모두)
- 두 질문 사이에 스트리밍 체크박스를 바꿔도 이어진다
- "새 대화" 후 "그럼 PER은?" → 어떤 종목인지 되묻는다
- 개발자도구 Network 에서 요청 본문에 conversationId 가 있고 user_id 는 없다
- 새로고침하면 새 대화로 시작한다
```

---

## 통합 확인 체크리스트

- ☐ "그럼", "아까 그 종목" 같은 표현이 이전 대화를 참고해 해석된다
- ☐ JSON 모드와 스트리밍 모드가 같은 대화 기록을 공유한다
- ☐ "새 대화"를 누르면 맥락이 사라진다
- ☐ 다른 사용자는 내 대화에 접근할 수 없다 (같은 conversationId 를 써도)
- ☐ 오류가 난 턴은 기록에 남지 않는다
- ☐ 대화가 길어지면 오래된 메시지부터 잘린다 (최근 N개)
- ☐ 서버를 재시작하면 기억이 사라진다 → 영구 저장(Redis·DB)이 필요한 이유 이해

## 면접 질문

- LLM 은 이전 대화를 기억하나요? 멀티턴 챗봇은 어떻게 구현하나요?
- 대화 기록을 클라이언트가 보내게 하지 않고 서버가 보관하는 이유는?
- 대화가 길어지면 어떤 문제가 생기고, 어떻게 해결하나요?
- 메모리에 저장한 대화 기록의 한계는 무엇이고 어떻게 개선하나요?

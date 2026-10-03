# 2일차 계좌조회 Tool 연결 — Vibe Coding 문구 (HttpOnly 쿠키 인증 전제)

관련 그림: `account-tool-flow.png` (호출 흐름), `account-tool-rules.png` (분류 규칙 · 실패 메시지)
선행 문구: `vibe-day2-jwt-cookie.md` (JWT 쿠키 인증)

```text
[SpringBoot] 인증된 사용자의 계좌 잔액을 반환하는 내부 API를 만들어 주세요.
- GET /internal/api/accounts/{userId}/balance
- 테스트용 인메모리 잔액 (예: userId 1 → 3,250,000원)
- 응답: {"userId": 1, "balance": 3250000}
- 존재하지 않는 userId는 404
- JWT 인증 필요 (/internal/** 도 authenticated)
  · 이 API는 FastAPI가 서버 간 호출하므로 Authorization: Bearer 헤더로 받는다
    (JwtAuthenticationFilter의 resolveToken이 쿠키가 없으면 Bearer 헤더를 읽음)
  · 토큰의 사용자 ID와 userId가 다르면 403

[SpringBoot] 게이트웨이 연결
- AiGatewayService가 FastAPI 호출 시
  · 로그인 사용자 ID를 body의 user_id로 전달
  · 필터가 Authentication의 credentials에 보관한 토큰 원문을 Authorization: Bearer 헤더로 전달
    (브라우저 쿠키를 그대로 넘기지 않는다. 서버 간 호출은 Bearer 헤더 사용)

[FastAPI] SpringBoot 내부 API를 호출하는 계좌조회 기능을 추가해 주세요.

1. 질문 분류 (question_classifier — ACCOUNT를 가장 먼저 검사)
   - "잔액" / "잔고" 포함 → ACCOUNT
   - "계좌" / "통장" + ("얼마" / "조회" / "확인" / "남았" / "있어") → ACCOUNT
   - "계좌 개설" 같은 지식 질문 → GENERAL
     ("개설" 등이 포함되면 위 두 번째 규칙에서 제외)

2. 입력
   - user_id: 질문 문장이 아니라 요청 본문의 user_id 필드
   - 토큰: Swagger Authorize(HTTPBearer, 선택 입력)

3. 호출 흐름
   router → route_service.answer_by_route(question, user_id, access_token)
          → account_tool.get_account_balance(user_id, access_token)

4. account_tool 규칙
   - httpx로 GET 요청, 토큰이 있으면 Authorization: Bearer 헤더 추가
   - 예외를 던지지 않고 항상 한국어 문자열 반환
   - 실패 케이스별 안내 문구 포함:
     잘못된 user_id(호출 전 검증), 연결 실패, 타임아웃, 404, 401, 403, 5xx, 그 외 예외

5. 설정 (config.py)
   - SPRING_API_BASE_URL (기본 http://localhost:8000), SPRING_API_TIMEOUT 사용
   - 하드코딩 금지
   - 타임아웃은 Spring 게이트웨이 타임아웃(10초)보다 짧게 (예: 5초)

[확인]
- "내 잔액 알려줘" → ACCOUNT, "계좌 개설하는 방법 알려줘" → GENERAL
- Spring 중지 / 토큰 없음(401) / 타인 userId(403) / 없는 userId(404) 각각 한국어 안내 문구 반환
- 로그인 쿠키로 /api/ai/route 호출 시 계좌 잔액 문장이 반환
```

## 쿠키 방식 전환으로 바뀐 점 (이전 버전 대비)
- 브라우저 ↔ Spring: 토큰이 `Authorization` 헤더에서 HttpOnly 쿠키로 바뀜
- Spring → FastAPI → Spring(내부 API): **변경 없음** (Bearer 헤더 유지). FastAPI 코드와 문구는 그대로
- Spring 게이트웨이가 쿠키에서 꺼낸 토큰을 Bearer 헤더로 변환해 전달하는 단계가 추가됨
- 내부 API는 쿠키가 없는 서버 간 호출이므로, 필터의 Bearer 대체 경로(`resolveToken`)를 막으면 계좌조회가 동작하지 않음

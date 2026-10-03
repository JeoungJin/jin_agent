# 2일차 Spring JWT 인증 — Vibe Coding 문구 (HttpOnly 쿠키 방식)

관련 그림: `jwt-components.png` (구조·구성요소), `jwt-flow.png` (인증 처리 흐름)

```text
이 Spring Boot 프로젝트(Spring MVC + WebClient, 아직 스트리밍 아님)에 JWT 인증을 적용해 주세요.
토큰은 HttpOnly 쿠키로 주고받습니다. (응답 본문에는 토큰을 담지 않음)

[전제]
- Servlet 기반(spring-boot-starter-web) 유지. WebClient는 FastAPI 호출용으로만 사용하므로 별도 전환 없음

[1. 의존성]
- spring-boot-starter-security
- jjwt 0.12.6: jjwt-api(implementation), jjwt-impl · jjwt-jackson(runtimeOnly)

[2. 설정 (application.yml)]
- jwt.secret: ${JWT_SECRET:기본값}      ← Base64, 디코딩 후 32바이트 이상
- jwt.expiration-ms: 3600000             ← 1시간
- jwt.cookie-name: access_token
- jwt.cookie-secure: ${JWT_COOKIE_SECURE:false}   ← 로컬(http)은 false, 운영(https)은 true

[3. security 패키지]
- AuthUser: record (Long id, String email)
- JwtTokenProvider: createToken / validateToken / getAuthUser
- AuthCookieFactory: ResponseCookie로 발급 쿠키와 삭제 쿠키 생성
  · 속성: HttpOnly, Secure(설정값), SameSite=Lax, Path=/, Max-Age=토큰 만료시간(초)
  · 삭제 쿠키: 같은 속성에 Max-Age=0
- JwtAuthenticationFilter: OncePerRequestFilter
  · 토큰 추출은 resolveToken(request) 메서드 하나로 분리
    (① jwt.cookie-name 쿠키 → ② 없으면 Authorization: Bearer, curl · Swagger 테스트용)
  · 검증 성공 시 SecurityContextHolder에 AuthUser 설정
    (토큰 원문은 이후 FastAPI 전달에 쓸 수 있도록 Authentication의 credentials에 보관)
  · @Component로 등록하지 않기 (필터 중복 실행 방지)

[4. SecurityConfig]
- CSRF · formLogin · httpBasic 비활성화, 세션 STATELESS
  (쿠키 인증이므로 CSRF는 SameSite=Lax + JSON 요청으로 방어)
- 인증 실패 시 401 반환
- PUBLIC_URLS(로그인 · 로그아웃 · 회원가입 · Swagger · /error)는 permitAll
- /api/ai/** 는 authenticated
- JwtAuthenticationFilter는 addFilterBefore로 등록
- CORS: 프론트가 프록시로 호출하면 불필요. 직접 호출 시 allowedOrigins를 명시하고(* 금지) allowCredentials(true)
- (SSE용 ASYNC/ERROR 디스패치 permitAll은 3일차 스트리밍 때 추가)

[5. 인증 API (테스트용)]
- POST /api/auth/login: 이메일만 받아 인메모리로 ID 부여 후, 토큰을 Set-Cookie(HttpOnly)로 발급
  · 응답 본문은 { "id": ..., "email": ... } (토큰 미포함)
- POST /api/auth/logout: 삭제 쿠키(Max-Age=0)를 내려줌

[6. 컨트롤러]
- POST /api/ai/route: @AuthenticationPrincipal로 로그인 사용자를 로깅
- GET /api/ai/me: SecurityContextHolder에서 사용자 반환
  (프론트가 로그인 여부 확인에 사용: 200이면 로그인 상태, 401이면 로그아웃 상태)

[7. 확인 (서버 실행 후 curl)]
① 쿠키 없이 /api/ai/me 호출 → 401
② curl -c cookies.txt 로 로그인 → 응답 헤더 Set-Cookie에 HttpOnly; SameSite=Lax 확인, 본문에 토큰 없음
③ curl -b cookies.txt 로 /api/ai/me, /api/ai/route 호출 → 200
④ 로그아웃 후 같은 쿠키로 다시 호출 → 401
⑤ (선택) 쿠키 대신 Authorization: Bearer 헤더로도 200이 나오는지 확인
```

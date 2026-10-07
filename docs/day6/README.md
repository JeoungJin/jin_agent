# Day 6 교육생 자료

| 파일 | 설명 |
|---|---|
| `Day6_AI_Agent(Student).docx` | Day 2~5와 같은 형식의 교육생 자료 (LangGraph StateGraph 전환 + 미션 4 자율형 실습). 시간 표시 없음, 프롬프트는 `[범위]·[계약]·요구사항` 구조 |
| `images/` | 새로 만든 그림 7장 (`d6-01~07`, SVG + PNG). 원본에는 그림이 없었음 |
| `build/` | 문서·그림 생성 스크립트 |

## 원본 대비 추가·정리한 부분
- **미션 4 (실습, 신규)**: plan → execute → reflect 순환과 재계획 상한. 읽기 전용 Tool만 자동 실행, 계획 5단계·재계획 2회·전체 노드 수·시간 상한.
- 원본의 시간표 제거, 짧은 요청문을 `[범위]·[계약]·번호 항목` 프롬프트로 정리.
- 그래프는 새 패키지 `app/graph/`에 만들고 CLI로 확인하며, 기존 `/route`·`/route-stream`은 수정하지 않는 것으로 범위를 명시(원본에는 API 연결 여부 언급 없음).
- 미션 3의 Kill Switch는 Day 5의 판정 로직을 재사용하고 `State.steps` 기반 그래프 실행 횟수 조건을 추가. `recursion_limit`은 최후 보루로 설명.
- 참고 박스: 규칙 기반 `route_question`과 Function Calling이 공존하는 이유, `draw_mermaid_png()`의 외부 서비스 의존.

## 보유 종목 API 반영 (미션 4)
- 미션 4의 "보유 종목 조회"는 Spring에 읽기 전용 내부 API(`GET /internal/api/accounts/{userId}/holdings`)를 추가하는 7-1절(IntelliJ)과, FastAPI의 `get_holdings` Tool·비중 계산(코드)·코드 기반 누락 점검을 만드는 7-2절(VS Code)로 구성. 개인 데이터는 Spring을 거치고 FastAPI는 DB에 직접 붙지 않음.

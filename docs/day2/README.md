# Day 2 교육생 자료

| 파일 | 설명 |
|---|---|
| `Day2_교육생자료.docx` | Day 1 4시간판과 같은 형식의 교육생 자료. 시간 표시 없음, 프롬프트는 `[범위]·[계약]·[요구사항]` 구조로 정리, 개념 설명은 모두 본문에 포함 |
| `images/` | 이미지 (PNG, SVG). `d2-r*` = 기존 Day 2 문서의 그림, `d2-01~09` = 새로 추가한 그림 |
| `build/` | 문서·이미지 생성 스크립트 |

기존 그림 `webclient-flow`는 `.block()` 표기가 4-1 프롬프트(Mono 그대로 반환)와 맞지 않아 `d2-r3-webclient-mono-flux`로 고쳐 다시 그렸다 (경로 `/api/v1/route`, DTO `AiRouteResponse`로도 통일).

## 버전 중립 표기
- Spring Boot 3.x(`starter-web` + `starter-webflux`)와 4.x(`starter-webmvc` + `starter-webclient`)의 스타터 이름이 달라, 프롬프트의 `[전제]`·의존성 문구를 버전 중립으로 고침. 9절에 "Agent의 Tool은 DB가 아니라 API 경계에 붙는다" 개념 박스 추가.

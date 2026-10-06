# Day 5 교육생 자료

| 파일 | 설명 |
|---|---|
| `Day5_AI_Agent(Student).docx` | Day 2~4와 같은 형식의 교육생 자료 (RAG · Kill Switch · PII 마스킹). 시간 표시 없음, 프롬프트는 `[범위]·[계약]·[요구사항]` 구조로 정리 |
| `images/` | `d5-r1~r5`: 원본 문서의 그림 5장(수정 없이 유지), `d5-01~05`: 새로 추가한 그림 5장 (SVG + PNG) |
| `build/` | 문서·그림 생성 스크립트 (`build_day5.py`, `img_b7.py`, `docx_lib.py`, `img_lib2.py`, `shot.mjs`) |

## 원본 대비 추가·정리한 부분
- **4-4 Kill Switch 구현 프롬프트(신규)**: 원본은 버그를 만들고 되돌리기까지만 있고 구현 프롬프트가 없었음. 라운드·시간·반복 감지 3상한으로 작성.
- 원본 학습목표·흐름의 "환각 검증 로직" 항목은 해당 프롬프트가 없어 제외.
- 그림 5장 추가: sources 경로, Kill Switch, StreamMasker, PII 검사 순서, Day 6 예고(미션 4 자율형 순환 포함).
- 정리: 3-1 확인 항목 중복 제거, PII 출력 단계에 system 문구 통합, Spring 계약 문구 보완, 쿠키 파일명 `cookies.txt`로 통일, 로컬 경로(pytest) 일반화.

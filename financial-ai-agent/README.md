# 금융 AI Agent — Day 1 (financial-ai-agent)

AI 시대의 개발 방식 이해 + 첫 번째 금융 AI Assistant

## 해결하려는 문제
초보 투자자가 자연어로 금융 질문을 입력하면, 질문 종류에 따라 **Tool(정해진 데이터)** 또는 **LLM**이 답한다.
모든 질문을 LLM에 보내면 실시간 데이터가 필요한 질문에서 오래된 정보를 사실처럼 말할 위험(Hallucination)이 있다.

## 전체 구조
```
질문 → route_question() → STOCK             → stock_tool.get_stock_price()      (더미)
                        → EXCHANGE          → exchange_tool.get_exchange_rate() (더미)
                        → FINANCE_KNOWLEDGE → LLM(OpenAI)
                        → GENERAL           → LLM(OpenAI)
```
```
financial-ai-agent/
├── app.py                 # 터미널 대화 루프 + answer_question()
├── router.py              # route_question()
├── tools/stock_tool.py    # 더미 주가
├── tools/exchange_tool.py # 더미 환율
├── tests/                 # pytest (Router 10개 + Tool + 통합)
└── README.md
```

## 실행
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # OPENAI_API_KEY 입력
python app.py
pytest
```

## 질문 분류 기준
| 분류 | 키워드 예 |
|---|---|
| FINANCE_KNOWLEDGE | PER, PBR, ROE, DSR, EPS, BPS |
| EXCHANGE | 환율, 원화, 달러, 엔화, 유로, 위안 |
| STOCK | 주가, 종목, 가격, 주식, 시세, 종목명 |
| GENERAL | 나머지 |

여러 키워드가 동시에 있으면 **FINANCE_KNOWLEDGE > EXCHANGE > STOCK > GENERAL** 순으로 분류한다.

## Tool이 필요한 이유
주가·환율처럼 매번 바뀌는 값은 LLM이 "기억"하는 값이 아니라 Tool이 가져온 값이어야 한다. (오늘은 더미, Day2부터 실제 연동)

## 사용한 주요 Prompt
- 7절: "Python 3.10 환경에서 동작하는 간단한 금융 AI Assistant를 만들어줘 …"
- 9절: "Python으로 금융 질문 Router를 만들어줘 … 우선순위 FINANCE_KNOWLEDGE > EXCHANGE > STOCK > GENERAL …"
- 10절: "STOCK으로 분류된 질문에 답할 stock_tool.py를 만들어줘 …", "main.py의 대화 루프를 아래처럼 수정해줘 …"

## AI가 틀렸던 사례 (직접 실행해서 발견)
| 입력 | 실제 결과 | 문제 |
|---|---|---|
| `카카오뱅크 주가 알려줘` | 카카오 현재가 45,000원 | **부분 문자열 매칭** 때문에 다른 회사(카카오)로 오인 |
| `LG화학 얼마나 올랐어?` | GENERAL → LLM이 그럴듯하게 답함 | Tool에는 LG화학이 있는데 **Router 키워드에는 없음** (Router와 Tool의 종목 목록 불일치) |
| `삼성 전자 가격`, `SK hynix 주가` | 종목명을 알려주세요 | 띄어쓰기·영문 표기를 못 찾음 |
| `100달러는 원화로 얼마야?` | 1달러 = 1,380.0원 | 금액(100)을 무시하고 환율만 반환 |
| `삼성전자 얼마나 올랐어?` | 현재가만 반환 | "올랐다(등락)"에 답하지 못함 (Tool이 가격만 가짐) |
| `삼성전자 PER 알려줘` | PER의 일반 설명 | 우선순위 규칙상 FINANCE_KNOWLEDGE → 삼성전자의 PER이 아님 |

## 오늘 배운 AI 용어
LLM, Prompt, Context, Tool, Router, Hallucination, AI Coding, Vibe Coding

## 다음날 개선할 내용
- FastAPI 서버로 감싸기(Router/Service/Schema), 실제 외부 금융 데이터 연동
- 종목명 매핑을 한 곳에서 관리해 Router와 Tool의 불일치 제거

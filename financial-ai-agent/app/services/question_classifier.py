"""질문 분류 (Day1 router.py 의 route_question 을 서비스 계층으로 이전).

우선순위: ACCOUNT > FINANCE_KNOWLEDGE > EXCHANGE > STOCK > GENERAL
"""

FINANCE_KNOWLEDGE_KEYWORDS = ["per", "pbr", "roe", "dsr", "eps", "bps"]
EXCHANGE_KEYWORDS = ["환율", "원화", "달러", "엔화", "유로", "위안", "usd", "jpy", "eur"]
STOCK_KEYWORDS = ["주가", "종목", "가격", "주식", "시세", "삼성전자", "sk하이닉스", "naver", "네이버", "카카오", "현대차"]

ACCOUNT_BALANCE_WORDS = ["잔액", "잔고"]
ACCOUNT_NOUNS = ["계좌", "통장"]
ACCOUNT_QUERY_WORDS = ["얼마", "조회", "확인", "남았", "있어"]
ACCOUNT_KNOWLEDGE_WORDS = ["개설", "해지"]   # "계좌 개설" 같은 지식 질문은 ACCOUNT 가 아니라 GENERAL 로 둔다

_RULES = [
    ("FINANCE_KNOWLEDGE", FINANCE_KNOWLEDGE_KEYWORDS),
    ("EXCHANGE", EXCHANGE_KEYWORDS),
    ("STOCK", STOCK_KEYWORDS),
]


def _is_account_question(text: str) -> bool:
    if any(w in text for w in ACCOUNT_BALANCE_WORDS):
        return True
    return (
        any(n in text for n in ACCOUNT_NOUNS)
        and any(q in text for q in ACCOUNT_QUERY_WORDS)
        and not any(k in text for k in ACCOUNT_KNOWLEDGE_WORDS)
    )


def route_question(question: str) -> str:
    text = (question or "").lower()
    if _is_account_question(text):      # ACCOUNT 를 가장 먼저 검사한다
        return "ACCOUNT"
    for category, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "GENERAL"

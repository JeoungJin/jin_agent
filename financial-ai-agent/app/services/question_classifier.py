"""질문 분류 (Day1 router.py 의 route_question 을 서비스 계층으로 이전).

우선순위: FINANCE_KNOWLEDGE > EXCHANGE > STOCK > GENERAL
"""

FINANCE_KNOWLEDGE_KEYWORDS = ["per", "pbr", "roe", "dsr", "eps", "bps"]
EXCHANGE_KEYWORDS = ["환율", "원화", "달러", "엔화", "유로", "위안", "usd", "jpy", "eur"]
STOCK_KEYWORDS = ["주가", "종목", "가격", "주식", "시세", "삼성전자", "sk하이닉스", "naver", "네이버", "카카오", "현대차"]

_RULES = [
    ("FINANCE_KNOWLEDGE", FINANCE_KNOWLEDGE_KEYWORDS),
    ("EXCHANGE", EXCHANGE_KEYWORDS),
    ("STOCK", STOCK_KEYWORDS),
]


def route_question(question: str) -> str:
    text = (question or "").lower()
    for category, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "GENERAL"

"""금융 질문 Router - Day1 9절.

사용자의 질문을 STOCK / EXCHANGE / FINANCE_KNOWLEDGE / GENERAL 중 하나로 분류한다.
※ 키워드 몇 개로만 분류하는 학습용 단순 구현이다. 실제 서비스에서는 이것만으로 모든 질문을 정확히 분류할 수 없다.

한 문장에 여러 키워드가 동시에 있으면 우선순위: FINANCE_KNOWLEDGE > EXCHANGE > STOCK > GENERAL
"""

FINANCE_KNOWLEDGE_KEYWORDS = ["per", "pbr", "roe", "dsr", "eps", "bps"]
EXCHANGE_KEYWORDS = ["환율", "원화", "달러", "엔화", "유로", "위안", "usd", "jpy", "eur"]
STOCK_KEYWORDS = ["주가", "종목", "가격", "주식", "시세", "삼성전자", "sk하이닉스", "naver", "네이버", "카카오", "현대차"]

# 우선순위 순서대로 검사한다.
_RULES = [
    ("FINANCE_KNOWLEDGE", FINANCE_KNOWLEDGE_KEYWORDS),
    ("EXCHANGE", EXCHANGE_KEYWORDS),
    ("STOCK", STOCK_KEYWORDS),
]


def route_question(question: str) -> str:
    """질문을 분류해 'STOCK' | 'EXCHANGE' | 'FINANCE_KNOWLEDGE' | 'GENERAL' 중 하나를 반환한다."""
    text = (question or "").lower()
    for category, keywords in _RULES:
        if any(keyword in text for keyword in keywords):
            return category
    return "GENERAL"

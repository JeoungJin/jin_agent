"""STOCK 질문용 Tool (Day1: 더미 데이터 버전).

※ 아직 외부 API 연동 전이라 정해둔 값만 돌려준다. 실제 실시간 API 연동은 내일(Day2) FastAPI에서 진행할 예정이다.
"""

DUMMY_STOCK_PRICES = {
    "삼성전자": 71000,
    "SK하이닉스": 195000,
    "NAVER": 210000,
    "카카오": 45000,
    "현대차": 250000,
    "LG화학": 380000,
}

NOT_REGISTERED = "등록되지 않은 종목입니다"


def get_stock_price(name: str) -> str:
    """종목명으로 더미 가격 문장을 반환한다. 목록에 없으면 '등록되지 않은 종목입니다'."""
    price = DUMMY_STOCK_PRICES.get(name)
    if price is None:
        return NOT_REGISTERED
    return f"{name} 현재가는 {price:,}원입니다. (더미 데이터)"

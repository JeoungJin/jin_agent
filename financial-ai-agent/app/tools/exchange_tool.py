"""EXCHANGE 질문용 Tool (Day1: 더미 데이터 버전).

※ 고정된 환율만 돌려준다. 실제 환율 API 연동은 이후에 진행한다.
"""

DUMMY_EXCHANGE_RATES = {
    "달러": 1380.0,   # 1달러
    "엔화": 9.2,      # 1엔
    "유로": 1500.0,   # 1유로
    "위안": 190.0,    # 1위안
}

NOT_REGISTERED = "등록되지 않은 통화입니다"


def get_exchange_rate(currency: str) -> str:
    """통화명으로 더미 환율 문장을 반환한다. 목록에 없으면 '등록되지 않은 통화입니다'."""
    rate = DUMMY_EXCHANGE_RATES.get(currency)
    if rate is None:
        return NOT_REGISTERED
    return f"1{currency} = {rate:,.1f}원입니다. (더미 데이터)"

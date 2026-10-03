"""Day1 9절 Router 테스트 질문 10개."""
import pytest

from router import route_question


@pytest.mark.parametrize(
    "question, expected",
    [
        ("삼성전자 가격 알려줘", "STOCK"),
        ("SK하이닉스 주가가 궁금해", "STOCK"),
        ("100달러는 원화로 얼마야?", "EXCHANGE"),
        ("엔화 환율 알려줘", "EXCHANGE"),
        ("PER이 낮으면 좋은 거야?", "FINANCE_KNOWLEDGE"),
        ("PBR은 무엇인가?", "FINANCE_KNOWLEDGE"),
        ("안녕하세요", "GENERAL"),
        ("오늘 날씨 어때?", "GENERAL"),
        ("삼성전자 PER 알려줘", "FINANCE_KNOWLEDGE"),          # 우선순위: 종목 + 용어 → FINANCE_KNOWLEDGE
        ("삼성전자 주가와 PER을 함께 알려줘", "FINANCE_KNOWLEDGE"),
    ],
)
def test_route_question(question, expected):
    assert route_question(question) == expected


def test_empty_and_none_are_general():
    assert route_question("") == "GENERAL"
    assert route_question(None) == "GENERAL"

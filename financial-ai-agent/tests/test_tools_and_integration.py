"""Day1 10절: Tool 과 app.py 통합 검증."""
import app
from tools.exchange_tool import get_exchange_rate
from tools.stock_tool import get_stock_price
from tests.test_app_stage7 import FakeClient


def test_stock_tool_known_and_unknown():
    assert "71,000원" in get_stock_price("삼성전자")
    assert get_stock_price("없는회사") == "등록되지 않은 종목입니다"


def test_exchange_tool_known_and_unknown():
    assert "1,380.0원" in get_exchange_rate("달러")
    assert get_exchange_rate("페소") == "등록되지 않은 통화입니다"


def test_stock_question_uses_tool_not_llm():
    client = FakeClient()
    category, answer = app.answer_question("삼성전자 가격 알려줘", client)
    assert category == "STOCK" and "71,000원" in answer
    assert client.calls == []          # LLM 을 호출하지 않았다


def test_exchange_question_uses_tool_not_llm():
    client = FakeClient()
    category, answer = app.answer_question("엔화 환율 알려줘", client)
    assert category == "EXCHANGE" and "9.2" in answer and client.calls == []


def test_knowledge_and_general_go_to_llm():
    for q, cat in (("PER이 뭐야?", "FINANCE_KNOWLEDGE"), ("안녕하세요", "GENERAL")):
        client = FakeClient("LLM 답변")
        assert app.answer_question(q, client) == (cat, "LLM 답변")
        assert len(client.calls) == 1


def test_stock_question_without_known_name_asks_for_name():
    _, answer = app.answer_question("주가가 궁금해", FakeClient())
    assert "종목명" in answer

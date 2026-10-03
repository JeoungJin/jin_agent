import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.agent import reset_sessions
from app.tools import calculate_loan_payment

client = TestClient(app)


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    reset_sessions()


def test_balance_uses_tool():
    r = client.post("/api/v1/agent/chat", json={"message": "내 잔액 알려줘", "customer_id": "C002"}).json()
    assert r["steps"][0]["tool"] == "get_account_balance"
    assert "480,000원" in r["answer"]


def test_loan_calculation():
    r = client.post("/api/v1/agent/chat", json={"message": "1000만원 연 6%로 12개월 대출 이자"}).json()
    assert r["steps"][0]["tool"] == "calculate_loan_payment"
    assert r["steps"][0]["result"]["monthly_payment"] == calculate_loan_payment(10_000_000, 6, 12)["monthly_payment"]


def test_unknown_question_no_tool():
    r = client.post("/api/v1/agent/chat", json={"message": "안녕"}).json()
    assert r["steps"] == []


def test_stream_events_order():
    with client.stream("POST", "/api/v1/agent/chat/stream", json={"message": "거래내역"}) as resp:
        body = "".join(resp.iter_text())
    events = [l.split(": ")[1] for l in body.splitlines() if l.startswith("event:")]
    assert events[0] == "tool_call" and events[1] == "tool_result"
    assert "token" in events and events[-1] == "done"


def test_validation_rejects_empty_message():
    assert client.post("/api/v1/agent/chat", json={"message": ""}).status_code == 422

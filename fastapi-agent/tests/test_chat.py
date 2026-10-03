import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _mock_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def post(q):
    return client.post("/api/v1/chat", json={"question": q})


def test_stock_goes_to_tool():
    body = post("삼성전자 주가 알려줘").json()
    assert body["category"] == "stock"
    assert "71,000원" in body["answer"]
    assert body["question"] == "삼성전자 주가 알려줘"


def test_missing_stock_name_asks_instead_of_inventing():
    assert post("주가 알려줘").json()["answer"].startswith("종목명을")
    assert post("카카오 주가").json()["answer"].startswith("종목명을")


def test_account_goes_to_tool():
    body = post("내 잔액 알려줘").json()
    assert body["category"] == "account" and "3,250,000원" in body["answer"]


def test_general_goes_to_llm():
    assert post("예금과 적금의 차이가 뭐야?").json()["category"] == "general"


@pytest.mark.parametrize("payload", [{}, {"question": ""}, {"q": "x"}])
def test_invalid_request_is_422(payload):
    assert client.post("/api/v1/chat", json=payload).status_code == 422

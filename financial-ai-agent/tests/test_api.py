import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import get_llm_client
from tests.fakes import FakeClient

client = TestClient(app)


@pytest.fixture(autouse=True)
def fake_llm():
    fake = FakeClient("LLM 답변")
    app.dependency_overrides[get_llm_client] = lambda: fake
    yield fake
    app.dependency_overrides.clear()


def post(path, question):
    return client.post(path, json={"question": question})


@pytest.mark.parametrize(
    "q, category",
    [
        ("삼성전자 가격 알려줘", "STOCK"),
        ("SK하이닉스 주가가 궁금해", "STOCK"),
        ("100달러는 원화로 얼마야?", "EXCHANGE"),
        ("엔화 환율 알려줘", "EXCHANGE"),
        ("PER이 낮으면 좋은 거야?", "FINANCE_KNOWLEDGE"),
        ("PBR은 무엇인가?", "FINANCE_KNOWLEDGE"),
        ("안녕하세요", "GENERAL"),
        ("오늘 날씨 어때?", "GENERAL"),
        ("삼성전자 PER 알려줘", "FINANCE_KNOWLEDGE"),
        ("삼성전자 주가와 PER을 함께 알려줘", "FINANCE_KNOWLEDGE"),
    ],
)
def test_route_day1_questions(q, category):
    body = post("/api/v1/route", q).json()
    assert body["category"] == category and body["question"] == q


def test_route_stock_uses_tool_not_llm(fake_llm):
    body = post("/api/v1/route", "삼성전자 주가 알려줘").json()
    assert "71,000원" in body["answer"] and fake_llm.calls == []


def test_chat_goes_to_llm(fake_llm):
    body = post("/api/v1/chat", "삼성전자 주가 알려줘").json()
    assert body["answer"] == "LLM 답변" and len(fake_llm.calls) == 1


@pytest.mark.parametrize("path", ["/api/v1/chat", "/api/v1/route"])
def test_validation_422(path):
    assert client.post(path, json={"question": ""}).status_code == 422
    assert client.post(path, json={}).status_code == 422


def test_no_api_key_is_503_not_500():
    app.dependency_overrides.clear()          # 실제 get_llm_client (키 없음)
    r = post("/api/v1/chat", "안녕")
    assert r.status_code == 503 and "AI 서비스" in r.json()["detail"]
    assert post("/api/v1/route", "삼성전자 주가").status_code == 200   # Tool 질문은 키 없이도 동작


def test_swagger_and_examples_and_cors():
    spec = client.get("/openapi.json").json()
    req_schema = spec["components"]["schemas"]["QuestionRequest"]
    assert req_schema["examples"][0]["question"] == "내 잔액 알려줘"
    assert client.get("/docs").status_code == 200
    r = client.options("/api/v1/route", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"

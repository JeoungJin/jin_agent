"""Day2 FastAPI 기본 + /chat (JSON). /route 는 Day3 에서 SSE 로 바뀌었으므로 test_stream_route.py 참고."""
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


def test_chat_is_json_and_goes_to_llm(fake_llm):
    r = post("/api/v1/chat", "삼성전자 주가 알려줘")
    assert r.headers["content-type"].startswith("application/json")
    body = r.json()
    assert body == {"question": "삼성전자 주가 알려줘", "answer": "LLM 답변", "category": "GENERAL"}
    assert len(fake_llm.calls) == 1 and "stream" not in fake_llm.calls[0]     # /chat 은 스트리밍이 아니다


@pytest.mark.parametrize("path", ["/api/v1/chat", "/api/v1/route"])
def test_validation_422(path):
    assert client.post(path, json={"question": ""}).status_code == 422
    assert client.post(path, json={}).status_code == 422


def test_chat_without_api_key_is_503_json():
    app.dependency_overrides.clear()
    r = post("/api/v1/chat", "안녕")
    assert r.status_code == 503 and "AI 서비스" in r.json()["detail"]


def test_swagger_and_examples_and_cors():
    spec = client.get("/openapi.json").json()
    assert spec["components"]["schemas"]["QuestionRequest"]["examples"][0]["question"] == "내 잔액 알려줘"
    assert client.get("/docs").status_code == 200
    r = client.options("/api/v1/route", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"

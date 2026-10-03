"""Day3 Step1: POST /api/v1/route — SSE 이벤트 약속 (category → token* → done / error)"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import get_llm_client
from tests.fakes import FakeClient
from tests.sse_helpers import parse_sse

client = TestClient(app)


def stream(question, fake, **extra):
    app.dependency_overrides[get_llm_client] = lambda: fake
    try:
        r = client.post("/api/v1/route", json={"question": question, **extra})
        return r, parse_sse(r.text)
    finally:
        app.dependency_overrides.clear()


def names(events):
    return [e for e, _ in events]


def test_headers_for_sse():
    r, _ = stream("PER이 뭐야?", FakeClient("답"))
    assert r.headers["content-type"].startswith("text/event-stream")
    assert r.headers["cache-control"] == "no-cache" and r.headers["x-accel-buffering"] == "no"


def test_llm_question_streams_category_tokens_done():
    fake = FakeClient(pieces=["PER은 ", "주가수익", "비율입니다"])
    _, events = stream("PER이 뭐야?", fake)
    assert events[0] == ("category", {"question": "PER이 뭐야?", "category": "FINANCE_KNOWLEDGE"})
    assert names(events) == ["category", "token", "token", "token", "done"]
    assert "".join(d["text"] for e, d in events if e == "token") == "PER은 주가수익비율입니다"
    assert events[-1] == ("done", {}) and fake.calls[0]["stream"] is True   # stream=True 로 호출했다


def test_none_and_empty_choice_chunks_are_skipped():
    fake = FakeClient(pieces=["가", "나"])           # FakeClient 가 None/빈 choices chunk 를 앞뒤로 섞어 보낸다
    _, events = stream("안녕", fake)
    assert [d["text"] for e, d in events if e == "token"] == ["가", "나"]


@pytest.mark.parametrize("q, cat, expect", [
    ("삼성전자 주가 알려줘", "STOCK", "71,000원"),
    ("엔화 환율 알려줘", "EXCHANGE", "9.2"),
])
def test_tool_question_is_one_token_and_no_llm(q, cat, expect):
    fake = FakeClient()
    _, events = stream(q, fake)
    assert names(events) == ["category", "token", "done"]
    assert events[0][1]["category"] == cat and expect in events[1][1]["text"]
    assert fake.calls == []


def test_account_tool_gets_user_id_and_token(monkeypatch):
    got = {}
    monkeypatch.setattr("app.services.route_service.get_account_balance", lambda u, t: got.update(u=u, t=t) or "잔액")
    app.dependency_overrides[get_llm_client] = lambda: FakeClient()
    try:
        r = client.post("/api/v1/route", json={"question": "내 잔액", "user_id": 5}, headers={"Authorization": "Bearer XYZ"})
    finally:
        app.dependency_overrides.clear()
    assert names(parse_sse(r.text)) == ["category", "token", "done"] and got == {"u": 5, "t": "XYZ"}


def test_error_after_start_is_error_event_without_done():
    fake = FakeClient(pieces=["하나", "둘", "셋"], fail_after=1)
    r, events = stream("PER이 뭐야?", fake)
    assert r.status_code == 200                                  # 이미 200 을 보낸 뒤라 상태코드는 그대로
    assert names(events) == ["category", "token", "error"]       # done 은 오지 않는다
    msg = events[-1][1]["message"]
    assert "문제가 발생" in msg and "RuntimeError" not in msg and "끊어졌" not in msg   # 내부 예외 상세는 노출하지 않는다


def test_special_characters_are_json_encoded_safely():
    tricky = '따옴표 " 와 줄바꿈\n 그리고 {중괄호}'
    _, events = stream("안녕", FakeClient(pieces=[tricky]))
    assert [d["text"] for e, d in events if e == "token"] == [tricky]


def test_before_start_errors_are_plain_json():
    assert client.post("/api/v1/route", json={"question": ""}).status_code == 422
    r = client.post("/api/v1/route", json={"question": "PER이 뭐야?"})     # 키 없음(override 없음)
    assert r.status_code == 503 and r.headers["content-type"].startswith("application/json")
    # Tool 질문은 키 없이도 동작
    assert client.post("/api/v1/route", json={"question": "삼성전자 주가"}).status_code == 200


def test_chat_endpoint_is_untouched_json():
    app.dependency_overrides[get_llm_client] = lambda: FakeClient("그대로")
    try:
        r = client.post("/api/v1/chat", json={"question": "안녕"})
    finally:
        app.dependency_overrides.clear()
    assert r.headers["content-type"].startswith("application/json") and r.json()["answer"] == "그대로"

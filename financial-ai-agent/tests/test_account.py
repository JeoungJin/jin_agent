"""Day2 4-4: ACCOUNT 분류 + account_tool(실패 케이스별 한국어 문구) + /route 연결"""
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.llm_service import get_llm_client
from app.services.question_classifier import route_question
from app.tools import account_tool
from tests.fakes import FakeClient


@pytest.mark.parametrize(
    "q, expected",
    [
        ("내 잔액 알려줘", "ACCOUNT"),
        ("통장 잔고 얼마야?", "ACCOUNT"),
        ("통장에 얼마 남았어?", "ACCOUNT"),
        ("계좌 조회해줘", "ACCOUNT"),
        ("계좌 확인 좀", "ACCOUNT"),
        ("계좌 개설하는 방법 알려줘", "GENERAL"),
        ("계좌 개설 가능한 은행 있어?", "GENERAL"),
        ("삼성전자 주가 얼마야?", "STOCK"),           # '얼마' 만으로는 ACCOUNT 가 아니다
        ("삼성전자 PER 알려줘", "FINANCE_KNOWLEDGE"),  # Day1 규칙은 그대로
    ],
)
def test_classifier(q, expected):
    assert route_question(q) == expected


def make_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_success_sends_bearer_and_formats_won():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        seen["path"] = request.url.path
        return httpx.Response(200, json={"userId": 1, "balance": 3250000})

    text = account_tool.get_account_balance(1, "TOK", client=make_client(handler))
    assert text == "현재 계좌 잔액은 3,250,000원입니다."
    assert seen == {"auth": "Bearer TOK", "path": "/internal/api/accounts/1/balance"}


def test_no_token_means_no_authorization_header():
    seen = {}

    def handler(request):
        seen["auth"] = request.headers.get("authorization")
        return httpx.Response(401)

    assert account_tool.get_account_balance(1, None, client=make_client(handler)) == account_tool.MSG_UNAUTHORIZED
    assert seen["auth"] is None


@pytest.mark.parametrize(
    "status, message",
    [(404, account_tool.MSG_NOT_FOUND), (401, account_tool.MSG_UNAUTHORIZED), (403, account_tool.MSG_FORBIDDEN),
     (500, account_tool.MSG_SERVER), (503, account_tool.MSG_SERVER), (418, account_tool.MSG_UNKNOWN)],
)
def test_status_messages(status, message):
    assert account_tool.get_account_balance(1, "T", client=make_client(lambda r: httpx.Response(status))) == message


def test_connection_failure_and_timeout_and_garbage():
    def refuse(request):
        raise httpx.ConnectError("refused")

    def slow(request):
        raise httpx.ReadTimeout("slow")

    assert account_tool.get_account_balance(1, "T", client=make_client(refuse)) == account_tool.MSG_CONNECT
    assert account_tool.get_account_balance(1, "T", client=make_client(slow)) == account_tool.MSG_TIMEOUT
    garbage = make_client(lambda r: httpx.Response(200, text="not json"))
    assert account_tool.get_account_balance(1, "T", client=garbage) == account_tool.MSG_UNKNOWN


@pytest.mark.parametrize("bad", [None, 0, -1, "1", "abc", 1.5, True])
def test_invalid_user_id_never_calls_server(bad):
    def boom(request):
        raise AssertionError("서버를 호출하면 안 된다")

    assert account_tool.get_account_balance(bad, "T", client=make_client(boom)) == account_tool.MSG_INVALID_USER


def test_route_endpoint_passes_user_id_and_token(monkeypatch):
    from tests.sse_helpers import parse_sse

    captured = {}
    monkeypatch.setattr("app.services.route_service.get_account_balance",
                        lambda user_id, token: captured.update(user_id=user_id, token=token) or "잔액 문장")
    app.dependency_overrides[get_llm_client] = lambda: FakeClient()
    try:
        c = TestClient(app)
        r = c.post("/api/v1/route", json={"question": "내 잔액 알려줘", "user_id": 1}, headers={"Authorization": "Bearer ABC"})
        assert parse_sse(r.text) == [
            ("category", {"question": "내 잔액 알려줘", "category": "ACCOUNT"}),
            ("token", {"text": "잔액 문장"}),
            ("done", {}),
        ]
        assert captured == {"user_id": 1, "token": "ABC"}
        # 토큰 없이도 요청은 받는다 (선택 입력)
        r2 = c.post("/api/v1/route", json={"question": "내 잔액 알려줘"})
        assert r2.status_code == 200 and captured == {"user_id": None, "token": None}
    finally:
        app.dependency_overrides.clear()


def test_swagger_has_authorize_button():
    spec = TestClient(app).get("/openapi.json").json()
    assert "HTTPBearer" in spec["components"]["securitySchemes"]

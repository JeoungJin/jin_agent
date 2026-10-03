import time

from fastapi.testclient import TestClient

from app.main import app
from app.tools import stock_tool
from app.tools.stock_tool import STOCKS, UNAVAILABLE, get_quotes, get_stock_price

client = TestClient(app)


def test_normal_sentence():
    s = get_stock_price("삼성전자")
    assert s.startswith("삼성전자 현재가 71,000원, 전일 대비 +1.43% (지연 시세일 수 있음 · ")
    assert s.endswith("기준)")


def test_unknown_stock_keeps_guide_message():
    assert get_stock_price("없는회사") == "등록되지 않은 종목입니다"


def test_ttl_uses_cache_without_refetch(monkeypatch):
    calls = []
    monkeypatch.setattr(stock_tool, "_fetch_one", lambda t: calls.append(t) or (100.0, 100.0))
    get_quotes(["삼성전자"]); get_quotes(["삼성전자"])
    assert calls == ["005930.KS"]


def test_ttl_expired_refetches(monkeypatch):
    calls = []
    monkeypatch.setattr(stock_tool, "_fetch_one", lambda t: calls.append(t) or (100.0, 100.0))
    monkeypatch.setattr(stock_tool, "STOCK_CACHE_TTL", 0)
    get_quotes(["삼성전자"]); get_quotes(["삼성전자"])
    assert len(calls) == 2


def test_failure_uses_stale_cache_with_minutes(monkeypatch):
    get_quotes(["삼성전자"])
    old = stock_tool._cache["005930.KS"]
    stock_tool._cache["005930.KS"] = stock_tool.Quote(old.name, old.ticker, old.price, old.change_percent,
                                                       time.time() - 300)
    def boom(t): raise RuntimeError("yahoo down")
    monkeypatch.setattr(stock_tool, "_fetch_one", boom)
    s = get_stock_price("삼성전자")
    assert "71,000원" in s and "5분 전 값" in s


def test_failure_without_cache_returns_error_message(monkeypatch):
    def boom(t): raise RuntimeError("yahoo down")
    monkeypatch.setattr(stock_tool, "_fetch_one", boom)
    assert get_stock_price("삼성전자") == UNAVAILABLE


def test_portfolio_format_9_items_camel_case():
    r = client.get("/api/v1/portfolio")
    assert r.status_code == 200
    body = r.json()
    assert [q["name"] for q in body] == list(STOCKS)
    assert len(body) == 9
    assert set(body[0]) == {"ticker", "name", "price", "changePercent"}
    assert body[0] == {"ticker": "005930.KS", "name": "삼성전자", "price": 71000, "changePercent": 1.43}


def test_portfolio_partial_failure_skips_uncached(monkeypatch):
    def partial(t):
        if t == "000660.KS": raise RuntimeError("x")
        return 100.0, 100.0
    monkeypatch.setattr(stock_tool, "_fetch_one", partial)
    body = client.get("/api/v1/portfolio").json()
    assert len(body) == 8 and "SK하이닉스" not in [q["name"] for q in body]


def test_portfolio_all_fail_503(monkeypatch):
    def boom(t): raise RuntimeError("x")
    monkeypatch.setattr(stock_tool, "_fetch_one", boom)
    r = client.get("/api/v1/portfolio")
    assert r.status_code == 503 and "시세를 가져올 수 없습니다" in r.json()["detail"]


def test_fetch_is_parallel(monkeypatch):
    def slow(t): time.sleep(0.3); return 100.0, 100.0
    monkeypatch.setattr(stock_tool, "_fetch_one", slow)
    t0 = time.time(); get_quotes(); assert time.time() - t0 < 1.0   # 순차면 2.7초


def test_hung_fetch_respects_timeout(monkeypatch):
    monkeypatch.setattr(stock_tool, "STOCK_FETCH_TIMEOUT", 0.3)
    monkeypatch.setattr(stock_tool, "_fetch_one", lambda t: time.sleep(2) or (1.0, 1.0))
    t0 = time.time()
    assert get_stock_price("삼성전자") == UNAVAILABLE
    assert time.time() - t0 < 1.0

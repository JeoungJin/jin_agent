import pytest

from app.tools import stock_tool


@pytest.fixture(autouse=True)
def fake_yfinance(monkeypatch):
    """모든 테스트에서 yfinance 네트워크 호출을 막고, 삼성전자 71,000 / 전일 70,000(+1.43%)으로 응답한다."""
    stock_tool.clear_cache()
    monkeypatch.setattr(stock_tool, "_fetch_one", lambda ticker: (71000.0, 70000.0))
    yield
    stock_tool.clear_cache()

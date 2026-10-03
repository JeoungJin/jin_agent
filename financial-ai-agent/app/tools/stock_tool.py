"""STOCK Tool: yfinance 기반 시세 조회 (9종목 병렬 조회 + 메모리 캐시).

규칙: 예외를 밖으로 던지지 않는다. Tool 은 항상 한국어 문자열을 돌려준다.
"""
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import datetime

from app.config import STOCK_CACHE_TTL, STOCK_FETCH_TIMEOUT

log = logging.getLogger(__name__)

# 종목명 → 티커 (고정 매핑, 순서가 곧 /portfolio 응답 순서). .KS = 코스피
STOCKS = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "NAVER": "035420.KS",
    "카카오": "035720.KS",
    "LG화학": "051910.KS",
    "현대차": "005380.KS",
    "삼성SDI": "006400.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
}

NOT_REGISTERED = "등록되지 않은 종목입니다"
UNAVAILABLE = "현재 시세를 가져올 수 없습니다. 잠시 후 다시 시도해주세요."


@dataclass(frozen=True)
class Quote:
    name: str
    ticker: str
    price: int
    change_percent: float
    fetched_at: float          # epoch seconds
    cached_age_min: int = 0    # 0 이면 방금 조회한 값, 1 이상이면 "N분 전 값"


def _fetch_one(ticker: str) -> tuple:
    """(현재가, 전일 종가). 테스트에서는 이 함수를 모킹한다."""
    import yfinance as yf

    info = yf.Ticker(ticker).fast_info
    return float(info["last_price"]), float(info["previous_close"])


_cache: dict = {}           # ticker -> Quote
_lock = threading.Lock()


def clear_cache() -> None:
    with _lock:
        _cache.clear()


def _calc(name: str, ticker: str, price: float, prev_close: float, now: float) -> Quote:
    pct = round((price - prev_close) / prev_close * 100, 2)
    return Quote(name, ticker, round(price), pct, now)


def _fresh(q: Quote, now: float) -> bool:
    return now - q.fetched_at < STOCK_CACHE_TTL


def get_quotes(names=None) -> list:
    """종목별 Quote 목록(STOCKS 순서). 조회 실패 종목은 캐시값, 캐시도 없으면 제외."""
    wanted = [n for n in STOCKS if names is None or n in names]
    now = time.time()
    with _lock:
        cached = dict(_cache)

    result: dict = {}
    stale = []
    for name in wanted:
        q = cached.get(STOCKS[name])
        if q and _fresh(q, now):
            result[name] = q
        else:
            stale.append(name)

    if stale:
        pool = ThreadPoolExecutor(max_workers=len(stale))
        futures = {n: pool.submit(_fetch_one, STOCKS[n]) for n in stale}
        deadline = time.monotonic() + STOCK_FETCH_TIMEOUT
        for name in stale:
            ticker = STOCKS[name]
            try:
                price, prev = futures[name].result(timeout=max(0.0, deadline - time.monotonic()))
                q = _calc(name, ticker, price, prev, now)
                with _lock:
                    _cache[ticker] = q
                result[name] = q
            except (FutureTimeout, Exception) as e:   # 한 종목 실패가 전체를 막지 않는다
                log.warning("yfinance 조회 실패 %s: %s %s", ticker, type(e).__name__, e)
                old = cached.get(ticker)
                if old:
                    age = max(1, int((now - old.fetched_at) // 60))
                    result[name] = Quote(old.name, old.ticker, old.price, old.change_percent,
                                         old.fetched_at, cached_age_min=age)
        pool.shutdown(wait=False, cancel_futures=True)

    return [result[n] for n in wanted if n in result]


def get_stock_price(name: str) -> str:
    """종목명으로 시세 문장을 반환한다. 항상 문자열, 예외 없음."""
    if name not in STOCKS:
        return NOT_REGISTERED
    try:
        quotes = get_quotes([name])
    except Exception as e:  # 방어: 어떤 경우에도 던지지 않는다
        log.warning("STOCK Tool 오류: %s %s", type(e).__name__, e)
        return UNAVAILABLE
    if not quotes:
        return UNAVAILABLE
    q = quotes[0]
    hhmm = datetime.fromtimestamp(q.fetched_at).strftime("%H:%M")
    suffix = f" · {hhmm} 기준"
    if q.cached_age_min:
        suffix += f", {q.cached_age_min}분 전 값"
    return f"{name} 현재가 {q.price:,}원, 전일 대비 {q.change_percent:+.2f}% (지연 시세일 수 있음{suffix})"

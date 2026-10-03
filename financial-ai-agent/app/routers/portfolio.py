from fastapi import APIRouter, HTTPException

from app.schemas.portfolio import StockQuote
from app.tools.stock_tool import get_quotes

router = APIRouter(prefix="/api/v1", tags=["portfolio"])


@router.get("/portfolio", response_model=list[StockQuote], response_model_by_alias=True)
def portfolio():
    quotes = get_quotes()
    if not quotes:
        raise HTTPException(status_code=503, detail="시세를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
    return [StockQuote(ticker=q.ticker, name=q.name, price=q.price, changePercent=q.change_percent)
            for q in quotes]

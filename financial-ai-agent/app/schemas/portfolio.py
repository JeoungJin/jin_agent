from pydantic import BaseModel, ConfigDict, Field


class StockQuote(BaseModel):
    """포트폴리오 한 종목. 내부는 snake_case, JSON 은 camelCase(changePercent)."""
    model_config = ConfigDict(populate_by_name=True)

    ticker: str = Field(examples=["005930.KS"])
    name: str = Field(examples=["삼성전자"])
    price: int = Field(examples=[71000])
    change_percent: float = Field(alias="changePercent", examples=[1.43])

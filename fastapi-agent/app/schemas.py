"""요청/응답 스키마 (Spring의 DTO에 해당)."""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="default", description="대화 세션 ID")
    message: str = Field(min_length=1, max_length=2000)
    customer_id: str = Field(default="C001", description="로그인한 고객 ID")


class ToolStep(BaseModel):
    tool: str
    arguments: dict
    result: dict


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    steps: list[ToolStep] = []

"""요청/응답 데이터의 형태(Pydantic). Swagger 에 예시가 그대로 나타난다."""
from typing import Optional

from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, description="사용자 질문")
    user_id: Optional[int] = Field(default=None, description="로그인 사용자 ID (계좌조회에 필요. SpringBoot 가 채워서 보낸다)")

    model_config = {"json_schema_extra": {"examples": [{"question": "내 잔액 알려줘", "user_id": 1}]}}


class AnswerResponse(BaseModel):
    question: str = Field(description="요청한 질문")
    answer: str = Field(description="답변")
    category: str = Field(description="ACCOUNT | STOCK | EXCHANGE | FINANCE_KNOWLEDGE | GENERAL")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "삼성전자 주가 알려줘",
                    "answer": "삼성전자 현재가는 71,000원입니다. (더미 데이터)",
                    "category": "STOCK",
                }
            ]
        }
    }

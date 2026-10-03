"""요청/응답 데이터의 형태(Pydantic). Swagger 에 예시가 그대로 나타난다."""
from pydantic import BaseModel, Field


class QuestionRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000, description="사용자 질문")

    model_config = {"json_schema_extra": {"examples": [{"question": "삼성전자 주가 알려줘"}]}}


class AnswerResponse(BaseModel):
    question: str = Field(description="요청한 질문")
    answer: str = Field(description="답변")
    category: str = Field(description="STOCK | EXCHANGE | FINANCE_KNOWLEDGE | GENERAL")

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

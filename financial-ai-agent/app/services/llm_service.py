"""OpenAI 호출 (일반 대화 / 지식 질문). 키는 .env 의 OPENAI_API_KEY."""
from openai import OpenAI

from app import config

SYSTEM_PROMPT = (
    "너는 금융교육 전문가다. 대상은 금융을 처음 배우는 20대 초보 투자자다.\n"
    "- 어려운 전문용어는 쉬운 말로 풀어서 설명하고, 일상적인 예시를 포함한다.\n"
    "- 특정 종목이나 상품의 매수/매도 추천은 절대 하지 않는다.\n"
    "- 모르는 정보나 실시간 정보는 추측하지 말고 모른다고 말한다."
)


class LLMUnavailableError(Exception):
    """API 키가 없거나 OpenAI 호출에 실패했을 때."""


class LazyOpenAI:
    """OpenAI 클라이언트를 '처음 쓰는 순간'에 만든다.

    요청이 들어올 때마다 미리 만들면, 키가 없을 때 LLM 이 필요 없는 Tool 질문(주가·환율)까지 실패한다.
    """

    def __init__(self):
        self._client = None

    @property
    def chat(self):
        if self._client is None:
            if not config.OPENAI_API_KEY:
                raise LLMUnavailableError("OPENAI_API_KEY 가 설정되지 않았습니다.")
            self._client = OpenAI(api_key=config.OPENAI_API_KEY)
        return self._client.chat


def get_llm_client() -> LazyOpenAI:
    """FastAPI 의존성. 테스트에서는 dependency_overrides 로 가짜 클라이언트를 넣는다."""
    return LazyOpenAI()


def ask_llm(question: str, client) -> str:
    try:
        response = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question},
            ],
        )
    except Exception as e:  # 네트워크/인증/서버 오류
        raise LLMUnavailableError(f"OpenAI 호출 실패: {type(e).__name__}") from e
    return response.choices[0].message.content or ""

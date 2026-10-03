"""금융교육용 AI Assistant - Day1 (Router + Tool 통합 버전).

질문을 route_question() 으로 분류한 뒤
  STOCK             -> stock_tool 의 get_stock_price() 결과
  EXCHANGE          -> exchange_tool 의 get_exchange_rate() 결과
  FINANCE_KNOWLEDGE -> LLM
  GENERAL           -> LLM
로 처리한다. (투자 매수/매도 추천은 하지 않는다)

실행:  python app.py
"""
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from router import route_question
from tools.exchange_tool import DUMMY_EXCHANGE_RATES, get_exchange_rate
from tools.stock_tool import DUMMY_STOCK_PRICES, get_stock_price

SYSTEM_PROMPT = (
    "너는 금융교육 전문가다. 대상은 금융을 처음 배우는 20대 초보 투자자다.\n"
    "- 어려운 전문용어는 쉬운 말로 풀어서 설명하고, 일상적인 예시를 포함한다.\n"
    "- 특정 종목이나 상품의 매수/매도 추천은 절대 하지 않는다.\n"
    "- 모르는 정보나 실시간 정보는 추측하지 말고 모른다고 말한다."
)

EXIT_WORDS = {"exit", "quit", "q", "종료"}


def create_client() -> OpenAI:
    """환경변수(.env)의 OPENAI_API_KEY 로 클라이언트를 만든다. 키가 없으면 안내 후 종료."""
    load_dotenv()
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY 가 설정되지 않았습니다. .env 파일에 키를 넣어 주세요.")
    return OpenAI()


def ask_llm(question: str, client: OpenAI) -> str:
    """질문을 OpenAI 에 보내 답변 문자열을 돌려준다."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content or ""


def extract_stock_name(question: str):
    """질문에서 등록된 종목명을 찾는다. 대소문자는 구분하지 않는다. 없으면 None."""
    lowered = question.lower()
    for name in DUMMY_STOCK_PRICES:
        if name.lower() in lowered:
            return name
    return None


def extract_currency(question: str):
    """질문에서 등록된 통화명을 찾는다. 없으면 None."""
    for currency in DUMMY_EXCHANGE_RATES:
        if currency in question:
            return currency
    return None


def answer_question(question: str, client) -> tuple:
    """질문을 분류하고 처리 경로에 맞는 답변을 만든다. (분류 결과, 답변)을 반환한다."""
    category = route_question(question)
    if category == "STOCK":
        name = extract_stock_name(question)
        answer = get_stock_price(name) if name else "종목명을 알려주세요. (예: 삼성전자)"
    elif category == "EXCHANGE":
        currency = extract_currency(question)
        answer = get_exchange_rate(currency) if currency else "통화를 알려주세요. (예: 달러, 엔화, 유로)"
    else:  # FINANCE_KNOWLEDGE / GENERAL
        answer = ask_llm(question, client)
    return category, answer


def main() -> None:
    try:
        client = create_client()
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    print("금융교육 AI Assistant입니다. 종료하려면 exit 를 입력하세요.")
    while True:
        try:
            question = input("\n질문> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n종료합니다.")
            break
        if question.lower() in EXIT_WORDS:
            print("종료합니다.")
            break
        if not question:
            print("질문을 입력해주세요.")
            continue
        try:
            category, answer = answer_question(question, client)
            print(f"\n[분류: {category}]")
            print("답변>", answer)
        except Exception as e:  # 네트워크/키 오류 등: 프로그램이 죽지 않게 한다
            print(f"\n답변을 가져오지 못했습니다. ({type(e).__name__})")


if __name__ == "__main__":
    main()

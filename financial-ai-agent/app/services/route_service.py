"""질문 분류 + Tool 실행 (Day1 app.py 의 answer_question 을 서비스 계층으로 이전)."""
from app.services.llm_service import ask_llm, stream_llm
from app.services.question_classifier import route_question
from app.tools.account_tool import get_account_balance
from app.tools.exchange_tool import DUMMY_EXCHANGE_RATES, get_exchange_rate
from app.tools.stock_tool import STOCKS, get_stock_price


def extract_stock_name(question: str):
    lowered = question.lower()
    for name in STOCKS:
        if name.lower() in lowered:
            return name
    return None


def extract_currency(question: str):
    for currency in DUMMY_EXCHANGE_RATES:
        if currency in question:
            return currency
    return None


def answer_by_route(question: str, user_id, access_token, client) -> tuple:
    """(category, answer) 를 반환한다."""
    category = route_question(question)
    if category == "ACCOUNT":
        answer = get_account_balance(user_id, access_token)
    elif category == "STOCK":
        name = extract_stock_name(question)
        answer = get_stock_price(name) if name else "종목명을 알려주세요. (예: 삼성전자)"
    elif category == "EXCHANGE":
        currency = extract_currency(question)
        answer = get_exchange_rate(currency) if currency else "통화를 알려주세요. (예: 달러, 엔화, 유로)"
    else:  # FINANCE_KNOWLEDGE / GENERAL
        answer = ask_llm(question, client)
    return category, answer


TOOL_CATEGORIES = {"ACCOUNT", "STOCK", "EXCHANGE"}


def stream_by_route(question: str, user_id, access_token, client):
    """(event, data) 를 순서대로 내보내는 제너레이터. category → token(여러 번)  (done/error 는 라우터가 붙인다)"""
    category = route_question(question)
    yield "category", {"question": question, "category": category}

    if category in TOOL_CATEGORIES:
        # Tool 은 기존 동기 방식을 유지하고, 결과 문자열 전체를 token 이벤트 1개로 보낸다.
        _, answer = answer_by_route(question, user_id, access_token, client)
        yield "token", {"text": answer}
    else:  # FINANCE_KNOWLEDGE / GENERAL → OpenAI 스트리밍 조각을 그대로 흘려보낸다
        for text in stream_llm(question, client):
            yield "token", {"text": text}

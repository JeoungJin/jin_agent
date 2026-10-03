"""질문 분류 + Tool 실행 (Day1 app.py 의 answer_question 을 서비스 계층으로 이전)."""
from app.services.llm_service import ask_llm
from app.services.question_classifier import route_question
from app.tools.account_tool import get_account_balance
from app.tools.exchange_tool import DUMMY_EXCHANGE_RATES, get_exchange_rate
from app.tools.stock_tool import DUMMY_STOCK_PRICES, get_stock_price


def extract_stock_name(question: str):
    lowered = question.lower()
    for name in DUMMY_STOCK_PRICES:
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

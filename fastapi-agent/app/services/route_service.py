"""질문 분류 후 Tool 또는 LLM으로 처리하는 서비스 계층."""
from app.schemas import AnswerResponse
from app.services.llm import get_llm
from app.tools import STOCK_PRICES, get_account_balance, get_stock_price

DEFAULT_CUSTOMER = "C001"
SYSTEM_PROMPT = "당신은 금융 서비스 AI 상담원입니다. 한국어로 간결하게 답하세요."


def classify(question: str) -> str:
    if any(k in question for k in ("주가", "시세", "현재가")):
        return "stock"
    if any(k in question for k in ("잔액", "잔고")):
        return "account"
    return "general"


def route_question(question: str) -> AnswerResponse:
    category = classify(question)

    if category == "stock":  # 정확한 값 → Tool
        name = next((n for n in STOCK_PRICES if n in question), None)
        result = get_stock_price(name) if name else {"error": "종목명을 알려주세요. (예: 삼성전자)"}
        answer = result["error"] if "error" in result else \
            f"{result['name']} 현재가는 {result['price']:,}원입니다. (수업용 모의 데이터)"

    elif category == "account":  # 개인 데이터 → Tool
        acc = get_account_balance(DEFAULT_CUSTOMER)
        answer = f"{acc['owner']}님의 잔액은 {acc['balance']:,}원입니다."

    else:  # 설명·일반 질문 → LLM
        resp = get_llm().complete([
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ])
        answer = resp.text or "주가·잔액 조회와 일반 금융 질문을 도와드릴 수 있어요."

    return AnswerResponse(question=question, answer=answer, category=category)

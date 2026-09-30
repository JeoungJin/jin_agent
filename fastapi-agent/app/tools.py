"""에이전트가 호출할 수 있는 Tool(Function Calling) 정의와 실행기."""
from app.data import ACCOUNTS, TRANSACTIONS


def get_account_balance(customer_id: str) -> dict:
    acc = ACCOUNTS.get(customer_id)
    if not acc:
        return {"error": f"고객 {customer_id} 계좌를 찾을 수 없습니다."}
    return acc


def get_transaction_history(customer_id: str, limit: int = 5) -> dict:
    rows = TRANSACTIONS.get(customer_id, [])
    return {"customer_id": customer_id, "transactions": rows[-limit:]}


def calculate_loan_payment(principal: int, annual_rate_pct: float, months: int) -> dict:
    """원리금균등상환 월 납입액."""
    if principal <= 0 or months <= 0 or annual_rate_pct < 0:
        return {"error": "입력값이 올바르지 않습니다."}
    r = annual_rate_pct / 100 / 12
    if r == 0:
        monthly = principal / months
    else:
        monthly = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return {
        "principal": principal,
        "annual_rate_pct": annual_rate_pct,
        "months": months,
        "monthly_payment": round(monthly),
        "total_interest": round(monthly * months - principal),
    }


REGISTRY = {
    "get_account_balance": get_account_balance,
    "get_transaction_history": get_transaction_history,
    "calculate_loan_payment": calculate_loan_payment,
}

# OpenAI Function Calling 스키마
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "get_account_balance",
            "description": "고객의 계좌 잔액을 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {"customer_id": {"type": "string"}},
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_transaction_history",
            "description": "고객의 최근 거래내역을 조회한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_id": {"type": "string"},
                    "limit": {"type": "integer", "default": 5},
                },
                "required": ["customer_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_loan_payment",
            "description": "대출 원리금균등상환 월 납입액을 계산한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "principal": {"type": "integer", "description": "대출 원금(원)"},
                    "annual_rate_pct": {"type": "number", "description": "연이율(%)"},
                    "months": {"type": "integer", "description": "상환 개월 수"},
                },
                "required": ["principal", "annual_rate_pct", "months"],
            },
        },
    },
]


def run_tool(name: str, arguments: dict) -> dict:
    fn = REGISTRY.get(name)
    if fn is None:
        return {"error": f"알 수 없는 tool: {name}"}
    try:
        return fn(**arguments)
    except TypeError as e:  # 인자 불일치 (LLM이 잘못 호출한 경우)
        return {"error": f"인자 오류: {e}"}

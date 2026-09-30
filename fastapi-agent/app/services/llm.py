"""LLM 어댑터. 인터페이스는 하나, 구현은 Mock / OpenAI 두 가지."""
import json
import os
import re
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.tools import TOOL_SCHEMAS


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLM(Protocol):
    def complete(self, messages: list[dict]) -> LLMResponse: ...


class OpenAILLM:
    def __init__(self, api_key: str, model: str):
        self.api_key, self.model = api_key, model

    def complete(self, messages: list[dict]) -> LLMResponse:
        resp = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": messages, "tools": TOOL_SCHEMAS},
            timeout=60,
        )
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        calls = [
            ToolCall(c["id"], c["function"]["name"], json.loads(c["function"]["arguments"] or "{}"))
            for c in msg.get("tool_calls") or []
        ]
        return LLMResponse(text=msg.get("content") or "", tool_calls=calls)


class MockLLM:
    """API 키 없이 수업에서 흐름을 볼 수 있게 하는 규칙 기반 LLM.

    1) 사용자 질문의 키워드로 tool을 고르고  2) tool 결과가 들어오면 문장으로 정리한다.
    """

    def complete(self, messages: list[dict]) -> LLMResponse:
        last = messages[-1]
        if last["role"] == "tool":
            return LLMResponse(text=self._summarize(messages))

        text = last["content"]
        cid = self._customer_id(messages)
        if m := re.search(r"(\d[\d,]*)\s*(만원|원)", text):
            if any(k in text for k in ("대출", "상환", "이자")):
                num = int(m.group(1).replace(",", "")) * (10_000 if m.group(2) == "만원" else 1)
                rate = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
                months = re.search(r"(\d+)\s*개월", text)
                years = re.search(r"(\d+)\s*년", text)
                n = int(months.group(1)) if months else int(years.group(1)) * 12 if years else 36
                return self._call("calculate_loan_payment", {
                    "principal": num,
                    "annual_rate_pct": float(rate.group(1)) if rate else 5.0,
                    "months": n,
                })
        if any(k in text for k in ("거래", "내역", "지출", "입금")):
            return self._call("get_transaction_history", {"customer_id": cid})
        if any(k in text for k in ("잔액", "잔고", "얼마")):
            return self._call("get_account_balance", {"customer_id": cid})
        return LLMResponse(text="잔액 조회, 거래내역 조회, 대출 월 납입액 계산을 도와드릴 수 있어요.")

    @staticmethod
    def _call(name: str, args: dict) -> LLMResponse:
        return LLMResponse(tool_calls=[ToolCall(f"call_{name}", name, args)])

    @staticmethod
    def _customer_id(messages: list[dict]) -> str:
        sys = messages[0]["content"]
        m = re.search(r"customer_id=(\w+)", sys)
        return m.group(1) if m else "C001"

    @staticmethod
    def _summarize(messages: list[dict]) -> str:
        data = json.loads(messages[-1]["content"])
        if "error" in data:
            return f"처리 중 문제가 있었어요: {data['error']}"
        if "balance" in data:
            return f"{data['owner']}님의 계좌({data['account_no']}) 잔액은 {data['balance']:,}원입니다."
        if "transactions" in data:
            lines = [f"- {t['date']} {t['desc']} {t['amount']:+,}원" for t in data["transactions"]]
            return "최근 거래내역입니다.\n" + "\n".join(lines)
        if "monthly_payment" in data:
            return (f"{data['principal']:,}원을 연 {data['annual_rate_pct']}%로 {data['months']}개월 상환하면 "
                    f"월 {data['monthly_payment']:,}원, 총 이자는 {data['total_interest']:,}원입니다.")
        return json.dumps(data, ensure_ascii=False)


def get_llm() -> LLM:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if key:
        return OpenAILLM(key, os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    return MockLLM()

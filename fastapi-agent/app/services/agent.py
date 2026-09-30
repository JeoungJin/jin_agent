"""에이전트 루프: LLM → (tool 호출 → 결과 주입)* → 최종 답변.

이벤트를 yield 하는 제너레이터로 만들어 스트리밍(SSE)과 일반 응답이 같은 로직을 공유한다.
"""
import json
from collections.abc import Iterator

from app.services.llm import LLM
from app.tools import run_tool

MAX_STEPS = 5  # 무한 tool 호출 방지
MAX_HISTORY = 20  # 세션 메모리 상한(메시지 수)

SYSTEM_PROMPT = (
    "당신은 금융 서비스 AI 상담원입니다. 현재 고객은 customer_id={cid} 입니다. "
    "계좌/거래/대출 질문은 반드시 tool로 확인한 뒤 답하고, 모르는 것은 모른다고 말하세요. "
    "한국어로 간결하게 답합니다."
)

_sessions: dict[str, list[dict]] = {}


def reset_sessions() -> None:
    _sessions.clear()


def run_agent(llm: LLM, session_id: str, customer_id: str, message: str) -> Iterator[dict]:
    history = _sessions.setdefault(session_id, [])
    history.append({"role": "user", "content": message})
    system = {"role": "system", "content": SYSTEM_PROMPT.format(cid=customer_id)}

    for _ in range(MAX_STEPS):
        resp = llm.complete([system, *history])
        if not resp.tool_calls:
            history.append({"role": "assistant", "content": resp.text})
            del history[:-MAX_HISTORY]
            yield {"type": "answer", "text": resp.text}
            return

        history.append({
            "role": "assistant",
            "content": resp.text or None,
            "tool_calls": [
                {"id": c.id, "type": "function",
                 "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                for c in resp.tool_calls
            ],
        })
        for call in resp.tool_calls:
            yield {"type": "tool_call", "tool": call.name, "arguments": call.arguments}
            result = run_tool(call.name, call.arguments)
            yield {"type": "tool_result", "tool": call.name, "result": result}
            history.append({"role": "tool", "tool_call_id": call.id,
                            "content": json.dumps(result, ensure_ascii=False)})

    yield {"type": "answer", "text": "요청을 처리하지 못했습니다. 질문을 조금 더 구체적으로 해주세요."}

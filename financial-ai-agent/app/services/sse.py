"""SSE 한 건을 만든다: "event: <이름>\\ndata: <JSON>\\n\\n"  (빈 줄이 이벤트의 끝)"""
import json


def sse(event: str, data: dict) -> str:
    # data 는 문자열을 직접 이어 붙이지 않고 json.dumps 로 직렬화한다. (따옴표·줄바꿈이 있어도 안전)
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

import json


def parse_sse(text: str):
    """SSE 본문을 [(event, data_dict), ...] 로 파싱한다. 빈 줄이 이벤트의 끝."""
    events = []
    for block in text.replace("\r\n", "\n").split("\n\n"):
        if not block.strip():
            continue
        event, data = None, None
        for line in block.split("\n"):
            if line.startswith("event:"):
                event = line[6:].strip()
            elif line.startswith("data:"):
                data = json.loads(line[5:].strip())
        events.append((event, data))
    return events

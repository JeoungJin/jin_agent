import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from app.schemas import ChatRequest, ChatResponse, ToolStep
from app.services.agent import run_agent
from app.services.llm import get_llm

app = FastAPI(title="Finance AI Agent")
# Spring이 호출하는 서버 간 통신이 기본이지만, 수업 중 Swagger/브라우저 직접 테스트를 위해 열어 둔다.
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "llm": type(get_llm()).__name__}


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    steps, pending, answer = [], None, ""
    for ev in run_agent(get_llm(), req.session_id, req.customer_id, req.message):
        if ev["type"] == "tool_call":
            pending = ev
        elif ev["type"] == "tool_result" and pending:
            steps.append(ToolStep(tool=ev["tool"], arguments=pending["arguments"], result=ev["result"]))
        elif ev["type"] == "answer":
            answer = ev["text"]
    return ChatResponse(session_id=req.session_id, answer=answer, steps=steps)


@app.post("/api/v1/chat/stream")
def chat_stream(req: ChatRequest):
    def gen():
        try:
            for ev in run_agent(get_llm(), req.session_id, req.customer_id, req.message):
                if ev["type"] == "answer":  # 답변은 글자 단위로 흘려보낸다
                    text = ev["text"]
                    for i in range(0, len(text), 4):
                        yield _sse("token", {"text": text[i:i + 4]})
                else:
                    yield _sse(ev["type"], ev)
        except Exception as e:  # LLM 호출 실패 등
            yield _sse("error", {"message": str(e)})
        yield _sse("done", {})

    return StreamingResponse(gen(), media_type="text/event-stream")


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

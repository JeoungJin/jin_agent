"""Day1 7절 검증 체크리스트: 정상 질문 / 빈 질문 / 잘못된 입력 / 키 없음"""
import subprocess
import sys
from types import SimpleNamespace

import pytest

import app


class FakeClient:
    def __init__(self, text="테스트 답변"):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.calls = []
        self._text = text

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        msg = SimpleNamespace(content=self._text)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def test_ask_llm_returns_text_and_sends_system_prompt():
    client = FakeClient("PER은 주가수익비율입니다")
    assert app.ask_llm("PER이 뭐야?", client) == "PER은 주가수익비율입니다"
    sent = client.calls[0]["messages"]
    assert sent[0]["role"] == "system" and "추천은 절대 하지 않는다" in sent[0]["content"]
    assert sent[1] == {"role": "user", "content": "PER이 뭐야?"}


def test_missing_api_key_gives_guidance(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(app, "load_dotenv", lambda: None)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        app.create_client()


def run_cli(inputs, env_extra=None):
    import os
    env = {**os.environ, "OPENAI_API_KEY": "fake", **(env_extra or {})}
    return subprocess.run([sys.executable, "app.py"], input=inputs, capture_output=True, text=True, env=env, timeout=30)


def test_cli_blank_and_exit():
    out = run_cli("\n   \nexit\n").stdout
    assert "질문을 입력해주세요" in out and "종료합니다" in out

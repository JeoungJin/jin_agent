from types import SimpleNamespace


class FakeClient:
    """OpenAI 클라이언트 흉내: chat.completions.create() 만 지원."""

    def __init__(self, text="테스트 답변"):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.calls = []
        self._text = text

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._text))])

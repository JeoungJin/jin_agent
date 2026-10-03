from types import SimpleNamespace


class FakeClient:
    """OpenAI 클라이언트 흉내: chat.completions.create() 만 지원 (일반 응답 + stream=True)."""

    def __init__(self, text="테스트 답변", pieces=None, fail_after=None):
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self.calls = []
        self._text = text
        self._pieces = pieces
        self._fail_after = fail_after      # 스트림 도중 이 개수만큼 내보낸 뒤 예외

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if kwargs.get("stream"):
            return self._stream()
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self._text))])

    def _chunk(self, content):
        return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content))])

    def _stream(self):
        yield self._chunk(None)                       # 첫 chunk: role 만 있고 content 는 None
        yield SimpleNamespace(choices=[])             # choices 가 비어 있는 chunk
        pieces = self._pieces or [self._text[i:i + 3] for i in range(0, len(self._text), 3)]
        for i, piece in enumerate(pieces):
            if self._fail_after is not None and i >= self._fail_after:
                raise RuntimeError("OpenAI 연결이 끊어졌습니다")
            yield self._chunk(piece)
        yield self._chunk(None)                       # 마지막 chunk: finish_reason 만 있고 content 는 None

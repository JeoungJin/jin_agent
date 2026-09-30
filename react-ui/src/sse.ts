export interface SseEvent {
  event: string
  data: string
}

/** SSE 텍스트 버퍼에서 완성된 이벤트를 꺼내고, 남은 조각(rest)을 돌려준다. */
export function parseSse(buffer: string): { events: SseEvent[]; rest: string } {
  const chunks = buffer.split('\n\n')
  const rest = chunks.pop() ?? ''
  const events: SseEvent[] = []
  for (const chunk of chunks) {
    let event = 'message'
    const data: string[] = []
    for (const line of chunk.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data.push(line.slice(5).trim())
    }
    if (data.length) events.push({ event, data: data.join('\n') })
  }
  return { events, rest }
}

/** POST 기반 SSE. EventSource는 POST를 못 보내므로 fetch + ReadableStream을 쓴다. */
export async function streamChat(
  body: { sessionId: string; message: string },
  onEvent: (e: SseEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
  if (!res.ok || !res.body) throw new Error(`서버 오류 (${res.status})`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n')
    const parsed = parseSse(buffer)
    buffer = parsed.rest
    parsed.events.forEach(onEvent)
  }
}

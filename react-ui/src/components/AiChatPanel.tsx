import { useEffect, useRef, useState } from 'react'
import { parseSse } from '../lib/parseSse'

interface Message {
  role: 'user' | 'assistant'
  text: string
  category?: string
  error?: boolean
}

export default function AiChatPanel({ onUnauthorized }: { onUnauthorized: () => void }) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const abortRef = useRef<AbortController | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => () => abortRef.current?.abort(), [])
  useEffect(() => bottomRef.current?.scrollIntoView?.({ behavior: 'smooth' }), [messages])

  // 마지막(assistant) 메시지를 갱신
  const patchLast = (fn: (m: Message) => Message) =>
    setMessages((prev) => prev.map((m, i) => (i === prev.length - 1 ? fn(m) : m)))

  const send = async () => {
    const question = input.trim()
    if (!question || loading) return
    setInput('')
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', text: question }, { role: 'assistant', text: '' }])

    const controller = new AbortController()
    abortRef.current = controller
    try {
      const res = await fetch('/api/ai/route', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
        body: JSON.stringify({ question }),
        signal: controller.signal,
      })
      if (!res.ok) {
        if (res.status === 401) return onUnauthorized()
        const body = await res.json().catch(() => null)
        patchLast((m) => ({ ...m, text: body?.message ?? '요청을 처리하지 못했습니다.', error: true }))
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''
      for (;;) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const parsed = parseSse(buffer)
        buffer = parsed.rest
        for (const { event, data } of parsed.events) {
          const d = data as { text?: string; category?: string; message?: string }
          if (event === 'category') patchLast((m) => ({ ...m, category: d.category }))
          else if (event === 'token') patchLast((m) => ({ ...m, text: m.text + (d.text ?? '') }))
          else if (event === 'error')
            patchLast((m) => ({ ...m, text: m.text || d.message || '오류가 발생했습니다.', error: true }))
          // done / 알 수 없는 이벤트: finally에서 로딩 해제
        }
      }
    } catch (e) {
      if ((e as Error).name !== 'AbortError')
        patchLast((m) => ({ ...m, text: '네트워크 오류가 발생했습니다.', error: true }))
    } finally {
      setLoading(false)
    }
  }

  const stop = () => abortRef.current?.abort()

  return (
    <div className="mx-auto flex h-[70vh] max-w-2xl flex-col rounded-lg border">
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div key={i} className={m.role === 'user' ? 'text-right' : 'text-left'}>
            {m.category && (
              <span data-testid="category" className="mr-2 rounded bg-gray-200 px-2 py-0.5 text-xs">
                {m.category}
              </span>
            )}
            <span
              className={`inline-block whitespace-pre-wrap rounded px-3 py-2 ${
                m.role === 'user' ? 'bg-blue-100' : m.error ? 'bg-red-100 text-red-700' : 'bg-gray-100'
              }`}
            >
              {m.text || (loading && i === messages.length - 1 ? '…' : '')}
            </span>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 border-t p-3">
        <input
          className="flex-1 rounded border px-3 py-2 disabled:bg-gray-100"
          placeholder="금융 질문을 입력하세요"
          value={input}
          disabled={loading}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            // 한글 조합 중 Enter 방지
            if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
              e.preventDefault()
              send()
            }
          }}
        />
        {loading ? (
          <button onClick={stop} className="rounded bg-gray-500 px-4 text-white">중지</button>
        ) : (
          <button onClick={send} className="rounded bg-blue-600 px-4 text-white">전송</button>
        )}
      </div>
    </div>
  )
}

import { useRef, useState } from 'react'
import { streamChat } from './sse'

interface Msg {
  role: 'user' | 'assistant'
  text: string
  tools?: string[] // 에이전트가 호출한 tool 흔적
}

const SESSION_ID = crypto.randomUUID()
const SUGGESTIONS = ['내 계좌 잔액 알려줘', '최근 거래내역 보여줘', '1000만원 연 5%로 24개월 대출하면 월 얼마야?']

export function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // 마지막(assistant) 메시지만 갱신하는 헬퍼 — 불변성을 지키며 복사
  const patchLast = (fn: (m: Msg) => Msg) =>
    setMessages((prev) => [...prev.slice(0, -1), fn(prev[prev.length - 1])])

  async function send(text: string) {
    if (!text.trim() || loading) return
    setInput('')
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', text }, { role: 'assistant', text: '', tools: [] }])
    try {
      await streamChat({ sessionId: SESSION_ID, message: text }, ({ event, data }) => {
        const payload = JSON.parse(data)
        if (event === 'token') patchLast((m) => ({ ...m, text: m.text + payload.text }))
        else if (event === 'tool_call')
          patchLast((m) => ({ ...m, tools: [...(m.tools ?? []), `${payload.tool}(${JSON.stringify(payload.arguments)})`] }))
        else if (event === 'error') patchLast((m) => ({ ...m, text: payload.message }))
      })
    } catch (e) {
      patchLast((m) => ({ ...m, text: `오류: ${(e as Error).message}` }))
    } finally {
      setLoading(false)
      setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 0)
    }
  }

  return (
    <main className="chat">
      <h1>금융 AI 상담원</h1>
      <p className="flow">React → Spring Boot → FastAPI → LLM + Tools</p>

      <div className="messages">
        {messages.length === 0 && (
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}>{s}</button>
            ))}
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`msg ${m.role}`}>
            {m.tools?.map((t, j) => <div key={j} className="tool">🔧 {t}</div>)}
            <div className="text">{m.text || (loading && i === messages.length - 1 ? '…' : '')}</div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(input) }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="메시지를 입력하세요" disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()}>전송</button>
      </form>
    </main>
  )
}

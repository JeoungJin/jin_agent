import { useState } from 'react'
import { routeQuestion } from './api'

interface Msg {
  role: 'user' | 'assistant'
  text: string
  category?: string
}

const SUGGESTIONS = ['삼성전자 주가 알려줘', '내 계좌 잔액 알려줘', '예금과 적금의 차이가 뭐야?']

export function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  async function send(question: string) {
    if (!question.trim() || loading) return
    setInput('')
    setLoading(true)
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    try {
      const res = await routeQuestion(question) // 응답이 완성되면 한 번에 도착
      setMessages((prev) => [...prev, { role: 'assistant', text: res.answer, category: res.category }])
    } catch {
      setMessages((prev) => [...prev, { role: 'assistant', text: '서버와 통신하지 못했습니다.', category: 'error' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="chat">
      <h1>금융 AI 상담원</h1>
      <p className="flow">React → Spring Boot(8000) → FastAPI(9000)</p>

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
            {m.category && <div className="tool">{m.category}</div>}
            <div className="text">{m.text}</div>
          </div>
        ))}
        {loading && <div className="msg assistant">…</div>}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send(input) }}>
        <input value={input} onChange={(e) => setInput(e.target.value)} placeholder="질문을 입력하세요" disabled={loading} />
        <button type="submit" disabled={loading || !input.trim()}>전송</button>
      </form>
    </main>
  )
}

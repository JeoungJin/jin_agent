import { useCallback, useEffect, useState } from 'react'
import { fetchMe, logout } from './api/authApi'
import { setUnauthorizedHandler } from './api/httpClient'
import AiChatPanel from './components/AiChatPanel'
import PortfolioDashboard from './components/PortfolioDashboard'
import LoginForm from './components/LoginForm'

type AuthState = 'checking' | 'in' | 'out'

export default function App() {
  const [auth, setAuth] = useState<AuthState>('checking')
  const [tab, setTab] = useState<'chat' | 'portfolio'>('chat')

  const goLogin = useCallback(() => setAuth('out'), [])

  useEffect(() => {
    setUnauthorizedHandler(goLogin)
    fetchMe().then(() => setAuth('in')).catch(() => setAuth('out'))
  }, [goLogin])

  const handleLogout = async () => {
    await logout().catch(() => {})
    setAuth('out')
  }

  if (auth === 'checking') return <p className="p-8">로딩 중…</p>
  if (auth === 'out') return <LoginForm onLoggedIn={() => setAuth('in')} />

  return (
    <div className="mx-auto max-w-3xl p-4">
      <header className="mb-4 flex items-center justify-between">
        <h1 className="text-xl font-bold">금융 AI 에이전트</h1>
        <button onClick={handleLogout} className="rounded border px-3 py-1">로그아웃</button>
      </header>
      <nav className="mb-4 flex gap-2">
        {(['chat', 'portfolio'] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`rounded px-4 py-1 ${tab === t ? 'bg-blue-600 text-white' : 'border'}`}
          >
            {t === 'chat' ? '채팅' : '포트폴리오'}
          </button>
        ))}
      </nav>
      {tab === 'chat' ? <AiChatPanel onUnauthorized={goLogin} /> : <PortfolioDashboard />}
    </div>
  )
}

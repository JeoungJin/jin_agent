import { useState } from 'react'
import { login } from '../api/authApi'

export default function LoginForm({ onLoggedIn }: { onLoggedIn: () => void }) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email.trim())
      onLoggedIn()
    } catch {
      setError('로그인에 실패했습니다. 이메일을 확인해주세요.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-24 w-80 space-y-3 rounded-lg border p-6 shadow">
      <h1 className="text-lg font-bold">금융 AI 에이전트 로그인</h1>
      <input
        className="w-full rounded border px-3 py-2"
        type="email"
        placeholder="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button disabled={busy} className="w-full rounded bg-blue-600 py-2 text-white disabled:opacity-50">
        로그인
      </button>
    </form>
  )
}

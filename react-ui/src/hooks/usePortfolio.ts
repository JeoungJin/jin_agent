import { useCallback, useEffect, useRef, useState } from 'react'
import axios from 'axios'
import { fetchPortfolio } from '../api/portfolioApi'
import type { StockQuote } from '../types/portfolio'

const REFRESH_MS = 60_000 // 서버 캐시 TTL(60초)과 맞춤

export function usePortfolio() {
  const [data, setData] = useState<StockQuote[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const refetch = useCallback(async () => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setLoading(true)
    setError(false)
    try {
      setData(await fetchPortfolio(controller.signal))
      setUpdatedAt(new Date())
    } catch (e) {
      if (axios.isCancel(e)) return
      setError(true) // 401은 httpClient 인터셉터가 처리
    } finally {
      if (abortRef.current === controller) setLoading(false)
    }
  }, [])

  useEffect(() => {
    refetch()
    // 탭이 숨겨지면 자동 갱신 중지
    const id = setInterval(() => {
      if (document.visibilityState === 'visible') refetch()
    }, REFRESH_MS)
    return () => {
      clearInterval(id)
      abortRef.current?.abort()
    }
  }, [refetch])

  return { data, loading, error, updatedAt, refetch }
}

import { httpClient } from './httpClient'
import type { StockQuote } from '../types/portfolio'

export const fetchPortfolio = (signal?: AbortSignal) =>
  httpClient.get<StockQuote[]>('/api/ai/portfolio', { signal }).then((r) => r.data)

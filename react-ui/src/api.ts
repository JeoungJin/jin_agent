import axios from 'axios'

export interface AiRouteResponse {
  question: string
  answer: string
  category: string // stock | account | general | fallback
}

/** Spring(/api/ai/route)에 질문을 보내고 완성된 JSON 응답을 한 번에 받는다. */
export async function routeQuestion(question: string): Promise<AiRouteResponse> {
  const { data } = await axios.post<AiRouteResponse>('/api/ai/route', { question }, { timeout: 10_000 })
  return data
}

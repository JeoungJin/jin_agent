import axios from 'axios'
import { describe, expect, it, vi } from 'vitest'
import { routeQuestion } from './api'

vi.mock('axios')

describe('routeQuestion', () => {
  it('질문을 body로 보내고 data만 꺼내 돌려준다', async () => {
    const res = { question: 'q', answer: 'a', category: 'general' }
    vi.mocked(axios.post).mockResolvedValue({ data: res })

    await expect(routeQuestion('q')).resolves.toEqual(res)
    expect(axios.post).toHaveBeenCalledWith('/api/ai/route', { question: 'q' }, expect.anything())
  })
})

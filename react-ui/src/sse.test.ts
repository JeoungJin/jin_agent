import { describe, expect, it } from 'vitest'
import { parseSse } from './sse'

describe('parseSse', () => {
  it('완성된 이벤트만 파싱하고 나머지는 rest로 남긴다', () => {
    const { events, rest } = parseSse('event: token\ndata: {"text":"안"}\n\nevent: tok')
    expect(events).toEqual([{ event: 'token', data: '{"text":"안"}' }])
    expect(rest).toBe('event: tok')
  })

  it('event 이름이 없으면 message', () => {
    expect(parseSse('data: hi\n\n').events[0].event).toBe('message')
  })
})

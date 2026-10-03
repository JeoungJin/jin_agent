import { describe, expect, it } from 'vitest'
import { parseSse } from './parseSse'

describe('parseSse', () => {
  it('완성된 이벤트 1개를 파싱한다', () => {
    const { events, rest } = parseSse('event: token\ndata: {"text":"안"}\n\n')
    expect(events).toEqual([{ event: 'token', data: { text: '안' } }])
    expect(rest).toBe('')
  })

  it('청크 경계에서 잘린 이벤트는 rest에 남기고 이어 붙이면 완성된다', () => {
    const first = parseSse('event: token\ndata: {"te')
    expect(first.events).toEqual([])
    const second = parseSse(first.rest + 'xt":"녕"}\n\n')
    expect(second.events).toEqual([{ event: 'token', data: { text: '녕' } }])
  })

  it('\\r\\n 줄바꿈을 \\n으로 정규화한다', () => {
    const { events } = parseSse('event: done\r\ndata: {}\r\n\r\n')
    expect(events).toEqual([{ event: 'done', data: {} }])
  })

  it('한 청크에 여러 이벤트가 있어도 모두 반환한다', () => {
    const { events, rest } = parseSse(
      'event: category\ndata: {"question":"q","category":"GENERAL"}\n\n' +
        'event: token\ndata: {"text":"a"}\n\n' +
        'event: done\ndata: {}\n\nevent: tok',
    )
    expect(events.map((e) => e.event)).toEqual(['category', 'token', 'done'])
    expect(rest).toBe('event: tok')
  })

  it('JSON이 아닌 data는 무시한다', () => {
    expect(parseSse('event: x\ndata: nope\n\n').events).toEqual([])
  })
})

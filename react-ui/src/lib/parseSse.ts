export interface SseEvent {
  event: string
  data: unknown
}

/**
 * SSE 파서 (순수 함수).
 * buffer에 새 청크를 이어 붙여 완성된 이벤트만 반환하고, 미완성 부분은 rest로 돌려준다.
 */
export function parseSse(buffer: string): { events: SseEvent[]; rest: string } {
  const normalized = buffer.replace(/\r\n/g, '\n')
  const blocks = normalized.split('\n\n')
  const rest = blocks.pop() ?? ''
  const events: SseEvent[] = []

  for (const block of blocks) {
    let event = 'message'
    const dataLines: string[] = []
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) dataLines.push(line.slice(5).replace(/^ /, ''))
    }
    if (dataLines.length === 0) continue
    try {
      events.push({ event, data: JSON.parse(dataLines.join('\n')) })
    } catch {
      // JSON이 아닌 data는 무시
    }
  }
  return { events, rest }
}

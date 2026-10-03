import { useState } from 'react'
import { Bar, BarChart, Cell, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { usePortfolio } from '../hooks/usePortfolio'
import type { StockQuote } from '../types/portfolio'

const UP = '#dc2626'
const DOWN = '#2563eb'
const FLAT = '#6b7280'

const colorOf = (v: number) => (v > 0 ? UP : v < 0 ? DOWN : FLAT)
const arrowOf = (v: number) => (v > 0 ? '▲' : v < 0 ? '▼' : '-')
const pct = (v: number) => `${v > 0 ? '+' : v < 0 ? '−' : ''}${Math.abs(v).toFixed(2)}%`
const won = (v: number) => `${v.toLocaleString('ko-KR')}원`

function ChartTooltip({ active, payload }: { active?: boolean; payload?: { payload: StockQuote }[] }) {
  if (!active || !payload?.length) return null
  const q = payload[0].payload
  return (
    <div className="rounded border bg-white p-2 text-sm shadow">
      <div className="font-bold">{q.name}</div>
      <div>{won(q.price)}</div>
      <div style={{ color: colorOf(q.changePercent) }}>
        {arrowOf(q.changePercent)} {pct(q.changePercent)}
      </div>
    </div>
  )
}

export default function PortfolioDashboard() {
  const { data, loading, error, updatedAt, refetch } = usePortfolio()
  const [selected, setSelected] = useState<string | null>(null)
  const sel = data?.find((q) => q.ticker === selected)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">포트폴리오 (전일 대비 등락률)</h2>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          {updatedAt && <span>마지막 갱신 {updatedAt.toLocaleTimeString('ko-KR')}</span>}
          <button onClick={refetch} disabled={loading} className="rounded border px-3 py-1 disabled:opacity-50">
            새로고침
          </button>
        </div>
      </div>

      <div className="h-80 rounded border p-2">
        {loading && !data ? (
          <div role="status" className="flex h-full items-center justify-center text-gray-500">
            시세를 불러오는 중…
          </div>
        ) : error ? (
          <div className="flex h-full flex-col items-center justify-center gap-3">
            <p>시세를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.</p>
            <button onClick={refetch} className="rounded bg-blue-600 px-4 py-1 text-white">다시 시도</button>
          </div>
        ) : !data || data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-gray-500">표시할 종목이 없습니다.</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 30 }}>
              <XAxis dataKey="name" interval={0} angle={-30} textAnchor="end" height={50} tick={{ fontSize: 12 }} />
              <YAxis unit="%" />
              <Tooltip content={<ChartTooltip />} />
              <ReferenceLine y={0} stroke="#374151" />
              <Bar
                dataKey="changePercent"
                cursor="pointer"
                onClick={(d) => {
                  const t = (d.payload as StockQuote).ticker
                  setSelected((cur) => (cur === t ? null : t))
                }}
              >
                {data.map((q) => (
                  <Cell
                    key={q.ticker}
                    fill={colorOf(q.changePercent)}
                    fillOpacity={selected && selected !== q.ticker ? 0.3 : 1}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>

      <div className="rounded border p-3" data-testid="detail">
        {sel ? (
          <div>
            <div className="font-bold">{sel.name} <span className="text-sm text-gray-500">{sel.ticker}</span></div>
            <div>{won(sel.price)}</div>
            <div style={{ color: colorOf(sel.changePercent) }}>
              {arrowOf(sel.changePercent)} {pct(sel.changePercent)}
            </div>
          </div>
        ) : (
          <span className="text-gray-500">종목을 클릭하면 상세 정보가 표시됩니다</span>
        )}
      </div>
      <p className="text-xs text-gray-500">지연 시세일 수 있으며 투자 참고용입니다</p>
    </div>
  )
}

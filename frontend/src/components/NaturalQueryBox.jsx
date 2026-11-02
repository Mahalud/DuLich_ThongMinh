import { useEffect, useRef, useState } from 'react'
import { getTaskStatus, parseNaturalQuery } from '../api'

const EXAMPLES = [
  'đi biển cuối tuần này, ngân sách 3 triệu, trời mát',
  'đi núi ngày mai, ngân sách 5tr, ít mưa',
  'ẩm thực và văn hóa Huế tuần sau, 500k',
]
const WEATHER_LABELS = { balanced: 'Mặc định', cool: 'Mát mẻ', warm: 'Nắng ấm', dry: 'Ít mưa' }

function hasUsefulCriteria(parsed) {
  return Boolean(
    (parsed.preference_labels || []).length || parsed.preference_text?.trim() ||
    parsed.budget_vnd != null || parsed.travel_date || parsed.weather_preference !== 'balanced' ||
    parsed.duration_days != null || parsed.party_size != null || parsed.origin_text,
  )
}

function parsedSummary(parsed) {
  const parts = []
  const preferences = [...(parsed.preference_labels || []), parsed.preference_text].filter(Boolean).join(', ')
  if (preferences) parts.push(`Sở thích: ${preferences}`)
  if (parsed.budget_vnd != null) parts.push(`Ngân sách: ${new Intl.NumberFormat('vi-VN').format(parsed.budget_vnd)}đ`)
  if (parsed.travel_date) {
    const [year, month, day] = parsed.travel_date.split('-')
    parts.push(`Ngày đi: ${day}/${month}/${year}`)
  }
  if (parsed.weather_preference && parsed.weather_preference !== 'balanced') {
    parts.push(`Thời tiết: ${WEATHER_LABELS[parsed.weather_preference] || WEATHER_LABELS.balanced}`)
  }
  if (parsed.duration_days != null) parts.push(`Thời lượng: ${parsed.duration_days} ngày`)
  if (parsed.party_size != null) parts.push(`Số người: ${parsed.party_size}`)
  if (parsed.origin_text) parts.push(`Xuất phát: ${parsed.origin_text}`)
  return parts
}

export default function NaturalQueryBox({ onApply }) {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [understood, setUnderstood] = useState(null)
  const sequenceRef = useRef(0)
  const timersRef = useRef(new Set())

  const clearTimers = () => {
    timersRef.current.forEach((timer) => { window.clearTimeout(timer); window.clearInterval(timer) })
    timersRef.current.clear()
  }

  useEffect(() => () => { sequenceRef.current += 1; clearTimers() }, [])

  const finish = (parsed, requestId) => {
    if (requestId !== sequenceRef.current) return
    sequenceRef.current += 1
    clearTimers()
    setLoading(false)
    if (!parsed || !hasUsefulCriteria(parsed)) {
      setUnderstood(null)
      setMessage('Chưa hiểu câu này, bạn thử câu như ví dụ hoặc điền vào form bên dưới.')
      return
    }
    setMessage('')
    setUnderstood(parsed)
    onApply(parsed)
  }

  const submit = async (event, submittedQuery = query) => {
    event?.preventDefault()
    const cleaned = submittedQuery.trim()
    if (!cleaned || loading) return
    clearTimers()
    const requestId = ++sequenceRef.current
    setLoading(true)
    setMessage('')
    setUnderstood(null)
    let fallback = null
    let response
    try {
      response = await parseNaturalQuery(cleaned.slice(0, 300))
      if (requestId !== sequenceRef.current) return
      fallback = response.fallback
    } catch {
      if (requestId === sequenceRef.current) {
        setLoading(false)
        setMessage('Chưa hiểu câu này, bạn thử câu như ví dụ hoặc điền vào form bên dưới.')
      }
      return
    }

    const deadline = window.setTimeout(() => finish(fallback, requestId), 10_000)
    timersRef.current.add(deadline)
    const poll = async () => {
      if (requestId !== sequenceRef.current) return
      try {
        const status = await getTaskStatus(response.task_id)
        if (requestId !== sequenceRef.current) return
        if (status.status === 'done') finish(status.result, requestId)
        else if (status.status === 'failed') finish(fallback, requestId)
        else {
          const timer = window.setTimeout(poll, 900)
          timersRef.current.add(timer)
        }
      } catch {
        finish(fallback, requestId)
      }
    }
    if (response.task_id) {
      const firstPoll = window.setTimeout(poll, 300)
      timersRef.current.add(firstPoll)
    } else finish(fallback, requestId)
  }

  const fillExample = (example) => {
    setQuery(example)
    submit(null, example)
  }

  return <section className="natural-query-card" aria-label="Tìm kiếm bằng câu tự nhiên">
    <form className="natural-query-form" onSubmit={submit}>
      <label htmlFor="natural-trip-query">Mô tả chuyến đi bằng câu tự nhiên</label>
      <div className="natural-query-controls">
        <input id="natural-trip-query" value={query} maxLength={300} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') submit(event) }} placeholder="Ví dụ: đi biển cuối tuần này, ngân sách 3 triệu, trời mát" />
        <button className="primary-btn" type="submit" disabled={!query.trim() || loading}>Tìm</button>
      </div>
      <div className="natural-query-examples" aria-label="Câu gợi ý mẫu">{EXAMPLES.map((example) => <button type="button" key={example} onClick={() => fillExample(example)} disabled={loading}>{example}</button>)}</div>
    </form>
    {loading && <div className="natural-query-skeleton" aria-hidden="true"><span /><span /></div>}
    {message && <p className="natural-query-message" role="status">{message}</p>}
    {understood && <div className="natural-query-understood" aria-live="polite" role="status">
      <strong>Hệ thống hiểu:</strong> {parsedSummary(understood).map((part, index) => <span className="natural-query-chip" key={`${index}-${part}`}>{part}</span>)}
      {!!understood.notes?.length && <small>{understood.notes.join(' · ')}</small>}
    </div>}
  </section>
}

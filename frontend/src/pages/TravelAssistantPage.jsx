import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUp, Bot, Trash2 } from 'lucide-react'
import { askTravelAssistant, getTravelAssistantTaskStatus } from '../api'

const HISTORY_KEY = 'travel-assistant-messages-v1'
const PROMPTS = [
  'Phú Quốc có những chỗ ở nào?',
  'Tour nào dưới 5 triệu?',
  'Hủy đặt phòng thì hoàn bao nhiêu?',
  'Hệ thống gợi ý dựa trên tiêu chí nào?',
]
const NO_INFORMATION = 'Mình chưa có thông tin về việc này trong hệ thống. Bạn có thể hỏi về điểm đến, tour, chỗ ở hoặc chính sách đặt và hủy.'

function readHistory() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(HISTORY_KEY) || '[]')
    return Array.isArray(saved) ? saved.slice(-10) : []
  } catch {
    return []
  }
}

export default function TravelAssistantPage() {
  const [messages, setMessages] = useState(readHistory)
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef(null)
  const controllerRef = useRef(null)
  const timerRef = useRef(null)
  const sequenceRef = useRef(0)
  const fallbackRef = useRef(null)
  const doneRef = useRef(false)
  const messagesRef = useRef(messages)
  messagesRef.current = messages

  useEffect(() => {
    try { sessionStorage.setItem(HISTORY_KEY, JSON.stringify(messages.slice(-10))) } catch {}
    messagesEndRef.current?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'end' })
  }, [messages, loading])

  useEffect(() => () => {
    sequenceRef.current += 1
    controllerRef.current?.abort()
    window.clearTimeout(timerRef.current)
  }, [])

  const appendMessage = (message) => {
    setMessages((current) => [...current, { id: `${Date.now()}-${Math.random()}`, ...message }].slice(-10))
  }

  const finish = (result, requestId) => {
    if (requestId !== sequenceRef.current || doneRef.current) return
    doneRef.current = true
    window.clearTimeout(timerRef.current)
    controllerRef.current?.abort()
    setLoading(false)
    appendMessage({
      role: 'assistant',
      text: result?.answer || NO_INFORMATION,
      citations: Array.isArray(result?.citations) ? result.citations : [],
    })
  }

  const submit = async (event, presetQuestion = question) => {
    event?.preventDefault()
    const clean = presetQuestion.replace(/[\u0000-\u001f\u007f-\u009f]/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 300)
    if (!clean) return
    controllerRef.current?.abort()
    window.clearTimeout(timerRef.current)
    const requestId = ++sequenceRef.current
    const controller = new AbortController()
    controllerRef.current = controller
    doneRef.current = false
    fallbackRef.current = null
    setError('')
    setQuestion('')
    appendMessage({ role: 'user', text: clean, citations: [] })
    setLoading(true)

    timerRef.current = window.setTimeout(() => {
      finish(fallbackRef.current || { answer: NO_INFORMATION, citations: [] }, requestId)
    }, 12_000)

    const priorUserQuestion = [...messagesRef.current].reverse().find((message) => message.role === 'user')?.text || ''
    try {
      const started = await askTravelAssistant(clean, priorUserQuestion, controller.signal)
      if (requestId !== sequenceRef.current || doneRef.current) return
      fallbackRef.current = started.fallback
      if (!started.task_id) {
        finish(started.fallback, requestId)
        return
      }

      const poll = async () => {
        if (requestId !== sequenceRef.current || doneRef.current) return
        try {
          const status = await getTravelAssistantTaskStatus(started.task_id, controller.signal)
          if (requestId !== sequenceRef.current || doneRef.current) return
          if (status.status === 'done') finish(status.result, requestId)
          else if (status.status === 'failed') finish(started.fallback, requestId)
          else timerRef.current = window.setTimeout(poll, 700)
        } catch {
          if (!controller.signal.aborted) finish(started.fallback, requestId)
        }
      }
      poll()
    } catch (requestError) {
      if (requestId !== sequenceRef.current || controller.signal.aborted) return
      setError(requestError.retryAfterSeconds
        ? `Bạn đã dùng hết lượt hỏi. Hãy thử lại sau ${requestError.retryAfterSeconds} giây.`
        : 'Không gửi được câu hỏi lúc này. Bạn có thể thử lại sau.')
      finish(fallbackRef.current || { answer: NO_INFORMATION, citations: [] }, requestId)
    }
  }

  const clearConversation = () => {
    controllerRef.current?.abort()
    window.clearTimeout(timerRef.current)
    sequenceRef.current += 1
    doneRef.current = true
    setLoading(false)
    setError('')
    setMessages([])
    try { sessionStorage.removeItem(HISTORY_KEY) } catch {}
  }

  return <section className="assistant-page page-shell">
    <header className="assistant-heading"><span className="assistant-heading-icon"><Bot size={22} /></span><div><p className="eyebrow">ĐI VIỆT NAM</p><h1>Trợ lý du lịch</h1><p>Hỏi về điểm đến, tour, chỗ ở và cách sử dụng hệ thống.</p></div></header>

    <section className="assistant-panel" aria-label="Cuộc trò chuyện với trợ lý du lịch">
      <div className="assistant-panel-heading"><div><strong>Hỏi đáp du lịch</strong><span>Trả lời dựa trên dữ liệu công khai của hệ thống</span></div><button type="button" className="assistant-clear-button" onClick={clearConversation} disabled={!messages.length && !loading}><Trash2 size={16} /> Xóa cuộc trò chuyện</button></div>
      <div className="assistant-messages" aria-live="polite" aria-relevant="additions text">
        {!messages.length && <div className="assistant-empty"><Bot size={28} /><p>Bạn muốn tìm hiểu điều gì?</p><span>Chọn câu gợi ý hoặc nhập câu hỏi bên dưới.</span></div>}
        {messages.map((message) => <article className={`assistant-message assistant-message--${message.role}`} key={message.id}>
          <div className="assistant-bubble">{message.text}</div>
          {message.role === 'assistant' && message.citations?.length > 0 && <div className="assistant-citations" aria-label="Nguồn thông tin">{message.citations.map((citation) => citation.url?.startsWith('/')
            ? <Link key={`${message.id}-${citation.n}`} to={citation.url}>[{citation.n}] {citation.title}</Link>
            : <span key={`${message.id}-${citation.n}`}>[{citation.n}] {citation.title}</span>)}</div>}
        </article>)}
        {loading && <div className="assistant-message assistant-message--assistant"><div className="assistant-bubble assistant-typing" aria-label="Đang tìm thông tin"><i /><i /><i /></div></div>}
        <div ref={messagesEndRef} />
      </div>
      {error && <p className="assistant-error" role="status">{error}</p>}
      <div className="assistant-suggestions" aria-label="Câu hỏi gợi ý">{PROMPTS.map((prompt) => <button type="button" key={prompt} onClick={() => submit(null, prompt)} disabled={loading}>{prompt}</button>)}</div>
      <form className="assistant-composer" onSubmit={submit}>
        <label className="sr-only" htmlFor="assistant-question">Câu hỏi của bạn</label>
        <input id="assistant-question" value={question} maxLength={300} onChange={(event) => setQuestion(event.target.value)} placeholder="Nhập câu hỏi về du lịch…" />
        <button className="primary-btn" type="submit" disabled={!question.trim() || loading} aria-label="Gửi câu hỏi"><ArrowUp size={19} /><span>Gửi</span></button>
      </form>
      <p className="assistant-disclaimer">Trả lời tự động dựa trên dữ liệu của hệ thống; thông tin chỗ ở và tour là dữ liệu minh họa phục vụ đồ án.</p>
    </section>
  </section>
}

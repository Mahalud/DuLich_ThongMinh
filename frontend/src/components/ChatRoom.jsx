import { useCallback, useEffect, useRef, useState } from 'react'
import { Paperclip, Send } from 'lucide-react'
import { api } from '../api'
import { useChatConnection } from './ChatConnection'

function ChatComposer({ connection, onSend, onUpload }) {
  const [text, setText] = useState('')
  const connected = connection === 'Đã kết nối'

  const submit = (event) => {
    event.preventDefault()
    const message = text.trim()
    if (!message || !connected) return
    onSend(message)
    setText('')
  }

  return <form className="chat-composer" onSubmit={submit}>
    <label className={`chat-attach-btn ${connected ? '' : 'is-disabled'}`} title="Đính kèm ảnh hoặc PDF" aria-label="Đính kèm ảnh hoặc PDF" aria-disabled={!connected}>
      <Paperclip size={17} aria-hidden="true" />
      <input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" onChange={onUpload} disabled={!connected} />
    </label>
    <input value={text} onChange={(event) => setText(event.target.value)} placeholder="Nhập tin nhắn" aria-label="Nội dung tin nhắn" disabled={!connected} />
    <button className="chat-send-btn" type="submit" aria-label="Gửi tin nhắn" title="Gửi tin nhắn" disabled={!connected || !text.trim()}><Send size={17} aria-hidden="true" /></button>
  </form>
}

export default function ChatRoom({ conversationId, currentUserId, isAdmin = false, compact = false, active = true, onIncomingMessage, onConnectionChange }) {
  const [messages, setMessages] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const bottomRef = useRef(null)
  const conversationIdRef = useRef(conversationId)
  const currentUserIdRef = useRef(currentUserId)
  const activeRef = useRef(active)
  const incomingCallbackRef = useRef(onIncomingMessage)
  const connectionCallbackRef = useRef(onConnectionChange)
  const { connection, sendFrame, markRead, setConversationActive } = useChatConnection()
  conversationIdRef.current = conversationId
  currentUserIdRef.current = currentUserId
  activeRef.current = active
  incomingCallbackRef.current = onIncomingMessage
  connectionCallbackRef.current = onConnectionChange

  const loadHistory = useCallback(async () => {
    if (!conversationId) return
    setLoading(true)
    setError('')
    try {
      const data = await api(`/api/chat/messages/?conversation_user_id=${conversationId}`)
      const history = Array.isArray(data?.results) ? data.results : []
      setMessages((current) => {
        const known = new Set(history.map((item) => item.id))
        return [...history, ...current.filter((item) => !known.has(item.id))]
          .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
      })
      if (activeRef.current && document.visibilityState === 'visible') markRead(conversationId)
    } catch (requestError) {
      setError(requestError.message || 'Chưa tải được lịch sử trò chuyện.')
    } finally {
      setLoading(false)
    }
  }, [conversationId, markRead])

  useEffect(() => {
    setMessages([])
    loadHistory()
  }, [loadHistory])

  useEffect(() => {
    setConversationActive(conversationId, active)
    return () => setConversationActive(conversationId, false)
  }, [conversationId, active, setConversationActive])

  useEffect(() => {
    const onFrame = (event) => {
      const frame = event.detail
      if (!frame || (frame.type !== 'new_message' && !frame.id)) return
      if (Number(frame.conversation_user) !== Number(conversationIdRef.current)) return
      setMessages((current) => current.some((item) => item.id === frame.id) ? current : [...current, frame])
      if (Number(frame.sender) !== Number(currentUserIdRef.current)) {
        incomingCallbackRef.current?.(frame)
        if (activeRef.current && document.visibilityState === 'visible') markRead(conversationIdRef.current)
      }
    }
    window.addEventListener('travel-chat-frame', onFrame)
    return () => window.removeEventListener('travel-chat-frame', onFrame)
  }, [markRead])

  useEffect(() => {
    connectionCallbackRef.current?.(connection)
  }, [connection])

  useEffect(() => {
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    bottomRef.current?.scrollIntoView({ behavior: reducedMotion ? 'auto' : 'smooth', block: 'end' })
  }, [messages])

  const sendMessage = useCallback((message) => {
    const sent = sendFrame({ type: 'message', message, ...(isAdmin ? { conversation_id: conversationIdRef.current } : {}) })
    if (!sent) setError('Chưa gửi được tin nhắn. Đang kết nối lại…')
    else setError('')
  }, [sendFrame, isAdmin])

  const upload = useCallback(async (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const body = new FormData()
    body.append('file', file)
    body.append('conversation_user_id', conversationIdRef.current)
    try {
      const data = await api('/api/chat/upload/', { method: 'POST', body })
      const sent = sendFrame({
        type: 'message', message: '', attachment_url: data.attachment_url,
        attachment_type: data.attachment_type,
        ...(isAdmin ? { conversation_id: conversationIdRef.current } : {}),
      })
      if (!sent) setError('Tệp đã tải lên nhưng chưa gửi được. Đang kết nối lại…')
    } catch (requestError) {
      setError(requestError.message || 'Không tải được tệp đính kèm.')
    }
  }, [sendFrame, isAdmin])

  return <div className={`chat-room ${compact ? 'chat-room-compact' : ''}`}>
    {!compact && <div className="chat-room-status" role="status"><span className={`chat-status-dot ${connection === 'Đã kết nối' ? 'is-online' : connection === 'Mất kết nối' ? 'is-offline' : ''}`} />{connection}</div>}
    <div className="chat-box" aria-live="polite">
      {loading ? <div className="chat-skeleton"><span /><span /><span /></div> : messages.length ? messages.map((item) => <article className={`chat-message ${Number(item.sender) === Number(currentUserId) ? 'mine' : ''}`} key={item.id}>
        <strong>{Number(item.sender) === Number(currentUserId) ? 'Bạn' : (item.sender_name || (item.is_from_admin ? 'Quản trị viên' : 'Người dùng'))}</strong>
        {item.content && <p>{item.content}</p>}
        {item.attachment_url && (item.attachment_type === 'image' ? <img className="chat-attachment-image" src={item.attachment_url} alt="Tệp ảnh đính kèm" /> : <a href={item.attachment_url} target="_blank" rel="noreferrer">Mở tệp PDF</a>)}
        <small>{new Date(item.created_at).toLocaleString('vi-VN')}</small>
      </article>) : <div className="chat-empty"><strong>{isAdmin ? 'Chưa có tin nhắn' : 'Xin chào!'}</strong><p>{isAdmin ? 'Tin nhắn mới sẽ xuất hiện tại đây.' : 'Hãy gửi lời nhắn nếu bạn cần hỗ trợ.'}</p></div>}
      <div ref={bottomRef} />
    </div>
    {error && <p className="form-error" role="status">{error}</p>}
    <ChatComposer connection={connection} onSend={sendMessage} onUpload={upload} />
  </div>
}

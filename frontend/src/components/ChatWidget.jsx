import { useEffect, useState } from 'react'
import { Headphones, MessageCircle, Volume2, VolumeX, X } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'
import ChatRoom from './ChatRoom'
import { useChatConnection } from './ChatConnection'

const CHAT_OPEN_KEY = 'travel-chat-open'

export default function ChatWidget({ user, authStatus = 'loading', authError = '', onRetryAuth }) {
  const [open, setOpen] = useState(() => localStorage.getItem(CHAT_OPEN_KEY) === 'true')
  const location = useLocation()
  const { connection, unreadCount, soundEnabled, toggleSound } = useChatConnection()

  useEffect(() => {
    localStorage.setItem(CHAT_OPEN_KEY, String(open))
    window.dispatchEvent(new CustomEvent('travel-chat-open-change', { detail: { open } }))
  }, [open])

  useEffect(() => {
    const closeOnEscape = (event) => {
      if (event.key === 'Escape') setOpen(false)
    }
    window.addEventListener('keydown', closeOnEscape)
    return () => window.removeEventListener('keydown', closeOnEscape)
  }, [])

  if (location.pathname.startsWith('/quan-tri') || location.pathname === '/chat' || user?.is_staff || user?.is_superuser) return null

  return <div className={`chat-widget ${open ? 'is-open' : ''}`}>
    <section className={`profile-panel chat-page ${open ? '' : 'is-closed'}`} aria-label="Trò chuyện hỗ trợ" aria-hidden={!open}>
      <header className="chat-widget-header">
        <div className="chat-title-line">
          <span className="chat-title-icon"><Headphones size={17} aria-hidden="true" /></span>
          <strong>Hỗ trợ trực tuyến</strong>
      <span className="chat-title-status" role="status"><span className={`chat-status-dot ${authStatus === 'authenticated' && connection === 'Đã kết nối' ? 'is-online' : authStatus === 'anonymous' || connection === 'Mất kết nối' ? 'is-offline' : ''}`} />{authStatus === 'loading' ? 'Đang kiểm tra phiên' : authStatus === 'authenticated' ? connection : 'Đăng nhập để trò chuyện'}</span>
        </div>
        <div className="chat-widget-actions">
          <button className="chat-close" type="button" aria-label={soundEnabled ? 'Tắt âm báo tin nhắn' : 'Bật âm báo tin nhắn'} aria-pressed={soundEnabled} onClick={toggleSound}>{soundEnabled ? <Volume2 size={17} aria-hidden="true" /> : <VolumeX size={17} aria-hidden="true" />}</button>
          <button className="chat-close" type="button" aria-label="Đóng cửa sổ trò chuyện" onClick={() => setOpen(false)}><X size={18} aria-hidden="true" /></button>
        </div>
      </header>
      {authStatus === 'authenticated' && user ? <ChatRoom conversationId={user.id} currentUserId={user.id} compact active={open} /> : authStatus === 'loading' ? <div className="chat-empty"><strong>{authError ? 'Không kết nối được máy chủ' : 'Đang kiểm tra phiên đăng nhập'}</strong>{authError && <p>{authError}</p>}{authError && onRetryAuth && <button className="travel-button travel-button--outline" type="button" onClick={onRetryAuth}>Thử lại</button>}</div> : <div className="chat-empty"><strong>Đăng nhập để trò chuyện</strong><p>Lịch sử hỗ trợ sẽ được lưu cùng tài khoản của bạn.</p><Link className="primary-btn" to="/dang-nhap" onClick={() => setOpen(false)}>Đăng nhập</Link></div>}
    </section>
    {!open && <button className="chat-launcher" type="button" aria-expanded="false" aria-label="Mở trò chuyện hỗ trợ" onClick={() => setOpen(true)}>
      <MessageCircle size={22} aria-hidden="true" />
      {unreadCount > 0 && <span className="chat-launcher-unread" aria-label={`${unreadCount} tin nhắn chưa đọc`}>{unreadCount > 99 ? '99+' : unreadCount}</span>}
    </button>}
  </div>
}

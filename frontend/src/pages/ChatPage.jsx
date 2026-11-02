import ChatRoom from '../components/ChatRoom'
import { useAuth } from '../auth'

export default function ChatPage() {
  const { user } = useAuth()
  return <section className="profile-panel chat-page chat-page-standalone">
    <div className="section-head"><span className="eyebrow dark">Hỗ trợ trực tuyến</span><h1>Trò chuyện cùng chúng tôi</h1><p>Chúng tôi sẵn sàng hỗ trợ bạn lên kế hoạch cho chuyến đi.</p></div>
    {user ? <ChatRoom conversationId={user.id} currentUserId={user.id} /> : <div className="chat-empty"><strong>Đăng nhập để trò chuyện</strong><p>Lịch sử hỗ trợ sẽ được lưu cùng tài khoản của bạn.</p><a className="primary-btn" href="/dang-nhap">Đăng nhập</a></div>}
  </section>
}

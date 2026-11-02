import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api, getWeather } from '../api'
import { useAuth } from '../auth'
import { useOrigin } from '../origin'

export function WeatherPage() {
  const { originLocation } = useOrigin()
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  useEffect(() => {
    if (!originLocation) { setData(null); setLoading(false); return undefined }
    let active = true
    setLoading(true); setError('')
    const today = new Date().toISOString().slice(0, 10)
    getWeather(originLocation, today).then((result) => { if (active) setData(result) }).catch(() => { if (active) setError('Chưa thể tải dự báo thời tiết. Vui lòng thử lại sau.') }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [originLocation])
  return <section className="profile-panel"><div className="section-head"><span className="eyebrow dark">Dự báo hành trình</span><h1>Thời tiết chuyến đi</h1>{originLocation && <p>Vị trí xuất phát: {originLocation.name}</p>}</div>{!originLocation ? <div className="empty-state"><h2>Chưa chọn vị trí xuất phát</h2><p>Chọn nơi bạn đang ở để xem thông tin thời tiết.</p><Link className="primary-btn" to="/goi-y">Chọn vị trí xuất phát</Link></div> : loading ? <div className="profile-skeleton" aria-label="Đang tải thời tiết"><span /><span /><span /></div> : error ? <div className="empty-state"><h2>Chưa có dữ liệu thời tiết</h2><p>{error}</p></div> : <div className="mini-card card-main"><h3>{data?.temperature ?? '--'}°C</h3><p>Khả năng mưa: {data?.precipitation_probability ?? '--'}%</p><strong>Điểm thời tiết: {data?.weather_score ?? '--'}</strong></div>}</section>
}

export function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState([]); const [input, setInput] = useState(''); const [status, setStatus] = useState(''); const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!user) { setMessages([]); setLoading(false); return }
    setLoading(true)
    api(`/api/chat/messages/?user_id=${user.id}&receiver_id=1`).then(setMessages).catch(() => setStatus('Chưa thể tải cuộc trò chuyện. Vui lòng thử tải lại trang.')).finally(() => setLoading(false))
  }, [user?.id])
  return <section className="profile-panel chat-page"><div className="section-head"><span className="eyebrow dark">Hỗ trợ trực tuyến</span><h1>Trò chuyện cùng chúng tôi</h1><p>Chúng tôi sẵn sàng hỗ trợ bạn lên kế hoạch cho chuyến đi.</p></div><div className="chat-box" aria-live="polite">{loading ? <div className="chat-skeleton"><span /><span /><span /></div> : messages.length ? messages.map((item) => <div className="chat-message" key={item.id}><strong>{item.sender}</strong><p>{item.content}</p></div>) : <div className="chat-empty"><strong>Xin chào!</strong><p>Chưa có tin nhắn nào. Hãy gửi lời nhắn nếu bạn cần hỗ trợ.</p></div>}</div><form className="inline-group chat-composer" onSubmit={(event) => { event.preventDefault(); setStatus('Kết nối gửi tin nhắn thời gian thực chưa sẵn sàng. Vui lòng thử lại sau.'); setInput('') }}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Nhập tin nhắn của bạn" aria-label="Nội dung tin nhắn" /><button className="primary-btn" type="submit">Gửi tin nhắn</button></form>{status && <p className="form-error" role="status">{status}</p>}</section>
}

export function ReviewsPage() {
  const [reviews, setReviews] = useState([]); const [loading, setLoading] = useState(true); const [error, setError] = useState('')
  useEffect(() => { api('/api/reviews/').then(setReviews).catch(() => setError('Chưa thể tải đánh giá. Vui lòng thử lại sau.')).finally(() => setLoading(false)) }, [])
  return <section className="profile-panel"><div className="section-head"><span className="eyebrow dark">Cộng đồng</span><h1>Đánh giá chỗ ở</h1><p>Nhận xét từ những người đã trải nghiệm các điểm lưu trú.</p></div>{loading ? <div className="profile-skeleton" aria-label="Đang tải đánh giá"><span /><span /><span /></div> : error ? <div className="empty-state"><h2>Đánh giá chưa tải được</h2><p>{error}</p></div> : <div className="admin-list">{reviews.length ? reviews.map((review) => <article className="list-item review-item" key={review.id}><strong>{review.rating} / 5 sao</strong><p>{review.comment}</p><p><span>{review.user_name}</span>{review.user_is_demo && <span className="demo-badge">Minh họa</span>}</p></article>) : <div className="empty-state"><h2>Chưa có đánh giá</h2><p>Các nhận xét về chỗ ở sẽ được chia sẻ tại đây.</p></div>}</div>}</section>
}

export function PaymentReturnPage() {
  const [query] = useSearchParams()
  const simulated = query.get('provider') === 'simulated'
  const vnpay = query.get('provider') === 'vnpay'
  const success = query.get('status') === 'success'
  const title = simulated
    ? (success ? 'Thanh toán mô phỏng thành công' : 'Thanh toán mô phỏng thất bại')
    : vnpay
      ? (success ? 'Thanh toán VNPay thành công' : 'Thanh toán VNPay chưa thành công')
      : 'Đã nhận kết quả thanh toán'
  const description = simulated
    ? 'Đây là kết quả mô phỏng, không phát sinh giao dịch thật. Bạn có thể kiểm tra trạng thái đơn trong tài khoản.'
    : vnpay
      ? (success ? 'VNPay đã xác nhận giao dịch sandbox. Trạng thái đơn đã được cập nhật.' : 'Giao dịch sandbox chưa được xác nhận. Bạn có thể thử thanh toán lại trong hồ sơ.')
      : 'Hệ thống đã tiếp nhận kết quả từ cổng thanh toán. Bạn có thể kiểm tra trạng thái đơn trong tài khoản.'
  return <section className="auth-page payment-result-page"><div className="auth-card thanks-card"><div className="payment-result-mark" aria-hidden="true">{success ? '✓' : '!'}</div><span className="eyebrow dark">{simulated ? 'Thanh toán mô phỏng' : vnpay ? 'VNPay Sandbox' : 'Thanh toán thử nghiệm'}</span><h1>{title}</h1><p>{description}</p><Link className="primary-btn" to="/ho-so">Về hồ sơ của tôi</Link></div></section>
}

export function SimulatedPaymentPage() {
  const [query] = useSearchParams()
  const navigate = useNavigate()
  const order = query.get('order') || ''
  const [booking, setBooking] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    api('/api/payments/simulated/complete/').then(() => api('/api/my-bookings/')).then((data) => {
      const match = /^(BOOK|TOUR)-(\d+)$/.exec(order)
      if (!match) throw new Error('Mã đơn thanh toán không hợp lệ.')
      const isTour = match[1] === 'TOUR'
      const list = isTour ? data.tour_bookings : data.room_bookings
      const item = (Array.isArray(list) ? list : []).find((entry) => String(entry.id) === match[2])
      if (!item) throw new Error('Không tìm thấy thông tin đơn trong tài khoản này.')
      if (active) setBooking({ ...item, kind: isTour ? 'tour' : 'room' })
    }).catch((loadError) => { if (active) setError(loadError.message || 'Chưa tải được thông tin đơn.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [order])

  const complete = async (result) => {
    setBusy(true); setError('')
    try {
      const response = await api('/api/payments/simulated/complete/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ order, result }),
      })
      navigate('/payment-return?provider=simulated&status=' + (response.success ? 'success' : 'failed') + '&order=' + encodeURIComponent(order), { replace: true })
    } catch (completeError) {
      setError(completeError.message || 'Chưa ghi nhận được kết quả mô phỏng.')
      setBusy(false)
    }
  }

  const title = booking?.kind === 'tour' ? booking.tour_name : booking ? booking.accommodation_name + ' · ' + booking.room_type_name : ''
  const amount = booking?.total_price
  return <section className="auth-page payment-result-page simulated-payment-page">
    <div className="auth-card thanks-card simulated-payment-card">
      <span className="eyebrow dark">Thanh toán dự phòng</span><h1>Hoàn tất thanh toán</h1>
      <div className="simulated-payment-warning" role="note">Chế độ thanh toán mô phỏng, không phải giao dịch thật</div>
      {loading ? <div className="profile-skeleton" aria-label="Đang tải đơn"><span /><span /></div> : error && !booking ? <div className="empty-state" role="alert"><p>{error}</p><Link to="/ho-so">Về hồ sơ</Link></div> : booking && <>
        <div className="booking-summary simulated-payment-summary"><strong>{title}</strong><p>Mã đơn: {order}</p><p>Số tiền: <strong>{Number(amount || 0).toLocaleString('vi-VN')} đ</strong></p></div>
        <p>Chọn kết quả để tiếp tục bản demo.</p>
        <div className="simulated-payment-actions"><button className="primary-btn" type="button" disabled={busy || booking.status === 'cancelled'} onClick={() => complete('success')}>{busy ? 'Đang xử lý…' : 'Thanh toán thành công'}</button><button className="travel-button travel-button--outline" type="button" disabled={busy || booking.status === 'cancelled'} onClick={() => complete('failed')}>Thanh toán thất bại</button></div>
        {error && <p className="form-error" role="alert">{error}</p>}
      </>}
    </div>
  </section>
}

import { useEffect, useMemo, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { api, getAmenities } from '../api'
import { amenityIcon, amenityLabel, setAmenityCatalog } from '../amenityIcons'
import { SectionSkeleton } from '../components/DesignSystem'
import { useAuth } from '../auth'

const localDate = () => {
  const now = new Date()
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}
const formatMoney = (value) => `${Number(value || 0).toLocaleString('vi-VN')} đ`

export default function BookingPage() {
  const { user, status: authStatus } = useAuth()
  const { roomTypeId } = useParams()
  const location = useLocation()
  const accommodationId = new URLSearchParams(location.search).get('accommodation')
  const [room, setRoom] = useState(null)
  const [loadingRoom, setLoadingRoom] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [retryKey, setRetryKey] = useState(0)
  const [form, setForm] = useState({ check_in: localDate(), check_out: '', guest_phone: '' })
  const [message, setMessage] = useState('')
  const [createdBooking, setCreatedBooking] = useState(null)
  const [paymentProvider, setPaymentProvider] = useState('vnpay')
  const [loading, setLoading] = useState(false)
  const amenities = room?.amenities || []
  const price = Number(room?.base_price || 0)

  useEffect(() => {
    let active = true
    setLoadingRoom(true)
    setLoadError('')
    api(`/api/room-types/${roomTypeId}/`).then((roomData) => {
      if (!active) return
      setRoom(roomData)
      getAmenities().then(setAmenityCatalog).catch(() => {})
    }).catch((error) => {
      if (active) {
        setRoom(null)
        setLoadError(error.message || 'Không tải được thông tin phòng. Vui lòng thử lại.')
      }
    }).finally(() => {
      if (active) setLoadingRoom(false)
    })
    return () => { active = false }
  }, [roomTypeId, retryKey])

  const nights = useMemo(() => {
    if (!form.check_in || !form.check_out) return 0
    return Math.max(0, Math.round((new Date(`${form.check_out}T00:00:00`) - new Date(`${form.check_in}T00:00:00`)) / 86400000))
  }, [form.check_in, form.check_out])
  const total = price * nights
  const returnPath = `${location.pathname}${location.search}`
  const loginUrl = `/dang-nhap?next=${encodeURIComponent(returnPath)}`

  const submit = async (event) => {
    event.preventDefault()
    if (!room) return setMessage('Không tìm thấy thông tin phòng. Vui lòng chọn lại từ trang chỗ ở.')
    if (nights < 1) return setMessage('Ngày trả phải sau ngày nhận ít nhất một đêm.')
    setLoading(true)
    setMessage('')
    try {
      const booking = await api('/api/bookings/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ room_type: room.id, ...form }),
      })
      setCreatedBooking(booking)
    } catch (error) {
      setMessage(error.message)
    } finally {
      setLoading(false)
    }
  }

  const pay = async () => {
    setLoading(true)
    setMessage('')
    try {
      const payment = await api('/api/payments/init/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ booking_id: createdBooking.id, provider: paymentProvider, amount: total, return_url: `${window.location.origin}/payment-return` }),
      })
      window.location.href = payment.redirect_url
    } catch (error) {
      setMessage(error.message)
      setLoading(false)
    }
  }

  if (authStatus === 'loading' || loadingRoom) {
    return <section className="auth-page"><div className="auth-card booking-card"><h1>Đang tải thông tin đặt phòng…</h1><SectionSkeleton count={1} /></div></section>
  }

  if (loadError || !room) {
    return <section className="auth-page"><div className="auth-card booking-card"><h1>Không tải được phòng</h1><p className="form-error" role="alert">{loadError || 'Không tìm thấy thông tin phòng.'}</p><div className="form-actions"><button className="primary-btn" type="button" onClick={() => setRetryKey((key) => key + 1)}>Thử tải lại</button>{accommodationId && <Link className="travel-button travel-button--outline" to={`/cho-o/${accommodationId}`}>Quay lại chỗ ở</Link>}</div></div></section>
  }

  if (!user) {
    return <section className="auth-page"><div className="auth-card booking-card"><h1>Đăng nhập để tiếp tục đặt phòng</h1><p>Bạn cần đăng nhập để tạo đơn. Sau khi đăng nhập, hệ thống sẽ quay lại đúng phòng đang chọn.</p><Link className="primary-btn" to={loginUrl}>Đăng nhập</Link>{room.accommodation && <p><Link to={`/cho-o/${room.accommodation}`}>Quay lại {room.accommodation_name}</Link></p>}</div></section>
  }

  return <section className="auth-page"><div className="auth-card booking-card"><span className="eyebrow dark">Thanh toán sandbox</span><h1>Xác nhận đặt phòng</h1><div className="booking-summary"><strong>{room.accommodation_name}</strong><span>{room.name}</span><p>{formatMoney(price)} / đêm</p>{amenities.length > 0 && <div className="amenity-list" aria-label="Tiện ích phòng">{amenities.map((key) => <span className="amenity-icon" title={amenityLabel(key)} aria-label={amenityLabel(key)} key={key}>{amenityIcon(key)}</span>)}</div>}</div><form className="admin-form" onSubmit={submit}><label>Ngày nhận<input type="date" min={localDate()} required value={form.check_in} onChange={(event) => setForm({ ...form, check_in: event.target.value })} /></label><label>Ngày trả<input type="date" min={form.check_in || localDate()} required value={form.check_out} onChange={(event) => setForm({ ...form, check_out: event.target.value })} /></label><label>Số điện thoại<input type="tel" required value={form.guest_phone} onChange={(event) => setForm({ ...form, guest_phone: event.target.value })} /></label><div className="booking-total"><span>{nights} đêm</span><strong>Tổng cộng: {formatMoney(total)}</strong></div><button className="primary-btn" disabled={loading || !!createdBooking}>{loading ? 'Đang xử lý…' : createdBooking ? 'Đơn đã được tạo' : 'Đặt phòng'}</button></form>{createdBooking && <div className="booking-confirmation"><p>Đơn đặt phòng đã được tạo. Số tiền cần thanh toán: <strong>{formatMoney(total)}</strong>.</p><fieldset className="payment-provider-choice"><legend>Chọn cổng thanh toán</legend><label><input type="radio" name="room-payment-provider" value="vnpay" checked={paymentProvider === 'vnpay'} onChange={() => setPaymentProvider('vnpay')} /> VNPay Sandbox</label><label><input type="radio" name="room-payment-provider" value="momo" checked={paymentProvider === 'momo'} onChange={() => setPaymentProvider('momo')} /> MoMo Sandbox</label></fieldset><button className="primary-btn" disabled={loading} onClick={pay}>{loading ? 'Đang chuyển cổng thanh toán…' : `Tiếp tục với ${paymentProvider === 'vnpay' ? 'VNPay' : 'MoMo'}`}</button></div>}{message && <p className="form-error" role="alert">{message}</p>}</div></section>
}

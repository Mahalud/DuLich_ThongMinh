import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { useAuth } from '../auth'
import { PasswordField, PasswordHint } from './AuthPages'
import { PreferenceChips, WeatherPreferenceChips } from '../components/RecommendationForm'

const safeList = (value) => Array.isArray(value) ? value : []
const localDate = () => {
  const date = new Date()
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}
const asLocalDate = (value) => {
  if (!value) return null
  const [year, month, day] = String(value).slice(0, 10).split('-').map(Number)
  return year && month && day ? new Date(year, month - 1, day) : null
}
const formatDate = (value) => asLocalDate(value)?.toLocaleDateString('vi-VN') || '—'
const formatDateTime = (value) => value ? new Date(value).toLocaleString('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh', day: '2-digit', month: '2-digit', year: 'numeric',
  hour: '2-digit', minute: '2-digit', hour12: false,
}) : '—'
const formatMoney = (value) => `${Number(value || 0).toLocaleString('vi-VN')} đ`
const weatherLabels = { balanced: 'Mặc định', cool: 'Mát mẻ', warm: 'Nắng ấm', dry: 'Ít mưa' }
const statusLabel = (status) => ({ pending: 'Chờ thanh toán', confirmed: 'Đã xác nhận', cancelled: 'Đã hủy' }[status] || 'Không rõ')
const refundLabel = (status, isSimulated = false) => {
  if (status === 'refunded' && isSimulated) return 'Hoàn tiền mô phỏng'
  return ({ none: 'Chưa phát sinh hoàn tiền', pending: 'Đang xử lý hoàn tiền', refunded: 'Đã hoàn tiền', failed: 'Hoàn tiền chưa thành công' }[status] || 'Chưa có thông tin hoàn tiền')
}

function replaySearchUrl(item) {
  const params = new URLSearchParams()
  if (item.preferences) params.set('user_preferences', item.preferences)
  if (item.budget_estimate) params.set('budget_estimate', item.budget_estimate)
  if (item.latitude != null) params.set('latitude', item.latitude)
  if (item.longitude != null) params.set('longitude', item.longitude)
  if (item.travel_date) params.set('travel_date', item.travel_date)
  if (item.top_n) params.set('top_n', item.top_n)
  if (item.weather_preference) params.set('weather_preference', item.weather_preference)
  return `/goi-y?${params.toString()}`
}

export default function ProfilePage() {
  const { user, setUser } = useAuth()
  const [account, setAccount] = useState({ display_name: '', email: '', current_password: '' })
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', new_password_confirm: '' })
  const [accountBusy, setAccountBusy] = useState(false)
  const [passwordBusy, setPasswordBusy] = useState(false)
  const [accountError, setAccountError] = useState('')
  const [accountNotice, setAccountNotice] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [profile, setProfile] = useState({ travel_preferences: [], budget_estimate: '', weather_preference: 'balanced', free_text: '' })
  const [bookings, setBookings] = useState({ room_bookings: [], tour_bookings: [] })
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('room')
  const [filter, setFilter] = useState('all')
  const [cancelTarget, setCancelTarget] = useState(null)
  const [cancelBusy, setCancelBusy] = useState(false)
  const [payingId, setPayingId] = useState(null)

  const load = useCallback(async () => {
    if (!user?.id) return
    setLoading(true)
    setError('')
    try {
      const [profileData, bookingData, historyData] = await Promise.all([
        api(`/api/profile/${user.id}/`), api('/api/my-bookings/'), api('/api/search-history/'),
      ])
      setProfile({
        travel_preferences: safeList(profileData.travel_preferences),
        budget_estimate: profileData.budget_estimate ?? '',
        weather_preference: profileData.weather_preference || 'balanced',
        free_text: profileData.free_text ?? '',
      })
      setAccount({ display_name: profileData.display_name || profileData.username || '', email: profileData.email || '', current_password: '' })
      setBookings({
        room_bookings: safeList(bookingData.room_bookings),
        tour_bookings: safeList(bookingData.tour_bookings),
      })
      setHistory(safeList(historyData).sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
    } catch (loadError) {
      setError(loadError.message || 'Chưa tải được thông tin hồ sơ. Vui lòng thử lại.')
    } finally { setLoading(false) }
  }, [user?.id])

  useEffect(() => { load() }, [load])

  const allBookings = useMemo(() => [
    ...safeList(bookings.room_bookings).map((item) => ({ ...item, kind: 'room' })),
    ...safeList(bookings.tour_bookings).map((item) => ({ ...item, kind: 'tour' })),
  ].sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0)), [bookings])

  const visibleBookings = useMemo(() => allBookings.filter((item) => {
    if (item.kind !== activeTab) return false
    const journeyDate = asLocalDate(item.kind === 'room' ? item.check_in : item.departure_date)
    if (filter === 'cancelled') return item.status === 'cancelled'
    if (filter === 'upcoming') return item.status !== 'cancelled' && journeyDate && journeyDate >= asLocalDate(localDate())
    if (filter === 'past') return item.status !== 'cancelled' && journeyDate && journeyDate < asLocalDate(localDate())
    return true
  }), [allBookings, activeTab, filter])

  const saveProfile = async (event) => {
    event.preventDefault()
    if (!user?.id) return
    setSaving(true); setNotice(''); setError('')
    try {
      const updated = await api(`/api/profile/${user.id}/`, {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          travel_preferences: String(profile.travel_preferences || []).split(',').map((x) => x.trim()).filter(Boolean),
          budget_estimate: profile.budget_estimate, weather_preference: profile.weather_preference,
          free_text: profile.free_text,
        }),
      })
      setProfile({ travel_preferences: safeList(updated.travel_preferences), budget_estimate: updated.budget_estimate ?? '', weather_preference: updated.weather_preference || 'balanced', free_text: updated.free_text ?? '' })
      setNotice('Đã lưu hồ sơ của bạn.')
    } catch (saveError) { setError(saveError.message || 'Chưa lưu được hồ sơ.') }
    finally { setSaving(false) }
  }

  const saveAccount = async (event) => {
    event.preventDefault()
    setAccountBusy(true); setAccountError(''); setAccountNotice(''); setNotice('')
    try {
      const updated = await api('/api/auth/account/', {
        method: 'PATCH', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(account),
      })
      setAccount({ display_name: updated.display_name, email: updated.email, current_password: '' })
      setUser({ ...user, ...updated })
      setAccountNotice('Đã cập nhật thông tin tài khoản.')
    } catch (saveError) { setAccountError(saveError.message || 'Chưa cập nhật được tài khoản.') }
    finally { setAccountBusy(false) }
  }

  const savePassword = async (event) => {
    event.preventDefault()
    setPasswordError(''); setNotice('')
    if (passwordForm.new_password !== passwordForm.new_password_confirm) {
      setPasswordError('Hai mật khẩu mới chưa khớp.')
      return
    }
    setPasswordBusy(true)
    try {
      const result = await api('/api/auth/change-password/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(passwordForm),
      })
      setPasswordForm({ current_password: '', new_password: '', new_password_confirm: '' })
      setNotice(result.message || 'Đã đổi mật khẩu.')
    } catch (saveError) { setPasswordError(saveError.message || 'Chưa đổi được mật khẩu.') }
    finally { setPasswordBusy(false) }
  }

  const startPayment = async (item, provider) => {
    setPayingId(`${item.kind}-${item.id}`); setError('')
    try {
      const result = await api('/api/payments/init/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          booking_id: item.id,
          provider,
          booking_type: item.kind === 'tour' ? 'tour_booking' : 'accommodation_booking',
          return_url: `${window.location.origin}/payment-return`,
        }),
      })
      if (result.redirect_url) window.location.href = result.redirect_url
      else throw new Error('Chưa nhận được liên kết thanh toán. Vui lòng thử lại.')
    } catch (payError) { setError(payError.message || 'Chưa khởi tạo được thanh toán.') }
    finally { setPayingId(null) }
  }

  const cancelBooking = async () => {
    if (!cancelTarget) return
    setCancelBusy(true); setError('')
    try {
      const path = cancelTarget.kind === 'tour' ? `/api/tour-bookings/${cancelTarget.id}/cancel/` : `/api/bookings/${cancelTarget.id}/cancel/`
      const result = await api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({}) })
      const bucket = cancelTarget.kind === 'tour' ? 'tour_bookings' : 'room_bookings'
      setBookings((current) => ({
        ...current,
        [bucket]: safeList(current[bucket]).map((item) => item.id === cancelTarget.id ? {
          ...item, status: 'cancelled', refund_amount: result.refund_amount,
          refund_status: result.refund_status,
          refund_preview: { ...item.refund_preview, can_cancel: false, refund_amount: result.refund_amount, message: 'Đơn đã được hủy.' },
        } : item),
      }))
      setNotice(`Đơn #${cancelTarget.id} đã được hủy. Khoản hoàn: ${formatMoney(result.refund_amount)} (${refundLabel(result.refund_status)}).`)
      setCancelTarget(null)
    } catch (cancelError) { setError(cancelError.message || 'Chưa hủy được đơn. Vui lòng thử lại.') }
    finally { setCancelBusy(false) }
  }

  if (loading) return <section className="profile-page"><div className="profile-skeleton" aria-label="Đang tải hồ sơ"><span /><span /><span /><span /></div></section>

  return <section className="profile-page">
    <div className="section-head"><span className="eyebrow dark">Tài khoản của bạn</span><h1>Hồ sơ cá nhân</h1><p>Xin chào {account.display_name || user?.username || ''}. Quản lý sở thích và các hành trình đã đặt.</p></div>
    {error && <div className="profile-alert profile-alert--error" role="alert">{error}<button type="button" onClick={load}>Thử lại</button></div>}
    {notice && <div className="profile-alert" role="status">{notice}</div>}

    <form className="profile-form profile-account-form" onSubmit={saveAccount}>
      <div className="profile-section-title"><h2>Thông tin tài khoản</h2><p>Đổi email cần nhập mật khẩu hiện tại.</p></div>
      <label>Tên hiển thị<input required maxLength="150" autoComplete="name" value={account.display_name} onChange={(event) => setAccount({ ...account, display_name: event.target.value })} /></label>
      <label>Email<input required type="email" autoComplete="email" value={account.email} onChange={(event) => setAccount({ ...account, email: event.target.value })} /></label>
      <div className="profile-password-field"><PasswordField id="account-current-password" label="Mật khẩu hiện tại (khi đổi email)" autoComplete="current-password" required={false} value={account.current_password} onChange={(current_password) => setAccount({ ...account, current_password })} /><small>Chỉ cần nhập mật khẩu hiện tại khi bạn thay đổi email.</small></div>
      <button className="primary-btn" type="submit" disabled={accountBusy}>{accountBusy ? 'Đang lưu…' : 'Lưu thông tin tài khoản'}</button>
      {accountError && <p className="form-error profile-form-feedback" role="alert">{accountError}</p>}
      {accountNotice && <p className="admin-message profile-form-feedback" role="status">{accountNotice}</p>}
    </form>

    <form className="profile-form profile-security-form" onSubmit={savePassword}>
      <div className="profile-section-title"><h2>Bảo mật tài khoản</h2><p>Đổi mật khẩu sẽ giữ phiên hiện tại và kết thúc các phiên đăng nhập khác.</p></div>
      <PasswordField id="change-current-password" label="Mật khẩu hiện tại" autoComplete="current-password" value={passwordForm.current_password} onChange={(current_password) => setPasswordForm({ ...passwordForm, current_password })} />
      <PasswordField id="change-new-password" label="Mật khẩu mới" value={passwordForm.new_password} onChange={(new_password) => setPasswordForm({ ...passwordForm, new_password })} />
      <PasswordHint password={passwordForm.new_password} />
      <PasswordField id="change-confirm-password" label="Nhập lại mật khẩu mới" value={passwordForm.new_password_confirm} onChange={(new_password_confirm) => setPasswordForm({ ...passwordForm, new_password_confirm })} />
      {passwordError && <p className="form-error" role="alert">{passwordError}</p>}
      <button className="primary-btn" type="submit" disabled={passwordBusy}>{passwordBusy ? 'Đang đổi…' : 'Đổi mật khẩu'}</button>
    </form>

    <form className="profile-form" onSubmit={saveProfile}>
      <div className="profile-section-title"><h2>Sở thích và ngân sách</h2></div>
      <div className="profile-preference-field"><label htmlFor="profile-preferences">Sở thích du lịch</label><input id="profile-preferences" value={Array.isArray(profile.travel_preferences) ? profile.travel_preferences.join(', ') : profile.travel_preferences} onChange={(event) => setProfile({ ...profile, travel_preferences: event.target.value })} placeholder="Biển, ẩm thực, văn hóa" /><PreferenceChips value={Array.isArray(profile.travel_preferences) ? profile.travel_preferences.join(', ') : profile.travel_preferences} onChange={(travel_preferences) => setProfile({ ...profile, travel_preferences })} /></div>
      <label className="profile-budget-field">Ngân sách dự kiến<div className="profile-money-control"><input type="text" inputMode="numeric" value={profile.budget_estimate === '' ? '' : Number(String(profile.budget_estimate).replace(/\D/g, '') || 0).toLocaleString('vi-VN')} onChange={(event) => setProfile({ ...profile, budget_estimate: event.target.value.replace(/\D/g, '') })} placeholder="Ví dụ: 6.000.000" /><span>đ</span></div></label>
      <WeatherPreferenceChips value={profile.weather_preference} onChange={(weather_preference) => setProfile({ ...profile, weather_preference })} />
      <label className="profile-description-field">Mô tả thêm<textarea rows="4" value={profile.free_text} onChange={(event) => setProfile({ ...profile, free_text: event.target.value })} placeholder="Chia sẻ thêm về kiểu chuyến đi bạn yêu thích" /></label>
      <button className="primary-btn" type="submit" disabled={saving}>{saving ? 'Đang lưu…' : 'Lưu hồ sơ'}</button>
    </form>

    <section className="profile-history" aria-labelledby="booking-history-title">
      <div className="profile-section-title"><h2 id="booking-history-title">Lịch sử đặt phòng và tour</h2><p>Đơn mới nhất hiển thị trước.</p></div>
      <div className="profile-booking-tabs" role="tablist" aria-label="Loại đơn">
        <button type="button" role="tab" aria-selected={activeTab === 'room'} className={activeTab === 'room' ? 'is-active' : ''} onClick={() => setActiveTab('room')}>Đặt phòng <span>{safeList(bookings.room_bookings).length}</span></button>
        <button type="button" role="tab" aria-selected={activeTab === 'tour'} className={activeTab === 'tour' ? 'is-active' : ''} onClick={() => setActiveTab('tour')}>Đặt tour <span>{safeList(bookings.tour_bookings).length}</span></button>
      </div>
      <div className="profile-filter-chips" aria-label="Lọc đơn">
        {[['all', 'Tất cả'], ['upcoming', 'Sắp tới'], ['cancelled', 'Đã hủy'], ['past', 'Đã qua']].map(([key, label]) => <button type="button" key={key} className={filter === key ? 'is-active' : ''} onClick={() => setFilter(key)}>{label}</button>)}
      </div>
      {visibleBookings.length === 0 ? <div className="empty-state"><h3>Chưa có đơn phù hợp</h3><p>Các đơn đặt phòng và tour của bạn sẽ xuất hiện tại đây.</p></div> : <div className="booking-history-grid">
        {visibleBookings.map((item) => {
          const preview = item.refund_preview || { can_cancel: false, refund_amount: 0, refund_percent: 0, message: '' }
          const title = item.kind === 'room' ? (item.accommodation_name || 'Chỗ ở') : (item.tour_name || 'Tour')
          const dates = item.kind === 'room' ? `${formatDate(item.check_in)} – ${formatDate(item.check_out)}` : formatDate(item.departure_date)
          const detailPath = item.kind === 'room' ? `/cho-o/${item.accommodation_id}` : `/tours/${item.tour_id}`
          const key = `${item.kind}-${item.id}`
          return <article className="booking-history-card" key={key}>
            <header className="booking-history-card__header"><strong>Đặt {item.kind === 'room' ? 'phòng' : 'tour'} #{item.id}</strong><span className={`booking-status booking-status--${item.status}`}>{statusLabel(item.status)}</span></header>
            <div className="booking-history-card__body">
              <h3><Link to={detailPath}>{title}</Link></h3>
              {item.kind === 'room' ? <>
                <p>{item.room_type_name || 'Loại phòng'}</p><p>Nhận phòng {formatDate(item.check_in)} · Trả phòng {formatDate(item.check_out)} · {item.nights ?? 0} đêm</p>
              </> : <>
                <p>Khởi hành {formatDate(item.departure_date)}</p><p>{Number(item.num_adults || 0)} người lớn · {Number(item.num_children || 0)} trẻ em</p>
              </>}
              <p>Tổng tiền <strong>{formatMoney(item.total_price)}</strong></p><p>Ngày đặt {formatDate(item.created_at)}</p>
              <p className="booking-refund-line">Hoàn tiền: {refundLabel(item.refund_status, item.payment_simulated)}{item.status === 'cancelled' ? ` · ${formatMoney(item.refund_amount)}` : ''}</p>
            </div>
            <footer className="booking-history-card__actions">
              {item.status === 'pending' && <div className="profile-payment-actions"><button className="primary-btn" type="button" disabled={payingId === key} onClick={() => startPayment(item, 'vnpay')}>{payingId === key ? 'Đang chuyển…' : 'Thanh toán qua VNPay'}</button><button className="travel-button travel-button--outline" type="button" disabled={payingId === key} onClick={() => startPayment(item, 'momo')}>Thanh toán qua MoMo</button></div>}
              {item.status !== 'cancelled' && preview.can_cancel && <div className="booking-cancel-action"><button className="booking-cancel-button" type="button" onClick={() => setCancelTarget(item)}>Hủy đơn</button><small>Hoàn {formatMoney(preview.refund_amount)}{preview.refund_percent ? ` · ${preview.refund_percent}%` : ''}</small></div>}
              {item.can_review && item.kind === 'room' && <Link className="travel-button travel-button--outline" to={detailPath}>Đánh giá</Link>}
              <Link className="travel-button travel-button--outline" to={detailPath}>Xem chi tiết</Link>
            </footer>
          </article>
        })}
      </div>}
    </section>

    <section className="profile-history search-history-section" aria-labelledby="search-history-title">
      <div className="profile-section-title"><h2 id="search-history-title">Lịch sử tìm kiếm</h2><p>Các tiêu chí gợi ý bạn đã tìm gần đây.</p></div>
      {history.length ? <div className="search-history-list">{history.map((item) => <article className="search-history-entry" key={item.id}>
        <div><strong>{item.preferences || item.query || 'Mọi sở thích'} · Ngân sách {formatMoney(item.budget_estimate)} · Ngày đi {formatDate(item.travel_date)} · Thời tiết {weatherLabels[item.weather_preference] || weatherLabels.balanced} · Điểm đến hạng 1 {item.destination_name || 'Chưa có'}</strong><small>{formatDateTime(item.created_at)} (giờ Việt Nam)</small></div>
        <Link className="travel-button travel-button--outline" to={replaySearchUrl(item)}>Tìm lại</Link>
      </article>)}</div> : <div className="empty-state"><h3>Chưa có lịch sử tìm kiếm</h3><p>Các lần tìm gợi ý của bạn sẽ được lưu tại đây.</p><Link to="/goi-y">Khám phá gợi ý</Link></div>}
    </section>

    {cancelTarget && <div className="cancel-confirmation-overlay" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget && !cancelBusy) setCancelTarget(null) }}>
      <section className="cancel-confirmation-modal" role="dialog" aria-modal="true" aria-labelledby="cancel-dialog-title">
        <span className="eyebrow dark">Xác nhận thao tác</span><h2 id="cancel-dialog-title">Hủy đơn #{cancelTarget.id}?</h2>
        <p><strong>{cancelTarget.kind === 'room' ? cancelTarget.accommodation_name : cancelTarget.tour_name}</strong></p>
        <p>{cancelTarget.kind === 'room' ? `Ngày nhận ${formatDate(cancelTarget.check_in)} · trả ${formatDate(cancelTarget.check_out)}` : `Ngày khởi hành ${formatDate(cancelTarget.departure_date)}`}</p>
        <p>Số tiền dự kiến hoàn: <strong>{formatMoney(cancelTarget.refund_preview?.refund_amount)}</strong>{cancelTarget.refund_preview?.refund_percent ? ` (${cancelTarget.refund_preview.refund_percent}%)` : ''}</p>
        <p className="cancel-policy-note">{cancelTarget.kind === 'room' ? 'Đơn phòng đã thanh toán: hủy trước từ 3 ngày hoàn 100%, trước 1–2 ngày hoàn 50%; cần còn ít nhất 1 ngày trước nhận phòng.' : 'Đơn tour đã thanh toán: hủy trước từ 7 ngày hoàn 100%, trước 3–6 ngày hoàn 50%; cần còn ít nhất 3 ngày trước khởi hành.'} Đơn chưa thanh toán không có khoản hoàn.</p>
        <div className="cancel-confirmation-actions"><button className="travel-button travel-button--outline" type="button" disabled={cancelBusy} onClick={() => setCancelTarget(null)}>Giữ đơn</button><button className="booking-cancel-button" type="button" disabled={cancelBusy} onClick={cancelBooking}>{cancelBusy ? 'Đang hủy…' : 'Xác nhận hủy'}</button></div>
      </section>
    </div>}
  </section>
}

import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api, bookTourDeparture, getTourDetail, getTours } from '../api'
import { ActionButton, CategoryChip, EmptyState, ErrorNotice, PriceTag, SectionSkeleton, TravelImage } from '../components/DesignSystem'
import { useAuth } from '../auth'

export const CATEGORY_LABELS = {
  kham_pha: 'Khám phá thiên nhiên',
  van_hoa: 'Văn hóa - Lịch sử',
  nghi_duong: 'Nghỉ dưỡng',
  mao_hiem: 'Mạo hiểm',
  am_thuc: 'Ẩm thực',
  ghep_doan: 'Tour ghép đoàn',
  rieng: 'Tour riêng',
}

const CATEGORIES = [
  { key: '', label: 'Tất cả' },
  { key: 'kham_pha', label: 'Khám phá thiên nhiên' },
  { key: 'van_hoa', label: 'Văn hóa - Lịch sử' },
  { key: 'nghi_duong', label: 'Nghỉ dưỡng' },
  { key: 'mao_hiem', label: 'Mạo hiểm' },
  { key: 'am_thuc', label: 'Ẩm thực' },
  { key: 'ghep_doan', label: 'Tour ghép đoàn' },
  { key: 'rieng', label: 'Tour riêng' },
]

export function formatVND(amount) {
  return Number(amount || 0).toLocaleString('vi-VN') + ' đ'
}

export function formatDateVN(dateStr) {
  if (!dateStr) return ''
  const parts = dateStr.split('-')
  if (parts.length === 3) return `${parts[2]}/${parts[1]}/${parts[0]}`
  return dateStr
}

export function ToursPage() {
  const [tours, setTours] = useState([])
  const [selectedCategory, setSelectedCategory] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    setError('')
    getTours(selectedCategory)
      .then(setTours)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [selectedCategory])

  return (
    <div className="tours-page">
      <div className="section-head tours-page-heading">
        <span className="eyebrow dark">Trải nghiệm du lịch</span>
        <h1>Chọn hành trình tiếp theo</h1>
        <p className="section-desc">Những chuyến đi được sắp xếp để bạn khám phá nhiều hơn, an tâm tận hưởng từng ngày.</p>
      </div>

      <div className="tour-categories-bar" role="tablist">
        {CATEGORIES.map((cat) => (
          <button
            key={cat.key}
            type="button"
            className={`category-pill ${selectedCategory === cat.key ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat.key)}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {error && <ErrorNotice>{error}</ErrorNotice>}

      {loading ? (
        <SectionSkeleton count={6} className="tours-grid" />
      ) : tours.length === 0 ? (
        <EmptyState title="Chưa có tour trong danh mục này" description="Hãy chọn một loại trải nghiệm khác để xem thêm hành trình." />
      ) : (
        <div className="tours-grid">
          {tours.map((tour) => (
            <article className="tour-card refreshed-tour-card" key={tour.id}>
              <Link to={`/tours/${tour.id}`} className="tour-card-media refreshed-tour-media"><TravelImage src={tour.cover_image_url} alt={tour.name} aspectRatio="16 / 10" width="960" height="600" /><span className="tour-duration-badge">{tour.duration_days} ngày</span></Link>
              <div className="tour-card-body">
                <CategoryChip className="tour-category-tag refreshed-tour-tag">{CATEGORY_LABELS[tour.category] || tour.category}</CategoryChip>
                <h3 className="tour-card-title"><Link to={`/tours/${tour.id}`}>{tour.name}</Link></h3>
                <p className="tour-card-desc">{tour.description}</p>
                <div className="tour-card-footer"><PriceTag suffix="/ khách">{formatVND(tour.price_adult)}</PriceTag><ActionButton as={Link} to={`/tours/${tour.id}`} variant="ghost">Xem tour <span aria-hidden="true">→</span></ActionButton></div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  )
}

export function TourDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tour, setTour] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDepartureId, setSelectedDepartureId] = useState(null)

  useEffect(() => {
    setLoading(true)
    getTourDetail(id)
      .then((data) => {
        setTour(data)
        const firstAvailable = data.departures?.find((d) => d.slots_available > 0)
        if (firstAvailable) setSelectedDepartureId(firstAvailable.id)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="loading-state">Đang tải chi tiết tour...</div>
  if (error || !tour) return <div className="form-error">{error || 'Không tìm thấy tour.'}</div>

  const handleBookNow = (depId) => {
    const targetId = depId || selectedDepartureId
    if (!targetId) return
    navigate(`/tours/${tour.id}/dat?departure=${targetId}`)
  }
  const selectedDeparture = tour.departures?.find((departure) => departure.id === selectedDepartureId)

  return (
    <div className="tour-detail-container refreshed-tour-detail">
      <header className="tour-detail-hero">
        <TravelImage className="tour-detail-hero-image" src={tour.cover_image_url} alt={tour.name} aspectRatio="16 / 6" width="1600" height="600" />
        <div className="tour-detail-hero-shade" />
        <div className="tour-hero-content"><CategoryChip>{CATEGORY_LABELS[tour.category] || tour.category}</CategoryChip><h1>{tour.name}</h1><div className="tour-meta-pills"><span>{tour.duration_days} ngày</span>{tour.min_age ? <span>Từ {tour.min_age} tuổi</span> : null}<span>Hành trình trải nghiệm</span></div></div>
      </header>

      <div className="tour-detail-layout">
        <div className="tour-main-content">
          <section className="tour-section">
            <h2>Mô tả chuyến đi</h2>
            <p className="tour-full-description">{tour.description}</p>
          </section>

          <section className="tour-section">
            <h2>Lịch trình chi tiết theo ngày</h2>
            {tour.stops && tour.stops.length > 0 ? (
              <div className="tour-itinerary-timeline">
                {tour.stops.map((stop) => (
                  <div className="timeline-item" key={stop.id}>
                    <div className="timeline-badge">Ngày {stop.day_number}</div>
                    <div className="timeline-card">
                      <h3>{stop.destination?.name || 'Điểm đến'}</h3>
                      {stop.note && <p className="timeline-note">{stop.note}</p>}
                      {stop.destination?.image_url && (
                        <img className="timeline-dest-img" src={stop.destination.image_url} alt={stop.destination.name} />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="muted-text">Lịch trình đang được cập nhật.</p>
            )}
          </section>

          <section className="tour-section">
            <h2>Dịch vụ bao gồm & không bao gồm</h2>
            <div className="services-dual-grid">
              <div className="service-card included">
                <h3>✅ Bao gồm</h3>
                <ul>
                  {tour.included_services?.length > 0 ? (
                    tour.included_services.map((srv, idx) => <li key={idx}>{srv}</li>)
                  ) : (
                    <li>Xe đưa đón đời mới, hướng dẫn viên, bảo hiểm du lịch, các bữa ăn tiêu chuẩn.</li>
                  )}
                </ul>
              </div>
              <div className="service-card excluded">
                <h3>❌ Không bao gồm</h3>
                <ul>
                  {tour.excluded_services?.length > 0 ? (
                    tour.excluded_services.map((srv, idx) => <li key={idx}>{srv}</li>)
                  ) : (
                    <li>Chi phí cá nhân, đồ uống ngoài thực đơn, tiền tip hướng dẫn viên.</li>
                  )}
                </ul>
              </div>
            </div>
          </section>

          {tour.cancellation_policy && (
            <section className="tour-section">
              <h2>Chính sách hủy tour</h2>
              <div className="cancellation-policy-box">
                <p>{tour.cancellation_policy}</p>
              </div>
            </section>
          )}
        </div>

        <aside className="tour-booking-sidebar">
          <div className="booking-card-sticky">
            <div className="booking-price-header">
              <span className="price-title">Giá người lớn:</span>
              <strong className="price-big">{formatVND(tour.price_adult)}</strong>
            </div>

            {tour.price_child ? (
              <div className="booking-price-sub">
                <span>Trẻ em: </span>
                <strong>{formatVND(tour.price_child)}</strong>
              </div>
            ) : null}

            {tour.single_room_supplement > 0 ? (
              <div className="booking-price-sub">
                <span>Phụ thu phòng đơn: </span>
                <strong>+{formatVND(tour.single_room_supplement)}</strong>
              </div>
            ) : null}

            <hr className="divider" />

            <div className="departures-selector-section">
              <h3>Chọn ngày khởi hành:</h3>
              {tour.departures && tour.departures.length > 0 ? (
                <div className="departure-table-wrap"><table className="departure-table"><thead><tr><th>Ngày khởi hành</th><th>Chỗ còn</th><th>Chọn</th></tr></thead><tbody>
                  {tour.departures.map((dep) => {
                    const isFull = dep.slots_available <= 0
                    const isSelected = selectedDepartureId === dep.id
                    return <tr key={dep.id} className={isSelected ? 'is-selected' : ''}><td>{formatDateVN(dep.departure_date)}</td><td>{isFull ? <span className="departure-full">Hết chỗ</span> : <span className={`departure-availability ${dep.slots_available <= 5 ? 'is-low' : ''}`}>Còn {dep.slots_available} chỗ</span>}</td><td><button type="button" className="departure-select" disabled={isFull} aria-label={`Chọn ngày ${formatDateVN(dep.departure_date)}`} aria-pressed={isSelected} onClick={() => !isFull && setSelectedDepartureId(dep.id)}>{isSelected ? 'Đã chọn' : 'Chọn'}</button></td></tr>
                  })}
                </tbody></table></div>
              ) : (
                <p className="form-error">Hiện chưa có chuyến khởi hành nào sắp tới.</p>
              )}
            </div>

            <button
              type="button"
              className="primary-btn w-full btn-large"
              disabled={!selectedDepartureId}
              onClick={() => handleBookNow()}
            >
              {selectedDepartureId ? 'Đặt chỗ ngay' : 'Vui lòng chọn ngày khởi hành'}
            </button>
          </div>
        </aside>
      </div>
      <div className="mobile-tour-booking"><div><small>Giá từ</small><strong>{formatVND(tour.price_adult)} <span>/ khách</span></strong><small>{selectedDeparture ? `${formatDateVN(selectedDeparture.departure_date)} · Còn ${selectedDeparture.slots_available} chỗ` : 'Chọn ngày khởi hành'}</small></div><button type="button" className="travel-button travel-button--primary" disabled={!selectedDepartureId || selectedDeparture?.slots_available <= 0} onClick={() => handleBookNow()}>{selectedDepartureId ? 'Đặt tour' : 'Chọn ngày'}</button></div>
    </div>
  )
}

export function TourBookingPage() {
  const { user, status: authStatus } = useAuth()
  const { id } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const location = useLocation()
  const departureIdFromQuery = params.get('departure')

  const [tour, setTour] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [paymentProvider, setPaymentProvider] = useState('vnpay')

  const [departureId, setDepartureId] = useState(departureIdFromQuery || '')
  const [numAdults, setNumAdults] = useState(1)
  const [numChildren, setNumChildren] = useState(0)
  const [isSingleRoom, setIsSingleRoom] = useState(false)
  const [guestPhone, setGuestPhone] = useState('')

  useEffect(() => {
    setLoading(true)
    getTourDetail(id)
      .then((data) => {
        setTour(data)
        if (!departureIdFromQuery) {
          const firstAvail = data.departures?.find((d) => d.slots_available > 0)
          if (firstAvail) setDepartureId(String(firstAvail.id))
        }
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id, departureIdFromQuery])

  if (authStatus === 'loading' || loading) return <div className="loading-state">Đang tải biểu mẫu đặt tour...</div>
  if (error || !tour) return <div className="form-error">{error || 'Không tìm thấy tour.'}</div>
  if (!user) return <section className="auth-page"><div className="auth-card booking-card"><h1>Đăng nhập để tiếp tục đặt tour</h1><p>Sau khi đăng nhập, bạn sẽ quay lại đúng tour và ngày khởi hành đã chọn.</p><Link className="primary-btn" to={`/dang-nhap?next=${encodeURIComponent(`${location.pathname}${location.search}`)}`}>Đăng nhập</Link><p><Link to={`/tours/${tour.id}`}>Quay lại {tour.name}</Link></p></div></section>

  const selectedDeparture = tour.departures?.find((d) => String(d.id) === String(departureId))
  const slotsAvailable = selectedDeparture?.slots_available ?? 0
  const requestedSlots = Number(numAdults || 0) + Number(numChildren || 0)
  const isOverSlot = selectedDeparture && requestedSlots > slotsAvailable

  // Server formula: (adults * price_adult) + (children * price_child) + (single_room_supplement if isSingleRoom)
  const adultPrice = Number(tour.price_adult || 0)
  const childPrice = Number(tour.price_child || 0)
  const singleSupplement = isSingleRoom ? Number(tour.single_room_supplement || 0) : 0
  const totalAmount = (Number(numAdults || 0) * adultPrice) + (Number(numChildren || 0) * childPrice) + singleSupplement

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')

    if (!departureId) return setError('Vui lòng chọn ngày khởi hành.')
    if (numAdults < 1) return setError('Cần ít nhất 1 người lớn tham gia.')
    if (!guestPhone.trim()) return setError('Vui lòng nhập số điện thoại liên hệ.')
    if (isOverSlot) return setError(`Số chỗ còn lại chỉ còn ${slotsAvailable} chỗ. Vui lòng chọn lại số lượng.`)

    setSubmitting(true)
    try {
      // 1. Tạo đơn TourBooking
      const booking = await bookTourDeparture(departureId, {
        num_adults: Number(numAdults),
        num_children: Number(numChildren),
        guest_phone: guestPhone.trim(),
        is_single_room: Boolean(isSingleRoom),
      })

      // 2. Khởi tạo thanh toán sandbox chung
      const paymentRes = await api('/api/payments/init/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          booking_id: booking.id,
          booking_type: 'tour_booking',
          provider: paymentProvider,
          amount: booking.total_price,
        }),
      })

      if (paymentRes?.redirect_url) {
        window.location.href = paymentRes.redirect_url
      } else {
        navigate('/ho-so')
      }
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <div className="tour-booking-page">
      <div className="section-head">
        <span className="eyebrow">Đặt tour</span>
        <h1>Xác Nhận & Đặt Chỗ Tour</h1>
      </div>

      <div className="tour-booking-layout">
        <form className="tour-booking-form card" onSubmit={handleSubmit}>
          <h2>Thông tin đặt tour</h2>
          {error && <p className="form-error">{error}</p>}

          <label>
            Chuyến khởi hành *
            <select
              value={departureId}
              onChange={(e) => setDepartureId(e.target.value)}
              required
            >
              <option value="">-- Chọn ngày khởi hành --</option>
              {tour.departures?.map((dep) => (
                <option
                  key={dep.id}
                  value={dep.id}
                  disabled={dep.slots_available <= 0}
                >
                  {formatDateVN(dep.departure_date)} — {dep.slots_available > 0 ? `Còn ${dep.slots_available} chỗ` : 'Hết chỗ'}
                </option>
              ))}
            </select>
          </label>

          {selectedDeparture && (
            <div className={`slots-alert ${slotsAvailable <= 3 ? 'warning' : 'ok'}`}>
              ℹ️ Ngày đi: <strong>{formatDateVN(selectedDeparture.departure_date)}</strong> — Còn <strong>{slotsAvailable}</strong> chỗ trống.
            </div>
          )}

          <div className="inline-group">
            <label>
              Số người lớn *
              <input
                type="number"
                min="1"
                max={slotsAvailable || 50}
                value={numAdults}
                onChange={(e) => setNumAdults(Math.max(1, parseInt(e.target.value) || 1))}
                required
              />
              <span className="input-hint">{formatVND(tour.price_adult)} / người lớn</span>
            </label>

            <label>
              Số trẻ em
              <input
                type="number"
                min="0"
                max={slotsAvailable || 50}
                value={numChildren}
                onChange={(e) => setNumChildren(Math.max(0, parseInt(e.target.value) || 0))}
              />
              <span className="input-hint">{tour.price_child ? `${formatVND(tour.price_child)} / trẻ em` : 'Miễn phí'}</span>
            </label>
          </div>

          {tour.single_room_supplement > 0 && (
            <label className="checkbox-label single-room-choice">
              <input
                type="checkbox"
                checked={isSingleRoom}
                onChange={(e) => setIsSingleRoom(e.target.checked)}
              />
              <span>Yêu cầu ở phòng đơn (Phụ thu: <strong>+{formatVND(tour.single_room_supplement)}</strong>)</span>
            </label>
          )}

          <label>
            Số điện thoại liên hệ *
            <input
              type="tel"
              placeholder="VD: 0912345678"
              required
              value={guestPhone}
              onChange={(e) => setGuestPhone(e.target.value)}
            />
            <span className="input-hint">Số điện thoại được mã hóa bảo mật Fernet trước khi lưu vào CSDL.</span>
          </label>

          <fieldset className="payment-provider-choice">
            <legend>Chọn cổng thanh toán</legend>
            <label><input type="radio" name="tour-payment-provider" value="vnpay" checked={paymentProvider === 'vnpay'} onChange={() => setPaymentProvider('vnpay')} /> VNPay Sandbox</label>
            <label><input type="radio" name="tour-payment-provider" value="momo" checked={paymentProvider === 'momo'} onChange={() => setPaymentProvider('momo')} /> MoMo Sandbox</label>
          </fieldset>

          <button
            type="submit"
            className="primary-btn btn-large w-full"
            disabled={submitting || isOverSlot || !selectedDeparture}
          >
            {submitting ? 'Đang khởi tạo thanh toán...' : isOverSlot ? 'Vượt quá số chỗ còn lại' : `Xác nhận & Thanh toán ${paymentProvider === 'vnpay' ? 'qua VNPay' : 'qua MoMo'} (${formatVND(totalAmount)})`}
          </button>
        </form>

        <aside className="tour-summary-aside card">
          <h3>Tóm tắt đơn đặt tour</h3>
          <div className="summary-tour-info">
            <img src={tour.cover_image_url || 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=400&q=80'} alt={tour.name} />
            <div>
              <h4>{tour.name}</h4>
              <span className="category-pill sm">{CATEGORY_LABELS[tour.category] || tour.category}</span>
              <p>⏱️ Thời gian: {tour.duration_days} ngày</p>
            </div>
          </div>

          <hr className="divider" />

          <div className="calculation-breakdown">
            <div className="calc-row">
              <span>Người lớn ({numAdults}):</span>
              <strong>{formatVND(numAdults * adultPrice)}</strong>
            </div>

            {numChildren > 0 && (
              <div className="calc-row">
                <span>Trẻ em ({numChildren}):</span>
                <strong>{formatVND(numChildren * childPrice)}</strong>
              </div>
            )}

            {isSingleRoom && tour.single_room_supplement > 0 && (
              <div className="calc-row">
                <span>Phụ thu phòng đơn:</span>
                <strong>+{formatVND(tour.single_room_supplement)}</strong>
              </div>
            )}

            <div className="calc-row total">
              <span>Tổng thanh toán:</span>
              <strong className="price-big">{formatVND(totalAmount)}</strong>
            </div>
          </div>

          <div className="secure-badge">
            🔒 Thanh toán MoMo thử nghiệm, bảo mật
          </div>
        </aside>
      </div>
    </div>
  )
}

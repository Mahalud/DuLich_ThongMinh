import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowRight, MapPin, ShieldCheck, Sparkles, Star } from 'lucide-react'
import { api, getAccommodations, getAmenities, getDestinations } from '../api'
import RoomTypeCard from '../components/RoomTypeCard'
import RouteMap from '../RouteMap'
import { amenityIcon, setAmenityCatalog } from '../amenityIcons'
import { CategoryChip, ErrorNotice, TravelImage } from '../components/DesignSystem'
import { useAuth } from '../auth'
import { useOrigin } from '../origin'

export default function AccommodationDetailPage() {
  const { user, status: authStatus } = useAuth()
  const { originLocation } = useOrigin()
  const { id } = useParams()
  const [accommodation, setAccommodation] = useState(null)
  const [destination, setDestination] = useState(null)
  const [labels, setLabels] = useState({})
  const [route, setRoute] = useState(null)
  const [reviews, setReviews] = useState([])
  const [reviewBookings, setReviewBookings] = useState([])
  const [reviewForm, setReviewForm] = useState({ booking: '', rating: 5, comment: '' })
  const [reviewMessage, setReviewMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getAccommodations(), getAmenities(), getDestinations()]).then(([items, amenities, destinations]) => {
      setAmenityCatalog(amenities)
      const selected = items.find((item) => String(item.id) === id)
      setAccommodation(selected)
      setDestination(destinations.find((item) => String(item.id) === String(selected?.destination)) || null)
      setLabels(Object.fromEntries(amenities.map((item) => [item.key, item.label])))
    }).catch((err) => setError(err.message))
  }, [id])

  useEffect(() => {
    if (!accommodation || !originLocation) { setRoute(null); return }
    let active = true
    api(`/api/routes/?start_lat=${originLocation.latitude}&start_lng=${originLocation.longitude}&end_lat=${accommodation.latitude}&end_lng=${accommodation.longitude}`).then((data) => { if (active) setRoute(data) }).catch((err) => { if (active) setError(err.message) })
    return () => { active = false }
  }, [accommodation, originLocation])

  useEffect(() => {
    if (!accommodation) return
    api(`/api/reviews/?accommodation=${accommodation.id}`).then(setReviews).catch((err) => setError(err.message))
  }, [accommodation])

  useEffect(() => {
    if (!accommodation || authStatus !== 'authenticated' || !user) { setReviewBookings([]); return }
    api('/api/my-bookings/').then((orders) => {
      setReviewBookings((orders.room_bookings || []).filter((item) => item.accommodation_id === accommodation.id && item.can_review))
    }).catch((err) => setError(err.message))
  }, [accommodation, user, authStatus])

  const submitReview = async (event) => {
    event.preventDefault()
    setReviewMessage('')
    try {
      const review = await api('/api/reviews/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...reviewForm, booking: Number(reviewForm.booking), rating: Number(reviewForm.rating) }),
      })
      setReviews((current) => [review, ...current])
      setReviewBookings((current) => current.filter((item) => item.id !== review.booking))
      const updated = (await getAccommodations()).find((item) => item.id === accommodation.id)
      if (updated) setAccommodation(updated)
      setReviewMessage('Đánh giá của bạn đã được gửi.')
      setReviewForm({ booking: '', rating: 5, comment: '' })
    } catch (err) { setReviewMessage(err.message || 'Chưa thể gửi đánh giá. Vui lòng thử lại.') }
  }

  const roomTypes = accommodation?.room_types || []
  const amenityKeys = useMemo(() => [...new Set(roomTypes.flatMap((room) => room.amenities || []))], [roomTypes])
  const lowestRoom = [...roomTypes].sort((left, right) => Number(left.base_price) - Number(right.base_price))[0]

  if (!accommodation) return <section className="accommodation-detail page-shell">{error ? <ErrorNotice>{error}</ErrorNotice> : <div className="loading-state">Đang tải thông tin chỗ ở…</div>}</section>

  return <section className="accommodation-detail page-shell">
    <div className="accommodation-breadcrumb"><Link to="/">Trang chủ</Link><span>/</span><Link to={`/diem-den/${accommodation.destination}`}>{destination?.name || 'Điểm đến'}</Link><span>/</span><span>{accommodation.name}</span></div>
    <header className="accommodation-heading"><div><CategoryChip className="accommodation-kind">{accommodation.category === 'homestay' ? 'Nhà lưu trú' : 'Khách sạn'}</CategoryChip><h1>{accommodation.name}</h1><p>{accommodation.description}</p><div className="accommodation-heading-meta"><span><Star size={15} fill="currentColor" /> {Number(accommodation.rating || 0).toFixed(1)}</span><span><MapPin size={15} /> {destination?.name || 'Việt Nam'}</span></div></div><Link to={`/diem-den/${accommodation.destination}`} className="accommodation-back-link">Xem điểm đến <ArrowRight size={16} /></Link></header>

    <div className="accommodation-gallery" aria-label="Ảnh cảnh quan khu vực">
      <TravelImage className="accommodation-gallery-main" src={destination?.image_url} alt={`Cảnh quan khu vực ${destination?.name || 'điểm đến'}`} aspectRatio="16 / 8" width="1500" height="750" />
      <div className="accommodation-gallery-side"><TravelImage src={destination?.image_url} alt={`Khung cảnh quanh ${accommodation.name}`} aspectRatio="4 / 3" width="720" height="540" /><div className="gallery-note"><Sparkles size={19} /><span>Gần gũi với điểm đến</span><small>Khám phá khu vực quanh nơi lưu trú</small></div></div>
      <span className="gallery-caption">Ảnh cảnh quan khu vực {destination?.name || ''}</span>
    </div>

    {error && <ErrorNotice>{error}</ErrorNotice>}
    <div className="accommodation-detail-layout">
      <div className="accommodation-detail-main">
        <section className="detail-surface accommodation-reviews"><div className="detail-section-heading"><div><span className="section-kicker">Trải nghiệm của khách</span><h2>Đánh giá khách lưu trú</h2><p><Star size={15} fill="currentColor" /> {Number(accommodation.rating || 0).toFixed(1)} · {reviews.length} đánh giá</p></div></div>{reviews.length ? <div className="review-list">{reviews.map((review) => <article className="list-item" key={review.id}><div><strong>{review.user_name}</strong>{review.user_is_demo && <span className="demo-badge">Minh họa</span>}<p>{'★'.repeat(review.rating)}{'☆'.repeat(Math.max(0, 5 - review.rating))}</p><p>{review.comment || 'Khách chưa để lại nội dung.'}</p><small>{new Date(review.created_at).toLocaleDateString('vi-VN')}</small></div></article>)}</div> : <div className="empty-state"><h3>Chưa có đánh giá</h3><p>Đánh giá từ khách đã lưu trú sẽ hiện ở đây.</p></div>}{reviewBookings.length > 0 && <form className="admin-form review-form" onSubmit={submitReview}><h3>Chia sẻ trải nghiệm lưu trú</h3><label>Đơn đặt phòng<select required value={reviewForm.booking} onChange={(event) => setReviewForm({ ...reviewForm, booking: event.target.value })}><option value="">Chọn đơn đã hoàn tất</option>{reviewBookings.map((item) => <option value={item.id} key={item.id}>Đơn #{item.id} · {item.check_in} – {item.check_out}</option>)}</select></label><label>Điểm đánh giá<select value={reviewForm.rating} onChange={(event) => setReviewForm({ ...reviewForm, rating: event.target.value })}><option value="5">5 sao</option><option value="4">4 sao</option><option value="3">3 sao</option><option value="2">2 sao</option><option value="1">1 sao</option></select></label><label>Nhận xét<textarea rows="3" value={reviewForm.comment} onChange={(event) => setReviewForm({ ...reviewForm, comment: event.target.value })} placeholder="Chia sẻ điều bạn yêu thích về chỗ ở" /></label><button className="primary-btn" type="submit">Gửi đánh giá</button>{reviewMessage && <p className="admin-message" role="status">{reviewMessage}</p>}</form>}{authStatus === 'authenticated' && user && reviewBookings.length === 0 && <p className="detail-muted">Bạn có thể đánh giá sau khi đơn đã xác nhận và ngày trả phòng đã qua.</p>}{authStatus === 'anonymous' && <p className="detail-muted"><Link to="/dang-nhap">Đăng nhập</Link> để gửi đánh giá sau lưu trú.</p>}{authStatus === 'loading' && <p className="detail-muted">Đang kiểm tra phiên đăng nhập…</p>}</section>
        <section className="detail-surface accommodation-about"><div><span className="section-kicker">Một nơi để nghỉ chân</span><h2>Không gian nghỉ ngơi tại {destination?.name || 'điểm đến'}</h2><p>{accommodation.description}</p></div><div className="accommodation-trust"><span><ShieldCheck size={17} /> Thông tin minh họa</span><span>Đặt phòng trực tuyến</span></div></section>

        <section className="detail-surface amenities-surface"><div className="detail-section-heading"><div><span className="section-kicker">Tiện nghi</span><h2>Tiện ích có tại phòng</h2></div></div>{amenityKeys.length ? <div className="amenity-cards">{amenityKeys.map((key) => <div className="amenity-card" key={key}><span>{amenityIcon(key, 20)}</span><strong>{labels[key] || key}</strong></div>)}</div> : <p className="detail-muted">Thông tin tiện ích đang được cập nhật.</p>}</section>

        <section className="detail-surface room-list-surface"><div className="detail-section-heading"><div><span className="section-kicker">Chọn không gian phù hợp</span><h2>Loại phòng</h2><p>{roomTypes.length} lựa chọn phòng nghỉ</p></div></div><div className="room-list">{roomTypes.map((room) => <RoomTypeCard key={room.id} room={room} labels={labels} onBook={() => { window.location.href = `/dat-phong/${room.id}?accommodation=${accommodation.id}` }} />)}</div></section>

        <section className="detail-surface accommodation-map-surface"><div className="detail-section-heading"><div><span className="section-kicker">Vị trí</span><h2>Bản đồ khu vực</h2></div></div><div id="route-map">{route ? <RouteMap route={route} destination={accommodation} /> : originLocation ? <p className="detail-muted">Đang tải bản đồ…</p> : <p className="detail-muted">Chọn vị trí xuất phát để xem tuyến đường đến chỗ ở này. <Link to="/goi-y">Chọn vị trí xuất phát</Link></p>}</div></section>
      </div>

      <aside className="accommodation-booking-aside"><div className="accommodation-booking-card"><span className="section-kicker">Đặt chỗ lưu trú</span><h2>{lowestRoom ? `${Number(lowestRoom.base_price).toLocaleString('vi-VN')} đ` : 'Liên hệ để biết giá'}</h2>{lowestRoom && <p>mỗi đêm · {lowestRoom.name}</p>}<div className="booking-assurance"><ShieldCheck size={17} /> Thanh toán thử nghiệm an toàn</div>{lowestRoom ? <button type="button" className="travel-button travel-button--primary" onClick={() => { window.location.href = `/dat-phong/${lowestRoom.id}?accommodation=${accommodation.id}` }}>Chọn phòng này <ArrowRight size={16} /></button> : <span className="detail-muted">Chưa có loại phòng</span>}<small>Chọn loại phòng để tiếp tục đặt chỗ.</small></div></aside>
    </div>
  </section>
}

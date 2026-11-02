import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, getDestinations, getNearby, getWeather } from '../api'
import LoadingSkeleton from '../components/LoadingSkeleton'
import RouteMap from '../RouteMap'
import { CategoryChip, ErrorNotice, RatingStars, TravelImage } from '../components/DesignSystem'
import { CloudRain, CloudSun, MapPin, SlidersHorizontal, Star, Wind } from 'lucide-react'
import { useOrigin } from '../origin'

const localDateString = (value) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
const today = localDateString(new Date())
const latestTravelDate = (() => { const latest = new Date(); latest.setDate(latest.getDate() + 15); return localDateString(latest) })()

export default function DestinationDetailPage() {
  const { originLocation } = useOrigin()
  const { id } = useParams()
  const [destination, setDestination] = useState(null)
  const [nearby, setNearby] = useState([])
  const [nearbyLoading, setNearbyLoading] = useState(false)
  const [radiusComparison, setRadiusComparison] = useState(null)
  const [route, setRoute] = useState(null)
  const [radius, setRadius] = useState('10')
  const [travelDate, setTravelDate] = useState(today)
  const [weather, setWeather] = useState(null)
  const [error, setError] = useState('')
  const [weatherError, setWeatherError] = useState('')
  const coverRef = useRef(null)
  const nearbyLoadedRef = useRef({ radius: 10, count: 0 })

  useEffect(() => { getDestinations().then((items) => setDestination(items.find((item) => String(item.id) === id))).catch((err) => setError(err.message)) }, [id])
  useEffect(() => {
    if (!destination) return undefined
    let active = true
    setNearbyLoading(true)
    getNearby(destination.id, radius).then((data) => {
      if (!active) return
      const results = [...(data.results || [])].sort((a, b) => Number(a.distance_km) - Number(b.distance_km))
      setNearby(results)
      nearbyLoadedRef.current = { radius: Number(radius), count: results.length }
      setNearbyLoading(false)
    }).catch((err) => {
      if (active) { setNearbyLoading(false); setError(err.message) }
    })
    return () => { active = false }
  }, [destination, radius])
  useEffect(() => {
    if (!destination || !originLocation) { setRoute(null); return }
    let active = true
    api(`/api/routes/?start_lat=${originLocation.latitude}&start_lng=${originLocation.longitude}&end_lat=${destination.latitude}&end_lng=${destination.longitude}`).then((data) => { if (active) setRoute(data) }).catch((err) => { if (active) setError(err.message) })
    return () => { active = false }
  }, [destination, originLocation])
  useEffect(() => {
    if (!destination) return undefined
    let active = true
    setWeatherError('')
    getWeather(destination, travelDate).then((data) => { if (active) setWeather(data) }).catch((err) => { if (active) setWeatherError(err.message) })
    return () => { active = false }
  }, [destination, travelDate])
  useEffect(() => {
    const cover = coverRef.current
    if (!cover || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    let frame = 0
    const update = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => cover.style.setProperty('--cover-parallax', `${Math.min(window.scrollY * 0.12, 56)}px`))
    }
    window.addEventListener('scroll', update, { passive: true })
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', update) }
  }, [destination])

  if (!destination) return error ? <section className="destination-detail page-shell"><ErrorNotice>{error}</ErrorNotice></section> : <section className="destination-detail page-shell"><LoadingSkeleton count={1} /></section>

  return <section className="destination-detail page-shell">
    <header className="destination-cover" ref={coverRef}>
      <div className="destination-cover-media"><TravelImage className="destination-cover-image" src={destination.image_url} alt={destination.name} aspectRatio="16 / 7" width="1600" height="700" /></div>
      <div className="destination-cover-shade" />
      <div className="destination-cover-content"><CategoryChip>{destination.category}</CategoryChip><h1>{destination.name}</h1><p>{destination.description}</p><div className="destination-cover-meta"><RatingStars rating={destination.rating} /><span><MapPin size={15} /> {destination.address || 'Việt Nam'}</span></div></div>
    </header>

    {error && <ErrorNotice>{error}</ErrorNotice>}
    <div className="destination-detail-grid">
      <div className="destination-detail-main">
        <section className="detail-surface weather-surface">
          <div className="detail-section-heading"><span className="detail-icon"><CloudSun size={20} /></span><div><h2>Thời tiết ngày đi</h2><p>Xem điều kiện dự báo cho lịch trình của bạn.</p></div></div>
          <label className="trip-date-field">Ngày khởi hành<input type="date" min={today} max={latestTravelDate} value={travelDate} onChange={(event) => setTravelDate(event.target.value)} /><small>Dự báo thời tiết tối đa 16 ngày</small></label>
          {weatherError ? <p className="detail-inline-error">{weatherError}</p> : weather?.weather_available === false ? <p className="detail-muted">Chưa có dữ liệu thời tiết</p> : weather ? <div className="weather-summary"><strong><CloudSun size={21} aria-hidden="true" /> {Math.round(Number(weather.weather?.temperature_c))}°C</strong><span><CloudRain size={16} aria-hidden="true" /> Mưa {Math.round(Number(weather.weather?.rain_probability))}%</span><span><Wind size={16} aria-hidden="true" /> Gió {Math.round(Number(weather.weather?.wind_kmh))} km/h</span><small>{weather.weather?.summary}</small><span>Điểm thời tiết {weather.weather_score}</span></div> : <p className="detail-muted">Đang tải dự báo thời tiết…</p>}
        </section>

        <section className="detail-surface route-surface" id="route-map">
          {route ? <RouteMap route={route} destination={destination} /> : originLocation ? <div className="route-loading"><span className="detail-icon"><MapPin size={20} /></span><div><h2>Bản đồ hành trình</h2><p>Đang tải tuyến đường đến {destination.name}…</p></div></div> : <div className="route-loading"><span className="detail-icon"><MapPin size={20} /></span><div><h2>Chọn vị trí xuất phát</h2><p>Chọn thành phố hoặc dùng vị trí hiện tại để xem tuyến đường đến {destination.name}.</p><Link className="travel-button travel-button--primary" to="/goi-y">Chọn vị trí xuất phát</Link></div></div>}
        </section>

        <section className="detail-surface nearby-panel">
          <div className="nearby-panel-head detail-section-heading">
            <div><span className="section-kicker">Nghỉ ngơi quanh điểm đến</span><h2>Chỗ ở quanh đây</h2><p>Tìm thấy {nearby.length} chỗ ở trong {radius} km</p></div>
            <label className="radius-control"><span><SlidersHorizontal size={16} /> Bán kính <strong>{radius} km</strong></span>
              <input type="range" min="5" max="50" step="5" value={radius} onChange={(event) => {
                const nextRadius = Number(event.target.value)
                const previous = nearbyLoadedRef.current
                setRadiusComparison(nextRadius > previous.radius ? { from: previous.radius, count: previous.count, target: nextRadius } : null)
                setRadius(String(nextRadius))
              }} aria-label="Bán kính tìm chỗ ở" />
              <span className="radius-marks" aria-hidden="true"><span>5 km</span><span>10 km</span><span>20 km</span><span>30 km</span><span>50 km</span></span>
            </label>
          </div>
          {nearbyLoading ? <LoadingSkeleton count={2} /> : nearby.length ? <div className="nearby-accommodation-grid">{nearby.map((item) => <article className="nearby-accommodation-card" key={item.id}><div className="nearby-card-icon"><MapPin size={19} /></div><div className="nearby-card-copy"><span>{item.category === 'homestay' ? 'Nhà lưu trú' : 'Khách sạn'}</span><h3>{item.name}</h3><p>{item.description}</p><div className="nearby-card-meta"><strong>{Number(item.distance_km).toFixed(1)} km đến điểm đến</strong><span><Star size={14} fill="currentColor" /> {item.rating}</span></div><Link className="nearby-card-link" to={`/cho-o/${item.id}`}>Xem chỗ ở <span aria-hidden="true">→</span></Link></div></article>)}</div> : <p className="detail-muted">Chưa có chỗ ở trong bán kính này.</p>}
          {!nearbyLoading && radiusComparison?.target === Number(radius) && Number(radius) > radiusComparison.from && nearby.length <= radiusComparison.count && <p className="radius-no-additions">Không có thêm chỗ ở nào trong bán kính này</p>}
        </section>
      </div>
      <aside className="destination-aside"><div className="destination-aside-card"><span className="section-kicker">Lên đường khám phá</span><h2>{destination.name}</h2><p>Điểm đến phù hợp đang chờ bạn. Xem gợi ý được cá nhân hóa theo ngày đi và vị trí xuất phát.</p><Link to="/goi-y" className="travel-button travel-button--primary">Tạo hành trình <span aria-hidden="true">→</span></Link></div></aside>
    </div>
  </section>
}

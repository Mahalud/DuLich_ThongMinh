import { Fragment, useEffect, useMemo, useState } from 'react'
import { CircleMarker, MapContainer, Polyline, TileLayer, Tooltip, useMap } from 'react-leaflet'
import { Link, useLocation } from 'react-router-dom'
import { CalendarDays, MapPin, Plus, Route, Trash2 } from 'lucide-react'
import { api, getDestinations, getNearby, getWeather } from '../api'
import { EmptyState, ErrorNotice, TravelImage } from '../components/DesignSystem'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { useOrigin } from '../origin'
import { createEmptyTripPlan, readTripPlan, saveTripPlan } from '../tripPlan'

function localDateString(date = new Date()) {
  const safeDate = date instanceof Date && Number.isFinite(date.getTime()) ? date : new Date()
  return `${safeDate.getFullYear()}-${String(safeDate.getMonth() + 1).padStart(2, '0')}-${String(safeDate.getDate()).padStart(2, '0')}`
}
const money = (value) => `${Number(value || 0).toLocaleString('vi-VN')} đ`

function addDays(dateValue, count) {
  const parsedDate = new Date(`${dateValue}T12:00:00`)
  const date = Number.isFinite(parsedDate.getTime()) ? parsedDate : new Date()
  date.setDate(date.getDate() + count)
  return date
}

function formatDate(dateValue) {
  return new Intl.DateTimeFormat('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(addDays(dateValue, 0))
}

function FitPlanRoute({ points }) {
  const map = useMap()
  useEffect(() => {
    if (points.length === 1) map.setView(points[0], 10)
    else if (points.length > 1) map.fitBounds(points, { padding: [28, 28], maxZoom: 9 })
  }, [map, points])
  return null
}

function TripRouteMap({ segments, originLocation, destinations, activeLegIndex }) {
  const selectedLeg = Number.isInteger(activeLegIndex) && activeLegIndex < segments.length ? activeLegIndex : null
  const visibleSegments = selectedLeg == null ? segments : [segments[selectedLeg]]
  const points = visibleSegments.flat()
  if (!points.length) return null
  const startDestination = selectedLeg != null && selectedLeg > 0 ? destinations[selectedLeg - 1] : null
  const startPosition = startDestination
    ? [Number(startDestination.latitude), Number(startDestination.longitude)]
    : [Number(originLocation.latitude), Number(originLocation.longitude)]
  const startLabel = startDestination ? `Điểm ${selectedLeg}: ${startDestination.name}` : `Xuất phát: ${originLocation.name || 'Vị trí của bạn'}`
  const shownDestinations = selectedLeg == null ? destinations.map((destination, index) => ({ destination, index })) : [{ destination: destinations[selectedLeg], index: selectedLeg }]
  return <MapContainer className="route-map trip-plan-map" center={points[0]} zoom={6} scrollWheelZoom={false} aria-label="Bản đồ các điểm đến trong kế hoạch">
    <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    <FitPlanRoute points={points} />
    {visibleSegments.map((segment, index) => <Fragment key={`leg-${index}`}><Polyline positions={segment} pathOptions={{ color: '#fff', weight: 10, opacity: 0.9 }} /><Polyline positions={segment} pathOptions={{ color: '#176B67', weight: 5, opacity: 1 }} /></Fragment>)}
    <CircleMarker center={startPosition} radius={10} pathOptions={{ color: '#fff', fillColor: '#0B2545', fillOpacity: 1, weight: 4 }}>
      <Tooltip direction="top" permanent className="trip-plan-map-label">{startLabel}</Tooltip>
    </CircleMarker>
    {shownDestinations.map(({ destination, index }) => <CircleMarker key={destination.id} center={[Number(destination.latitude), Number(destination.longitude)]} radius={9} pathOptions={{ color: '#fff', fillColor: '#B9470B', fillOpacity: 1, weight: 4 }}>
      <Tooltip direction="top" permanent className="trip-plan-map-label">Điểm {index + 1}: {destination.name}</Tooltip>
    </CircleMarker>)}
  </MapContainer>
}

export default function TripPlanPage() {
  const location = useLocation()
  const { originLocation } = useOrigin()
  const [plan, setPlan] = useState(readTripPlan)
  const [destinations, setDestinations] = useState([])
  const [destinationId, setDestinationId] = useState('')
  const [nearbyByDestination, setNearbyByDestination] = useState({})
  const [weatherByDestination, setWeatherByDestination] = useState({})
  const [routeLegs, setRouteLegs] = useState([])
  const [activeMapLeg, setActiveMapLeg] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [routeError, setRouteError] = useState('')

  const updatePlan = (update) => setPlan((current) => {
    const next = typeof update === 'function' ? update(current) : update
    saveTripPlan(next)
    return next
  })

  useEffect(() => {
    let active = true
    getDestinations().then((items) => { if (active) setDestinations(Array.isArray(items) ? items : (items?.results || [])) })
      .catch((err) => { if (active) setError(err.message || 'Chưa tải được danh sách điểm đến.') })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  useEffect(() => {
    const requestedId = Number(new URLSearchParams(location.search).get('destination'))
    if (!requestedId || !destinations.some((item) => Number(item.id) === requestedId)) return
    updatePlan((current) => current.stops.some((stop) => stop.destinationId === requestedId)
      ? current
      : { ...current, stops: [...current.stops, { destinationId: requestedId, day: Math.min(current.durationDays, current.stops.length + 1) }] })
  }, [destinations, location.search])

  const stops = useMemo(() => plan.stops
    .map((stop, order) => ({ ...stop, order, destination: destinations.find((item) => Number(item.id) === stop.destinationId) }))
    .filter((stop) => stop.destination)
    .sort((left, right) => left.day - right.day || left.order - right.order), [plan.stops, destinations])

  useEffect(() => { setActiveMapLeg(null) }, [stops.map(({ destination }) => destination.id).join('|')])

  useEffect(() => {
    let active = true
    if (!stops.length) {
      setNearbyByDestination({})
      setWeatherByDestination({})
      return undefined
    }
    Promise.all(stops.map(async ({ destination, day }) => {
      const forecastDate = localDateString(addDays(plan.startDate, day - 1))
      const [nearby, weather] = await Promise.all([
        getNearby(destination.id, 10).catch(() => ({ results: [] })),
        getWeather(destination, forecastDate).catch(() => ({ weather_available: false })),
      ])
      const nearbyResults = Array.isArray(nearby) ? nearby : Array.isArray(nearby?.results) ? nearby.results : []
      return [destination.id, { nearby: nearbyResults.slice(0, 2), weather }]
    })).then((entries) => {
      if (active) {
        setNearbyByDestination(Object.fromEntries(entries.map(([id, value]) => [id, value.nearby])))
        setWeatherByDestination(Object.fromEntries(entries.map(([id, value]) => [id, value.weather])))
      }
    })
    return () => { active = false }
  }, [stops.map(({ destination, day }) => `${destination.id}:${day}`).join('|'), plan.startDate])

  useEffect(() => {
    let active = true
    setRouteError('')
    if (!originLocation || !stops.length) {
      setRouteLegs([])
      return undefined
    }
    const points = stops.map(({ destination }) => [Number(destination.latitude), Number(destination.longitude)])
    const legs = points.map((end, index) => ({
      start: index === 0 ? [Number(originLocation.latitude), Number(originLocation.longitude)] : points[index - 1],
      end,
    }))
    Promise.all(legs.map(({ start, end }) => api(`/api/routes/?start_lat=${start[0]}&start_lng=${start[1]}&end_lat=${end[0]}&end_lng=${end[1]}`)))
      .then((results) => { if (active) setRouteLegs(results) })
      .catch((err) => { if (active) { setRouteLegs([]); setRouteError(err.message || 'Chưa tải được tuyến đường.') } })
    return () => { active = false }
  }, [originLocation?.latitude, originLocation?.longitude, stops.map(({ destination }) => destination.id).join('|')])

  const routeSegments = useMemo(() => routeLegs.map((leg, index) => {
    const geometry = Array.isArray(leg.geometry) ? leg.geometry.filter((point) => Array.isArray(point) && point.length >= 2 && point.slice(0, 2).every((value) => Number.isFinite(Number(value)))) : []
    if (geometry.length >= 2) return geometry
    const end = [Number(stops[index]?.destination.latitude), Number(stops[index]?.destination.longitude)]
    const start = index === 0
      ? [Number(originLocation?.latitude), Number(originLocation?.longitude)]
      : [Number(stops[index - 1]?.destination.latitude), Number(stops[index - 1]?.destination.longitude)]
    return [...(start.every(Number.isFinite) ? [start] : []), ...(end.every(Number.isFinite) ? [end] : [])]
  }), [routeLegs, stops, originLocation?.latitude, originLocation?.longitude])
  const mapPoints = useMemo(() => routeSegments.flat(), [routeSegments])
  const estimatedCost = stops.reduce((total, stop) => total + Number(stop.destination.reference_cost || 0), 0)
  const totalDistance = routeLegs.reduce((total, leg) => total + Number(leg.distance_km || 0), 0)
  const totalDuration = routeLegs.reduce((total, leg) => total + Number(leg.duration_minutes || 0), 0)
  const lastDestination = stops.at(-1)?.destination
  const googleMapsUrl = originLocation && lastDestination
    ? `https://www.google.com/maps/dir/?api=1&origin=${originLocation.latitude},${originLocation.longitude}&destination=${lastDestination.latitude},${lastDestination.longitude}${stops.length > 1 ? `&waypoints=${stops.slice(0, -1).map(({ destination }) => `${destination.latitude},${destination.longitude}`).join('|')}` : ''}&travelmode=driving`
    : ''

  const addDestination = () => {
    const id = Number(destinationId)
    if (!id || plan.stops.some((stop) => stop.destinationId === id)) return
    updatePlan((current) => ({ ...current, stops: [...current.stops, { destinationId: id, day: Math.min(current.durationDays, current.stops.length + 1) }] }))
    setDestinationId('')
  }

  const removeStop = (id) => updatePlan((current) => ({ ...current, stops: current.stops.filter((stop) => Number(stop.destinationId) !== Number(id)) }))
  const assignDay = (id, day) => updatePlan((current) => ({ ...current, stops: current.stops.map((stop) => Number(stop.destinationId) === Number(id) ? { ...stop, day: Number(day) } : stop) }))
  const clearPlan = () => updatePlan(createEmptyTripPlan())

  return <section className="trip-plan-page page-shell">
    <header className="trip-plan-heading">
      <span className="section-kicker">LỊCH TRÌNH CỦA BẠN</span>
      <h1>Kế hoạch chuyến đi</h1>
      <p>Chọn điểm đến, xếp từng ngày và xem thời tiết, chỗ ở cùng tuyến đường dự kiến trong một nơi.</p>
    </header>

    <section className="trip-plan-controls detail-surface" aria-label="Thông tin kế hoạch">
      <label>Ngày bắt đầu<input type="date" min={localDateString()} value={plan.startDate || localDateString()} onChange={(event) => updatePlan((current) => ({ ...current, startDate: event.target.value || localDateString() }))} /></label>
      <label>Số ngày<select value={plan.durationDays} onChange={(event) => {
        const durationDays = Number(event.target.value)
        updatePlan((current) => ({ ...current, durationDays, stops: current.stops.map((stop) => ({ ...stop, day: Math.min(stop.day, durationDays) })) }))
      }}>{Array.from({ length: 14 }, (_, index) => <option value={index + 1} key={index + 1}>{index + 1} ngày</option>)}</select></label>
      <label className="trip-plan-add-select">Thêm điểm đến<select value={destinationId} onChange={(event) => setDestinationId(event.target.value)}>
        <option value="">Chọn điểm đến</option>
        {destinations.filter((item) => !plan.stops.some((stop) => stop.destinationId === Number(item.id))).map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
      </select></label>
      <button type="button" className="travel-button travel-button--primary" onClick={addDestination} disabled={!destinationId}><Plus size={17} /> Thêm điểm</button>
    </section>

    {error && <ErrorNotice>{error}</ErrorNotice>}
    {loading ? <LoadingSkeleton count={2} /> : <>
      <section className="trip-plan-summary" aria-label="Tóm tắt kế hoạch">
        <article><strong>{stops.length}</strong><span>điểm đến</span></article>
        <article><strong>{plan.durationDays}</strong><span>ngày dự kiến</span></article>
        <article><strong>{money(estimatedCost)}</strong><span>mức tham khảo cộng theo điểm đến</span></article>
        <button type="button" className="trip-plan-clear" onClick={clearPlan} disabled={!plan.stops.length}><Trash2 size={16} /> Xóa kế hoạch</button>
      </section>

      <section className="detail-surface trip-plan-route-section">
        <div className="detail-section-heading"><span className="detail-icon"><Route size={20} /></span><div><h2>Tuyến đường dự kiến</h2><p>{originLocation ? 'Tuyến nối vị trí xuất phát với các điểm đến theo thứ tự ngày.' : 'Chọn vị trí xuất phát để dựng tuyến tổng thể.'}</p></div></div>
        {!originLocation ? <div className="trip-plan-origin-note"><p>Chưa có vị trí xuất phát trong ứng dụng.</p><Link className="travel-button travel-button--outline" to="/goi-y">Chọn vị trí xuất phát</Link></div>
          : !stops.length ? <p className="detail-muted">Thêm ít nhất một điểm đến để xem tuyến.</p>
            : routeError ? <ErrorNotice>{routeError}</ErrorNotice>
              : routeLegs.length !== stops.length ? <p className="detail-muted">Đang tính tuyến đường giữa các điểm…</p>
                : <><div className="trip-plan-route-meta"><strong>{totalDistance.toFixed(1)} km</strong><span>·</span><span>{Math.floor(totalDuration / 60)} giờ {totalDuration % 60} phút ước tính</span></div><p className="trip-plan-route-sequence">{[originLocation.name || 'Vị trí của bạn', ...stops.map(({ destination }) => destination.name)].join('  →  ')}</p><div className="trip-plan-map-filters" role="group" aria-label="Chọn phạm vi bản đồ"><button type="button" className={activeMapLeg === null ? 'is-active' : ''} aria-pressed={activeMapLeg === null} onClick={() => setActiveMapLeg(null)}>Toàn tuyến</button>{stops.map(({ destination }, index) => <button type="button" className={activeMapLeg === index ? 'is-active' : ''} aria-pressed={activeMapLeg === index} key={destination.id} onClick={() => setActiveMapLeg(index)}>Chặng {index + 1}</button>)}</div><TripRouteMap segments={routeSegments} originLocation={originLocation} destinations={stops.map(({ destination }) => destination)} activeLegIndex={activeMapLeg} /><div className="trip-plan-map-legend"><span><i className="is-origin" />Vị trí xuất phát</span>{stops.map(({ destination }, index) => <span key={destination.id}><i>{index + 1}</i>{destination.name}</span>)}</div><ol className="trip-plan-route-legs">{stops.map(({ destination }, index) => <li key={destination.id}><span>{index === 0 ? originLocation.name || 'Vị trí của bạn' : stops[index - 1].destination.name} <b aria-hidden="true">→</b> {destination.name}</span><strong>{Number(routeLegs[index]?.distance_km || 0).toFixed(1)} km · {Number(routeLegs[index]?.duration_minutes || 0)} phút</strong></li>)}</ol><p className="trip-plan-route-note">Chọn “Toàn tuyến” để xem cả hành trình, hoặc chọn một chặng để phóng to khu vực đó.</p><a className="travel-button travel-button--outline route-google-link" href={googleMapsUrl} target="_blank" rel="noreferrer">Mở tuyến trên Google Maps</a></>}
      </section>

      {!stops.length ? <EmptyState title="Kế hoạch đang trống" description="Thêm một điểm đến ở trên hoặc bấm “Lập kế hoạch” từ trang chi tiết điểm đến để bắt đầu." /> : <div className="trip-plan-days">
        {Array.from({ length: plan.durationDays }, (_, dayIndex) => {
          const day = dayIndex + 1
          const date = localDateString(addDays(plan.startDate, dayIndex))
          const dayStops = stops.filter((stop) => stop.day === day)
          return <section className="detail-surface trip-plan-day" key={day}>
            <header className="trip-plan-day-heading"><span className="trip-plan-day-number">{day}</span><div><h2>Ngày {day}</h2><p><CalendarDays size={15} /> {formatDate(date)}</p></div></header>
            {dayStops.length ? <div className="trip-plan-stop-list">{dayStops.map(({ destination, order }) => {
              const weather = weatherByDestination[destination.id]
              const nearby = nearbyByDestination[destination.id] || []
              return <article className="trip-plan-stop" key={destination.id}>
                <TravelImage src={destination.image_url} alt={destination.name} aspectRatio="4 / 3" width="480" height="360" />
                <div className="trip-plan-stop-copy"><div className="trip-plan-stop-title"><span><MapPin size={15} /> Điểm {order + 1}</span><button type="button" className="trip-plan-remove" onClick={() => removeStop(destination.id)} aria-label={`Xóa ${destination.name} khỏi kế hoạch`}><Trash2 size={16} /></button></div>
                  <h3><Link to={`/diem-den/${destination.id}`}>{destination.name}</Link></h3><p>{destination.category} · {destination.address || 'Việt Nam'}</p>
                  <label className="trip-plan-day-select">Xếp vào ngày<select value={day} onChange={(event) => assignDay(destination.id, event.target.value)}>{Array.from({ length: plan.durationDays }, (_, index) => <option key={index + 1} value={index + 1}>Ngày {index + 1}</option>)}</select></label>
                  <div className="trip-plan-facts"><span>{money(destination.reference_cost)} / mức tham khảo</span>{weather?.weather_available && weather.weather ? <span>{Math.round(Number(weather.weather.temperature_c))}°C · mưa {Math.round(Number(weather.weather.rain_probability))}% · gió {Math.round(Number(weather.weather.wind_kmh))} km/h</span> : weather ? <span>Chưa có dữ liệu thời tiết</span> : <span>Đang tải thời tiết…</span>}</div>
                  <div className="trip-plan-stays"><strong>Chỗ ở quanh điểm đến</strong>{nearby.length ? nearby.map((stay) => <Link to={`/cho-o/${stay.id}`} key={stay.id}>{stay.name}<span>{Number(stay.distance_km).toFixed(1)} km</span></Link>) : <small>Chưa có gợi ý chỗ ở trong 10 km.</small>}</div>
                </div>
              </article>
            })}</div> : <div className="trip-plan-empty-day"><p>Chưa xếp điểm đến cho ngày này.</p><span>Dùng lựa chọn “Xếp vào ngày” trên thẻ điểm đến.</span></div>}
          </section>
        })}
      </div>}
      <p className="trip-plan-disclaimer">Chi phí là tổng mức tham khảo trong dữ liệu của từng điểm đến cho khoảng 3 ngày 2 đêm, một người; không phải báo giá đặt phòng hay tour.</p>
    </>}
  </section>
}

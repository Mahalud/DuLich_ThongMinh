import { useEffect, useRef, useState } from 'react'
import { lookupDestinations, reverseLookupDestination } from '../api'
import { useOrigin } from '../origin'

export const PREFERENCE_QUICK_CHOICES = ['biển', 'núi', 'ẩm thực', 'văn hóa', 'nghỉ dưỡng', 'mạo hiểm']
const WEATHER_PREFERENCE_CHOICES = [['balanced', 'Mặc định'], ['cool', 'Mát mẻ'], ['warm', 'Nắng ấm'], ['dry', 'Ít mưa']]

export function PreferenceChips({ value = '', onChange, choices = PREFERENCE_QUICK_CHOICES, label = 'Chọn nhanh sở thích' }) {
  const selectedItems = String(value || '').split(',').map((item) => item.trim()).filter(Boolean)
  const toggle = (preference) => {
    const exists = selectedItems.some((item) => item.toLocaleLowerCase('vi') === preference.toLocaleLowerCase('vi'))
    onChange((exists ? selectedItems.filter((item) => item.toLocaleLowerCase('vi') !== preference.toLocaleLowerCase('vi')) : [...selectedItems, preference]).join(', '))
  }
  return <span className="quick-preferences" aria-label={label}>{choices.map((preference) => {
    const selected = selectedItems.some((item) => item.toLocaleLowerCase('vi') === preference.toLocaleLowerCase('vi'))
    return <button key={preference} type="button" className={`quick-preference ${selected ? 'is-selected' : ''}`} onClick={() => toggle(preference)} aria-pressed={selected}>{preference}</button>
  })}</span>
}

export function WeatherPreferenceChips({ value = 'balanced', onChange }) {
  return <fieldset className="weather-preference-field"><legend>Thời tiết mong muốn</legend><div className="weather-preference-chips">{WEATHER_PREFERENCE_CHOICES.map(([choice, label]) => <button key={choice} type="button" className={`quick-preference ${value === choice ? 'is-selected' : ''}`} aria-pressed={value === choice} onClick={() => onChange(choice)}>{label}</button>)}</div></fieldset>
}

const localDateString = (value) => `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`
export const today = localDateString(new Date())
export const latestTravelDate = (() => { const latest = new Date(); latest.setDate(latest.getDate() + 15); return localDateString(latest) })()
export const defaultRecommendationForm = { user_preferences: 'biển, ẩm thực', budget_estimate: '6000000', travel_date: today, top_n: '5', weather_preference: 'balanced' }

const locationHelp = 'Hãy cho phép vị trí trong thanh địa chỉ trình duyệt và bật Dịch vụ vị trí (Location) trong cài đặt quyền riêng tư của Windows. Bạn cũng có thể tìm thành phố hoặc khu vực bên dưới.'

export default function RecommendationForm({ initialValues = defaultRecommendationForm, submitLabel = 'Tạo gợi ý', onSubmit, onFormChange, quickChips = [] }) {
  const { originLocation, setOriginLocation } = useOrigin()
  const [form, setForm] = useState({ ...defaultRecommendationForm, ...initialValues })
  const [error, setError] = useState('')
  const [locationError, setLocationError] = useState('')
  const [locating, setLocating] = useState(false)
  const [lookupQuery, setLookupQuery] = useState('')
  const [lookupResults, setLookupResults] = useState([])
  const [lookupLoading, setLookupLoading] = useState(false)
  const lookupSequence = useRef(0)

  useEffect(() => setForm({ ...defaultRecommendationForm, ...initialValues }), [initialValues])
  useEffect(() => { onFormChange?.(form) }, [form, onFormChange])
  useEffect(() => {
    const query = lookupQuery.trim()
    if (originLocation || query.length < 3) { lookupSequence.current += 1; setLookupResults([]); setLookupLoading(false); return undefined }
    const sequence = ++lookupSequence.current
    const timer = window.setTimeout(async () => {
      setLookupLoading(true)
      setLocationError('')
      try {
        const data = await lookupDestinations(query)
        const places = (data.results || []).filter((place) => Number.isFinite(Number(place.latitude)) && Number.isFinite(Number(place.longitude)) && (Number(place.latitude) !== 0 || Number(place.longitude) !== 0))
        if (sequence === lookupSequence.current) {
          setLookupResults(places)
          if (!places.length) setLocationError('Không tìm thấy địa điểm có tọa độ phù hợp. Hãy thử tên thành phố hoặc khu vực khác.')
        }
      } catch (requestError) {
        if (sequence === lookupSequence.current) setLocationError(requestError.message || 'Chưa thể tìm địa điểm lúc này.')
      } finally {
        if (sequence === lookupSequence.current) setLookupLoading(false)
      }
    }, 400)
    return () => window.clearTimeout(timer)
  }, [lookupQuery, originLocation])

  const change = (event) => setForm({ ...form, [event.target.name]: event.target.value })
  const selectLocation = (place) => {
    setOriginLocation({ name: place.name || place.full_name, latitude: Number(place.latitude), longitude: Number(place.longitude) })
    setLookupQuery('')
    setLookupResults([])
    setLocationError('')
  }

  const useCurrentLocation = () => {
    setLocationError('')
    if (!navigator.geolocation) { setLocationError(`Trình duyệt không hỗ trợ định vị. ${locationHelp}`); return }
    setLocating(true)
    navigator.geolocation.getCurrentPosition(async ({ coords }) => {
      try {
        const place = await reverseLookupDestination(coords.latitude, coords.longitude)
        setOriginLocation({ name: place.name, latitude: Number(coords.latitude), longitude: Number(coords.longitude) })
        setLocationError('')
      } catch (requestError) {
        setLocationError(`${requestError.message || 'Chưa xác định được tên nơi đang ở.'} ${locationHelp}`)
      } finally { setLocating(false) }
    }, (geoError) => {
      const reason = geoError.code === 1 ? 'Bạn đã từ chối quyền truy cập vị trí.' : geoError.code === 2 ? 'Thiết bị chưa xác định được vị trí.' : 'Yêu cầu lấy vị trí đã hết thời gian chờ.'
      setLocationError(`${reason} ${locationHelp}`)
      setLocating(false)
    }, { enableHighAccuracy: true, timeout: 12000, maximumAge: 60000 })
  }

  const submit = (event) => {
    event.preventDefault()
    if (!form.user_preferences.trim() || !form.budget_estimate || !form.travel_date) return setError('Vui lòng điền sở thích, ngân sách và ngày đi.')
    if (form.travel_date < today || form.travel_date > latestTravelDate) return setError('Ngày đi cần nằm trong 16 ngày tới để có dự báo thời tiết.')
    const payload = { ...form }
    if (originLocation) {
      payload.latitude = String(originLocation.latitude)
      payload.longitude = String(originLocation.longitude)
    } else {
      delete payload.latitude
      delete payload.longitude
    }
    setError('')
    onSubmit(payload)
  }

  return <>
    <form className="recommend-form" onSubmit={submit}>
      <div className="recommend-preference-field">
        <label htmlFor="recommend-preferences">Sở thích</label>
        <input id="recommend-preferences" name="user_preferences" value={form.user_preferences} onChange={change} required />
        {quickChips.length > 0 && <PreferenceChips value={form.user_preferences} onChange={(user_preferences) => setForm((previous) => ({ ...previous, user_preferences }))} choices={quickChips} />}
      </div>
      <label>Ngân sách<input name="budget_estimate" type="number" min="0" value={form.budget_estimate} onChange={change} required /></label>
      <WeatherPreferenceChips value={form.weather_preference} onChange={(weather_preference) => setForm((previous) => ({ ...previous, weather_preference }))} />
      <div className="recommend-location">
        <span className="recommend-location-title">Vị trí xuất phát</span>
        {originLocation ? <p className="location-success" role="status">Xuất phát từ: <strong>{originLocation.name}</strong> <button className="secondary-btn" type="button" onClick={() => { setOriginLocation(null); setLookupQuery(''); setLocationError('') }}>(đổi)</button></p> : <>
          <button className="secondary-btn" type="button" onClick={useCurrentLocation} disabled={locating}>{locating ? 'Đang xác định vị trí…' : 'Dùng vị trí hiện tại'}</button>
          <div className="recommend-location-search"><label htmlFor="recommend-location-query">Tìm thành phố hoặc khu vực
              <input id="recommend-location-query" type="search" value={lookupQuery} onChange={(event) => setLookupQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter' && lookupResults.length) { event.preventDefault(); selectLocation(lookupResults[0]) } }} placeholder="Ví dụ: Đà Lạt" autoComplete="off" />
            </label></div>
          {lookupLoading && <p className="detail-muted" role="status">Đang tìm địa điểm…</p>}
          {lookupResults.length > 0 && <ul className="recommend-location-results" aria-label="Gợi ý địa điểm">{lookupResults.map((place, index) => <li key={`${place.latitude}-${place.longitude}-${index}`}><button type="button" onClick={() => selectLocation(place)}><strong>{place.name}</strong><span>{place.full_name}</span></button></li>)}</ul>}
        </>}
        {locationError && <p className="form-error" role="alert">{locationError}</p>}
      </div>
      <label>Ngày đi<input name="travel_date" type="date" min={today} max={latestTravelDate} value={form.travel_date} onChange={change} required /><small>Dự báo thời tiết tối đa 16 ngày</small></label>
      <label>Số gợi ý<input name="top_n" type="number" min="1" max="10" value={form.top_n} onChange={change} required /></label>
      <button className="primary-btn">{submitLabel}</button>
    </form>
    {error && <p className="form-error">{error}</p>}
  </>
}

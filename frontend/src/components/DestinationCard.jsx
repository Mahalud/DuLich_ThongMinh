import { Link } from 'react-router-dom'
import { ArrowRight, CloudRain, CloudSun, Star, Wind } from 'lucide-react'
import { CategoryChip, TravelImage } from './DesignSystem'

const SCORE_PARTS = [
  ['preference_score', 'preference', 'Sở thích', 'preference'],
  ['weather_score', 'weather', 'Thời tiết', 'weather'],
  ['budget_score', 'budget', 'Ngân sách', 'budget'],
  ['distance_score', 'distance', 'Khoảng cách', 'distance'],
]

function scorePercent(value) {
  const numeric = Number(value || 0)
  return Math.round(Math.max(0, Math.min(1, numeric)) * 100)
}

export default function DestinationCard({ destination, score, onViewDetail, rank = 1, criteriaUsed, isCompared = false, onToggleCompare }) {
  const usedCriteria = Array.isArray(criteriaUsed)
    ? criteriaUsed
    : SCORE_PARTS.filter(([key]) => destination[key] != null).map(([, criterion]) => criterion)
  return <article className="recommendation-card">
    <div className="recommendation-card-media">
      <TravelImage src={destination.image_url} alt={destination.name} aspectRatio="16 / 10" width="1000" height="625" />
      <span className="recommendation-rank">#{rank}</span>
      <span className="recommendation-score">{Math.round(Number(score || 0) * 100)}<small> điểm</small></span>
    </div>
    <div className="recommendation-card-body">
      <div className="recommendation-card-title"><CategoryChip className="recommendation-category">{destination.category}</CategoryChip><span className="recommendation-rating"><Star size={15} fill="currentColor" /> {Number(destination.rating || 0).toFixed(1)}</span></div>
      <h2>{destination.name}</h2>
      <p className="recommendation-description">{destination.description}</p>
      <div className="score-breakdown" aria-label="Điểm thành phần của gợi ý">
        {SCORE_PARTS.filter(([key, criterion]) => usedCriteria.includes(criterion) && destination[key] != null).map(([key, criterion, label, tone]) => {
          const percent = scorePercent(destination[key])
          const unmatchedPreference = criterion === 'preference' && destination.preference_matched === false
          const budgetStatus = criterion === 'budget' && (destination.budget_overage > 0
            ? `Vượt ngân sách ${Number(destination.budget_overage).toLocaleString('vi-VN')} đ so với chi phí ước tính`
            : 'Trong ngân sách')
          return <div className={`score-breakdown-row${unmatchedPreference ? ' is-unmatched' : ''}`} key={key}>
            <span>{label}</span><div className="score-track"><span className={`score-fill score-fill--${tone}`} style={{ width: `${percent}%` }} /></div>
            <strong>{unmatchedPreference ? 'Chưa khớp' : `${percent}%`}</strong>
            {budgetStatus && <small className="score-breakdown-note">{budgetStatus}</small>}
          </div>
        })}
      </div>
      {destination.weather_available && destination.weather && <div className="recommendation-weather-data" aria-label="Số liệu thời tiết ngày đi">
        <span><CloudSun size={16} aria-hidden="true" /> {Math.round(Number(destination.weather.temperature_c))}°C</span>
        <span><CloudRain size={16} aria-hidden="true" /> mưa {Math.round(Number(destination.weather.rain_probability))}%</span>
        <span><Wind size={16} aria-hidden="true" /> gió {Math.round(Number(destination.weather.wind_kmh))} km/h</span>
        <small>{destination.weather.summary}</small>
      </div>}
      {!destination.weather_available && <p className="recommendation-weather-unavailable">Chưa có dữ liệu thời tiết</p>}
      <div className="recommendation-card-footer">
        <div className="recommendation-card-meta">{destination.distance_km != null && <span>{destination.distance_km} km</span>}<span>Ngân sách ước tính {Number(destination.estimated_cost || 0).toLocaleString('vi-VN')} đ</span></div>
        <div className="recommendation-card-actions">
          <button className={`compare-toggle${isCompared ? ' is-selected' : ''}`} type="button" aria-pressed={isCompared} onClick={() => onToggleCompare?.(destination)}>{isCompared ? 'Đã chọn so sánh' : 'So sánh'}</button>
          <Link className="recommendation-detail-link" to={`/diem-den/${destination.id}`} onClick={() => onViewDetail?.(destination)}>Xem chi tiết <ArrowRight size={16} /></Link>
          <Link className="recommendation-plan-link" to={`/ke-hoach?destination=${destination.id}`}>Lập kế hoạch</Link>
        </div>
      </div>
    </div>
  </article>
}

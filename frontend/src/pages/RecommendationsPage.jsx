import { useEffect, useState, useRef } from 'react'
import {
  api,
  getRecommendations,
  getRecommendationExplanationTask,
  getTaskStatus,
  sendRecommendationFeedback,
} from '../api'
import DestinationCard from '../components/DestinationCard'
import LoadingSkeleton from '../components/LoadingSkeleton'
import RecommendationForm, { defaultRecommendationForm, PREFERENCE_QUICK_CHOICES } from '../components/RecommendationForm'
import NaturalQueryBox from '../components/NaturalQueryBox'
import { EmptyState, ErrorNotice } from '../components/DesignSystem'
import { useAuth } from '../auth'
import { useOrigin } from '../origin'

const EXPLANATION_TIMEOUT_MS = 25_000
const POLL_INTERVAL_MS = 1_500

function makeLocalExplanation(form, destination) {
  if (!destination) return 'Hiện chưa có điểm đến phù hợp để giải thích theo bộ tiêu chí này.'
  const dateValue = form.travel_date
    ? new Intl.DateTimeFormat('vi-VN', { timeZone: 'UTC', day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(`${form.travel_date}T00:00:00Z`))
    : 'chưa chọn ngày đi'
  const budget = Number(form.budget_estimate || 0)
  const budgetLabel = budget ? `${new Intl.NumberFormat('vi-VN').format(budget)}đ` : 'linh hoạt'
  const weather = destination.weather_available && destination.weather?.temperature_c != null
    ? ` Dự báo ngày đi: ${destination.weather.temperature_c}°C, mưa ${destination.weather.rain_probability}%, gió ${destination.weather.wind_kmh} km/h.`
    : destination.weather_available === false ? ' Chưa có dữ liệu thời tiết cho ngày đi.' : ''
  const category = destination.category ? ` (${destination.category})` : ''
  let budgetText = ' Ngân sách chưa được cung cấp nên không được dùng làm tiêu chí xếp hạng.'
  if (budget) {
    const estimate = Number(destination.estimated_cost || 0)
    const estimateLabel = new Intl.NumberFormat('vi-VN').format(estimate)
    budgetText = estimate > budget
      ? ` Chi phí tham khảo ${estimateLabel}đ, vượt ngân sách ${new Intl.NumberFormat('vi-VN').format(estimate - budget)}đ.`
      : ` Chi phí tham khảo ${estimateLabel}đ, trong ngân sách ${budgetLabel}.`
  }
  let preferenceText = ''
  if (destination.preference_matched === true && form.user_preferences?.trim()) {
    preferenceText = ` Kết quả có xét tiêu chí sở thích “${form.user_preferences.trim()}”.`
  }
  const distanceText = destination.distance_km != null && destination.criteria_used?.includes('distance')
    ? ` Khoảng cách từ vị trí xuất phát là ${destination.distance_km} km.` : ''
  return `${destination.name}${category} đang đứng đầu kết quả cho ngày ${dateValue}.${preferenceText}${budgetText}${weather}${distanceText}`
}

export default function RecommendationsPage() {
  const { user, status: authStatus, authError, retryAuth } = useAuth()
  const { originLocation } = useOrigin()
  const [data, setData] = useState({ results: [] })
  const [formInitialValues, setFormInitialValues] = useState({ ...defaultRecommendationForm })
  const formValuesRef = useRef({ ...defaultRecommendationForm })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [explanation, setExplanation] = useState('')
  const [streamedExplanation, setStreamedExplanation] = useState('')
  const [explanationLoading, setExplanationLoading] = useState(false)
  const pollTimerRef = useRef(null)
  const deadlineTimerRef = useRef(null)
  const requestSequenceRef = useRef(0)
  const explanationAttemptRef = useRef(0)

  const stopPolling = () => {
    if (pollTimerRef.current) {
      clearInterval(pollTimerRef.current)
      pollTimerRef.current = null
    }
    if (deadlineTimerRef.current) {
      clearTimeout(deadlineTimerRef.current)
      deadlineTimerRef.current = null
    }
  }

  useEffect(() => {
    return () => { requestSequenceRef.current += 1; stopPolling() }
  }, [])

  useEffect(() => {
    setStreamedExplanation('')
    if (!explanation) return undefined
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setStreamedExplanation(explanation)
      return undefined
    }
    let index = 0
    const timer = window.setInterval(() => {
      index = Math.min(index + 3, explanation.length)
      setStreamedExplanation(explanation.slice(0, index))
      if (index >= explanation.length) window.clearInterval(timer)
    }, 28)
    return () => window.clearInterval(timer)
  }, [explanation])

  const loadExplanation = (form, results, requestId, criteriaUsed) => {
    stopPolling()
    const attemptId = ++explanationAttemptRef.current
    setExplanationLoading(true)
    setExplanation('')
    const destinationIds = (results || []).slice(0, 3).map((item) => item.id)
    const localFallback = makeLocalExplanation(
      form,
      results?.[0] ? { ...results[0], criteria_used: criteriaUsed } : null,
    )

    deadlineTimerRef.current = setTimeout(() => {
      if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
      stopPolling()
      explanationAttemptRef.current += 1
      setExplanation(localFallback)
      setExplanationLoading(false)
    }, EXPLANATION_TIMEOUT_MS)

    getRecommendationExplanationTask(form, destinationIds, results?.[0] ? { ...results[0], criteria_used: criteriaUsed } : null)
      .then((res) => {
        if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
        if (res.task_id) {
          const poll = () => {
            if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
            getTaskStatus(res.task_id)
              .then((statusRes) => {
                if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
                if (statusRes.status === 'done') {
                  stopPolling()
                  const resultText = statusRes.result?.explanation || localFallback
                  setExplanation(resultText)
                  setExplanationLoading(false)
                } else if (statusRes.status === 'failed') {
                  stopPolling()
                  setExplanation(localFallback)
                  setExplanationLoading(false)
                }
              })
              .catch(() => {
                if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
                stopPolling()
                setExplanation(localFallback)
                setExplanationLoading(false)
              })
          }
          pollTimerRef.current = setInterval(poll, POLL_INTERVAL_MS)
          poll()
        } else if (res.explanation) {
          stopPolling()
          setExplanation(res.explanation)
          setExplanationLoading(false)
        } else {
          stopPolling()
          setExplanation(localFallback)
          setExplanationLoading(false)
        }
      })
      .catch(() => {
        if (requestId !== requestSequenceRef.current || attemptId !== explanationAttemptRef.current) return
        stopPolling()
        setExplanation(localFallback)
        setExplanationLoading(false)
      })
  }

  const load = (form) => {
    formValuesRef.current = form
    const requestId = ++requestSequenceRef.current
    stopPolling()
    setLoading(true)
    setError('')
    setExplanationLoading(false)
    setExplanation('')
    explanationAttemptRef.current += 1
    getRecommendations(form)
      .then((res) => {
        if (requestId !== requestSequenceRef.current) return
        setData(res)
        if (res.results?.length) loadExplanation(form, res.results, requestId, res.criteria_used)
        else setExplanationLoading(false)
      })
      .catch((err) => { if (requestId === requestSequenceRef.current) setError(err.message) })
      .finally(() => { if (requestId === requestSequenceRef.current) setLoading(false) })
  }

  const applyNaturalQuery = (parsed) => {
    const nextForm = { ...formValuesRef.current }
    const preferences = [...(parsed.preference_labels || []), parsed.preference_text].filter(Boolean).join(', ')
    if (preferences) nextForm.user_preferences = preferences
    if (parsed.budget_vnd != null) nextForm.budget_estimate = String(parsed.budget_vnd)
    if (parsed.travel_date) nextForm.travel_date = parsed.travel_date
    if (parsed.weather_preference) nextForm.weather_preference = parsed.weather_preference
    formValuesRef.current = nextForm
    setFormInitialValues(nextForm)
    const payload = { ...nextForm }
    if (originLocation) {
      payload.latitude = String(originLocation.latitude)
      payload.longitude = String(originLocation.longitude)
    }
    load(payload)
  }

  const recordViewedDetail = (destination) =>
    sendRecommendationFeedback({
      destination_id: destination.id,
      action: 'viewed_detail',
      preference_score: destination.preference_score,
      weather_score: destination.weather_score,
      budget_score: destination.budget_score,
      distance_score: destination.distance_score,
    }).catch(() => {})

  const weights = data.weights_used || (originLocation ? { w1: 0.4, w2: 0.25, w3: 0.2, w4: 0.15 } : { w1: 0.470588, w2: 0.294118, w3: 0.235294, w4: 0 })
  const criteria = data.criteria_used || ['preference', 'weather', 'budget', ...(originLocation ? ['distance'] : [])]
  const criterionWeights = [
    ['preference', 'w1', 'Sở thích'], ['weather', 'w2', 'Thời tiết'],
    ['budget', 'w3', 'Ngân sách'], ['distance', 'w4', 'Khoảng cách'],
  ]
  const weightLine = `Trọng số đang dùng: ${criterionWeights.filter(([key]) => criteria.includes(key)).map(([, key, label]) => `${label} ${Math.round(weights[key] * 100)}%`).join(' · ')}.`

  useEffect(() => {
    let active = true
    const initialize = async () => {
      if (authStatus === 'loading') return
      const query = new URLSearchParams(window.location.search)
      let form = { ...defaultRecommendationForm }
      Object.keys(form).forEach((key) => { if (query.has(key)) form[key] = query.get(key) })
      const hasRestoredCriteria = Object.keys(defaultRecommendationForm).some((key) => query.has(key))
      if (!hasRestoredCriteria && user) {
        try {
          const profile = await api(`/api/profile/${user.id}/`)
          form = {
            ...form,
            user_preferences: (profile.travel_preferences || []).join(', '),
            budget_estimate: String(profile.budget_estimate ?? form.budget_estimate),
            weather_preference: profile.weather_preference || 'balanced',
          }
        } catch {}
      }
      if (active) { setFormInitialValues(form); load(form) }
    }
    initialize()
    return () => { active = false }
  }, [authStatus, user?.id])

  return (
    <section className="recommend recommendations-page">
      <div className="section-head recommendations-heading">
        <span className="eyebrow dark">Dành riêng cho hành trình của bạn</span>
        <h1>Những nơi hợp với bạn</h1>
        <section className="recommendation-explanation" aria-live="polite" aria-busy={explanationLoading}>
          {explanationLoading ? <div className="explanation-skeleton" aria-hidden="true"><span /><span /><span /></div> : <p className="recommendation-intro"><span className="ai-explanation">{explanation ? streamedExplanation : data.explanation || 'Xếp hạng dựa trên sở thích, thời tiết, ngân sách và khoảng cách.'}</span></p>}
        </section>
        <small className="weights-caption">{weightLine}</small>
        {(data.notes || []).map((note) => <small className="weights-caption recommendation-note" key={note}>{note}</small>)}
      </div>
      <NaturalQueryBox onApply={applyNaturalQuery} />
      <div className="recommendation-filter-card"><h2>Điều chỉnh tiêu chí</h2><RecommendationForm initialValues={formInitialValues} submitLabel="Cập nhật gợi ý" onSubmit={load} onFormChange={(form) => { formValuesRef.current = form }} quickChips={PREFERENCE_QUICK_CHOICES} /></div>
      {authStatus === 'loading' && authError && <ErrorNotice>{authError} <button className="travel-button travel-button--outline" type="button" onClick={retryAuth}>Thử lại</button></ErrorNotice>}
      {error && <ErrorNotice>{error}</ErrorNotice>}
      {loading ? (
        <LoadingSkeleton />
      ) : data.results.length ? (
        <div className="destination-grid recommendation-results">
          {data.results.map((item, index) => (
            <DestinationCard
              key={item.id}
              destination={item}
              score={item.score}
              rank={index + 1}
              criteriaUsed={data.criteria_used}
              onViewDetail={recordViewedDetail}
            />
          ))}
        </div>
      ) : <EmptyState title="Chưa tìm thấy điểm đến phù hợp" description="Thử điều chỉnh sở thích, ngân sách hoặc vị trí xuất phát để mở rộng lựa chọn." />}
    </section>
  )
}

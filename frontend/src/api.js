export const backendUrl = 'http://localhost:8000'

const csrfToken = () => document.cookie.split('; ').find((item) => item.startsWith('csrftoken='))?.split('=')[1] || ''

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.method && options.method !== 'GET') headers['X-CSRFToken'] = csrfToken()
  const response = await fetch(`${backendUrl}${path}`, { credentials: 'include', ...options, headers })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const backendMessage = data.detail || data.error || data.non_field_errors?.[0]
    const genericErrors = {
      400: 'Thông tin chưa hợp lệ. Vui lòng kiểm tra lại.',
      401: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
      403: 'Bạn không có quyền thực hiện thao tác này.',
      404: 'Không tìm thấy nội dung bạn yêu cầu.',
      500: 'Máy chủ đang gặp sự cố. Vui lòng thử lại sau.',
    }
    const error = new Error(backendMessage || genericErrors[response.status] || 'Không thể kết nối với máy chủ. Vui lòng thử lại sau.')
    error.status = response.status
    error.code = data.code
    error.retryAfterSeconds = data.retry_after_seconds
    throw error
  }
  return data
}

export const getDestinations = () => api('/api/destinations/')
export const lookupDestinations = (query) => api(`/api/destinations/lookup/?q=${encodeURIComponent(query)}&include_image=false`)
export const reverseLookupDestination = (latitude, longitude) => api(`/api/destinations/reverse-lookup/?latitude=${encodeURIComponent(latitude)}&longitude=${encodeURIComponent(longitude)}`)
export const getAccommodations = () => api('/api/accommodations/')
export const getAmenities = () => api('/api/amenities/')
export const getRecommendations = (params) => api(`/api/recommendations/?${new URLSearchParams(params)}`)
export const parseNaturalQuery = (query) => api('/api/recommendations/parse-query/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query }),
})
export const askTravelAssistant = (question, previousQuestion = '', signal) => api('/api/assistant/ask/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ question, previous_question: previousQuestion }),
  signal,
})
export const getTravelAssistantTaskStatus = (taskId, signal) => api(`/api/tasks/${taskId}/status/`, { signal })
export const getRecommendationExplanationTask = (params, destinationIds = [], destinationData = null) => {
  const query = new URLSearchParams(params)
  if (destinationIds.length) query.set('destination_ids', destinationIds.join(','))
  if (destinationData) query.set('destination_data', JSON.stringify(destinationData))
  return api(`/api/recommendations/explain/?${query}`)
}
export const getTaskStatus = (taskId) => api(`/api/tasks/${taskId}/status/`)
export const sendRecommendationFeedback = (data) => api('/api/recommendations/feedback/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})
export const getNearby = (id, radius) => api(`/api/destinations/${id}/accommodations-nearby/?radius=${radius}`)
export const getWeather = (destination, date) => api(`/api/weather/?latitude=${destination.latitude}&longitude=${destination.longitude}&date=${date}`)
export const getCurrentUser = () => api('/api/auth/me/')

export const getTours = (category) => api(`/api/tours/${category ? `?category=${encodeURIComponent(category)}` : ''}`)
export const getTourDetail = (id) => api(`/api/tours/${id}/`)
export const bookTourDeparture = (departureId, data) => api(`/api/tours/departures/${departureId}/book/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})

export const getTravelPosts = (params = {}) => api(`/api/travel-posts/?${new URLSearchParams(params)}`)
export const getTravelPost = (id) => api(`/api/travel-posts/${id}/`)
export const createTravelPost = (data) => api('/api/travel-posts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data),
})
export const deleteTravelPost = (id) => api(`/api/travel-posts/${id}/`, { method: 'DELETE' })
export const likeTravelPost = (id) => api(`/api/travel-posts/${id}/like/`, { method: 'POST' })


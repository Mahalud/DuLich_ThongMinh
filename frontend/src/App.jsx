import { AnimatePresence, motion } from 'framer-motion'
import { AirVent, Bath, MapPin, Paperclip, Send, Star, Waves, Wifi, WifiOff, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import './App.css'

const highlights = [
  'Gợi ý điểm đến theo sở thích cá nhân',
  'Dự báo thời tiết theo ngày đến dự kiến',
  'Tối ưu ngân sách và khoảng cách di chuyển',
  'Đặt phòng + thanh toán sandbox cho demo',
]

const backendUrl = 'http://localhost:8000'
const heroFallbackImage = 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1800&q=85'

const getCookie = (name) => document.cookie.split('; ').find((item) => item.startsWith(`${name}=`))?.split('=')[1] || ''

const amenityIcon = (amenity) => {
  const normalized = amenity.toLowerCase()
  if (normalized.includes('wifi')) return <Wifi size={15} />
  if (normalized.includes('điều hòa') || normalized.includes('may')) return <AirVent size={15} />
  if (normalized.includes('bồn tắm')) return <Bath size={15} />
  if (normalized.includes('biển')) return <Waves size={15} />
  return <span aria-hidden="true">•</span>
}

const emptyDestinationForm = {
  name: '',
  description: '',
  category: 'biển',
  latitude: '',
  longitude: '',
  image_url: '',
  rating: '4.5',
}

const emptyAccommodationForm = {
  name: '',
  description: '',
  category: 'hotel',
  latitude: '',
  longitude: '',
  rating: '4.5',
}

function App() {
  const routeToTab = (pathname) => ({
    '/': 'home', '/tinh-nang': 'features', '/goi-y': 'recommend', '/ho-so': 'profile',
    '/chat': 'chat', '/quan-tri': 'admin', '/dang-nhap': 'login', '/dang-ky': 'register',
    '/quen-mat-khau': 'forgot', '/dat-lai-mat-khau': 'reset', '/cam-on': 'thanks', '/payment-return': 'thanks',
  }[pathname] || 'not-found')
  const [activeTab, setActiveTab] = useState(() => routeToTab(window.location.pathname))
  const [form, setForm] = useState({
    user_preferences: 'biển,ẩm thực',
    budget_estimate: '6000000',
    latitude: '12.25',
    longitude: '109.19',
    travel_date: '2026-09-12',
    top_n: '5',
  })
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [destinations, setDestinations] = useState([])
  const [accommodations, setAccommodations] = useState([])
  const [destinationForm, setDestinationForm] = useState(emptyDestinationForm)
  const [destinationEditId, setDestinationEditId] = useState(null)
  const [accommodationForm, setAccommodationForm] = useState(emptyAccommodationForm)
  const [accommodationEditId, setAccommodationEditId] = useState(null)
  const [roomTypeForm, setRoomTypeForm] = useState({
    name: '',
    base_price: '1200000',
    stock: '2',
    amenities: 'wifi, điều hòa, bồn tắm',
  })
  const [roomTypeEditId, setRoomTypeEditId] = useState(null)
  const [selectedAccommodationId, setSelectedAccommodationId] = useState(null)
  const [roomTypesByAccommodation, setRoomTypesByAccommodation] = useState({})
  const [bookingForm, setBookingForm] = useState({
    accommodationId: '',
    roomTypeId: '',
    check_in: '2026-09-12',
    check_out: '2026-09-15',
    guest_phone: '0901234567',
  })
  const [bookingMessage, setBookingMessage] = useState('')
  const [bookingLoading, setBookingLoading] = useState(false)
  const [adminMessage, setAdminMessage] = useState('')
  const [authForm, setAuthForm] = useState({
    username: 'traveler_demo',
    email: 'traveler_demo@example.com',
    password: 'DemoPass123!',
  })
  const [currentUser, setCurrentUser] = useState(null)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatStatus, setChatStatus] = useState('')
  const [chatConnected, setChatConnected] = useState(false)
  const [chatAttachment, setChatAttachment] = useState(null)
  const [chatPreviewUrl, setChatPreviewUrl] = useState('')
  const [lightboxUrl, setLightboxUrl] = useState('')
  const chatSocketRef = useRef(null)
  const chatReconnectRef = useRef({ attempts: 0, timer: null })
  const chatBoxRef = useRef(null)
  const [heroWeather, setHeroWeather] = useState(null)
  const [chatRecipientId, setChatRecipientId] = useState(1)
  const [profileForm, setProfileForm] = useState({
    travel_preferences: 'biển,ẩm thực',
    budget_estimate: '6000000',
    free_text: 'Muốn nghỉ dưỡng, ăn ngon và trải nghiệm biển.',
  })
  const [profileMessage, setProfileMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('du lịch biển Phú Quốc')
  const [searchHistory, setSearchHistory] = useState([])
  const [reviewForm, setReviewForm] = useState({
    accommodation: '',
    rating: '5',
    comment: 'Chỗ ở rất đẹp, lịch trình ổn.',
  })
  const [reviews, setReviews] = useState([])
  const [forgotEmail, setForgotEmail] = useState('')
  const [authMessage, setAuthMessage] = useState('')
  const [resetPassword, setResetPassword] = useState('')
  const [resetPasswordConfirm, setResetPasswordConfirm] = useState('')
  const adminFetch = (endpoint, options = {}) => fetch(endpoint, {
    credentials: 'include',
    headers: { 'X-CSRFToken': getCookie('csrftoken'), ...(options.headers || {}) },
    ...options,
  })

  const pageMeta = {
    home: ['DuLich_ThongMinh | Lên kế hoạch chuyến đi thông minh', 'Gợi ý điểm đến, nơi ở và lịch trình theo sở thích, ngân sách và thời tiết.'],
    features: ['Tính năng | DuLich_ThongMinh', 'Khám phá các tính năng gợi ý lịch trình du lịch thông minh.'],
    recommend: ['Gợi ý điểm đến | DuLich_ThongMinh', 'Tìm điểm đến và nơi lưu trú phù hợp cho hành trình của bạn.'],
    profile: ['Hồ sơ du lịch | DuLich_ThongMinh', 'Quản lý tài khoản, sở thích và đánh giá du lịch của bạn.'],
    chat: ['Hỗ trợ trực tuyến | DuLich_ThongMinh', 'Nhận hỗ trợ cho hành trình và đặt phòng của bạn.'],
    admin: ['Quản trị nội dung | DuLich_ThongMinh', 'Quản lý điểm đến, nơi ở và loại phòng.'],
    login: ['Đăng nhập | DuLich_ThongMinh', 'Đăng nhập để lưu sở thích, hành trình và đánh giá xác thực.'],
    register: ['Đăng ký | DuLich_ThongMinh', 'Tạo tài khoản DuLich_ThongMinh để cá nhân hóa chuyến đi.'],
    forgot: ['Quên mật khẩu | DuLich_ThongMinh', 'Yêu cầu hướng dẫn đặt lại mật khẩu tài khoản của bạn.'],
    reset: ['Đặt lại mật khẩu | DuLich_ThongMinh', 'Tạo mật khẩu mới cho tài khoản DuLich_ThongMinh của bạn.'],
    thanks: ['Cảm ơn bạn | DuLich_ThongMinh', 'Yêu cầu của bạn đã được tiếp nhận thành công.'],
    'not-found': ['Không tìm thấy trang | DuLich_ThongMinh', 'Trang bạn tìm kiếm không tồn tại hoặc đã được di chuyển.'],
  }
  const navigate = (path) => {
    window.history.pushState({}, '', path)
    setActiveTab(routeToTab(path))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const fetchRecommendations = async (payload) => {
    const params = new URLSearchParams({
      user_preferences: payload.user_preferences,
      budget_estimate: payload.budget_estimate,
      latitude: payload.latitude,
      longitude: payload.longitude,
      travel_date: payload.travel_date,
      top_n: payload.top_n,
    })

    setLoading(true)
    setError('')

    try {
      const response = await fetch(`${backendUrl}/api/recommendations/?${params.toString()}`)
      if (!response.ok) {
        throw new Error('Không thể tải gợi ý từ backend')
      }
      const data = await response.json()
      setResults(data.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const loadBookingCatalog = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/accommodations/`)
      if (!response.ok) {
        throw new Error('Không thể tải danh sách chỗ ở cho đặt phòng')
      }

      const data = await response.json()
      setAccommodations(data)
      if (data.length > 0) {
        const firstAccommodationId = data[0].id
        const firstRoomTypeId = data[0].room_types?.[0]?.id || ''
        setBookingForm((current) => ({
          ...current,
          accommodationId: String(firstAccommodationId),
          roomTypeId: String(firstRoomTypeId),
        }))
      }
    } catch (err) {
      setBookingMessage(err.message)
    }
  }

  const refreshAdminData = async () => {
    try {
      const [destinationsResponse, accommodationsResponse] = await Promise.all([
        adminFetch(`${backendUrl}/api/admin/destinations/`),
        adminFetch(`${backendUrl}/api/admin/accommodations/`),
      ])

      if (!destinationsResponse.ok || !accommodationsResponse.ok) {
        throw new Error('Không thể tải danh sách quản trị')
      }

      const destinationData = await destinationsResponse.json()
      const accommodationData = await accommodationsResponse.json()
      setDestinations(destinationData)
      setAccommodations(accommodationData)

      const entries = await Promise.all(
        accommodationData.map(async (item) => {
          const response = await adminFetch(`${backendUrl}/api/admin/accommodations/${item.id}/room-types/`)
          if (!response.ok) {
            return [item.id, []]
          }
          return [item.id, await response.json()]
        }),
      )

      const roomMap = Object.fromEntries(entries)
      setRoomTypesByAccommodation(roomMap)
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  useEffect(() => {
    fetchRecommendations(form)
    loadBookingCatalog()
    fetch(`${backendUrl}/api/auth/csrf/`, { credentials: 'include' }).catch(() => {})
  }, [])

  useEffect(() => {
    if (!results.length) return undefined
    let cancelled = false
    let index = 0
    const loadWeather = () => {
      const destination = results[index % results.length]
      index += 1
      fetch(`${backendUrl}/api/weather/?latitude=${destination.latitude}&longitude=${destination.longitude}&date=${form.travel_date}`)
        .then((response) => response.ok ? response.json() : null)
        .then((weather) => {
          if (!cancelled && weather) setHeroWeather({ ...weather, name: destination.name, image_url: destination.image_url })
        })
        .catch(() => {})
    }
    loadWeather()
    const timer = window.setInterval(loadWeather, 6000)
    return () => { cancelled = true; window.clearInterval(timer) }
  }, [results, form.travel_date])

  useEffect(() => {
    fetch(`${backendUrl}/api/auth/me/`, { credentials: 'include' })
      .then((response) => response.ok ? response.json() : null)
      .then((data) => {
        if (!data) return
        setCurrentUser(data.user)
        setProfileForm({
          travel_preferences: (data.profile.travel_preferences || []).join(', '),
          budget_estimate: String(data.profile.budget_estimate || 0),
          free_text: data.profile.free_text || '',
        })
        fetchSearchHistory(data.user.id)
      })
      .catch(() => {})
  }, [])

  useEffect(() => {
    const handlePopState = () => setActiveTab(routeToTab(window.location.pathname))
    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    const [title, description] = pageMeta[activeTab] || pageMeta.home
    document.title = title
    document.querySelector('meta[name="description"]')?.setAttribute('content', description)
    document.querySelector('meta[property="og:title"]')?.setAttribute('content', title)
    document.querySelector('meta[property="og:description"]')?.setAttribute('content', description)
  }, [activeTab])

  useEffect(() => {
    if (activeTab === 'admin') {
      if (currentUser?.is_staff) {
        refreshAdminData()
      } else {
        setAdminMessage('Bạn không có quyền truy cập khu vực quản trị.')
      }
    }
  }, [activeTab, currentUser])

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    fetchRecommendations(form)
  }

  const handleDestinationField = (event) => {
    const { name, value } = event.target
    setDestinationForm((current) => ({ ...current, [name]: value }))
  }

  const handleAccommodationField = (event) => {
    const { name, value } = event.target
    setAccommodationForm((current) => ({ ...current, [name]: value }))
  }

  const handleRoomTypeField = (event) => {
    const { name, value } = event.target
    setRoomTypeForm((current) => ({ ...current, [name]: value }))
  }

  const handleBookingField = (event) => {
    const { name, value } = event.target
    setBookingForm((current) => ({ ...current, [name]: value }))
  }

  const submitDestination = async (event) => {
    event.preventDefault()
    setAdminMessage('')

    const payload = {
      ...destinationForm,
      latitude: Number(destinationForm.latitude || 0),
      longitude: Number(destinationForm.longitude || 0),
      rating: Number(destinationForm.rating || 0),
    }

    const endpoint = destinationEditId
      ? `${backendUrl}/api/admin/destinations/${destinationEditId}/`
      : `${backendUrl}/api/admin/destinations/`
    const method = destinationEditId ? 'PATCH' : 'POST'

    try {
      const response = await adminFetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Không thể lưu điểm đến')
      }

      setDestinationForm(emptyDestinationForm)
      setDestinationEditId(null)
      setAdminMessage(destinationEditId ? 'Cập nhật điểm đến thành công.' : 'Thêm điểm đến thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const submitAccommodation = async (event) => {
    event.preventDefault()
    setAdminMessage('')

    const payload = {
      ...accommodationForm,
      latitude: Number(accommodationForm.latitude || 0),
      longitude: Number(accommodationForm.longitude || 0),
      rating: Number(accommodationForm.rating || 0),
    }

    const endpoint = accommodationEditId
      ? `${backendUrl}/api/admin/accommodations/${accommodationEditId}/`
      : `${backendUrl}/api/admin/accommodations/`
    const method = accommodationEditId ? 'PATCH' : 'POST'

    try {
      const response = await adminFetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Không thể lưu chỗ ở')
      }

      setAccommodationForm(emptyAccommodationForm)
      setAccommodationEditId(null)
      setAdminMessage(accommodationEditId ? 'Cập nhật chỗ ở thành công.' : 'Thêm chỗ ở thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const startEditDestination = (item) => {
    setDestinationEditId(item.id)
    setDestinationForm({
      name: item.name,
      description: item.description,
      category: item.category,
      latitude: String(item.latitude),
      longitude: String(item.longitude),
      image_url: item.image_url || '',
      rating: String(item.rating || 4.5),
    })
    setActiveTab('admin')
  }

  const startEditAccommodation = (item) => {
    setAccommodationEditId(item.id)
    setAccommodationForm({
      name: item.name,
      description: item.description,
      category: item.category,
      latitude: String(item.latitude),
      longitude: String(item.longitude),
      rating: String(item.rating || 4.5),
    })
    setActiveTab('admin')
  }

  const deleteDestination = async (id) => {
    try {
      const response = await adminFetch(`${backendUrl}/api/admin/destinations/${id}/`, { method: 'DELETE' })
      if (!response.ok) {
        throw new Error('Xóa điểm đến thất bại')
      }
      setAdminMessage('Xóa điểm đến thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const deleteAccommodation = async (id) => {
    try {
      const response = await adminFetch(`${backendUrl}/api/admin/accommodations/${id}/`, { method: 'DELETE' })
      if (!response.ok) {
        throw new Error('Xóa chỗ ở thất bại')
      }
      setAdminMessage('Xóa chỗ ở thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const submitRoomType = async (event) => {
    event.preventDefault()
    if (!selectedAccommodationId) {
      setAdminMessage('Vui lòng chọn chỗ ở trước khi thêm loại phòng.')
      return
    }

    const payload = {
      name: roomTypeForm.name,
      base_price: Number(roomTypeForm.base_price || 0),
      stock: Number(roomTypeForm.stock || 0),
      amenities: roomTypeForm.amenities.split(',').map((item) => item.trim()).filter(Boolean),
    }

    const endpoint = roomTypeEditId
      ? `${backendUrl}/api/admin/room-types/${roomTypeEditId}/`
      : `${backendUrl}/api/admin/accommodations/${selectedAccommodationId}/room-types/`
    const method = roomTypeEditId ? 'PATCH' : 'POST'

    try {
      const response = await adminFetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Không thể lưu loại phòng')
      }

      setRoomTypeForm({
        name: '',
        base_price: '1200000',
        stock: '2',
        amenities: 'wifi, điều hòa, bồn tắm',
      })
      setRoomTypeEditId(null)
      setAdminMessage(roomTypeEditId ? 'Cập nhật loại phòng thành công.' : 'Thêm loại phòng thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const deleteRoomType = async (roomTypeId) => {
    try {
      const response = await adminFetch(`${backendUrl}/api/admin/room-types/${roomTypeId}/`, { method: 'DELETE' })
      if (!response.ok) {
        throw new Error('Xóa loại phòng thất bại')
      }
      setAdminMessage('Xóa loại phòng thành công.')
      refreshAdminData()
    } catch (err) {
      setAdminMessage(err.message)
    }
  }

  const startEditRoomType = (item, accommodationId) => {
    setSelectedAccommodationId(accommodationId)
    setRoomTypeEditId(item.id)
    setRoomTypeForm({
      name: item.name,
      base_price: String(item.base_price),
      stock: String(item.stock),
      amenities: (item.amenities || []).join(', '),
    })
  }

  const selectedBookingAccommodation = accommodations.find((item) => String(item.id) === String(bookingForm.accommodationId)) || null
  const availableBookingRooms = selectedBookingAccommodation?.room_types || []

  const handleBookingSubmit = async (event) => {
    event.preventDefault()
    setBookingMessage('')
    setBookingLoading(true)

    try {
      if (!bookingForm.accommodationId || !bookingForm.roomTypeId) {
        throw new Error('Vui lòng chọn chỗ ở và loại phòng trước khi đặt.')
      }

      if (!bookingForm.check_in || !bookingForm.check_out || !bookingForm.guest_phone) {
        throw new Error('Vui lòng điền đầy đủ ngày nhận/trả và số điện thoại.')
      }

      const room = availableBookingRooms.find((item) => String(item.id) === String(bookingForm.roomTypeId))
      if (!room) {
        throw new Error('Loại phòng không hợp lệ.')
      }

      const username = `demo_${Date.now()}`
      const registerResponse = await fetch(`${backendUrl}/api/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username,
          email: `${username}@demo.local`,
          password: 'DemoPass123!',
        }),
      })

      if (!registerResponse.ok) {
        const errorBody = await registerResponse.json().catch(() => ({}))
        throw new Error(errorBody?.error || 'Không thể tạo tài khoản demo cho đặt phòng.')
      }

      const userData = await registerResponse.json()
      const bookingResponse = await fetch(`${backendUrl}/api/bookings/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user: userData.id,
          room_type: Number(bookingForm.roomTypeId),
          check_in: bookingForm.check_in,
          check_out: bookingForm.check_out,
          guest_phone: bookingForm.guest_phone,
        }),
      })

      if (!bookingResponse.ok) {
        const errorBody = await bookingResponse.json().catch(() => ({}))
        throw new Error(errorBody?.non_field_errors?.[0] || errorBody?.error || 'Đặt phòng thất bại.')
      }

      const bookingData = await bookingResponse.json()
      const paymentResponse = await fetch(`${backendUrl}/api/payments/init/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          booking_id: bookingData.id,
          amount: Number(room.base_price),
          return_url: 'http://localhost:5173/payment-return',
        }),
      })

      if (!paymentResponse.ok) {
        throw new Error('Khởi tạo thanh toán sandbox thất bại.')
      }

      const paymentData = await paymentResponse.json()
      setBookingMessage('Thanh toán sandbox đang được chuyển hướng…')
      window.location.href = paymentData.redirect_url
    } catch (err) {
      setBookingMessage(err.message)
    } finally {
      setBookingLoading(false)
    }
  }

  const handleOpenRoute = async (destination) => {
    try {
      const response = await fetch(`${backendUrl}/api/routes/?start_lat=${form.latitude}&start_lng=${form.longitude}&end_lat=${destination.latitude}&end_lng=${destination.longitude}`)
      if (!response.ok) {
        throw new Error('Không thể lấy thông tin chỉ đường.')
      }

      const data = await response.json()
      window.open(data.google_maps_url, '_blank', 'noopener,noreferrer')
    } catch (err) {
      setError(err.message)
    }
  }

  const fetchUserProfile = async (userId) => {
    try {
      const response = await fetch(`${backendUrl}/api/profile/${userId}/`, { credentials: 'include' })
      if (!response.ok) {
        throw new Error('Không thể tải hồ sơ người dùng')
      }
      const data = await response.json()
      setProfileForm({
        travel_preferences: (data.travel_preferences || []).join(', '),
        budget_estimate: String(data.budget_estimate || 6000000),
        free_text: data.free_text || '',
      })
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const fetchSearchHistory = async (userId) => {
    if (!userId) return
    try {
      const response = await fetch(`${backendUrl}/api/search-history/?user_id=${userId}`)
      if (!response.ok) {
        throw new Error('Không thể tải lịch sử tìm kiếm')
      }
      const data = await response.json()
      setSearchHistory(data)
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const handleAuthField = (event) => {
    const { name, value } = event.target
    setAuthForm((current) => ({ ...current, [name]: value }))
  }

  const handleProfileField = (event) => {
    const { name, value } = event.target
    setProfileForm((current) => ({ ...current, [name]: value }))
  }

  const loginDemoUser = async (event) => {
    if (event) event.preventDefault()
    try {
      const response = await fetch(`${backendUrl}/api/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          username: authForm.username,
          password: authForm.password,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.error || 'Đăng nhập demo thất bại.')
      }

      const data = await response.json()
      setCurrentUser(data.user)
      setProfileForm({
        travel_preferences: (data.profile.travel_preferences || []).join(', '),
        budget_estimate: String(data.profile.budget_estimate || 6000000),
        free_text: data.profile.free_text || '',
      })
      setProfileMessage('Đăng nhập thành công.')
      fetchSearchHistory(data.user.id)
      setAuthMessage('Đăng nhập thành công.')
      navigate(data.user.is_staff ? '/quan-tri' : '/ho-so')
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const registerDemoUser = async (event) => {
    if (event) event.preventDefault()
    try {
      const response = await fetch(`${backendUrl}/api/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          username: authForm.username,
          email: authForm.email,
          password: authForm.password,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.error || 'Tạo tài khoản demo thất bại.')
      }

      const data = await response.json()
      setCurrentUser(data)
      setProfileMessage('Tạo tài khoản demo thành công.')
      setAuthMessage('Tạo tài khoản thành công. Hãy hoàn thiện hồ sơ của bạn.')
      fetchUserProfile(data.id)
      fetchSearchHistory(data.id)
      navigate('/ho-so')
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const saveProfile = async (event) => {
    event.preventDefault()
    if (!currentUser) {
      setProfileMessage('Vui lòng đăng nhập hoặc tạo tài khoản demo trước.')
      return
    }

    try {
      const response = await fetch(`${backendUrl}/api/profile/${currentUser.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          travel_preferences: profileForm.travel_preferences.split(',').map((item) => item.trim()).filter(Boolean),
          budget_estimate: Number(profileForm.budget_estimate || 0),
          free_text: profileForm.free_text,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Cập nhật hồ sơ thất bại.')
      }

      const data = await response.json()
      setProfileMessage('Cập nhật hồ sơ người dùng thành công.')
      setProfileForm({
        travel_preferences: (data.travel_preferences || []).join(', '),
        budget_estimate: String(data.budget_estimate || 6000000),
        free_text: data.free_text || '',
      })
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  useEffect(() => {
    if (!currentUser || activeTab !== 'chat') return undefined

    const roomName = `support-${Math.min(currentUser.id, chatRecipientId)}-${Math.max(currentUser.id, chatRecipientId)}`
    let disposed = false
    const connect = () => {
      if (disposed) return
      setChatStatus('Đang kết nối chat realtime...')
      const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`)
      chatSocketRef.current = socket
      socket.onopen = () => {
        chatReconnectRef.current.attempts = 0
        setChatConnected(true)
        setChatStatus('Đã kết nối chat realtime.')
        fetch(`${backendUrl}/api/chat/messages/?user_id=${currentUser.id}&receiver_id=${chatRecipientId}`)
          .then((response) => response.ok ? response.json() : [])
          .then((messages) => setChatMessages(messages))
          .catch(() => setChatMessages([]))
      }
      socket.onmessage = (event) => {
        const message = JSON.parse(event.data)
        setChatMessages((current) => current.some((item) => item.id === message.id) ? current : [...current, message])
      }
      socket.onclose = () => {
        setChatConnected(false)
        if (!disposed && chatReconnectRef.current.attempts < 5) {
          chatReconnectRef.current.attempts += 1
          setChatStatus(`Mất kết nối, thử lại sau 3 giây (${chatReconnectRef.current.attempts}/5).`)
          chatReconnectRef.current.timer = window.setTimeout(connect, 3000)
        } else if (!disposed) setChatStatus('Chat đã mất kết nối.')
      }
      socket.onerror = () => setChatStatus('Không thể kết nối chat realtime.')
    }
    connect()
    return () => {
      disposed = true
      if (chatReconnectRef.current.timer) window.clearTimeout(chatReconnectRef.current.timer)
      chatSocketRef.current?.close()
      chatSocketRef.current = null
      setChatConnected(false)
    }
  }, [activeTab, currentUser, chatRecipientId])

  useEffect(() => {
    if (chatBoxRef.current) chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight
  }, [chatMessages])

  const handleChatSubmit = async (event) => {
    event.preventDefault()
    if (!currentUser || (!chatInput.trim() && !chatAttachment) || chatSocketRef.current?.readyState !== WebSocket.OPEN) return

    try {
      let attachment = { attachment_url: '', attachment_type: 'none' }
      if (chatAttachment) {
        const formData = new FormData()
        formData.append('file', chatAttachment)
        const uploadResponse = await fetch(`${backendUrl}/api/chat/upload/`, { method: 'POST', body: formData })
        const uploadData = await uploadResponse.json()
        if (!uploadResponse.ok) throw new Error(uploadData.error || 'Tải tệp lên thất bại.')
        attachment = uploadData
      }
      chatSocketRef.current.send(JSON.stringify({
        message: chatInput.trim(),
        sender_id: currentUser.id,
        receiver_id: chatRecipientId,
        ...attachment,
      }))
      setChatInput('')
      setChatAttachment(null)
      setChatPreviewUrl('')
    } catch (err) { setChatStatus(err.message) }
  }

  const handleChatAttachment = (event) => {
    const file = event.target.files?.[0]
    if (!file) return
    setChatAttachment(file)
    setChatPreviewUrl(URL.createObjectURL(file))
    event.target.value = ''
  }

  const saveSearchHistory = async (event) => {
    event.preventDefault()
    if (!currentUser) {
      setProfileMessage('Vui lòng đăng nhập trước khi lưu lịch sử tìm kiếm.')
      return
    }

    try {
      const response = await fetch(`${backendUrl}/api/search-history/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: currentUser.id,
          query: searchQuery,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Lưu lịch sử tìm kiếm thất bại.')
      }

      const data = await response.json()
      setSearchHistory((current) => [data, ...current])
      setSearchQuery('')
      setProfileMessage('Lưu lịch sử tìm kiếm thành công.')
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const loadReviews = async () => {
    try {
      const response = await fetch(`${backendUrl}/api/reviews/`)
      if (!response.ok) {
        throw new Error('Không thể tải đánh giá chỗ ở')
      }
      const data = await response.json()
      setReviews(data)
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  const submitReview = async (event) => {
    event.preventDefault()
    if (!currentUser) {
      setProfileMessage('Vui lòng đăng nhập trước khi viết đánh giá.')
      return
    }

    try {
      const response = await fetch(`${backendUrl}/api/reviews/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          accommodation: Number(reviewForm.accommodation || accommodations[0]?.id),
          user: currentUser.id,
          rating: Number(reviewForm.rating),
          comment: reviewForm.comment,
        }),
      })

      if (!response.ok) {
        const errorBody = await response.json().catch(() => ({}))
        throw new Error(errorBody?.detail || 'Gửi đánh giá thất bại.')
      }

      const data = await response.json()
      setReviews((current) => [data, ...current])
      setReviewForm((current) => ({ ...current, comment: '', rating: '5' }))
      setProfileMessage('Cảm ơn bạn đã đánh giá chỗ ở.')
    } catch (err) {
      setProfileMessage(err.message)
    }
  }

  useEffect(() => {
    loadReviews()
  }, [])

  useEffect(() => {
    const measurementId = import.meta.env.VITE_GA_MEASUREMENT_ID
    if (!measurementId || document.querySelector(`script[data-ga-id="${measurementId}"]`)) return
    const script = document.createElement('script')
    script.async = true
    script.src = `https://www.googletagmanager.com/gtag/js?id=${measurementId}`
    script.dataset.gaId = measurementId
    document.head.appendChild(script)
    window.dataLayer = window.dataLayer || []
    window.gtag = function gtag() { window.dataLayer.push(arguments) }
    window.gtag('js', new Date())
    window.gtag('config', measurementId, { anonymize_ip: true })
  }, [])

  const submitForgotPassword = (event) => {
    event.preventDefault()
    fetch(`${backendUrl}/api/auth/password-reset/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ email: forgotEmail }),
    })
      .then((response) => response.json())
      .then((data) => setAuthMessage(data.message || 'Nếu email tồn tại, hướng dẫn đặt lại mật khẩu sẽ được gửi.'))
      .catch(() => setAuthMessage('Không thể gửi yêu cầu lúc này. Vui lòng thử lại.'))
  }

  const submitResetPassword = async (event) => {
    event.preventDefault()
    if (resetPassword !== resetPasswordConfirm) {
      setAuthMessage('Mật khẩu xác nhận chưa khớp.')
      return
    }
    const params = new URLSearchParams(window.location.search)
    try {
      const response = await fetch(`${backendUrl}/api/auth/password-reset/confirm/`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
        body: JSON.stringify({ uid: params.get('uid'), token: params.get('token'), password: resetPassword }),
      })
      const data = await response.json()
      if (!response.ok) throw new Error(data.error || 'Không thể đặt lại mật khẩu.')
      setAuthMessage('Đặt lại mật khẩu thành công. Bạn có thể đăng nhập ngay.')
      navigate('/dang-nhap')
    } catch (err) {
      setAuthMessage(err.message)
    }
  }

  const handleLogout = async () => {
    await fetch(`${backendUrl}/api/auth/logout/`, { method: 'POST', credentials: 'include' }).catch(() => {})
    setCurrentUser(null)
    setChatMessages([])
    setSearchHistory([])
    setAuthMessage('Bạn đã đăng xuất.')
    navigate('/dang-nhap')
  }

  return (
    <div className="travel-app">
      <header className="topbar">
        <button type="button" className="brand brand-button" onClick={() => navigate('/')}>DuLich_ThongMinh</button>
        <nav>
          <button type="button" className={activeTab === 'home' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/')}>
            Giới thiệu
          </button>
          <button type="button" className={activeTab === 'features' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/tinh-nang')}>
            Tính năng
          </button>
          <button type="button" className={activeTab === 'recommend' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/goi-y')}>
            Gợi ý
          </button>
          <button type="button" className={activeTab === 'profile' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/ho-so')}>
            Hồ sơ
          </button>
          <button type="button" className={activeTab === 'chat' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/chat')}>
            Chat realtime
          </button>
          {currentUser?.is_staff && (
            <button type="button" className={activeTab === 'admin' ? 'nav-button active' : 'nav-button'} onClick={() => navigate('/quan-tri')}>
              Quản trị
            </button>
          )}
        </nav>
        <button type="button" className="primary-btn" onClick={() => navigate(currentUser ? '/ho-so' : '/dang-nhap')}>{currentUser ? 'Hồ sơ' : 'Đăng nhập'}</button>
        {currentUser && <button type="button" className="secondary-btn" onClick={handleLogout}>Đăng xuất</button>}
      </header>

      <main>
        {activeTab === 'login' && (
          <section className="auth-page" aria-labelledby="login-title">
            <div className="auth-card">
              <span className="eyebrow dark">Chào mừng trở lại</span>
              <h1 id="login-title">Đăng nhập</h1>
              <p>Đăng nhập để quản lý hành trình, hồ sơ và những đánh giá đã xác thực.</p>
              <form className="admin-form" onSubmit={loginDemoUser}>
                <label>Tên đăng nhập<input name="username" autoComplete="username" required value={authForm.username} onChange={handleAuthField} /></label>
                <label>Mật khẩu<input name="password" type="password" autoComplete="current-password" required value={authForm.password} onChange={handleAuthField} /></label>
                <button type="submit" className="primary-btn">Đăng nhập</button>
              </form>
              <div className="auth-links"><button type="button" onClick={() => navigate('/quen-mat-khau')}>Quên mật khẩu?</button><button type="button" onClick={() => navigate('/dang-ky')}>Chưa có tài khoản? Đăng ký</button></div>
              {authMessage && <p className="admin-message">{authMessage}</p>}
            </div>
          </section>
        )}

        {activeTab === 'register' && (
          <section className="auth-page" aria-labelledby="register-title">
            <div className="auth-card">
              <span className="eyebrow dark">Bắt đầu hành trình</span>
              <h1 id="register-title">Tạo tài khoản</h1>
              <p>Lưu sở thích và nhận gợi ý du lịch phù hợp hơn sau mỗi chuyến đi.</p>
              <form className="admin-form" onSubmit={registerDemoUser}>
                <label>Tên đăng nhập<input name="username" autoComplete="username" required value={authForm.username} onChange={handleAuthField} /></label>
                <label>Email<input name="email" type="email" autoComplete="email" required value={authForm.email} onChange={handleAuthField} /></label>
                <label>Mật khẩu<input name="password" type="password" autoComplete="new-password" minLength="8" required value={authForm.password} onChange={handleAuthField} /></label>
                <button type="submit" className="primary-btn">Tạo tài khoản</button>
              </form>
              <div className="auth-links"><button type="button" onClick={() => navigate('/dang-nhap')}>Đã có tài khoản? Đăng nhập</button></div>
              {authMessage && <p className="admin-message">{authMessage}</p>}
            </div>
          </section>
        )}

        {activeTab === 'forgot' && (
          <section className="auth-page" aria-labelledby="forgot-title">
            <div className="auth-card">
              <span className="eyebrow dark">Khôi phục tài khoản</span>
              <h1 id="forgot-title">Quên mật khẩu?</h1>
              <p>Nhập email đăng ký. Vì lý do bảo mật, thông báo luôn giống nhau dù email có tồn tại hay không.</p>
              <form className="admin-form" onSubmit={submitForgotPassword}>
                <label>Email<input type="email" autoComplete="email" required value={forgotEmail} onChange={(event) => setForgotEmail(event.target.value)} /></label>
                <button type="submit" className="primary-btn">Gửi hướng dẫn</button>
              </form>
              <div className="auth-links"><button type="button" onClick={() => navigate('/dang-nhap')}>Quay lại đăng nhập</button></div>
              {authMessage && <p className="admin-message">{authMessage}</p>}
            </div>
          </section>
        )}

        {activeTab === 'reset' && (
          <section className="auth-page" aria-labelledby="reset-title">
            <div className="auth-card">
              <span className="eyebrow dark">Bảo mật tài khoản</span>
              <h1 id="reset-title">Đặt lại mật khẩu</h1>
              <form className="admin-form" onSubmit={submitResetPassword}>
                <label>Mật khẩu mới<input type="password" autoComplete="new-password" minLength="8" required value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} /></label>
                <label>Xác nhận mật khẩu<input type="password" autoComplete="new-password" minLength="8" required value={resetPasswordConfirm} onChange={(event) => setResetPasswordConfirm(event.target.value)} /></label>
                <button type="submit" className="primary-btn">Lưu mật khẩu mới</button>
              </form>
              {authMessage && <p className="admin-message">{authMessage}</p>}
            </div>
          </section>
        )}

        {activeTab === 'thanks' && (
          <section className="auth-page" aria-labelledby="thanks-title"><div className="auth-card thanks-card"><span className="eyebrow dark">Đã tiếp nhận</span><h1 id="thanks-title">Cảm ơn bạn!</h1><p>Yêu cầu của bạn đã được ghi nhận. Chúc bạn có một hành trình thật đáng nhớ.</p><button type="button" className="primary-btn" onClick={() => navigate('/')}>Về trang chủ</button></div></section>
        )}

        {activeTab === 'not-found' && (
          <section className="auth-page" aria-labelledby="not-found-title"><div className="auth-card thanks-card"><span className="eyebrow dark">Lỗi 404</span><h1 id="not-found-title">Không tìm thấy trang</h1><p>Đường dẫn này không tồn tại hoặc đã được thay đổi. Bạn có thể quay về trang chủ để tiếp tục khám phá.</p><button type="button" className="primary-btn" onClick={() => navigate('/')}>Về trang chủ</button></div></section>
        )}

        {activeTab === 'home' && (
          <>
            <motion.section className="hero" style={{ '--hero-image': `url(${heroWeather?.image_url || heroFallbackImage})` }} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="hero-copy">
                <span className="eyebrow"><MapPin size={14} /> Website gợi ý du lịch thông minh</span>
                <h1>Khám phá hành trình phù hợp với bạn hơn.</h1>
                <p>
                  Hệ thống dựa trên sở thích du lịch, ngân sách, thời tiết và khoảng cách để đề xuất
                  điểm đến, nơi nghỉ, và lịch trình tối ưu nhất cho mỗi chuyến đi.
                </p>
                <div className="hero-actions">
                  <button className="primary-btn" onClick={() => navigate('/goi-y')}>Bắt đầu ngay</button>
                  <button className="secondary-btn" onClick={() => setActiveTab('admin')}>Xem demo</button>
                </div>
                <ul className="highlight-list">
                  {highlights.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>

              <div className="hero-panel">
                <div className="mini-card card-main">
                  <span className="tag">Dữ liệu trực tiếp</span>
                  <AnimatePresence mode="wait">
                    <motion.div key={heroWeather?.name || 'weather'} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }}>
                      <h3>{heroWeather?.name || 'Đang chọn điểm đến'}</h3>
                      <p>Hôm nay {heroWeather?.name || 'điểm đến'} đang <Wifi size={16} /> {heroWeather?.temperature ?? '--'}°C — phù hợp để đi!</p>
                      <div className="meta-row"><span>Khả năng mưa: {heroWeather?.precipitation_probability ?? '--'}%</span><span>Điểm thời tiết: {heroWeather?.weather_score ?? '--'}</span></div>
                    </motion.div>
                  </AnimatePresence>
                </div>
                <div className="mini-card card-small">
                  <span>Ngân sách ước tính</span>
                  <strong>6.5 triệu</strong>
                </div>
              </div>
            </motion.section>

            <motion.section id="features" className="features" initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, amount: 0.15 }}>
              <div className="section-head">
                <span className="eyebrow dark">Tính năng cốt lõi</span>
                <h2>Hệ thống giúp tối ưu quyết định du lịch</h2>
              </div>
              <div className="feature-grid">
                <article>
                  <h3>1. Sở thích cá nhân</h3>
                  <p>Người dùng chọn nhãn ưu tiên như biển, núi, thành phố và ẩm thực.</p>
                </article>
                <article>
                  <h3>2. Dự báo thời tiết</h3>
                  <p>Tích hợp Open-Meteo theo ngày dự kiến đến nơi để đánh giá điều kiện thời tiết.</p>
                </article>
                <article>
                  <h3>3. Tối ưu ngân sách</h3>
                  <p>So sánh chi phí lưu trú với ngân sách dự kiến để lọc nơi ở phù hợp.</p>
                </article>
                <article>
                  <h3>4. Gợi ý thông minh</h3>
                  <p>Weighted Sum Model kết hợp preference, weather, cost và distance.</p>
                </article>
              </div>
            </motion.section>
          </>
        )}

        {activeTab === 'recommend' && (
          <section id="recommend" className="recommend">
            <div className="section-head">
              <span className="eyebrow dark">Gợi ý cho bạn</span>
              <h2>Những điểm đến đáng cân nhắc</h2>
            </div>

            <form className="recommend-form" onSubmit={handleSubmit}>
              <label>
                Sở thích
                <input name="user_preferences" value={form.user_preferences} onChange={handleChange} />
              </label>
              <label>
                Ngân sách
                <input name="budget_estimate" type="number" value={form.budget_estimate} onChange={handleChange} />
              </label>
              <label>
                Vĩ độ
                <input name="latitude" type="number" step="0.01" value={form.latitude} onChange={handleChange} />
              </label>
              <label>
                Kinh độ
                <input name="longitude" type="number" step="0.01" value={form.longitude} onChange={handleChange} />
              </label>
              <label>
                Ngày đến
                <input name="travel_date" type="date" value={form.travel_date} onChange={handleChange} />
              </label>
              <label>
                Số gợi ý
                <input name="top_n" type="number" min="1" max="10" value={form.top_n} onChange={handleChange} />
              </label>
              <button type="submit" className="primary-btn">Tạo gợi ý</button>
            </form>

            {error && <p className="form-error">{error}</p>}

            <div className="destination-grid">
              {loading && [1, 2, 3].map((item) => <div className="destination-card skeleton-card" key={item} aria-label="Đang tải điểm đến" />)}
              {!loading && results.length === 0 && !error && <p className="loading-state">Chưa có dữ liệu điểm đến.</p>}
              {results.map((item, index) => (
                <article className="destination-card" key={item.id || `${item.name}-${index}`}>
                  <div className="destination-image" style={{ backgroundImage: `url(${item.image_url || heroFallbackImage})` }} />
                  <span className="destination-tag">{item.category}</span>
                  <div className="card-title-row"><h3>{item.name}</h3><strong className="score-badge">{item.score}</strong></div>
                  <p>{item.description}</p>
                  <div className="destination-meta">
                    <span>Điểm số: {item.score}</span>
                    <span>Khoảng cách: {item.distance_km} km</span>
                  </div>
                  <div className="destination-meta">
                    <span><Star size={14} fill="currentColor" /> {item.rating}</span>
                    <span>Chi phí: {Number(item.estimated_cost).toLocaleString()} đ</span>
                  </div>
                  <div className="card-actions">
                    <button type="button" className="primary-btn" onClick={() => handleOpenRoute(item)}>Chỉ đường</button>
                    <button type="button" className="secondary-btn" onClick={() => {
                      setBookingForm((current) => ({
                        ...current,
                        accommodationId: accommodations[0]?.id ? String(accommodations[0].id) : '',
                        roomTypeId: accommodations[0]?.room_types?.[0]?.id ? String(accommodations[0].room_types[0].id) : '',
                      }))
                      setActiveTab('recommend')
                    }}>Đặt phòng</button>
                  </div>
                </article>
              ))}
            </div>

            <div className="booking-panel">
              <div className="section-head">
                <span className="eyebrow dark">Đặt phòng demo</span>
                <h3>Chọn phòng để thanh toán sandbox</h3>
              </div>

              {bookingMessage && <div className="booking-message">{bookingMessage}</div>}

              <form className="booking-form" onSubmit={handleBookingSubmit}>
                <label>
                  Chỗ ở
                  <select name="accommodationId" value={bookingForm.accommodationId} onChange={(event) => {
                    const selectedId = event.target.value
                    const selectedAccommodation = accommodations.find((item) => String(item.id) === String(selectedId))
                    setBookingForm((current) => ({
                      ...current,
                      accommodationId: selectedId,
                      roomTypeId: selectedAccommodation?.room_types?.[0]?.id ? String(selectedAccommodation.room_types[0].id) : '',
                    }))
                  }}>
                    <option value="">-- Chọn chỗ ở --</option>
                    {accommodations.map((item) => (
                      <option key={item.id} value={item.id}>{item.name}</option>
                    ))}
                  </select>
                </label>

                <label>
                  Loại phòng
                  <select name="roomTypeId" value={bookingForm.roomTypeId} onChange={handleBookingField}>
                    <option value="">-- Chọn loại phòng --</option>
                    {availableBookingRooms.map((item) => (
                      <option key={item.id} value={item.id}>{item.name} · {Number(item.base_price).toLocaleString()} đ</option>
                    ))}
                  </select>
                </label>

                <label>
                  Ngày nhận
                  <input name="check_in" type="date" value={bookingForm.check_in} onChange={handleBookingField} />
                </label>

                <label>
                  Ngày trả
                  <input name="check_out" type="date" value={bookingForm.check_out} onChange={handleBookingField} />
                </label>

                <label>
                  Số điện thoại
                  <input name="guest_phone" value={bookingForm.guest_phone} onChange={handleBookingField} />
                </label>

                <button type="submit" className="primary-btn" disabled={bookingLoading}>
                  {bookingLoading ? 'Đang xử lý...' : 'Đặt phòng & thanh toán'}
                </button>
              </form>
            </div>
          </section>
        )}

        {activeTab === 'profile' && (
          <section className="profile-panel">
            <div className="section-head">
              <span className="eyebrow dark">Tài khoản & hồ sơ</span>
              <h2>Quản lý thông tin cá nhân</h2>
            </div>

            <div className="profile-grid">
              <form className="admin-form" onSubmit={loginDemoUser}>
                <h3>Đăng nhập / tạo tài khoản demo</h3>
                <label>
                  Tên đăng nhập
                  <input name="username" value={authForm.username} onChange={handleAuthField} />
                </label>
                <label>
                  Email
                  <input name="email" type="email" value={authForm.email} onChange={handleAuthField} />
                </label>
                <label>
                  Mật khẩu
                  <input name="password" type="password" value={authForm.password} onChange={handleAuthField} />
                </label>
                <div className="form-actions">
                  <button type="submit" className="primary-btn">Đăng nhập</button>
                  <button type="button" className="secondary-btn" onClick={registerDemoUser}>Tạo tài khoản</button>
                </div>
              </form>

              <form className="admin-form" onSubmit={saveProfile}>
                <h3>Thông tin sở thích du lịch</h3>
                <label>
                  Sở thích
                  <input name="travel_preferences" value={profileForm.travel_preferences} onChange={handleProfileField} />
                </label>
                <label>
                  Ngân sách dự kiến
                  <input name="budget_estimate" type="number" value={profileForm.budget_estimate} onChange={handleProfileField} />
                </label>
                <label>
                  Mô tả tự do
                  <textarea name="free_text" rows="4" value={profileForm.free_text} onChange={handleProfileField} />
                </label>
                <div className="form-actions">
                  <button type="submit" className="primary-btn">Lưu hồ sơ</button>
                </div>
              </form>
            </div>

            <form className="admin-form search-form" onSubmit={saveSearchHistory}>
              <h3>Lịch sử tìm kiếm</h3>
              <div className="inline-group">
                <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Nhập từ khóa tìm kiếm..." />
                <button type="submit" className="primary-btn">Lưu tìm kiếm</button>
              </div>
            </form>

            {profileMessage && <div className="admin-message">{profileMessage}</div>}

            <div className="admin-list">
              <h3>Gần đây</h3>
              {searchHistory.length === 0 ? <p>Chưa có lịch sử tìm kiếm.</p> : searchHistory.map((item) => (
                <div className="list-item" key={item.id || `${item.query}-${item.created_at}`}>
                  <div>
                    <strong>{item.query}</strong>
                    <p>{item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'Mới nhất'}</p>
                  </div>
                </div>
              ))}
            </div>

            <form className="admin-form review-form" onSubmit={submitReview}>
              <h3>Đánh giá chỗ ở</h3>
              <label>
                Chỗ ở
                <select name="accommodation" value={reviewForm.accommodation} onChange={(event) => setReviewForm((current) => ({ ...current, accommodation: event.target.value }))}>
                  <option value="">-- Chọn chỗ ở --</option>
                  {accommodations.map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Số sao
                <select name="rating" value={reviewForm.rating} onChange={(event) => setReviewForm((current) => ({ ...current, rating: event.target.value }))}>
                  <option value="5">5 sao</option>
                  <option value="4">4 sao</option>
                  <option value="3">3 sao</option>
                  <option value="2">2 sao</option>
                  <option value="1">1 sao</option>
                </select>
              </label>
              <label>
                Nhận xét
                <textarea name="comment" rows="3" value={reviewForm.comment} onChange={(event) => setReviewForm((current) => ({ ...current, comment: event.target.value }))} />
              </label>
              <button type="submit" className="primary-btn">Gửi đánh giá</button>
            </form>

            <div className="admin-list">
              <h3>Đánh giá gần đây</h3>
              {reviews.length === 0 ? <p>Chưa có đánh giá nào.</p> : reviews.map((item) => (
                <div className="list-item" key={item.id || `${item.user}-${item.created_at}`}>
                  <div>
                    <strong>{item.user_name || 'Khách đã xác thực'} · {item.rating} sao ✓</strong>
                    <p>{item.comment}</p>
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {activeTab === 'chat' && (
          <section className="profile-panel">
            <div className="section-head">
              <span className="eyebrow dark">Chat realtime</span>
              <h2>Hỗ trợ khách hàng trực tiếp</h2>
            </div>

            <div className="admin-form">
              <label>
                Người nhận
                <select value={chatRecipientId} onChange={(event) => setChatRecipientId(Number(event.target.value))}>
                  <option value={1}>Quản trị viên</option>
                  <option value={2}>Hỗ trợ booking</option>
                </select>
              </label>
              {!currentUser && <p>Vui lòng đăng nhập để bắt đầu chat realtime.</p>}
              {currentUser && (
                <>
                  <div className="chat-box" ref={chatBoxRef}>
                    {chatMessages.length === 0 ? (
                      <p className="loading-state">Chưa có tin nhắn nào.</p>
                    ) : (
                      chatMessages.map((item) => (
                        <div key={item.id || `${item.sender}-${item.created_at}`} className={Number(item.sender) === Number(currentUser.id) ? 'chat-message mine' : 'chat-message'}>
                          <strong>{Number(item.sender) === Number(currentUser.id) ? 'Bạn' : 'Admin'}</strong>
                          {item.content && <p>{item.content}</p>}
                          {item.attachment_url && item.attachment_type === 'image' && <button type="button" className="chat-media-button" onClick={() => setLightboxUrl(item.attachment_url)}><img src={item.attachment_url} alt="Tệp ảnh trong tin nhắn" /></button>}
                          {item.attachment_url && item.attachment_type === 'video' && <video className="chat-video" src={item.attachment_url} controls preload="metadata" />}
                          <small>{item.created_at ? new Date(item.created_at).toLocaleString('vi-VN') : 'Mới'}</small>
                        </div>
                      ))
                    )}
                  </div>

                  {chatPreviewUrl && <div className="attachment-preview"><img src={chatPreviewUrl} alt="Xem trước tệp đính kèm" /><button type="button" className="icon-button" title="Bỏ tệp đính kèm" onClick={() => { setChatAttachment(null); setChatPreviewUrl('') }}><X size={16} /></button></div>}
                  <form onSubmit={handleChatSubmit} className="inline-group chat-input-row">
                    <label className="icon-button" title="Đính kèm ảnh hoặc video"><Paperclip size={18} /><input type="file" accept=".jpg,.jpeg,.png,.webp,.mp4,.webm" onChange={handleChatAttachment} hidden /></label>
                    <input value={chatInput} onChange={(event) => setChatInput(event.target.value)} placeholder="Nhập tin nhắn..." />
                    <button type="submit" className="primary-btn"><Send size={16} /> Gửi</button>
                  </form>
                  {chatStatus && <p className="loading-state connection-status">{chatConnected ? <Wifi size={15} /> : <WifiOff size={15} />} {chatStatus}</p>}
                </>
              )}
            </div>
          </section>
        )}

        {lightboxUrl && <div className="lightbox" role="dialog" aria-label="Ảnh phóng to" onClick={() => setLightboxUrl('')}><button type="button" className="icon-button" title="Đóng" onClick={() => setLightboxUrl('')}><X /></button><img src={lightboxUrl} alt="Ảnh phóng to" onClick={(event) => event.stopPropagation()} /></div>}

        {activeTab === 'admin' && !currentUser?.is_staff && (
          <section className="auth-page"><div className="auth-card thanks-card"><span className="eyebrow dark">Truy cập bị từ chối</span><h1>Khu vực quản trị</h1><p>Chỉ tài khoản quản trị mới có thể quản lý điểm đến, chỗ ở và loại phòng.</p><button type="button" className="primary-btn" onClick={() => navigate('/')}>Về trang chủ</button></div></section>
        )}

        {activeTab === 'admin' && currentUser?.is_staff && (
          <section className="admin-panel">
            <div className="section-head">
              <span className="eyebrow dark">Quản trị nội dung</span>
              <h2>Quản lý điểm đến và chỗ ở</h2>
            </div>

            {adminMessage && <div className="admin-message">{adminMessage}</div>}

            <div className="admin-grid">
              <form className="admin-form" onSubmit={submitDestination}>
                <h3>{destinationEditId ? 'Cập nhật điểm đến' : 'Thêm điểm đến mới'}</h3>
                <label>
                  Tên điểm đến
                  <input name="name" value={destinationForm.name} onChange={handleDestinationField} />
                </label>
                <label>
                  Mô tả
                  <textarea name="description" value={destinationForm.description} onChange={handleDestinationField} rows="3" />
                </label>
                <div className="inline-group">
                  <label>
                    Loại
                    <select name="category" value={destinationForm.category} onChange={handleDestinationField}>
                      <option value="biển">Biển</option>
                      <option value="núi">Núi</option>
                      <option value="thành phố">Thành phố</option>
                      <option value="ẩm thực">Ẩm thực</option>
                    </select>
                  </label>
                  <label>
                    Rating
                    <input name="rating" type="number" step="0.1" min="0" max="5" value={destinationForm.rating} onChange={handleDestinationField} />
                  </label>
                </div>
                <div className="inline-group">
                  <label>
                    Vĩ độ
                    <input name="latitude" type="number" step="0.0001" value={destinationForm.latitude} onChange={handleDestinationField} />
                  </label>
                  <label>
                    Kinh độ
                    <input name="longitude" type="number" step="0.0001" value={destinationForm.longitude} onChange={handleDestinationField} />
                  </label>
                </div>
                <label>
                  Ảnh
                  <input name="image_url" value={destinationForm.image_url} onChange={handleDestinationField} />
                </label>
                <div className="form-actions">
                  <button type="submit" className="primary-btn">{destinationEditId ? 'Lưu thay đổi' : 'Thêm điểm đến'}</button>
                  {destinationEditId && (
                    <button type="button" className="secondary-btn" onClick={() => { setDestinationForm(emptyDestinationForm); setDestinationEditId(null) }}>
                      Hủy
                    </button>
                  )}
                </div>
              </form>

              <div className="admin-list">
                <h3>Danh sách điểm đến</h3>
                {destinations.length === 0 ? <p>Chưa có dữ liệu điểm đến.</p> : destinations.map((item) => (
                  <div className="list-item" key={item.id}>
                    <div>
                      <strong>{item.name}</strong>
                      <p>{item.category} · {item.rating} sao</p>
                    </div>
                    <div className="list-actions">
                      <button type="button" className="secondary-btn" onClick={() => startEditDestination(item)}>Sửa</button>
                      <button type="button" className="danger-btn" onClick={() => deleteDestination(item.id)}>Xóa</button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="admin-grid">
              <form className="admin-form" onSubmit={submitAccommodation}>
                <h3>{accommodationEditId ? 'Cập nhật chỗ ở' : 'Thêm chỗ ở mới'}</h3>
                <label>
                  Tên chỗ ở
                  <input name="name" value={accommodationForm.name} onChange={handleAccommodationField} />
                </label>
                <label>
                  Mô tả
                  <textarea name="description" value={accommodationForm.description} onChange={handleAccommodationField} rows="3" />
                </label>
                <div className="inline-group">
                  <label>
                    Loại
                    <select name="category" value={accommodationForm.category} onChange={handleAccommodationField}>
                      <option value="hotel">Hotel</option>
                      <option value="homestay">Homestay</option>
                    </select>
                  </label>
                  <label>
                    Rating
                    <input name="rating" type="number" step="0.1" min="0" max="5" value={accommodationForm.rating} onChange={handleAccommodationField} />
                  </label>
                </div>
                <div className="inline-group">
                  <label>
                    Vĩ độ
                    <input name="latitude" type="number" step="0.0001" value={accommodationForm.latitude} onChange={handleAccommodationField} />
                  </label>
                  <label>
                    Kinh độ
                    <input name="longitude" type="number" step="0.0001" value={accommodationForm.longitude} onChange={handleAccommodationField} />
                  </label>
                </div>
                <div className="form-actions">
                  <button type="submit" className="primary-btn">{accommodationEditId ? 'Lưu thay đổi' : 'Thêm chỗ ở'}</button>
                  {accommodationEditId && (
                    <button type="button" className="secondary-btn" onClick={() => { setAccommodationForm(emptyAccommodationForm); setAccommodationEditId(null) }}>
                      Hủy
                    </button>
                  )}
                </div>
              </form>

              <div className="admin-list">
                <h3>Danh sách chỗ ở</h3>
                {accommodations.length === 0 ? <p>Chưa có dữ liệu chỗ ở.</p> : accommodations.map((item) => (
                  <div className="list-item list-item-column" key={item.id}>
                    <div className="list-main">
                      <div>
                        <strong>{item.name}</strong>
                        <p>{item.category} · {item.rating} sao</p>
                      </div>
                      <div className="list-actions">
                        <button type="button" className="secondary-btn" onClick={() => startEditAccommodation(item)}>Sửa</button>
                        <button type="button" className="danger-btn" onClick={() => deleteAccommodation(item.id)}>Xóa</button>
                        <button type="button" className="primary-btn" onClick={() => setSelectedAccommodationId(item.id)}>Chọn phòng</button>
                      </div>
                    </div>

                    <div className="room-list">
                      {(roomTypesByAccommodation[item.id] || []).map((room) => (
                        <div className="room-item" key={room.id}>
                          <div>
                            <strong>{room.name}</strong>
                            <p>{room.stock} phòng · {Number(room.base_price).toLocaleString()} đ</p>
                            <div className="amenity-list" aria-label="Tiện ích phòng">
                              {(room.amenities || []).map((amenity) => <span className="amenity-icon" title={amenity} key={amenity}>{amenityIcon(amenity)}</span>)}
                            </div>
                          </div>
                          <div className="list-actions">
                            <button type="button" className="secondary-btn" onClick={() => startEditRoomType(room, item.id)}>Sửa</button>
                            <button type="button" className="danger-btn" onClick={() => deleteRoomType(room.id)}>Xóa</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <form className="admin-form room-form" onSubmit={submitRoomType}>
              <h3>{roomTypeEditId ? 'Cập nhật loại phòng' : 'Thêm loại phòng cho chỗ ở đã chọn'}</h3>
              <label>
                Chỗ ở đang chọn
                <select value={selectedAccommodationId || ''} onChange={(event) => setSelectedAccommodationId(Number(event.target.value))}>
                  <option value="">-- Chọn chỗ ở --</option>
                  {accommodations.map((item) => (
                    <option key={item.id} value={item.id}>{item.name}</option>
                  ))}
                </select>
              </label>
              <label>
                Tên loại phòng
                <input name="name" value={roomTypeForm.name} onChange={handleRoomTypeField} />
              </label>
              <div className="inline-group">
                <label>
                  Giá phòng
                  <input name="base_price" type="number" value={roomTypeForm.base_price} onChange={handleRoomTypeField} />
                </label>
                <label>
                  Số lượng
                  <input name="stock" type="number" value={roomTypeForm.stock} onChange={handleRoomTypeField} />
                </label>
              </div>
              <label>
                Tiện ích
                <input name="amenities" value={roomTypeForm.amenities} onChange={handleRoomTypeField} />
              </label>
              <div className="form-actions">
                <button type="submit" className="primary-btn">{roomTypeEditId ? 'Lưu loại phòng' : 'Thêm loại phòng'}</button>
                {roomTypeEditId && (
                  <button type="button" className="secondary-btn" onClick={() => {
                    setRoomTypeEditId(null)
                    setRoomTypeForm({
                      name: '',
                      base_price: '1200000',
                      stock: '2',
                      amenities: 'wifi, điều hòa, bồn tắm',
                    })
                  }}>
                    Hủy
                  </button>
                )}
              </div>
            </form>
          </section>
        )}
      </main>
      <footer className="site-footer">
        <nav aria-label="Liên kết nội bộ">
          <button type="button" onClick={() => navigate('/')}>Trang chủ</button>
          <button type="button" onClick={() => navigate('/tinh-nang')}>Tính năng</button>
          <button type="button" onClick={() => navigate('/goi-y')}>Gợi ý du lịch</button>
          <button type="button" onClick={() => navigate('/dang-ky')}>Đăng ký</button>
          <button type="button" onClick={() => navigate('/dang-nhap')}>Đăng nhập</button>
        </nav>
        <p>© 2026 DuLich_ThongMinh · Lên kế hoạch chuyến đi thông minh.</p>
      </footer>
    </div>
  )
}

export default App

import { useEffect, useState } from 'react'
import './App.css'

const highlights = [
  'Gợi ý điểm đến theo sở thích cá nhân',
  'Dự báo thời tiết theo ngày đến dự kiến',
  'Tối ưu ngân sách và khoảng cách di chuyển',
  'Đặt phòng + thanh toán sandbox cho demo',
]

const backendUrl = 'http://localhost:8000'

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
  const [activeTab, setActiveTab] = useState('home')
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
  const [profileForm, setProfileForm] = useState({
    travel_preferences: 'biển,ẩm thực',
    budget_estimate: '6000000',
    free_text: 'Muốn nghỉ dưỡng, ăn ngon và trải nghiệm biển.',
  })
  const [profileMessage, setProfileMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('du lịch biển Phú Quốc')
  const [searchHistory, setSearchHistory] = useState([])

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
        fetch(`${backendUrl}/api/admin/destinations/`),
        fetch(`${backendUrl}/api/admin/accommodations/`),
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
          const response = await fetch(`${backendUrl}/api/admin/accommodations/${item.id}/room-types/`)
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
  }, [])

  useEffect(() => {
    if (activeTab === 'admin') {
      refreshAdminData()
    }
  }, [activeTab])

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
      const response = await fetch(endpoint, {
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
      const response = await fetch(endpoint, {
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
      const response = await fetch(`${backendUrl}/api/admin/destinations/${id}/`, { method: 'DELETE' })
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
      const response = await fetch(`${backendUrl}/api/admin/accommodations/${id}/`, { method: 'DELETE' })
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
      const response = await fetch(endpoint, {
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
      const response = await fetch(`${backendUrl}/api/admin/room-types/${roomTypeId}/`, { method: 'DELETE' })
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
      const response = await fetch(`${backendUrl}/api/profile/${userId}/`)
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
      fetchUserProfile(data.id)
      fetchSearchHistory(data.id)
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

  return (
    <div className="travel-app">
      <header className="topbar">
        <div className="brand">DuLich_ThongMinh</div>
        <nav>
          <button type="button" className={activeTab === 'home' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveTab('home')}>
            Giới thiệu
          </button>
          <button type="button" className={activeTab === 'features' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveTab('features')}>
            Tính năng
          </button>
          <button type="button" className={activeTab === 'recommend' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveTab('recommend')}>
            Gợi ý
          </button>
          <button type="button" className={activeTab === 'profile' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveTab('profile')}>
            Hồ sơ
          </button>
          <button type="button" className={activeTab === 'admin' ? 'nav-button active' : 'nav-button'} onClick={() => setActiveTab('admin')}>
            Quản trị
          </button>
        </nav>
        <button className="primary-btn">Đăng nhập</button>
      </header>

      <main>
        {activeTab === 'home' && (
          <>
            <section className="hero">
              <div className="hero-copy">
                <span className="eyebrow">Website gợi ý du lịch thông minh</span>
                <h1>Khám phá hành trình phù hợp với bạn hơn.</h1>
                <p>
                  Hệ thống dựa trên sở thích du lịch, ngân sách, thời tiết và khoảng cách để đề xuất
                  điểm đến, nơi nghỉ, và lịch trình tối ưu nhất cho mỗi chuyến đi.
                </p>
                <div className="hero-actions">
                  <button className="primary-btn" onClick={() => setActiveTab('recommend')}>Bắt đầu ngay</button>
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
                  <span className="tag">Điểm đến hot</span>
                  <h3>Phú Quốc</h3>
                  <p>Hạ tầng tốt, biển đẹp, phù hợp nghỉ dưỡng dài ngày.</p>
                  <div className="meta-row">
                    <span>Thời tiết: 29°C</span>
                    <span>Ưu tiên: 92%</span>
                  </div>
                </div>
                <div className="mini-card card-small">
                  <span>Ngân sách ước tính</span>
                  <strong>6.5 triệu</strong>
                </div>
              </div>
            </section>

            <section id="features" className="features">
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
            </section>
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
              {loading && <p className="loading-state">Đang tính toán gợi ý...</p>}
              {!loading && results.length === 0 && !error && <p className="loading-state">Chưa có dữ liệu điểm đến.</p>}
              {results.map((item, index) => (
                <article className="destination-card" key={item.id || `${item.name}-${index}`}>
                  <span className="destination-tag">{item.category}</span>
                  <h3>{item.name}</h3>
                  <p>{item.description}</p>
                  <div className="destination-meta">
                    <span>Điểm số: {item.score}</span>
                    <span>Khoảng cách: {item.distance_km} km</span>
                  </div>
                  <div className="destination-meta">
                    <span>Rating: {item.rating}</span>
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
          </section>
        )}

        {activeTab === 'admin' && (
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
    </div>
  )
}

export default App

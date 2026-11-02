import { NavLink, useSearchParams, useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'
import { Volume2, VolumeX } from 'lucide-react'
import { api, getAmenities, getDestinations, lookupDestinations } from '../api'
import { amenityIcon, amenityIconOptions, setAmenityCatalog } from '../amenityIcons'
import ChatRoom from '../components/ChatRoom'
import { useChatConnection } from '../components/ChatConnection'

const emptyDestination = { name: '', description: '', address: '', reference_cost: 0, category: 'biển', latitude: '', longitude: '', image_url: '', rating: '4.5' }
const emptyAccommodation = { destination: '', name: '', description: '', category: 'hotel', latitude: '', longitude: '', rating: '4.5' }
const emptyRoom = { name: '', base_price: '', stock: '', amenities: [] }
const emptyTour = {
  name: '',
  description: '',
  category: 'kham_pha',
  duration_days: '3',
  price_adult: '2000000',
  price_child: '1000000',
  single_room_supplement: '300000',
  min_age: '5',
  included_services: 'Xe đưa đón, Hướng dẫn viên, Vé tham quan, Bữa ăn theo tour',
  excluded_services: 'Chi phí cá nhân, Đồ uống, Tiền tip',
  cancellation_policy: 'Hủy trước 7 ngày hoàn 100%, hủy trước 3 ngày hoàn 50%, hủy dưới 3 ngày không hoàn tiền.',
  cover_image_url: '',
  is_active: true,
}

const listFromApi = (value) => {
  if (Array.isArray(value)) return value.filter((item) => item && typeof item === 'object')
  if (Array.isArray(value?.results)) return value.results.filter((item) => item && typeof item === 'object')
  return []
}

export function AdminLayout({ title, children }) {
  const { unreadCount } = useChatConnection()
  return (
    <section className="admin-panel">
      <aside className="admin-sidebar">
        <strong>Quản trị</strong>
        <NavLink to="/quan-tri">Tổng quan</NavLink>
        <NavLink to="/quan-tri/diem-den">Điểm đến</NavLink>
        <NavLink to="/quan-tri/cho-o">Chỗ ở</NavLink>
        <NavLink to="/quan-tri/phong">Loại phòng</NavLink>
        <NavLink to="/quan-tri/tien-ich">Tiện ích</NavLink>
        <NavLink to="/quan-tri/dat-phong">Đặt phòng</NavLink>
        <NavLink to="/quan-tri/tours">Quản lý Tour</NavLink>
        <NavLink to="/quan-tri/dat-tour">Đơn đặt Tour</NavLink>
        <NavLink to="/quan-tri/chat" className={({ isActive }) => `admin-chat-nav-link ${isActive ? 'active' : ''}`}>Hội thoại hỗ trợ{unreadCount > 0 && <span className="admin-nav-unread" aria-label={`${unreadCount} tin nhắn chưa đọc`}>{unreadCount > 99 ? '99+' : unreadCount}</span>}</NavLink>
        <NavLink to="/quan-tri/thong-ke">Thống kê</NavLink>
        <NavLink to="/quan-tri/gioi-thieu">Trang giới thiệu</NavLink>
      </aside>
      <div className="admin-content">
        <div className="section-head">
          <span className="eyebrow dark">Quản trị</span>
          <h1>{title}</h1>
        </div>
        {children}
      </div>
    </section>
  )
}

export function AdminChatPage({ user }) {
  const [conversations, setConversations] = useState([])
  const [selected, setSelected] = useState(null)
  const [error, setError] = useState('')
  const selectedRef = useRef(selected)
  const { connection, markRead, soundEnabled, toggleSound } = useChatConnection()
  selectedRef.current = selected

  useEffect(() => {
    let active = true
    const load = () => api('/api/admin/chat/conversations/').then((data) => {
      if (!active) return
      const results = listFromApi(data?.results)
      setConversations(results)
      setSelected((current) => current || results[0]?.user?.id || null)
    }).catch((e) => active && setError(e.message || 'Không tải được danh sách hội thoại.'))
    load()
    const onFrame = (event) => {
      const message = event.detail
      if (message?.type !== 'new_message') return
      const conversationId = Number(message.conversation_user)
      const isOpenHere = selectedRef.current === conversationId && document.visibilityState === 'visible'
      const isIncoming = Number(message.sender) !== Number(user.id)
      setConversations((current) => {
        const existing = current.find((item) => item.user.id === conversationId)
        const next = existing
          ? { ...existing, last_message: message, last_message_at: message.created_at, unread_count: isOpenHere ? 0 : isIncoming ? existing.unread_count + 1 : existing.unread_count }
          : { user: { id: conversationId, username: message.sender_name || 'Người dùng' }, last_message: message, last_message_at: message.created_at, unread_count: isOpenHere || !isIncoming ? 0 : 1 }
        return [next, ...current.filter((item) => item.user.id !== conversationId)]
      })
      if (isOpenHere) markRead(conversationId)
    }
    window.addEventListener('travel-chat-frame', onFrame)
    return () => { active = false; window.removeEventListener('travel-chat-frame', onFrame) }
  }, [user.id, markRead, connection])

  return <AdminLayout title="Hội thoại hỗ trợ">
    {error && <p className="form-error" role="status">{error}</p>}
    <div className="admin-chat-layout">
      <aside className="admin-chat-list" aria-label="Danh sách hội thoại">
        <h2>Cuộc trò chuyện</h2>
        {conversations.length ? conversations.map((conversation) => <button type="button" key={conversation.user.id} className={`admin-chat-conversation ${selected === conversation.user.id ? 'is-selected' : ''} ${conversation.unread_count ? 'has-unread' : ''}`} onClick={() => { setSelected(conversation.user.id); markRead(conversation.user.id); setConversations((current) => current.map((item) => item.user.id === conversation.user.id ? { ...item, unread_count: 0 } : item)) }}>
          <span className="admin-chat-avatar">{conversation.user.username?.slice(0, 1)?.toUpperCase() || 'K'}</span>
          <span className="admin-chat-preview"><strong>{conversation.user.username}</strong><small>{conversation.last_message?.content || 'Tệp đính kèm'}</small></span>
          {conversation.unread_count > 0 && <span className="chat-unread-count">{conversation.unread_count}</span>}
        </button>) : <div className="chat-empty"><p>Chưa có hội thoại nào. Tin nhắn mới sẽ hiện tại đây.</p></div>}
      </aside>
      <section className="admin-chat-window">
        <div className="admin-chat-sound"><button className="travel-button travel-button--outline" type="button" aria-pressed={soundEnabled} onClick={toggleSound}>{soundEnabled ? <Volume2 size={16} aria-hidden="true" /> : <VolumeX size={16} aria-hidden="true" />}{soundEnabled ? 'Tắt âm báo' : 'Bật âm báo'}</button></div>
        {selected ? <ChatRoom key={selected} conversationId={selected} currentUserId={user.id} isAdmin active /> : <div className="empty-state"><h2>Chọn một hội thoại</h2><p>Chọn người dùng bên trái để xem và trả lời tin nhắn.</p></div>}
      </section>
    </div>
  </AdminLayout>
}

function Notice({ message, error }) {
  return message ? <p className={error ? 'form-error' : 'admin-message'}>{message}</p> : null
}

export function AdminDashboardPage() {
  return (
    <AdminLayout title="Tổng quan">
      <div className="feature-grid">
        <article>
          <h3>Điểm đến</h3>
          <p>Quản lý nội dung, tọa độ và hình ảnh địa danh du lịch.</p>
        </article>
        <article>
          <h3>Chỗ ở</h3>
          <p>Quản lý chỗ ở và danh mục các loại phòng.</p>
        </article>
        <article>
          <h3>Đặt phòng</h3>
          <p>Xem, quản lý trạng thái và hủy đơn đặt phòng lưu trú.</p>
        </article>
        <article>
          <h3>Quản lý Tour</h3>
          <p>Quản lý tour, soạn lịch trình điểm dừng và quản lý chuyến khởi hành.</p>
        </article>
        <article>
          <h3>Đơn đặt Tour</h3>
          <p>Quản lý danh sách khách đặt tour, xem SĐT giải mã và đổi trạng thái.</p>
        </article>
        <article>
          <h3>Thống kê</h3>
          <p>Theo dõi lượt tìm kiếm, điểm đến gợi ý và số lượng đặt tour/phòng thành công.</p>
        </article>
      </div>
    </AdminLayout>
  )
}

export function AdminDestinationsPage() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(emptyDestination)
  const [editId, setEditId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [lookupQuery, setLookupQuery] = useState('')
  const [lookupResults, setLookupResults] = useState([])
  const [lookupLoading, setLookupLoading] = useState(false)
  const [lookupError, setLookupError] = useState('')
  const lookupRequest = useRef(0)

  const load = () => api('/api/admin/destinations/').then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  useEffect(() => { void load() }, [])

  const searchDestinations = async (event) => {
    event.preventDefault()
    const query = lookupQuery.trim()
    if (!query) return
    const requestId = ++lookupRequest.current
    setLookupLoading(true)
    setLookupError('')
    setLookupResults([])
    try {
      const data = await lookupDestinations(query)
      if (requestId === lookupRequest.current) setLookupResults(listFromApi(data?.results))
    } catch (err) {
      if (requestId === lookupRequest.current) setLookupError(err.message)
    } finally {
      if (requestId === lookupRequest.current) setLookupLoading(false)
    }
  }

  const selectLookupResult = (place) => {
    setForm((current) => ({
      ...current,
      name: place.name || current.name,
      latitude: String(place.latitude ?? current.latitude),
      longitude: String(place.longitude ?? current.longitude),
      image_url: place.image_url || current.image_url,
      address: place.full_name || current.address,
    }))
    setLookupResults([])
  }

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    if (!form.name || !form.description || !form.latitude || !form.longitude) {
      return setError('Vui lòng điền tên, mô tả và tọa độ.')
    }
    try {
      const endpoint = editId ? `/api/admin/destinations/${editId}/` : '/api/admin/destinations/'
      await api(endpoint, {
        method: editId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          rating: Number(form.rating || 0),
        }),
      })
      setMessage(editId ? 'Đã cập nhật điểm đến.' : 'Đã tạo điểm đến.')
      setForm(emptyDestination)
      setEditId(null)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const edit = (row) => {
    setEditId(row.id)
    setForm({
      name: row.name || '',
      description: row.description || '',
      address: row?.address || '',
      reference_cost: row?.reference_cost ?? 0,
      category: row.category || 'biển',
      latitude: row.latitude ?? '',
      longitude: row.longitude ?? '',
      image_url: row.image_url || '',
      rating: row.rating ?? '4.5',
    })
  }

  const remove = async (id) => {
    if (!window.confirm('Xóa điểm đến này?')) return
    try {
      await api(`/api/admin/destinations/${id}/`, { method: 'DELETE' })
      setMessage('Đã xóa điểm đến.')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Điểm đến">
      <Notice message={message} />
      <Notice message={error} error />
      <form className="admin-form" onSubmit={submit}>
        <h2>{editId ? 'Sửa điểm đến' : 'Tạo điểm đến'}</h2>
        <div className="destination-lookup">
          <div className="destination-lookup-form">
            <label htmlFor="destination-lookup-query">Tìm địa điểm từ Nominatim
              <input id="destination-lookup-query" type="search" value={lookupQuery} onChange={(event) => setLookupQuery(event.target.value)} placeholder="Ví dụ: Vịnh Hạ Long" />
            </label>
            <button className="secondary-btn" type="button" onClick={searchDestinations} disabled={lookupLoading || !lookupQuery.trim()}>{lookupLoading ? 'Đang tìm…' : 'Tìm địa điểm'}</button>
          </div>
          {lookupError && <p className="form-error">{lookupError}</p>}
          {lookupResults.length > 0 && <ul className="destination-lookup-results" aria-label="Kết quả tìm địa điểm">
            {lookupResults.map((place, index) => <li key={`${place.latitude}-${place.longitude}-${index}`}>
              <button type="button" className="destination-lookup-option" onClick={() => selectLookupResult(place)}>
                <strong>{place.name}</strong><span>{place.full_name}</span>
              </button>
            </li>)}
          </ul>}
          {!lookupLoading && lookupQuery.trim() && !lookupError && lookupResults.length === 0 && <p className="loading-state">Chưa có kết quả. Hãy thử tên địa điểm khác.</p>}
        </div>
        <label>Tên *<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label>Mô tả *<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        <label>Địa chỉ<input value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} /></label>
        <label>Chi phí tham khảo cho 3 ngày 2 đêm (VND)<input type="number" min="0" step="10000" value={form.reference_cost} onChange={(e) => setForm({ ...form, reference_cost: e.target.value })} /></label>
        <div className="inline-group">
          <label>Loại hình
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option>biển</option>
              <option>núi</option>
              <option>thành phố</option>
              <option>ẩm thực</option>
            </select>
          </label>
          <label>Đánh giá
            <input type="number" min="0" max="5" step="0.1" value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} />
          </label>
        </div>
        <div className="inline-group">
          <label>Vĩ độ *<input required type="number" step="0.0001" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} /></label>
          <label>Kinh độ *<input required type="number" step="0.0001" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} /></label>
        </div>
        <label>Ảnh URL<input type="url" value={form.image_url} onChange={(e) => setForm({ ...form, image_url: e.target.value })} /></label>
        <div className="form-actions">
          <button className="primary-btn">{editId ? 'Lưu thay đổi' : 'Tạo điểm đến'}</button>
          {editId && <button type="button" className="secondary-btn" onClick={() => { setForm(emptyDestination); setEditId(null) }}>Hủy</button>}
        </div>
      </form>
      <DataTable rows={rows} columns={['name', 'category', 'rating']} actions={(row) => (
        <>
          <button className="secondary-btn" onClick={() => edit(row)}>Sửa</button>
          <button className="danger-btn" onClick={() => remove(row.id)}>Xóa</button>
        </>
      )} />
    </AdminLayout>
  )
}

export function AdminAccommodationsPage() {
  const navigate = useNavigate()
  const [rows, setRows] = useState([])
  const [destinations, setDestinations] = useState([])
  const [form, setForm] = useState(emptyAccommodation)
  const [editId, setEditId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => api('/api/admin/accommodations/').then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  useEffect(() => { void load(); getDestinations().then((data) => setDestinations(listFromApi(data))).catch((err) => setError(err.message)) }, [])

  const selectDestination = (id) => {
    const destination = listFromApi(destinations).find((item) => String(item.id) === String(id))
    setForm((current) => ({
      ...current,
      destination: id,
      latitude: destination?.latitude ?? current.latitude,
      longitude: destination?.longitude ?? current.longitude,
    }))
  }

  const submit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    if (!form.name || !form.description || !form.destination || !form.latitude || !form.longitude) {
      return setError('Vui lòng điền các trường bắt buộc và chọn điểm đến.')
    }
    try {
      const endpoint = editId ? `/api/admin/accommodations/${editId}/` : '/api/admin/accommodations/'
      await api(endpoint, {
        method: editId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          destination: Number(form.destination),
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          rating: Number(form.rating || 0),
        }),
      })
      setMessage(editId ? 'Đã cập nhật chỗ ở.' : 'Đã tạo chỗ ở.')
      setForm(emptyAccommodation)
      setEditId(null)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const edit = (row) => {
    if (!row || typeof row !== 'object') return
    setForm({ destination: row.destination || '', name: row.name || '', description: row.description || '', category: row.category || 'hotel', latitude: row.latitude ?? '', longitude: row.longitude ?? '', rating: row.rating ?? '4.5' })
    setEditId(row.id ?? null)
  }

  const remove = async (id) => {
    if (!window.confirm('Xóa chỗ ở này và các loại phòng?')) return
    try {
      await api(`/api/admin/accommodations/${id}/`, { method: 'DELETE' })
      setMessage('Đã xóa chỗ ở.')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Chỗ ở">
      <Notice message={message} />
      <Notice message={error} error />
      <form className="admin-form" onSubmit={submit}>
        <h2>{editId ? 'Sửa chỗ ở' : 'Tạo chỗ ở'}</h2>
        <label>Điểm đến liên kết *
          <select required value={form.destination} onChange={(e) => selectDestination(e.target.value)}>
            <option value="">-- Chọn điểm đến --</option>
            {destinations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
          </select>
        </label>
        <label>Tên *<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label>Mô tả *<textarea required value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>
        <div className="inline-group">
          <label>Loại
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option value="hotel">Khách sạn</option>
              <option value="homestay">Nhà lưu trú</option>
            </select>
          </label>
          <label>Đánh giá
            <input type="number" min="0" max="5" step="0.1" value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} />
          </label>
        </div>
        <div className="inline-group">
          <label>Vĩ độ *<input required type="number" step="0.0001" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} /></label>
          <label>Kinh độ *<input required type="number" step="0.0001" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} /></label>
        </div>
        <div className="form-actions">
          <button className="primary-btn">{editId ? 'Lưu thay đổi' : 'Tạo chỗ ở'}</button>
          {editId && <button type="button" className="secondary-btn" onClick={() => { setForm(emptyAccommodation); setEditId(null) }}>Hủy</button>}
        </div>
      </form>
      <DataTable rows={rows} columns={['name', 'category', 'rating']} actions={(row) => (
        <>
          <button className="secondary-btn" onClick={() => { setEditId(row.id); edit(row) }}>Sửa</button>
          <button className="secondary-btn" onClick={() => navigate(`/quan-tri/phong?accommodation=${row.id}`)}>Quản lý loại phòng</button>
          <button className="danger-btn" onClick={() => remove(row.id)}>Xóa</button>
        </>
      )} />
    </AdminLayout>
  )
}

export function AdminRoomTypesPage() {
  const [params] = useSearchParams()
  const selectedAccommodation = params.get('accommodation') || ''
  const [accommodations, setAccommodations] = useState([])
  const [amenities, setAmenities] = useState([])
  const [rows, setRows] = useState([])
  const [form, setForm] = useState(emptyRoom)
  const [editId, setEditId] = useState(null)
  const [accommodationId, setAccommodationId] = useState(selectedAccommodation)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api('/api/admin/accommodations/').then((items) => setAccommodations(listFromApi(items))).catch((err) => setError(err.message))
    getAmenities().then((items) => { const list = listFromApi(items); setAmenities(list); setAmenityCatalog(list) }).catch((err) => setError(err.message))
  }, [])

  const load = () => {
    if (!accommodationId) { setRows([]); return }
    return api(`/api/admin/accommodations/${accommodationId}/room-types/`).then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  }
  useEffect(() => { void load() }, [accommodationId])

  const submit = async (event) => {
    event.preventDefault()
    if (!accommodationId || !form.name || !form.base_price || !form.stock) {
      return setError('Vui lòng chọn chỗ ở và điền đủ trường bắt buộc.')
    }
    try {
      const endpoint = editId ? `/api/admin/room-types/${editId}/` : `/api/admin/accommodations/${accommodationId}/room-types/`
      await api(endpoint, {
        method: editId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...form,
          base_price: Number(form.base_price),
          stock: Number(form.stock),
        }),
      })
      setMessage(editId ? 'Đã cập nhật loại phòng.' : 'Đã tạo loại phòng.')
      setForm(emptyRoom)
      setEditId(null)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const remove = async (id) => {
    if (!window.confirm('Xóa loại phòng này?')) return
    try {
      await api(`/api/admin/room-types/${id}/`, { method: 'DELETE' })
      setMessage('Đã xóa loại phòng.')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Loại phòng">
      <Notice message={message} />
      <Notice message={error} error />
      <label className="admin-form">Chỗ ở *
        <select value={accommodationId} onChange={(e) => { setAccommodationId(e.target.value); setRows([]) }}>
          <option value="">-- Chọn chỗ ở --</option>
          {accommodations.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
        </select>
      </label>
      <form className="admin-form" onSubmit={submit}>
        <h2>{editId ? 'Sửa loại phòng' : 'Tạo loại phòng'}</h2>
        <label>Tên *<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <div className="inline-group">
          <label>Giá/đêm *<input required type="number" min="0" value={form.base_price} onChange={(e) => setForm({ ...form, base_price: e.target.value })} /></label>
          <label>Số lượng *<input required type="number" min="1" value={form.stock} onChange={(e) => setForm({ ...form, stock: e.target.value })} /></label>
        </div>
        <fieldset className="amenity-checkboxes">
          <legend>Tiện ích</legend>
          {amenities.map((item) => (
            <label className="amenity-checkbox" key={item.key}>
              <input
                type="checkbox"
              checked={Array.isArray(form.amenities) && form.amenities.includes(item.key)}
                onChange={() => setForm({
                  ...form,
                amenities: (Array.isArray(form.amenities) ? form.amenities : []).includes(item.key)
                  ? (Array.isArray(form.amenities) ? form.amenities : []).filter((key) => key !== item.key)
                  : [...(Array.isArray(form.amenities) ? form.amenities : []), item.key],
                })}
              />
              {amenityIcon(item.icon_name || item.key)}
              <span>{item.label}</span>
            </label>
          ))}
        </fieldset>
        <div className="form-actions">
          <button className="primary-btn">{editId ? 'Lưu thay đổi' : 'Tạo loại phòng'}</button>
          {editId && <button type="button" className="secondary-btn" onClick={() => { setForm(emptyRoom); setEditId(null) }}>Hủy</button>}
        </div>
      </form>
      <DataTable rows={rows} columns={['name', 'base_price', 'stock', 'amenities']} actions={(row) => (
        <>
          <button className="secondary-btn" onClick={() => { setEditId(row.id); setForm({ name: row.name || '', base_price: row.base_price ?? '', stock: row.stock ?? '', amenities: Array.isArray(row.amenities) ? row.amenities : [] }) }}>Sửa</button>
          <button className="danger-btn" onClick={() => remove(row.id)}>Xóa</button>
        </>
      )} />
    </AdminLayout>
  )
}

export function AdminAmenitiesPage() {
  const [rows, setRows] = useState([])
  const [form, setForm] = useState({ key: '', label: '', icon_name: amenityIconOptions[0] })
  const [editId, setEditId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => getAmenities().then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  useEffect(() => { void load() }, [])

  const submit = async (event) => {
    event.preventDefault()
    setMessage(''); setError('')
    try {
      const endpoint = editId ? `/api/admin/amenities/${editId}/` : '/api/admin/amenities/'
      const body = editId ? { label: form.label, icon_name: form.icon_name } : form
      await api(endpoint, { method: editId ? 'PATCH' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
      setMessage(editId ? 'Đã cập nhật tiện ích.' : 'Đã thêm tiện ích.')
      setForm({ key: '', label: '', icon_name: amenityIconOptions[0] }); setEditId(null); load()
    } catch (err) { setError(err.message) }
  }

  const remove = async (amenity) => {
    if (!window.confirm(`Xóa tiện ích “${amenity.label}”? Khóa này sẽ được gỡ khỏi các loại phòng.`)) return
    try {
      await api(`/api/admin/amenities/${amenity.id}/`, { method: 'DELETE' })
      setMessage('Đã xóa tiện ích và gỡ khóa khỏi các loại phòng.')
      if (editId === amenity.id) { setEditId(null); setForm({ key: '', label: '', icon_name: amenityIconOptions[0] }) }
      load()
    } catch (err) { setError(err.message) }
  }

  return <AdminLayout title="Quản lý tiện ích">
    <Notice message={message} /><Notice message={error} error />
    <form className="admin-form amenity-admin-form" onSubmit={submit}>
      <h2>{editId ? 'Sửa tiện ích' : 'Thêm tiện ích'}</h2>
      <label>Khóa tiện ích *<input required pattern="[a-z0-9_-]+" disabled={!!editId} value={form.key} onChange={(event) => setForm({ ...form, key: event.target.value })} placeholder="vi_du_tien_ich" /></label>
      <label>Nhãn tiếng Việt *<input required maxLength="120" value={form.label} onChange={(event) => setForm({ ...form, label: event.target.value })} /></label>
      <label>Biểu tượng *<select value={form.icon_name} onChange={(event) => setForm({ ...form, icon_name: event.target.value })}>{amenityIconOptions.map((name) => <option key={name} value={name}>{name}</option>)}</select></label>
      <div className="amenity-icon-preview" aria-live="polite"><span>{amenityIcon(form.icon_name, 24)}</span><strong>Xem trước: {form.label || 'Tiện ích mới'}</strong></div>
      <div className="form-actions"><button className="primary-btn">{editId ? 'Lưu thay đổi' : 'Thêm tiện ích'}</button>{editId && <button type="button" className="secondary-btn" onClick={() => { setEditId(null); setForm({ key: '', label: '', icon_name: amenityIconOptions[0] }) }}>Hủy</button>}</div>
    </form>
    <div className="admin-list amenity-admin-list"><h2>Danh sách tiện ích</h2>{rows.map((item) => <article className="list-item amenity-admin-row" key={item.id}><span>{amenityIcon(item.icon_name, 20)}</span><div><strong>{item.label}</strong><small>{item.key} · {item.icon_name}</small></div><button type="button" className="secondary-btn" onClick={() => { setEditId(item.id); setForm({ key: item.key, label: item.label, icon_name: item.icon_name }) }}>Sửa</button><button type="button" className="danger-btn" onClick={() => remove(item)}>Xóa</button></article>)}</div>
  </AdminLayout>
}

export function AdminBookingsPage() {
  const [rows, setRows] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => api('/api/admin/bookings/').then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  useEffect(() => { void load() }, [])

  const cancel = async (row) => {
    const refund = window.prompt('Nhập số tiền hoàn tùy chỉnh (VND):', String(row.refund_amount || 0))
    if (refund === null) return
    if (!window.confirm('Hủy đơn đặt phòng này?')) return
    try {
      const data = await api(`/api/bookings/${row.id}/cancel/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refund_amount: Number.parseInt(refund, 10) || 0 }),
      })
      setMessage(data.message)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const changeStatus = async (row, nextStatus) => {
    if (nextStatus === 'cancelled') return cancel(row)
    try {
      await api(`/api/admin/bookings/${row.id}/status/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus }),
      })
      setMessage('Đã cập nhật trạng thái đơn đặt phòng.')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Đặt phòng">
      <Notice message={message} />
      <Notice message={error} error />
      <DataTable
        rows={rows}
        columns={['id', 'user', 'room_type_name', 'check_in', 'check_out', 'decrypted_phone', 'status', 'refund_amount', 'refund_status']}
        actions={(row) => (
          row.status !== 'cancelled' ? (
            <select value={row.status} onChange={(event) => changeStatus(row, event.target.value)}>
              <option value="pending">Chờ xử lý</option>
              <option value="confirmed">Xác nhận</option>
              <option value="cancelled">Hủy đơn đặt phòng</option>
            </select>
          ) : <span>Đã hủy</span>
        )}
      />
    </AdminLayout>
  )
}

export function AdminToursPage() {
  const [rows, setRows] = useState([])
  const [destinations, setDestinations] = useState([])
  const [form, setForm] = useState(emptyTour)
  const [editId, setEditId] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Sub-management: stops and departures
  const [activeTour, setActiveTour] = useState(null)
  const [activeTab, setActiveTab] = useState('stops') // 'stops' | 'departures'

  // Form stops
  const [stopForm, setStopForm] = useState({ destination_id: '', day_number: 1, note: '' })
  const [stopEditId, setStopEditId] = useState(null)
  // Form departures
  const [depForm, setDepForm] = useState({ departure_date: '', slots_total: 15 })

  const load = () => {
    api('/api/admin/tours/').then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
    getDestinations().then((data) => setDestinations(listFromApi(data))).catch(() => {})
  }
  useEffect(load, [])

  const submitTour = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    try {
      const payload = {
        name: form.name,
        description: form.description,
        category: form.category,
        duration_days: parseInt(form.duration_days) || 1,
        price_adult: parseInt(form.price_adult) || 0,
        price_child: form.price_child ? parseInt(form.price_child) : null,
        single_room_supplement: parseInt(form.single_room_supplement) || 0,
        min_age: form.min_age ? parseInt(form.min_age) : null,
        included_services: typeof form.included_services === 'string'
          ? form.included_services.split(',').map((s) => s.trim()).filter(Boolean)
          : form.included_services,
        excluded_services: typeof form.excluded_services === 'string'
          ? form.excluded_services.split(',').map((s) => s.trim()).filter(Boolean)
          : form.excluded_services,
        cancellation_policy: form.cancellation_policy,
        cover_image_url: form.cover_image_url,
        is_active: Boolean(form.is_active),
      }

      const endpoint = editId ? `/api/admin/tours/${editId}/` : '/api/admin/tours/'
      await api(endpoint, {
        method: editId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      setMessage(editId ? 'Đã cập nhật tour.' : 'Đã tạo tour mới.')
      setForm(emptyTour)
      setEditId(null)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  const editTour = (row) => {
    setEditId(row.id)
    setForm({
      name: row.name,
      description: row.description,
      category: row.category,
      duration_days: String(row.duration_days || 1),
      price_adult: String(row.price_adult || 0),
      price_child: row.price_child ? String(row.price_child) : '',
      single_room_supplement: String(row.single_room_supplement || 0),
      min_age: row.min_age ? String(row.min_age) : '',
      included_services: Array.isArray(row.included_services) ? row.included_services.join(', ') : '',
      excluded_services: Array.isArray(row.excluded_services) ? row.excluded_services.join(', ') : '',
      cancellation_policy: row.cancellation_policy || '',
      cover_image_url: row.cover_image_url || '',
      is_active: row.is_active ?? true,
    })
  }

  const removeTour = async (id) => {
    if (!window.confirm('Xóa tour này cùng toàn bộ lịch trình và chuyến khởi hành?')) return
    try {
      await api(`/api/admin/tours/${id}/`, { method: 'DELETE' })
      setMessage('Đã xóa tour.')
      if (activeTour?.id === id) setActiveTour(null)
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  // Manage stops
  const refreshActiveTour = async () => {
    if (!activeTour) return
    try {
      const updated = await api(`/api/admin/tours/${activeTour.id}/`)
      setActiveTour(updated)
      load()
    } catch {}
  }

  const addStop = async (event) => {
    event.preventDefault()
    if (!stopForm.destination_id) return setError('Vui lòng chọn điểm đến.')
    try {
      const endpoint = stopEditId
        ? `/api/admin/tours/${activeTour.id}/stops/${stopEditId}/`
        : `/api/admin/tours/${activeTour.id}/stops/`
      await api(endpoint, {
        method: stopEditId ? 'PATCH' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          destination_id: parseInt(stopForm.destination_id),
          day_number: parseInt(stopForm.day_number) || 1,
          note: stopForm.note,
        }),
      })
      setStopForm({ destination_id: '', day_number: 1, note: '' })
      setStopEditId(null)
      setMessage(stopEditId ? 'Đã cập nhật điểm dừng.' : 'Đã thêm điểm dừng vào lịch trình.')
      refreshActiveTour()
    } catch (err) {
      setError(err.message)
    }
  }

  const removeStop = async (stopId) => {
    try {
      await api(`/api/admin/tours/${activeTour.id}/stops/${stopId}/`, {
        method: 'DELETE',
      })
      setMessage('Đã xóa điểm dừng.')
      refreshActiveTour()
    } catch (err) {
      setError(err.message)
    }
  }

  const editStop = (stop) => {
    setStopEditId(stop.id)
    setStopForm({ destination_id: String(stop.destination?.id || stop.destination_id || ''), day_number: stop.day_number, note: stop.note || '' })
  }

  // Manage departures
  const addDeparture = async (event) => {
    event.preventDefault()
    if (!depForm.departure_date) return setError('Vui lòng chọn ngày khởi hành.')
    try {
      await api(`/api/admin/tours/${activeTour.id}/departures/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          departure_date: depForm.departure_date,
          slots_total: parseInt(depForm.slots_total) || 10,
        }),
      })
      setDepForm({ departure_date: '', slots_total: 15 })
      setMessage('Đã thêm chuyến khởi hành mới.')
      refreshActiveTour()
    } catch (err) {
      setError(err.message)
    }
  }

  const toggleCancelDeparture = async (dep) => {
    try {
      await api(`/api/admin/tours/departures/${dep.id}/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_cancelled: !dep.is_cancelled }),
      })
      setMessage(dep.is_cancelled ? 'Đã kích hoạt lại chuyến khởi hành.' : 'Đã hủy chuyến khởi hành.')
      refreshActiveTour()
    } catch (err) {
      setError(err.message)
    }
  }

  const removeDeparture = async (depId) => {
    if (!window.confirm('Xóa chuyến khởi hành này?')) return
    try {
      await api(`/api/admin/tours/departures/${depId}/`, { method: 'DELETE' })
      setMessage('Đã xóa chuyến khởi hành.')
      refreshActiveTour()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Quản lý Tour">
      <Notice message={message} />
      <Notice message={error} error />

      <form className="admin-form" onSubmit={submitTour}>
        <h2>{editId ? 'Sửa thông tin Tour' : 'Tạo Tour du lịch mới'}</h2>
        <label>Tên tour *<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
        <label>Mô tả *<textarea required rows="4" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} /></label>

        <div className="inline-group">
          <label>Danh mục *
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })}>
              <option value="kham_pha">Khám phá thiên nhiên</option>
              <option value="van_hoa">Văn hóa - Lịch sử</option>
              <option value="nghi_duong">Nghỉ dưỡng</option>
              <option value="mao_hiem">Mạo hiểm</option>
              <option value="am_thuc">Ẩm thực</option>
              <option value="ghep_doan">Tour ghép đoàn</option>
              <option value="rieng">Tour riêng</option>
            </select>
          </label>
          <label>Số ngày *
            <input required type="number" min="1" value={form.duration_days} onChange={(e) => setForm({ ...form, duration_days: e.target.value })} />
          </label>
        </div>

        <div className="inline-group">
          <label>Giá người lớn (VND) *
            <input required type="number" min="0" value={form.price_adult} onChange={(e) => setForm({ ...form, price_adult: e.target.value })} />
          </label>
          <label>Giá trẻ em (VND)
            <input type="number" min="0" value={form.price_child} onChange={(e) => setForm({ ...form, price_child: e.target.value })} />
          </label>
          <label>Phụ thu phòng đơn
            <input type="number" min="0" value={form.single_room_supplement} onChange={(e) => setForm({ ...form, single_room_supplement: e.target.value })} />
          </label>
        </div>

        <div className="inline-group">
          <label>Độ tuổi tối thiểu
            <input type="number" min="0" value={form.min_age} onChange={(e) => setForm({ ...form, min_age: e.target.value })} />
          </label>
          <label>Ảnh bìa URL
            <input type="url" value={form.cover_image_url} onChange={(e) => setForm({ ...form, cover_image_url: e.target.value })} />
          </label>
        </div>

        <label>Dịch vụ bao gồm (ngăn cách dấu phẩy)
          <input value={form.included_services} onChange={(e) => setForm({ ...form, included_services: e.target.value })} />
        </label>
        <label>Dịch vụ không bao gồm (ngăn cách dấu phẩy)
          <input value={form.excluded_services} onChange={(e) => setForm({ ...form, excluded_services: e.target.value })} />
        </label>
        <label>Chính sách hủy tour
          <textarea rows="2" value={form.cancellation_policy} onChange={(e) => setForm({ ...form, cancellation_policy: e.target.value })} />
        </label>

        <label className="checkbox-label">
          <input type="checkbox" checked={form.is_active} onChange={(e) => setForm({ ...form, is_active: e.target.checked })} />
          <span>Tour đang mở bán</span>
        </label>

        <div className="form-actions">
          <button className="primary-btn">{editId ? 'Lưu thay đổi' : 'Tạo tour'}</button>
          {editId && <button type="button" className="secondary-btn" onClick={() => { setForm(emptyTour); setEditId(null) }}>Hủy</button>}
        </div>
      </form>

      {activeTour && (
        <div className="sub-management-panel card">
          <div className="sub-panel-header">
            <h3>Chi tiết Tour: <strong>{activeTour.name}</strong></h3>
            <button className="secondary-btn sm" onClick={() => setActiveTour(null)}>Đóng quản lý chi tiết</button>
          </div>

          <div className="sub-panel-tabs">
            <button className={`tab-btn ${activeTab === 'stops' ? 'active' : ''}`} onClick={() => setActiveTab('stops')}>
              📍 Lịch trình stops ({activeTour.stops?.length || 0})
            </button>
            <button className={`tab-btn ${activeTab === 'departures' ? 'active' : ''}`} onClick={() => setActiveTab('departures')}>
              📅 Chuyến khởi hành ({activeTour.departures?.length || 0})
            </button>
          </div>

          {activeTab === 'stops' ? (
            <div className="stops-manager">
              <form className="inline-add-form" onSubmit={addStop}>
                <label>Ngày:
                  <input type="number" min="1" max={activeTour.duration_days} value={stopForm.day_number} onChange={(e) => setStopForm({ ...stopForm, day_number: e.target.value })} required />
                </label>
                <label>Điểm đến:
                  <select value={stopForm.destination_id} onChange={(e) => setStopForm({ ...stopForm, destination_id: e.target.value })} required>
                    <option value="">-- Chọn điểm đến --</option>
                    {destinations.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                  </select>
                </label>
                <label>Ghi chú:
                  <input placeholder="VD: Khám phá vịnh..." value={stopForm.note} onChange={(e) => setStopForm({ ...stopForm, note: e.target.value })} />
                </label>
                <button className="primary-btn sm">{stopEditId ? 'Lưu điểm dừng' : 'Thêm điểm dừng'}</button>
                {stopEditId && <button type="button" className="secondary-btn sm" onClick={() => { setStopEditId(null); setStopForm({ destination_id: '', day_number: 1, note: '' }) }}>Hủy sửa</button>}
              </form>

              <table className="admin-table">
                <thead>
                  <tr><th>Ngày</th><th>Điểm đến</th><th>Ghi chú</th><th>Thao tác</th></tr>
                </thead>
                <tbody>
                  {activeTour.stops?.map((stop) => (
                    <tr key={stop.id}>
                      <td>Ngày {stop.day_number}</td>
                      <td>{stop.destination?.name}</td>
                      <td>{stop.note || '—'}</td>
                      <td><button className="secondary-btn sm" onClick={() => editStop(stop)}>Sửa</button> <button className="danger-btn sm" onClick={() => removeStop(stop.id)}>Xóa</button></td>
                    </tr>
                  ))}
                  {(!activeTour.stops || activeTour.stops.length === 0) && (
                    <tr><td colSpan="4">Chưa có điểm dừng nào.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="departures-manager">
              <form className="inline-add-form" onSubmit={addDeparture}>
                <label>Ngày khởi hành:
                  <input type="date" value={depForm.departure_date} onChange={(e) => setDepForm({ ...depForm, departure_date: e.target.value })} required />
                </label>
                <label>Tổng số chỗ:
                  <input type="number" min="1" value={depForm.slots_total} onChange={(e) => setDepForm({ ...depForm, slots_total: e.target.value })} required />
                </label>
                <button className="primary-btn sm">Thêm chuyến</button>
              </form>

              <table className="admin-table">
                <thead>
                  <tr><th>Ngày đi</th><th>Tổng chỗ</th><th>Còn trống</th><th>Trạng thái</th><th>Thao tác</th></tr>
                </thead>
                <tbody>
                  {activeTour.departures?.map((dep) => (
                    <tr key={dep.id}>
                      <td>{dep.departure_date}</td>
                      <td>{dep.slots_total}</td>
                      <td><strong>{dep.slots_available}</strong></td>
                      <td>{dep.is_cancelled ? <span className="slot-badge full">Đã hủy</span> : <span className="slot-badge ok">Hoạt động</span>}</td>
                      <td className="list-actions">
                        <button className="secondary-btn sm" onClick={() => toggleCancelDeparture(dep)}>
                          {dep.is_cancelled ? 'Khôi phục' : 'Hủy chuyến'}
                        </button>
                        <button className="danger-btn sm" onClick={() => removeDeparture(dep.id)}>Xóa</button>
                      </td>
                    </tr>
                  ))}
                  {(!activeTour.departures || activeTour.departures.length === 0) && (
                    <tr><td colSpan="5">Chưa có chuyến đi nào.</td></tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      <h2>Danh sách Tour</h2>
      <DataTable
        rows={rows}
        columns={['id', 'name', 'category', 'duration_days', 'price_adult']}
        actions={(row) => (
          <>
            <button className="secondary-btn" onClick={() => editTour(row)}>Sửa</button>
            <button className="secondary-btn" onClick={() => setActiveTour(row)}>Lịch trình & Chuyến đi</button>
            <button className="danger-btn" onClick={() => removeTour(row.id)}>Xóa</button>
          </>
        )}
      />
    </AdminLayout>
  )
}

export function AdminTourBookingsPage() {
  const [rows, setRows] = useState([])
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = () => api('/api/admin/tour-bookings/').then((data) => setRows(listFromApi(data))).catch((err) => setError(err.message))
  useEffect(() => { void load() }, [])

  const changeStatus = async (row, nextStatus) => {
    let refund = 0
    if (nextStatus === 'cancelled') {
      const input = window.prompt('Nhập số tiền hoàn vé (VND) nếu có:', '0')
      if (input === null) return
      refund = parseInt(input) || 0
    }
    try {
      await api(`/api/admin/tour-bookings/${row.id}/status/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nextStatus, refund_amount: refund }),
      })
      setMessage('Đã cập nhật trạng thái đơn đặt tour.')
      load()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <AdminLayout title="Đơn đặt Tour">
      <Notice message={message} />
      <Notice message={error} error />
      <DataTable
        rows={rows}
        columns={['id', 'username', 'tour_name', 'departure_date', 'num_adults', 'num_children', 'total_price', 'decrypted_phone', 'status', 'refund_amount', 'refund_status']}
        actions={(row) => (
          <select value={row.status} onChange={(event) => changeStatus(row, event.target.value)}>
            <option value="pending">Chờ xử lý</option>
            <option value="confirmed">Xác nhận</option>
            <option value="cancelled">Hủy đơn</option>
          </select>
        )}
      />
    </AdminLayout>
  )
}

const columnLabels = {
  id: 'Mã',
  name: 'Tên',
  category: 'Danh mục',
  rating: 'Đánh giá',
  base_price: 'Giá/đêm',
  stock: 'Số lượng',
  amenities: 'Tiện ích',
  user: 'Người đặt',
  room_type: 'Loại phòng',
  check_in: 'Ngày nhận',
  check_out: 'Ngày trả',
  decrypted_phone: 'Số điện thoại',
  status: 'Trạng thái',
  duration_days: 'Số ngày',
  price_adult: 'Giá người lớn',
  username: 'Tài khoản',
  tour_name: 'Tên tour',
  departure_date: 'Ngày khởi hành',
  num_adults: 'Số người lớn',
  num_children: 'Số trẻ em',
  total_price: 'Tổng tiền',
  refund_amount: 'Số tiền hoàn',
  refund_status: 'Trạng thái hoàn',
  room_type_name: 'Loại phòng',
}

function DataTable({ rows, columns, actions }) {
  const safeRows = listFromApi(rows)
  const safeColumns = Array.isArray(columns) ? columns.filter((column) => typeof column === 'string') : []
  const statusLabels = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', cancelled: 'Đã hủy' }
  const refundLabels = { none: 'Chưa hoàn', pending: 'Đang hoàn', refunded: 'Đã hoàn', failed: 'Hoàn thất bại' }
  return (
    <div className="admin-table-wrap">
      <table className="admin-table">
        <thead>
          <tr>
            {safeColumns.map((column) => <th key={column}>{columnLabels[column] || column}</th>)}
            {actions && <th>Thao tác</th>}
          </tr>
        </thead>
        <tbody>
          {safeRows.map((row, index) => (
            <tr key={row.id || index}>
              {safeColumns.map((column) => (
                <td key={column}>{column === 'status' ? (statusLabels[row[column]] || String(row[column] ?? '')) : column === 'refund_status' ? (refundLabels[row[column]] || String(row[column] ?? '')) : column === 'refund_amount' ? `${Number(row[column] || 0).toLocaleString('vi-VN')} đ` : Array.isArray(row[column]) ? row[column].join(', ') : String(row[column] ?? '')}</td>
              ))}
              {actions && <td className="list-actions">{actions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
      {!safeRows.length && <p className="loading-state">Chưa có dữ liệu.</p>}
    </div>
  )
}

export function AdminStatisticsPage() {
  const [days, setDays] = useState(7)
  const [data, setData] = useState({
    total_searches: 0,
    searches_by_day: [],
    top_destinations: [],
    top_booked_destinations: [],
    days: 7,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = (selectedDays) => {
    setLoading(true)
    setError('')
    api(`/api/admin/statistics/?days=${selectedDays}`)
      .then((res) => {
        setData(res)
      })
      .catch((err) => {
        setError(err.message || 'Lỗi khi tải dữ liệu thống kê.')
      })
      .finally(() => {
        setLoading(false)
      })
  }

  useEffect(() => {
    loadData(days)
  }, [days])

  const maxSearchesInDay = Math.max(1, ...(data.searches_by_day || []).map((d) => d.count))
  const maxTopDestCount = Math.max(1, ...(data.top_destinations || []).map((d) => d.count || d.appearance_count || 0))
  const maxTopBookedCount = Math.max(1, ...(data.top_booked_destinations || []).map((d) => d.total_bookings || d.count || 0))
  const daysWithSearches = (data.searches_by_day || []).filter((d) => d.count > 0).length

  return (
    <AdminLayout title="Thống kê hệ thống">
      <Notice message={error} error />

      {/* Bộ chọn khoảng thời gian */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <p style={{ margin: 0, color: 'var(--text-muted, #666)' }}>
          Xem thống kê hoạt động gợi ý, tìm kiếm và đặt dịch vụ theo thời gian thực.
        </p>
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.05)', padding: '4px', borderRadius: '8px' }}>
          {[7, 30, 90].map((d) => (
            <button
              key={d}
              type="button"
              onClick={() => setDays(d)}
              style={{
                padding: '6px 16px',
                borderRadius: '6px',
                border: 'none',
                cursor: 'pointer',
                fontWeight: days === d ? '600' : 'normal',
                background: days === d ? 'var(--primary, #0ea5e9)' : 'transparent',
                color: days === d ? '#fff' : 'inherit',
                transition: 'all 0.2s',
              }}
            >
              {d} ngày qua
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="feature-grid" style={{ marginBottom: '32px' }}>
        <article style={{ borderLeft: '4px solid #0ea5e9', padding: '16px' }}>
          <span style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Tổng lượt tìm kiếm</span>
          <h2 style={{ fontSize: '28px', margin: '8px 0 4px', color: '#0ea5e9' }}>{loading ? '...' : data.total_searches}</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#777' }}>Lượt truy vấn gợi ý trong {days} ngày</p>
        </article>
        <article style={{ borderLeft: '4px solid #10b981', padding: '16px' }}>
          <span style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Ngày có lượt tìm</span>
          <h2 style={{ fontSize: '28px', margin: '8px 0 4px', color: '#10b981' }}>{loading ? '...' : `${daysWithSearches}/${data.searches_by_day?.length || days}`}</h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#777' }}>Tỷ lệ ngày có tương tác tìm kiếm</p>
        </article>
        <article style={{ borderLeft: '4px solid #f59e0b', padding: '16px' }}>
          <span style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Gợi ý nhiều nhất</span>
          <h2 style={{ fontSize: '20px', margin: '8px 0 4px', color: '#f59e0b', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {loading ? '...' : (data.top_destinations?.[0]?.name || 'Chưa có dữ liệu')}
          </h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#777' }}>
            {data.top_destinations?.[0] ? `${data.top_destinations[0].count} lượt gợi ý (Điểm: ${data.top_destinations[0].avg_score})` : 'Chưa có bản ghi gợi ý'}
          </p>
        </article>
        <article style={{ borderLeft: '4px solid #8b5cf6', padding: '16px' }}>
          <span style={{ fontSize: '13px', color: '#666', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Đặt thành công nhất</span>
          <h2 style={{ fontSize: '20px', margin: '8px 0 4px', color: '#8b5cf6', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {loading ? '...' : (data.top_booked_destinations?.[0]?.name || 'Chưa có dữ liệu')}
          </h2>
          <p style={{ margin: 0, fontSize: '13px', color: '#777' }}>
            {data.top_booked_destinations?.[0] ? `${data.top_booked_destinations[0].total_bookings} lượt booking đã xác nhận` : 'Chưa có đơn hoàn tất'}
          </p>
        </article>
      </div>

      {/* 1. Lượt tìm kiếm theo ngày */}
      <div style={{ marginBottom: '36px' }}>
        <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          📅 Lượt tìm kiếm theo ngày ({days} ngày gần nhất)
        </h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th style={{ width: '150px' }}>Ngày</th>
                <th style={{ width: '140px', textAlign: 'center' }}>Số lượt tìm kiếm</th>
                <th>Biểu đồ phân bổ</th>
              </tr>
            </thead>
            <tbody>
              {(data.searches_by_day || []).map((row) => {
                const percent = Math.round((row.count / maxSearchesInDay) * 100)
                return (
                  <tr key={row.date}>
                    <td><strong>{row.date}</strong></td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 10px',
                        borderRadius: '12px',
                        background: row.count > 0 ? 'rgba(14,165,233,0.15)' : 'rgba(0,0,0,0.05)',
                        color: row.count > 0 ? '#0284c7' : '#999',
                        fontWeight: '600',
                      }}>
                        {row.count}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, background: 'rgba(0,0,0,0.06)', borderRadius: '4px', height: '14px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${row.count > 0 ? Math.max(5, percent) : 0}%`,
                            background: 'linear-gradient(90deg, #0ea5e9, #38bdf8)',
                            height: '100%',
                            borderRadius: '4px',
                            transition: 'width 0.3s ease',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#888', minWidth: '35px' }}>{percent}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!data.searches_by_day?.length && <p className="loading-state">Chưa có dữ liệu tìm kiếm.</p>}
        </div>
      </div>

      {/* 2. Top 10 Điểm đến được gợi ý nhiều nhất */}
      <div style={{ marginBottom: '36px' }}>
        <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          ⭐ Top 10 điểm đến được gợi ý nhiều nhất
        </h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th style={{ width: '60px', textAlign: 'center' }}>Hạng</th>
                <th>Điểm đến</th>
                <th style={{ width: '140px', textAlign: 'center' }}>Số lần xuất hiện</th>
                <th style={{ width: '130px', textAlign: 'center' }}>Điểm trung bình</th>
                <th>Mức độ gợi ý</th>
              </tr>
            </thead>
            <tbody>
              {(data.top_destinations || []).map((row, idx) => {
                const count = row.count || row.appearance_count || 0
                const percent = Math.round((count / maxTopDestCount) * 100)
                return (
                  <tr key={row.destination_id || idx}>
                    <td style={{ textAlign: 'center', fontWeight: 'bold', color: idx < 3 ? '#f59e0b' : '#666' }}>
                      {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`}
                    </td>
                    <td>
                      <strong>{row.name}</strong>
                      <span style={{ fontSize: '11px', color: '#999', marginLeft: '6px' }}>(ID: {row.destination_id})</span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 10px',
                        borderRadius: '12px',
                        background: 'rgba(245,158,11,0.15)',
                        color: '#b45309',
                        fontWeight: '600',
                      }}>
                        {count} lần
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{ fontWeight: '600', color: '#059669' }}>
                        {Number(row.avg_score).toFixed(2)}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, background: 'rgba(0,0,0,0.06)', borderRadius: '4px', height: '14px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${Math.max(5, percent)}%`,
                            background: 'linear-gradient(90deg, #f59e0b, #fbbf24)',
                            height: '100%',
                            borderRadius: '4px',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#888', minWidth: '35px' }}>{percent}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!data.top_destinations?.length && <p className="loading-state">Chưa có điểm đến nào trong lịch sử gợi ý.</p>}
        </div>
      </div>

      {/* 3. Top 10 Điểm đến có nhiều booking thành công nhất */}
      <div style={{ marginBottom: '36px' }}>
        <h3 style={{ marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🏆 10 điểm đến được đặt nhiều nhất (đặt phòng + đặt tour)
        </h3>
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead>
              <tr>
                <th style={{ width: '60px', textAlign: 'center' }}>Hạng</th>
                <th>Điểm đến</th>
                <th style={{ width: '120px', textAlign: 'center' }}>Đặt phòng</th>
                <th style={{ width: '120px', textAlign: 'center' }}>Đặt tour</th>
                <th style={{ width: '140px', textAlign: 'center' }}>Tổng thành công</th>
                <th>Tỷ lệ trực quan</th>
              </tr>
            </thead>
            <tbody>
              {(data.top_booked_destinations || []).map((row, idx) => {
                const total = row.total_bookings ?? row.count ?? 0
                const percent = Math.round((total / maxTopBookedCount) * 100)
                return (
                  <tr key={row.destination_id || idx}>
                    <td style={{ textAlign: 'center', fontWeight: 'bold', color: idx < 3 ? '#8b5cf6' : '#666' }}>
                      {idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : `#${idx + 1}`}
                    </td>
                    <td>
                      <strong>{row.name}</strong>
                      <span style={{ fontSize: '11px', color: '#999', marginLeft: '6px' }}>(ID: {row.destination_id})</span>
                    </td>
                    <td style={{ textAlign: 'center' }}>{row.booking_count ?? 0}</td>
                    <td style={{ textAlign: 'center' }}>{row.tour_booking_count ?? 0}</td>
                    <td style={{ textAlign: 'center' }}>
                      <span style={{
                        display: 'inline-block',
                        padding: '2px 10px',
                        borderRadius: '12px',
                        background: 'rgba(139,92,246,0.15)',
                        color: '#6d28d9',
                        fontWeight: '600',
                      }}>
                        {total} đơn
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{ flex: 1, background: 'rgba(0,0,0,0.06)', borderRadius: '4px', height: '14px', overflow: 'hidden' }}>
                          <div style={{
                            width: `${Math.max(5, percent)}%`,
                            background: 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
                            height: '100%',
                            borderRadius: '4px',
                          }} />
                        </div>
                        <span style={{ fontSize: '12px', color: '#888', minWidth: '35px' }}>{percent}%</span>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {!data.top_booked_destinations?.length && <p className="loading-state">Chưa có đơn đặt phòng hoặc tour nào được xác nhận trong khoảng thời gian này.</p>}
        </div>
      </div>
    </AdminLayout>
  )
}


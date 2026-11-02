import { useEffect, useState, useCallback } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import {
  getTravelPosts,
  getTravelPost,
  createTravelPost,
  deleteTravelPost,
  likeTravelPost,
  getDestinations,
} from '../api'
import { useAuth } from '../auth'

// ─── helpers ────────────────────────────────────────────────────────────────

function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000
  if (diff < 60) return 'Vừa xong'
  if (diff < 3600) return `${Math.floor(diff / 60)} phút trước`
  if (diff < 86400) return `${Math.floor(diff / 3600)} giờ trước`
  return `${Math.floor(diff / 86400)} ngày trước`
}

function toast(msg, error = false) {
  window.dispatchEvent(new CustomEvent('toast', { detail: { message: msg, error } }))
}

// ─── PostCard ────────────────────────────────────────────────────────────────

function PostCard({ post, currentUser, onLike, onDelete }) {
  const cover = post.images?.[0]
  const canDelete = currentUser && (currentUser.id === post.user || currentUser.is_staff)

  return (
    <article className="travel-post-card mini-card">
      {cover && (
        <Link to={`/cong-dong/${post.id}`} className="travel-post-img-wrap">
          <img src={cover} alt={post.title} className="travel-post-img" />
        </Link>
      )}
      <div className="travel-post-body">
        <div className="travel-post-meta">
          <span className="eyebrow dark">{post.destination_name || 'Chung'}</span>
          <span className="travel-post-time">{timeAgo(post.created_at)}</span>
        </div>
        <Link to={`/cong-dong/${post.id}`} className="travel-post-title-link">
          <h3 className="travel-post-title">{post.title}</h3>
        </Link>
        <p className="travel-post-excerpt">{post.content.slice(0, 140)}{post.content.length > 140 ? '…' : ''}</p>
        <div className="travel-post-footer">
          <span className="travel-post-author">✍ {post.user_name}{post.user_is_demo && <span className="demo-badge">Minh họa</span>}</span>
          <div className="travel-post-actions">
            <button
              type="button"
              className={`like-btn ${post.is_liked ? 'liked' : ''}`}
              onClick={() => onLike(post.id)}
              aria-label={post.is_liked ? 'Bỏ thích' : 'Thích'}
            >
              {post.is_liked ? '❤️' : '🤍'} {post.likes_count}
            </button>
            {canDelete && (
              <button
                type="button"
                className="danger-btn"
                style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                onClick={() => onDelete(post.id)}
              >
                Xoá
              </button>
            )}
          </div>
        </div>
      </div>
    </article>
  )
}

// ─── CreatePostForm ──────────────────────────────────────────────────────────

function CreatePostForm({ destinations, onCreated }) {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [destinationId, setDestinationId] = useState('')
  const [imageUrls, setImageUrls] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    const images = imageUrls
      .split('\n')
      .map((u) => u.trim())
      .filter(Boolean)
    if (images.length > 5) { setError('Tối đa 5 ảnh.'); return }
    setLoading(true)
    try {
      const post = await createTravelPost({
        title,
        content,
        destination: destinationId || null,
        images,
      })
      toast('Đăng bài thành công!')
      setTitle(''); setContent(''); setDestinationId(''); setImageUrls('')
      onCreated(post)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form className="admin-form" onSubmit={handleSubmit} style={{ marginBottom: 32 }}>
      <h2 style={{ marginTop: 0 }}>✏️ Chia sẻ trải nghiệm</h2>
      {error && <p className="form-error">{error}</p>}
      <div className="form-group">
        <label htmlFor="post-title">Tiêu đề *</label>
        <input
          id="post-title"
          className="form-input"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          maxLength={200}
          placeholder="Tóm tắt hành trình của bạn..."
        />
      </div>
      <div className="form-group">
        <label htmlFor="post-destination">Điểm đến (tuỳ chọn)</label>
        <select
          id="post-destination"
          className="form-input"
          value={destinationId}
          onChange={(e) => setDestinationId(e.target.value)}
        >
          <option value="">— Chọn điểm đến —</option>
          {destinations.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
      </div>
      <div className="form-group">
        <label htmlFor="post-content">Nội dung *</label>
        <textarea
          id="post-content"
          className="form-input"
          rows={6}
          value={content}
          onChange={(e) => setContent(e.target.value)}
          required
          placeholder="Kể về chuyến đi của bạn, cảm nhận, mẹo hay..."
        />
      </div>
      <div className="form-group">
        <label htmlFor="post-images">Đường dẫn ảnh (mỗi dòng một đường dẫn, tối đa 5 ảnh)</label>
        <textarea
          id="post-images"
          className="form-input"
          rows={3}
          value={imageUrls}
          onChange={(e) => setImageUrls(e.target.value)}
          placeholder="https://example.com/anh1.jpg"
        />
      </div>
      <button type="submit" className="primary-btn" disabled={loading}>
        {loading ? 'Đang đăng…' : 'Đăng bài'}
      </button>
    </form>
  )
}

// ─── TravelFeedPage ──────────────────────────────────────────────────────────

export function TravelFeedPage() {
  const { user: currentUser } = useAuth()
  const [posts, setPosts] = useState([])
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [sort, setSort] = useState('-created_at')
  const [destinationFilter, setDestinationFilter] = useState('')
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showForm, setShowForm] = useState(false)

  useEffect(() => {
    getDestinations().then((d) => setDestinations(d.results || d)).catch(() => {})
  }, [])

  const load = useCallback((p = 1, s = sort, dest = destinationFilter) => {
    setLoading(true)
    const params = { page: p, sort: s }
    if (dest) params.destination_id = dest
    getTravelPosts(params)
      .then((data) => {
        setPosts(data.results)
        setTotalPages(data.total_pages || 1)
        setPage(p)
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [sort, destinationFilter])

  useEffect(() => { load(1, sort, destinationFilter) }, [sort, destinationFilter]) // eslint-disable-line

  const handleLike = async (id) => {
    if (!currentUser) { toast('Vui lòng đăng nhập để thích bài.', true); return }
    try {
      const { likes_count, is_liked } = await likeTravelPost(id)
      setPosts((prev) => prev.map((p) => p.id === id ? { ...p, likes_count, is_liked } : p))
    } catch (err) {
      toast(err.message, true)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm('Xoá bài viết này?')) return
    try {
      await deleteTravelPost(id)
      setPosts((prev) => prev.filter((p) => p.id !== id))
      toast('Đã xoá bài viết.')
    } catch (err) {
      toast(err.message, true)
    }
  }

  const handleCreated = (newPost) => {
    setShowForm(false)
    setPosts((prev) => [{ ...newPost, is_liked: false }, ...prev])
  }

  return (
    <section className="recommend" style={{ maxWidth: 860, margin: '0 auto', padding: '32px 20px 64px' }}>
      <div className="section-head" style={{ marginBottom: 28 }}>
        <span className="eyebrow dark">Cộng đồng</span>
        <h1>Chia sẻ trải nghiệm du lịch</h1>
        <p>Đọc câu chuyện từ những người đã trải qua — hoặc kể chuyến đi của bạn.</p>
      </div>

      {/* Controls */}
      <div className="travel-feed-controls">
        <select
          id="feed-sort"
          className="form-input"
          style={{ maxWidth: 220 }}
          value={sort}
          onChange={(e) => { setSort(e.target.value); load(1, e.target.value, destinationFilter) }}
        >
          <option value="-created_at">Mới nhất</option>
          <option value="created_at">Cũ nhất</option>
          <option value="-likes_count">Nhiều lượt thích nhất</option>
        </select>
        <select
          id="feed-dest"
          className="form-input"
          style={{ maxWidth: 220 }}
          value={destinationFilter}
          onChange={(e) => { setDestinationFilter(e.target.value); load(1, sort, e.target.value) }}
        >
          <option value="">Tất cả điểm đến</option>
          {destinations.map((d) => (
            <option key={d.id} value={d.id}>{d.name}</option>
          ))}
        </select>
        {currentUser && (
          <button
            type="button"
            className="primary-btn"
            onClick={() => setShowForm((v) => !v)}
          >
            {showForm ? '✕ Đóng form' : '+ Đăng bài'}
          </button>
        )}
        {!currentUser && (
          <Link className="primary-btn" to="/dang-nhap">Đăng nhập để đăng bài</Link>
        )}
      </div>

      {showForm && (
        <CreatePostForm destinations={destinations} onCreated={handleCreated} />
      )}

      {error && <p className="form-error">{error}</p>}
      {loading && (
        <div className="travel-post-grid">
          {[1, 2, 3].map((i) => <div key={i} className="skeleton-card" style={{ height: 280, borderRadius: 20 }} />)}
        </div>
      )}
      {!loading && posts.length === 0 && (
        <p style={{ color: '#9cc4d8', textAlign: 'center', marginTop: 48 }}>Chưa có bài viết nào. Hãy là người đầu tiên chia sẻ!</p>
      )}
      {!loading && posts.length > 0 && (
        <div className="travel-post-grid">
          {posts.map((p) => (
            <PostCard
              key={p.id}
              post={p}
              currentUser={currentUser}
              onLike={handleLike}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination-row">
          <button
            type="button"
            className="secondary-btn"
            disabled={page <= 1}
            onClick={() => load(page - 1)}
          >← Trước</button>
          <span style={{ color: '#9cc4d8' }}>Trang {page} / {totalPages}</span>
          <button
            type="button"
            className="secondary-btn"
            disabled={page >= totalPages}
            onClick={() => load(page + 1)}
          >Sau →</button>
        </div>
      )}
    </section>
  )
}

// ─── TravelPostDetailPage ────────────────────────────────────────────────────

export function TravelPostDetailPage() {
  const { user: currentUser } = useAuth()
  const { id } = useParams()
  const navigate = useNavigate()
  const [post, setPost] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getTravelPost(id)
      .then(setPost)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [id])

  const handleLike = async () => {
    if (!currentUser) { toast('Vui lòng đăng nhập.', true); return }
    try {
      const { likes_count, is_liked } = await likeTravelPost(id)
      setPost((p) => ({ ...p, likes_count, is_liked }))
    } catch (err) { toast(err.message, true) }
  }

  const handleDelete = async () => {
    if (!window.confirm('Xoá bài viết này?')) return
    try {
      await deleteTravelPost(id)
      toast('Đã xoá bài viết.')
      navigate('/cong-dong')
    } catch (err) { toast(err.message, true) }
  }

  if (loading) return <section style={{ padding: 48, textAlign: 'center', color: '#9cc4d8' }}>Đang tải…</section>
  if (error) return <section style={{ padding: 48, textAlign: 'center' }}><p className="form-error">{error}</p></section>
  if (!post) return null

  const canDelete = currentUser && (currentUser.id === post.user || currentUser.is_staff)

  return (
    <section style={{ maxWidth: 760, margin: '0 auto', padding: '32px 20px 80px' }}>
      <Link to="/cong-dong" className="secondary-btn" style={{ display: 'inline-block', marginBottom: 24 }}>← Quay lại</Link>

      {post.images?.[0] && (
        <div style={{ borderRadius: 20, overflow: 'hidden', marginBottom: 24, maxHeight: 400 }}>
          <img
            src={post.images[0]}
            alt={post.title}
            style={{ width: '100%', height: 400, objectFit: 'cover', display: 'block' }}
          />
        </div>
      )}

      <div className="mini-card">
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
          {post.destination_name && <span className="eyebrow dark">{post.destination_name}</span>}
          <span style={{ color: '#9cc4d8', fontSize: '0.85rem', alignSelf: 'center' }}>
            {timeAgo(post.created_at)} · ✍ {post.user_name}{post.user_is_demo && <span className="demo-badge">Minh họa</span>}
          </span>
        </div>

        <h1 style={{ margin: '0 0 20px', color: '#f3fbff', fontSize: 'clamp(1.6rem, 3vw, 2.2rem)' }}>{post.title}</h1>

        <p style={{ color: '#d0e9f8', lineHeight: 1.8, whiteSpace: 'pre-wrap', marginBottom: 28 }}>{post.content}</p>

        {/* Extra images */}
        {post.images?.length > 1 && (
          <div className="travel-post-gallery">
            {post.images.slice(1).map((url, i) => (
              <img key={i} src={url} alt={`ảnh ${i + 2}`} className="gallery-thumb" />
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginTop: 24, alignItems: 'center' }}>
          <button
            type="button"
            className={`like-btn ${post.is_liked ? 'liked' : ''}`}
            onClick={handleLike}
          >
            {post.is_liked ? '❤️' : '🤍'} {post.likes_count} lượt thích
          </button>
          {canDelete && (
            <button type="button" className="danger-btn" onClick={handleDelete}>
              Xoá bài
            </button>
          )}
        </div>
      </div>
    </section>
  )
}

import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api'

const notify = (message, error = false) => window.dispatchEvent(new CustomEvent('toast', { detail: { message, error } }))

function AuthShell({ title, children }) {
  return <section className="auth-page auth-page--split">
    <div className="auth-visual" role="img" aria-label="Phong cảnh núi non Việt Nam"><div><span className="section-kicker">Mỗi chuyến đi, một câu chuyện</span><h2>Việt Nam đang chờ bạn khám phá.</h2><p>Gợi ý hành trình, điểm đến và nơi nghỉ phù hợp với cách bạn muốn đi.</p></div></div>
    <div className="auth-card auth-card--form"><span className="eyebrow dark">Du lịch thông minh</span><h1>{title}</h1>{children}</div>
  </section>
}

export function PasswordField({ id, label, value, onChange, autoComplete = 'new-password', required = true }) {
  const [visible, setVisible] = useState(false)
  return <div className="auth-password-field">
    <label htmlFor={id}>{label}</label>
    <div className="auth-password-control">
      <input id={id} required={required} minLength={autoComplete === 'current-password' || !required ? undefined : 8} type={visible ? 'text' : 'password'} autoComplete={autoComplete} value={value} onChange={(event) => onChange(event.target.value)} />
      <button type="button" className="auth-password-toggle" onClick={() => setVisible(!visible)} aria-label={visible ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}>{visible ? 'Ẩn' : 'Hiện'}</button>
    </div>
  </div>
}

export function PasswordHint({ password }) {
  const level = !password ? '' : password.length < 8 || /^\d+$/.test(password) ? 'Yếu' : password.length >= 12 && /[A-Za-z]/.test(password) && /\d/.test(password) && /[^A-Za-z\d]/.test(password) ? 'Mạnh' : 'Trung bình'
  return <p className="auth-password-hint">Ít nhất 8 ký tự, không chỉ gồm số và tránh mật khẩu phổ biến.{level && <strong> Độ mạnh: {level}.</strong>}</p>
}

export function LoginPage({ onLogin }) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [form, setForm] = useState({ username: '', password: '' })
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setMessage('')
    try {
      const data = await api('/api/auth/login/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      const requestedNext = searchParams.get('next')
      const next = requestedNext?.startsWith('/') && !requestedNext.startsWith('//')
        ? requestedNext : (data.user?.is_staff ? '/quan-tri' : '/ho-so')
      onLogin(data.user)
      navigate(next, { replace: true })
      notify('Đăng nhập thành công.')
    } catch (err) {
      const text = err.message || 'Tên đăng nhập hoặc mật khẩu không đúng.'
      setMessage(text); notify(text, true)
    } finally { setLoading(false) }
  }
  return <AuthShell title="Chào mừng trở lại">
    <p className="auth-intro">Đăng nhập để tiếp tục lên kế hoạch cho hành trình của bạn.</p>
    {searchParams.get('reset') === 'success' && <p className="admin-message" role="status">Mật khẩu đã được cập nhật. Vui lòng đăng nhập.</p>}
    <form className="admin-form" onSubmit={submit}>
      <label>Tên đăng nhập<input required autoComplete="username" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label>
      <PasswordField id="login-password" label="Mật khẩu" autoComplete="current-password" value={form.password} onChange={(password) => setForm({ ...form, password })} />
      <button className="primary-btn" disabled={loading}>{loading ? 'Đang xử lý…' : 'Đăng nhập'}</button>
    </form>
    {message && <p className="form-error" role="alert">{message}</p>}
    <p className="auth-help"><Link to="/quen-mat-khau">Quên mật khẩu? Nhận liên kết đặt lại qua email.</Link></p>
    <p className="auth-switch">Chưa có tài khoản? <Link to="/dang-ky">Đăng ký</Link></p>
  </AuthShell>
}

export function RegisterPage({ onLogin }) {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [form, setForm] = useState({ username: '', email: '', password: '', password_confirm: '' })
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setMessage('')
    if (form.password !== form.password_confirm) { setMessage('Hai mật khẩu chưa khớp.'); return }
    setLoading(true)
    try {
      const data = await api('/api/auth/register/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      const requestedNext = searchParams.get('next')
      const next = requestedNext?.startsWith('/') && !requestedNext.startsWith('//') ? requestedNext : '/ho-so'
      onLogin(data)
      navigate(next, { replace: true })
      notify('Đăng ký thành công.')
    } catch (err) {
      const text = err.message || 'Đăng ký chưa thành công. Vui lòng thử lại.'
      setMessage(text); notify(text, true)
    } finally { setLoading(false) }
  }
  return <AuthShell title="Bắt đầu hành trình">
    <p className="auth-intro">Tạo tài khoản để lưu sở thích và nhận gợi ý dành riêng cho bạn.</p>
    <form className="admin-form" onSubmit={submit}>
      <label>Tên đăng nhập<input required autoComplete="username" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} /></label>
      <label>Email<input required type="email" autoComplete="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })} /></label>
      <PasswordField id="register-password" label="Mật khẩu" value={form.password} onChange={(password) => setForm({ ...form, password })} />
      <PasswordHint password={form.password} />
      <PasswordField id="register-confirm" label="Nhập lại mật khẩu" value={form.password_confirm} onChange={(password_confirm) => setForm({ ...form, password_confirm })} />
      <button className="primary-btn" disabled={loading}>{loading ? 'Đang xử lý…' : 'Tạo tài khoản'}</button>
    </form>
    {message && <p className="form-error" role="alert">{message}</p>}
    <p className="auth-switch">Đã có tài khoản? <Link to="/dang-nhap">Đăng nhập</Link></p>
  </AuthShell>
}

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError(''); setMessage('')
    try {
      const result = await api('/api/auth/password-reset/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) })
      setMessage(result.message || 'Nếu email có tài khoản, hướng dẫn đặt lại mật khẩu đã được gửi.')
    } catch (err) { setError(err.message || 'Chưa gửi được email. Vui lòng thử lại.') }
    finally { setLoading(false) }
  }
  return <AuthShell title="Quên mật khẩu">
    <p className="auth-intro">Nhập email tài khoản để nhận liên kết đặt lại mật khẩu.</p>
    <form className="admin-form" onSubmit={submit}><label>Email<input required type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} /></label><button className="primary-btn" disabled={loading}>{loading ? 'Đang gửi…' : 'Gửi liên kết'}</button></form>
    {message && <p className="admin-message" role="status">{message}</p>}{error && <p className="form-error" role="alert">{error}</p>}
    <p className="auth-switch"><Link to="/dang-nhap">Quay lại đăng nhập</Link></p>
  </AuthShell>
}

export function ResetPasswordPage() {
  const navigate = useNavigate()
  const [query] = useSearchParams()
  const uid = query.get('uid') || ''
  const token = query.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState('')
  const [expired, setExpired] = useState(!uid || !token)
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setError('')
    if (password !== confirmation) { setError('Hai mật khẩu chưa khớp.'); return }
    setLoading(true)
    try {
      await api('/api/auth/password-reset/confirm/', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ uid, token, password, password_confirm: confirmation }) })
      navigate('/dang-nhap?reset=success', { replace: true })
    } catch (err) {
      setError(err.message || 'Không thể đặt lại mật khẩu.')
      if (err.code === 'invalid_or_expired_token') setExpired(true)
    } finally { setLoading(false) }
  }
  return <AuthShell title="Đặt lại mật khẩu">
    {expired ? <>
      <p className="form-error" role="alert">{error || 'Liên kết đặt lại mật khẩu đã hết hạn hoặc đã được sử dụng.'}</p>
      <Link className="primary-btn auth-resend-link" to="/quen-mat-khau">Gửi lại liên kết</Link>
    </> : <>
      <p className="auth-intro">Tạo mật khẩu mới cho tài khoản của bạn.</p>
      <form className="admin-form" onSubmit={submit}>
        <PasswordField id="reset-password" label="Mật khẩu mới" value={password} onChange={setPassword} />
        <PasswordHint password={password} />
        <PasswordField id="reset-confirm" label="Nhập lại mật khẩu" value={confirmation} onChange={setConfirmation} />
        <button className="primary-btn" disabled={loading}>{loading ? 'Đang cập nhật…' : 'Lưu mật khẩu mới'}</button>
      </form>
      {error && <p className="form-error" role="alert">{error}</p>}
    </>}
  </AuthShell>
}

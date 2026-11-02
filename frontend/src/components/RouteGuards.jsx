import { Link, Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../auth'

export function safeInternalPath(path) {
  return typeof path === 'string' && path.startsWith('/') && !path.startsWith('//') ? path : null
}

export function AuthLoading({ error, retry }) {
  return <section className="auth-route-wait" aria-live="polite" aria-busy="true">
    <span className="auth-route-spinner" aria-hidden="true" />
    {error ? <><strong>Không kết nối được máy chủ</strong><p>{error}</p><button className="travel-button travel-button--outline" type="button" onClick={retry}>Thử lại</button></> : <span>Đang kiểm tra phiên đăng nhập…</span>}
  </section>
}

function LoginRedirect({ location }) {
  const requestedPath = `${location.pathname}${location.search}${location.hash}`
  return <Navigate to={`/dang-nhap?next=${encodeURIComponent(requestedPath)}`} replace />
}

export function RequireAuth({ children }) {
  const location = useLocation()
  const { status, authError, retryAuth } = useAuth()
  if (status === 'loading') return <AuthLoading error={authError} retry={retryAuth} />
  if (status === 'anonymous') return <LoginRedirect location={location} />
  return children
}

export function RequireStaff({ children }) {
  const location = useLocation()
  const { status, user, authError, retryAuth } = useAuth()
  if (status === 'loading') return <AuthLoading error={authError} retry={retryAuth} />
  if (status === 'anonymous') return <LoginRedirect location={location} />
  if (!user?.is_staff && !user?.is_superuser) return <section className="route-access-denied" role="alert">
    <div><span className="section-kicker">Khu vực quản trị</span><h1>Bạn không có quyền truy cập khu vực này</h1><p>Tài khoản hiện tại không có quyền quản trị.</p><Link className="travel-button travel-button--primary" to="/">Về trang chủ</Link></div>
  </section>
  return children
}

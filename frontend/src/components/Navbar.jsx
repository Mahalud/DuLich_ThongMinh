import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { Menu, X } from 'lucide-react'
import { useAuth } from '../auth'
import { useChatConnection } from './ChatConnection'

export default function Navbar() {
  const location = useLocation()
  const { user, status, authError, retryAuth, logout: onLogout } = useAuth()
  const { unreadCount } = useChatConnection()
  const [scrolled, setScrolled] = useState(window.scrollY > 24)
  const [menuOpen, setMenuOpen] = useState(false)
  const atHome = location.pathname === '/'
  const solid = !atHome || scrolled

  useEffect(() => {
    const update = () => setScrolled(window.scrollY > 24)
    window.addEventListener('scroll', update, { passive: true })
    return () => window.removeEventListener('scroll', update)
  }, [])

  useEffect(() => setMenuOpen(false), [location.pathname])

  const navLinkClass = ({ isActive }) => `nav-link ${isActive ? 'is-active' : ''}`
  const authControl = status === 'loading'
    ? authError
      ? <button type="button" className="travel-button travel-button--outline" onClick={retryAuth}>Không kết nối được máy chủ · Thử lại</button>
      : <span className="travel-button travel-button--outline" aria-live="polite">Đang kiểm tra phiên…</span>
    : status === 'authenticated'
      ? <button type="button" className="travel-button travel-button--outline" onClick={onLogout}>Đăng xuất</button>
      : <Link className="travel-button travel-button--primary" to="/dang-nhap">Đăng nhập</Link>
  return <header className={`topbar travel-navbar ${solid ? 'is-solid' : 'is-over-hero'}`}>
    <div className="navbar-inner">
      <Link className="brand" to="/" aria-label="Du lịch thông minh, về trang chủ"><span className="brand-mark"><img src="/brand/divietnam-logo.png" alt="" /></span><span>Đi Việt Nam</span></Link>
      <button className="mobile-menu-toggle" type="button" aria-label={menuOpen ? 'Đóng menu' : 'Mở menu'} aria-expanded={menuOpen} onClick={() => setMenuOpen((open) => !open)}>{menuOpen ? <X /> : <Menu />}</button>
      <nav className={`main-nav ${menuOpen ? 'is-open' : ''}`} aria-label="Điều hướng chính">
        <NavLink className={navLinkClass} to="/" end>Trang chủ</NavLink>
        <NavLink className={navLinkClass} to="/goi-y">Gợi ý</NavLink>
        <NavLink className={navLinkClass} to="/tro-ly">Trợ lý</NavLink>
        <NavLink className={navLinkClass} to="/tours">Tour</NavLink>
        <NavLink className={navLinkClass} to="/cong-dong">Cộng đồng</NavLink>
        <NavLink className={navLinkClass} to="/gioi-thieu">Giới thiệu</NavLink>
        <NavLink className={navLinkClass} to="/ho-so">Hồ sơ</NavLink>
        {status === 'authenticated' && (user?.is_staff || user?.is_superuser) && <NavLink className={navLinkClass} to="/quan-tri">Quản trị{unreadCount > 0 && <span className="navbar-unread" aria-label={`${unreadCount} tin nhắn chưa đọc`}>{unreadCount > 99 ? '99+' : unreadCount}</span>}</NavLink>}
        <NavLink className={navLinkClass} to="/ke-hoach">Kế hoạch</NavLink>
        <div className="mobile-auth-action">{authControl}</div>
      </nav>
      <div className="header-actions">{authControl}</div>
    </div>
  </header>
}

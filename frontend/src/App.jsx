import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import { api, getCurrentUser } from './api'
import { AuthContext, useAuth } from './auth'
import Footer from './components/Footer'
import Navbar from './components/Navbar'
import HomePage from './pages/HomePage'
import AboutPage from './pages/AboutPage'
import RecommendationsPage from './pages/RecommendationsPage'
import DestinationDetailPage from './pages/DestinationDetailPage'
import AccommodationDetailPage from './pages/AccommodationDetailPage'
import BookingPage from './pages/BookingPage'
import ProfilePage from './pages/ProfilePage'
import { ForgotPasswordPage, LoginPage, RegisterPage, ResetPasswordPage } from './pages/AuthPages'
import {
  AdminDashboardPage,
  AdminDestinationsPage,
  AdminAccommodationsPage,
  AdminRoomTypesPage,
  AdminAmenitiesPage,
  AdminBookingsPage,
  AdminToursPage,
  AdminTourBookingsPage,
  AdminStatisticsPage,
  AdminChatPage,
} from './pages/AdminPages'
import AdminSitePagePage from './pages/AdminSitePagePage'
import { PaymentReturnPage, ReviewsPage, SimulatedPaymentPage, WeatherPage } from './pages/UtilityPages'
import ChatPage from './pages/ChatPage'
import TravelAssistantPage from './pages/TravelAssistantPage'
import { TourBookingPage, TourDetailPage, ToursPage } from './pages/ToursPages'
import { TravelFeedPage, TravelPostDetailPage } from './pages/TravelFeedPages'
import ChatWidget from './components/ChatWidget'
import { ChatConnectionProvider } from './components/ChatConnection'
import RouteErrorBoundary from './components/RouteErrorBoundary'
import { AuthLoading, RequireAuth, RequireStaff, safeInternalPath } from './components/RouteGuards'
import { OriginContext } from './origin'

function readSavedOrigin() {
  try {
    const saved = JSON.parse(localStorage.getItem('travel-origin') || 'null')
    if (saved && saved.name && Number.isFinite(Number(saved.latitude)) && Number.isFinite(Number(saved.longitude))) {
      return { name: saved.name, latitude: Number(saved.latitude), longitude: Number(saved.longitude) }
    }
  } catch {}
  return null
}

function Toast() {
  const [toast, setToast] = useState(null)
  useEffect(() => {
    const show = (event) => {
      setToast(event.detail)
      window.setTimeout(() => setToast(null), 3500)
    }
    window.addEventListener('toast', show)
    return () => window.removeEventListener('toast', show)
  }, [])
  return toast && <div className={`toast ${toast.error ? 'toast-error' : ''}`} role="status">{toast.message}</div>
}

function AuthenticationEntry({ children }) {
  const location = useLocation()
  const { user, status, authError, retryAuth } = useAuth()
  const allowPageLoginRedirectRef = useRef(status === 'anonymous')
  const requestedNext = new URLSearchParams(location.search).get('next')
  const next = safeInternalPath(requestedNext) || '/'
  useEffect(() => {
    if (status === 'anonymous') allowPageLoginRedirectRef.current = true
  }, [status])
  if (status === 'loading') return <AuthLoading error={authError} retry={retryAuth} />
  if (status === 'authenticated' && !allowPageLoginRedirectRef.current) return <Navigate to={next} replace />
  return children
}

function PageRoutes() {
  const location = useLocation()
  const { user, setUser } = useAuth()
  return <div key={location.pathname} className="page-transition"><RouteErrorBoundary key={location.key || `${location.pathname}${location.search}`}><Routes>
    <Route path="/" element={<HomePage />} />
    <Route path="/gioi-thieu" element={<AboutPage />} />
    <Route path="/goi-y" element={<RecommendationsPage />} />
    <Route path="/tro-ly" element={<TravelAssistantPage />} />
    <Route path="/tours" element={<ToursPage />} />
    <Route path="/tours/:id" element={<TourDetailPage />} />
    <Route path="/tours/:id/dat" element={<RequireAuth><TourBookingPage /></RequireAuth>} />
    <Route path="/diem-den/:id" element={<DestinationDetailPage />} />
    <Route path="/cho-o/:id" element={<AccommodationDetailPage />} />
    <Route path="/dat-phong/:roomTypeId" element={<RequireAuth><BookingPage /></RequireAuth>} />
    <Route path="/ho-so" element={<RequireAuth><ProfilePage user={user} /></RequireAuth>} />
    <Route path="/dang-nhap" element={<AuthenticationEntry><LoginPage onLogin={setUser} /></AuthenticationEntry>} />
    <Route path="/dang-ky" element={<AuthenticationEntry><RegisterPage onLogin={setUser} /></AuthenticationEntry>} />
    <Route path="/quen-mat-khau" element={<ForgotPasswordPage />} />
    <Route path="/dat-lai-mat-khau" element={<ResetPasswordPage />} />
    <Route path="/thoi-tiet" element={<WeatherPage />} />
    <Route path="/chat" element={<RequireAuth><ChatPage /></RequireAuth>} />
    <Route path="/danh-gia" element={<ReviewsPage />} />
    <Route path="/cong-dong" element={<RequireAuth><TravelFeedPage /></RequireAuth>} />
    <Route path="/cong-dong/:id" element={<RequireAuth><TravelPostDetailPage /></RequireAuth>} />
    <Route path="/payment-return" element={<RequireAuth><PaymentReturnPage /></RequireAuth>} />
    <Route path="/thanh-toan-mo-phong" element={<RequireAuth><SimulatedPaymentPage /></RequireAuth>} />
    <Route path="/quan-tri" element={<RequireStaff><AdminDashboardPage /></RequireStaff>} />
    <Route path="/quan-tri/diem-den" element={<RequireStaff><AdminDestinationsPage /></RequireStaff>} />
    <Route path="/quan-tri/cho-o" element={<RequireStaff><AdminAccommodationsPage /></RequireStaff>} />
    <Route path="/quan-tri/phong" element={<RequireStaff><AdminRoomTypesPage /></RequireStaff>} />
    <Route path="/quan-tri/tien-ich" element={<RequireStaff><AdminAmenitiesPage /></RequireStaff>} />
    <Route path="/quan-tri/dat-phong" element={<RequireStaff><AdminBookingsPage /></RequireStaff>} />
    <Route path="/quan-tri/tours" element={<RequireStaff><AdminToursPage /></RequireStaff>} />
    <Route path="/quan-tri/dat-tour" element={<RequireStaff><AdminTourBookingsPage /></RequireStaff>} />
    <Route path="/quan-tri/chat" element={<RequireStaff><AdminChatPage user={user} /></RequireStaff>} />
    <Route path="/quan-tri/thong-ke" element={<RequireStaff><AdminStatisticsPage /></RequireStaff>} />
    <Route path="/quan-tri/gioi-thieu" element={<RequireStaff><AdminSitePagePage /></RequireStaff>} />
    <Route path="/quan-tri/*" element={<RequireStaff><Navigate to="/quan-tri" replace /></RequireStaff>} />
    <Route path="*" element={<Navigate to="/" replace />} />
  </Routes></RouteErrorBoundary></div>
}

function BackToTop() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const update = () => setVisible(window.scrollY > 520)
    window.addEventListener('scroll', update, { passive: true })
    update()
    return () => window.removeEventListener('scroll', update)
  }, [])
  return visible ? <button className="back-to-top" type="button" aria-label="Lên đầu trang" onClick={() => window.scrollTo({ top: 0, behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth' })}>↑ <span>Lên đầu trang</span></button> : null
}

export default function App({ Router = BrowserRouter, routerProps = {} } = {}) {
  const [user, setUserState] = useState(null)
  const [status, setStatus] = useState('loading')
  const [authError, setAuthError] = useState('')
  const [authAttempt, setAuthAttempt] = useState(0)
  const authRequestRef = useRef(null)
  const authGenerationRef = useRef(0)
  const [originLocation, setOriginLocation] = useState(readSavedOrigin)
  useEffect(() => {
    if (originLocation) localStorage.setItem('travel-origin', JSON.stringify(originLocation))
    else localStorage.removeItem('travel-origin')
  }, [originLocation])
  useEffect(() => {
    fetch('http://localhost:8000/api/auth/csrf/', { credentials: 'include' }).catch(() => {})
    const generation = ++authGenerationRef.current
    if (!authRequestRef.current) authRequestRef.current = getCurrentUser()
    let active = true
    authRequestRef.current
      .then((data) => {
        if (!active || authGenerationRef.current !== generation) return
        const currentUser = data?.user
        if (!currentUser) {
          setAuthError('Phản hồi kiểm tra phiên không hợp lệ. Vui lòng thử lại.')
          setStatus('loading')
          return
        }
        setUserState(currentUser)
        setStatus('authenticated')
        setAuthError('')
      })
      .catch((error) => {
        if (!active || authGenerationRef.current !== generation) return
        if (error.status === 401) {
          setUserState(null)
          setStatus('anonymous')
          setAuthError('')
        } else {
          setAuthError('Máy chủ chưa phản hồi. Kiểm tra kết nối rồi thử lại.')
          setStatus('loading')
        }
      })
    return () => { active = false }
  }, [authAttempt])

  const setUser = useCallback((nextUser) => {
    const resolvedUser = nextUser?.user || nextUser || null
    authGenerationRef.current += 1
    authRequestRef.current = null
    setUserState(resolvedUser)
    setStatus(resolvedUser ? 'authenticated' : 'anonymous')
    setAuthError('')
  }, [])

  const retryAuth = useCallback(() => {
    authGenerationRef.current += 1
    authRequestRef.current = null
    setAuthError('')
    setStatus('loading')
    setAuthAttempt((attempt) => attempt + 1)
  }, [])

  const logout = async () => {
    try {
      await api('/api/auth/logout/', { method: 'POST' })
      setUser(null)
    } catch (error) {
      window.dispatchEvent(new CustomEvent('toast', { detail: { message: error.message || 'Chưa đăng xuất được. Vui lòng thử lại.', error: true } }))
    }
  }
  const authState = { user, setUser, status, authError, retryAuth, logout }

  return (
    <Router {...routerProps}>
      <AuthContext.Provider value={authState}>
       <OriginContext.Provider value={{ originLocation, setOriginLocation }}>
        <ChatConnectionProvider user={user} authStatus={status}>
          <div className="travel-app">
            <Navbar />
            <main>
              <PageRoutes />
            </main>
            <Footer />
            <ChatWidget user={user} authStatus={status} authError={authError} onRetryAuth={retryAuth} />
            <Toast />
            <BackToTop />
          </div>
        </ChatConnectionProvider>
       </OriginContext.Provider>
      </AuthContext.Provider>
    </Router>
  )
}

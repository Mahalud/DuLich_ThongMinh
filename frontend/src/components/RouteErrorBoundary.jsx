import { Component } from 'react'
import { Link } from 'react-router-dom'

export default class RouteErrorBoundary extends Component {
  state = { error: null }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    const componentName = info?.componentStack?.trim().split('\n')[0]?.trim() || error?.name || 'Lỗi giao diện'
    console.error(`[RouteErrorBoundary] Lỗi khi dựng ${componentName}`, error, info?.componentStack || '')
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <section className="route-error-boundary" role="alert">
        <span className="section-kicker">Đã xảy ra sự cố</span>
        <h1>Trang gặp sự cố</h1>
        <p>Bạn có thể tải lại hoặc quay về trang chủ.</p>
        <div className="route-error-actions">
          <button className="travel-button travel-button--primary" type="button" onClick={() => window.location.reload()}>Tải lại</button>
          <Link className="travel-button travel-button--outline" to="/">Về trang chủ</Link>
        </div>
      </section>
    )
  }
}

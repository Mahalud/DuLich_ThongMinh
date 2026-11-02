import { useEffect, useState } from 'react'
import { api } from '../api'
import LoadingSkeleton from '../components/LoadingSkeleton'
import { ErrorNotice } from '../components/DesignSystem'
import SitePageView from '../components/SitePageView'

export default function AboutPage() {
  const [page, setPage] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([
      api('/api/pages/gioi-thieu/'),
      api('/api/public-stats/').catch(() => null),
    ]).then(([pageData, statsData]) => {
      if (!active) return
      setPage(pageData)
      setStats(statsData)
    }).catch((requestError) => {
      if (active) setError(requestError.message || 'Không tải được nội dung giới thiệu.')
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

  if (loading) return <section className="site-page page-shell"><LoadingSkeleton count={3} /></section>
  if (error) return <section className="site-page page-shell"><ErrorNotice>{error}</ErrorNotice></section>
  return <section className="site-page page-shell"><SitePageView page={page} stats={stats} /></section>
}

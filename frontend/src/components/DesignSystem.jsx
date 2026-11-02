import { useEffect, useRef, useState } from 'react'
import { MapPin, Star } from 'lucide-react'

export function ActionButton({ as: Component = 'button', variant = 'primary', className = '', children, ...props }) {
  return <Component className={`travel-button travel-button--${variant} ${className}`.trim()} {...props}>{children}</Component>
}

export function CategoryChip({ children, className = '' }) {
  return <span className={`travel-chip ${className}`.trim()}>{children}</span>
}

export function RatingStars({ rating }) {
  return <span className="travel-rating" aria-label={`Đánh giá ${rating || 0} trên 5`}><Star size={15} fill="currentColor" /> <strong>{Number(rating || 0).toFixed(1)}</strong></span>
}

export function PriceTag({ children, suffix = '' }) {
  return <span className="travel-price"><strong>{children}</strong>{suffix && <small>{suffix}</small>}</span>
}

export function TravelImage({ src, alt, className = '', aspectRatio = '4 / 3', width = 800, height = 600 }) {
  const [failed, setFailed] = useState(false)
  return <div className={`travel-image ${failed || !src ? 'travel-image--fallback' : ''} ${className}`.trim()} style={{ aspectRatio }}>
    {src && !failed
      ? <img src={src} alt={alt} loading="lazy" width={width} height={height} onError={() => setFailed(true)} />
      : <span className="travel-image-fallback" aria-label={alt}><MapPin size={30} /><span>{alt}</span></span>}
  </div>
}

export function SectionSkeleton({ count = 3, className = '' }) {
  return <div className={`travel-skeleton-grid ${className}`}>{Array.from({ length: count }, (_, index) => <div className="travel-skeleton" key={index} />)}</div>
}

export function EmptyState({ title, description }) {
  return <div className="travel-empty"><svg viewBox="0 0 120 88" role="img" aria-label="Minh họa phong cảnh" focusable="false"><path d="M5 76 38 29l19 25 18-17 40 39H5Z" /><circle cx="91" cy="19" r="11" /></svg><strong>{title}</strong><p>{description}</p></div>
}

export function ErrorNotice({ children }) {
  return <div className="travel-error" role="alert">{children}</div>
}

export function Reveal({ children, className = '', delay = 0 }) {
  const [visible, setVisible] = useState(false)
  const ref = useRef(null)
  useEffect(() => {
    const node = ref.current
    if (!node || visible) return
    if (!('IntersectionObserver' in window)) {
      setVisible(true)
      return
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setVisible(true)
        observer.disconnect()
      }
    }, { threshold: 0.12 })
    observer.observe(node)
    return () => observer.disconnect()
  }, [visible])
  return <div ref={ref} className={`reveal ${visible ? 'is-visible' : ''} ${className}`.trim()} style={{ '--reveal-delay': `${delay}ms` }}>{children}</div>
}

export function AnimatedCount({ value = 0, decimals = 0 }) {
  const [count, setCount] = useState(0)
  const ref = useRef(null)
  useEffect(() => {
    const node = ref.current
    if (!node) return
    if (!('IntersectionObserver' in window)) {
      setCount(value)
      return
    }
    let frame = 0
    const observer = new IntersectionObserver(([entry]) => {
      if (!entry.isIntersecting) return
      observer.disconnect()
      const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
      if (reduced || value <= 0) {
        setCount(value)
        return
      }
      const start = performance.now()
      const duration = 950
      const animate = (now) => {
        const progress = Math.min(1, (now - start) / duration)
        const scale = 10 ** decimals
        setCount(Math.round(value * scale * (1 - (1 - progress) ** 3)) / scale)
        if (progress < 1) frame = requestAnimationFrame(animate)
      }
      frame = requestAnimationFrame(animate)
    }, { threshold: 0.7 })
    observer.observe(node)
    return () => {
      observer.disconnect()
      cancelAnimationFrame(frame)
    }
  }, [value, decimals])
  return <span ref={ref}>{count.toLocaleString('vi-VN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}</span>
}

export default function LoadingSkeleton({ count = 3 }) {
  return <div className="destination-grid recommendation-skeleton-grid" aria-label="Đang tải điểm đến" aria-busy="true">{Array.from({ length: count }, (_, index) => <article className="recommendation-skeleton" key={index}><div className="recommendation-skeleton-image" /><div className="recommendation-skeleton-copy"><span /><span /><span /><span /></div></article>)}</div>
}

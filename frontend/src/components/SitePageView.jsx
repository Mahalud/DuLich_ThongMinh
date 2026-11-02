import { AnimatedCount, Reveal, TravelImage } from './DesignSystem'
import { PlainTextContent } from './PlainTextContent'

const STAT_ITEMS = [
  ['destination_count', 'Điểm đến'],
  ['tour_count', 'Tour'],
  ['accommodation_count', 'Chỗ ở'],
  ['travel_post_count', 'Bài chia sẻ'],
  ['average_rating', 'Điểm đánh giá trung bình / 5'],
]

function SectionContent({ section }) {
  if (section.layout === 'cards') {
    const cards = String(section.content || '').split(/\s*·\s*|\n+/).map((item) => item.trim()).filter(Boolean)
    return <div className="site-section-cards">{cards.map((card, index) => <article key={`${index}-${card}`}><PlainTextContent content={card} /></article>)}</div>
  }
  return <PlainTextContent content={section.content} />
}

export default function SitePageView({ page, stats, showStats = true }) {
  if (!page) return null
  const sections = Array.isArray(page.sections) ? page.sections : []
  return <div className="site-page-view">
    <header className="site-page-hero">
      <TravelImage className="site-page-cover" src={page.cover_image_url} alt={page.title} aspectRatio="16 / 7" width="1800" height="790" />
      <div className="site-page-cover-shade" />
      <div className="site-page-hero-copy"><span className="eyebrow">Đi Việt Nam</span><h1>{page.title}</h1><PlainTextContent content={page.intro} /></div>
    </header>

    {showStats && <Reveal className="site-page-stats">{STAT_ITEMS.map(([key, label]) => <article key={key}><strong><AnimatedCount value={Number(stats?.[key] || 0)} decimals={key === 'average_rating' ? 1 : 0} /></strong><span>{label}</span></article>)}</Reveal>}

    <div className="site-page-sections">{sections.map((section, index) => <Reveal key={section.id ?? `${section.order}-${section.title}`} delay={index * 45} className={`site-page-section site-page-section--${section.layout || 'text'}`}>
      {(section.layout === 'image_left' || section.layout === 'image_right') && section.image_url && <TravelImage className="site-page-section-image" src={section.image_url} alt={section.title} aspectRatio="4 / 3" width="900" height="675" />}
      <div className="site-page-section-copy"><span className="section-kicker">{String(index + 1).padStart(2, '0')}</span><h2>{section.title}</h2><SectionContent section={section} /></div>
    </Reveal>)}</div>
  </div>
}

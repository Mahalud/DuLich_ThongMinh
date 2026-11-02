import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowDown, ArrowRight, ChevronLeft, ChevronRight, CloudSun, Compass, MapPin, Route, Wallet } from 'lucide-react'
import { getAccommodations, getDestinations, getRecommendations, getTours, getTravelPosts, getWeather } from '../api'
import RecommendationForm, { defaultRecommendationForm } from '../components/RecommendationForm'
import { AnimatedCount, CategoryChip, EmptyState, ErrorNotice, PriceTag, RatingStars, Reveal, SectionSkeleton, TravelImage } from '../components/DesignSystem'

const QUICK_PREFERENCES = ['biển', 'núi', 'ẩm thực', 'văn hóa', 'nghỉ dưỡng', 'mạo hiểm']

function asList(data) {
  if (Array.isArray(data)) return data
  return Array.isArray(data?.results) ? data.results : []
}

function Hero({ destinations, weather, form, parallaxRef }) {
  const slides = destinations.filter((item) => item.image_url).slice(0, 7)
  const [slideIndex, setSlideIndex] = useState(0)
  const [failedSlides, setFailedSlides] = useState([])
  const previousIndex = (slideIndex - 1 + slides.length) % Math.max(slides.length, 1)
  const activeSlide = slides[slideIndex]
  const activeSlideKey = activeSlide?.id || activeSlide?.name

  useEffect(() => {
    if (slides.length < 2 || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    const timer = window.setInterval(() => setSlideIndex((index) => (index + 1) % slides.length), 5000)
    return () => window.clearInterval(timer)
  }, [slides.length])

  return <section className="home-hero" ref={parallaxRef}>
    <div className="hero-backdrop" aria-hidden="true">
      {slides.length > 0 && <>
        <img className="hero-background hero-background--previous" src={slides[previousIndex]?.image_url} alt="" width="1800" height="1200" loading="lazy" onError={(event) => { event.currentTarget.style.display = 'none' }} />
        <img key={activeSlideKey || slideIndex} className="hero-background hero-background--active" src={activeSlide?.image_url} alt="" width="1800" height="1200" loading="eager" fetchPriority="high" onError={() => setFailedSlides((items) => [...new Set([...items, activeSlideKey])])} />
        {failedSlides.includes(activeSlideKey) && <div className="hero-image-fallback"><Compass size={42} /><span>{activeSlide?.name}</span></div>}
      </>}
      {slides.length === 0 && <div className="hero-image-fallback"><Compass size={42} /><span>Việt Nam đang chờ bạn khám phá</span></div>}
    </div>
    <div className="hero-shade" />
    <div className="hero-content page-shell">
      <div className="hero-copy">
        <span className="hero-kicker"><Compass size={16} /> Hành trình mang dấu ấn của bạn</span>
        <h1>Đi để thấy Việt Nam <em>thật gần.</em></h1>
        <p>Chọn điều bạn yêu thích. Chúng tôi giúp bạn tìm điểm đến hợp ngân sách, thời tiết và khoảng cách.</p>
        {weather?.name && <div className="hero-weather"><CloudSun size={17} /><span>Đang khám phá thời tiết ở <strong>{weather.name}</strong>{weather.temperature !== undefined ? ` · ${weather.temperature}°C` : ''}</span></div>}
        <a className="hero-scroll-link" href="#diem-noi-bat">Khám phá Việt Nam <ArrowDown size={15} /></a>
      </div>
      <div className="hero-search-card">
        <div className="hero-search-heading"><span className="search-icon"><MapPin size={18} /></span><div><strong>Bạn muốn đi đâu?</strong><span>Lên kế hoạch theo cách của bạn</span></div></div>
        <RecommendationForm
          initialValues={form}
          quickChips={QUICK_PREFERENCES}
          submitLabel="Gợi ý cho tôi"
          onSubmit={(values) => { window.location.href = `/goi-y?${new URLSearchParams(values)}` }}
        />
      </div>
    </div>
    <div className="hero-slide-indicator" aria-label="Ảnh điểm đến">
      {slides.map((slide, index) => <button key={slide.id || slide.name} type="button" aria-label={`Hiện ảnh ${slide.name}`} aria-current={slideIndex === index ? 'true' : undefined} onClick={() => setSlideIndex(index)} />)}
    </div>
  </section>
}

function FeaturedDestination({ destination, delay }) {
  return <Reveal className="featured-destination-reveal" delay={delay}>
    <Link className="featured-destination" to={`/diem-den/${destination.id}`}>
      <TravelImage className="featured-destination-image" src={destination.image_url} alt={destination.name} aspectRatio="4 / 5" width="720" height="900" />
      <div className="featured-destination-shade" />
      <div className="featured-destination-info"><CategoryChip>{destination.category}</CategoryChip><h3>{destination.name}</h3><RatingStars rating={destination.rating} /></div>
    </Link>
  </Reveal>
}

function TourCard({ tour, fallbackImage, delay }) {
  const categoryLabels = { kham_pha: 'Khám phá thiên nhiên', van_hoa: 'Văn hóa - lịch sử', nghi_duong: 'Nghỉ dưỡng', mao_hiem: 'Mạo hiểm', am_thuc: 'Ẩm thực', ghep_doan: 'Tour ghép đoàn', rieng: 'Tour riêng' }
  return <Reveal className="home-tour-reveal" delay={delay}>
    <article className="home-tour-card">
      <Link to={`/tours/${tour.id}`} className="home-tour-media"><TravelImage src={tour.cover_image_url || fallbackImage} alt={tour.name} aspectRatio="16 / 10" width="960" height="600" /><span className="tour-days">{tour.duration_days} ngày</span></Link>
      <div className="home-tour-body"><span className="home-tour-category">{categoryLabels[tour.category] || tour.category}</span><h3><Link to={`/tours/${tour.id}`}>{tour.name}</Link></h3><p>{tour.description}</p><div className="home-tour-footer"><PriceTag suffix="/ khách">{Number(tour.price_adult || tour.price_per_person || 0).toLocaleString('vi-VN')} đ</PriceTag><Link className="round-arrow" to={`/tours/${tour.id}`} aria-label={`Xem tour ${tour.name}`}><ArrowRight size={18} /></Link></div></div>
    </article>
  </Reveal>
}

function CommunityCard({ post, delay }) {
  const image = post.images?.[0]
  return <Reveal className="community-reveal" delay={delay}><Link className="community-card" to={`/cong-dong/${post.id}`}>
    {image && <TravelImage src={image} alt={post.title} aspectRatio="16 / 10" width="800" height="500" />}
    <div className="community-card-copy"><span>{post.destination_name || 'Chia sẻ hành trình'}</span><h3>{post.title}</h3><p>{(post.content || '').slice(0, 120)}{post.content?.length > 120 ? '…' : ''}</p><strong>Đọc bài viết <ArrowRight size={15} /></strong></div>
  </Link></Reveal>
}

export default function HomePage() {
  const [destinations, setDestinations] = useState([])
  const [tours, setTours] = useState([])
  const [posts, setPosts] = useState([])
  const [stats, setStats] = useState({ destinations: 0, tours: 0, accommodations: 0, posts: 0 })
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [weather, setWeather] = useState(null)
  const form = useMemo(() => ({ ...defaultRecommendationForm }), [])
  const carouselRef = useRef(null)
  const heroRef = useRef(null)

  useEffect(() => {
    let active = true
    Promise.allSettled([getDestinations(), getTours(), getAccommodations(), getTravelPosts({ page: 1 })]).then((results) => {
      if (!active) return
      const [destinationResult, tourResult, accommodationResult, postResult] = results
      const destinationList = destinationResult.status === 'fulfilled' ? asList(destinationResult.value) : []
      const tourList = tourResult.status === 'fulfilled' ? asList(tourResult.value) : []
      const accommodationList = accommodationResult.status === 'fulfilled' ? asList(accommodationResult.value) : []
      const postData = (postResult.status === 'fulfilled' ? postResult.value : {}) || {}
      const postList = asList(postData)
      setDestinations(destinationList)
      setTours(tourList)
      setPosts(postList.slice(0, 3))
      setStats({
        destinations: destinationList.length,
        tours: tourList.length,
        accommodations: accommodationList.length,
        posts: Number(postData.count ?? postList.length),
      })
      if (results.every((result) => result.status === 'rejected')) setLoadError('Chưa thể tải dữ liệu. Vui lòng kiểm tra kết nối rồi thử lại.')
      setLoading(false)
    })

    getRecommendations(form).then((data) => {
      const destination = data.results?.[0]
      if (!destination) return
      if (active) setWeather({ name: destination.name })
      return getWeather(destination, form.travel_date).then((weatherData) => { if (active) setWeather({ ...weatherData, name: destination.name }) })
    }).catch(() => {})

    return () => { active = false }
  }, [form])

  useEffect(() => {
    const hero = heroRef.current
    if (!hero || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return undefined
    let frame = 0
    const update = () => {
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(() => hero.style.setProperty('--hero-parallax', `${Math.min(window.scrollY * 0.16, 90)}px`))
    }
    window.addEventListener('scroll', update, { passive: true })
    return () => { cancelAnimationFrame(frame); window.removeEventListener('scroll', update) }
  }, [])

  const featured = destinations.slice(0, 9)
  const featuredTours = tours.slice(0, 3)
  const featuredImage = featured[0]?.image_url

  const scrollCarousel = (direction) => carouselRef.current?.scrollBy({ left: direction * Math.max(280, carouselRef.current.clientWidth * 0.72), behavior: 'smooth' })

  return <div className="home-page">
    <Hero destinations={destinations} weather={weather} form={form} parallaxRef={heroRef} />

    <section className="stats-band page-shell" aria-label="Đi Việt Nam qua những con số">
      <Reveal className="stats-inner">
        {[['Điểm đến', stats.destinations], ['Tour trải nghiệm', stats.tours], ['Chỗ ở', stats.accommodations], ['Bài chia sẻ', stats.posts]].map(([label, value]) => <div className="stat-item" key={label}><strong><AnimatedCount value={value} /><span>+</span></strong><span>{label}</span></div>)}
      </Reveal>
    </section>

    <section className="home-section page-shell" id="diem-noi-bat">
      <Reveal><div className="home-section-heading"><div><span className="section-kicker">Chạm vào nơi bạn muốn đến</span><h2>Điểm đến nổi bật</h2><p>Những góc Việt Nam đáng để dành thêm một ngày.</p></div><div className="carousel-controls"><button type="button" onClick={() => scrollCarousel(-1)} aria-label="Cuộn điểm đến sang trái"><ChevronLeft /></button><button type="button" onClick={() => scrollCarousel(1)} aria-label="Cuộn điểm đến sang phải"><ChevronRight /></button></div></div></Reveal>
      {loading ? <SectionSkeleton count={4} className="destination-skeleton-grid" /> : loadError && !featured.length ? <ErrorNotice>{loadError}</ErrorNotice> : featured.length ? <div className="featured-destinations" ref={carouselRef}>{featured.map((destination, index) => <FeaturedDestination destination={destination} delay={index * 70} key={destination.id} />)}</div> : <EmptyState title="Chưa có điểm đến để giới thiệu" description="Khi có dữ liệu mới, những hành trình nổi bật sẽ xuất hiện tại đây." />}
      {loadError && featured.length > 0 && <ErrorNotice>{loadError}</ErrorNotice>}
    </section>

    <section className="home-section home-section--tinted">
      <div className="page-shell">
        <Reveal><div className="home-section-heading"><div><span className="section-kicker">Đi xa hơn cùng nhau</span><h2>Tour được yêu thích</h2><p>Hành trình được sắp xếp để bạn tận hưởng trọn vẹn từng vùng đất.</p></div><Link className="text-link" to="/tours">Xem tất cả tour <ArrowRight size={17} /></Link></div></Reveal>
        {loading ? <SectionSkeleton count={3} className="home-tour-grid" /> : featuredTours.length ? <div className="home-tour-grid">{featuredTours.map((tour, index) => <TourCard key={tour.id} tour={tour} fallbackImage={featuredImage} delay={index * 90} />)}</div> : <EmptyState title="Chưa có tour nào" description="Các hành trình mới sẽ sớm được cập nhật." />}
      </div>
    </section>

    <section className="home-section page-shell">
      <Reveal><div className="home-section-heading home-section-heading--center"><div><span className="section-kicker">Gợi ý có cơ sở</span><h2>Hành trình phù hợp bắt đầu từ 4 yếu tố</h2><p>Mỗi lựa chọn được cân nhắc theo những tiêu chí gần với nhu cầu thực tế của bạn.</p></div></div></Reveal>
      <div className="how-it-works">
        {[
          { icon: Compass, title: 'Sở thích', text: 'Tìm những điểm đến phù hợp với điều bạn muốn trải nghiệm.' },
          { icon: CloudSun, title: 'Thời tiết', text: 'Ưu tiên nơi có điều kiện thời tiết thuận lợi vào ngày đi.' },
          { icon: Wallet, title: 'Ngân sách', text: 'Cân đối chi phí dự kiến với mức chi bạn lựa chọn.' },
          { icon: Route, title: 'Khoảng cách', text: 'Xếp hạng điểm đến dựa trên vị trí xuất phát của bạn.' },
        ].map(({ icon: Icon, title, text }, index) => <Reveal className="how-step" delay={index * 100} key={title}><span className="how-icon"><Icon size={22} /></span><span className="how-step-number">0{index + 1}</span><h3>{title}</h3><p>{text}</p></Reveal>)}
      </div>
    </section>

    <section className="home-section home-section--community">
      <div className="page-shell">
        <Reveal><div className="home-section-heading"><div><span className="section-kicker">Câu chuyện từ những chuyến đi</span><h2>Cộng đồng chia sẻ</h2><p>Kinh nghiệm nhỏ, cảm hứng lớn cho hành trình tiếp theo.</p></div><Link className="text-link" to="/cong-dong">Đến cộng đồng <ArrowRight size={17} /></Link></div></Reveal>
        {loading ? <SectionSkeleton count={3} className="community-grid" /> : posts.length ? <div className="community-grid">{posts.map((post, index) => <CommunityCard key={post.id} post={post} delay={index * 90} />)}</div> : <EmptyState title="Cộng đồng đang chờ câu chuyện đầu tiên" description="Ghé thăm trang cộng đồng để chia sẻ trải nghiệm của bạn." />}
        <Link className="community-cta" to="/cong-dong">Chia sẻ chuyến đi của bạn <ArrowRight size={16} /></Link>
      </div>
    </section>
  </div>
}

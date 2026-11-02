import { Link } from 'react-router-dom'
import { Compass, ShieldCheck } from 'lucide-react'

export default function Footer() {
  return <footer className="site-footer">
    <div className="footer-inner">
      <div className="footer-brand-block">
        <Link className="brand footer-brand" to="/"><span className="brand-mark"><Compass size={21} /></span><span>Đi Việt Nam</span></Link>
        <p>Gợi ý hành trình gần với sở thích, ngân sách và thời tiết của bạn. Bắt đầu từ một điểm đến, mở ra nhiều trải nghiệm.</p>
      </div>
      <div className="footer-links-block"><strong>Khám phá</strong><nav aria-label="Liên kết chính ở chân trang"><Link to="/">Trang chủ</Link><Link to="/goi-y">Gợi ý điểm đến</Link><Link to="/tro-ly">Trợ lý du lịch</Link><Link to="/tours">Tour du lịch</Link><Link to="/cong-dong">Cộng đồng</Link><Link to="/gioi-thieu">Giới thiệu</Link></nav></div>
      <div className="footer-note"><ShieldCheck size={19} /><p>Thanh toán trên website hiện dùng môi trường sandbox để thử nghiệm.</p></div>
    </div>
    <div className="footer-bottom"><span>Đồ án chuyên ngành - Trường ĐH Tài nguyên và Môi trường TP.HCM</span><span>© {new Date().getFullYear()} Đi Việt Nam</span></div>
  </footer>
}

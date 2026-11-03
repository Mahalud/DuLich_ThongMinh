import { Link } from 'react-router-dom'
import { MessageCircle, ShieldCheck } from 'lucide-react'

export default function Footer() {
  return <footer className="site-footer">
    <div className="footer-inner">
      <div className="footer-brand-block">
        <Link className="brand footer-brand" to="/"><span className="brand-mark"><img src="/brand/divietnam-logo.png" alt="" /></span><span>Đi Việt Nam</span></Link>
        <p>Khám phá điểm đến và lên kế hoạch chuyến đi theo sở thích, ngân sách, thời tiết và vị trí xuất phát của bạn.</p>
        <span className="footer-project-tag">Đồ án chuyên ngành · Dữ liệu minh họa</span>
      </div>
      <div className="footer-links-block">
        <strong>Khám phá</strong>
        <nav aria-label="Liên kết khám phá ở chân trang"><Link to="/">Trang chủ</Link><Link to="/goi-y">Gợi ý điểm đến</Link><Link to="/tours">Tour du lịch</Link><Link to="/cong-dong">Cộng đồng</Link><Link to="/gioi-thieu">Giới thiệu</Link></nav>
      </div>
      <div className="footer-links-block">
        <strong>Hỗ trợ</strong>
        <nav aria-label="Liên kết hỗ trợ ở chân trang"><Link to="/tro-ly">Trợ lý du lịch</Link><Link to="/ho-so">Quản lý đặt chỗ</Link><Link to="/gioi-thieu">Cách hệ thống hoạt động</Link></nav>
        <Link className="footer-support-link" to="/tro-ly"><MessageCircle size={16} /> Hỏi trợ lý du lịch</Link>
      </div>
      <div className="footer-note"><ShieldCheck size={19} /><div><strong>Thanh toán thử nghiệm</strong><p>Các giao dịch trên website dùng môi trường sandbox hoặc mô phỏng, không phải thanh toán thật.</p></div></div>
    </div>
    <div className="footer-bottom"><span>Đồ án chuyên ngành · Trường Đại học Tài nguyên và Môi trường TP.HCM</span><span>Một số chỗ ở, tour, đánh giá và bài chia sẻ là dữ liệu minh họa.</span><span>© {new Date().getFullYear()} Đi Việt Nam</span></div>
  </footer>
}

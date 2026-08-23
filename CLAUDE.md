# Website Gợi Ý Du Lịch Thông Minh — Bối cảnh dự án

> File này dành cho AI coding agent (Claude Code, Copilot, ChatGPT...) đọc để hiểu toàn bộ
> bối cảnh trước khi code. Nếu dùng Claude Code: đặt file này ở gốc repo, tên đúng là
> `CLAUDE.md` — công cụ sẽ tự động đọc mỗi lần mở, không cần dán tay lại từ đầu.
> Với agent khác (Copilot Chat, ChatGPT...): dán toàn bộ nội dung này vào tin nhắn đầu tiên
> của mỗi phiên làm việc mới.

## 1. Giới thiệu đề tài
- **Tên đề tài:** Website gợi ý du lịch thông minh
- **Loại:** Đồ án chuyên ngành (môn học, KHÔNG phải đồ án tốt nghiệp), ngành Công nghệ phần mềm
- **Trường:** Đại học Tài nguyên và Môi trường TP.HCM, Khoa CNTT
- **Thời gian:** 24/08/2026 – 04/12/2026 (14-15 tuần)
- **GVHD:** yêu cầu rất nghiêm — làm không đúng đề cương có thể không được ra hội đồng, nên
  mọi thứ code ra phải khớp với đề cương đã nộp, không tự ý thêm/bớt phạm vi lớn.

## 2. Stack công nghệ
- **Backend:** Python, Django, Django REST Framework
- **Frontend:** React (khởi tạo bằng Vite)
- **CSDL:** PostgreSQL (tạo qua Docker, biến môi trường `POSTGRES_DB`, KHÔNG gõ tay `CREATE DATABASE`)
- **Cache & hàng đợi:** Redis + Celery (xử lý tác vụ bất đồng bộ: gọi API thời tiết, embedding, LLM)
- **Container:** Docker + docker-compose (bắt buộc, đã cam kết trong đề cương)
- **Cấu trúc repo:** monorepo — `backend/` (Django) và `frontend/` (React) trong cùng 1 repo

## 3. Chức năng cốt lõi — BẮT BUỘC, phải hoàn thành đầy đủ

1. Đăng ký/đăng nhập, quản lý hồ sơ người dùng, lịch sử tìm kiếm
2. Thiết lập sở thích du lịch (chọn nhãn có sẵn: biển/núi/thành phố/ẩm thực + mô tả tự do) và ngân sách dự kiến
3. Nhập thông tin chuyến đi: vị trí hiện tại, ngày khởi hành, **ngày dự kiến đến nơi**, số ngày lưu trú
4. Tích hợp dự báo thời tiết **Open-Meteo** (miễn phí, không cần API key, không cần thẻ) — lấy đúng dự báo tại ngày dự kiến đến
5. Quản lý điểm đến (admin CRUD): tên, mô tả (tự viết tay), loại hình, tọa độ, ảnh, rating tham khảo
   - Dữ liệu địa điểm lấy từ **Nominatim (OpenStreetMap)** — KHÔNG dùng Google Places (đòi thẻ ngân hàng)
   - Ảnh lấy từ **Unsplash API** (miễn phí, không thẻ) — nhớ ghi chú nguồn ảnh theo yêu cầu bản quyền
6. **Bộ máy gợi ý đa tiêu chí (trọng tâm đề tài — xem chi tiết Mục 5)**
7. Giải thích gợi ý bằng LLM — dùng **Gemini API model Flash hoặc Flash-Lite** (free tier), **KHÔNG dùng model Pro** (giới hạn quá thấp, dễ hết quota)
8. Quản lý chỗ ở: khách sạn/homestay **demo tự đặt tên** (không dùng thương hiệu thật ngoài đời — tránh gây hiểu nhầm đã hợp tác thật), mỗi chỗ ở có nhiều loại phòng (đơn/đôi/gia đình), mỗi loại phòng có giá + số lượng tồn kho + **danh sách tiện ích hiển thị icon** (wifi, điều hòa, bồn tắm, hướng biển...)
9. Đặt phòng thật (không phải mô phỏng):
   - Validate ngày: ngày nhận ≥ hôm nay, ngày trả > ngày nhận
   - Kiểm tra tồn kho theo loại phòng (đếm đơn chồng lấn ngày < số lượng tối đa loại phòng đó)
   - Chống 2 người đặt trùng cùng lúc: dùng **transaction + row-level locking** (`select_for_update()` trong Django) khi kiểm tra và tạo đơn
10. Thanh toán qua **VNPay hoặc Momo, môi trường sandbox, luồng Return URL** (redirect qua trình duyệt, KHÔNG cần webhook/IPN, KHÔNG cần server có địa chỉ public — chạy được cả trên localhost lúc dev)
11. Chỉ đường thông minh cho người tự lái xe máy/ô tô: dùng **OpenRouteService** (miễn phí, chỉ cần email đăng ký, không cần thẻ) lấy khoảng cách + thời gian di chuyển; kèm nút mở Google Maps app (chỉ là deep link URL miễn phí, không phải gọi API trả phí)
12. Mã hóa dữ liệu nhạy cảm của khách hàng (số điện thoại) bằng thuật toán đối xứng **Fernet (dựa trên AES)** trước khi lưu vào CSDL, khóa mã hóa lưu ở biến môi trường tách biệt CSDL
13. Trang quản trị: xây bằng **React riêng** (không dùng giao diện Django admin mặc định làm giao diện chính thức để demo — vì không đồng bộ style với phần người dùng); Django admin vẫn giữ bật ngầm chỉ để tiện nhập nhanh dữ liệu mẫu lúc chuẩn bị

## 4. Kiến trúc & nguyên tắc kỹ thuật cần nhớ
- Backend và frontend giao tiếp qua REST API (Django REST Framework)
- Các tác vụ chậm (gọi API thời tiết, tính embedding, gọi LLM) chạy bất đồng bộ qua Celery + Redis
- Kết quả dự báo thời tiết được cache trong Redis theo (địa điểm, ngày) để giảm số lần gọi API ngoài
- OpenRouteService và cổng thanh toán chỉ gọi khi người dùng chủ động thao tác (chọn xem chỉ đường / đặt phòng) — không nằm trong vòng lặp tính điểm gợi ý chính, không ảnh hưởng hiệu năng thuật toán
- Toàn bộ hệ thống đóng gói bằng Docker/docker-compose

## 5. Giải thuật gợi ý — PHẢI GIẢI THÍCH ĐƯỢC khi GVHD hỏi

Thuật toán trọng tâm: **Weighted Sum Model** (mô hình tổng trọng số đa tiêu chí), gồm 4 thành phần điểm:

1. **Preference Score** — Cosine Similarity trên vector embedding (ứng dụng NLP): chuyển sở thích người dùng và mô tả điểm đến thành vector bằng mô hình embedding đa ngôn ngữ có sẵn (không tự huấn luyện), tính độ tương đồng cosine.
   `Preference_Score = (A · B) / (‖A‖ × ‖B‖)`

2. **Weather Score** — Logic mờ (Fuzzy Logic): dùng hàm thành viên hình thang cho nhiệt độ/xác suất mưa/tốc độ gió tại điểm đến đúng ngày dự kiến đến, thay vì ngưỡng if-else cứng.
   `μ_nhietdo(t) = 0 nếu t≤15 hoặc t≥40; tăng dần 15→24; =1 nếu 24≤t≤30; giảm dần 30→40`
   `Weather_Score = α·μ_nhietdo + β·μ_mua + γ·μ_gio, α+β+γ=1`

3. **Budget Score** — Linear Scoring: so ngân sách người dùng với giá phòng thực tế tại điểm đến.
   `Budget_Score = 1 nếu Cost≤Budget; ngược lại = max(0, 1-(Cost-Budget)/Budget)`

4. **Distance Score** — công thức Haversine, chuẩn hóa nghịch theo khoảng cách.

**Tổng hợp:** `Final_Score = w1·Preference + w2·Weather + w3·Budget + w4·Distance` (w1+w2+w3+w4=1), xếp hạng giảm dần, trả Top-N.

Sau khi có kết quả, gọi **Gemini API** sinh đoạn giải thích cá nhân hóa ngắn cho gợi ý hàng đầu.

**Thuật toán phụ (đặt phòng):**
- Kiểm tra phòng trống: `Trùng lịch nếu (NgayNhan_moi < NgayTra_cu) VÀ (NgayNhan_cu < NgayTra_moi)`; còn trống nếu số đơn chồng lấn < số lượng phòng tối đa của loại phòng
- Mã hóa SĐT: Fernet/AES trước khi lưu

## 6. Phần MỞ RỘNG — chỉ làm nếu còn dư thời gian, KHÔNG bắt buộc, không ảnh hưởng điểm nếu chưa kịp

Thứ tự ưu tiên nếu có thời gian dư (làm từ trên xuống):
1. **Chat realtime** giữa người dùng và quản trị viên — dùng Django Channels + Redis (GVHD đánh giá cao ý này, ưu tiên làm trước các mục dưới nếu có thời gian) — LƯU Ý: cần WebSocket/ASGI, kỹ thuật khác hẳn REST thông thường, cần thời gian học/thử nghiệm riêng
2. IPN (webhook xác nhận thanh toán song song từ cổng thanh toán, cần server có địa chỉ public)
3. Hủy đơn kèm hoàn tiền qua sandbox
4. Gửi email xác nhận đặt phòng tự động
5. Cho phép đánh giá chỗ ở sau khi lưu trú
6. Tự động điều chỉnh trọng số (w1-w4) theo phản hồi người dùng
7. Gợi ý lịch trình nhiều điểm đến liên tiếp thay vì 1 điểm đến đơn lẻ

## 7. Những điều TUYỆT ĐỐI cần tránh (đã có lý do rõ ràng, đừng đổi lại)
- ❌ Google Places / Google Maps Directions API — cần thẻ ngân hàng, dev không có thẻ dùng được quốc tế → dùng Nominatim + OpenRouteService thay thế
- ❌ Gemini model Pro — quota quá thấp cho việc test lặp lại → dùng Flash/Flash-Lite
- ❌ Kết nối Booking.com/Agoda thật — các nền tảng này không cấp API cho sinh viên → tự quản lý dữ liệu chỗ ở riêng (demo)
- ❌ Dùng tên khách sạn thật ngoài đời cho dữ liệu demo → tự đặt tên minh họa, tránh hiểu nhầm đã hợp tác thật
- ❌ IPN/webhook thanh toán làm phần bắt buộc → chỉ làm Return URL flow là đủ cho phần lõi
- ❌ Dùng Django admin mặc định làm giao diện quản trị chính thức để demo → phải là trang React tự xây

## 8. Nguyên tắc chung khi code cùng AI agent
- Mọi đoạn code AI viết ra, người dùng (Tiến) phải đọc hiểu được — vì GVHD có thể hỏi bất kỳ dòng nào lúc bảo vệ, "AI viết giúp" không phải câu trả lời chấp nhận được
- Ưu tiên code đơn giản, dễ giải thích hơn là code "khôn khéo" nhưng khó hiểu
- Commit thường xuyên, message rõ ràng — không dồn hết vào 1 commit cuối kỳ

# DuLich_ThongMinh

## Trợ lý du lịch dùng RAG

Trang `/tro-ly` trả lời câu hỏi tiếng Việt dựa trên các đoạn tri thức công khai, không đọc đơn hàng, giao dịch, tài khoản, đánh giá lưu trú hay bài chia sẻ. Nguồn gồm danh mục điểm đến, chỗ ở, loại phòng, tour, lịch khởi hành, các mục của trang Giới thiệu và chính sách tại `backend/core/rag_knowledge/chinh_sach.md`. Thông tin tour và chỗ ở là dữ liệu minh họa.

Chỉ mục lai lưu nội dung, metadata, mã băm và embedding trong `KnowledgeChunk`. Lệnh `python manage.py build_knowledge_index` dựng/cập nhật các đoạn theo nguồn, xóa đoạn mồ côi và chỉ gọi Sentence-BERT khi nội dung một đoạn thay đổi. Một worker đồng bộ hóa lúc khởi động và Celery Beat làm mới mỗi 6 giờ; model chỉ được nạp khi cần tạo embedding. Trong mỗi tiến trình web, vector được giữ trong RAM và tải lại khi số đoạn hoặc thời điểm cập nhật chỉ mục đổi.

Truy xuất dùng cosine similarity trên embedding cùng khớp tên điểm đến sau khi bỏ dấu; nếu câu hỏi nêu điểm đến thì ưu tiên các đoạn liên quan. Bộ phân tích quy tắc hiện có lấy ngân sách và loại đoạn tour/chỗ ở có giá thấp nhất cao hơn ngân sách. `RAG_MIN_SIMILARITY` đặt ngưỡng cosine (mặc định tạm thời `0.38`). Đây là giá trị khởi đầu, chưa được hiệu chỉnh bằng dữ liệu triển khai trong lượt thêm tính năng này vì chỉ mục chưa được build theo yêu cầu; không coi đây là ngưỡng đã đo.

| Nhóm câu hỏi trong `rag_examples.py` | Số câu | Cosine đo được | Ngưỡng đề xuất |
| --- | ---: | ---: | ---: |
| Có nguồn trong chỉ mục | 15 | Chưa đo: chưa build chỉ mục | Chưa xác định |
| Không có nguồn / ngoài phạm vi | 10 | Chưa đo: chưa build chỉ mục | Chưa xác định |

Lệnh `python manage.py check_rag` in 25 câu mẫu, top 3 đoạn cùng cosine, Recall@3, tỉ lệ từ chối và ngưỡng đề xuất từ điểm của nhóm câu có/không có nguồn. Bảng đo chưa có số liệu thực cho đến khi đã migrate và build chỉ mục; không ghi số ước đoán vào đây. Sau khi chạy, xem các cặp điểm dương/âm, đặt `RAG_MIN_SIMILARITY` theo kết quả phù hợp, rồi chạy lại lệnh. Nếu `GEMINI_API_KEY` có trong môi trường, lệnh cũng gửi câu mẫu tới Gemini để kiểm tra đầu ra; có thể tạm bỏ key nếu chỉ muốn đo truy xuất.

API `POST /api/assistant/ask/` dùng được cho khách hoặc người dùng đăng nhập, giới hạn 20 lượt/giờ theo IP hoặc tài khoản. Câu hỏi dưới 6 từ được nối với câu hỏi trước để truy xuất hội thoại ngắn. Kết quả dùng Gemini qua Celery khi có đoạn đạt ngưỡng; task có timeout 10 giây, giới hạn mềm 20 giây và tối đa một lần thử lại. Câu trả lời được kiểm tra số liệu và ký hiệu nguồn trước khi hiển thị; khi Gemini lỗi hoặc nội dung không đạt kiểm tra, hệ thống trả trích đoạn có dẫn nguồn. Không có đoạn đạt ngưỡng thì trả lời cố định, không gọi Gemini. Mỗi câu hỏi gần như độc lập; lịch sử chỉ giữ tối đa 10 tin trong `sessionStorage` của trình duyệt.

Lần đầu triển khai, chạy thủ công theo thứ tự:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py build_knowledge_index
docker compose exec backend python manage.py check_rag
```

## Tìm kiếm bằng câu tự nhiên

Trang Gợi ý có ô “Tìm kiếm bằng câu tự nhiên”. `POST /api/recommendations/parse-query/` chuẩn hóa câu tối đa 300 ký tự, giới hạn 20 yêu cầu mỗi giờ theo tài khoản hoặc IP, và trả `task_id` cùng kết quả dự phòng tức thì từ bộ quy tắc. Celery thử trích xuất JSON bằng Gemini; kết quả được kiểm tra trước khi trả về và lưu trong Redis tối đa một giờ theo câu đã chuẩn hóa. Nếu Gemini thiếu cấu hình, lỗi, quá thời gian hoặc trả JSON không dùng được, hệ thống dùng kết quả của bộ quy tắc offline.

Schema gồm `preference_labels` (biển, núi, ẩm thực, văn hóa, nghỉ dưỡng, mạo hiểm), `preference_text`, `budget_vnd`, `travel_date`, `weather_preference`, `duration_days`, `party_size` và `origin_text`. Ngân sách ngoài khoảng 100.000–1.000.000.000đ bị bỏ; ngày đi chỉ nhận trong 16 ngày tính cả hôm nay. “Cuối tuần này” là thứ Bảy sắp tới (nếu hôm nay là thứ Bảy hoặc Chủ nhật thì lấy hôm nay); “ngày mai” là +1 và “tuần sau” là +7. Số ngày, số người và địa điểm xuất phát hiện chỉ được hiển thị trong ghi chú, chưa dùng để tính điểm; người dùng cần chọn tọa độ xuất phát trong form nếu muốn tính khoảng cách.

Lệnh `python manage.py check_nl_parser` so sánh bộ quy tắc với 20 câu mẫu và cả Gemini nếu đã cấu hình `GEMINI_API_KEY`; lệnh không warm-up Sentence-BERT. Báo cáo có kết quả theo từng trường và tỉ lệ đúng tổng.

## Thời tiết mong muốn trong gợi ý

API gợi ý nhận tham số `weather_preference`: `balanced` (mặc định), `cool`, `warm` hoặc `dry`. Hồ sơ lưu lựa chọn này; mỗi lần tìm kiếm thành công cũng ghi lựa chọn vào lịch sử để chức năng “Tìm lại” khôi phục đúng bộ lọc.

Điểm thời tiết dùng logic mờ trên nhiệt độ, xác suất mưa và gió. `balanced` giữ hình thang nhiệt 15–24–30–40 °C với trọng số nhiệt/mưa/gió 0,5/0,3/0,2. `cool` dùng hình thang 12–16–24–30 °C; `warm` dùng 24–28–33–40 °C. `dry` dùng hình thang nhiệt cân bằng và trọng số 0,3/0,5/0,2. Hàm thành viên mưa và gió giống nhau ở cả bốn lựa chọn, và tổng trọng số luôn bằng 1.

Redis dùng chung một khóa `weather:v3:<latitude>:<longitude>:<date>` cho mọi lựa chọn. Cache chỉ lưu dự báo thô (nhiệt độ, xác suất mưa, tốc độ gió); điểm thành phần và điểm tổng được tính khi tạo response. Mỗi kết quả có thêm `weather` với `temperature_c`, `rain_probability`, `wind_kmh` và tóm tắt tiếng Việt; khi thiếu dự báo, `weather_available` là `false` và điểm thời tiết trung tính là 0,5. Lời giải thích AI nhận lựa chọn cùng số liệu của điểm đến hạng nhất và được yêu cầu chỉ dùng đúng các con số đã cung cấp.

## Chuẩn hóa đầu vào và ngưỡng khớp sở thích

Ô sở thích được gom khoảng trắng, bỏ ký tự điều khiển, giới hạn 200 ký tự và mở rộng các nhãn quen thuộc trước khi tạo embedding. Nếu bỏ trống, tiêu chí sở thích không tham gia. Ngân sách trống hoặc bằng 0 cũng bị bỏ qua; các trọng số cá nhân hóa được chuẩn hóa lại trên những tiêu chí có mặt. Điểm cosine gốc vẫn có trong `preference_raw`.

Min-max chỉ được dùng khi cosine cao nhất vượt `PREFERENCE_MATCH_MIN=0.30`. Ngưỡng này được chọn từ 35 điểm đến đã có embedding, truy vấn đã áp dụng mở rộng nhãn, vị trí xuất phát TP. Hồ Chí Minh và dữ liệu đo ngày 25/10/2026. Nhóm liên quan có cosine thấp nhất 0.425053; nhóm không liên quan có cosine cao nhất 0.175904, nên ngưỡng 0.30 nằm giữa hai nhóm.

| Nhóm | Truy vấn | Cosine cao nhất |
| --- | --- | ---: |
| Liên quan | biển | 0.693640 |
| Liên quan | núi | 0.450897 |
| Liên quan | ẩm thực | 0.474012 |
| Liên quan | văn hóa lịch sử | 0.436829 |
| Liên quan | nghỉ dưỡng | 0.468392 |
| Liên quan | đi biển ăn hải sản | 0.425053 |
| Không liên quan | xyz | 0.175904 |
| Không liên quan | bóng đá | 0.096845 |
| Không liên quan | lập trình | 0.071849 |
| Không liên quan | asdfgh | 0.088793 |

Chạy lại báo cáo với `docker compose exec backend python manage.py check_recommendation_quality --latitude 10.7769 --longitude 106.7009 --budget 5000000 --travel-date YYYY-MM-DD`. Báo cáo in cosine cao nhất trên toàn bộ điểm đến đã có embedding cùng top 8 điểm thành phần.

## Cấu hình dịch vụ tích hợp

Sao chép `.env.example` thành `.env`, sau đó đăng ký các dịch vụ dưới đây và điền credential tương ứng. Không đưa file `.env` hoặc bất kỳ key thật nào lên Git.

| Dịch vụ                | Đăng ký                                                         | Biến trong `.env`                                         |
| ---------------------- | --------------------------------------------------------------- | --------------------------------------------------------- |
| Gemini AI Studio       | [Tạo API key](https://aistudio.google.com/apikey)               | `GEMINI_API_KEY`                                          |
| OpenRouteService       | [Đăng ký tài khoản](https://openrouteservice.org/dev/#/signup)  | `ORS_API_KEY`                                             |
| VNPay Sandbox          | [Đăng ký merchant test](https://sandbox.vnpayment.vn/devreg) · [Tài liệu tích hợp](https://sandbox.vnpayment.vn/apis/docs/) | `VNPAY_TMN_CODE`, `VNPAY_HASH_SECRET` |
| MoMo Developer Sandbox | [Tài liệu/đăng ký MoMo Developers](https://developers.momo.vn/) | `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY` |
| Unsplash Developers    | [Đăng ký ứng dụng developer](https://unsplash.com/developers)   | `UNSPLASH_ACCESS_KEY`                                     |

Admin có thể kiểm tra trạng thái cấu hình (không gọi API, không hiển thị secret) tại `GET /api/admin/integrations-status/`. Với thanh toán, nếu cổng được chọn chưa có credential hoặc không khởi tạo được giao dịch thì backend báo lỗi; hệ thống không tự xác nhận thanh toán hay chuyển ngầm sang cổng khác.

### Cấu hình VNPay Sandbox

Luồng mặc định dùng VNPay Sandbox theo phương thức chuyển hướng GET. Đăng ký merchant sandbox tại VNPay để nhận `VNPAY_TMN_CODE` và `VNPAY_HASH_SECRET`, rồi điền hai giá trị vào `.env`. Backend ký URL thanh toán và xác minh `vnp_SecureHash` bằng HMAC-SHA512 trước khi cập nhật đơn. Số tiền được lấy từ đơn trong cơ sở dữ liệu và chuyển sang đơn vị xu theo quy ước VNPay.

#### Các liên kết VNPay trong email cấp Sandbox

| Liên kết | Dùng để làm gì | Khi nào dùng |
| --- | --- | --- |
| [Merchant Admin](https://sandbox.vnpayment.vn/merchantv2/) | Đăng nhập trang quản lý merchant, tra cứu giao dịch sandbox và xem trạng thái thanh toán. | Sau khi được cấp tài khoản; dùng để kiểm tra giao dịch vừa thử. |
| [SIT Testing](https://sandbox.vnpayment.vn/vnpaygw-sit-testing/user/login) | Khu vực kiểm thử SIT/IPN của VNPay, giúp kiểm tra việc VNPay gọi máy chủ merchant và nhận phản hồi IPN. | Khi thử callback server-to-server; không phải trang thanh toán của khách. |
| [Tài liệu thanh toán PAY](https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html) | Đặc tả tạo URL thanh toán, các tham số, Return URL, IPN và cách xác minh chữ ký. | Khi cần hiểu hoặc đối chiếu cách tích hợp trong backend. |
| [Code demo tích hợp](https://sandbox.vnpayment.vn/apis/vnpay-demo/code-demo-tích-hợp) | Mã ví dụ chính thức để tham khảo cách tạo yêu cầu, ký dữ liệu và nhận kết quả. | Dùng để tham khảo; dự án này đã có phần tích hợp riêng, không cần chép demo vào dự án. |
| [Demo Cổng thanh toán](https://sandbox.vnpayment.vn/apis/vnpay-demo/) | Trang trải nghiệm thanh toán demo và thông tin thẻ test do VNPay công bố. | Thử giao diện thẻ sandbox độc lập; không thay thế luồng đặt đơn của website. |

Email cấp sandbox có `vnp_TmnCode` (Terminal ID/Mã Website) và `vnp_HashSecret` (Secret Key). Điền chúng vào đúng hai biến trong file `.env` gốc; không đưa giá trị thật vào README, `.env.example`, mã nguồn hoặc Git:

```env
VNPAY_TMN_CODE=<vnp_TmnCode được cấp>
VNPAY_HASH_SECRET=<vnp_HashSecret được cấp>
PAYMENT_PROVIDER=vnpay
```

Sau khi sửa `.env`, tạo lại container backend để Docker nạp biến môi trường mới:

```bash
docker compose up -d --force-recreate backend
```

#### Thử thanh toán VNPay trong website

1. Chạy website và đăng nhập.
2. Tạo đơn đặt phòng hoặc đặt tour. Ở bước thanh toán, chọn **VNPay Sandbox**.
3. Website chuyển sang trang thanh toán sandbox. Chọn ngân hàng NCB và dùng đúng dữ liệu thẻ test trong email VNPay: số thẻ `9704198526191432198`, chủ thẻ `NGUYEN VAN A`, ngày phát hành `07/15`, OTP `123456`. Đây là dữ liệu thử nghiệm, không phải thẻ hay giao dịch thật.
4. Sau khi xác nhận, VNPay chuyển trình duyệt về Return URL của website. Backend xác minh chữ ký và số tiền trước khi cập nhật đơn; kết quả hiện tại có thể xem trong Hồ sơ và Merchant Admin.
5. IPN là thông báo riêng từ máy chủ VNPay đến backend, không phải trang trình duyệt. Đăng ký URL `https://<domain-cong-khai>/api/payments/vnpay/ipn/` với VNPay/SIT. Khi chạy local, VNPay không gọi được `localhost`; cần HTTPS có thể truy cập công khai (chẳng hạn tunnel đang hoạt động). Cấu hình `BASE_URL` bằng origin công khai của backend khi thử callback qua Internet.

Không gửi mật khẩu Merchant Admin, `VNPAY_HASH_SECRET`, mã OTP hoặc thông tin đăng nhập qua README/Git/chat. Mật khẩu Merchant Admin và SIT là mật khẩu bạn đã đặt khi đăng ký merchant, không phải Secret Key.

`BASE_URL` phải là origin của backend, ví dụ `https://api.example.com`; cấu hình Return URL trong yêu cầu sẽ trỏ tới `/api/payments/return/`. Đăng ký `/api/payments/vnpay/ipn/` trong cấu hình merchant VNPay để nhận xác nhận server-to-server. IPN yêu cầu HTTPS và domain công khai; VNPay không thể gọi `localhost`. API IPN trả `RspCode`/`Message` và xử lý callback lặp idempotent. Có thể dùng tunnel HTTPS trong môi trường phát triển để thử IPN.

Khi hủy đơn đã thanh toán qua VNPay, backend gửi yêu cầu hoàn tiền sandbox có chữ ký HMAC-SHA512 tới API transaction refund của VNPay. Kết quả được ghi vào trạng thái hoàn tiền của đơn; cần cấu hình credential merchant sandbox hợp lệ để kiểm thử thật.

### Cấu hình MoMo Sandbox (AIO v2)

MoMo vẫn là cổng thanh toán độc lập bên cạnh VNPay. Điền bộ thông tin merchant sandbox được MoMo cấp vào `MOMO_PARTNER_CODE`, `MOMO_ACCESS_KEY`, `MOMO_SECRET_KEY`. Hệ thống tạo yêu cầu AIO v2, xác minh chữ ký HMAC-SHA256 trên Return URL/IPN và gửi hoàn tiền qua API MoMo khi đơn được thanh toán bằng MoMo.

Return URL dùng chung `/api/payments/return/`; IPN MoMo là `POST /api/payments/momo/ipn/`. Cả Return URL và IPN cần domain public khi thử callback server-to-server thực tế.

### Nhà cung cấp thanh toán

`PAYMENT_PROVIDER=vnpay` là lựa chọn mặc định nếu client cũ không gửi lựa chọn. Ở giao diện, khách chọn riêng VNPay Sandbox hoặc MoMo Sandbox cho từng đơn; lựa chọn được lưu cùng đơn để callback và hoàn tiền đi đúng cổng. Nếu cổng đã chọn thiếu cấu hình hoặc lỗi, API báo lỗi và không tự chuyển sang cổng khác hay giả lập thanh toán. Chế độ `simulated` vẫn dành riêng cho kiểm thử/dự phòng khi chủ động bật `PAYMENT_PROVIDER=simulated`. Sau khi đổi `.env`, khởi động lại backend và celery để Docker nạp cấu hình mới.
> tao test xem có dính bên antigravity không

### Khôi phục mật khẩu và cấu hình email

Mặc định, `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`: email chỉ được **in vào log backend**, không gửi tới hộp thư. Khi triển khai thật, đặt các biến môi trường:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@example.com
EMAIL_HOST_PASSWORD=mat_khau_smtp
DEFAULT_FROM_EMAIL=noreply@example.com
FRONTEND_URL=https://example.com
PASSWORD_RESET_TIMEOUT=3600
```

`FRONTEND_URL` là địa chỉ website công khai dùng trong liên kết đặt lại mật khẩu. `PASSWORD_RESET_TIMEOUT` tính bằng giây, mặc định 3600. Lệnh `python manage.py check_user_emails` chỉ liệt kê tài khoản thiếu email hoặc trùng email, không sửa dữ liệu.

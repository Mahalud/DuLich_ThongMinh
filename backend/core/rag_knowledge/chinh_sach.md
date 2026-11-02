# Đặt phòng
Người dùng chọn chỗ ở, loại phòng, ngày nhận, ngày trả và thông tin khách trên trang đặt phòng. Hệ thống kiểm tra ngày hợp lệ, số phòng còn trống trong toàn bộ khoảng lưu trú và tính tổng tiền từ giá phòng nhân với số đêm. Đơn mới có trạng thái chờ thanh toán; tình trạng chỗ chỉ đổi sau khi cổng thanh toán xác nhận. Dữ liệu chỗ ở và loại phòng trên website là dữ liệu minh họa phục vụ đồ án.

# Đặt tour
Người dùng chọn tour, ngày khởi hành còn nhận khách và số người lớn, trẻ em. Hệ thống kiểm tra số chỗ còn lại trước khi tạo đơn và tự tính tổng tiền theo giá của tour, không dùng số tiền do trình duyệt gửi lên. Đơn mới chờ thanh toán; trạng thái xác nhận được cập nhật sau khi nhận kết quả thanh toán hợp lệ. Tour và lịch khởi hành hiện là dữ liệu minh họa phục vụ đồ án.

# Thanh toán sandbox
Thanh toán trực tuyến của đồ án chạy trong môi trường sandbox hoặc chế độ mô phỏng, không phải giao dịch thật và không chuyển tiền thật. Ở chế độ mô phỏng, người dùng chọn kết quả thành công hoặc thất bại để kiểm thử luồng. Ở chế độ sandbox, trạng thái đơn chỉ được xác nhận sau khi website kiểm tra kết quả trả về hoặc thông báo IPN có chữ ký hợp lệ từ cổng thanh toán. Không nhập thông tin thanh toán thật.

# Hủy đơn và hoàn tiền
Đơn phòng được hủy trước ngày nhận ít nhất {ROOM_CANCELLATION_MIN_DAYS} ngày. Nếu còn từ {ROOM_FULL_REFUND_MIN_DAYS} ngày trở lên, khoản hoàn theo chính sách là 100%; nếu còn từ {ROOM_CANCELLATION_MIN_DAYS} đến dưới {ROOM_FULL_REFUND_MIN_DAYS} ngày, khoản hoàn là 50%. Đơn tour được hủy trước ngày khởi hành ít nhất {TOUR_CANCELLATION_MIN_DAYS} ngày; nếu còn từ {TOUR_FULL_REFUND_MIN_DAYS} ngày trở lên thì hoàn 100%, còn từ {TOUR_CANCELLATION_MIN_DAYS} đến dưới {TOUR_FULL_REFUND_MIN_DAYS} ngày thì hoàn 50%. Số tiền cụ thể phụ thuộc đơn đã thanh toán và chính sách đang cấu hình; hệ thống hiển thị khoản dự kiến trước khi xác nhận.

# Quên mật khẩu
Người dùng nhập email đã đăng ký tại trang quên mật khẩu. Hệ thống trả lời theo cùng một cách dù email có tài khoản hay không để không tiết lộ thông tin tài khoản. Nếu email hợp lệ và gửi thư được cấu hình, liên kết đặt lại sẽ được gửi tới hộp thư và chỉ dùng được trong thời hạn cấu hình của hệ thống. Nếu không nhận được thư, hãy kiểm tra thư rác hoặc thử gửi lại sau.

# Trò chuyện hỗ trợ
Người dùng có thể trò chuyện với quản trị viên qua khung hỗ trợ khi đã đăng nhập. Tin nhắn được lưu để hiển thị lịch sử của đúng cuộc hội thoại; người dùng chỉ xem được hội thoại của mình, còn quản trị viên có quyền xử lý các hội thoại. Tính năng này dùng để hỗ trợ sử dụng website, không phải kênh khẩn cấp và không nên gửi mật khẩu, mã xác thực hay thông tin thanh toán.

# Dự báo thời tiết
Điểm thời tiết trong gợi ý dựa trên dữ liệu dự báo của Open-Meteo khi có sẵn. Dự báo tối đa 16 ngày tính cả hôm nay; ngày xa hơn hoặc khi dịch vụ không có dữ liệu thì hệ thống không thể cung cấp dự báo cụ thể. Thời tiết là một trong các tiêu chí gợi ý cùng với sở thích, ngân sách và khoảng cách, không phải cam kết về thời tiết thực tế.

# Cách hoạt động của gợi ý
Hệ thống xếp hạng điểm đến theo tối đa bốn tiêu chí: mức gần với sở thích, thời tiết mong muốn, ngân sách dự kiến và khoảng cách từ vị trí xuất phát. Nếu người dùng không cung cấp một tiêu chí, tiêu chí đó được bỏ qua và trọng số được chia lại cho các tiêu chí còn lại. Kết quả là gợi ý tham khảo, có thể thay đổi khi dữ liệu hoặc dự báo được cập nhật.

# Dữ liệu minh họa
Đây là đồ án chuyên ngành. Thông tin chỗ ở, loại phòng, tour và lịch khởi hành được biên soạn làm dữ liệu minh họa phục vụ trình diễn tính năng. Nội dung có thể không tương ứng với cơ sở lưu trú, dịch vụ hay chỗ bán thực tế. Người dùng cần xác nhận trực tiếp với đơn vị cung cấp trước khi đưa ra quyết định ngoài phạm vi kiểm thử.

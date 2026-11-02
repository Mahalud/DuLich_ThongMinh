# ĐỀ CƯƠNG ĐỒ ÁN CHUYÊN NGÀNH
## CÔNG NGHỆ PHẦN MỀM

**Đề tài:** Xây dựng Website Đặt Tour Du Lịch Thông Minh Tích Hợp AI

| Thông tin | Nội dung |
|---|---|
| **Trường** | Trường Đại học Tài nguyên và Môi trường TP.HCM |
| **Khoa** | Công nghệ thông tin |
| **Giảng viên hướng dẫn** | ThS. Nguyễn Duy Tuấn |
| **Sinh viên thực hiện** | Nguyễn Minh Tiến |
| **Mã số sinh viên** | 1250080196 |
| **Lớp** | 12_ĐH_CNPM3 |
| **Khóa** | 2023–2027 |
| **Thời gian** | Tháng 09 năm 2026 |

---

## Mục lục

- [I. Mở đầu](#i-mở-đầu)
  - [1. Cơ sở khoa học và tính thực tiễn của đề tài](#1-cơ-sở-khoa-học-và-tính-thực-tiễn-của-đề-tài)
  - [2. Mục đích nghiên cứu](#2-mục-đích-nghiên-cứu)
  - [3. Đối tượng và phạm vi nghiên cứu](#3-đối-tượng-và-phạm-vi-nghiên-cứu)
  - [4. Phương pháp nghiên cứu](#4-phương-pháp-nghiên-cứu)
  - [5. Thời gian thực hiện](#5-thời-gian-thực-hiện)
  - [6. Kết quả dự kiến đạt được](#6-kết-quả-dự-kiến-đạt-được)
- [II. Nội dung](#ii-nội-dung)
- [III. Dự kiến kế hoạch thực hiện](#iii-dự-kiến-kế-hoạch-thực-hiện)
- [IV. Tài liệu tham khảo](#iv-tài-liệu-tham-khảo)
- [V. Các cơ quan, đơn vị cần liên hệ](#v-các-cơ-quan-đơn-vị-cần-liên-hệ)

---

# I. MỞ ĐẦU

## 1. Cơ sở khoa học và tính thực tiễn của đề tài

Trong bối cảnh chuyển đổi số của ngành du lịch, ứng dụng trí tuệ nhân tạo (AI) vào hệ thống gợi ý và đặt tour du lịch đang là hướng nghiên cứu được quan tâm rộng rãi cả trong và ngoài nước. Trên thế giới, nhiều hệ thống gợi ý du lịch thông minh đã được đề xuất, kết hợp học máy với dữ liệu lớn để cá nhân hóa gợi ý điểm đến [4], hoặc kết hợp logic mờ (fuzzy logic) với phương pháp ra quyết định đa tiêu chí để xử lý tính không chắc chắn trong sở thích người dùng [2], [5]. Đáng chú ý, Yoon và Choi đã đề xuất hệ thống R2Tour — gợi ý điểm đến du lịch dựa trên thông tin tình huống thời gian thực như nhiệt độ, lượng mưa, kết hợp khoảng cách địa lý, đạt độ chính xác 77,3% khi thử nghiệm trên dữ liệu thực tế tại đảo Jeju, Hàn Quốc [1]. Tại Việt Nam, một nghiên cứu tổng quan hệ thống trên 290 bài báo của Nguyễn Lê Uyên Minh và Nguyễn Minh Tâm cũng ghi nhận xu hướng ứng dụng AI ngày càng tăng trong các mảng dịch vụ khách hàng, tiếp thị và quản lý vận hành du lịch [6], cho thấy nhu cầu và tiềm năng ứng dụng AI vào du lịch tại Việt Nam là có cơ sở thực tiễn rõ ràng. Tuy nhiên, phần lớn các nền tảng du lịch phổ biến hiện nay tại Việt Nam chủ yếu hỗ trợ tìm kiếm theo địa điểm hoặc giá phòng, chưa tích hợp đồng thời yếu tố dự báo thời tiết vào quá trình gợi ý điểm đến và đặt tour.

Tuy nhiên, các nghiên cứu và hệ thống hiện có vẫn còn một số khoảng trống. Thứ nhất, Yoon và Choi chỉ ra rằng các công cụ gợi ý du lịch truyền thống gặp khó khăn khi đưa ra gợi ý trong tình huống thông tin không đầy đủ hoặc thay đổi theo thời gian thực, do phần lớn vẫn dựa chủ yếu vào mối quan hệ tĩnh giữa người dùng và điểm đến, chưa tích hợp đồng thời cả yếu tố thời tiết thời gian thực lẫn sở thích cá nhân được diễn đạt bằng ngôn ngữ tự nhiên [1]. Thứ hai, Chrysafiadi và cộng sự đã đề xuất hệ thống cá nhân hóa du lịch dựa trên logic mờ kết hợp phương pháp TOPSIS để xử lý tính không chắc chắn trong tiêu chí lựa chọn, nhưng chính nhóm tác giả thừa nhận việc tích hợp các nguồn dữ liệu thời gian thực bên ngoài như thời tiết trực tiếp vẫn còn là hướng phát triển trong tương lai, chưa được hiện thực hóa đầy đủ trong hệ thống [2]. Thứ ba, các nghiên cứu ứng dụng học sâu và học máy cho gợi ý du lịch [4], [5] chủ yếu tập trung vào cải thiện độ chính xác thuật toán trên tập dữ liệu lớn, nhưng ít phân tích khả năng triển khai thực tế với chi phí thấp, phù hợp quy mô vừa và nhỏ như thị trường du lịch trong nước; đồng thời phần lớn dừng lại ở việc gợi ý điểm đến đơn lẻ, chưa mở rộng thành quy trình đặt tour — đặt chỗ — thanh toán hoàn chỉnh trên cùng một nền tảng.

Đây chính là lý do đề tài lựa chọn hướng nghiên cứu này: cần một hệ thống có khả năng kết hợp đồng thời dự báo thời tiết thời gian thực theo đúng thời điểm dự kiến di chuyển, sở thích cá nhân diễn đạt bằng ngôn ngữ tự nhiên thông qua kỹ thuật embedding ngữ nghĩa [3], cùng ngân sách và khoảng cách của người dùng, trong một mô hình chấm điểm đa tiêu chí có thể giải thích được — điều mà chưa nghiên cứu nào nêu trên giải quyết trọn vẹn cùng lúc. Từ đó, đề tài xác định vấn đề cốt lõi cần giải quyết là xây dựng một hệ thống website đặt tour du lịch tích hợp đầy đủ các yếu tố trên, đồng thời hoàn thiện thành quy trình đặt tour, đặt chỗ và thanh toán trực tuyến khép kín.

Về cơ sở khoa học cụ thể, đề tài kết hợp các mô hình và giải thuật sau để hình thành các chức năng tương ứng: (1) mô hình embedding ngôn ngữ tự nhiên Sentence-BERT [3] kết hợp độ tương đồng cosine để hình thành chức năng so khớp sở thích người dùng với đặc điểm điểm đến; (2) logic mờ (fuzzy logic) [2] để hình thành chức năng chấm điểm mức độ phù hợp thời tiết; (3) mô hình tổng trọng số đa tiêu chí (Weighted Sum Model) để hình thành chức năng tổng hợp và xếp hạng điểm đến; (4) mô hình ngôn ngữ lớn (Gemini API) để hình thành chức năng giải thích gợi ý bằng ngôn ngữ tự nhiên; (5) công nghệ GIS (PostGIS) để hình thành chức năng tìm kiếm chỗ ở theo bán kính và tính toán khoảng cách di chuyển. Sự kết hợp này tạo thành một hệ thống gợi ý và đặt tour hoàn chỉnh, có thể giải thích được từng bước tính toán, khắc phục đúng các khoảng trống đã nêu ở [1], [2].

Về tính thực tiễn, sản phẩm của đề tài có thể ứng dụng trực tiếp cho các cá nhân đi du lịch tự túc cần công cụ hỗ trợ ra quyết định nhanh chóng thay vì tự tra cứu thủ công qua nhiều nguồn thông tin; cho các đơn vị lữ hành quy mô vừa và nhỏ có nhu cầu số hóa quy trình tư vấn, bán tour và quản lý đặt chỗ mà không cần đầu tư hệ thống lớn; đồng thời làm cơ sở tham khảo cho các nghiên cứu tiếp theo về tích hợp dữ liệu thời gian thực (thời tiết, vị trí) vào hệ thống gợi ý du lịch. Ngoài ra, toàn bộ dịch vụ bên ngoài được lựa chọn tích hợp (Open-Meteo, Nominatim, OpenRouteService, Gemini API) đều ở mức miễn phí, không yêu cầu thẻ ngân hàng, chứng minh khả năng triển khai thực tế với chi phí hạ tầng thấp, phù hợp quy mô khởi nghiệp nhỏ tại Việt Nam.

## 2. Mục đích nghiên cứu

Mục đích của đề tài là xây dựng một website đặt tour du lịch tích hợp trí tuệ nhân tạo, giúp người dùng — đặc biệt là nhóm khách du lịch tự túc — lựa chọn được điểm đến và tour du lịch phù hợp với sở thích cá nhân, ngân sách, điều kiện thời tiết tại thời điểm dự kiến đi và khoảng cách di chuyển, đồng thời thực hiện được toàn bộ quy trình đặt tour, đặt chỗ ở và thanh toán trực tuyến ngay trên hệ thống, qua đó rút ngắn thời gian tìm kiếm và ra quyết định so với việc tự tra cứu thủ công qua nhiều nguồn thông tin khác nhau. Để đạt được mục đích này, đề tài hướng đến việc tìm hiểu và ứng dụng cụ thể các mô hình AI, giải thuật và nghiệp vụ chính sau:

- Kỹ thuật embedding ngôn ngữ tự nhiên (Sentence-BERT) kết hợp logic mờ (fuzzy logic) và mô hình tổng trọng số đa tiêu chí (Weighted Sum Model) để xây dựng thuật toán gợi ý điểm đến dựa trên sở thích, thời tiết, ngân sách và khoảng cách.
- Mô hình ngôn ngữ lớn (Gemini API) để sinh giải thích cá nhân hóa bằng ngôn ngữ tự nhiên cho từng gợi ý.
- Nghiệp vụ đặt tour và đặt phòng lưu trú có kiểm tra tồn kho/chỗ trống thời gian thực, chống trùng lịch bằng cơ chế khóa dòng dữ liệu, tích hợp thanh toán trực tuyến qua cổng sandbox.
- Công nghệ GIS (PostGIS) để xây dựng chức năng tìm kiếm chỗ ở theo bán kính quanh điểm đến và hiển thị tuyến đường di chuyển thông minh trên bản đồ.
- Cơ chế bảo mật dữ liệu khách hàng bằng mã hóa đối xứng (Fernet) cho các trường thông tin nhạy cảm.
- Kiến trúc hệ thống website client – server (Django REST Framework, React), đóng gói và triển khai bằng Docker, đảm bảo khả năng vận hành ổn định.
## 3. Đối tượng và phạm vi nghiên cứu

### 3.1. Đối tượng nghiên cứu

Đối tượng nghiên cứu của đề tài gồm ba nhóm: (1) nhóm người dùng — những người có nhu cầu du lịch tự túc nhưng gặp khó khăn trong việc lựa chọn điểm đến và tour phù hợp với sở thích, ngân sách, điều kiện thời tiết và phương tiện di chuyển; (2) các mô hình trí tuệ nhân tạo và giải thuật được nghiên cứu, ứng dụng, gồm mô hình embedding ngôn ngữ tự nhiên (Sentence-BERT), mô hình ngôn ngữ lớn (Gemini API), giải thuật logic mờ (fuzzy logic), mô hình tổng trọng số đa tiêu chí (Weighted Sum Model), công thức Haversine và truy vấn không gian địa lý PostGIS; (3) các chức năng, nghiệp vụ chính của hệ thống, gồm gợi ý điểm đến thông minh, quản lý và đặt tour, quản lý và đặt chỗ ở, thanh toán trực tuyến, chỉ đường thông minh và tìm kiếm chỗ ở theo bán kính. Loại phần mềm phát triển là ứng dụng website (web application).

### 3.2. Phạm vi nghiên cứu

Phạm vi giải thuật: đề tài giới hạn nghiên cứu và ứng dụng các giải thuật gồm độ tương đồng cosine trên vector embedding (Sentence-BERT) cho bài toán so khớp sở thích, logic mờ (hàm thành viên hình thang) cho bài toán chấm điểm thời tiết, hàm tuyến tính cho bài toán chấm điểm ngân sách, công thức Haversine cho khoảng cách địa lý, mô hình tổng trọng số đa tiêu chí (Weighted Sum Model) để tổng hợp và xếp hạng, cùng truy vấn không gian PostGIS cho bài toán tìm kiếm theo bán kính. Đề tài sử dụng các mô hình AI đã được huấn luyện sẵn (pretrained) là Sentence-BERT và Gemini, không tự huấn luyện mô hình học sâu mới từ đầu.

Phạm vi chức năng phần mềm: hệ thống gồm các chức năng chính: đăng ký/đăng nhập, thiết lập sở thích và ngân sách, gợi ý điểm đến thông minh với trọng số tiêu chí tự động điều chỉnh dựa trên phản hồi người dùng, giải thích gợi ý bằng AI, quản lý và đặt tour theo lịch trình nhiều ngày, quản lý và đặt chỗ ở kèm hiển thị tiện ích phòng (có bồn tắm, hướng biển, wifi miễn phí, điều hòa...) dưới dạng các thẻ tiện ích (tag) có biểu tượng (icon) trực quan, giúp người dùng nhận diện nhanh tiện nghi của từng phòng, đánh giá chỗ ở sau khi lưu trú, thanh toán trực tuyến qua cổng sandbox kèm cơ chế xác nhận song song từ máy chủ cổng thanh toán (IPN) và chức năng hủy đơn kèm hoàn tiền qua sandbox, bảo mật thông tin khách hàng bằng mã hóa Fernet, chỉ đường thông minh, tìm kiếm chỗ ở theo bán kính, trò chuyện thời gian thực (chat realtime) giữa người dùng và quản trị viên sử dụng hạ tầng Redis kết hợp Django Channels, đăng tin chia sẻ đánh giá/trải nghiệm chuyến đi quy mô nhỏ, và quản trị hệ thống dành cho quản trị viên. Giao diện được thiết kế responsive, hiển thị tốt trên cả máy tính, máy tính bảng và điện thoại di động.

Phạm vi không gian: đề tài giới hạn phạm vi gợi ý và đặt tour trong lãnh thổ Việt Nam, với thời gian dự báo thời tiết tối đa theo giới hạn của dịch vụ sử dụng (tối đa 16 ngày).

Phạm vi dữ liệu: dữ liệu điểm đến (tên, tọa độ, địa chỉ) được thu thập từ dịch vụ Nominatim (OpenStreetMap); ảnh minh họa điểm đến lấy từ dịch vụ Unsplash; dữ liệu chỗ ở, loại phòng và tour mang tính minh họa (demo), do quản trị viên tự biên soạn để kiểm chứng luồng nghiệp vụ đặt chỗ — đặt tour hoạt động đúng như hệ thống thật, chưa phải dữ liệu hợp tác thương mại với đơn vị lữ hành hay khách sạn ngoài đời thực; việc kết nối dữ liệu thật với các nền tảng thương mại của bên thứ ba là hướng phát triển trong tương lai, ngoài phạm vi một đồ án chuyên ngành.

### 3.3. Công nghệ và công cụ sử dụng

#### 3.3.1. Django và Django REST Framework

Django là một framework phát triển ứng dụng web bằng ngôn ngữ Python, cung cấp sẵn các thành phần cho việc quản lý cơ sở dữ liệu, xác thực người dùng và tổ chức mã nguồn theo mô hình MVC. Đề tài sử dụng Django REST Framework (DRF) — một thư viện mở rộng của Django — để xây dựng các API theo chuẩn RESTful, làm cầu nối giao tiếp giữa phần giao diện người dùng và phần xử lý dữ liệu phía máy chủ, đảm nhiệm việc xử lý nghiệp vụ, tính toán thuật toán gợi ý và gọi các dịch vụ bên ngoài.

#### 3.3.2. React

React là một thư viện JavaScript dùng để xây dựng giao diện người dùng theo hướng thành phần (component-based). Đề tài sử dụng React để xây dựng giao diện web phía người dùng, bao gồm các màn hình nhập sở thích, ngân sách, thông tin chuyến đi, hiển thị danh sách điểm đến và tour được gợi ý, quản lý lịch trình cá nhân; giao diện này giao tiếp với phần máy chủ thông qua các API do Django REST Framework cung cấp.

#### 3.3.3. PostgreSQL

PostgreSQL là hệ quản trị cơ sở dữ liệu quan hệ mã nguồn mở, kết hợp phần mở rộng PostGIS (trình bày tại Mục 3.3.8), được đề tài sử dụng để lưu trữ toàn bộ dữ liệu của hệ thống, bao gồm thông tin tài khoản người dùng, sở thích cá nhân, dữ liệu điểm đến, tour, lịch trình, dữ liệu chỗ ở (phòng, giá, tồn kho theo ngày, tiện ích) và các bản ghi đặt tour, đặt phòng, giao dịch thanh toán.

#### 3.3.4. Redis và Celery

Redis là công cụ lưu trữ dữ liệu dạng khóa–giá trị trong bộ nhớ, được đề tài sử dụng làm bộ nhớ đệm (cache) cho kết quả dự báo thời tiết theo từng địa điểm và ngày cụ thể nhằm giảm số lần gọi đến dịch vụ thời tiết bên ngoài, đồng thời đóng vai trò hàng đợi (message broker) cho Celery. Celery là công cụ xử lý tác vụ bất đồng bộ bằng Python, được sử dụng để thực hiện các tác vụ tốn thời gian như gọi dịch vụ dự báo thời tiết, tính toán vector embedding và gọi mô hình ngôn ngữ lớn mà không làm gián đoạn trải nghiệm của người dùng trên giao diện.

#### 3.3.5. Docker

Docker là công cụ đóng gói ứng dụng cùng toàn bộ môi trường chạy (thư viện, cấu hình) thành các container độc lập. Đề tài sử dụng Docker để đóng gói các thành phần của hệ thống (máy chủ Django, cơ sở dữ liệu PostgreSQL, Redis), giúp việc cài đặt, triển khai và trình diễn hệ thống được thực hiện nhất quán trên nhiều môi trường khác nhau.

#### 3.3.6. Các dịch vụ API bên ngoài

Đề tài tích hợp bốn dịch vụ bên ngoài, đều ở mức miễn phí và không yêu cầu thẻ ngân hàng: dịch vụ dự báo thời tiết Open-Meteo để lấy dữ liệu nhiệt độ, xác suất mưa và tốc độ gió theo địa điểm và ngày cụ thể; dịch vụ dữ liệu địa điểm Nominatim của OpenStreetMap để lấy thông tin và tọa độ của các điểm đến; dịch vụ OpenRouteService để lấy khoảng cách thực tế, thời gian di chuyển ước tính và tuyến đường đến điểm đến; và dịch vụ Gemini API — một mô hình ngôn ngữ lớn — để sinh đoạn giải thích cá nhân hóa cho từng gợi ý.

#### 3.3.7. Cổng thanh toán trực tuyến

Đề tài tích hợp cổng thanh toán VNPay hoặc Momo ở môi trường thử nghiệm (sandbox) theo luồng chuyển hướng thanh toán (Return URL): sau khi người dùng xác nhận đặt tour/đặt phòng, hệ thống chuyển hướng sang trang thanh toán sandbox của cổng, sau đó nhận kết quả giao dịch qua địa chỉ trả về đã đăng ký sẵn để cập nhật trạng thái đơn. Toàn bộ giao dịch chỉ mang tính thử nghiệm kỹ thuật, không phát sinh giao dịch tiền thật.

#### 3.3.8. PostGIS

PostGIS là phần mở rộng của PostgreSQL cho phép lưu trữ và truy vấn dữ liệu không gian địa lý (geometry) trực tiếp trong cơ sở dữ liệu, kết hợp với GeoDjango — bộ công cụ GIS tích hợp sẵn trong Django. Đề tài sử dụng PostGIS để lưu tọa độ của điểm đến và chỗ ở dưới dạng kiểu dữ liệu không gian (Point) có đánh chỉ mục không gian (spatial index), phục vụ chức năng tìm kiếm chỗ ở trong bán kính quanh điểm đến.

## 4. Phương pháp nghiên cứu

### 4.1. Các phương pháp nghiên cứu lý thuyết áp dụng

Đề tài thu thập và tổng hợp tài liệu về hệ thống gợi ý (recommendation system), phương pháp ra quyết định đa tiêu chí (multi-criteria decision making), kỹ thuật embedding ngôn ngữ tự nhiên, logic mờ, kiến trúc web client – server hiện đại (RESTful API), công nghệ GIS và dữ liệu không gian (PostGIS), cũng như phương pháp đánh giá mô hình gợi ý (đánh giá thời gian phản hồi và mức độ phù hợp của kết quả gợi ý thông qua kiểm thử thực nghiệm).

### 4.2. Các phương pháp thực nghiệm áp dụng

Đề tài tiến hành phân tích và thiết kế hệ thống, cài đặt và xây dựng phần mềm theo mô hình phát triển lặp, thử nghiệm cài đặt từng giải thuật và mô hình AI, tích hợp vào hệ thống hoàn chỉnh, sau đó kiểm thử chức năng và đánh giá kết quả gợi ý trên dữ liệu thực tế. Giải thuật trọng tâm của đề tài là mô hình chấm điểm đa tiêu chí có trọng số (Weighted Sum Model), thuộc nhóm phương pháp ra quyết định đa tiêu chí, được cài đặt cụ thể qua các giải thuật thành phần.

#### 4.2.1. Thuật toán tính độ phù hợp sở thích — Cosine Similarity trên vector embedding (ứng dụng NLP)

Sở thích do người dùng nhập (dạng chọn nhãn có sẵn kết hợp mô tả bằng ngôn ngữ tự do) và phần mô tả của từng điểm đến trong cơ sở dữ liệu được chuyển thành các vector số thực bằng mô hình embedding ngôn ngữ tự nhiên đa ngôn ngữ Sentence-BERT [3] đã được huấn luyện sẵn (không tự huấn luyện). Độ phù hợp giữa hai vector được tính bằng độ tương đồng cosine, cho giá trị trong khoảng từ 0 đến 1.

$$
Preference_Score = (A · B) / (‖A‖ \times  ‖B‖), trong đó A là vector embedding của sở thích người dùng, B là vector embedding của mô tả điểm đến.
$$

#### 4.2.2. Thuật toán tính độ phù hợp thời tiết — Logic mờ (Fuzzy Logic)

Dữ liệu dự báo nhiệt độ, xác suất mưa và tốc độ gió tại điểm đến vào đúng ngày dự kiến tới nơi được lấy từ dịch vụ thời tiết, sau đó được đưa qua các hàm thành viên mờ (membership function) để tính điểm phù hợp, thay vì dùng ngưỡng if-else cứng nhắc.

$$
μ_nhietdo(t) = 0 nếu t \le  15 hoặc t \ge  40; (t−15)/(24−15) nếu 15 < t < 24; 1 nếu 24 \le  t \le  30; (40−t)/(40−30) nếu 30 < t < 40.
$$

Điểm phù hợp thời tiết cuối cùng là trung bình có trọng số của các hàm thành viên tương ứng với từng tiêu chí:

$$
Weather_Score = \alpha \times  μ_nhietdo(t) + \beta \times  μ_mua(p) + \gamma \times  μ_gio(v), với \alpha + \beta + \gamma = 1.
$$

#### 4.2.3. Thuật toán tính độ phù hợp ngân sách — Linear Scoring

Ngân sách người dùng nhập được so sánh với chi phí tham khảo của điểm đến. Nếu chi phí tham khảo không vượt quá ngân sách, điểm phù hợp đạt giá trị tối đa; nếu vượt quá, điểm giảm tuyến tính theo mức độ chênh lệch.

$$
Budget_Score = 1 nếu Cost \le  Budget;
$$

ngược lại Budget_Score = max(0, 1 − (Cost − Budget) / Budget).

#### 4.2.4. Thuật toán tính độ thuận tiện khoảng cách — công thức Haversine

Khoảng cách địa lý giữa vị trí hiện tại của người dùng và điểm đến được tính bằng công thức Haversine dựa trên tọa độ kinh độ, vĩ độ của hai vị trí, sau đó được chuẩn hóa nghịch để điểm đến càng gần vị trí người dùng thì điểm càng cao.

$$
d = 2r \times  arcsin(√(sin²((lat2−lat1)/2) + cos(lat1) \times  cos(lat2) \times  sin²((lon2−lon1)/2))); Distance_Score = 1 − min(d / d_max, 1).
$$

#### 4.2.5. Thuật toán tổng hợp và xếp hạng — Weighted Sum Model

Bốn thành phần điểm số ở trên được tổng hợp thành một điểm số duy nhất cho mỗi điểm đến, sau đó toàn bộ điểm đến ứng viên được sắp xếp giảm dần theo điểm số này để trả về danh sách Top-N điểm đến phù hợp nhất.

$$
Final_Score = w1 \times  Preference_Score + w2 \times  Weather_Score + w3 \times  Budget_Score + w4 \times  Distance_Score, với w1 + w2 + w3 + w4 = 1.
$$

#### 4.2.6. Ứng dụng mô hình ngôn ngữ lớn (LLM) sinh giải thích cá nhân hóa

Sau khi có kết quả xếp hạng, hệ thống gọi mô hình ngôn ngữ lớn thông qua Gemini API, truyền vào thông tin về điểm đến được chọn cùng các tiêu chí đạt điểm cao để sinh ra một đoạn văn ngắn giải thích lý do vì sao điểm đến đó được gợi ý cho người dùng cụ thể.

#### 4.2.7. Kiến trúc hệ thống tổng quan

Giao diện người dùng được xây dựng bằng React giao tiếp với phần xử lý phía máy chủ được xây dựng bằng Django REST Framework thông qua các API theo chuẩn RESTful; các tác vụ tốn thời gian như gọi dịch vụ dự báo thời tiết, tính toán embedding và gọi mô hình ngôn ngữ lớn được xử lý bất đồng bộ thông qua Celery kết hợp Redis. Dịch vụ OpenRouteService và cổng thanh toán chỉ được gọi khi người dùng chủ động thao tác, không nằm trong vòng lặp tính điểm gợi ý chính. Toàn bộ dữ liệu được lưu trữ trong PostgreSQL/PostGIS, hệ thống được đóng gói bằng Docker.

#### 4.2.8. Tích hợp bản đồ và chỉ đường thông minh (OpenRouteService)

Dành cho người dùng tự di chuyển bằng phương tiện cá nhân, hệ thống tích hợp OpenRouteService để lấy tuyến đường, khoảng cách thực tế và thời gian di chuyển ước tính, hiển thị trên bản đồ nhúng kèm nút mở Google Maps để chỉ đường chi tiết khi thực sự di chuyển — việc dẫn đường thời gian thực nằm ngoài phạm vi đồ án nên được giao cho ứng dụng bản đồ ngoài đảm nhiệm.

#### 4.2.9. Luồng xử lý thanh toán qua cổng sandbox

Sau khi đơn đặt tour/đặt phòng được tạo, hệ thống chuyển hướng người dùng đến cổng thanh toán sandbox kèm mã đơn và số tiền cần thanh toán; sau khi thanh toán thử nghiệm hoàn tất, hệ thống nhận kết quả giao dịch qua địa chỉ trả về, xác thực chữ ký, và cập nhật trạng thái đơn tương ứng.

#### 4.2.10. Mã hóa dữ liệu nhạy cảm của khách hàng

Số điện thoại liên hệ của khách hàng được mã hóa trước khi lưu vào cơ sở dữ liệu bằng thuật toán mã hóa đối xứng Fernet (xây dựng trên AES), khóa mã hóa được lưu tách biệt khỏi cơ sở dữ liệu qua biến môi trường, đảm bảo dữ liệu không thể đọc trực tiếp nếu cơ sở dữ liệu bị truy cập trái phép.

#### 4.2.11. Tìm kiếm chỗ ở trong bán kính bằng truy vấn không gian PostGIS

Tọa độ của điểm đến và chỗ ở được lưu dưới dạng kiểu dữ liệu không gian Point (PostGIS). Khi người dùng chọn xem các chỗ ở xung quanh một điểm đến trong bán kính tự chọn, hệ thống thực hiện truy vấn không gian trực tiếp trong cơ sở dữ liệu bằng hàm khoảng cách của PostGIS, lọc và sắp xếp theo khoảng cách tăng dần, tận dụng chỉ mục không gian (spatial index) để tính toán hiệu quả ngay ở tầng cơ sở dữ liệu.

## 5. Thời gian thực hiện

Từ ngày 24/08/2026 đến ngày 04/12/2026, theo đúng Thông báo số ngày 24/08/2026 của Khoa Công nghệ thông tin về việc tổ chức thực hiện môn học Đồ án chuyên ngành, thực hiện tại Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh.

## 6. Kết quả dự kiến đạt được

- Xây dựng hoàn chỉnh một website đặt tour du lịch thông minh tích hợp AI, ứng dụng các giải thuật và mô hình đã trình bày.
- Chức năng so khớp sở thích người dùng với điểm đến, xử lý được sở thích diễn đạt bằng ngôn ngữ tự nhiên.
- Chức năng chấm điểm mức độ phù hợp thời tiết tại đúng thời điểm dự kiến di chuyển.
- Chức năng tổng hợp và xếp hạng gợi ý điểm đến, có thể giải thích từng bước tính điểm; trọng số các tiêu chí được tự động điều chỉnh dựa trên phản hồi của người dùng.
- Chức năng giải thích gợi ý bằng ngôn ngữ tự nhiên
- Chức năng đặt tour, đặt phòng và thanh toán trực tuyến, không bị đặt trùng khi nhiều người dùng thao tác đồng thời; hỗ trợ hủy đơn kèm hoàn tiền qua sandbox.
- Chức năng bảo mật thông tin khách hàng bằng mã hóa Fernet.
- Chức năng tìm chỗ ở theo bán kính và chỉ đường thông minh.
- Chức năng trò chuyện thời gian thực (chat realtime) giữa người dùng và quản trị viên, sử dụng hạ tầng Redis kết hợp Django Channels.
- Chức năng đăng tin chia sẻ đánh giá, trải nghiệm chuyến đi quy mô nhỏ và đánh giá chỗ ở sau khi lưu trú.
- Đối với người dùng: đăng ký/đăng nhập; thiết lập sở thích và ngân sách; nhận gợi ý điểm đến kèm giải thích bằng AI; đặt tour theo lịch trình nhiều ngày; đặt phòng có kiểm tra chỗ trống thời gian thực; thanh toán trực tuyến; xem chỉ đường thông minh và tìm chỗ ở theo bán kính; trò chuyện thời gian thực với quản trị viên; đăng tin và đánh giá chỗ ở sau khi lưu trú.
- Đối với quản trị viên: quản lý (thêm/sửa/xóa) dữ liệu điểm đến, tour, chỗ ở, loại phòng và tiện ích; quản lý và cập nhật trạng thái đơn đặt tour/đặt phòng, xử lý hủy đơn và hoàn tiền; xem thống kê lượt tìm kiếm và điểm đến được gợi ý nhiều nhất.
- Hoàn thành báo cáo khóa luận đầy đủ theo đúng yêu cầu và định dạng của Khoa Công nghệ thông tin, Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh.
# II. NỘI DUNG

## LỜI MỞ ĐẦU

## CHƯƠNG 1: TỔNG QUAN TÀI LIỆU

### 1.1. Khảo sát hiện trạng các ứng dụng đặt tour, gợi ý du lịch hiện có

### 1.2. Cơ sở lý thuyết về hệ thống gợi ý, embedding ngôn ngữ tự nhiên và logic mờ

### 1.3. Giới thiệu công nghệ và công cụ sử dụng

## CHƯƠNG 2: PHƯƠNG PHÁP THỰC HIỆN

### 2.1. Phân tích yêu cầu hệ thống

### 2.2. Thiết kế cơ sở dữ liệu (ERD)

### 2.3. Thiết kế kiến trúc hệ thống

### 2.4. Thiết kế thuật toán gợi ý và các giải thuật liên quan

### 2.5. Thiết kế giao diện người dùng

## CHƯƠNG 3: CÀI ĐẶT THỰC NGHIỆM

### 3.1. Cài đặt môi trường và xây dựng các module chức năng

### 3.2. Kiểm thử và đánh giá kết quả

## KẾT LUẬN

# III. DỰ KIẾN KẾ HOẠCH THỰC HIỆN

| Tuần | Thời gian | Nội dung | Địa điểm thực hiện |
|---:|---|---|---|
| 1 | 24/08/2026 – 30/08/2026 | Đăng ký GVHD, đề tài; tìm hiểu đề tài; khảo sát hiện trạng các ứng dụng đặt tour/gợi ý du lịch hiện có; chuẩn bị hồ sơ đăng ký. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 2 | 31/08/2026 – 06/09/2026 | Đăng ký GVHD, đề tài; hoàn tất đăng ký GVHD và tên đề tài trước hạn chót của Khoa (04/09/2026). | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 3 | 07/09/2026 – 13/09/2026 | Nộp quyển đề cương; hoàn thiện và nộp quyển đề cương cho Văn phòng Khoa (10–11/09/2026). | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 4 | 14/09/2026 – 20/09/2026 | Khảo sát nghiệp vụ, xác định yêu cầu và tác nhân; thiết kế cơ sở dữ liệu gồm các thực thể tour, chỗ ở, phòng, đơn đặt, giao dịch thanh toán; hệ thống tổng thể và giao diện các màn hình chính. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 5 | 21/09/2026 – 27/09/2026 | Cài đặt môi trường phát triển; xây dựng module quản lý người dùng, sở thích cá nhân và tích hợp API thời tiết. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 6 | 28/09/2026 – 04/10/2026 | Xây dựng module quản lý điểm đến và thuật toán gợi ý đa tiêu chí (embedding sở thích, logic mờ thời tiết, ngân sách, khoảng cách, tổng hợp trọng số). | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 7 | 05/10/2026 – 11/10/2026 | Xây dựng module quản lý tour, chỗ ở, tồn kho phòng (admin) và module đặt tour/đặt phòng có kiểm tra chỗ trống. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 8 | 12/10/2026 – 18/10/2026 | Tích hợp cổng thanh toán sandbox; tích hợp OpenRouteService và PostGIS cho chỉ đường, tìm chỗ ở theo bán kính; hoàn thiện giao diện người dùng. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 9 | 19/10/2026 – 25/10/2026 | Kiểm thử chức năng (unit test, kiểm thử tích hợp API, kiểm thử luồng đặt tour/đặt phòng – thanh toán sandbox); sửa lỗi phát sinh. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 10 | 26/10/2026 – 01/11/2026 | Kiểm thử hiệu năng hệ thống gợi ý; đánh giá độ chính xác/phù hợp của kết quả gợi ý trên dữ liệu thực tế. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 11 | 02/11/2026 – 08/11/2026 | Hoàn thiện các dashboard, báo cáo, thông báo, chat realtime và bản tin. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 12 | 09/11/2026 – 15/11/2026 | Viết báo cáo đồ án: Chương 1 (Tổng quan tài liệu), Chương 2 (Phương pháp thực hiện), Chương 3 (Cài đặt thực nghiệm) và phần Kết luận. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 13 | 16/11/2026 – 22/11/2026 | Kiểm thử và hoàn thiện khóa luận theo quy định của Khoa; rà soát toàn bộ hệ thống; chuẩn bị slide bảo vệ. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 14 | 23/11/2026 – 29/11/2026 | Báo cáo đồ án trước Hội đồng theo lịch của Khoa. | Trường ĐH Tài nguyên và Môi trường TP.HCM |
| 15 | 30/11/2026 – 06/12/2026 | Nộp file báo cáo; chỉnh sửa theo góp ý của Hội đồng; nộp file báo cáo hoàn chỉnh. | Trường ĐH Tài nguyên và Môi trường TP.HCM |

# IV. TÀI LIỆU THAM KHẢO

[1] J. Yoon and C. Choi, "Real-Time Context-Aware Recommendation System for Tourism," Sensors, vol. 23, no. 7, Art. no. 3679, 2023.

[2] K. Chrysafiadi, A. Kontogianni, M. Virvou, and E. Alepis, "Enhancing User Experience in Smart Tourism via Fuzzy Logic-Based Personalization," Mathematics, vol. 13, no. 5, Art. no. 846, 2025.

[3] N. Reimers and I. Gurevych, "Sentence-BERT: Sentence Embeddings using Siamese BERT-Networks," in Proc. 2019 Conf. Empirical Methods in Natural Language Processing and 9th Int. Joint Conf. Natural Language Processing (EMNLP-IJCNLP), Hong Kong, China, 2019, pp. 3982–3992.

[4] J. Lu, "Personalized Recommendation Algorithm of Smart Tourism Based on Cross-Media Big Data and Neural Network," Computational Intelligence and Neuroscience, vol. 2022, Art. no. 9566766, 2022.

[5] Y. Rafique, J. Wu, A. W. Muzaffar, and B. Rafique, "An Enhanced Integrated Fuzzy Logic-Based Deep Learning Techniques (EIFL-DL) for the Recommendation System on Industrial Applications," PeerJ Computer Science, vol. 10, Art. no. e2529, 2024.

[6] N. L. U. Minh and N. M. Tâm, "Ứng dụng Trí tuệ Nhân tạo trong Du lịch," Tạp chí Khoa học Trường Đại học Phan Thiết, vol. 2, no. 4, 2024.

[7] Django Software Foundation, “Django documentation,” version 5.2. [Trực tuyến]. Địa chỉ: https://docs.djangoproject.com/en/5.2/. [Truy cập: 13/09/2026].

[8] Django REST framework, “Django REST framework.” [Trực tuyến]. Địa chỉ: https://www.django-rest-framework.org/. [Truy cập: 13/09/2026].

[9] The PostgreSQL Global Development Group, “PostgreSQL documentation.” [Trực tuyến]. Địa chỉ: https://www.postgresql.org/docs/current/index.html. [Truy cập: 13/09/2026].

[10] Google, “Models,” Gemini API. [Trực tuyến]. Địa chỉ: https://ai.google.dev/gemini-api/docs/models. [Truy cập: 13/09/2026].

[11] Django Software Foundation, “GeoDjango,” Django documentation, version 5.2. [Trực tuyến]. Địa chỉ: https://docs.djangoproject.com/en/5.2/ref/contrib/gis/. [Truy cập: 13/09/2026].

[12] PostGIS Project, “ST_DWithin,” PostGIS documentation. [Trực tuyến]. Địa chỉ: https://postgis.net/docs/ST_DWithin.html. [Truy cập: 13/09/2026].

[13] V. Agafonkin and Leaflet contributors, “Leaflet API reference.” [Trực tuyến]. Địa chỉ: https://leafletjs.com/reference.html. [Truy cập: 13/09/2026].

# V. CÁC CƠ QUAN, ĐƠN VỊ CẦN LIÊN HỆ

Khoa Công nghệ Thông tin – Trường Đại học Tài nguyên và Môi trường TP. Hồ Chí Minh, 236B Lê Văn Sỹ, Phường Tân Sơn Hòa, TP. Hồ Chí Minh.

TRƯỞNG BỘ MÔN


---

> **Ghi chú:** Tài liệu này được chuẩn hóa từ đề cương gốc sang Markdown, giữ nguyên nội dung chuyên môn và thuật ngữ của bản gốc; thay đổi chủ yếu ở cách trình bày để thuận tiện đọc trên GitHub và VS Code.

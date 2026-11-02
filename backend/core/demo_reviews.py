"""Pure, bounded generation of demonstration accommodation reviews."""

COMMON_OPENERS = (
    'Mình có một kỳ nghỉ khá dễ chịu tại nơi lưu trú này.',
    'Nhìn chung chuyến đi diễn ra đúng như nhóm mình mong đợi.',
    'Đây là một lựa chọn phù hợp với lịch trình ngắn của mình.',
    'Mình thích cách chuyến đi vẫn có đủ thời gian để nghỉ ngơi.',
    'Sau vài ngày lưu trú, mình có nhiều cảm nhận tích cực.',
    'Nơi nghỉ đáp ứng những nhu cầu cơ bản của chuyến đi.',
    'Trải nghiệm lưu trú giúp mình giữ lịch trình khá thoải mái.',
    'Mình đã có một khoảng thời gian nghỉ ngơi nhẹ nhàng.',
    'Chuyến đi này để lại cho mình nhiều kỷ niệm vui.',
    'Cả nhóm thấy việc sắp xếp chỗ nghỉ tương đối thuận tiện.',
    'Kỳ lưu trú phù hợp với cách mình lên kế hoạch chuyến đi.',
    'Mình thấy lựa chọn này hợp với nhu cầu của nhóm mình.',
)

COMMON_DETAILS = (
    'Phòng được sắp xếp gọn gàng khi nhóm mình nhận phòng.',
    'Mình đánh giá cao cảm giác sạch sẽ trong thời gian ở.',
    'Các vật dụng cơ bản đủ dùng cho chuyến đi ngắn.',
    'Thủ tục nhận phòng khá dễ theo dõi.',
    'Việc trả phòng diễn ra thuận lợi với lịch trình của mình.',
    'Nhân viên trao đổi rõ ràng khi mình hỏi thông tin.',
    'Cách hỗ trợ của nhân viên tạo cảm giác dễ chịu.',
    'Chi phí nằm trong khoảng nhóm mình dự tính.',
    'Mức giá phù hợp với nhu cầu nghỉ ngơi của mình.',
    'Mình có thể sắp xếp thời gian đi lại tương đối linh hoạt.',
    'Vị trí phù hợp với kế hoạch tham quan của nhóm.',
    'Không gian nghỉ ngơi giúp mình thư giãn sau ngày dài.',
    'Phòng có đủ chỗ cho những đồ dùng cần mang theo.',
    'Thông tin tiện ích giúp mình chuẩn bị trước chuyến đi.',
    'Mình thích cảm giác yên tĩnh khi trở về phòng.',
    'Bữa sáng là một phần dễ chịu trong buổi đầu ngày.',
    'Việc đặt phòng không mất nhiều thời gian tìm hiểu.',
    'Mình thấy thời gian lưu trú trôi qua khá thoải mái.',
    'Nhóm mình có thể nghỉ ngơi trước khi tiếp tục lịch trình.',
    'Cách bố trí phòng giúp việc sử dụng khá thuận tiện.',
    'Mình thích có khoảng riêng để sắp xếp lại hành lý.',
    'Giá cả và nhu cầu của mình khá cân đối.',
    'Đường đi trong lịch trình của nhóm được sắp xếp hợp lý.',
    'Mình nhận được thông tin cần thiết trước ngày đến.',
    'Phần lớn thời gian ở đây đúng với kỳ vọng ban đầu.',
    'Những lúc nghỉ giữa các hoạt động khá thoải mái.',
    'Mình có thêm thời gian xem lại kế hoạch cho hôm sau.',
    'Không gian chung tạo cảm giác gần gũi.',
    'Tốc độ phản hồi khi hỏi thông tin khiến mình yên tâm.',
    'Mình sẽ cân nhắc lựa chọn tương tự cho chuyến sau.',
)

CATEGORY_OPENERS = {
    'biển': (
        'Chuyến đi biển lần này cho mình dịp nghỉ ngơi đúng nghĩa.',
        'Mình chọn một lịch trình nhẹ nhàng cho kỳ nghỉ ven biển.',
        'Cả nhóm có thời gian tận hưởng chuyến đi biển theo nhịp riêng.',
        'Sau những hoạt động bên biển, mình mong có chỗ nghỉ thoải mái.',
    ),
    'núi': (
        'Chuyến đi vùng núi khiến mình muốn dành thêm thời gian nghỉ ngơi.',
        'Mình lên lịch trình vừa sức cho những ngày ở vùng núi.',
        'Sau một ngày khám phá, mình thấy việc nghỉ ngơi rất cần thiết.',
        'Cả nhóm đi vùng núi với mong muốn đổi không khí vài hôm.',
    ),
    'thành phố': (
        'Mình dành vài ngày khám phá thành phố theo nhịp riêng.',
        'Chuyến đi phố lần này có lịch trình khá linh hoạt.',
        'Cả nhóm chọn một nơi nghỉ để dễ chia thời gian tham quan.',
        'Mình muốn có một điểm dừng sau những buổi dạo quanh thành phố.',
    ),
    'ẩm thực': (
        'Chuyến đi này mình dành nhiều thời gian tìm hiểu ẩm thực địa phương.',
        'Cả nhóm lên kế hoạch thưởng thức món ăn theo sở thích.',
        'Sau những bữa ăn và giờ dạo chơi, mình muốn nghỉ ngơi thoải mái.',
        'Mình thích cách chuyến đi kết hợp khám phá và nghỉ ngơi.',
    ),
}

CATEGORY_DETAILS = {
    'biển': (
        'Mình dành phần lớn ngày cho các hoạt động ngoài trời.',
        'Lịch nghỉ xen kẽ thời gian khám phá biển khá hợp với nhóm.',
        'Về chỗ nghỉ sau một ngày đi biển là lúc mình thư giãn nhất.',
        'Mình chủ động xem thời tiết trước khi sắp xếp lịch ra ngoài.',
        'Nhóm mình có đủ thời gian nghỉ giữa các buổi tham quan.',
        'Mình thích kết thúc ngày đi chơi bằng một buổi tối thong thả.',
        'Kế hoạch đi biển không quá dày nên kỳ nghỉ khá nhẹ nhàng.',
        'Chỗ nghỉ giúp nhóm mình chuẩn bị đồ cho ngày kế tiếp.',
    ),
    'núi': (
        'Mình dành thời gian nghỉ trước khi tiếp tục lịch trình hôm sau.',
        'Nhóm mình ưu tiên nhịp di chuyển vừa sức trong chuyến đi.',
        'Sau những đoạn đường dài, có nơi nghỉ là điều rất đáng quý.',
        'Mình kiểm tra dự báo thời tiết trước mỗi ngày tham quan.',
        'Kế hoạch được chia nhỏ nên cả nhóm không thấy vội.',
        'Mình thấy thoải mái khi có thời gian chuẩn bị cho buổi sáng.',
        'Những lúc nghỉ giữa các chặng giúp chuyến đi dễ chịu hơn.',
        'Mình mang hành lý vừa đủ để di chuyển gọn nhẹ.',
    ),
    'thành phố': (
        'Mình dành thời gian đi bộ và quan sát nhịp sống xung quanh.',
        'Lịch trình tham quan được chia theo từng buổi.',
        'Nhóm mình chủ động chọn giờ đi lại phù hợp.',
        'Mình thích quay về nghỉ trước khi ra ngoài buổi tối.',
        'Việc có chỗ để đồ giúp mình di chuyển gọn hơn.',
        'Mình cân đối giữa thời gian tham quan và nghỉ ngơi.',
        'Một ngày không quá kín lịch khiến chuyến đi thoải mái hơn.',
        'Nhóm mình có thể đổi kế hoạch khi cần mà không quá gấp.',
    ),
    'ẩm thực': (
        'Mình để trống vài khung giờ để thử món ăn theo gợi ý của bạn bè.',
        'Cả nhóm bàn trước về ngân sách dành cho các bữa ăn.',
        'Lịch nghỉ xen kẽ việc khám phá món ăn khá hợp với mình.',
        'Mình thích tìm hiểu món ăn theo cách tự nhiên, không vội.',
        'Sau mỗi buổi đi ăn, nhóm mình có thời gian nghỉ ngơi.',
        'Việc chọn quán ăn được cả nhóm thống nhất trước mỗi buổi.',
        'Mình ghi lại vài trải nghiệm ẩm thực để nhớ chuyến đi.',
        'Lịch trình vừa phải giúp mình tận hưởng mỗi bữa ăn hơn.',
    ),
}


def review_category(category):
    if category in ('biển', 'nghỉ dưỡng', 'đảo'):
        return 'biển'
    if category in ('núi', 'thiên nhiên', 'mạo hiểm'):
        return 'núi'
    if category == 'ẩm thực':
        return 'ẩm thực'
    return 'thành phố'


def review_sentence_pool(category):
    kind = review_category(category)
    return COMMON_OPENERS + CATEGORY_OPENERS[kind], COMMON_DETAILS + CATEGORY_DETAILS[kind]


def generate_review_comment(category, rng, used_comments, max_attempts=24):
    """Return a locally unique 2–3 sentence review without mutating inputs.

    The finite fallback has more candidates than `used_comments`, so it must
    terminate even if every random candidate is already present.
    """
    openers, details = review_sentence_pool(category)
    for _ in range(max_attempts):
        sentence_count = rng.randint(2, 3)
        candidate = ' '.join((rng.choice(openers), *rng.sample(details, sentence_count - 1)))
        if candidate not in used_comments:
            return candidate

    for number in range(len(used_comments) + 1):
        candidate = f'{openers[0]} {details[0]} Mình lưu lại ghi chú số {number + 1} cho chuyến đi này.'
        if candidate not in used_comments:
            return candidate
    raise AssertionError('Không thể tạo bình luận duy nhất trong phạm vi chỗ ở.')

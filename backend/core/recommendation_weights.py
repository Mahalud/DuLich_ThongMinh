"""Các hàm học trọng số đơn giản, minh bạch cho hệ thống gợi ý."""

from .models import RecommendationFeedback, UserCriteriaWeight


DEFAULT_WEIGHTS = {'w1': 0.4, 'w2': 0.25, 'w3': 0.2, 'w4': 0.15}
MIN_FEEDBACK_FOR_ADAPTATION = 5
WEIGHT_STEP = 0.02
MIN_WEIGHT = 0.1
MAX_WEIGHT = 0.6

_SCORE_FIELDS = (
    ('w1', 'preference_score'),
    ('w2', 'weather_score'),
    ('w3', 'budget_score'),
    ('w4', 'distance_score'),
)


def weights_as_dict(weight_record):
    """Chuyển bản ghi trọng số sang dict để dùng trong response và công thức."""
    return {key: float(getattr(weight_record, key)) for key in DEFAULT_WEIGHTS}


def get_user_weights(user):
    """Trả trọng số cá nhân hóa chỉ khi người dùng đã có đủ phản hồi có điểm."""
    if not user or not user.is_authenticated:
        return DEFAULT_WEIGHTS.copy()

    scored_feedback_count = RecommendationFeedback.objects.filter(
        user=user,
        preference_score__isnull=False,
        weather_score__isnull=False,
        budget_score__isnull=False,
        distance_score__isnull=False,
    ).count()
    if scored_feedback_count < MIN_FEEDBACK_FOR_ADAPTATION:
        return DEFAULT_WEIGHTS.copy()

    weight_record, _ = UserCriteriaWeight.objects.get_or_create(user=user)
    return weights_as_dict(weight_record)


def recalculate_user_weights(user):
    """Cập nhật trọng số gợi ý của một người dùng theo phản hồi đã ghi nhận.

    Các bước được giữ cố ý đơn giản để dễ giải thích:
    1. Chỉ dùng phản hồi có đủ bốn điểm thành phần và chỉ bắt đầu từ 5 phản hồi.
    2. Tính trung bình từng điểm của hai nhóm ``booked`` và ``ignored``.
    3. Với mỗi tiêu chí, lấy chênh lệch trung bình ``booked - ignored``.
       Tiêu chí có chênh lệch lớn nhất là tiêu chí có tín hiệu tích cực mạnh nhất.
    4. Tăng trọng số tiêu chí đó 0,02, tối đa 0,6; đồng thời giảm 0,02 ở
       tiêu chí khác đang có trọng số cao nhất, tối thiểu 0,1. Vì tăng và
       giảm cùng lượng nên tổng bốn trọng số luôn bằng 1.

    Nếu chưa có đủ dữ liệu ở cả hai nhóm hoặc không thể dịch chuyển trong
    giới hạn, hàm giữ nguyên trọng số hiện tại.
    """
    weight_record, _ = UserCriteriaWeight.objects.get_or_create(user=user)
    feedback = RecommendationFeedback.objects.filter(
        user=user,
        preference_score__isnull=False,
        weather_score__isnull=False,
        budget_score__isnull=False,
        distance_score__isnull=False,
    )
    if feedback.count() < MIN_FEEDBACK_FOR_ADAPTATION:
        return weight_record

    booked = list(feedback.filter(action='booked'))
    ignored = list(feedback.filter(action='ignored'))
    if not booked or not ignored:
        return weight_record

    differences = {}
    for weight_name, score_name in _SCORE_FIELDS:
        booked_average = sum(getattr(item, score_name) for item in booked) / len(booked)
        ignored_average = sum(getattr(item, score_name) for item in ignored) / len(ignored)
        differences[weight_name] = booked_average - ignored_average

    winner = max(differences, key=differences.get)
    if differences[winner] <= 0 or getattr(weight_record, winner) >= MAX_WEIGHT:
        return weight_record

    donor_candidates = [
        key for key in DEFAULT_WEIGHTS
        if key != winner and getattr(weight_record, key) > MIN_WEIGHT
    ]
    if not donor_candidates:
        return weight_record
    donor = max(donor_candidates, key=lambda key: getattr(weight_record, key))
    adjustment = min(
        WEIGHT_STEP,
        MAX_WEIGHT - getattr(weight_record, winner),
        getattr(weight_record, donor) - MIN_WEIGHT,
    )
    if adjustment <= 0:
        return weight_record

    setattr(weight_record, winner, round(getattr(weight_record, winner) + adjustment, 6))
    setattr(weight_record, donor, round(getattr(weight_record, donor) - adjustment, 6))
    weight_record.full_clean()
    weight_record.save(update_fields=[winner, donor])
    return weight_record


def record_booked_feedback(user, destination):
    """Ghi nhận đặt chỗ thành công, sao chép điểm từ lần xem gợi ý gần nhất."""
    latest_view = RecommendationFeedback.objects.filter(
        user=user,
        destination=destination,
        action='viewed_detail',
        preference_score__isnull=False,
    ).order_by('-created_at').first()
    if not latest_view:
        latest_view = RecommendationFeedback.objects.filter(
            user=user,
            destination=destination,
            preference_score__isnull=False,
        ).order_by('-created_at').first()
    score_values = {
        score_name: getattr(latest_view, score_name) if latest_view else None
        for _, score_name in _SCORE_FIELDS
    }
    feedback = RecommendationFeedback.objects.create(
        user=user,
        destination=destination,
        action='booked',
        **score_values,
    )
    recalculate_user_weights(user)
    return feedback


from django.conf import settings
from django.utils import timezone


def cancellation_refund_preview(booking, is_tour=False):
    """Return the single source of truth for cancellation eligibility and refund."""
    if booking.status == 'cancelled':
        return {
            'can_cancel': False,
            'refund_amount': 0,
            'refund_percent': 0,
            'message': 'Đơn đã được hủy.',
        }

    target_date = booking.departure.departure_date if is_tour else booking.check_in
    days_left = (target_date - timezone.localdate()).days
    minimum = settings.TOUR_CANCELLATION_MIN_DAYS if is_tour else settings.ROOM_CANCELLATION_MIN_DAYS
    full_refund_minimum = settings.TOUR_FULL_REFUND_MIN_DAYS if is_tour else settings.ROOM_FULL_REFUND_MIN_DAYS
    if days_left < minimum:
        message = 'Đã quá hạn hủy đơn tour.' if is_tour else 'Đã quá hạn hủy phòng.'
        return {'can_cancel': False, 'refund_amount': 0, 'refund_percent': 0, 'message': message}

    if booking.status != 'confirmed':
        return {
            'can_cancel': True,
            'refund_amount': 0,
            'refund_percent': 0,
            'message': 'Đơn chưa thanh toán nên không có khoản hoàn',
        }

    refund_percent = 100 if days_left >= full_refund_minimum else 50
    if is_tour:
        charge = int(booking.total_price or 0)
    else:
        nights = max(0, (booking.check_out - booking.check_in).days)
        charge = int(booking.room_type.base_price * nights)
    return {
        'can_cancel': True,
        'refund_amount': charge * refund_percent // 100,
        'refund_percent': refund_percent,
        'message': '',
    }

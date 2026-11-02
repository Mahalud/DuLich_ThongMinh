"""Send a Vietnamese SMTP test message to one recipient."""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email


class Command(BaseCommand):
    help = 'Gửi một email thử để kiểm tra cấu hình SMTP.'

    def add_arguments(self, parser):
        parser.add_argument('recipient', help='Địa chỉ email nhận thư thử')

    def handle(self, *args, **options):
        recipient = options['recipient'].strip()
        try:
            validate_email(recipient)
        except ValidationError as exc:
            raise CommandError('Địa chỉ email nhận không hợp lệ.') from exc

        try:
            sent = send_mail(
                'Thư thử từ hệ thống Đi Việt Nam',
                'Xin chào,\n\nĐây là thư thử từ hệ thống Đi Việt Nam để kiểm tra cấu hình gửi email.\n'
                'Bạn không cần trả lời thư này.\n',
                settings.DEFAULT_FROM_EMAIL,
                [recipient],
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError('Máy chủ SMTP không xác nhận đã gửi thư.')
        except Exception as exc:
            # An SMTP server may echo parts of a command in its error text.
            message = str(exc)
            password = settings.EMAIL_HOST_PASSWORD
            if password:
                message = message.replace(password, '[đã ẩn]')
            raise CommandError(f'Gửi thư thất bại ({type(exc).__name__}): {message}') from None

        self.stdout.write(self.style.SUCCESS('Đã gửi'))

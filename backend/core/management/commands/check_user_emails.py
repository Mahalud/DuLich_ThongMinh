"""Report missing and duplicate account emails without changing the database."""

from collections import defaultdict

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Chỉ in tài khoản thiếu email hoặc dùng chung email, không sửa dữ liệu.'

    def handle(self, *args, **options):
        missing = []
        by_email = defaultdict(list)
        users = get_user_model().objects.order_by('date_joined', 'pk').values(
            'pk', 'username', 'email', 'is_active', 'date_joined',
        )
        for user in users.iterator():
            email = (user['email'] or '').strip()
            if not email:
                missing.append(user)
            else:
                by_email[email.casefold()].append(user)

        self.stdout.write(f'Tài khoản không có email: {len(missing)}')
        for user in missing:
            self.stdout.write(f"  #{user['pk']} {user['username']} (hoạt động: {user['is_active']})")

        duplicates = {email: members for email, members in by_email.items() if len(members) > 1}
        self.stdout.write(f'Nhóm email trùng (không phân biệt hoa thường): {len(duplicates)}')
        for email, members in sorted(duplicates.items()):
            self.stdout.write(f'  {email}:')
            for user in members:
                self.stdout.write(f"    #{user['pk']} {user['username']} (hoạt động: {user['is_active']})")

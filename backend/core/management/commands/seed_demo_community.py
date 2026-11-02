import calendar
import random
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Avg
from django.utils import timezone

from core.demo_reviews import generate_review_comment
from core.models import (
    Accommodation,
    AccommodationReview,
    Booking,
    DemoAccommodationRatingSnapshot,
    Destination,
    RoomType,
    TravelPost,
    TravelPostLike,
    UserProfile,
)


User = get_user_model()
DEMO_USER_COUNT = 15
DEMO_POST_COUNT = 30
RANDOM_SEED = 20261012

DISPLAY_NAMES = [
    'Minh Anh', 'Hoàng Nam', 'Ngọc Hà', 'Tuấn Kiệt', 'Thảo Vy',
    'Quốc Bảo', 'Khánh Linh', 'Gia Huy', 'Phương Nhi', 'Đức Anh',
    'Mai Chi', 'Thanh Tùng', 'Bảo Ngọc', 'Hải Đăng', 'Thu Trang',
]

TITLE_PATTERNS = [
    'Một cuối tuần đáng nhớ ở {name}', 'Ghi lại chuyến đi đến {name}',
    'Vài điều mình thích tại {name}', 'Chuyến đi thư thả qua {name}',
    'Kỷ niệm nhỏ ở {name}', 'Lên kế hoạch khám phá {name}',
    'Một ngày nhiều cảm hứng tại {name}', 'Nhật ký hành trình: {name}',
    'Chia sẻ lịch trình ở {name}', 'Điều mình muốn kể về {name}',
    'Góc nhìn của mình về {name}', 'Một chuyến đi nhẹ nhàng đến {name}',
    'Cùng lưu lại hành trình {name}', 'Trải nghiệm cuối tuần tại {name}',
    'Một điểm dừng chân thú vị: {name}', 'Chuyến đi nhiều kỷ niệm ở {name}',
    'Gợi ý nhỏ cho ngày ở {name}', 'Hành trình chậm rãi tại {name}',
    'Cảm nhận sau chuyến ghé thăm {name}', 'Một lần khám phá {name}',
    'Thêm một dấu chân ở {name}', 'Kể chuyện chuyến đi {name}',
    'Ngày nghỉ của mình tại {name}', 'Những khoảnh khắc ở {name}',
    'Một hành trình thật dễ chịu: {name}', 'Đi và cảm nhận {name}',
    'Chuyến đi ngắn tới {name}', 'Lưu lại vài khoảnh khắc tại {name}',
    'Kinh nghiệm sắp xếp chuyến đi {name}', 'Một nơi đáng để dành thời gian: {name}',
]

POST_SENTENCES = [
    'Mình dành thời gian tìm hiểu trước và sắp xếp lịch trình vừa phải.',
    'Đi cùng bạn bè khiến những khoảnh khắc bình thường cũng trở nên đáng nhớ.',
    'Mình thích giữ lịch trình linh hoạt để có thời gian nghỉ ngơi.',
    'Ảnh chụp giúp mình lưu lại những góc nhìn rất riêng của chuyến đi.',
    'Một chút chuẩn bị trước chuyến đi giúp cả nhóm chủ động hơn.',
    'Mình ưu tiên chọn chỗ nghỉ phù hợp với ngân sách và nhu cầu của cả nhóm.',
    'Chuyến đi này nhắc mình rằng không cần lịch trình quá dày mới vui.',
    'Mình thường dành một khoảng trống trong ngày để tùy hứng khám phá.',
    'Cả nhóm thống nhất chi phí trước nên chuyến đi khá thoải mái.',
    'Mình sẽ lưu lại những gợi ý hữu ích để tham khảo cho lần sau.',
    'Điều mình nhớ nhất là cảm giác được tạm rời nhịp sống thường ngày.',
    'Mình chọn những hoạt động phù hợp với thời gian và sức khỏe của mọi người.',
    'Chia sẻ lại hành trình để bạn bè có thêm ý tưởng tham khảo.',
    'Nếu có dịp, mình muốn quay lại với nhiều thời gian hơn.',
    'Một lịch trình gọn giúp mình tận hưởng chuyến đi trọn vẹn hơn.',
]

def subtract_months(day, months):
    month_index = day.month - 1 - months
    year = day.year + month_index // 12
    month = month_index % 12 + 1
    return day.replace(year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1]))


class Command(BaseCommand):
    help = 'Tạo hoặc xóa người dùng, đơn, đánh giá và bài viết minh họa cho demo.'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Chỉ in số lượng dự kiến, không ghi dữ liệu.')
        parser.add_argument('--remove', action='store_true', help='Xóa dữ liệu do lệnh này tạo.')

    def handle(self, *args, **options):
        if options['remove']:
            self.remove_demo_data(dry_run=options['dry_run'])
            return
        self.seed_demo_data(dry_run=options['dry_run'])

    def _demo_users(self):
        return User.objects.filter(username__regex=r'^demo_user_[0-9]{2}$', profile__is_demo=True)

    def _expected_users(self):
        return [f'demo_user_{number:02d}' for number in range(1, DEMO_USER_COUNT + 1)]

    def _existing_demo_bookings(self):
        return Booking.objects.filter(user__in=self._demo_users())

    def seed_demo_data(self, dry_run=False):
        users = list(self._demo_users().order_by('username'))
        existing_names = set(User.objects.filter(username__in=self._expected_users()).values_list('username', flat=True))
        new_user_count = DEMO_USER_COUNT - len(existing_names)
        if dry_run:
            booking_total = 0
            review_total = 0
            for accommodation in Accommodation.objects.order_by('id'):
                room = RoomType.objects.filter(accommodation=accommodation).order_by('id').first()
                if room:
                    target_count = random.Random(f'{RANDOM_SEED}:accommodation:{accommodation.id}').randint(3, 6)
                    existing_count = self._existing_demo_bookings().filter(room_type__accommodation=accommodation).count()
                    booking_total += max(0, target_count - existing_count)
                    review_total += self._existing_demo_bookings().filter(
                        room_type__accommodation=accommodation, review__isnull=True,
                    ).count() + max(0, target_count - existing_count)
            destinations = list(Destination.objects.order_by('id'))
            posts_missing = 0
            if destinations:
                for index, pattern in enumerate(TITLE_PATTERNS):
                    title = pattern.format(name=destinations[index % len(destinations)].name)
                    user_name = self._expected_users()[(index * 7 + 2) % DEMO_USER_COUNT]
                    posts_missing += not TravelPost.objects.filter(user__username=user_name, title=title).exists()
            self.stdout.write(
                f'Dry-run: {new_user_count} người dùng mới; {booking_total} đơn và tối đa {review_total} đánh giá; '
                f'{posts_missing} bài viết còn thiếu (mục tiêu {DEMO_POST_COUNT}); lượt thích sẽ được tạo cho bài mới.'
            )
            return

        users = self._ensure_users()
        destinations = list(Destination.objects.order_by('id'))
        self._seed_reviews(users)
        self._seed_posts(users, destinations)
        self._recalculate_ratings()
        self.stdout.write(self.style.SUCCESS(
            f'Hoàn tất dữ liệu minh họa: {len(users)} người dùng, '
            f'{self._existing_demo_bookings().count()} đơn đặt phòng, '
            f'{AccommodationReview.objects.filter(user__in=users).count()} đánh giá, '
            f'{TravelPost.objects.filter(user__in=users).count()} bài viết.'
        ))

    def _ensure_users(self):
        users = []
        for index, username in enumerate(self._expected_users()):
            user, _ = User.objects.get_or_create(
                username=username,
                defaults={'first_name': DISPLAY_NAMES[index], 'last_name': ''},
            )
            # Reserved demo usernames must never become usable login accounts.
            user.first_name = DISPLAY_NAMES[index]
            user.last_name = ''
            user.set_unusable_password()
            user.save(update_fields=['first_name', 'last_name', 'password'])
            UserProfile.objects.update_or_create(user=user, defaults={'is_demo': True})
            users.append(user)
        return users

    def _seed_reviews(self, users):
        today = timezone.localdate()
        total = Accommodation.objects.count()
        for index, accommodation in enumerate(Accommodation.objects.select_related('destination').order_by('id'), start=1):
            print(f'[{index}/{total}] Đang tạo đánh giá: {accommodation.name}', file=self.stdout, flush=True)
            rng = random.Random(f'{RANDOM_SEED}:accommodation:{accommodation.id}')
            rooms = list(RoomType.objects.filter(accommodation=accommodation).order_by('id'))
            if not rooms:
                self.stdout.write(self.style.WARNING(f'Bỏ qua đánh giá cho {accommodation.name}: chưa có loại phòng.'))
                print(f'[{index}/{total}] Đã tạo 0 đánh giá: {accommodation.name}', file=self.stdout, flush=True)
                continue
            # Capture before the first write. A later interrupted run must not
            # replace this value with a partially recalculated demo average.
            DemoAccommodationRatingSnapshot.objects.get_or_create(
                accommodation=accommodation,
                defaults={'rating': accommodation.rating},
            )
            target_count = rng.randint(3, 6)
            existing = list(self._existing_demo_bookings().filter(room_type__accommodation=accommodation).order_by('id'))
            needed = max(0, target_count - len(existing))
            bookings = []
            for offset in range(needed):
                sequence = len(existing) + offset
                user = users[(accommodation.id + sequence) % len(users)]
                months_ago = rng.randint(1, 6)
                check_in = subtract_months(today, months_ago) + timedelta(days=rng.randint(0, 12))
                check_out = check_in + timedelta(days=rng.randint(1, 4))
                bookings.append(Booking(
                    user=user,
                    room_type=rooms[sequence % len(rooms)],
                    check_in=check_in,
                    check_out=check_out,
                    guest_phone='',
                    status='confirmed',
                    refund_amount=Decimal('0'),
                    refund_status='none',
                ))
            if bookings:
                # Intentionally bypass Booking.save()/full_clean(): these are
                # historical demonstration stays and must not alter room stock.
                Booking.objects.bulk_create(bookings)
                created = list(self._existing_demo_bookings().filter(
                    room_type__accommodation=accommodation,
                    review__isnull=True,
                ).order_by('-id')[:len(bookings)])
                created_ids = [booking.id for booking in created]
                if created_ids:
                    base_time = timezone.now()
                    Booking.objects.filter(id__in=created_ids).update(
                        created_at=base_time - timedelta(days=30 * 3),
                    )
            else:
                created_ids = []

            all_bookings = list(self._existing_demo_bookings().filter(
                room_type__accommodation=accommodation,
            ).order_by('id'))
            used_comments = set(AccommodationReview.objects.filter(
                accommodation=accommodation,
            ).exclude(comment='').values_list('comment', flat=True))
            review_rows = []
            review_dates = []
            for booking in all_bookings:
                if AccommodationReview.objects.filter(booking=booking).exists():
                    continue
                rating = rng.choices([5, 4, 3, 2], weights=[35, 40, 22, 3], k=1)[0]
                comment = generate_review_comment(
                    accommodation.destination.category if accommodation.destination else 'thành phố',
                    rng, used_comments,
                )
                used_comments.add(comment)
                review_rows.append(AccommodationReview(
                    accommodation=accommodation,
                    user=booking.user,
                    booking=booking,
                    rating=rating,
                    comment=comment,
                ))
                review_dates.append(booking.check_out + timedelta(days=rng.randint(1, 5)))
            if review_rows:
                AccommodationReview.objects.bulk_create(review_rows)
                new_reviews = list(AccommodationReview.objects.filter(
                    booking_id__in=[row.booking_id for row in review_rows],
                ).order_by('id'))
                now = timezone.now()
                for review, reviewed_on in zip(new_reviews, review_dates):
                    # Match the generated date offset to the historical stay.
                    AccommodationReview.objects.filter(pk=review.pk).update(
                        created_at=now - timedelta(days=max(1, (today - reviewed_on).days)),
                    )
            print(f'[{index}/{total}] Đã tạo {len(review_rows)} đánh giá: {accommodation.name}', file=self.stdout, flush=True)

    def _seed_posts(self, users, destinations):
        if not destinations:
            self.stdout.write(self.style.WARNING('Chưa có điểm đến; bỏ qua bài viết cộng đồng.'))
            return
        posts = []
        for index, pattern in enumerate(TITLE_PATTERNS):
            rng = random.Random(f'{RANDOM_SEED}:post:{index}')
            destination = destinations[index % len(destinations)]
            title = pattern.format(name=destination.name)
            user = users[(index * 7 + 2) % len(users)]
            existing = TravelPost.objects.filter(user=user, title=title).first()
            if existing:
                posts.append(existing)
                continue
            sentence_count = rng.randint(3, 6)
            sentences = rng.sample(POST_SENTENCES, sentence_count - 1)
            content = f'Mình vừa có dịp ghé {destination.name}. ' + ' '.join(sentences)
            image_url = destination.image_url or ''
            images = [image_url] if image_url else []
            post = TravelPost.objects.create(
                user=user,
                title=title,
                content=content,
                destination=destination,
                images=images[:3],
            )
            posted_on = timezone.now() - timedelta(days=rng.randint(0, 59), hours=rng.randint(0, 23))
            TravelPost.objects.filter(pk=post.pk).update(created_at=posted_on, updated_at=posted_on)
            posts.append(post)

        for post in posts:
            rng = random.Random(f'{RANDOM_SEED}:likes:{post.id}')
            candidates = [user for user in users if user.id != post.user_id]
            like_count = rng.randint(3, min(9, len(candidates))) if candidates else 0
            chosen = rng.sample(candidates, like_count) if like_count else []
            TravelPostLike.objects.bulk_create(
                [TravelPostLike(user=user, post=post) for user in chosen],
                ignore_conflicts=True,
            )
            post.likes_count = post.likes.count()
            post.save(update_fields=['likes_count'])

    def _recalculate_ratings(self):
        for accommodation in Accommodation.objects.all().iterator():
            if not AccommodationReview.objects.filter(accommodation=accommodation, user__profile__is_demo=True).exists():
                continue
            DemoAccommodationRatingSnapshot.objects.get_or_create(
                accommodation=accommodation,
                defaults={'rating': accommodation.rating},
            )
            average = AccommodationReview.objects.filter(accommodation=accommodation).aggregate(value=Avg('rating'))['value']
            Accommodation.objects.filter(pk=accommodation.pk).update(rating=float(average or 0))

    def remove_demo_data(self, dry_run=False):
        users = self._demo_users()
        user_ids = list(users.values_list('id', flat=True))
        posts = TravelPost.objects.filter(user_id__in=user_ids)
        post_ids = list(posts.values_list('id', flat=True))
        bookings = Booking.objects.filter(user_id__in=user_ids)
        reviews = AccommodationReview.objects.filter(user_id__in=user_ids)
        likes = TravelPostLike.objects.filter(user_id__in=user_ids) | TravelPostLike.objects.filter(post_id__in=post_ids)
        counts = {
            'người dùng': len(user_ids),
            'đơn đặt phòng': bookings.count(),
            'đánh giá': reviews.count(),
            'bài viết': posts.count(),
            'lượt thích': likes.distinct().count(),
        }
        if dry_run:
            self.stdout.write('Dry-run xóa: ' + ', '.join(f'{count} {label}' for label, count in counts.items()))
            return

        reviewed_accommodation_ids = set(reviews.values_list('accommodation_id', flat=True).distinct())
        snapshots = {
            item.accommodation_id: item.rating
            for item in DemoAccommodationRatingSnapshot.objects.all()
        }
        affected_accommodation_ids = reviewed_accommodation_ids | set(snapshots)
        TravelPostLike.objects.filter(user_id__in=user_ids).delete()
        posts.delete()
        # Delete review rows explicitly before bookings; their booking FK is nullable.
        reviews.delete()
        bookings.delete()
        users.delete()
        for accommodation in Accommodation.objects.filter(id__in=affected_accommodation_ids):
            if accommodation.pk in snapshots:
                Accommodation.objects.filter(pk=accommodation.pk).update(rating=snapshots[accommodation.pk])
            else:
                average = AccommodationReview.objects.filter(accommodation=accommodation).aggregate(value=Avg('rating'))['value']
                Accommodation.objects.filter(pk=accommodation.pk).update(rating=float(average or 0))
        DemoAccommodationRatingSnapshot.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(
            'Đã xóa dữ liệu minh họa: ' + ', '.join(f'{count} {label}' for label, count in counts.items())
        ))

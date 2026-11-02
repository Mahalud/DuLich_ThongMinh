from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


DEFAULT_SECTIONS = [
    {
        'title': 'Du lịch phù hợp với bạn',
        'content': 'Đi Việt Nam giúp bạn khám phá điểm đến trong nước theo sở thích, thời gian và ngân sách. Hệ thống tổng hợp thông tin để bạn tham khảo trước khi lên kế hoạch.',
        'image_url': 'https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1200&q=80',
        'layout': 'image_right',
    },
    {
        'title': 'Cách gợi ý hoạt động',
        'content': '- Sở thích: đối chiếu chủ đề chuyến đi với đặc trưng điểm đến.\n- Thời tiết: dùng dự báo ngày đi và lựa chọn thời tiết mong muốn.\n- Ngân sách: so sánh chi phí tham khảo của điểm đến với ngân sách.\n- Khoảng cách: ước tính quãng đường từ vị trí xuất phát đã chọn.',
        'image_url': '',
        'layout': 'text',
    },
    {
        'title': 'Những chức năng chính',
        'content': 'Đặt phòng lưu trú · Tìm và đặt tour · Xem tuyến đường trên bản đồ · Trò chuyện với bộ phận hỗ trợ · Chia sẻ trải nghiệm cùng cộng đồng.',
        'image_url': '',
        'layout': 'cards',
    },
    {
        'title': 'Công nghệ sử dụng',
        'content': 'Ứng dụng được xây dựng với React và Django REST Framework. PostgreSQL/PostGIS lưu dữ liệu địa lý; Redis và Celery xử lý công việc nền; Django Channels hỗ trợ trò chuyện thời gian thực. Bản đồ sử dụng Leaflet và dữ liệu nền OpenStreetMap.',
        'image_url': '',
        'layout': 'text',
    },
    {
        'title': 'Liên hệ',
        'content': 'Bạn có thể gửi câu hỏi hoặc góp ý qua email: lienhe@example.com. Đây là địa chỉ minh họa trung tính dành cho nội dung mẫu của đồ án.',
        'image_url': '',
        'layout': 'image_left',
    },
    {
        'title': 'Thông tin về dữ liệu',
        'content': 'Đi Việt Nam là đồ án chuyên ngành. Dữ liệu chỗ ở và tour trên website mang tính minh họa để trình diễn chức năng; vui lòng kiểm tra thông tin thực tế trước khi đưa ra quyết định du lịch.',
        'image_url': '',
        'layout': 'text',
    },
]


def seed_about_page(apps, schema_editor):
    SitePage = apps.get_model('core', 'SitePage')
    SitePageSection = apps.get_model('core', 'SitePageSection')
    database = schema_editor.connection.alias
    page, _ = SitePage.objects.using(database).get_or_create(
        slug='gioi-thieu',
        defaults={
            'title': 'Về Đi Việt Nam',
            'cover_image_url': 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=2000&q=85',
            'intro': 'Một người bạn đồng hành giúp bạn tìm cảm hứng, khám phá điểm đến và sắp xếp chuyến đi theo cách của riêng mình.',
        },
    )
    for order, section in enumerate(DEFAULT_SECTIONS):
        SitePageSection.objects.using(database).get_or_create(
            page_id=page.pk,
            order=order,
            defaults=section,
        )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0017_weather_preference'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SitePage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=120, unique=True)),
                ('title', models.CharField(max_length=200)),
                ('cover_image_url', models.URLField(blank=True, default='', max_length=600)),
                ('intro', models.TextField(blank=True, default='')),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_site_pages', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['slug']},
        ),
        migrations.CreateModel(
            name='SitePageSection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(default=0)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField(blank=True, default='')),
                ('image_url', models.URLField(blank=True, default='', max_length=600)),
                ('layout', models.CharField(choices=[('text', 'Văn bản'), ('image_left', 'Ảnh trái'), ('image_right', 'Ảnh phải'), ('cards', 'Thẻ')], default='text', max_length=16)),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sections', to='core.sitepage')),
            ],
            options={'ordering': ['order', 'id']},
        ),
        migrations.RunPython(seed_about_page, migrations.RunPython.noop),
    ]

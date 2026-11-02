from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0007_accommodation_destination'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Tour',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('category', models.CharField(choices=[('kham_pha', 'Khám phá thiên nhiên'), ('van_hoa', 'Văn hóa - Lịch sử'), ('nghi_duong', 'Nghỉ dưỡng'), ('mao_hiem', 'Mạo hiểm'), ('am_thuc', 'Ẩm thực'), ('ghep_doan', 'Tour ghép đoàn'), ('rieng', 'Tour riêng')], default='kham_pha', max_length=20)),
                ('duration_days', models.PositiveIntegerField()),
                ('price_adult', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('price_child', models.DecimalField(blank=True, decimal_places=0, max_digits=12, null=True)),
                ('single_room_supplement', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('min_age', models.PositiveIntegerField(blank=True, null=True)),
                ('included_services', models.JSONField(blank=True, default=list)),
                ('excluded_services', models.JSONField(blank=True, default=list)),
                ('cancellation_policy', models.TextField(blank=True, default='')),
                ('price_per_person', models.DecimalField(blank=True, decimal_places=0, default=0, max_digits=12, null=True)),
                ('cover_image_url', models.URLField(blank=True, default='')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='TourStop',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day_number', models.PositiveIntegerField()),
                ('note', models.TextField(blank=True, default='')),
                ('destination', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.destination')),
                ('tour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stops', to='core.tour')),
            ],
            options={'ordering': ['day_number']},
        ),
        migrations.CreateModel(
            name='TourDeparture',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('departure_date', models.DateField()),
                ('slots_total', models.PositiveIntegerField()),
                ('is_cancelled', models.BooleanField(default=False)),
                ('tour', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='departures', to='core.tour')),
            ],
            options={'ordering': ['departure_date'], 'unique_together': {('tour', 'departure_date')}},
        ),
        migrations.CreateModel(
            name='TourBooking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('departure_date', models.DateField(blank=True, null=True)),
                ('num_guests', models.PositiveIntegerField(default=1)),
                ('num_adults', models.PositiveIntegerField(default=1)),
                ('num_children', models.PositiveIntegerField(default=0)),
                ('is_single_room', models.BooleanField(default=False)),
                ('total_price', models.DecimalField(decimal_places=0, max_digits=12)),
                ('guest_phone', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('cancelled', 'Cancelled')], default='pending', max_length=20)),
                ('refund_amount', models.DecimalField(decimal_places=0, default=0, max_digits=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('departure', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='core.tourdeparture')),
                ('tour', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='core.tour')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tour_bookings', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]

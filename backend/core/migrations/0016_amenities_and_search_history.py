from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def load_amenities(apps, schema_editor):
    Amenity = apps.get_model('core', 'Amenity')
    rows = [
        ('wifi', 'Wifi miễn phí', 'wifi'),
        ('dieu_hoa', 'Điều hòa', 'dieu_hoa'),
        ('bon_tam', 'Bồn tắm', 'bon_tam'),
        ('huong_bien', 'Hướng biển', 'huong_bien'),
        ('ho_boi', 'Hồ bơi', 'ho_boi'),
        ('bua_sang', 'Bữa sáng miễn phí', 'bua_sang'),
        ('do_xe', 'Chỗ đậu xe', 'do_xe'),
        ('thang_may', 'Thang máy', 'thang_may'),
        ('bep', 'Bếp riêng', 'bep'),
        ('giat_ui', 'Dịch vụ giặt ủi', 'giat_ui'),
        ('tivi', 'TV màn hình phẳng', 'tivi'),
        ('ban_cong', 'Ban công', 'ban_cong'),
    ]
    Amenity.objects.using(schema_editor.connection.alias).bulk_create([
        Amenity(key=key, label=label, icon_name=icon_name) for key, label, icon_name in rows
    ])


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0015_chat_conversation_rooms'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Amenity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.SlugField(db_index=True, max_length=80, unique=True)),
                ('label', models.CharField(max_length=120)),
                ('icon_name', models.CharField(choices=[
                    ('wifi', 'wifi'), ('dieu_hoa', 'dieu_hoa'), ('bon_tam', 'bon_tam'),
                    ('huong_bien', 'huong_bien'), ('ho_boi', 'ho_boi'), ('bua_sang', 'bua_sang'),
                    ('do_xe', 'do_xe'), ('thang_may', 'thang_may'), ('bep', 'bep'),
                    ('giat_ui', 'giat_ui'), ('tivi', 'tivi'), ('ban_cong', 'ban_cong'),
                ], default='wifi', max_length=40)),
            ],
            options={'ordering': ['label', 'key']},
        ),
        migrations.AddField(model_name='searchhistory', name='preferences', field=models.JSONField(blank=True, default=list)),
        migrations.AddField(model_name='searchhistory', name='budget_estimate', field=models.PositiveBigIntegerField(default=0)),
        migrations.AddField(model_name='searchhistory', name='latitude', field=models.FloatField(default=0)),
        migrations.AddField(model_name='searchhistory', name='longitude', field=models.FloatField(default=0)),
        migrations.AddField(model_name='searchhistory', name='travel_date', field=models.DateField(blank=True, null=True)),
        migrations.AddField(model_name='searchhistory', name='top_n', field=models.PositiveSmallIntegerField(default=5)),
        migrations.AddField(
            model_name='searchhistory', name='destination',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='search_history', to='core.destination'),
        ),
        migrations.RunPython(load_amenities, migrations.RunPython.noop),
    ]

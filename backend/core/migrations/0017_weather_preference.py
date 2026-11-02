from django.db import migrations, models


WEATHER_CHOICES = [
    ('balanced', 'Mặc định'),
    ('cool', 'Mát mẻ'),
    ('warm', 'Nắng ấm'),
    ('dry', 'Ít mưa'),
]


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0016_amenities_and_search_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='weather_preference',
            field=models.CharField(choices=WEATHER_CHOICES, default='balanced', max_length=12),
        ),
        migrations.AddField(
            model_name='searchhistory',
            name='weather_preference',
            field=models.CharField(choices=WEATHER_CHOICES, default='balanced', max_length=12),
        ),
    ]

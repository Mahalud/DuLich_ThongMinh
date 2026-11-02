from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_increase_image_url_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='address',
            field=models.CharField(blank=True, max_length=300),
        ),
        migrations.AddField(
            model_name='destination',
            name='reference_cost',
            field=models.PositiveIntegerField(default=0, help_text='Chi phí tham khảo cho chuyến 3 ngày 2 đêm, một người (VND).'),
        ),
    ]

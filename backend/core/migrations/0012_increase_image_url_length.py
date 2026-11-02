# Generated manually for longer external image URLs.
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_recommendationlog'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='image_url',
            field=models.URLField(blank=True, default='', max_length=600),
        ),
        migrations.AlterField(
            model_name='tour',
            name='cover_image_url',
            field=models.URLField(blank=True, default='', max_length=600),
        ),
    ]

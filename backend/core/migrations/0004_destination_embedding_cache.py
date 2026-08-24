from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_chatmessage'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='embedding_cache',
            field=models.JSONField(blank=True, null=True),
        ),
    ]
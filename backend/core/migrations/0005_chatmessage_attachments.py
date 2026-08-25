from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0004_destination_embedding_cache'),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='chat_attachments/%Y/%m/'),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='attachment_type',
            field=models.CharField(choices=[('none', 'Không có'), ('image', 'Ảnh'), ('video', 'Video')], default='none', max_length=10),
        ),
    ]
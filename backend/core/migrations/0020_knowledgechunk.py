from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0019_demo_community'),
    ]

    operations = [
        migrations.CreateModel(
            name='KnowledgeChunk',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('source_type', models.CharField(choices=[('destination', 'Điểm đến'), ('accommodation', 'Chỗ ở'), ('tour', 'Tour'), ('policy', 'Chính sách'), ('page', 'Trang nội dung')], max_length=24)),
                ('source_id', models.PositiveBigIntegerField()),
                ('title', models.CharField(max_length=240)),
                ('content', models.TextField()),
                ('url', models.CharField(max_length=300)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('content_hash', models.CharField(max_length=64)),
                ('embedding', models.JSONField(default=list)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['source_type', 'source_id'],
                'constraints': [models.UniqueConstraint(fields=('source_type', 'source_id'), name='unique_knowledge_chunk_source')],
            },
        ),
    ]

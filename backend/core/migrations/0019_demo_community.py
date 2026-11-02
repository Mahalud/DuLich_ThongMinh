from django.db import migrations, models
import django.db.models.deletion


def add_demo_disclosure(apps, schema_editor):
    SitePageSection = apps.get_model('core', 'SitePageSection')
    database = schema_editor.connection.alias
    sections = SitePageSection.objects.using(database).filter(
        page__slug='gioi-thieu', title='Thông tin về dữ liệu',
    )
    disclosure = ' Một số đánh giá và bài chia sẻ là dữ liệu minh họa phục vụ đồ án.'
    for section in sections:
        if disclosure.strip() not in section.content:
            section.content = f'{section.content}{disclosure}'
            section.save(update_fields=['content'])


class Migration(migrations.Migration):
    dependencies = [('core', '0018_site_pages')]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='is_demo',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='DemoAccommodationRatingSnapshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rating', models.FloatField(default=0)),
                ('accommodation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='demo_rating_snapshot', to='core.accommodation')),
            ],
        ),
        migrations.RunPython(add_demo_disclosure, migrations.RunPython.noop),
    ]

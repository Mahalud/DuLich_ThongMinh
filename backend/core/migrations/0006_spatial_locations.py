from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


def populate_spatial_locations(apps, schema_editor):
    Destination = apps.get_model('core', 'Destination')
    Accommodation = apps.get_model('core', 'Accommodation')
    for model in (Destination, Accommodation):
        for obj in model.objects.all().iterator():
            if obj.latitude is not None and obj.longitude is not None:
                obj.vi_tri = Point(obj.longitude, obj.latitude, srid=4326)
                obj.save(update_fields=['vi_tri'])


class Migration(migrations.Migration):
    dependencies = [('core', '0005_chatmessage_attachments')]

    operations = [
        CreateExtension('postgis'),
        migrations.AddField(
            model_name='destination',
            name='vi_tri',
            field=models.PointField(blank=True, null=True, spatial_index=True, srid=4326),
        ),
        migrations.AddField(
            model_name='accommodation',
            name='vi_tri',
            field=models.PointField(blank=True, null=True, spatial_index=True, srid=4326),
        ),
        migrations.RunPython(populate_spatial_locations, migrations.RunPython.noop),
    ]

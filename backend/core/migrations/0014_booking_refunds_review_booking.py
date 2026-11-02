from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0013_destination_address_reference_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='momo_trans_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='booking',
            name='refund_status',
            field=models.CharField(choices=[('none', 'Chưa hoàn'), ('pending', 'Đang hoàn'), ('refunded', 'Đã hoàn'), ('failed', 'Hoàn thất bại')], default='none', max_length=12),
        ),
        migrations.AddField(
            model_name='booking',
            name='refunded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tourbooking',
            name='momo_trans_id',
            field=models.CharField(blank=True, default='', max_length=64),
        ),
        migrations.AddField(
            model_name='tourbooking',
            name='refund_status',
            field=models.CharField(choices=[('none', 'Chưa hoàn'), ('pending', 'Đang hoàn'), ('refunded', 'Đã hoàn'), ('failed', 'Hoàn thất bại')], default='none', max_length=12),
        ),
        migrations.AddField(
            model_name='tourbooking',
            name='refunded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='accommodationreview',
            name='booking',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='review', to='core.booking'),
        ),
    ]

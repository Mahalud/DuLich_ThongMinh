from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('core', '0020_knowledgechunk')]

    operations = [
        *[
            migrations.AddField(
                model_name=model_name,
                name=field_name,
                field=field,
            )
            for model_name in ('booking', 'tourbooking')
            for field_name, field in (
                ('payment_provider', models.CharField(blank=True, default='', max_length=20)),
                ('payment_order_ref', models.CharField(blank=True, default='', max_length=100)),
                ('payment_transaction_id', models.CharField(blank=True, default='', max_length=64)),
                ('payment_create_date', models.CharField(blank=True, default='', max_length=14)),
                ('payment_pay_date', models.CharField(blank=True, default='', max_length=14)),
            )
        ],
    ]

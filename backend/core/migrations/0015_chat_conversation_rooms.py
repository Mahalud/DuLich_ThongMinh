from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def backfill_conversation_owner(apps, schema_editor):
    ChatMessage = apps.get_model('core', 'ChatMessage')
    User = apps.get_model(*settings.AUTH_USER_MODEL.split('.'))
    database = schema_editor.connection.alias
    messages = ChatMessage.objects.using(database).filter(conversation_user__isnull=True)
    for message in messages.iterator():
        sender = User.objects.using(database).filter(pk=message.sender_id).first()
        receiver = User.objects.using(database).filter(pk=message.receiver_id).first() if message.receiver_id else None
        if sender and sender.is_staff and receiver and not receiver.is_staff:
            owner_id = receiver.pk
        elif sender and not sender.is_staff:
            owner_id = sender.pk
        elif receiver and not receiver.is_staff:
            owner_id = receiver.pk
        else:
            owner_id = message.sender_id
        ChatMessage.objects.using(database).filter(pk=message.pk).update(
            conversation_user_id=owner_id,
            is_from_admin=bool(sender and sender.is_staff),
        )


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0014_booking_refunds_review_booking'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='chatmessage',
            name='conversation_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='chat_conversations', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='is_from_admin',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='chatmessage',
            name='is_read',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='receiver',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='received_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='chatmessage',
            name='attachment_type',
            field=models.CharField(choices=[('none', 'Không có'), ('image', 'Ảnh'), ('pdf', 'PDF')], default='none', max_length=10),
        ),
        migrations.RunPython(backfill_conversation_owner, migrations.RunPython.noop),
    ]

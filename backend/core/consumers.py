import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth import get_user_model
from django.conf import settings

from .models import ChatMessage

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        attachment_url = data.get('attachment_url', '').strip()
        attachment_type = data.get('attachment_type', 'none')
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')

        if not (message or attachment_url) or not sender_id or not receiver_id:
            return

        sender = await sync_to_async(User.objects.get)(id=sender_id)
        receiver = await sync_to_async(User.objects.get)(id=receiver_id)
        attachment_name = attachment_url.replace(settings.MEDIA_URL, '', 1).lstrip('/') if attachment_url else ''
        saved_message = await sync_to_async(ChatMessage.objects.create)(
            sender=sender,
            receiver=receiver,
            content=message,
            attachment=attachment_name,
            attachment_type=attachment_type if attachment_name else 'none',
        )

        event = {
            'type': 'chat_message',
            'message': {
                'id': saved_message.id,
                'sender': sender_id,
                'receiver': receiver_id,
                'content': saved_message.content,
                'attachment_url': attachment_url,
                'attachment_type': saved_message.attachment_type,
                'created_at': saved_message.created_at.isoformat(),
            },
        }

        await self.channel_layer.group_send(self.room_group_name, event)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

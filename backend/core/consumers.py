import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from django.contrib.auth import get_user_model

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
        sender_id = data.get('sender_id')
        receiver_id = data.get('receiver_id')

        if not message or not sender_id or not receiver_id:
            return

        sender = await sync_to_async(User.objects.get)(id=sender_id)
        receiver = await sync_to_async(User.objects.get)(id=receiver_id)
        saved_message = await sync_to_async(ChatMessage.objects.create)(
            sender=sender,
            receiver=receiver,
            content=message,
        )

        event = {
            'type': 'chat_message',
            'message': {
                'id': saved_message.id,
                'sender': sender_id,
                'receiver': receiver_id,
                'content': saved_message.content,
                'created_at': saved_message.created_at.isoformat(),
            },
        }

        await self.channel_layer.group_send(self.room_group_name, event)

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

import json
import logging
from pathlib import PurePosixPath
from urllib.parse import urlparse

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.contrib.auth import get_user_model

from .models import ChatMessage

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.is_admin_feed = self.room_name == 'admin'
        self.user = user

        if self.is_admin_feed:
            if not (user.is_staff or user.is_superuser):
                await self.close(code=4403)
                return
            self.room_group_name = 'chat_admins'
            self.notification_group_name = 'notify_admins'
            await self.channel_layer.group_add(self.notification_group_name, self.channel_name)
        else:
            try:
                self.conversation_user_id = int(self.room_name)
            except (TypeError, ValueError):
                await self.close(code=4404)
                return
            if not (user.is_staff or user.is_superuser) and user.id != self.conversation_user_id:
                await self.close(code=4403)
                return
            self.room_group_name = f'chat_user_{self.conversation_user_id}'
            self.notification_group_name = f'notify_user_{self.conversation_user_id}'
            await self.channel_layer.group_add(self.notification_group_name, self.channel_name)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info('Chat WebSocket connected: user_id=%s room=%s', user.id, self.room_group_name)

    async def disconnect(self, close_code):
        group_name = getattr(self, 'room_group_name', None)
        if group_name:
            await self.channel_layer.group_discard(group_name, self.channel_name)
            notification_group = getattr(self, 'notification_group_name', None)
            if notification_group:
                await self.channel_layer.group_discard(notification_group, self.channel_name)
            logger.info('Chat WebSocket disconnected: user_id=%s room=%s close_code=%s', self.user.id, group_name, close_code)

    async def receive(self, text_data=None, bytes_data=None):
        if bytes_data is not None or not text_data:
            await self._send_error('Unsupported WebSocket frame.')
            return
        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            await self._send_error('Invalid JSON frame.')
            return
        if not isinstance(data, dict):
            await self._send_error('A JSON object is required.')
            return

        message_type = data.get('type', 'message')
        if message_type == 'ping':
            await self.send(text_data=json.dumps({'type': 'pong'}))
            return
        if message_type != 'message':
            await self._send_error('Unsupported message type.')
            return
        content = str(data.get('message', '')).strip()[:5000]
        attachment_url = str(data.get('attachment_url', '')).strip()
        attachment_type = data.get('attachment_type', 'none')
        if not (content or attachment_url):
            return

        attachment_name = ''
        if attachment_url:
            attachment_path = urlparse(attachment_url).path
            media_prefix = settings.MEDIA_URL.rstrip('/') + '/'
            if not attachment_path.startswith(media_prefix):
                return
            candidate = attachment_path[len(media_prefix):].lstrip('/')
            parts = PurePosixPath(candidate).parts
            upload_user_id = self.conversation_user_id if not self.is_admin_feed else data.get('conversation_id')
            if '..' in parts or not upload_user_id or not candidate.startswith(f'chat_attachments/user_{upload_user_id}/'):
                return
            extension = PurePosixPath(candidate).suffix.lower()
            valid_type = (attachment_type == 'image' and extension in {'.jpg', '.jpeg', '.png', '.webp'}) or (attachment_type == 'pdf' and extension == '.pdf')
            if not valid_type or not ChatMessage._meta.get_field('attachment').storage.exists(candidate):
                return
            storage = ChatMessage._meta.get_field('attachment').storage
            if storage.size(candidate) > 5 * 1024 * 1024:
                return
            attachment_name = candidate

        if self.is_admin_feed:
            try:
                conversation_user_id = int(data.get('conversation_id'))
            except (TypeError, ValueError):
                await self._send_error('A valid conversation_id is required.')
                return
            if not await self._user_exists(conversation_user_id):
                await self._send_error('Conversation not found.')
                return
        else:
            conversation_user_id = self.conversation_user_id

        saved_message = await self._save_message(conversation_user_id, content, attachment_name, attachment_type)
        payload = await self._message_payload(saved_message)
        await self.channel_layer.group_send(f'chat_user_{conversation_user_id}', {'type': 'chat_message', 'message': payload})
        await self.channel_layer.group_send('chat_admins', {
            'type': 'chat_notification',
            'message': {**payload, 'conversation_user': conversation_user_id},
        })
        if payload['is_from_admin']:
            unread_count = await self._unread_count_for_user(conversation_user_id)
            await self.channel_layer.group_send(f'notify_user_{conversation_user_id}', {
                'type': 'unread_event', 'count': unread_count,
                'conversation_id': conversation_user_id,
                'preview': content or 'Tệp đính kèm',
            })
        else:
            unread_count = await self._unread_count_for_admins()
            await self.channel_layer.group_send('notify_admins', {
                'type': 'unread_event', 'count': unread_count,
                'conversation_id': conversation_user_id,
                'preview': content or 'Tệp đính kèm',
            })

    async def _send_error(self, detail):
        await self.send(text_data=json.dumps({'type': 'error', 'error': detail}))

    @database_sync_to_async
    def _save_message(self, conversation_user_id, content, attachment_name, attachment_type):
        return ChatMessage.objects.create(
            conversation_user_id=conversation_user_id,
            sender=self.user,
            receiver=None,
            content=content,
            attachment=attachment_name,
            attachment_type=attachment_type if attachment_name else 'none',
            is_from_admin=bool(self.user.is_staff or self.user.is_superuser),
            is_read=False,
        )

    @database_sync_to_async
    def _user_exists(self, user_id):
        return get_user_model().objects.filter(pk=user_id).exists()

    @database_sync_to_async
    def _unread_count_for_user(self, user_id):
        return ChatMessage.objects.filter(
            conversation_user_id=user_id, is_from_admin=True, is_read=False,
        ).count()

    @database_sync_to_async
    def _unread_count_for_admins(self):
        return ChatMessage.objects.filter(is_from_admin=False, is_read=False).count()

    @database_sync_to_async
    def _message_payload(self, message):
        return {
            'id': message.id,
            'conversation_user': message.conversation_user_id,
            'sender': message.sender_id,
            'sender_name': message.sender.get_username(),
            'is_from_admin': message.is_from_admin,
            'content': message.content,
            'attachment_url': message.attachment.url if message.attachment else '',
            'attachment_type': message.attachment_type,
            'created_at': message.created_at.isoformat(),
            'is_read': message.is_read,
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def chat_notification(self, event):
        if self.is_admin_feed:
            await self.send(text_data=json.dumps({'type': 'new_message', **event['message']}))

    async def unread_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'unread',
            'count': event['count'],
            'conversation_id': event.get('conversation_id'),
            'preview': event.get('preview', ''),
        }))

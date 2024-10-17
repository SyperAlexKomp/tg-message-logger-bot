import logging

from aiogram.enums import ContentType
from aiogram.filters import Filter
from aiogram.types import Message, BusinessMessagesDeleted

from repo import Repo
from utils.encryptor import get_text_hash


class ContentTypeFilter(Filter):
    def __init__(self, type: tuple) -> None:
        self.type = type

    async def __call__(self, message: Message, repo: Repo) -> bool:
        if isinstance(message, BusinessMessagesDeleted):
            saved_message = repo.messages.get(message_id=message.message_ids[0],
                                        connection_id=get_text_hash(message.business_connection_id))
            if saved_message is None:
                logging.warning(f"Received update for message with id={message.message_ids[0]} in chat={message.chat.id} that was not found")
                return False

            if saved_message.is_media:
                return saved_message.media_type in self.type
            elif saved_message.is_sticker: return ContentType.STICKER in self.type
            else: return ContentType.TEXT in self.type

        return message.content_type in self.type
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User

from repo import Repo
from utils.encryptor import get_text_hash


class UsersMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        repo: Repo = data["repo"]
        user: User = data.get("event_from_user", None)

        if user is None:
            return await handler(event, data)

        user_data = repo.users.get(user.id)

        if user is None or user_data is None or data.get('business_connection_id') is None:
            return await handler(event, data)

        connection_id = get_text_hash(data['business_connection_id'])
        if user_data.connection_id != connection_id:
            print("e")
            user_data.connection_id = connection_id
            repo.save()

        return await handler(event, data)

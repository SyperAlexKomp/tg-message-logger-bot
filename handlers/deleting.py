import typing
from typing import Tuple

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import BusinessMessagesDeleted
from aiogram.utils.i18n import gettext as _

from filters.ContentTypeFilter import ContentTypeFilter
from repo import Repo
from utils.encryptor import get_text_hash, TextEncryptor

message_delete_route = Router()


# Text
@message_delete_route.deleted_business_messages(ContentTypeFilter((ContentType.TEXT, )))
async def text_delete(bdm: BusinessMessagesDeleted, bot: Bot, repo: Repo) -> None:
    user = repo.users.get_by_connection(get_text_hash(bdm.business_connection_id))

    if user is None:
        return
    connection_id = get_text_hash(bdm.business_connection_id)

    for m in bdm.message_ids:
        message = repo.messages.get(message_id=m, connection_id=connection_id)
        if message is None:
            return

        repo.messages.delete(message)

        user_link = ""
        if bdm.chat.has_private_forwards:
            user_link = f"tg://user?id={bdm.chat.id}"
        elif bdm.chat.username is not None:
            user_link = "https://t.me/" + bdm.chat.username

        text = _("<b>🗑 Deletion noticed!</b>"
                 "\n\nMessage by <b><a href='{user_link}'>{name}</a></b>:"
                 "<blockquote expandable>{msg}</blockquote>",
                 locale=user.language).format(user_link=user_link,
                                              name=bdm.chat.full_name,
                                              msg=TextEncryptor(key=bdm.business_connection_id).decrypt(message.message))

        await bot.send_message(chat_id=user.id, text=text)


# Media (Photo, Video, Voice, Animation, Audio)
@message_delete_route.deleted_business_messages(ContentTypeFilter((ContentType.PHOTO,
                                                                   ContentType.VIDEO,
                                                                   ContentType.VOICE,
                                                                   ContentType.ANIMATION,
                                                                   ContentType.AUDIO)))
async def media_delete(bdm: BusinessMessagesDeleted, bot: Bot, repo: Repo) -> None:
    user = repo.users.get_by_connection(get_text_hash(bdm.business_connection_id))

    if user is None:
        return
    connection_id = get_text_hash(bdm.business_connection_id)

    for m in bdm.message_ids:
        message = repo.messages.get(message_id=m, connection_id=connection_id)
        if message is None:
            return

        repo.messages.delete(message)

        user_link = ""
        if bdm.chat.has_private_forwards:
            user_link = f"tg://user?id={bdm.chat.id}"
        elif bdm.chat.username is not None:
            user_link = "https://t.me/" + bdm.chat.username

        text = _("<b>🗑 Deletion noticed!</b>"
                 "\n\nMessage by <b><a href='{user_link}'>{name}</a></b>:",
                 locale=user.language).format(user_link=user_link,
                                              name=bdm.chat.full_name)

        if message.message is None: pass
        else:
            text += "<blockquote expandable>{msg}</blockquote>".format(msg=TextEncryptor(key=bdm.business_connection_id).decrypt(message.message))

        if message.media_type == ContentType.PHOTO:
            await bot.send_photo(chat_id=user.id,
                                 photo=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media),
                                 caption=text)
        elif message.media_type == ContentType.VIDEO:
            await bot.send_video(chat_id=user.id,
                                 video=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media),
                                 caption=text)
        elif message.media_type == ContentType.VOICE:
            try:
                await bot.send_voice(chat_id=user.id,
                                     voice=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media),
                                     caption=text)
            except TelegramBadRequest:
                t = await bot.send_message(chat_id=user.id,
                                       text=text)
                await bot.send_message(reply_to_message_id=t.message_id,
                                       chat_id=user.id,
                                       text=_("<b>Voice message can't be sent because of your privacy settings!</b>"))
        elif message.media_type == ContentType.ANIMATION:
            await bot.send_animation(chat_id=user.id,
                                     animation=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media),
                                     caption=text)
        else:
            return


# No caption media (Stickers, Video note)
@message_delete_route.deleted_business_messages(ContentTypeFilter((ContentType.STICKER, ContentType.VIDEO_NOTE)))
async def nocap_media_delete(bdm: BusinessMessagesDeleted, bot: Bot, repo: Repo) -> None:
    user = repo.users.get_by_connection(get_text_hash(bdm.business_connection_id))

    if user is None:
        return
    connection_id = get_text_hash(bdm.business_connection_id)

    for m in bdm.message_ids:
        message = repo.messages.get(message_id=m, connection_id=connection_id)
        if message is None:
            return

        repo.messages.delete(message)

        user_link = ""
        if bdm.chat.has_private_forwards:
            user_link = f"tg://user?id={bdm.chat.id}"
        elif bdm.chat.username is not None:
            user_link = "https://t.me/" + bdm.chat.username

        text = _("<b>🗑 Deletion noticed!</b>"
                 "\n\nMessage by <b><a href='{user_link}'>{name}</a></b>:",
                 locale=user.language).format(user_link=user_link,
                                              name=bdm.chat.full_name)

        t = await bot.send_message(chat_id=user.id, text=text)

        if message.is_sticker:
            await bot.send_sticker(chat_id=user.id,
                                   reply_to_message_id=t.message_id,
                                   sticker=TextEncryptor(key=bdm.business_connection_id).decrypt(message.sticker))
        elif message.media_type == ContentType.VIDEO_NOTE:
            await bot.send_video_note(chat_id=user.id,
                                      reply_to_message_id=t.message_id,
                                      video_note=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media))
        else:
            return


@message_delete_route.edited_business_message()
async def not_handled(msg: BusinessMessagesDeleted):
    print("Bruh")
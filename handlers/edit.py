import typing
from typing import Tuple

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _
from aiogram.utils.media_group import MediaGroupBuilder

from filters.ContentTypeFilter import ContentTypeFilter
from repo import Repo
from repo.modules.messages import MessageData
from repo.modules.users import UserData
from utils.encryptor import get_text_hash, TextEncryptor

message_edit_route = Router()


async def get_data(repo: Repo, business_connection_id,
                      from_user_id, message_id) -> typing.Optional[tuple[UserData, MessageData]]:
    user = repo.users.get_by_connection(get_text_hash(business_connection_id))

    if user is None:
        return

    if user.id == from_user_id:
        return

    connection_id = get_text_hash(business_connection_id)

    message = repo.messages.get(message_id=message_id, connection_id=connection_id)

    if message is None:
        return

    return user, message


# Text
@message_edit_route.edited_business_message(ContentTypeFilter((ContentType.TEXT, )))
async def text_edit(bm: Message, bot: Bot, repo: Repo) -> None:
    data = await get_data(repo, bm.business_connection_id, bm.from_user.id, bm.message_id)
    if data is None: return

    message = data[1]
    user = data[0]

    text = _("<b>✏ Editing noticed!</b>"
             "\n\nOld message by <b><a href='https://t.me/{username}'>{name}</a></b>:"
             "<blockquote expandable>{old_msg}</blockquote>"
             "\nNew message:"
             "<blockquote expandable>{new_msg}</blockquote>",
             locale=user.language).format(username=bm.chat.username,
                                          name=bm.chat.full_name,
                                          new_msg=bm.html_text,
                                          old_msg=TextEncryptor(key=bm.business_connection_id).decrypt(
                                              message.message))

    message.message = TextEncryptor(key=bm.business_connection_id).encrypt(bm.html_text)
    repo.save()

    await bot.send_message(chat_id=user.id, text=text)


# TODO: Other media support
# Video and Photo
@message_edit_route.edited_business_message(ContentTypeFilter((ContentType.PHOTO, ContentType.VIDEO)))
async def text_edit(bm: Message, bot: Bot, repo: Repo) -> None:
    data = await get_data(repo, bm.business_connection_id, bm.from_user.id, bm.message_id)
    if data is None: return

    message = data[1]
    user = data[0]

    text = _("<b>✏ Editing noticed!</b>"
             "\n\nOld message by <b><a href='https://t.me/{username}'>{name}</a></b>:"
             "<blockquote expandable>{old_msg}</blockquote>"
             "\nNew message:"
             "<blockquote expandable>{new_msg}</blockquote>",
             locale=user.language).format(username=bm.chat.username,
                                          name=bm.chat.full_name,
                                          new_msg=bm.html_text,
                                          old_msg=TextEncryptor(key=bm.business_connection_id).decrypt(
                                              message.message))

    message.message = TextEncryptor(key=bm.business_connection_id).encrypt(bm.html_text)
    repo.save()

    if bm.content_type == ContentType.PHOTO:
        media = bm.photo[-1].file_id
    else:
        media = bm.dict()[bm.content_type]['file_id']

    media_group = MediaGroupBuilder(caption=text)
    media_group.add(type=message.media_type, media=TextEncryptor(key=bm.business_connection_id).decrypt(message.media))

    if media != TextEncryptor(key=bm.business_connection_id).decrypt(message.media):
        media_group.add(type=bm.content_type, media=media)

    message.media = TextEncryptor(key=bm.business_connection_id).encrypt(media)
    repo.save()

    await bot.send_media_group(chat_id=user.id, media=media_group.build())
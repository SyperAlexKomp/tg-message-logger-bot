import logging

from aiogram import Router, Bot
from aiogram.enums import ContentType
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from filters.ContentTypeFilter import ContentTypeFilter
from repo import Repo
from repo.modules.messages import MessageData
from utils.encryptor import get_text_hash, TextEncryptor

message_receive_route = Router()
bad_users = []  # Used to prevent spam if user is not found in db


# Text
@message_receive_route.business_message(ContentTypeFilter((ContentType.TEXT,)))
async def text_handle(msg: Message, repo: Repo, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(msg.business_connection_id))

    if user is None:
        if get_text_hash(msg.business_connection_id) not in bad_users:
            bad_users.append(get_text_hash(msg.business_connection_id))
            bot_info = await bot.me()
            await msg.answer(
                _("An error has occurred! Please add the bot to your profile again!\n\n<i>via</i> @{bot_username}").format(
                    bot_username=bot_info.username))
        return

    if user.id == msg.from_user.id:
        return

    msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                           message_id=msg.message_id,
                           message=TextEncryptor(key=msg.business_connection_id).encrypt(msg.html_text))

    repo.messages.add(message=msg_data)


# Sticker
@message_receive_route.business_message(ContentTypeFilter((ContentType.STICKER,)))
async def stick_handle(msg: Message, repo: Repo, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(msg.business_connection_id))

    if user is None:
        if get_text_hash(msg.business_connection_id) not in bad_users:
            bad_users.append(get_text_hash(msg.business_connection_id))
            bot_info = await bot.me()
            await msg.answer(
                _("An error has occurred! Please add the bot to your profile again!\n\n<i>via</i> @{bot_username}").format(
                    bot_username=bot_info.username))
        return

    if user.id == msg.from_user.id:
        return

    msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                           message_id=msg.message_id,
                           is_sticker=True,
                           sticker=TextEncryptor(key=msg.business_connection_id).encrypt(msg.sticker.file_id))

    repo.messages.add(message=msg_data)


# Media (Video, Animation, Voice, Photo, Audio)
@message_receive_route.business_message(ContentTypeFilter((ContentType.VIDEO,
                                                           ContentType.VOICE,
                                                           ContentType.ANIMATION,
                                                           ContentType.PHOTO,
                                                           ContentType.VIDEO_NOTE,
                                                           ContentType.AUDIO,)))
async def media_handle(msg: Message, repo: Repo, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(msg.business_connection_id))

    if user is None:
        if get_text_hash(msg.business_connection_id) not in bad_users:
            bad_users.append(get_text_hash(msg.business_connection_id))
            bot_info = await bot.me()
            await msg.answer(
                _("An error has occurred! Please add the bot to your profile again!\n\n<i>via</i> @{bot_username}").format(
                    bot_username=bot_info.username))
        return

    if user.id == msg.from_user.id:
        return

    msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                           message_id=msg.message_id,
                           is_media=True,
                           media_type=msg.content_type,
                           media=TextEncryptor(key=msg.business_connection_id).encrypt(
                               msg.model_dump()[msg.content_type][
                                   'file_id'] if msg.content_type != ContentType.PHOTO else msg.photo[-1].file_id),
                           message=TextEncryptor(key=msg.business_connection_id).encrypt(
                               msg.caption) if msg.caption is not None else None)

    repo.messages.add(message=msg_data)


@message_receive_route.business_message()
async def not_handled(msg: Message):
    logging.warning(f"Message of type {msg.content_type} is not handled!")

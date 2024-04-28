import asyncio
import logging
from configparser import ConfigParser

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ContentType
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message
from aiogram.utils.i18n import gettext as _, I18n, SimpleI18nMiddleware
from aiogram.utils.media_group import MediaGroupBuilder

from middlewares.user_check import UsersMiddleware
from repo import Repo
from repo.modules.messages import MessageData
from repo.modules.users import UserData
from utils.encryptor import TextEncryptor, get_text_hash

logging.basicConfig(level=logging.INFO, format="[%(asctime)s][%(levelname)s][%(funcName)s][%(module)s][%(lineno)d] - %(message)s")

dp = Dispatcher()
i18n = I18n(path="locales", default_locale="en", domain="messages")

dp.update.middleware(SimpleI18nMiddleware(i18n=i18n))
dp.update.middleware(UsersMiddleware())

config = ConfigParser()
config.read("config.ini")

repo = Repo(username=config.get("DATABASE", 'username'),
            password=config.get("DATABASE", 'password'),
            ip=config.get("DATABASE", 'ip'),
            port=config.getint("DATABASE", 'port'),
            db=config.get("DATABASE", 'db'))

dp["repo"] = repo

@dp.business_connection()
async def connection_handler(bc: BusinessConnection, bot: Bot) -> None:
    connection_id = get_text_hash(bc.id)

    user = repo.users.get(bc.user.id)

    if not bc.is_enabled:
        repo.messages.delete_by_cid(connection_id=connection_id)
        repo.users.delete(user=user)

        text = _("⚠ All your data was cleared because of disconnecting")

        await bot.send_message(chat_id=bc.user.id, text=text)
        return

    if user is not None:
        if user.connection_id != connection_id:
            user.connection_id = connection_id
            repo.save()

            repo.messages.delete_by_cid(connection_id=connection_id)
    s = repo.users.add(UserData(id=bc.user.id,
                                connection_id=get_text_hash(bc.id),
                                language=bc.user.language_code))

    if s:
        text = _("Hello, <b>{name}</b>!"
                 "\nI will help you to log editing and deleting messages done by another users!"
                 "\n\nYou just need to send me ID of the channel in which you prefer to see the logs. "
                 "By default I will save them here").format(name=bc.user.full_name)

        await bot.send_message(chat_id=bc.user.id, text=text)


# TODO
@dp.deleted_business_messages()
async def delete_handler(bdm: BusinessMessagesDeleted, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(bdm.business_connection_id))

    if user is None:
        return
    connection_id = get_text_hash(bdm.business_connection_id)

    for m in bdm.message_ids:
        message = repo.messages.get(message_id=m, connection_id=connection_id)
        if message is None:
            return

        repo.messages.delete(message)


        text = _("<b>🗑 Deletion noticed!</b>"
                 "\n\nMessage by <b><a href='https://t.me/{username}'>{name}</a></b>:",
                 locale=user.language).format(username=bdm.chat.username,
                                                          name=bdm.chat.full_name)
        if not message.is_sticker and message.message is not None:
            text += "<blockquote>{msg}</blockquote>".format(msg=TextEncryptor(key=bdm.business_connection_id).decrypt(message.message))
        elif not message.is_sticker and message.message is None:
            text.replace(":", "")

        if not message.is_media:
            await bot.send_message(chat_id=user.id, text=text)
            if message.is_sticker:
                await bot.send_sticker(chat_id=user.id,
                                       sticker=TextEncryptor(key=bdm.business_connection_id).decrypt(message.sticker))
        else:
            if message.media_type == ContentType.PHOTO:
                await bot.send_photo(chat_id=user.id,
                                     photo=TextEncryptor(key=bdm.business_connection_id).decrypt(message.media),
                                     caption=text)


@dp.edited_business_message()
async def edit_handle(bm: Message, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(bm.business_connection_id))

    if user is None:
        return

    if user.id == bm.from_user.id:
        return

    connection_id = get_text_hash(bm.business_connection_id)

    message = repo.messages.get(message_id=bm.message_id, connection_id=connection_id)

    if message is None:
        return

    if message.is_media:
        em = TextEncryptor(key=bm.business_connection_id).encrypt(bm.caption) if bm.caption is not None else None
        if message.message == em:
            text = _("<b>✏ Editing noticed!</b>"
                     "\n\nOld media by <b><a href='https://t.me/{username}'>{name}</a></b> at left"
                     "\nNew message at right",
                     locale=user.language).format(username=bm.chat.username,
                                                  name=bm.chat.full_name)
        else:
            text = _("<b>✏ Editing noticed!</b>"
                     "\n\nOld message by <b><a href='https://t.me/{username}'>{name}</a></b>:"
                     "<blockquote>{old_msg}</blockquote>"
                     "\nNew message:"
                     "<blockquote>{new_msg}</blockquote>",
                     locale=user.language).format(username=bm.chat.username,
                                                  name=bm.chat.full_name,
                                                  new_msg=bm.caption,
                                                  old_msg=TextEncryptor(key=bm.business_connection_id).decrypt(
                                                      message.message) if message.message is not None else "")

            message.message = TextEncryptor(key=bm.business_connection_id).encrypt(bm.caption)
            repo.save()



        if bm.content_type == ContentType.PHOTO:
            media = bm.photo[-1].file_id
        else:
            media = bm[bm.content_type].file_id



        media_group = MediaGroupBuilder(caption=text)
        media_group.add(type=message.media_type, media=TextEncryptor(key=bm.business_connection_id).decrypt(message.media))

        if media != TextEncryptor(key=bm.business_connection_id).decrypt(message.media):
            media_group.add(type=bm.content_type, media=media)

        message.media = TextEncryptor(key=bm.business_connection_id).encrypt(media)
        repo.save()

        await bot.send_media_group(chat_id=user.id, media=media_group.build())
        return
    else:
        text = _("<b>✏ Editing noticed!</b>"
                 "\n\nOld message by <b><a href='https://t.me/{username}'>{name}</a></b>:"
                 "<blockquote>{old_msg}</blockquote>"
                 "\nNew message:"
                 "<blockquote>{new_msg}</blockquote>",
                 locale=user.language).format(username=bm.chat.username,
                                              name=bm.chat.full_name,
                                              new_msg=bm.html_text,
                                              old_msg=TextEncryptor(key=bm.business_connection_id).decrypt(
                                                  message.message))

    message.message = TextEncryptor(key=bm.business_connection_id).encrypt(bm.html_text)
    repo.save()

    if user.channel_id is not None:
        try:
            await bot.send_message(chat_id=user.channel_id, text=text)
        except:
            await bot.send_message(chat_id=user.id, text=text)
    else:
        await bot.send_message(chat_id=user.id, text=text)



@dp.business_message()
async def message_handler(msg: Message, bot: Bot) -> None:
    user = repo.users.get_by_connection(get_text_hash(msg.business_connection_id))

    if user.id == msg.from_user.id:
        return

    if msg.content_type == ContentType.TEXT:
        msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                               message_id=msg.message_id,
                               message=TextEncryptor(key=msg.business_connection_id).encrypt(msg.html_text))
    elif msg.content_type == ContentType.STICKER:
        msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                               message_id=msg.message_id,
                               is_sticker=True,
                               sticker=TextEncryptor(key=msg.business_connection_id).encrypt(msg.sticker.file_id))
    elif msg.content_type == ContentType.PHOTO:
        msg_data = MessageData(connection_id=get_text_hash(msg.business_connection_id),
                               message_id=msg.message_id,
                               is_media=True,
                               media_type=msg.content_type,
                               media=TextEncryptor(key=msg.business_connection_id).encrypt(msg.photo[-1].file_id),
                               message=TextEncryptor(key=msg.business_connection_id).encrypt(msg.caption) if msg.caption is not None else None)

    else:
        return


    repo.messages.add(message=msg_data)


@dp.message(F.content_type.in_({'text'}))
async def get_chat_id(msg: Message, bot: Bot) -> None:
    try:
        chat_id = int(msg.text)
    except:
        return

    try:
        t = await bot.send_message(chat_id=chat_id, text="Test")
        await t.delete()
    except:
        await msg.answer(text=_("Sorry but I can't found this chat."
                                "\n\n<b>Maybe you forgot to add me to it?</b>"))
        return

    user = repo.users.get(msg.from_user.id)
    user.channel_id = chat_id
    repo.save()


async def main() -> None:
    bot = Bot(token=config.get("BOT", 'token'),
              parse_mode=ParseMode.HTML,
              disable_web_page_preview=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
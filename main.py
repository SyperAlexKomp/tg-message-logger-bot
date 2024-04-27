import asyncio
import logging
from configparser import ConfigParser

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message
from aiogram.utils.i18n import gettext as _, I18n, SimpleI18nMiddleware

from middlewares.user_check import UsersMiddleware
from repo import Repo
from repo.modules.messages import MessageData
from repo.modules.users import UserData
from utils.encryptor import TextEncryptor

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
    if not bc.is_enabled:
        return

    repo.users.add(UserData(id=bc.user.id, connection_id=bc.id))

    text = _("Hello, <b>{name}</b>!"
             "\nI will help you to log editing and deleting messages done by another users!"
             "\n\nYou just need to send me ID of the channel in which you prefer to see the logs. "
             "By default I will save them here").format(name=bc.user.full_name)

    await bot.send_message(chat_id=bc.user.id, text=text)


# TODO
@dp.deleted_business_messages()
async def delete_handler(bdm: BusinessMessagesDeleted, bot: Bot) -> None:
    user = repo.users.get_by_connection(bdm.business_connection_id)

    if user is None:
        return

    for m in bdm.message_ids:
        message = repo.messages.get(message_id=m, chat_id=bdm.chat.id)
        if message is None:
            return

        if user.id == message.chat_id:
            return

        repo.messages.delete(message)
        text = _("<b>🗑 Deletion noticed!</b>"
                 "\n\nMessage by <b><a href='https://t.me/{username}'>{name}</a></b>:"
                 "<blockquote>{msg}</blockquote>").format(username=bdm.chat.username,
                                                          name=bdm.chat.full_name,
                                                          msg=TextEncryptor(key=str(bdm.chat.id)).decrypt(message.message))

        if user.channel_id is not None:
            try:
                await bot.send_message(chat_id=user.channel_id, text=text)
            except:
                await bot.send_message(chat_id=user.id, text=text)
        else:
            await bot.send_message(chat_id=user.id, text=text)


@dp.edited_business_message()
async def edit_handle(bm: Message, bot: Bot) -> None:
    user = repo.users.get_by_connection(bm.business_connection_id)

    if user is None:
        return

    if user.id == bm.from_user.id:
        return

    message = repo.messages.get(message_id=bm.message_id, chat_id=bm.from_user.id)

    if message is None:
        return

    text = _("<b>✏ Editing noticed!</b>"
             "\n\nOld message by <b><a href='https://t.me/{username}'>{name}</a></b>:"
             "<blockquote>{old_msg}</blockquote>"
             "\nNew message:"
             "<blockquote>{new_msg}</blockquote>").format(username=bm.chat.username,
                                                      name=bm.chat.full_name,
                                                      new_msg=bm.html_text,
                                                          old_msg=TextEncryptor(key=str(bm.chat.id)).decrypt(
                                                          message.message))

    message.message = TextEncryptor(key=str(bm.chat.id)).encrypt(bm.html_text)
    repo.save()

    if user.channel_id is not None:
        try:
            await bot.send_message(chat_id=user.channel_id, text=text)
        except:
            await bot.send_message(chat_id=user.id, text=text)
    else:
        await bot.send_message(chat_id=user.id, text=text)



@dp.business_message(F.content_type.in_({'text'}))
async def message_handler(msg: Message) -> None:

    repo.messages.add(message=MessageData(chat_id=msg.from_user.id,
                                          message_id=msg.message_id,
                                          message=TextEncryptor(key=str(msg.chat.id)).encrypt(msg.html_text)))


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
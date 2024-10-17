import asyncio
import logging
from configparser import ConfigParser

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode, ContentType
from aiogram.types import BusinessConnection, BusinessMessagesDeleted, Message
from aiogram.utils.i18n import gettext as _, I18n, SimpleI18nMiddleware
from aiogram.utils.media_group import MediaGroupBuilder

from filters.ContentTypeFilter import ContentTypeFilter
from handlers.deleting import message_delete_route
from handlers.edit import message_edit_route
from handlers.receive import message_receive_route
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

dp.include_routers(message_receive_route, message_edit_route, message_delete_route)

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
        text = _("Hello, <b><a href='tg://user?id={user_id}'>{name}</a></b>!"
                 "\nI will help you to log editing and deleting messages done by another users!"
                 "\n\n<a href='https://github.com/SyperAlexKomp/tg-message-logger-bot'>Source code</a>").format(name=bc.user.full_name,
                                                                                                                id=bc.user.id)

        await bot.send_photo(chat_id=bc.user.id,
                             caption=text,
                             photo="https://omeba-work.com/screenshoot/fc36db79d525fb040fbad9c8039c8dca.jpg")


@dp.message(ContentTypeFilter((ContentType.TEXT, )))
async def get_chat_id(msg: Message, bot: Bot) -> None:
    text = _("Hello, <b><a href='tg://user?id={user_id}'>{name}</a></b>!"
             "\nI will help you to log editing and deleting messages done by another users!"
             "\n\n<a href='https://github.com/SyperAlexKomp/tg-message-logger-bot'>Source code</a>").format(
        name=msg.from_user.full_name,
        user_id=msg.from_user.id)

    await bot.send_photo(chat_id=msg.from_user.id,
                         caption=text,
                         photo="https://omeba-work.com/screenshoot/fc36db79d525fb040fbad9c8039c8dca.jpg")


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
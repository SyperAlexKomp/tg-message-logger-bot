import asyncio
from configparser import ConfigParser

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode

dp = Dispatcher()


config = ConfigParser()
config.read("config.ini")


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
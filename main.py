import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties  # Для указания parse_mode
from handlers import register_handlers
from config import API_TOKEN  # Импортируем секретный код из config.py

async def main():
    # Инициализируем бота с токеном из config.py
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Регистрируем хендлеры
    register_handlers(dp)

    # Запускаем бот (long-polling)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


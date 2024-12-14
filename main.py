import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties  # Для указания parse_mode и других параметров
from handlers import register_handlers

API_TOKEN = "8166219765:AAHzo-URTBei85_Zww_0DOP72Ihk7gQKRjQ"

async def main():
    # Инициализируем бота с помощью DefaultBotProperties для установки parse_mode
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")  # Устанавливаем форматирование HTML по умолчанию
    )
    dp = Dispatcher()

    # Регистрируем хендлеры
    register_handlers(dp)

    # Запускаем бот (long-polling)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

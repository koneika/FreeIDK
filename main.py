# main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from handlers import router
from config import API_TOKEN

import signal
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def shutdown(bot: Bot):
    logger.info("Shutting down bot...")
    await bot.close()
    logger.info("Bot shutdown complete.")
    sys.exit()

async def main():
    # Инициализация бота с DefaultBotProperties
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Регистрация обработчиков
    dp.include_router(router)

    logger.info("Bot is starting...")

    # Обработка сигналов для корректного завершения
    loop = asyncio.get_event_loop()

    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame), lambda: asyncio.create_task(shutdown(bot)))

    try:
        # Запуск polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error during polling: {e}")
    finally:
        await shutdown(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped manually.")
        sys.exit()

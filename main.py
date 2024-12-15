# main.py

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from handlers import router
from config import API_TOKEN

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    # Initialize the bot with DefaultBotProperties
    bot = Bot(
        token=API_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()

    # Register handlers
    dp.include_router(router)

    logger.info("Bot is starting...")
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

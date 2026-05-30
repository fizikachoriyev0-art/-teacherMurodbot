import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import admin, user, test_handler, subscription, referral
import database as db

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


async def main():
    db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Tartib muhim: admin birinchi (spesifik handler), user oxirida
    dp.include_router(admin.router)
    dp.include_router(subscription.router)
    dp.include_router(test_handler.router)
    dp.include_router(referral.router)
    dp.include_router(user.router)

    logging.info("✅ Bot ishga tushmoqda...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

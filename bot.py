import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database.engine import init_db
from utils.scheduler import setup_scheduler
from utils.throttling import ThrottlingMiddleware
from utils.menu_reset import MenuResetMiddleware

# Umumiy handlerlar
from handlers import common, fallback

# Admin handlerlari
from handlers.admin import (
    groups,
    years,
    students,
    excel,
    debt,
    monthly,
    tests,
    warning,
    public_files,
    public_test,
    debtors_excel,
    attendance,
    ids_excel,
    cards,
)

# User handlerlari
from handlers.user import (
    balance,
    payment,
    rating,
    files,
    test_archive,
    contact,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    await init_db()
    logger.info("✅ Ma'lumotlar bazasi tayyor (WAL).")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    # 1) Menyu tugmasi bosilsa eski oqimni tozalash (throttlingdan OLDIN)
    dp.message.middleware(MenuResetMiddleware())

    # 2) Throttling — har user uchun 0.5s da 1 ta xabar
    dp.message.middleware(ThrottlingMiddleware(rate=0.5))
    dp.callback_query.middleware(ThrottlingMiddleware(rate=0.5))

    dp.include_routers(
        common.router,
        contact.router,
        groups.router,
        years.router,
        students.router,
        debt.router,
        monthly.router,
        tests.router,
        warning.router,
        excel.router,
        debtors_excel.router,
        attendance.router,
        ids_excel.router,
        cards.router,
        public_files.router,
        public_test.router,
        balance.router,
        payment.router,
        rating.router,
        files.router,
        test_archive.router,
        fallback.router,
    )

    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("✅ Scheduler ishga tushdi (oylik + kunlik backup).")

    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🚀 Bot ishga tushdi. Polling boshlandi...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("⛔ Bot to'xtatildi.")

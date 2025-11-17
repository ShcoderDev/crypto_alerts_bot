import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN
from bot.database import Database
from bot.handlers import commands
from bot.price_monitor import PriceMonitor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация бота и диспетчера
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация роутеров
    dp.include_router(commands.router)
    
    # Инициализация базы данных
    db = Database()
    await db.init_db()
    logger.info("База данных инициализирована")
    
    # Инициализация мониторинга цен
    price_monitor = PriceMonitor(bot, db)
    monitor_task = None
    
    try:
        # Запуск мониторинга цен в фоне
        monitor_task = asyncio.create_task(price_monitor.start())
        logger.info("Мониторинг цен запущен")
        
        # Запуск бота
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Остановка бота...")
    finally:
        if monitor_task:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        await price_monitor.stop()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())


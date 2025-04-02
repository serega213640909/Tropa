import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
from handlers.common_handlers import router as common_router
from handlers.guide_handlers import router as guide_router  # Добавлен guide_router

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

async def main():
    """Основная функция для запуска бота."""
    if not BOT_TOKEN or not BOT_TOKEN.strip():
        raise ValueError("BOT_TOKEN отсутствует или пуст в переменных окружения!")

    storage = MemoryStorage()
    bot = Bot(token=BOT_TOKEN, parse_mode="HTML")

    router = Router()
    dp = Dispatcher(storage=storage)
    dp.include_router(common_router)
    dp.include_router(guide_router)  # Подключаем guide_router

    # Временный обработчик в main.py (можно убрать позже)
    @router.message(Command("start"))
    async def cmd_start(message: types.Message):
        await message.answer(f"Привет, {message.from_user.first_name}! Бот работает (main.py).")

    logger.info("Роутер зарегистрирован")

    try:
        logger.info("Бот запущен")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise
    finally:
        await bot.session.close()
        await storage.close()
        logger.info("Бот остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, Exception) as e:
        logger.critical(f"Критическая ошибка при запуске: {e}")
        exit(1)

# handlers/admin_handlers.py
import logging
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text
from keyboards import get_admin_keyboard, get_role_keyboard
from constants import ADMIN_ONLY, ERROR_MESSAGE, ADMIN_IDS

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def handle_admin_role(message: types.Message):
    """Обрабатывает выбор роли админа."""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer(ADMIN_ONLY)
        return
    try:
        await message.answer("Добро пожаловать в админ-панель! 🔧", reply_markup=get_admin_keyboard())
    except Exception as e:
        await message.answer(ERROR_MESSAGE)
        logger.error(f"Ошибка в handle_admin_role: {e}")

def register_admin_handlers(dp: Dispatcher):
    """Регистрирует обработчики для админа."""
    dp.register_message_handler(handle_admin_role, Text("🔧 Админ-панель"))

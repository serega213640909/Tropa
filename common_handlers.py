import logging
from aiogram import Bot, Router, types  # Добавлен Bot в импорт
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from keyboards import get_main_keyboard  # Импорт клавиатуры
from utils import get_time_greeting  # Импорт утилиты
from constants import WELCOME_MESSAGE, HELP_MESSAGE, CONTACT_ADMIN_MESSAGE, ERROR_MESSAGE
from database import get_admin_ids, add_notification  # Импорт функций БД

router = Router()
logger = logging.getLogger(__name__)

# Определение состояния для обратной связи
class ContactAdmin(StatesGroup):
    contact_admin = State()

@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """Обрабатывает команду /start."""
    try:
        await state.clear()  # Очищаем состояние
        greeting, sub_greeting = get_time_greeting()
        await message.answer(
            f"{greeting}, {message.from_user.first_name}! {sub_greeting}\n\n{WELCOME_MESSAGE}",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    except Exception as e:
        logger.error(f"Ошибка в cmd_start для user_id={message.from_user.id}: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "⬅️ Назад")
async def handle_back(message: types.Message, state: FSMContext):
    """Обрабатывает кнопку 'Назад'."""
    try:
        await state.clear()  # Очищаем состояние
        await message.answer(
            "Вы вернулись в главное меню.",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
    except Exception as e:
        logger.error(f"Ошибка в handle_back для user_id={message.from_user.id}: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "📚 Помощь")
async def handle_help(message: types.Message):
    """Обрабатывает кнопку 'Помощь'."""
    try:
        await message.answer(HELP_MESSAGE, reply_markup=get_main_keyboard(message.from_user.id))
    except Exception as e:
        logger.error(f"Ошибка в handle_help для user_id={message.from_user.id}: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "📞 Связаться с администратором")
async def handle_contact_admin(message: types.Message, state: FSMContext):
    """Обрабатывает кнопку 'Связаться с администратором'."""
    try:
        await message.answer(CONTACT_ADMIN_MESSAGE)
        await state.set_state(ContactAdmin.contact_admin)
    except Exception as e:
        logger.error(f"Ошибка в handle_contact_admin для user_id={message.from_user.id}: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(ContactAdmin.contact_admin)
async def process_contact_admin(message: types.Message, state: FSMContext, bot: Bot):  # Исправлен тип bot
    """Обрабатывает сообщение для администратора."""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or "Не указан"
        text = message.text
        admin_message = (
            f"Сообщение от пользователя:\n"
            f"ID: {user_id}\n"
            f"Username: @{username}\n"
            f"Текст: {text}"
        )
        for admin_id in get_admin_ids():
            await add_notification(admin_id, admin_message)
        await message.answer(
            "Сообщение отправлено администратору. Мы свяжемся с тобой скоро!",
            reply_markup=get_main_keyboard(user_id)
        )
        await state.clear()
    except ValueError as e:
        logger.error(f"Ошибка значения в process_contact_admin для user_id={user_id}: {e}")
        await message.answer("Пожалуйста, введи корректное сообщение.")
    except Exception as e:
        logger.error(f"Ошибка в process_contact_admin для user_id={user_id}: {e}")
        await message.answer(ERROR_MESSAGE)

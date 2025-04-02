import logging
from aiogram import Bot, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from constants import GUIDE_REGISTER_FIO, GUIDE_REGISTER_ABOUT, SUCCESSFUL_REGISTRATION
from keyboards import get_guide_keyboard
from database import register_guide

router = Router()
logger = logging.getLogger(__name__)

# Определение состояний для регистрации гида
class GuideRegistration(StatesGroup):
    first_name = State()
    experience = State()

@router.message(Command("guide_register"))
async def cmd_guide_register(message: types.Message, state: FSMContext):
    """Начинает процесс регистрации гида."""
    try:
        await message.answer(GUIDE_REGISTER_FIO, reply_markup=get_guide_keyboard())
        await state.set_state(GuideRegistration.first_name)
    except Exception as e:
        logger.error(f"Ошибка в cmd_guide_register для user_id={message.from_user.id}: {e}")
        await message.answer("Произошла ошибка. Попробуй снова.")

@router.message(GuideRegistration.first_name)
async def process_guide_name(message: types.Message, state: FSMContext):
    """Обрабатывает имя гида."""
    try:
        first_name = message.text.strip()
        if not first_name:
            await message.answer("Имя не может быть пустым. Введи своё ФИО:")
            return
        await state.update_data(first_name=first_name)
        await message.answer(GUIDE_REGISTER_ABOUT)
        await state.set_state(GuideRegistration.experience)
    except Exception as e:
        logger.error(f"Ошибка в process_guide_name для user_id={message.from_user.id}: {e}")
        await message.answer("Произошла ошибка. Попробуй снова.")

@router.message(GuideRegistration.experience)
async def process_guide_experience(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает опыт гида и завершает регистрацию."""
    try:
        experience = int(message.text.strip())
        if not 0 <= experience <= 50:
            await message.answer("Укажи реалистичное число лет опыта (0-50):")
            return
        
        user_data = await state.get_data()
        first_name = user_data.get("first_name")
        user_id = message.from_user.id
        
        await register_guide(user_id, first_name, experience)
        await message.answer(
            SUCCESSFUL_REGISTRATION,
            reply_markup=get_guide_keyboard()
        )
        await state.clear()
    except ValueError:
        logger.error(f"Некорректный ввод опыта для user_id={message.from_user.id}: {message.text}")
        await message.answer("Пожалуйста, введи число лет опыта (например, 5):")
    except Exception as e:
        logger.error(f"Ошибка в process_guide_experience для user_id={message.from_user.id}: {e}")
        await message.answer("Произошла ошибка. Попробуй снова.")

@router.message(lambda message: message.text == "⬅️ Назад")
async def handle_guide_back(message: types.Message, state: FSMContext):
    """Обрабатывает кнопку 'Назад' для гида."""
    try:
        await state.clear()
        await message.answer("Вы вернулись в меню гида.", reply_markup=get_guide_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_guide_back для user_id={message.from_user.id}: {e}")
        await message.answer("Произошла ошибка. Попробуй снова.")

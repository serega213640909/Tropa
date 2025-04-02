# handlers/traveler_handlers.py
import logging
from aiogram import Router, types, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from keyboards import get_traveler_keyboard
from constants import (
    TRAVELER_WELCOME, ERROR_MESSAGE, NO_EXCURSIONS, BOOKING_SUCCESS,
    REVIEW_SUCCESS, REQUEST_SUCCESS, NO_BOOKINGS
)
from database import (
    get_excursions, book_excursion, add_review, get_bookings_by_user,
    add_request, get_guide
)
from utils import notify_new_booking, notify_new_request

router = Router()
logger = logging.getLogger(__name__)

# Определяем состояния для создания заявки
class RequestCreation(StatesGroup):
    city = State()
    keywords = State()

# Определяем состояния для оставления отзыва
class ReviewCreation(StatesGroup):
    rating = State()
    comment = State()

@router.message(lambda message: message.text == "🌍 Я путешественник")
async def handle_traveler_menu(message: types.Message, state: FSMContext):
    """Обрабатывает вход в меню путешественника."""
    try:
        await state.clear()
        await message.answer(TRAVELER_WELCOME, reply_markup=get_traveler_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_traveler_menu: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "🔍 Найти маршрут")
async def handle_search_excursions(message: types.Message):
    """Показывает доступные маршруты."""
    try:
        excursions = await get_excursions()
        if not excursions:
            await message.answer(NO_EXCURSIONS, reply_markup=get_traveler_keyboard())
            return
        for excursion in excursions:
            guide = await get_guide(excursion["guide_id"])
            book_button = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Забронировать", callback_data=f"book_{excursion['id']}")]
            ])
            message_text = (
                f"Маршрут: {excursion['title']}\n"
                f"Гид: {guide['first_name']} {guide['last_name']}\n"
                f"Город: {excursion['city']}\n"
                f"Тематика: {excursion['theme']}\n"
                f"Описание: {excursion['description']}\n"
                f"Стоимость: {excursion['price']} руб./чел.\n"
                f"Даты: {', '.join(excursion['dates'])}\n"
                f"Рейтинг гида: {guide['rating']:.1f} ({guide['review_count']} отзывов)"
            )
            await message.answer(message_text, reply_markup=book_button)
        await message.answer("Вернуться в меню:", reply_markup=get_traveler_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_search_excursions: {e}")
        await message.answer(ERROR_MESSAGE)

@router.callback_query(lambda c: c.data.startswith("book_"))
async def process_book_excursion(callback: types.CallbackQuery, bot: Bot):
    """Обрабатывает бронирование маршрута."""
    try:
        excursion_id = int(callback.data.split("_")[1])
        user_id = callback.from_user.id
        await book_excursion(user_id, excursion_id)  # Убираем booking_id
        await callback.message.answer(BOOKING_SUCCESS, reply_markup=get_traveler_keyboard())
        # Уведомляем гида о новом бронировании
        excursion = next((e for e in await get_excursions() if e["id"] == excursion_id), None)
        if excursion:
            await notify_new_booking(bot, excursion["guide_id"], excursion["title"], user_id)
        await callback.answer()
    except Exception as e:
        logger.error(f"Ошибка в process_book_excursion: {e}")
        await callback.message.answer(ERROR_MESSAGE)
        await callback.answer()

@router.message(lambda message: message.text == "📅 Мои бронирования")
async def handle_my_bookings(message: types.Message):
    """Показывает бронирования путешественника."""
    try:
        bookings = await get_bookings_by_user(message.from_user.id)
        if not bookings:
            await message.answer(NO_BOOKINGS, reply_markup=get_traveler_keyboard())
            return
        for booking in bookings:
            excursion = next((e for e in await get_excursions() if e["id"] == booking["excursion_id"]), None)
            if excursion:
                guide = await get_guide(excursion["guide_id"])
                message_text = (
                    f"Бронирование #{booking['id']}\n"
                    f"Маршрут: {excursion['title']}\n"
                    f"Гид: {guide['first_name']} {guide['last_name']}\n"
                    f"Город: {excursion['city']}\n"
                    f"Дата бронирования: {booking['created_at']}\n"
                    f"Статус: {booking['status']}"
                )
                await message.answer(message_text)
        await message.answer("Вернуться в меню:", reply_markup=get_traveler_keyboard())
    except Exception as e:
        logger.error(f"Ошибка в handle_my_bookings: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "✍️ Оставить отзыв")
async def handle_leave_review(message: types.Message, state: FSMContext):
    """Начинает процесс оставления отзыва."""
    try:
        bookings = await get_bookings_by_user(message.from_user.id)
        if not bookings:
            await message.answer("У тебя нет бронирований, чтобы оставить отзыв.", reply_markup=get_traveler_keyboard())
            return
        await message.answer("Укажи рейтинг (от 1 до 5):")
        await state.set_state(ReviewCreation.rating)
    except Exception as e:
        logger.error(f"Ошибка в handle_leave_review: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(ReviewCreation.rating)
async def process_review_rating(message: types.Message, state: FSMContext):
    """Обрабатывает рейтинг отзыва."""
    try:
        rating = int(message.text)
        if rating < 1 or rating > 5:
            await message.answer("Рейтинг должен быть от 1 до 5. Попробуй снова:")
            return
        await state.update_data(rating=rating)
        await message.answer("Напиши комментарий к отзыву:")
        await state.set_state(ReviewCreation.comment)
    except ValueError:
        await message.answer("Пожалуйста, введи число от 1 до 5:")
    except Exception as e:
        logger.error(f"Ошибка в process_review_rating: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(ReviewCreation.comment)
async def process_review_comment(message: types.Message, state: FSMContext):
    """Обрабатывает комментарий отзыва и завершает процесс."""
    try:
        data = await state.get_data()
        rating = data["rating"]
        comment = message.text
        bookings = await get_bookings_by_user(message.from_user.id)
        # Берем первое бронирование для определения гида (можно улучшить выбор)
        booking = bookings[0]
        excursion = next((e for e in await get_excursions() if e["id"] == booking["excursion_id"]), None)
        if excursion:
            guide_id = excursion["guide_id"]
            await add_review(message.from_user.id, guide_id, rating, comment)
            await message.answer(REVIEW_SUCCESS, reply_markup=get_traveler_keyboard())
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в process_review_comment: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(lambda message: message.text == "📩 Оставить заявку")
async def handle_create_request(message: types.Message, state: FSMContext):
    """Начинает процесс создания заявки."""
    try:
        await message.answer("В каком городе ты хочешь найти маршрут?")
        await state.set_state(RequestCreation.city)
    except Exception as e:
        logger.error(f"Ошибка в handle_create_request: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(RequestCreation.city)
async def process_request_city(message: types.Message, state: FSMContext):
    """Обрабатывает город заявки."""
    try:
        await state.update_data(city=message.text)
        await message.answer("Какие у тебя интересы? (например, история, природа, гастрономия):")
        await state.set_state(RequestCreation.keywords)
    except Exception as e:
        logger.error(f"Ошибка в process_request_city: {e}")
        await message.answer(ERROR_MESSAGE)

@router.message(RequestCreation.keywords)
async def process_request_keywords(message: types.Message, state: FSMContext, bot: Bot):
    """Обрабатывает ключевые слова заявки и завершает процесс."""
    try:
        data = await state.get_data()
        city = data["city"]
        keywords = message.text
        await add_request(message.from_user.id, city, keywords)
        await message.answer(REQUEST_SUCCESS, reply_markup=get_traveler_keyboard())
        # Уведомляем администратора о новой заявке
        request_text = (
            f"Новая заявка от путешественника:\n"
            f"Пользователь: {message.from_user.id}\n"
            f"Город: {city}\n"
            f"Интересы: {keywords}"
        )
        await notify_new_request(bot, message.from_user.id, request_text)
        await state.clear()
    except Exception as e:
        logger.error(f"Ошибка в process_request_keywords: {e}")
        await message.answer(ERROR_MESSAGE)

def register_traveler_handlers() -> Router:
    """Регистрирует обработчики для путешественников."""
    return router

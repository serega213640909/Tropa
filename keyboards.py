# keyboards.p
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import types
from database import get_guide
from constants import ADMIN_IDS, REQUEST_NEW_CITY, CANCEL_REQUEST

def get_role_keyboard(user_id):
    """Создает клавиатуру для выбора роли."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_traveler = types.KeyboardButton("🌴 Я путешественник")
    guide = get_guide(user_id)
    if guide:
        if guide[5]:  # approved
            btn_guide = types.KeyboardButton("🧳 Личный кабинет")
            markup.add(btn_traveler, btn_guide)
    else:
        btn_guide = types.KeyboardButton("🧳 Я гид")
        markup.add(btn_traveler, btn_guide)
    btn_info = types.KeyboardButton("ℹ️ О боте")
    markup.add(btn_info)
    if user_id in ADMIN_IDS:
        btn_admin = types.KeyboardButton("🔧 Админ-панель")
        markup.add(btn_admin)
    return markup

def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Возвращает главную клавиатуру в зависимости от роли пользователя."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)

    # Общие кнопки для всех пользователей
    keyboard.add(KeyboardButton("🌍 Я путешественник"))
    keyboard.add(KeyboardButton("🗺️ Я гид"))
    keyboard.add(KeyboardButton("📚 Помощь"))
    keyboard.add(KeyboardButton("📞 Связаться с администратором"))

    # Если пользователь — администратор, добавляем кнопку админ-панели
    if user_id in get_admin_ids():
        keyboard.add(KeyboardButton("🔧 Админ-панель"))

    return keyboard

def get_traveler_keyboard(user_id):
    """Создает клавиатуру для путешественника с динамической информацией."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_view_tours = types.KeyboardButton("🗺️ Посмотреть экскурсии")
    btn_search = types.KeyboardButton("🔍 Поиск по ключевым словам")  # Новая кнопка
    btn_filter_price = types.KeyboardButton("💰 Фильтр по цене")
    btn_filter_date = types.KeyboardButton("📅 Фильтр по дате")
    bookings = get_bookings_by_user(user_id)
    btn_cancel_booking = types.KeyboardButton(f"❌ Отменить запись ({len(bookings)})")
    btn_cabinet = types.KeyboardButton("🌴 Личный кабинет")
    btn_back = types.KeyboardButton("↩️ Вернуться в меню")
    markup.add(btn_view_tours, btn_search)
    markup.add(btn_filter_price, btn_filter_date)
    markup.add(btn_cancel_booking, btn_cabinet)
    markup.add(btn_back)
    return markup

def get_guide_keyboard():
    """Создает клавиатуру для гида."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_add_tour = types.KeyboardButton("➕ Добавить маршрут")
    btn_my_tours = types.KeyboardButton("📋 Мои экскурсии")
    btn_back = types.KeyboardButton("↩️ Вернуться в меню")
    markup.add(btn_add_tour, btn_my_tours)
    markup.add(btn_back)
    return markup

def get_admin_keyboard():
    """Создает клавиатуру для админа."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_guides = types.KeyboardButton("📋 Список гидов")
    btn_tours = types.KeyboardButton("🗺️ Список экскурсий")
    btn_stats = types.KeyboardButton("📊 Статистика")
    btn_back = types.KeyboardButton("↩️ Вернуться в меню")
    markup.add(btn_guides, btn_tours)
    markup.add(btn_stats, btn_back)
    return markup

def get_cancel_keyboard():
    """Создает инлайн-клавиатуру с кнопкой 'Отмена'."""
    markup = types.InlineKeyboardMarkup()
    btn_cancel = types.InlineKeyboardButton("❌ Отмена", callback_data=CANCEL_REQUEST)
    markup.add(btn_cancel)
    return markup

def get_info_keyboard():
    """Создает клавиатуру для раздела 'О боте'."""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_feedback = types.KeyboardButton("📝 Оставить отзыв о боте")
    btn_back = types.KeyboardButton("↩️ Вернуться в меню")
    markup.add(btn_feedback, btn_back)
    return markup

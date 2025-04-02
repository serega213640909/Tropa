# utils.py
import logging
from datetime import datetime, timedelta
from aiogram import Bot
from database import get_pending_notifications, mark_notification_as_sent, get_subscribers_for_excursion, add_notification, get_excursion, get_excursion_locations, get_booking
import aiohttp
import json
import os
from dotenv import load_dotenv
from typing import Dict
from constants import (
    NOTIFICATION_NEW_BOOKING, NOTIFICATION_REMINDER, NOTIFICATION_NEW_REQUEST, NOTIFICATION_NEW_COMPLAINT,
    WEATHER_RECOMMENDATION_RAIN, WEATHER_RECOMMENDATION_SUN, WEATHER_RECOMMENDATION_COLD
)

# Загрузка переменных окружения
load_dotenv()

logger = logging.getLogger(__name__)

# Настройки для Яндекс API
YANDEX_WEATHER_API_KEY = os.getenv("YANDEX_WEATHER_API_KEY", "your_yandex_weather_api_key")
YANDEX_MAPS_API_KEY = os.getenv("YANDEX_MAPS_API_KEY", "your_yandex_maps_api_key")
YANDEX_TAXI_API_KEY = os.getenv("YANDEX_TAXI_API_KEY", "your_yandex_taxi_api_key")

def get_time_greeting() -> tuple[str, str]:
    """Возвращает приветствие в зависимости от времени суток."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро", "Надеюсь, ты готов к новым приключениям! 🌞"
    elif 12 <= hour < 17:
        return "Добрый день", "Самое время отправиться на экскурсию! ☀️"
    elif 17 <= hour < 23:
        return "Добрый вечер", "Как насчёт вечерней прогулки? 🌆"
    else:
        return "Доброй ночи", "Может, выберешь экскурсию на завтра? 🌙"

async def notify_users(bot: Bot):
    """Отправляет уведомления пользователям."""
    try:
        notifications = await get_pending_notifications()
        for notification in notifications:
            try:
                await bot.send_message(
                    chat_id=notification["user_id"],
                    text=notification["message"]
                )
                await mark_notification_as_sent(notification["id"])
                logger.info(f"Уведомление отправлено пользователю {notification['user_id']}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления пользователю {notification['user_id']}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при получении уведомлений: {e}")

async def notify_new_excursion(bot: Bot, excursion_id: int):
    """Уведомляет подписчиков о новом маршруте."""
    try:
        excursion = await get_excursion(excursion_id)
        if not excursion:
            return
        guide_id = excursion["guide_id"]
        city = excursion["city"]
        keywords = excursion["keywords"]
        subscribers = await get_subscribers_for_excursion(guide_id, city, keywords)
        for subscriber in subscribers:
            message = (
                f"Новый маршрут: {excursion['title']}\n"
                f"Город: {excursion['city']}\n"
                f"Тематика: {excursion['theme']}\n"
                f"Чтобы забронировать, напиши: /book_{excursion['id']}"
            )
            await add_notification(subscriber["user_id"], message)
    except Exception as e:
        logger.error(f"Ошибка при уведомлении о новом маршруте: {e}")

async def notify_new_booking(bot: Bot, guide_id: int, title: str, user_id: int):
    """Уведомляет гида о новом бронировании."""
    try:
        message = NOTIFICATION_NEW_BOOKING.format(title=title)
        await add_notification(guide_id, message)
        logger.info(f"Уведомление о новом бронировании отправлено гиду {guide_id} от пользователя {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при уведомлении о новом бронировании: {e}")

async def notify_new_request(bot: Bot, user_id: int, request_text: str):
    """Уведомляет администратора о новой заявке."""
    try:
        from database import get_admin_ids
        message = NOTIFICATION_NEW_REQUEST.format(request_text=request_text)
        for admin_id in get_admin_ids():
            await add_notification(admin_id, message)
    except Exception as e:
        logger.error(f"Ошибка при уведомлении о новой заявке: {e}")

async def notify_complaint(bot: Bot, excursion_id: int, chat_id: int):
    """Уведомляет администратора о жалобе в чате."""
    try:
        from database import get_admin_ids
        chat_link = f"https://t.me/c/{chat_id}"
        message = NOTIFICATION_NEW_COMPLAINT.format(excursion_id=excursion_id, chat_link=chat_link)
        for admin_id in get_admin_ids():
            await add_notification(admin_id, message)
    except Exception as e:
        logger.error(f"Ошибка при уведомлении о жалобе: {e}")

async def schedule_excursion_reminder(bot: Bot, booking_id: int, reminder_time: datetime):
    """Планирует напоминание перед экскурсией."""
    try:
        booking = await get_booking(booking_id)
        if not booking:
            return
        excursion = await get_excursion(booking["excursion_id"])
        start_location = await get_excursion_locations(booking["excursion_id"])
        dates = excursion["dates"].split(",")
        if not dates:
            return
        # Берём ближайшую дату
        start_time = min([datetime.fromisoformat(date) for date in dates])
        if start_time < datetime.now():
            return  # Экскурсия уже прошла

        # Получаем погоду
        weather = await get_weather(start_location["lat"], start_location["lon"], start_time)
        recommendation = get_weather_recommendation(weather)

        # Предполагаем, что у пользователя есть текущая геолокация (добавим позже)
        user_location = {"lat": 55.7558, "lon": 37.6173}  # Пример: Москва
        travel_time, map_link = await get_travel_info(user_location, start_location)

        time_until = (start_time - datetime.now()).total_seconds() / 3600  # В часах
        message = NOTIFICATION_REMINDER.format(
            title=excursion["title"],
            time=f"{time_until:.1f} ч",
            start_location=f"({start_location['lat']}, {start_location['lon']})",
            travel_time=f"{travel_time} мин",
            weather=weather,
            recommendation=recommendation,
            map_link=map_link,
            booking_id=booking_id
        )
        await add_notification(booking["user_id"], message)
    except Exception as e:
        logger.error(f"Ошибка при планировании напоминания: {e}")

async def get_weather(lat: float, lon: float, date: datetime) -> str:
    """Получает прогноз погоды через Яндекс Погода API."""
    try:
        url = "https://api.weather.yandex.ru/v2/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "lang": "ru_RU",
            "limit": 1,
            "hours": True,
            "extra": True
        }
        headers = {"X-Yandex-API-Key": YANDEX_WEATHER_API_KEY}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при получении погоды: {response.status}")
                    return "Неизвестно"
                data = await response.json()
                temp = data["fact"]["temp"]
                condition = data["fact"]["condition"]
                return f"{temp}°C, {condition}"
    except Exception as e:
        logger.error(f"Ошибка при получении погоды: {e}")
        return "Неизвестно"

def get_weather_recommendation(weather: str) -> str:
    """Возвращает рекомендацию на основе погоды."""
    if "rain" in weather.lower() or "shower" in weather.lower():
        return WEATHER_RECOMMENDATION_RAIN
    elif "clear" in weather.lower() or "sunny" in weather.lower():
        return WEATHER_RECOMMENDATION_SUN
    elif "cold" in weather.lower() or int(weather.split("°C")[0]) < 5:
        return WEATHER_RECOMMENDATION_COLD
    return ""

async def get_travel_info(start: Dict[str, float], end: Dict[str, float]) -> tuple[int, str]:
    """Получает время в пути и ссылку на маршрут через Яндекс Карты API."""
    try:
        url = "https://api.routing.yandex.net/v2/route"
        params = {
            "waypoints": f"{start['lat']},{start['lon']}|{end['lat']},{end['lon']}",
            "mode": "walking",  # Можно добавить выбор: walking, driving
            "apikey": YANDEX_MAPS_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при получении маршрута: {response.status}")
                    return 0, "Неизвестно"
                data = await response.json()
                duration = data["routes"][0]["duration"] // 60  # В минутах
                map_link = f"https://yandex.ru/maps/?rtext={start['lat']},{start['lon']}~{end['lat']},{end['lon']}&rtt=auto"
                return duration, map_link
    except Exception as e:
        logger.error(f"Ошибка при получении маршрута: {e}")
        return 0, "Неизвестно"

async def call_taxi(user_location: Dict[str, float], destination: Dict[str, float]) -> str:
    """Вызывает такси через Яндекс Такси API."""
    try:
        url = "https://taxi-routeinfo.taxi.yandex.net/route_info"
        params = {
            "cl": "econom",
            "rll": f"{user_location['lon']},{user_location['lat']}~{destination['lon']},{destination['lat']}",
            "apikey": YANDEX_TAXI_API_KEY
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при вызове такси: {response.status}")
                    return "Ошибка при вызове такси."
                data = await response.json()
                price = data["options"][0]["price"]
                order_url = f"https://taxi.yandex.ru/order?cl=econom&from={user_location['lat']},{user_location['lon']}&to={destination['lat']},{destination['lon']}"
                return f"Такси заказано! Стоимость: {price} руб. Перейди для подтверждения: {order_url}"
    except Exception as e:
        logger.error(f"Ошибка при вызове такси: {e}")
        return "Ошибка при вызове такси."

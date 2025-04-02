# database.py
import aiosqlite
from typing import List, Dict, Any
from datetime import datetime

DB_NAME = "bot_database.db"

async def init_db():
    """Инициализирует базу данных."""
    async with aiosqlite.connect(DB_NAME) as db:
        # Уровень отступа: 4 пробела
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guides (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                city TEXT,
                description TEXT,
                experience INTEGER,
                is_approved BOOLEAN DEFAULT 0,
                rating REAL DEFAULT 0.0,
                review_count INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS excursions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guide_id INTEGER,
                title TEXT,
                city TEXT,
                theme TEXT,
                description TEXT,
                price INTEGER,
                dates TEXT,
                keywords TEXT,
                start_location_lat REAL,
                start_location_lon REAL,
                is_approved BOOLEAN DEFAULT 0,
                FOREIGN KEY (guide_id) REFERENCES guides(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                excursion_id INTEGER,
                created_at TEXT,
                status TEXT,
                FOREIGN KEY (excursion_id) REFERENCES excursions(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                guide_id INTEGER,
                rating INTEGER,
                comment TEXT,
                created_at TEXT,
                FOREIGN KEY (guide_id) REFERENCES guides(user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                city TEXT,
                keywords TEXT,
                created_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                user_id INTEGER PRIMARY KEY,
                guide_id INTEGER,
                city TEXT,
                keywords TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                is_sent BOOLEAN DEFAULT 0,
                created_at TEXT
            )
        """)
        await db.commit()

def get_admin_ids() -> List[int]:
    """Возвращает список ID администраторов."""
    return [123456789]  # Пример ID администратора

async def get_all_guides() -> List[Dict[str, Any]]:
    """Возвращает список всех гидов."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM guides")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_guide(user_id: int) -> Dict[str, Any]:
    """Возвращает информацию о гиде по его ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM guides WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return {}

async def register_guide(user_id: int, first_name: str = "", last_name: str = "", city: str = "", description: str = "", experience: int = 0) -> None:
    """Регистрирует нового гида."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO guides (user_id, first_name, last_name, city, description, experience) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, first_name, last_name, city, description, experience)
        )
        await db.commit()

async def approve_guide(user_id: int) -> None:
    """Одобряет гида."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE guides SET is_approved = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

async def get_excursions() -> List[Dict[str, Any]]:
    """Возвращает список всех маршрутов."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM excursions WHERE is_approved = 1")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_pending_excursions() -> List[Dict[str, Any]]:
    """Возвращает список маршрутов, ожидающих модерации."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM excursions WHERE is_approved = 0")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_excursions_by_guide(guide_id: int) -> List[Dict[str, Any]]:
    """Возвращает маршруты конкретного гида."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM excursions WHERE guide_id = ? AND is_approved = 1", (guide_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_excursion(excursion_id: int) -> Dict[str, Any]:
    """Возвращает информацию о маршруте по его ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM excursions WHERE id = ?", (excursion_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return {}

async def get_excursion_locations(excursion_id: int) -> Dict[str, float]:
    """Возвращает координаты начальной точки маршрута."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT start_location_lat, start_location_lon FROM excursions WHERE id = ?", (excursion_id,))
        row = await cursor.fetchone()
        if row:
            return {"lat": row[0], "lon": row[1]}
        return {}

async def add_excursion(guide_id: int, title: str, city: str, theme: str, description: str, price: int, dates: List[str], keywords: str = "", start_location_lat: float = 0.0, start_location_lon: float = 0.0) -> int:
    """Добавляет новый маршрут."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO excursions (guide_id, title, city, theme, description, price, dates, keywords, start_location_lat, start_location_lon) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (guide_id, title, city, theme, description, price, ",".join(dates), keywords, start_location_lat, start_location_lon)
        )
        await db.commit()
        return cursor.lastrowid

async def approve_excursion(excursion_id: int) -> None:
    """Одобряет маршрут."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE excursions SET is_approved = 1 WHERE id = ?", (excursion_id,))
        await db.commit()

async def get_stats() -> Dict[str, int]:
    """Возвращает статистику."""
    async with aiosqlite.connect(DB_NAME) as db:
        guides_total = await (await db.execute("SELECT COUNT(*) FROM guides")).fetchone()
        guides_approved = await (await db.execute("SELECT COUNT(*) FROM guides WHERE is_approved = 1")).fetchone()
        guides_pending = await (await db.execute("SELECT COUNT(*) FROM guides WHERE is_approved = 0")).fetchone()
        excursions_total = await (await db.execute("SELECT COUNT(*) FROM excursions")).fetchone()
        excursions_approved = await (await db.execute("SELECT COUNT(*) FROM excursions WHERE is_approved = 1")).fetchone()
        excursions_pending = await (await db.execute("SELECT COUNT(*) FROM excursions WHERE is_approved = 0")).fetchone()
        travelers_total = await (await db.execute("SELECT COUNT(DISTINCT user_id) FROM bookings")).fetchone()
        requests_total = await (await db.execute("SELECT COUNT(*) FROM requests")).fetchone()
        return {
            "guides_total": guides_total[0],
            "guides_approved": guides_approved[0],
            "guides_pending": guides_pending[0],
            "excursions_total": excursions_total[0],
            "excursions_approved": excursions_approved[0],
            "excursions_pending": excursions_pending[0],
            "travelers_total": travelers_total[0],
            "requests_total": requests_total[0]
        }

async def get_bookings_by_excursion(excursion_id: int) -> List[Dict[str, Any]]:
    """Возвращает бронирования для маршрута."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM bookings WHERE excursion_id = ?", (excursion_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_bookings_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Возвращает бронирования пользователя."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM bookings WHERE user_id = ?", (user_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def get_booking(booking_id: int) -> Dict[str, Any]:
    """Возвращает информацию о бронировании по его ID."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM bookings WHERE id = ?", (booking_id,))
        row = await cursor.fetchone()
        if row:
            columns = [description[0] for description in cursor.description]
            return dict(zip(columns, row))
        return {}

async def book_excursion(user_id: int, excursion_id: int) -> int:
    """Создаёт бронирование."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "INSERT INTO bookings (user_id, excursion_id, created_at, status) VALUES (?, ?, ?, ?)",
            (user_id, excursion_id, datetime.now().isoformat(), "Подтверждено")
        )
        await db.commit()
        return cursor.lastrowid

async def get_reviews_by_guide(guide_id: int) -> List[Dict[str, Any]]:
    """Возвращает отзывы о гиде."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM reviews WHERE guide_id = ?", (guide_id,))
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def add_review(user_id: int, guide_id: int, rating: int, comment: str) -> None:
    """Добавляет отзыв о гиде."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO reviews (user_id, guide_id, rating, comment, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, guide_id, rating, comment, datetime.now().isoformat())
        )
        await db.commit()

async def get_requests() -> List[Dict[str, Any]]:
    """Возвращает список заявок."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM requests")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def add_request(user_id: int, city: str, keywords: str) -> None:
    """Добавляет новую заявку."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO requests (user_id, city, keywords, created_at) VALUES (?, ?, ?, ?)",
            (user_id, city, keywords, datetime.now().isoformat())
        )
        await db.commit()

async def get_subscribers() -> List[int]:
    """Возвращает список подписчиков."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM subscribers")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

async def get_subscribers_for_excursion(guide_id: int, city: str, keywords: str) -> List[Dict[str, Any]]:
    """Возвращает подписчиков, которые могут быть заинтересованы в маршруте."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT * FROM subscribers WHERE guide_id = ? OR city = ? OR keywords LIKE ?",
            (guide_id, city, f"%{keywords}%")
        )
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def add_notification(user_id: int, message: str) -> None:
    """Добавляет новое уведомление."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT INTO notifications (user_id, message, created_at) VALUES (?, ?, ?)",
            (user_id, message, datetime.now().isoformat())
        )
        await db.commit()

async def get_pending_notifications() -> List[Dict[str, Any]]:
    """Возвращает список неотправленных уведомлений."""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM notifications WHERE is_sent = 0")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

async def mark_notification_as_sent(notification_id: int) -> None:
    """Помечает уведомление как отправленное."""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE notifications SET is_sent = 1 WHERE id = ?", (notification_id,))
        await db.commit()

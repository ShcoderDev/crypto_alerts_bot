import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Optional
from bot.models import User, PriceAlert
from bot.config import DATABASE_PATH


class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path

    async def init_db(self):
        """Создание таблиц в базе данных"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблица пользователей
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    tg_id INTEGER PRIMARY KEY,
                    username TEXT,
                    registration_date TEXT NOT NULL
                )
            """)
            
            # Таблица алертов
            await db.execute("""
                CREATE TABLE IF NOT EXISTS price_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    cryptocurrency TEXT NOT NULL,
                    target_price REAL NOT NULL,
                    is_above INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(tg_id)
                )
            """)
            
            await db.commit()

    async def create_user(self, tg_id: int, username: Optional[str] = None) -> User:
        """Создание нового пользователя"""
        registration_date = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO users (tg_id, username, registration_date)
                VALUES (?, ?, ?)
            """, (tg_id, username, registration_date))
            await db.commit()
        
        return User(tg_id=tg_id, username=username, registration_date=datetime.fromisoformat(registration_date))

    async def get_user(self, tg_id: int) -> Optional[User]:
        """Получение пользователя по tg_id"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return User(
                        tg_id=row["tg_id"],
                        username=row["username"],
                        registration_date=datetime.fromisoformat(row["registration_date"])
                    )
        return None

    async def create_alert(self, user_id: int, cryptocurrency: str, target_price: float, is_above: bool) -> PriceAlert:
        """Создание нового алерта"""
        created_at = datetime.now().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO price_alerts (user_id, cryptocurrency, target_price, is_above, created_at, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (user_id, cryptocurrency, target_price, 1 if is_above else 0, created_at))
            await db.commit()
            alert_id = cursor.lastrowid
        
        return PriceAlert(
            id=alert_id,
            user_id=user_id,
            cryptocurrency=cryptocurrency,
            target_price=target_price,
            is_above=is_above,
            created_at=datetime.fromisoformat(created_at),
            is_active=True
        )

    async def get_user_alerts(self, user_id: int) -> List[PriceAlert]:
        """Получение всех алертов пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM price_alerts 
                WHERE user_id = ? AND is_active = 1
                ORDER BY created_at DESC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    PriceAlert(
                        id=row["id"],
                        user_id=row["user_id"],
                        cryptocurrency=row["cryptocurrency"],
                        target_price=row["target_price"],
                        is_above=bool(row["is_above"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        is_active=bool(row["is_active"])
                    )
                    for row in rows
                ]

    async def get_alert(self, alert_id: int) -> Optional[PriceAlert]:
        """Получение алерта по ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM price_alerts WHERE id = ?", (alert_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return PriceAlert(
                        id=row["id"],
                        user_id=row["user_id"],
                        cryptocurrency=row["cryptocurrency"],
                        target_price=row["target_price"],
                        is_above=bool(row["is_above"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        is_active=bool(row["is_active"])
                    )
        return None

    async def update_alert(self, alert_id: int, cryptocurrency: Optional[str] = None, 
                          target_price: Optional[float] = None, is_above: Optional[bool] = None) -> bool:
        """Обновление алерта"""
        updates = []
        params = []
        
        if cryptocurrency is not None:
            updates.append("cryptocurrency = ?")
            params.append(cryptocurrency)
        if target_price is not None:
            updates.append("target_price = ?")
            params.append(target_price)
        if is_above is not None:
            updates.append("is_above = ?")
            params.append(1 if is_above else 0)
        
        if not updates:
            return False
        
        params.append(alert_id)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE price_alerts 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            await db.commit()
            return True

    async def delete_alert(self, alert_id: int) -> bool:
        """Удаление алерта (деактивация)"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE price_alerts SET is_active = 0 WHERE id = ?", (alert_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def get_all_active_alerts(self) -> List[PriceAlert]:
        """Получение всех активных алертов (для мониторинга цен)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM price_alerts WHERE is_active = 1") as cursor:
                rows = await cursor.fetchall()
                return [
                    PriceAlert(
                        id=row["id"],
                        user_id=row["user_id"],
                        cryptocurrency=row["cryptocurrency"],
                        target_price=row["target_price"],
                        is_above=bool(row["is_above"]),
                        created_at=datetime.fromisoformat(row["created_at"]),
                        is_active=bool(row["is_active"])
                    )
                    for row in rows
                ]

    async def deactivate_alert(self, alert_id: int) -> bool:
        """Деактивация алерта после срабатывания"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("UPDATE price_alerts SET is_active = 0 WHERE id = ?", (alert_id,))
            await db.commit()
            return cursor.rowcount > 0


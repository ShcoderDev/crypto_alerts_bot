import sqlite3
import aiosqlite
from datetime import datetime
from typing import List, Optional
from bot.database import Database as BotDatabase
from bot.models import PriceAlert
from bot.config import DATABASE_PATH


# Используем ту же базу данных, что и бот
class Database(BotDatabase):
    def __init__(self, db_path: str = DATABASE_PATH):
        super().__init__(db_path)


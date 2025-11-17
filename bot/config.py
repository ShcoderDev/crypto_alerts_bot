import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")

# Список основных криптовалют
CRYPTOCURRENCIES = [
    "BTC",
    "ETH",
    "BNB",
    "SOL",
    "XRP",
    "ADA",
    "DOGE",
    "DOT",
    "MATIC",
    "AVAX"
]

# Путь к базе данных
DATABASE_PATH = "database.db"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

if not MINIAPP_URL:
    raise ValueError("MINIAPP_URL не найден в .env файле")


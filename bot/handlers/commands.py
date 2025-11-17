from aiogram import Router, F
from aiogram.types import Message, WebAppInfo
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.database import Database
from bot.config import MINIAPP_URL

router = Router()
db = Database()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    user = message.from_user
    
    # Регистрация пользователя в БД
    await db.create_user(tg_id=user.id, username=user.username)
    
    # Создание кнопки для открытия MiniApp
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🚀 Открыть MiniApp",
        web_app=WebAppInfo(url=MINIAPP_URL)
    )
    
    await message.answer(
        f"Привет, {user.first_name}! 👋\n\n"
        "Я помогу тебе отслеживать цены криптовалют.\n"
        "Нажми на кнопку ниже, чтобы открыть MiniApp и настроить уведомления о ценах.",
        reply_markup=builder.as_markup()
    )


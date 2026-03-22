from telegram import Update
from telegram.ext import ContextTypes

from keyboards import main_keyboard
from service import UserService
from database import get_session, close


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    session = get_session()
    try:
        user_service = UserService(session)

        user = user_service.get_or_create(
            user_id=update.effective_user.id,
            username=update.effective_user.username or ""
        )

        await update.message.reply_text(
            "Добро пожаловать! Выберите действие:",
            reply_markup=main_keyboard()
        )
    finally:
        close(session)
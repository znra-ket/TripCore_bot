from telegram import Update
from telegram.ext import ContextTypes

from keyboards import main_keyboard
from service import UserService
from database import get_session, close
from handlers.invitation import handle_invite_start


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start."""
    # Проверяем, есть ли параметр (для deep link с приглашением)
    if context.args and len(context.args) > 0:
        start_param = context.args[0]
        if start_param.startswith("invite_"):
            # Это ссылка-приглашение - передаём обработку в handle_invite_start
            await handle_invite_start(update, context)
            return

    session = get_session()
    try:
        user_service = UserService(session)

        user = user_service.get_or_create(
            user_id=update.effective_user.id,
            username=update.effective_user.username or "",
            first_name=update.effective_user.first_name
        )

        await update.message.reply_text(
            "Добро пожаловать! Выберите действие:",
            reply_markup=main_keyboard()
        )
    finally:
        close(session)
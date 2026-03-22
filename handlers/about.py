from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from service import AgentService, UserService
from database import get_session
from keyboards import main_keyboard


async def show_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ ИИ досье пользователя."""
    await update.callback_query.answer()

    user_id = update.effective_user.id
    name = update.effective_user.name

    session = get_session()
    agent_service = AgentService(session)

    dossier = agent_service.generate_user_dossier(user_id)

    await update.callback_query.message.edit_text(
        f"📋 <b>Досье пользователя</b>\n\nПривет, {name}!\n{dossier}",
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )

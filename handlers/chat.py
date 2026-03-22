from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from keyboards import main_keyboard, chat_mode_keyboard
from service import AgentService
from database import get_session, close


WAITING_FOR_MESSAGE = 1


async def start_chat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало чат-мода с ИИ."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "🤖 <b>Чат с ИИ</b>\n\n"
        "Задайте любой вопрос или попросите о помощи. "
        "Я отвечу на ваш запрос.\n\n"
        "Для выхода нажмите кнопку ниже.",
        reply_markup=chat_mode_keyboard(),
        parse_mode="HTML"
    )
    return WAITING_FOR_MESSAGE


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение сообщения от пользователя и отправка ИИ."""
    user_message = update.message.text

    session = get_session()
    try:
        agent_service = AgentService(session)

        # Генерация ответа через ИИ
        response = agent_service.chat_with_ai(user_message)

        # Отправка ответа пользователю (не редактирование, а новое сообщение)
        await update.message.reply_text(
            f"🤖 {response}",
            reply_markup=chat_mode_keyboard()
        )
    finally:
        close()

    return WAITING_FOR_MESSAGE


async def exit_chat_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из чат-мода."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Вы вышли из чата с ИИ.",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def chat_mode_fallback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для выхода из чат-мода через команду."""
    await update.message.reply_text(
        "Вы вышли из чата с ИИ.",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


chat_mode_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_chat_mode, pattern=r"^chat_mod$")],
    states={
        WAITING_FOR_MESSAGE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message),
            CallbackQueryHandler(exit_chat_mode, pattern=r"^chat_exit$"),
        ],
    },
    fallbacks=[MessageHandler(filters.COMMAND, chat_mode_fallback)],
    per_message=False,
)

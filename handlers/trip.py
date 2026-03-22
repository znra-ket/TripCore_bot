from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from keyboards import main_keyboard, cancel_keyboard, trips_keyboard, notes_menu_keyboard
from service import TripService
from database import get_session, close


async def safe_edit_message(update: Update, text: str, reply_markup=None, parse_mode: str = None):
    """
    Безопасное редактирование сообщения.
    Если сообщение содержит медиа, отправляем новое сообщение вместо редактирования.
    """
    try:
        await update.callback_query.message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except BadRequest as e:
        if "There is no text in the message to edit" in str(e) or "Message is not modified" in str(e):
            # Сообщение с медиа или не изменено - отправляем новое
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            raise


WAITING_FOR_TITLE = 1


async def start_create_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога создания поездки."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Введите название поездки:",
        reply_markup=cancel_keyboard()
    )
    return WAITING_FOR_TITLE


async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия и создание поездки."""
    title = update.message.text

    session = get_session()
    try:
        trip_service = TripService(session)

        trip = trip_service.create(
            user_id=update.effective_user.id,
            title=title
        )

        await update.message.reply_text(
            f"✅ Поездка «{trip.title}» успешно создана!",
            reply_markup=main_keyboard()
        )
    finally:
        close()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания поездки и возврат к главному меню."""
    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_keyboard()
    )
    return ConversationHandler.END


async def show_my_trips(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка поездок пользователя с пагинацией."""
    await update.callback_query.answer()

    session = get_session()
    try:
        trip_service = TripService(session)

        trips = trip_service.get_by_user_id(update.effective_user.id)

        if not trips:
            await update.callback_query.message.edit_text(
                "📭 У вас пока нет поездок.\n\nСоздайте первую поездку, нажав «Создать поездку» в главном меню.",
                reply_markup=main_keyboard()
            )
            return

        await update.callback_query.message.edit_text(
            "📋 <b>Мои поездки</b>\n\nВыберите поездку:",
            reply_markup=trips_keyboard(trips, page=0),
            parse_mode="HTML"
        )
    finally:
        close()


async def trips_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение страницы списка поездок."""
    await update.callback_query.answer()

    session = get_session()
    try:
        trip_service = TripService(session)

        trips = trip_service.get_by_user_id(update.effective_user.id)

        page = int(context.match.group(1))

        await update.callback_query.message.edit_text(
            "📋 <b>Мои поездки</b>\n\nВыберите поездку:",
            reply_markup=trips_keyboard(trips, page=page),
            parse_mode="HTML"
        )
    finally:
        close()


async def trip_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр деталей поездки."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    session = get_session()
    try:
        trip_service = TripService(session)

        trip = trip_service.get_by_id(trip_id)

        if trip is None:
            await safe_edit_message(
                update,
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return

        # Показываем сгенерированное описание, если оно есть
        description_text = trip.description if trip.description else "📝 Нет описания"

        await safe_edit_message(
            update,
            f"🚗 <b>{trip.title}</b>\n\n{description_text}",
            reply_markup=notes_menu_keyboard(trip_id),
            parse_mode="HTML"
        )
    finally:
        close()


async def trips_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к главному меню из списка поездок."""
    await update.callback_query.answer()
    await safe_edit_message(
        update,
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_keyboard()
    )


async def show_trips_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка поездок пользователя."""
    await update.callback_query.answer()

    session = get_session()
    try:
        trip_service = TripService(session)

        trips = trip_service.get_by_user_id(update.effective_user.id)

        if not trips:
            await safe_edit_message(
                update,
                "📭 У вас пока нет поездок.\n\nСоздайте первую поездку, нажав «Создать поездку» в главном меню.",
                reply_markup=main_keyboard()
            )
            return

        await safe_edit_message(
            update,
            "📋 <b>Мои поездки</b>\n\nВыберите поездку:",
            reply_markup=trips_keyboard(trips, page=0),
            parse_mode="HTML"
        )
    finally:
        close()


conversation_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_create_trip, pattern="^create_trip$")],
    states={
        WAITING_FOR_TITLE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title),
            CallbackQueryHandler(cancel, pattern="^cancel$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$")],
    per_message=False,
)

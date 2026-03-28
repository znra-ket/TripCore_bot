from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from keyboards import (
    trip_settings_keyboard,
    trip_rename_keyboard,
    trip_delete_confirm_keyboard,
    notes_menu_keyboard,
    main_keyboard,
)
from service import TripService, InvitationService
from database import get_session, close


WAITING_FOR_NEW_TITLE = 1
WAITING_FOR_DELETE_CONFIRM = 2


async def start_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие меню настроек поездки."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        # Проверка, что пользователь является владельцем
        if not invitation_service.has_access_to_trip(user_id, trip_id):
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к этой поездке.",
                reply_markup=main_keyboard()
            )
            return

        trip = trip_service.get_by_id(trip_id)

        if trip is None:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return

        # Только владелец может редактировать настройки
        if trip.user_id != user_id:
            await update.callback_query.message.edit_text(
                "❌ Только владелец поездки может изменять её настройки.",
                reply_markup=notes_menu_keyboard(trip_id, is_owner=False, is_admin=False)
            )
            return

        await update.callback_query.message.edit_text(
            f"⚙️ <b>Настройки поездки</b>\n\n"
            f"📍 <b>{trip.title}</b>\n\n"
            f"Выберите действие:",
            reply_markup=trip_settings_keyboard(trip_id),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def start_rename_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало переименования поездки."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["settings_trip_id"] = trip_id

    await update.callback_query.message.edit_text(
        "✏️ Введите новое название поездки:",
        reply_markup=trip_rename_keyboard(trip_id)
    )
    return WAITING_FOR_NEW_TITLE


async def receive_new_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохранение нового названия поездки."""
    new_title = update.message.text.strip()

    if not new_title:
        await update.message.reply_text(
            "❌ Название не может быть пустым. Введите название:",
            reply_markup=trip_rename_keyboard(context.user_data.get("settings_trip_id"))
        )
        return WAITING_FOR_NEW_TITLE

    trip_id = context.user_data.get("settings_trip_id")

    session = get_session()
    try:
        trip_service = TripService(session)

        trip = trip_service.update_title(trip_id, new_title)

        if trip:
            await update.message.reply_text(
                f"✅ Название поездки изменено на <b>{new_title}</b>",
                reply_markup=trip_settings_keyboard(trip_id),
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "❌ Не удалось изменить название поездки.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
    finally:
        close(session)

    # Очистка данных
    context.user_data.pop("settings_trip_id", None)

    return WAITING_FOR_NEW_TITLE


async def cancel_rename(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена переименования и возврат к настройкам."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    # Очистка данных
    context.user_data.pop("settings_trip_id", None)

    session = get_session()
    try:
        trip_service = TripService(session)
        trip = trip_service.get_by_id(trip_id)

        if trip:
            await update.callback_query.message.edit_text(
                f"⚙️ <b>Настройки поездки</b>\n\n"
                f"📍 <b>{trip.title}</b>\n\n"
                f"Выберите действие:",
                reply_markup=trip_settings_keyboard(trip_id),
                parse_mode="HTML"
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
    finally:
        close(session)

    return ConversationHandler.END


async def start_delete_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало удаления поездки."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    session = get_session()
    try:
        trip_service = TripService(session)
        trip = trip_service.get_by_id(trip_id)

        if trip:
            context.user_data["delete_trip_id"] = trip_id

            await update.callback_query.message.edit_text(
                f"⚠️ <b>Удаление поездки</b>\n\n"
                f"Вы действительно хотите удалить поездку <b>{trip.title}</b>?\n\n"
                f"🗑️ Все заметки и приглашения будут удалены без возможности восстановления.",
                reply_markup=trip_delete_confirm_keyboard(trip_id),
                parse_mode="HTML"
            )
            return WAITING_FOR_DELETE_CONFIRM
        else:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END
    finally:
        close(session)


async def confirm_delete_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и выполнение удаления поездки."""
    await update.callback_query.answer()

    trip_id = context.user_data.get("delete_trip_id")

    session = get_session()
    try:
        trip_service = TripService(session)

        trip = trip_service.get_by_id(trip_id)
        trip_title = trip.title if trip else "поездки"

        result = trip_service.delete_trip(trip_id)

        if result:
            await update.callback_query.message.edit_text(
                f"✅ Поездка <b>{trip_title}</b> успешно удалена.",
                reply_markup=main_keyboard(),
                parse_mode="HTML"
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Не удалось удалить поездку.",
                reply_markup=main_keyboard()
            )
    finally:
        close(session)

    # Очистка данных
    context.user_data.pop("delete_trip_id", None)

    return ConversationHandler.END


async def cancel_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена удаления и возврат к настройкам."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    # Очистка данных
    context.user_data.pop("delete_trip_id", None)

    session = get_session()
    try:
        trip_service = TripService(session)
        trip = trip_service.get_by_id(trip_id)

        if trip:
            await update.callback_query.message.edit_text(
                f"⚙️ <b>Настройки поездки</b>\n\n"
                f"📍 <b>{trip.title}</b>\n\n"
                f"Выберите действие:",
                reply_markup=trip_settings_keyboard(trip_id),
                parse_mode="HTML"
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
    finally:
        close(session)

    return ConversationHandler.END


# Обработчик диалога настроек
trip_settings_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_settings, pattern=r"^trip_settings_(\d+)$"),
        CallbackQueryHandler(start_rename_trip, pattern=r"^trip_rename_(\d+)$"),
        CallbackQueryHandler(start_delete_trip, pattern=r"^trip_delete_(\d+)$"),
    ],
    states={
        WAITING_FOR_NEW_TITLE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_title),
            CallbackQueryHandler(cancel_rename, pattern=r"^trip_settings_(\d+)$"),
        ],
        WAITING_FOR_DELETE_CONFIRM: [
            CallbackQueryHandler(confirm_delete_trip, pattern=r"^trip_delete_confirm_(\d+)$"),
            CallbackQueryHandler(cancel_delete, pattern=r"^trip_settings_(\d+)$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(cancel_rename, pattern=r"^trip_settings_(\d+)$"),
        CallbackQueryHandler(cancel_delete, pattern=r"^trip_settings_(\d+)$"),
    ],
    per_message=False,
)

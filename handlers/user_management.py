from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)

from keyboards import (
    users_list_keyboard,
    user_action_keyboard,
    user_delete_confirm_keyboard,
    trip_settings_keyboard,
    main_keyboard,
)
from service import InvitationService, TripService
from database import get_session, close


WAITING_FOR_DELETE_CONFIRM = 1


async def start_user_management(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Открытие меню управления пользователями."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        # Проверка, что пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)

        if trip is None:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return

        if trip.user_id != user_id:
            await update.callback_query.message.edit_text(
                "❌ Только владелец поездки может управлять пользователями.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
            return

        # Получение списка пользователей
        users = invitation_service.get_users_with_access(trip_id)

        await update.callback_query.message.edit_text(
            f"👥 <b>Управление пользователями</b>\n\n"
            f"Поездка: <b>{trip.title}</b>\n\n"
            f"Всего пользователей: {len(users)}\n\n"
            f"👑 — владелец поездки\n"
            f"Выберите пользователя:",
            reply_markup=users_list_keyboard(users, trip_id, page=0),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def show_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка пользователей с пагинацией."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    page = int(context.match.group(2))
    user_id = update.effective_user.id

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        # Проверка, что пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)

        if trip is None or trip.user_id != user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return

        # Получение списка пользователей
        users = invitation_service.get_users_with_access(trip_id)

        await update.callback_query.message.edit_text(
            f"👥 <b>Управление пользователями</b>\n\n"
            f"Поездка: <b>{trip.title}</b>\n\n"
            f"Всего пользователей: {len(users)}\n\n"
            f"👑 — владелец поездки\n"
            f"Выберите пользователя:",
            reply_markup=users_list_keyboard(users, trip_id, page=page),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def users_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение страницы списка пользователей."""
    await update.callback_query.answer()
    await show_users_list(update, context)


async def select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выбор пользователя для действий."""
    await update.callback_query.answer()

    user_id = int(context.match.group(1))
    trip_id = int(context.match.group(2))
    current_user_id = update.effective_user.id

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        # Проверка, что текущий пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)

        if trip is None or trip.user_id != current_user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return

        # Получение информации о выбранном пользователе
        from database import User
        selected_user = session.get(User, user_id)
        username = selected_user.username if selected_user else None
        first_name = selected_user.first_name if selected_user else None

        # Проверка, является ли выбранный пользователь владельцем
        is_owner = (user_id == trip.user_id)

        if is_owner:
            await update.callback_query.message.edit_text(
                "❌ Нельзя выполнить действия с владельцем поездки.",
                reply_markup=users_list_keyboard(
                    invitation_service.get_users_with_access(trip_id),
                    trip_id,
                    page=0
                )
            )
            return

        # Получение роли администратора
        invitation = invitation_service.invitation_repo.get_by_user_and_trip_with_role(user_id, trip_id)
        is_admin = invitation.is_admin if invitation else False

        # Приоритет: username > first_name > User_ID
        if username:
            display_name = f"@{username}"
        elif first_name:
            display_name = first_name
        else:
            display_name = f"User_{user_id}"

        await update.callback_query.message.edit_text(
            f"👤 <b>Пользователь</b>\n\n"
            f"Имя: <code>{display_name}</code>\n"
            f"ID: <code>{user_id}</code>\n\n"
            f"Выберите действие:",
            reply_markup=user_action_keyboard(
                user_id, trip_id, username, first_name,
                is_owner=is_owner,
                is_admin=is_admin,
                current_user_is_owner=True
            ),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def start_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало удаления пользователя из поездки."""
    await update.callback_query.answer()

    user_id = int(context.match.group(1))
    trip_id = int(context.match.group(2))
    current_user_id = update.effective_user.id

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        # Проверка, что текущий пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)

        if trip is None or trip.user_id != current_user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return

        # Проверка, что не пытаемся удалить владельца
        if user_id == trip.user_id:
            await update.callback_query.message.edit_text(
                "❌ Нельзя удалить владельца поездки.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
            return

        # Получение информации о пользователе
        from database import User
        selected_user = session.get(User, user_id)
        username = selected_user.username if selected_user else None
        first_name = selected_user.first_name if selected_user else None
        
        # Приоритет: username > first_name > User_ID
        if username:
            display_name = f"@{username}"
        elif first_name:
            display_name = first_name
        else:
            display_name = f"User_{user_id}"

        context.user_data["delete_user_id"] = user_id
        context.user_data["delete_trip_id"] = trip_id

        await update.callback_query.message.edit_text(
            f"⚠️ <b>Удаление пользователя</b>\n\n"
            f"Вы действительно хотите удалить <code>{display_name}</code> из поездки?\n\n"
            f"📝 Заметки этого пользователя останутся в поездке.",
            reply_markup=user_delete_confirm_keyboard(user_id, trip_id),
            parse_mode="HTML"
        )
    finally:
        close(session)

    return WAITING_FOR_DELETE_CONFIRM


async def confirm_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение и выполнение удаления пользователя."""
    await update.callback_query.answer()

    user_id = context.user_data.get("delete_user_id")
    trip_id = context.user_data.get("delete_trip_id")

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        trip_service = TripService(session)

        # Проверка прав
        trip = trip_service.get_by_id(trip_id)
        if trip is None or trip.user_id != update.effective_user.id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        # Удаление пользователя
        result = invitation_service.revoke_access(trip_id, user_id)

        if result:
            # Получение обновлённого списка пользователей
            users = invitation_service.get_users_with_access(trip_id)

            await update.callback_query.message.edit_text(
                f"✅ Пользователь успешно удалён из поездки.\n\n"
                f"Его заметки остались в поездке.",
                reply_markup=users_list_keyboard(users, trip_id, page=0),
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Не удалось удалить пользователя.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
    finally:
        close(session)

    # Очистка данных
    context.user_data.pop("delete_user_id", None)
    context.user_data.pop("delete_trip_id", None)

    return ConversationHandler.END


async def cancel_delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена удаления и возврат к списку пользователей."""
    await update.callback_query.answer()

    user_id = int(context.match.group(1))
    trip_id = int(context.match.group(2))
    current_user_id = update.effective_user.id

    # Очистка данных
    context.user_data.pop("delete_user_id", None)
    context.user_data.pop("delete_trip_id", None)

    session = get_session()
    try:
        trip_service = TripService(session)
        invitation_service = InvitationService(session)

        trip = trip_service.get_by_id(trip_id)

        if trip is None or trip.user_id != current_user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        # Получение информации о пользователе
        from database import User
        selected_user = session.get(User, user_id)
        username = selected_user.username if selected_user else None
        first_name = selected_user.first_name if selected_user else None

        await update.callback_query.message.edit_text(
            f"👤 <b>Пользователь</b>\n\n"
            f"Имя: <code>{username if username else (first_name if first_name else f'User_{user_id}')}</code>\n"
            f"ID: <code>{user_id}</code>\n\n"
            f"Выберите действие:",
            reply_markup=user_action_keyboard(user_id, trip_id, username, first_name),
            parse_mode="HTML"
        )
    finally:
        close(session)

    return ConversationHandler.END


async def back_to_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к меню управления поездкой."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    # Очистка данных
    context.user_data.pop("delete_user_id", None)
    context.user_data.pop("delete_trip_id", None)

    session = get_session()
    try:
        trip_service = TripService(session)
        trip = trip_service.get_by_id(trip_id)

        if trip:
            await update.callback_query.message.edit_text(
                f"⚙️ <b>Управление поездкой</b>\n\n"
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


async def make_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Назначение пользователя администратором."""
    await update.callback_query.answer()

    user_id = int(context.match.group(1))
    trip_id = int(context.match.group(2))
    current_user_id = update.effective_user.id

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        trip_service = TripService(session)

        # Проверка, что текущий пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)
        if trip is None or trip.user_id != current_user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        # Назначение администратором
        result = invitation_service.make_admin(trip_id, user_id, current_user_id)

        if result:
            # Получение обновлённого списка пользователей
            users = invitation_service.get_users_with_access(trip_id)

            await update.callback_query.message.edit_text(
                f"✅ Пользователь назначен администратором.\n\n"
                f"Теперь он может:\n"
                f"• Удалять любые заметки\n"
                f"• Удалять пользователей (кроме владельца и админов)\n"
                f"• Приглашать новых участников",
                reply_markup=users_list_keyboard(users, trip_id, page=0),
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Не удалось назначить администратора.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
    finally:
        close(session)

    return ConversationHandler.END


async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Снятие роли администратора."""
    await update.callback_query.answer()

    user_id = int(context.match.group(1))
    trip_id = int(context.match.group(2))
    current_user_id = update.effective_user.id

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        trip_service = TripService(session)

        # Проверка, что текущий пользователь является владельцем
        trip = trip_service.get_by_id(trip_id)
        if trip is None or trip.user_id != current_user_id:
            await update.callback_query.message.edit_text(
                "❌ У вас нет доступа к управлению этой поездкой.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        # Найти приглашение
        invitation = invitation_service.invitation_repo.get_by_user_and_trip_with_role(user_id, trip_id)
        if invitation:
            invitation_service.invitation_repo.set_admin_role(invitation, False)

            # Получение обновлённого списка пользователей
            users = invitation_service.get_users_with_access(trip_id)

            await update.callback_query.message.edit_text(
                f"✅ Пользователь лишён роли администратора.",
                reply_markup=users_list_keyboard(users, trip_id, page=0),
            )
        else:
            await update.callback_query.message.edit_text(
                "❌ Не удалось снять администратора.",
                reply_markup=trip_settings_keyboard(trip_id)
            )
    finally:
        close(session)

    return ConversationHandler.END


# Обработчик диалога управления пользователями
user_management_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(start_user_management, pattern=r"^trip_users_(\d+)$"),
        CallbackQueryHandler(select_user, pattern=r"^user_action_(\d+)_(\d+)$"),
        CallbackQueryHandler(start_delete_user, pattern=r"^user_delete_(\d+)_(\d+)$"),
        CallbackQueryHandler(make_admin, pattern=r"^user_make_admin_(\d+)_(\d+)$"),
        CallbackQueryHandler(remove_admin, pattern=r"^user_remove_admin_(\d+)_(\d+)$"),
    ],
    states={
        WAITING_FOR_DELETE_CONFIRM: [
            CallbackQueryHandler(confirm_delete_user, pattern=r"^user_delete_confirm_(\d+)_(\d+)$"),
            CallbackQueryHandler(cancel_delete_user, pattern=r"^user_action_(\d+)_(\d+)$"),
        ],
    },
    fallbacks=[
        CallbackQueryHandler(back_to_settings, pattern=r"^trip_settings_(\d+)$"),
        CallbackQueryHandler(start_user_management, pattern=r"^trip_users_(\d+)$"),
    ],
    per_message=False,
)

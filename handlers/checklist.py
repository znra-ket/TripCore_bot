from telegram import Update
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from keyboards import (
    checklists_list_keyboard,
    checklist_view_keyboard,
    checklist_empty_keyboard,
    checklist_create_keyboard,
    checklist_add_item_keyboard,
    notes_menu_keyboard,
    main_keyboard,
)
from service import ChecklistService, InvitationService
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
        if "There is no text in the message to edit" in str(e) or "Message to edit not found" in str(e):
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            raise


# Состояния для создания чек-листа
WAIT_CHECKLIST_TITLE = 1

# Состояния для добавления задачи
WAIT_ADD_ITEM_TEXT = 2


async def show_checklists_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка чек-листов пользователя с пагинацией."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        # Получаем только чек-листы пользователя
        checklists = checklist_service.get_checklists_by_user_id(user_id)

        # Фильтруем по trip_id (показываем только чек-листы этой поездки)
        trip_checklists = [c for c in checklists if c.trip_id == trip_id]

        if not trip_checklists:
            await safe_edit_message(
                update,
                "📭 У вас пока нет чек-листов в этой поездке.\n\n"
                "Создайте первый чек-лист, нажав кнопку ниже.",
                reply_markup=checklist_empty_keyboard(trip_id)
            )
            return

        await safe_edit_message(
            update,
            "📋 <b>Мои чек-листы</b>\n\nВыберите чек-лист:",
            reply_markup=checklists_list_keyboard(trip_checklists, trip_id, page=0),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def checklists_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение страницы списка чек-листов."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    page = int(context.match.group(2))
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        # Получаем только чек-листы пользователя
        checklists = checklist_service.get_checklists_by_user_id(user_id)

        # Фильтруем по trip_id
        trip_checklists = [c for c in checklists if c.trip_id == trip_id]

        if not trip_checklists:
            await safe_edit_message(
                update,
                "📭 У вас пока нет чек-листов.",
                reply_markup=checklist_empty_keyboard(trip_id)
            )
            return

        await safe_edit_message(
            update,
            "📋 <b>Мои чек-листы</b>\n\nВыберите чек-лист:",
            reply_markup=checklists_list_keyboard(trip_checklists, trip_id, page=page),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def checklists_page_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игнорирование нажатий на неактивные кнопки пагинации."""
    await update.callback_query.answer()


async def view_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр чек-листа."""
    await update.callback_query.answer()

    checklist_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        checklist = checklist_service.get_checklist_by_id(checklist_id)

        if checklist is None:
            await safe_edit_message(
                update,
                "❌ Чек-лист не найден.",
                reply_markup=main_keyboard()
            )
            return

        # Проверка, что пользователь является владельцем
        if checklist.user_id != user_id:
            await safe_edit_message(
                update,
                "❌ У вас нет доступа к этому чек-листу.",
                reply_markup=main_keyboard()
            )
            return

        trip_id = checklist.trip_id

        # Получаем задачи
        items = checklist_service.get_items_by_checklist_id(checklist_id)
        incomplete_items = checklist_service.get_incomplete_items(checklist_id)

        if not items:
            # Чек-лист пуст
            await safe_edit_message(
                update,
                f"📋 <b>{checklist.title}</b>\n\n"
                "В этом чек-листе пока нет задач.\n\n"
                "Добавьте первую задачу, нажав кнопку ниже.",
                reply_markup=checklist_view_keyboard(checklist_id, trip_id, incomplete_items, show_delete=True),
                parse_mode="HTML"
            )
            return

        # Формируем текст со списком задач
        text = f"📋 <b>{checklist.title}</b>\n\n"

        for i, item in enumerate(items, 1):
            status = "☑️" if item.is_completed else "⬜"
            text += f"{status} <b>{i}.</b> {item.text}\n"

        await safe_edit_message(
            update,
            text,
            reply_markup=checklist_view_keyboard(checklist_id, trip_id, incomplete_items, show_delete=True),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def start_create_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания чек-листа."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["checklist_trip_id"] = trip_id

    await update.callback_query.message.edit_text(
        "📋 Введите название чек-листа:",
        reply_markup=checklist_create_keyboard(trip_id)
    )
    return WAIT_CHECKLIST_TITLE


async def receive_checklist_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение названия и создание чек-листа."""
    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "❌ Название не может быть пустым. Введите название:",
            reply_markup=checklist_create_keyboard(context.user_data.get("checklist_trip_id"))
        )
        return WAIT_CHECKLIST_TITLE

    trip_id = context.user_data.get("checklist_trip_id")
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        checklist = checklist_service.create_checklist(
            user_id=user_id,
            trip_id=trip_id,
            title=title
        )

        await update.message.reply_text(
            f"✅ Чек-лист «{checklist.title}» создан!\n\n"
            f"Теперь добавьте задачи, нажав кнопку ниже.",
            reply_markup=checklist_view_keyboard(checklist.id, trip_id, [], show_delete=True)
        )
    finally:
        close(session)

    # Очистка данных
    context.user_data.pop("checklist_trip_id", None)

    return ConversationHandler.END


async def cancel_create_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена создания чек-листа."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    # Очистка данных
    context.user_data.pop("checklist_trip_id", None)

    session = get_session()
    try:
        checklist_service = ChecklistService(session)
        user_id = update.effective_user.id

        checklists = checklist_service.get_checklists_by_user_id(user_id)
        trip_checklists = [c for c in checklists if c.trip_id == trip_id]

        if not trip_checklists:
            await update.callback_query.message.edit_text(
                "📭 У вас пока нет чек-листов.",
                reply_markup=checklist_empty_keyboard(trip_id)
            )
        else:
            await update.callback_query.message.edit_text(
                "📋 <b>Мои чек-листы</b>\n\nВыберите чек-лист:",
                reply_markup=checklists_list_keyboard(trip_checklists, trip_id, page=0),
                parse_mode="HTML"
            )
    finally:
        close(session)

    return ConversationHandler.END


async def start_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало добавления задачи."""
    await update.callback_query.answer()

    checklist_id = int(context.match.group(1))
    context.user_data["add_item_checklist_id"] = checklist_id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)
        checklist = checklist_service.get_checklist_by_id(checklist_id)

        if checklist is None:
            await safe_edit_message(
                update,
                "❌ Чек-лист не найден.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        await update.callback_query.message.edit_text(
            "➕ Введите текст задачи:",
            reply_markup=checklist_add_item_keyboard(checklist_id, checklist.trip_id)
        )
        return WAIT_ADD_ITEM_TEXT
    finally:
        close(session)


async def receive_item_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение текста задачи и добавление."""
    text = update.message.text.strip()

    if not text:
        await update.message.reply_text(
            "❌ Задача не может быть пустой. Введите текст:",
            reply_markup=checklist_add_item_keyboard(
                context.user_data.get("add_item_checklist_id"),
                0  # trip_id не нужен для клавиатуры отмены
            )
        )
        return WAIT_ADD_ITEM_TEXT

    checklist_id = context.user_data.get("add_item_checklist_id")
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        checklist = checklist_service.get_checklist_by_id(checklist_id)

        if checklist is None or checklist.user_id != user_id:
            await update.message.reply_text(
                "❌ У вас нет доступа к этому чек-листу.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        # Добавляем задачу
        checklist_service.add_item(checklist_id, text)

        # Получаем обновлённый список задач
        items = checklist_service.get_items_by_checklist_id(checklist_id)
        incomplete_items = checklist_service.get_incomplete_items(checklist_id)

        # Формируем текст со списком задач
        task_text = f"📋 <b>{checklist.title}</b>\n\n"
        for i, item in enumerate(items, 1):
            status = "☑️" if item.is_completed else "⬜"
            task_text += f"{status} <b>{i}.</b> {item.text}\n"

        await update.message.reply_text(
            task_text,
            reply_markup=checklist_view_keyboard(checklist_id, checklist.trip_id, incomplete_items, show_delete=True),
            parse_mode="HTML"
        )
    finally:
        close(session)

    # Очистка данных
    context.user_data.pop("add_item_checklist_id", None)

    return ConversationHandler.END


async def cancel_add_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена добавления задачи."""
    await update.callback_query.answer()

    checklist_id = int(context.match.group(1))
    user_id = update.effective_user.id

    # Очистка данных
    context.user_data.pop("add_item_checklist_id", None)

    session = get_session()
    try:
        checklist_service = ChecklistService(session)
        checklist = checklist_service.get_checklist_by_id(checklist_id)

        if checklist is None:
            await update.callback_query.message.edit_text(
                "❌ Чек-лист не найден.",
                reply_markup=main_keyboard()
            )
            return ConversationHandler.END

        items = checklist_service.get_items_by_checklist_id(checklist_id)
        incomplete_items = checklist_service.get_incomplete_items(checklist_id)

        # Формируем текст со списком задач
        text = f"📋 <b>{checklist.title}</b>\n\n"
        for i, item in enumerate(items, 1):
            status = "☑️" if item.is_completed else "⬜"
            text += f"{status} <b>{i}.</b> {item.text}\n"

        await update.callback_query.message.edit_text(
            text,
            reply_markup=checklist_view_keyboard(checklist_id, checklist.trip_id, incomplete_items, show_delete=True),
            parse_mode="HTML"
        )
    finally:
        close(session)

    return ConversationHandler.END


async def complete_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выполнение задачи."""
    await update.callback_query.answer()

    item_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        # Получаем задачу для определения checklist_id
        item = checklist_service.item_repo.get_by_id(item_id)
        if item is None:
            await safe_edit_message(
                update,
                "❌ Задача не найдена.",
                reply_markup=main_keyboard()
            )
            return

        checklist = checklist_service.get_checklist_by_id(item.checklist_id)
        if checklist is None or checklist.user_id != user_id:
            await safe_edit_message(
                update,
                "❌ У вас нет доступа к этому чек-листу.",
                reply_markup=main_keyboard()
            )
            return

        # Выполняем задачу (если все задачи выполнены - чек-лист удалится)
        updated_item = checklist_service.complete_item(item_id)

        trip_id = checklist.trip_id

        if updated_item is None:
            # Чек-лист удалён (все задачи выполнены)
            await safe_edit_message(
                update,
                "🎉 Все задачи выполнены! Чек-лист автоматически удалён.",
                reply_markup=notes_menu_keyboard(trip_id, is_owner=True, is_admin=False)
            )
            return

        # Получаем обновлённый список задач
        items = checklist_service.get_items_by_checklist_id(item.checklist_id)
        incomplete_items = checklist_service.get_incomplete_items(item.checklist_id)

        # Формируем текст со списком задач
        text = f"📋 <b>{checklist.title}</b>\n\n"
        for i, item in enumerate(items, 1):
            status = "☑️" if item.is_completed else "⬜"
            text += f"{status} <b>{i}.</b> {item.text}\n"

        await safe_edit_message(
            update,
            text,
            reply_markup=checklist_view_keyboard(item.checklist_id, trip_id, incomplete_items, show_delete=True),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def delete_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление чек-листа."""
    await update.callback_query.answer()

    checklist_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        checklist_service = ChecklistService(session)

        checklist = checklist_service.get_checklist_by_id(checklist_id)

        if checklist is None:
            await safe_edit_message(
                update,
                "❌ Чек-лист не найден.",
                reply_markup=main_keyboard()
            )
            return

        if checklist.user_id != user_id:
            await safe_edit_message(
                update,
                "❌ У вас нет доступа к этому чек-листу.",
                reply_markup=main_keyboard()
            )
            return

        trip_id = checklist.trip_id
        checklist_service.delete_checklist(checklist_id)

        # Получаем обновлённый список чек-листов
        checklists = checklist_service.get_checklists_by_user_id(user_id)
        trip_checklists = [c for c in checklists if c.trip_id == trip_id]

        if not trip_checklists:
            await safe_edit_message(
                update,
                "✅ Чек-лист удалён.\n\nУ вас больше нет чек-листов в этой поездке.",
                reply_markup=checklist_empty_keyboard(trip_id)
            )
        else:
            await safe_edit_message(
                update,
                "✅ Чек-лист удалён.\n\nВыберите чек-лист:",
                reply_markup=checklists_list_keyboard(trip_checklists, trip_id, page=0),
                parse_mode="HTML"
            )
    finally:
        close(session)


async def checklists_back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат к меню заметок из списка чек-листов."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        user_id = update.effective_user.id

        # Проверяем права пользователя
        is_owner = invitation_service.is_owner(user_id, trip_id)
        is_admin = invitation_service.is_admin(user_id, trip_id)

        await safe_edit_message(
            update,
            "📋 Меню заметок",
            reply_markup=notes_menu_keyboard(trip_id, is_owner=is_owner, is_admin=is_admin)
        )
    finally:
        close(session)


# Обработчик создания чек-листа
checklist_create_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_create_checklist, pattern=r"^checklist_create_(\d+)$")],
    states={
        WAIT_CHECKLIST_TITLE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_checklist_title),
            CallbackQueryHandler(cancel_create_checklist, pattern=r"^checklist_list_(\d+)$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel_create_checklist, pattern=r"^checklist_list_(\d+)$")],
    per_message=False,
)

# Обработчик добавления задачи
checklist_add_item_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_item, pattern=r"^checklist_add_item_(\d+)$")],
    states={
        WAIT_ADD_ITEM_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_item_text),
            CallbackQueryHandler(cancel_add_item, pattern=r"^checklist_view_(\d+)$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(cancel_add_item, pattern=r"^checklist_view_(\d+)$")],
    per_message=False,
)

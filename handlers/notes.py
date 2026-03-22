from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo
from telegram.error import BadRequest
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from keyboards import (
    notes_menu_keyboard,
    note_media_keyboard,
    note_ai_approve_keyboard,
    notes_list_keyboard,
    note_view_keyboard,
    note_back_to_menu_keyboard,
    main_keyboard,
)
from service import NoteService, AgentService
from database import get_session
from handlers.trip import show_my_trips, show_trips_list


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
            # Сообщение с медиа или не найдено - отправляем новое
            await update.callback_query.message.reply_text(
                text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        else:
            raise


# Состояния для создания обычной заметки
WAIT_NOTE_TEXT = 1
WAIT_NOTE_MEDIA = 2

# Состояния для создания ИИ заметки
WAIT_AI_NOTE_PROMPT = 3
WAIT_AI_NOTE_APPROVE = 4
WAIT_AI_NOTE_MEDIA = 5


async def show_notes_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ меню заметок для поездки."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    await safe_edit_message(
        update,
        "📝 <b>Меню заметок</b>\n\nВыберите действие:",
        reply_markup=notes_menu_keyboard(trip_id),
        parse_mode="HTML"
    )


async def start_create_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания обычной заметки - запрос текста."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["note_trip_id"] = trip_id
    context.user_data["note_is_ai"] = False

    await update.callback_query.message.edit_text(
        "📝 Введите текст заметки:",
        reply_markup=note_back_to_menu_keyboard(trip_id)
    )
    return WAIT_NOTE_TEXT


async def receive_note_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение текста заметки и предложение прикрепить медиа."""
    text = update.message.text

    trip_id = context.user_data.get("note_trip_id")
    context.user_data["note_text"] = text

    await update.message.reply_text(
        "📎 Выберите тип медиа или завершите создание:",
        reply_markup=note_media_keyboard(trip_id, "create")
    )
    return WAIT_NOTE_MEDIA


async def attach_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос фото от пользователя."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["note_media_type"] = "photo"

    await update.callback_query.message.edit_text(
        "📷 Отправьте фото для заметки:"
    )
    return WAIT_NOTE_MEDIA


async def attach_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Запрос видео от пользователя."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["note_media_type"] = "video"

    await update.callback_query.message.edit_text(
        "🎥 Отправьте видео для заметки:"
    )
    return WAIT_NOTE_MEDIA


async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение медиа и создание заметки."""
    trip_id = context.user_data.get("note_trip_id")
    text = context.user_data.get("note_text")
    media_type = context.user_data.get("note_media_type")

    session = get_session()
    note_service = NoteService(session)

    media_file_id = None
    if media_type == "photo":
        photo = update.message.photo[-1]
        media_file_id = photo.file_id
    elif media_type == "video":
        media_file_id = update.message.video.file_id

    note = note_service.create(
        trip_id=trip_id,
        text=text,
        media_type=media_type,
        media_file_id=media_file_id,
    )

    # Очистка данных
    context.user_data.pop("note_trip_id", None)
    context.user_data.pop("note_text", None)
    context.user_data.pop("note_media_type", None)

    await update.message.reply_text(
        f"✅ Заметка создана!",
        reply_markup=note_back_to_menu_keyboard(trip_id)
    )
    return ConversationHandler.END


async def finish_note_without_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания заметки без медиа."""
    trip_id = context.user_data.get("note_trip_id")
    text = context.user_data.get("note_text")

    session = get_session()
    note_service = NoteService(session)

    note = note_service.create(
        trip_id=trip_id,
        text=text,
    )

    # Очистка данных
    context.user_data.pop("note_trip_id", None)
    context.user_data.pop("note_text", None)
    context.user_data.pop("note_media_type", None)

    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✅ Заметка создана!",
        reply_markup=note_back_to_menu_keyboard(trip_id)
    )
    return ConversationHandler.END


# === ИИ ЗАМЕТКИ ===

async def start_create_ai_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало создания ИИ заметки - запрос промпта."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    context.user_data["note_trip_id"] = trip_id
    context.user_data["note_is_ai"] = True

    await update.callback_query.message.edit_text(
        "🤖 Введите короткий текст для генерации ИИ заметки:",
        reply_markup=note_back_to_menu_keyboard(trip_id)
    )
    return WAIT_AI_NOTE_PROMPT


async def receive_ai_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение промпта и генерация текста ИИ."""
    prompt = update.message.text
    context.user_data["note_ai_prompt"] = prompt

    trip_id = context.user_data.get("note_trip_id")

    session = get_session()
    agent_service = AgentService(session)

    # Генерация текста через ИИ
    ai_text = agent_service.generate_note_text(prompt)

    context.user_data["note_ai_text"] = ai_text

    await update.message.reply_text(
        f"🤖 <b>ИИ предложил:</b>\n\n{ai_text}",
        reply_markup=note_ai_approve_keyboard(trip_id),
        parse_mode="HTML"
    )
    return WAIT_AI_NOTE_APPROVE


async def approve_ai_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Одобрение ИИ текста и переход к выбору медиа."""
    await update.callback_query.answer()

    trip_id = context.user_data.get("note_trip_id")

    await update.callback_query.message.edit_text(
        "📎 Выберите тип медиа или завершите создание:",
        reply_markup=note_media_keyboard(trip_id, "ai_create")
    )
    return WAIT_AI_NOTE_MEDIA


async def regenerate_ai_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перегенерация ИИ текста с тем же промптом."""
    await update.callback_query.answer()

    trip_id = context.user_data.get("note_trip_id")
    prompt = context.user_data.get("note_ai_prompt")

    session = get_session()
    agent_service = AgentService(session)

    # Перегенерация текста через ИИ
    ai_text = agent_service.generate_note_text(prompt)

    context.user_data["note_ai_text"] = ai_text

    await update.callback_query.message.edit_text(
        f"🤖 <b>ИИ предложил (новая версия):</b>\n\n{ai_text}",
        reply_markup=note_ai_approve_keyboard(trip_id),
        parse_mode="HTML"
    )
    return WAIT_AI_NOTE_APPROVE


async def exit_ai_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выход из создания ИИ заметки."""
    await update.callback_query.answer()

    trip_id = context.user_data.get("note_trip_id")

    # Очистка данных
    context.user_data.pop("note_trip_id", None)
    context.user_data.pop("note_ai_prompt", None)
    context.user_data.pop("note_ai_text", None)

    await update.callback_query.message.edit_text(
        "❌ Создание ИИ заметки отменено.",
        reply_markup=notes_menu_keyboard(trip_id)
    )
    return ConversationHandler.END


async def finish_ai_note_without_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение создания ИИ заметки без медиа."""
    trip_id = context.user_data.get("note_trip_id")
    text = context.user_data.get("note_ai_text")

    session = get_session()
    note_service = NoteService(session)

    note = note_service.create(
        trip_id=trip_id,
        text=text,
        is_ai_generated=True,
    )

    # Очистка данных
    context.user_data.pop("note_trip_id", None)
    context.user_data.pop("note_ai_prompt", None)
    context.user_data.pop("note_ai_text", None)

    await update.callback_query.answer()
    await update.callback_query.message.edit_text(
        f"✅ ИИ заметка создана!",
        reply_markup=notes_menu_keyboard(trip_id)
    )
    return ConversationHandler.END


async def receive_ai_note_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получение медиа для ИИ заметки и создание."""
    trip_id = context.user_data.get("note_trip_id")
    text = context.user_data.get("note_ai_text")
    media_type = context.user_data.get("note_media_type")

    session = get_session()
    note_service = NoteService(session)

    media_file_id = None
    if media_type == "photo":
        photo = update.message.photo[-1]
        media_file_id = photo.file_id
    elif media_type == "video":
        media_file_id = update.message.video.file_id

    note = note_service.create(
        trip_id=trip_id,
        text=text,
        media_type=media_type,
        media_file_id=media_file_id,
        is_ai_generated=True,
    )

    # Очистка данных
    context.user_data.pop("note_trip_id", None)
    context.user_data.pop("note_ai_prompt", None)
    context.user_data.pop("note_ai_text", None)
    context.user_data.pop("note_media_type", None)

    await update.message.reply_text(
        f"✅ ИИ заметка создана!",
        reply_markup=notes_menu_keyboard(trip_id)
    )
    return ConversationHandler.END


# === ПРОСМОТР ЗАМЕТОК ===

async def show_notes_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка заметок поездки с пагинацией."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    session = get_session()
    note_service = NoteService(session)

    notes = note_service.get_by_trip_id(trip_id)

    if not notes:
        await safe_edit_message(
            update,
            "📭 У этой поездки пока нет заметок.",
            reply_markup=notes_menu_keyboard(trip_id)
        )
        return

    await safe_edit_message(
        update,
        "📋 <b>Заметки поездки</b>\n\nВыберите заметку:",
        reply_markup=notes_list_keyboard(notes, trip_id, page=0),
        parse_mode="HTML"
    )


async def notes_list_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение страницы списка заметок."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    page = int(context.match.group(2))

    session = get_session()
    note_service = NoteService(session)

    notes = note_service.get_by_trip_id(trip_id)

    await safe_edit_message(
        update,
        "📋 <b>Заметки поездки</b>\n\nВыберите заметку:",
        reply_markup=notes_list_keyboard(notes, trip_id, page=page),
        parse_mode="HTML"
    )


async def view_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр заметки."""
    await update.callback_query.answer()

    note_id = int(context.match.group(1))

    session = get_session()
    note_service = NoteService(session)

    note = note_service.get_by_id(note_id)

    if note is None:
        await safe_edit_message(
            update,
            "❌ Заметка не найдена.",
            reply_markup=main_keyboard()
        )
        return

    # Получаем trip_id для кнопки назад
    trip_id = note.trip_id

    # Формируем текст заметки
    ai_marker = "🤖 " if note.is_ai_generated else ""
    text = f"{ai_marker}📝 <b>Заметка</b>\n\n{note.text}"

    # Если есть медиа, отправляем его с caption
    if note.media_type == "photo" and note.media_file_id:
        await update.callback_query.message.edit_media(
            media=InputMediaPhoto(media=note.media_file_id, caption=text, parse_mode="HTML"),
            reply_markup=note_view_keyboard(note_id, trip_id)
        )
    elif note.media_type == "video" and note.media_file_id:
        await update.callback_query.message.edit_media(
            media=InputMediaVideo(media=note.media_file_id, caption=text, parse_mode="HTML"),
            reply_markup=note_view_keyboard(note_id, trip_id)
        )
    else:
        # Заметка без медиа
        await safe_edit_message(
            update,
            text,
            reply_markup=note_view_keyboard(note_id, trip_id),
            parse_mode="HTML"
        )


async def delete_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление заметки."""
    await update.callback_query.answer()

    note_id = int(context.match.group(1))

    session = get_session()
    note_service = NoteService(session)

    note = note_service.get_by_id(note_id)
    trip_id = note.trip_id if note else None

    if note:
        note_service.delete(note_id)

    if trip_id:
        await safe_edit_message(
            update,
            "✅ Заметка удалена.",
            reply_markup=notes_menu_keyboard(trip_id)
        )
    else:
        await safe_edit_message(
            update,
            "✅ Заметка удалена.",
            reply_markup=main_keyboard()
        )


async def notes_list_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игнорирование нажатий на неактивные кнопки пагинации."""
    await update.callback_query.answer()


# Обработчики для обычной заметки
note_create_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_create_note, pattern=r"^note_create_(\d+)$")],
    states={
        WAIT_NOTE_TEXT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_note_text),
            CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"),
        ],
        WAIT_NOTE_MEDIA: [
            MessageHandler(filters.PHOTO, receive_media),
            MessageHandler(filters.VIDEO, receive_media),
            CallbackQueryHandler(attach_photo, pattern=r"^note_attach_photo_(\d+)$"),
            CallbackQueryHandler(attach_video, pattern=r"^note_attach_video_(\d+)$"),
            CallbackQueryHandler(finish_note_without_media, pattern=r"^note_finish_(\d+)$"),
            CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$")],
    per_message=False,
)

# Обработчики для ИИ заметки
note_ai_create_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_create_ai_note, pattern=r"^note_ai_create_(\d+)$")],
    states={
        WAIT_AI_NOTE_PROMPT: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ai_prompt),
            CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"),
        ],
        WAIT_AI_NOTE_APPROVE: [
            CallbackQueryHandler(approve_ai_text, pattern=r"^note_ai_approve_(\d+)$"),
            CallbackQueryHandler(regenerate_ai_text, pattern=r"^note_ai_regenerate_(\d+)$"),
            CallbackQueryHandler(exit_ai_note, pattern=r"^note_ai_exit_(\d+)$"),
            CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"),
        ],
        WAIT_AI_NOTE_MEDIA: [
            MessageHandler(filters.PHOTO, receive_ai_note_media),
            MessageHandler(filters.VIDEO, receive_ai_note_media),
            CallbackQueryHandler(attach_photo, pattern=r"^note_attach_photo_(\d+)$"),
            CallbackQueryHandler(attach_video, pattern=r"^note_attach_video_(\d+)$"),
            CallbackQueryHandler(finish_ai_note_without_media, pattern=r"^note_finish_(\d+)$"),
            CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"),
        ],
    },
    fallbacks=[CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$")],
    per_message=False,
)

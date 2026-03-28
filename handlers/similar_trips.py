from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from keyboards import (
    similar_trips_list_keyboard,
    similar_trip_slider_keyboard,
    similar_note_view_keyboard,
    notes_list_keyboard,
    notes_menu_keyboard,
)
from service import SimilarTripService, NoteService
from database import get_session, close


async def show_similar_trips_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка похожих поездок с пагинацией."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))

    session = get_session()
    try:
        similar_trip_service = SimilarTripService(session)

        similar_trips = similar_trip_service.find_similar_trips(trip_id, limit=10)

        if not similar_trips:
            await update.callback_query.message.edit_text(
                "🔍 Похожих поездок не найдено.\n\n"
                "Возможно, у других пользователей пока нет поездок с похожим описанием.",
                reply_markup=notes_menu_keyboard(trip_id, is_owner=True, is_admin=False)
            )
            return

        await update.callback_query.message.edit_text(
            f"🔍 <b>Похожие поездки</b>\n\n"
            f"Найдено {len(similar_trips)} похожих поездок:",
            reply_markup=similar_trips_list_keyboard(similar_trips, trip_id, page=0),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def similar_trips_page_change(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Переключение страницы списка похожих поездок."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    page = int(context.match.group(2))

    session = get_session()
    try:
        similar_trip_service = SimilarTripService(session)

        similar_trips = similar_trip_service.find_similar_trips(trip_id, limit=10)

        if not similar_trips:
            await update.callback_query.message.edit_text(
                "🔍 Похожих поездок не найдено.",
                reply_markup=notes_menu_keyboard(trip_id, is_owner=True, is_admin=False)
            )
            return

        await update.callback_query.message.edit_text(
            f"🔍 <b>Похожие поездки</b>\n\n"
            f"Найдено {len(similar_trips)} похожих поездок:",
            reply_markup=similar_trips_list_keyboard(similar_trips, trip_id, page=page),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def similar_trip_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр похожей поездки в режиме слайдера."""
    await update.callback_query.answer()

    other_trip_id = int(context.match.group(1))
    user_trip_id = int(context.match.group(2))

    session = get_session()
    try:
        similar_trip_service = SimilarTripService(session)

        similar_trips = similar_trip_service.find_similar_trips(user_trip_id, limit=5)

        if not similar_trips:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=notes_menu_keyboard(user_trip_id, is_owner=True, is_admin=False)
            )
            return

        # Находим индекс текущей поездки
        current_idx = next(
            (i for i, (trip, _) in enumerate(similar_trips) if trip.id == other_trip_id),
            0
        )

        trip, similarity = similar_trips[current_idx]

        await update.callback_query.message.edit_text(
            f"📍 <b>{trip.title}</b>\n\n"
            f"📊 Сходство: {similarity:.1f}%\n\n"
            f"📝 <b>Описание:</b>\n{trip.description or 'Описание отсутствует'}",
            reply_markup=similar_trip_slider_keyboard(similar_trips, user_trip_id, current_idx),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def similar_slider_navigate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Навигация по слайдеру похожих поездок."""
    await update.callback_query.answer()

    user_trip_id = int(context.match.group(1))
    current_idx = int(context.match.group(2))

    session = get_session()
    try:
        similar_trip_service = SimilarTripService(session)

        similar_trips = similar_trip_service.find_similar_trips(user_trip_id, limit=5)

        if not similar_trips or current_idx >= len(similar_trips):
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=notes_menu_keyboard(user_trip_id, is_owner=True, is_admin=False)
            )
            return

        trip, similarity = similar_trips[current_idx]

        await update.callback_query.message.edit_text(
            f"📍 <b>{trip.title}</b>\n\n"
            f"📊 Сходство: {similarity:.1f}%\n\n"
            f"📝 <b>Описание:</b>\n{trip.description or 'Описание отсутствует'}",
            reply_markup=similar_trip_slider_keyboard(similar_trips, user_trip_id, current_idx),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def similar_trip_notes_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показ списка заметок чужой поездки."""
    await update.callback_query.answer()

    other_trip_id = int(context.match.group(1))
    user_trip_id = int(context.match.group(2))

    session = get_session()
    try:
        note_service = NoteService(session)

        notes = note_service.get_by_trip_id(other_trip_id)

        if not notes:
            await update.callback_query.message.edit_text(
                "📭 В этой поездке пока нет заметок.",
                reply_markup=similar_trip_slider_keyboard(
                    [(type('obj', (object,), {'id': other_trip_id})(), 0)],
                    user_trip_id,
                    0
                )
            )
            return

        # Кнопка назад возвращает к слайдеру похожих поездок
        back_callback = f"similar_trip_view_{other_trip_id}_{user_trip_id}"

        await update.callback_query.message.edit_text(
            "📋 <b>Заметки поездки</b>\n\nВыберите заметку:",
            reply_markup=notes_list_keyboard(notes, other_trip_id, page=0, back_callback=back_callback, is_foreign=True, user_trip_id=user_trip_id),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def similar_trip_note_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр заметки из чужой поездки."""
    await update.callback_query.answer()

    note_id = int(context.match.group(1))
    other_trip_id = int(context.match.group(2))
    user_trip_id = int(context.match.group(3))

    session = get_session()
    try:
        note_service = NoteService(session)

        note = note_service.get_by_id(note_id)

        if note is None:
            await update.callback_query.message.edit_text(
                "❌ Заметка не найдена.",
                reply_markup=notes_menu_keyboard(user_trip_id, is_owner=True, is_admin=False)
            )
            return

        # Формируем текст заметки
        ai_marker = "🤖 " if note.is_ai_generated else ""
        text = f"{ai_marker}📝 <b>Заметка</b>\n\n{note.text}"

        # Если есть медиа, показываем его
        if note.media_type == "photo" and note.media_file_id:
            from telegram import InputMediaPhoto
            await update.callback_query.message.edit_media(
                media=InputMediaPhoto(media=note.media_file_id, caption=text, parse_mode="HTML"),
                reply_markup=similar_note_view_keyboard(note_id, other_trip_id, user_trip_id)
            )
        elif note.media_type == "video" and note.media_file_id:
            from telegram import InputMediaVideo
            await update.callback_query.message.edit_media(
                media=InputMediaVideo(media=note.media_file_id, caption=text, parse_mode="HTML"),
                reply_markup=similar_note_view_keyboard(note_id, other_trip_id, user_trip_id)
            )
        else:
            await update.callback_query.message.edit_text(
                text,
                reply_markup=similar_note_view_keyboard(note_id, other_trip_id, user_trip_id),
                parse_mode="HTML"
            )
    finally:
        close(session)


async def similar_trips_ignore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Игнорирование нажатий на неактивные кнопки пагинации."""
    await update.callback_query.answer()



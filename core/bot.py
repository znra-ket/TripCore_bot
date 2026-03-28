from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import TOKEN
from database import init_db, close_all
from handlers import (
    start,
    conversation_handler,
    show_about,
    show_my_trips,
    trips_page_change,
    trip_view,
    trips_back_to_menu,
    show_trips_list,
    chat_mode_handler,
    note_create_handler,
    note_ai_create_handler,
    note_edit_handler,
    show_notes_list,
    notes_list_page_change,
    view_note,
    delete_note,
    notes_list_ignore,
    show_similar_trips_list,
    similar_trips_page_change,
    similar_trip_view,
    similar_slider_navigate,
    similar_trip_notes_list,
    similar_trip_note_view,
    similar_trips_ignore,
    invite_handler,
    trip_settings_handler,
    user_management_handler,
    checklist_create_handler,
    checklist_add_item_handler,
    show_checklists_list,
    checklists_page_change,
    checklists_page_ignore,
    view_checklist,
    complete_item,
    delete_checklist,
    checklists_back_to_menu,
)


def create_bot() -> Application:
    """Создание и настройка бота."""
    init_db()

    app = Application.builder().token(token=TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conversation_handler)
    app.add_handler(CallbackQueryHandler(show_about, pattern=r"^about_me$"))
    app.add_handler(CallbackQueryHandler(show_my_trips, pattern=r"^my_trips$"))
    app.add_handler(CallbackQueryHandler(trips_page_change, pattern=r"^trips_page_(\d+)$"))
    app.add_handler(CallbackQueryHandler(trip_view, pattern=r"^trip_view_(\d+)$"))
    app.add_handler(CallbackQueryHandler(trips_back_to_menu, pattern=r"^trips_back_menu$"))
    app.add_handler(CallbackQueryHandler(show_trips_list, pattern=r"^show_trips_list$"))
    app.add_handler(CallbackQueryHandler(lambda u, c: u.callback_query.answer(), pattern=r"^trips_page_ignore$"))
    
    # Обработчики заметок
    app.add_handler(note_create_handler)
    app.add_handler(note_ai_create_handler)
    app.add_handler(note_edit_handler)
    app.add_handler(chat_mode_handler)
    app.add_handler(CallbackQueryHandler(show_notes_list, pattern=r"^note_list_(\d+)$"))
    app.add_handler(CallbackQueryHandler(notes_list_page_change, pattern=r"^note_list_page_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(view_note, pattern=r"^note_view_(\d+)$"))
    app.add_handler(CallbackQueryHandler(delete_note, pattern=r"^note_delete_(\d+)$"))
    app.add_handler(CallbackQueryHandler(notes_list_ignore, pattern=r"^note_list_ignore$"))
    
    # Обработчики похожих поездок
    app.add_handler(CallbackQueryHandler(show_similar_trips_list, pattern=r"^similar_trips_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_trips_page_change, pattern=r"^similar_trips_page_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_trip_view, pattern=r"^similar_trip_view_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_slider_navigate, pattern=r"^similar_slider_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_trip_notes_list, pattern=r"^similar_trip_notes_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_trip_note_view, pattern=r"^similar_note_view_(\d+)_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(similar_trips_ignore, pattern=r"^similar_trips_ignore$"))

    # Обработчики приглашений
    app.add_handler(invite_handler)

    # Обработчики настроек поездки
    app.add_handler(trip_settings_handler)

    # Обработчики управления пользователями
    app.add_handler(user_management_handler)

    # Обработчики чек-листов
    app.add_handler(checklist_create_handler)
    app.add_handler(checklist_add_item_handler)
    app.add_handler(CallbackQueryHandler(show_checklists_list, pattern=r"^checklist_list_(\d+)$"))
    app.add_handler(CallbackQueryHandler(checklists_page_change, pattern=r"^checklists_page_(\d+)_(\d+)$"))
    app.add_handler(CallbackQueryHandler(checklists_page_ignore, pattern=r"^checklists_page_ignore$"))
    app.add_handler(CallbackQueryHandler(view_checklist, pattern=r"^checklist_view_(\d+)$"))
    app.add_handler(CallbackQueryHandler(complete_item, pattern=r"^checklist_complete_(\d+)$"))
    app.add_handler(CallbackQueryHandler(delete_checklist, pattern=r"^checklist_delete_(\d+)$"))
    app.add_handler(CallbackQueryHandler(checklists_back_to_menu, pattern=r"^note_menu_(\d+)$"))

    return app


def run_bot() -> None:
    """Запуск бота."""
    app = create_bot()
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    finally:
        close_all()

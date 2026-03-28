from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Note


def notes_menu_keyboard(trip_id: int, is_owner: bool = True, is_admin: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура меню заметок для поездки.

    :param trip_id: ID поездки
    :param is_owner: Если True, показывать кнопку "Пригласить" и "Настройки" (только для владельца)
    :param is_admin: Если True, показывать кнопку "Пригласить" (для админа)
    """
    keyboard = [
        # 1 строка: Создать заметку, ИИ заметка
        [
            InlineKeyboardButton("📝 Создать заметку", callback_data=f"note_create_{trip_id}"),
            InlineKeyboardButton("🤖 ИИ заметка", callback_data=f"note_ai_create_{trip_id}")
        ],
        # 2 строка: Смотреть заметки, чек лист
        [
            InlineKeyboardButton("📋 Смотреть заметки", callback_data=f"note_list_{trip_id}"),
            InlineKeyboardButton("📋 Чек лист", callback_data=f"checklist_list_{trip_id}")
        ],
        # 3 строка: Похожие заметки
        [InlineKeyboardButton("🔍 Похожие поездки", callback_data=f"similar_trips_{trip_id}")],
    ]

    # 4 строка: Пригласить (только для владельца и администратора)
    if is_owner or is_admin:
        keyboard.append([InlineKeyboardButton("📩 Пригласить", callback_data=f"invite_create_{trip_id}")])

    # 5 строка: Управление поездкой (только для владельца)
    if is_owner:
        keyboard.append([InlineKeyboardButton("⚙️ Управление поездкой", callback_data=f"trip_settings_{trip_id}")])

    keyboard.append([InlineKeyboardButton("🔙 К списку поездок", callback_data="show_trips_list")])

    return InlineKeyboardMarkup(keyboard)


def note_media_keyboard(trip_id: int, note_type: str = "create") -> InlineKeyboardMarkup:
    """
    Клавиатура выбора типа медиа для заметки.
    
    :param trip_id: ID поездки
    :param note_type: "create" или "ai_create" - для возврата после создания
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📷 Прикрепить фото", callback_data=f"note_attach_photo_{trip_id}")],
        [InlineKeyboardButton("🎥 Прикрепить видео", callback_data=f"note_attach_video_{trip_id}")],
        [InlineKeyboardButton("✅ Готово", callback_data=f"note_finish_{trip_id}")],
    ])
    return keyboard


def note_ai_approve_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура одобрения ИИ заметки."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить текст", callback_data=f"note_ai_approve_{trip_id}")],
        [InlineKeyboardButton("🔄 Перегенерировать", callback_data=f"note_ai_regenerate_{trip_id}")],
        [InlineKeyboardButton("❌ Выйти", callback_data=f"note_ai_exit_{trip_id}")],
    ])
    return keyboard


def notes_list_keyboard(notes: list[Note], trip_id: int, page: int = 0, page_size: int = 3, back_callback: str = None, is_foreign: bool = False, user_trip_id: int = None) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком заметок и пагинацией.

    :param notes: Список всех заметок
    :param trip_id: ID поездки (для кнопки назад)
    :param page: Текущая страница (0-based)
    :param page_size: Количество кнопок на странице (максимум 3)
    :param back_callback: Callback для кнопки назад (по умолчанию note_menu_{trip_id})
    :param is_foreign: Если True, заметки чужой поездки (использовать другой callback)
    :param user_trip_id: ID поездки пользователя (для foreign заметок)
    """
    total_pages = (len(notes) + page_size - 1) // page_size if notes else 1
    page = max(0, min(page, total_pages - 1))

    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_notes = notes[start_idx:end_idx]

    keyboard = []

    # Кнопки с названиями заметок
    for i, note in enumerate(page_notes, start=start_idx):
        ai_marker = "🤖 " if note.is_ai_generated else ""
        if is_foreign and user_trip_id:
            # Для чужих заметок используем отдельный callback
            keyboard.append([InlineKeyboardButton(
                text=f"{ai_marker}Заметка {i + 1}",
                callback_data=f"similar_note_view_{note.id}_{trip_id}_{user_trip_id}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                text=f"{ai_marker}Заметка {i + 1}",
                callback_data=f"note_view_{note.id}"
            )])

    # Предпоследний ряд - кнопки навигации по страницам
    nav_row = []

    # Кнопка "Назад" - всегда видна, но неактивна если первая страница
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"note_list_page_{trip_id}_{page - 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(
            text="⬅️",
            callback_data="note_list_ignore"
        ))

    # Индикатор страницы
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="note_list_ignore"
    ))

    # Кнопка "Вперёд" - всегда видна, но неактивна если последняя страница
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"note_list_page_{trip_id}_{page + 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(
            text="➡️",
            callback_data="note_list_ignore"
        ))

    keyboard.append(nav_row)

    # Последний ряд - кнопка назад
    back_cb = back_callback if back_callback else f"note_menu_{trip_id}"
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=back_cb
    )])

    return InlineKeyboardMarkup(keyboard)


def note_view_keyboard(note_id: int, trip_id: int, can_edit: bool = False, can_delete: bool = False) -> InlineKeyboardMarkup:
    """Клавиатура просмотра заметки."""
    keyboard = []

    # Кнопки редактирования и удаления только для тех, у кого есть права
    if can_edit:
        keyboard.append([InlineKeyboardButton("✏️ Редактировать", callback_data=f"note_edit_{note_id}")])

    if can_delete:
        keyboard.append([InlineKeyboardButton("❌ Удалить заметку", callback_data=f"note_delete_{note_id}")])

    # Кнопка назад всегда отображается
    keyboard.append([InlineKeyboardButton("🔙 К списку поездок", callback_data="show_trips_list")])

    return InlineKeyboardMarkup(keyboard)


def note_back_to_menu_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура возврата в меню заметок."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 К списку поездок", callback_data="show_trips_list")],
    ])
    return keyboard


def similar_trips_list_keyboard(similar_trips: list, trip_id: int, page: int = 0, page_size: int = 3) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком похожих поездок и пагинацией.
    
    :param similar_trips: Список кортежей (trip, similarity) - поезд и процент сходства
    :param trip_id: ID исходной поездки пользователя
    :param page: Текущая страница (0-based)
    :param page_size: Количество кнопок на странице
    """
    if not similar_trips:
        return InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Назад", callback_data=f"note_menu_{trip_id}")
        ]])
    
    total_pages = (len(similar_trips) + page_size - 1) // page_size
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_trips = similar_trips[start_idx:end_idx]
    
    keyboard = []
    
    # Кнопки с названиями похожих поездок
    for trip, similarity in page_trips:
        keyboard.append([InlineKeyboardButton(
            text=f"📍 {trip.title} ({similarity:.0f}%)",
            callback_data=f"similar_trip_view_{trip.id}_{trip_id}"
        )])
    
    # Предпоследний ряд - кнопки навигации
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️",
            callback_data=f"similar_trips_page_{trip_id}_{page - 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="similar_trips_ignore"))
    
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="similar_trips_ignore"
    ))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="➡️",
            callback_data=f"similar_trips_page_{trip_id}_{page + 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(text="➡️", callback_data="similar_trips_ignore"))
    
    keyboard.append(nav_row)
    
    # Последний ряд - кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"note_menu_{trip_id}"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def similar_trip_slider_keyboard(similar_trips: list, trip_id: int, current_idx: int = 0) -> InlineKeyboardMarkup:
    """
    Клавиатура слайдера для просмотра похожих поездок.
    
    :param similar_trips: Список кортежей (trip, similarity)
    :param trip_id: ID исходной поездки пользователя
    :param current_idx: Текущий индекс в списке (0-based)
    """
    keyboard = []
    
    # Кнопки навигации слайдера
    nav_row = []
    
    if current_idx > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"similar_slider_{trip_id}_{current_idx - 1}"
        ))
    
    if current_idx < len(similar_trips) - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"similar_slider_{trip_id}_{current_idx + 1}"
        ))
    
    if nav_row:
        keyboard.append(nav_row)
    
    # Кнопка "Подробнее" для просмотра заметок
    current_trip_id = similar_trips[current_idx][0].id
    keyboard.append([InlineKeyboardButton(
        text="📋 Подробнее (заметки)",
        callback_data=f"similar_trip_notes_{current_trip_id}_{trip_id}"
    )])
    
    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 К списку похожих",
        callback_data=f"similar_trips_list_{trip_id}"
    )])
    
    return InlineKeyboardMarkup(keyboard)


def similar_note_view_keyboard(note_id: int, trip_id: int, user_trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура просмотра заметки из чужой поездки."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Назад к заметкам", callback_data=f"similar_trip_notes_{trip_id}_{user_trip_id}")],
    ])
    return keyboard


def invite_link_keyboard(invite_link: str, trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура со ссылкой-приглашением."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Скопировать ссылку", url=invite_link)],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"trip_view_{trip_id}")],
    ])
    return keyboard

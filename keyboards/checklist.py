from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Checklist, ChecklistItem


def checklists_list_keyboard(checklists: list[Checklist], trip_id: int, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком чек-листов и пагинацией.

    :param checklists: Список всех чек-листов
    :param trip_id: ID поездки
    :param page: Текущая страница (0-based)
    :param page_size: Количество кнопок на странице
    """
    total_pages = (len(checklists) + page_size - 1) // page_size if checklists else 1
    page = max(0, min(page, total_pages - 1))

    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_checklists = checklists[start_idx:end_idx]

    keyboard = []

    # Кнопки с названиями чек-листов
    for checklist in page_checklists:
        keyboard.append([InlineKeyboardButton(
            text=f"📋 {checklist.title}",
            callback_data=f"checklist_view_{checklist.id}"
        )])

    # Навигация по страницам
    if total_pages > 1:
        nav_row = []

        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"checklists_page_{trip_id}_{page - 1}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="checklists_page_ignore"))

        nav_row.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="checklists_page_ignore"
        ))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"checklists_page_{trip_id}_{page + 1}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(text="➡️", callback_data="checklists_page_ignore"))

        keyboard.append(nav_row)

    # Кнопка создания нового чек-листа
    keyboard.append([InlineKeyboardButton(
        text="➕ Создать чек-лист",
        callback_data=f"checklist_create_{trip_id}"
    )])

    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"note_menu_{trip_id}"
    )])

    return InlineKeyboardMarkup(keyboard)


def checklist_view_keyboard(
    checklist_id: int,
    trip_id: int,
    incomplete_items: list[ChecklistItem],
    show_delete: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура просмотра чек-листа с кнопками невыполненных задач.

    :param checklist_id: ID чек-листа
    :param trip_id: ID поездки
    :param incomplete_items: Список невыполненных задач
    :param show_delete: Показывать ли кнопку удаления чек-листа
    """
    keyboard = []

    # Кнопки невыполненных задач
    for item in incomplete_items:
        keyboard.append([InlineKeyboardButton(
            text=f"{item.order + 1}. {item.text}",
            callback_data=f"checklist_complete_{item.id}"
        )])

    # Кнопка добавления новой задачи
    keyboard.append([InlineKeyboardButton(
        text="➕ Добавить задачу",
        callback_data=f"checklist_add_item_{checklist_id}"
    )])

    # Кнопка удаления чек-листа (только для владельца)
    if show_delete:
        keyboard.append([InlineKeyboardButton(
            text="🗑️ Удалить чек-лист",
            callback_data=f"checklist_delete_{checklist_id}"
        )])

    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 К списку чек-листов",
        callback_data=f"checklist_list_{trip_id}"
    )])

    return InlineKeyboardMarkup(keyboard)


def checklist_empty_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура для случая, когда у пользователя нет чек-листов.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Создать чек-лист", callback_data=f"checklist_create_{trip_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"note_menu_{trip_id}")],
    ])
    return keyboard


def checklist_create_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура отмены при создании чек-листа.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data=f"checklist_list_{trip_id}")],
    ])
    return keyboard


def checklist_add_item_keyboard(checklist_id: int, trip_id: int) -> InlineKeyboardMarkup:
    """
    Клавиатура отмены при добавлении задачи.
    """
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data=f"checklist_view_{checklist_id}")],
    ])
    return keyboard

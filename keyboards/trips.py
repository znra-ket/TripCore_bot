from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from database.models import Trip


def trips_keyboard(trips: list[Trip], page: int = 0, page_size: int = 3) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком поездок и пагинацией.
    
    :param trips: Список всех поездок
    :param page: Текущая страница (0-based)
    :param page_size: Количество кнопок на странице (максимум 3)
    """
    total_pages = (len(trips) + page_size - 1) // page_size if trips else 1
    page = max(0, min(page, total_pages - 1))
    
    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_trips = trips[start_idx:end_idx]
    
    keyboard = []
    
    # Кнопки с названиями поездок
    for trip in page_trips:
        keyboard.append([InlineKeyboardButton(
            text=f"🚗 {trip.title}",
            callback_data=f"trip_view_{trip.id}"
        )])
    
    # Предпоследний ряд - кнопки навигации по страницам
    nav_row = []
    
    # Кнопка "Назад" - всегда видна, но неактивна если первая страница
    if page > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Назад",
            callback_data=f"trips_page_{page - 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(
            text="⬅️",
            callback_data="trips_page_ignore"
        ))
    
    # Индикатор страницы
    nav_row.append(InlineKeyboardButton(
        text=f"{page + 1}/{total_pages}",
        callback_data="trips_page_ignore"
    ))
    
    # Кнопка "Вперёд" - всегда видна, но неактивна если последняя страница
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton(
            text="Вперёд ➡️",
            callback_data=f"trips_page_{page + 1}"
        ))
    else:
        nav_row.append(InlineKeyboardButton(
            text="➡️",
            callback_data="trips_page_ignore"
        ))
    
    keyboard.append(nav_row)
    
    # Последний ряд - кнопка "В меню"
    keyboard.append([InlineKeyboardButton(
        text="🔙 В меню",
        callback_data="trips_back_menu"
    )])
    
    return InlineKeyboardMarkup(keyboard)

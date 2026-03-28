from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def users_list_keyboard(users: list, trip_id: int, page: int = 0, page_size: int = 5) -> InlineKeyboardMarkup:
    """
    Клавиатура со списком пользователей и пагинацией.

    :param users: Список кортежей (user_id, username, first_name, is_owner, is_admin)
    :param trip_id: ID поездки
    :param page: Текущая страница (0-based)
    :param page_size: Количество кнопок на странице
    """
    total_pages = (len(users) + page_size - 1) // page_size if users else 1
    page = max(0, min(page, total_pages - 1))

    start_idx = page * page_size
    end_idx = start_idx + page_size
    page_users = users[start_idx:end_idx]

    keyboard = []

    # Кнопки с пользователями
    for user_id, username, first_name, is_owner, is_admin in page_users:
        owner_marker = " 👑" if is_owner else ""
        admin_marker = " ⭐️" if is_admin and not is_owner else ""
        # Приоритет: username > first_name > User_ID
        if username:
            display_name = f"@{username}"
        elif first_name:
            display_name = first_name
        else:
            display_name = f"User_{user_id}"

        keyboard.append([InlineKeyboardButton(
            text=f"👤 {display_name}{owner_marker}{admin_marker}",
            callback_data=f"user_action_{user_id}_{trip_id}"
        )])

    # Навигация по страницам
    if total_pages > 1:
        nav_row = []

        if page > 0:
            nav_row.append(InlineKeyboardButton(
                text="⬅️",
                callback_data=f"users_page_{trip_id}_{page - 1}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(text="⬅️", callback_data="users_page_ignore"))

        nav_row.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="users_page_ignore"
        ))

        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton(
                text="➡️",
                callback_data=f"users_page_{trip_id}_{page + 1}"
            ))
        else:
            nav_row.append(InlineKeyboardButton(text="➡️", callback_data="users_page_ignore"))

        keyboard.append(nav_row)

    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data=f"trip_settings_{trip_id}"
    )])

    return InlineKeyboardMarkup(keyboard)


def user_action_keyboard(
    user_id: int,
    trip_id: int,
    username: str = None,
    first_name: str = None,
    is_owner: bool = False,
    is_admin: bool = False,
    current_user_is_owner: bool = False
) -> InlineKeyboardMarkup:
    """
    Клавиатура действий с пользователем.

    :param user_id: ID пользователя
    :param trip_id: ID поездки
    :param username: Username пользователя
    :param first_name: Имя пользователя
    :param is_owner: Является ли выбранный пользователь владельцем
    :param is_admin: Является ли выбранный пользователь админом
    :param current_user_is_owner: Является ли текущий пользователь владельцем поездки
    """
    # Приоритет: username > first_name > User_ID
    if username:
        display_name = f"@{username}"
    elif first_name:
        display_name = first_name
    else:
        display_name = f"User_{user_id}"

    keyboard = []

    # Кнопка назначения админом (только владелец может назначать)
    if current_user_is_owner and not is_owner and not is_admin:
        keyboard.append([InlineKeyboardButton(
            "⭐️ Назначить администратором",
            callback_data=f"user_make_admin_{user_id}_{trip_id}"
        )])

    # Кнопка удаления админа (только владелец может удалять админов)
    if current_user_is_owner and not is_owner and is_admin:
        keyboard.append([InlineKeyboardButton(
            "❌ Снять администратора",
            callback_data=f"user_remove_admin_{user_id}_{trip_id}"
        )])

    # Кнопка удаления из поездки (для не-владельцев)
    if not is_owner:
        keyboard.append([InlineKeyboardButton(
            "❌ Удалить из поездки",
            callback_data=f"user_delete_{user_id}_{trip_id}"
        )])

    # Кнопка назад
    keyboard.append([InlineKeyboardButton(
        "🔙 Назад к списку",
        callback_data=f"trip_users_{trip_id}"
    )])

    return InlineKeyboardMarkup(keyboard)


def user_delete_confirm_keyboard(user_id: int, trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления пользователя."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"user_delete_confirm_{user_id}_{trip_id}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"user_action_{user_id}_{trip_id}")],
    ])
    return keyboard

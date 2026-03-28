from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def trip_settings_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура меню управления поездкой."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Изменить название", callback_data=f"trip_rename_{trip_id}")],
        [InlineKeyboardButton("🗑️ Удалить поездку", callback_data=f"trip_delete_{trip_id}")],
        [InlineKeyboardButton("👥 Управление пользователями", callback_data=f"trip_users_{trip_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=f"trip_view_{trip_id}")],
    ])
    return keyboard


def trip_rename_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура отмены при переименовании."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Отмена", callback_data=f"trip_settings_{trip_id}")],
    ])
    return keyboard


def trip_delete_confirm_keyboard(trip_id: int) -> InlineKeyboardMarkup:
    """Клавиатура подтверждения удаления."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data=f"trip_delete_confirm_{trip_id}")],
        [InlineKeyboardButton("❌ Нет, отмена", callback_data=f"trip_settings_{trip_id}")],
    ])
    return keyboard

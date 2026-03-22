from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def chat_mode_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой выхода из чат-мода."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Выйти из чата", callback_data="chat_exit")],
    ])
    return keyboard

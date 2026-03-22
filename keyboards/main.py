from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def main_keyboard() -> InlineKeyboardMarkup:
    """Главная inline клавиатура с 4 кнопками."""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Создать поездку", callback_data="create_trip")],
        [InlineKeyboardButton("Мои поездки", callback_data="my_trips")],
        [InlineKeyboardButton("Обо мне", callback_data="about_me")],
        [InlineKeyboardButton("Чат мод", callback_data="chat_mod")],
    ])
    return keyboard

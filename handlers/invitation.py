from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler

from keyboards import invite_link_keyboard, notes_menu_keyboard, main_keyboard
from service import InvitationService, TripService
from database import get_session, close


async def create_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Создание приглашения в поездку и отправка deep link."""
    await update.callback_query.answer()

    trip_id = int(context.match.group(1))
    user_id = update.effective_user.id

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        trip_service = TripService(session)

        # Получаем поездку
        trip = trip_service.get_by_id(trip_id)

        if trip is None:
            await update.callback_query.message.edit_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return

        # Проверяем, что пользователь является владельцем поездки
        if trip.user_id != user_id:
            await update.callback_query.message.edit_text(
                "❌ Только владелец поездки может создавать приглашения.",
                reply_markup=notes_menu_keyboard(trip_id, is_owner=False, is_admin=False)
            )
            return

        # Создание приглашения
        token = invitation_service.create_invitation(
            trip_id=trip_id,
            inviter_user_id=user_id
        )

        # Формирование deep link
        bot_username = (await context.bot.get_me()).username
        invite_link = f"https://t.me/{bot_username}?start=invite_{token}"

        await update.callback_query.message.edit_text(
            f"📩 <b>Приглашение в поездку</b>\n\n"
            f"Поездка: <b>{trip.title}</b>\n\n"
            f"Отправьте эту ссылку другу:\n"
            f"<code>{invite_link}</code>\n\n"
            f"Или нажмите кнопку ниже, чтобы скопировать ссылку.",
            reply_markup=invite_link_keyboard(invite_link, trip_id),
            parse_mode="HTML"
        )
    finally:
        close(session)


async def handle_invite_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработка перехода по deep link с приглашением.
    Вызывается при нажатии /start с параметром invite_{token}.
    """
    if not context.args:
        await update.message.reply_text(
            "❌ Некорректная ссылка-приглашение.",
            reply_markup=main_keyboard()
        )
        return

    start_param = context.args[0]

    if not start_param.startswith("invite_"):
        await update.message.reply_text(
            "❌ Некорректная ссылка-приглашение.",
            reply_markup=main_keyboard()
        )
        return

    token = start_param.replace("invite_", "", 1)

    session = get_session()
    try:
        invitation_service = InvitationService(session)
        trip_service = TripService(session)

        # Поиск приглашения по токену
        invitation = invitation_service.get_invitation_by_token(token)

        if invitation is None:
            await update.message.reply_text(
                "❌ Приглашение не найдено или истекло.",
                reply_markup=main_keyboard()
            )
            return

        trip = trip_service.get_by_id(invitation.trip_id)

        if trip is None:
            await update.message.reply_text(
                "❌ Поездка не найдена.",
                reply_markup=main_keyboard()
            )
            return

        user_id = update.effective_user.id
        print(f"🔵 Обработка приглашения: user_id={user_id}, token={token}")

        # Если это владелец поездки
        if trip.user_id == user_id:
            await update.message.reply_text(
                f"ℹ️ Это ваша собственная поездка: <b>{trip.title}</b>\n\n"
                f"Вам не нужно принимать приглашение.",
                reply_markup=main_keyboard(),
                parse_mode="HTML"
            )
            return

        # Если уже принял приглашение
        if invitation.invitee_user_id == user_id:
            await update.message.reply_text(
                f"✅ Вы уже приняли приглашение в поездку: <b>{trip.title}</b>\n\n"
                f"Теперь вы можете просматривать и добавлять заметки в эту поездку.\n"
                f"Зайдите в раздел «Мои поездки», чтобы увидеть её.",
                reply_markup=main_keyboard(),
                parse_mode="HTML"
            )
            return

        # Если приглашение уже принято кем-то другим (не должно случиться с уникальным токеном)
        if invitation.invitee_user_id is not None:
            await update.message.reply_text(
                "❌ Это приглашение уже было использовано другим пользователем.",
                reply_markup=main_keyboard()
            )
            return

        # Принятие приглашения
        invitation = invitation_service.accept_invitation(token, user_id)

        if invitation is None:
            await update.message.reply_text(
                "❌ Не удалось принять приглашение.",
                reply_markup=main_keyboard()
            )
            return

        await update.message.reply_text(
            f"🎉 <b>Приглашение принято!</b>\n\n"
            f"Теперь у вас есть доступ к поездке: <b>{trip.title}</b>\n\n"
            f"Вы можете:\n"
            f"• Просматривать все заметки\n"
            f"• Добавлять новые заметки\n"
            f"• Удалять любые заметки в этой поездке\n\n"
            f"Зайдите в раздел «Мои поездки», чтобы увидеть её.",
            reply_markup=main_keyboard(),
            parse_mode="HTML"
        )
    finally:
        close(session)


invite_handler = CallbackQueryHandler(create_invite, pattern=r"^invite_create_(\d+)$")

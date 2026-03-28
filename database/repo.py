from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import User, Trip, Note, TripInvitation, Checklist, ChecklistItem


class UserRepo:
    """Репозиторий для работы с моделью User."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, username: str, first_name: str | None = None) -> User:
        """Создание нового пользователя."""
        user = User(user_id=user_id, username=username, first_name=first_name)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        """Получение пользователя по ID."""
        return self.session.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        """Получение пользователя по username."""
        return self.session.scalar(select(User).where(User.username == username))

    def update(self, user_id: int, username: str | None = None, first_name: str | None = None) -> User | None:
        """Обновление данных пользователя."""
        user = self.get_by_id(user_id)
        if user:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            self.session.commit()
            self.session.refresh(user)
        return user


class TripRepo:
    """Репозиторий для работы с моделью Trip."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, title: str, description: str | None = None) -> Trip:
        """Создание новой поездки."""
        trip = Trip(user_id=user_id, title=title, description=description or "")
        self.session.add(trip)
        self.session.commit()
        self.session.refresh(trip)
        return trip

    def get_by_id(self, trip_id: int) -> Trip | None:
        """Получение поездки по ID."""
        return self.session.get(Trip, trip_id)

    def get_by_user_id(self, user_id: int) -> list[Trip]:
        """Получение всех поездок пользователя."""
        return self.session.scalars(select(Trip).where(Trip.user_id == user_id)).all()

    def get_all_with_embedding(self) -> list[Trip]:
        """Получение всех поездок с эмбеддингом (для поиска похожих)."""
        return self.session.scalars(
            select(Trip).where(Trip.description_embedding.isnot(None))
        ).all()

    def update_title(self, trip_id: int, new_title: str) -> Trip | None:
        """Обновление названия поездки."""
        trip = self.get_by_id(trip_id)
        if trip:
            trip.title = new_title
            self.session.commit()
            self.session.refresh(trip)
        return trip

    def delete(self, trip_id: int) -> bool:
        """Удаление поездки."""
        trip = self.get_by_id(trip_id)
        if trip:
            self.session.delete(trip)
            self.session.commit()
            return True
        return False


class NoteRepo:
    """Репозиторий для работы с моделью Note."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        trip_id: int,
        text: str,
        user_id: int,
        media_type: str | None = None,
        media_file_id: str | None = None,
        is_ai_generated: bool = False,
    ) -> Note:
        """Создание новой заметки."""
        note = Note(
            trip_id=trip_id,
            user_id=user_id,
            text=text,
            media_type=media_type,
            media_file_id=media_file_id,
            is_ai_generated=is_ai_generated,
        )
        self.session.add(note)
        self.session.commit()
        self.session.refresh(note)
        return note

    def get_by_id(self, note_id: int) -> Note | None:
        """Получение заметки по ID."""
        return self.session.get(Note, note_id)

    def get_by_trip_id(self, trip_id: int) -> list[Note]:
        """Получение всех заметок поездки."""
        return self.session.scalars(select(Note).where(Note.trip_id == trip_id)).all()

    def delete(self, note_id: int) -> bool:
        """Удаление заметки по ID."""
        note = self.get_by_id(note_id)
        if note:
            self.session.delete(note)
            self.session.commit()
            return True
        return False

    def update_text(self, note_id: int, new_text: str) -> Note | None:
        """Обновление текста заметки."""
        note = self.get_by_id(note_id)
        if note:
            note.text = new_text
            self.session.commit()
            self.session.refresh(note)
        return note


class TripInvitationRepo:
    """Репозиторий для работы с моделью TripInvitation."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, trip_id: int, inviter_user_id: int, token: str) -> TripInvitation:
        """Создание нового приглашения."""
        invitation = TripInvitation(
            trip_id=trip_id,
            inviter_user_id=inviter_user_id,
            token=token
        )
        self.session.add(invitation)
        self.session.commit()
        self.session.refresh(invitation)
        return invitation

    def get_by_token(self, token: str) -> TripInvitation | None:
        """Получение приглашения по токену."""
        return self.session.get(TripInvitation, token, identity_token="token")

    def get_by_token_safe(self, token: str) -> TripInvitation | None:
        """Получение приглашения по токену (через select)."""
        return self.session.scalar(select(TripInvitation).where(TripInvitation.token == token))

    def accept(self, invitation: TripInvitation, invitee_user_id: int) -> TripInvitation:
        """Принятие приглашения пользователем."""
        print(f"🔵 Принятие приглашения: id={invitation.id}, token={invitation.token}, invitee_user_id={invitee_user_id}")
        invitation.invitee_user_id = invitee_user_id
        self.session.commit()
        self.session.refresh(invitation)
        print(f"🟢 Приглашение принято: invitee_user_id={invitation.invitee_user_id}")
        return invitation

    def get_by_user_and_trip(self, user_id: int, trip_id: int) -> TripInvitation | None:
        """Проверка, есть ли у пользователя доступ к поездке через приглашение."""
        return self.session.scalar(
            select(TripInvitation).where(
                TripInvitation.trip_id == trip_id,
                TripInvitation.invitee_user_id == user_id
            )
        )

    def get_by_trip(self, trip_id: int) -> list[TripInvitation]:
        """Получение всех приглашений для поездки."""
        return self.session.scalars(
            select(TripInvitation).where(TripInvitation.trip_id == trip_id)
        ).all()

    def delete(self, invitation: TripInvitation) -> None:
        """Удаление приглашения."""
        self.session.delete(invitation)
        self.session.commit()

    def delete_by_id(self, invitation_id: int) -> bool:
        """Удаление приглашения по ID."""
        invitation = self.session.get(TripInvitation, invitation_id)
        if invitation:
            self.session.delete(invitation)
            self.session.commit()
            return True
        return False

    def set_admin_role(self, invitation: TripInvitation, is_admin: bool) -> TripInvitation:
        """Установка или снятие роли администратора."""
        invitation.is_admin = is_admin
        self.session.commit()
        self.session.refresh(invitation)
        return invitation

    def get_by_user_and_trip_with_role(self, user_id: int, trip_id: int) -> TripInvitation | None:
        """Получение приглашения с данными о роли администратора."""
        return self.session.scalar(
            select(TripInvitation).where(
                TripInvitation.trip_id == trip_id,
                TripInvitation.invitee_user_id == user_id
            )
        )


class ChecklistRepo:
    """Репозиторий для работы с моделью Checklist."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, trip_id: int, title: str) -> Checklist:
        """Создание нового чек-листа."""
        checklist = Checklist(user_id=user_id, trip_id=trip_id, title=title)
        self.session.add(checklist)
        self.session.commit()
        self.session.refresh(checklist)
        return checklist

    def get_by_id(self, checklist_id: int) -> Checklist | None:
        """Получение чек-листа по ID."""
        return self.session.get(Checklist, checklist_id)

    def get_by_user_id(self, user_id: int) -> list[Checklist]:
        """Получение всех чек-листов пользователя."""
        return self.session.scalars(
            select(Checklist).where(Checklist.user_id == user_id)
        ).all()

    def get_by_trip_id(self, trip_id: int) -> list[Checklist]:
        """Получение всех чек-листов поездки."""
        return self.session.scalars(
            select(Checklist).where(Checklist.trip_id == trip_id)
        ).all()

    def delete(self, checklist_id: int) -> bool:
        """Удаление чек-листа."""
        checklist = self.get_by_id(checklist_id)
        if checklist:
            self.session.delete(checklist)
            self.session.commit()
            return True
        return False


class ChecklistItemRepo:
    """Репозиторий для работы с моделью ChecklistItem."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, checklist_id: int, text: str, order: int = 0) -> ChecklistItem:
        """Создание новой задачи чек-листа."""
        item = ChecklistItem(checklist_id=checklist_id, text=text, order=order)
        self.session.add(item)
        self.session.commit()
        self.session.refresh(item)
        return item

    def get_by_id(self, item_id: int) -> ChecklistItem | None:
        """Получение задачи по ID."""
        return self.session.get(ChecklistItem, item_id)

    def get_by_checklist_id(self, checklist_id: int) -> list[ChecklistItem]:
        """Получение всех задач чек-листа."""
        return self.session.scalars(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == checklist_id)
            .order_by(ChecklistItem.order)
        ).all()

    def get_incomplete_by_checklist_id(self, checklist_id: int) -> list[ChecklistItem]:
        """Получение невыполненных задач чек-листа."""
        return self.session.scalars(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == checklist_id, ChecklistItem.is_completed == False)
            .order_by(ChecklistItem.order)
        ).all()

    def mark_completed(self, item_id: int) -> ChecklistItem | None:
        """Отметка задачи как выполненной."""
        item = self.get_by_id(item_id)
        if item:
            item.is_completed = True
            self.session.commit()
            self.session.refresh(item)
        return item

    def delete(self, item_id: int) -> bool:
        """Удаление задачи."""
        item = self.get_by_id(item_id)
        if item:
            self.session.delete(item)
            self.session.commit()
            return True
        return False

    def count_total(self, checklist_id: int) -> int:
        """Подсчёт общего количества задач."""
        return self.session.scalar(
            select(ChecklistItem).where(ChecklistItem.checklist_id == checklist_id)
        ).count() if False else len(self.get_by_checklist_id(checklist_id))

    def count_completed(self, checklist_id: int) -> int:
        """Подсчёт количества выполненных задач."""
        return self.session.scalar(
            select(ChecklistItem)
            .where(ChecklistItem.checklist_id == checklist_id, ChecklistItem.is_completed == True)
        ).count() if False else len([i for i in self.get_by_checklist_id(checklist_id) if i.is_completed])

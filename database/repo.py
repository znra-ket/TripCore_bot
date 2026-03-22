from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import User, Trip, Note


class UserRepo:
    """Репозиторий для работы с моделью User."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, user_id: int, username: str) -> User:
        """Создание нового пользователя."""
        user = User(user_id=user_id, username=username)
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


class NoteRepo:
    """Репозиторий для работы с моделью Note."""

    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        trip_id: int,
        text: str,
        media_type: str | None = None,
        media_file_id: str | None = None,
        is_ai_generated: bool = False,
    ) -> Note:
        """Создание новой заметки."""
        note = Note(
            trip_id=trip_id,
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

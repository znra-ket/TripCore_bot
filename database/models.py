from datetime import datetime

from sqlalchemy import Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "Пользователи"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str | None] = mapped_column(String, nullable=True)  # Может быть None для приватных аккаунтов

    first_name: Mapped[str | None] = mapped_column(String, nullable=True)  # Имя пользователя

    trips: Mapped[list["Trip"]] = relationship(back_populates="user")
    invitations: Mapped[list["TripInvitation"]] = relationship(
        back_populates="inviter",
        foreign_keys="TripInvitation.inviter_user_id",
        cascade="all, delete-orphan"
    )
    accepted_invitations: Mapped[list["TripInvitation"]] = relationship(
        back_populates="invitee",
        foreign_keys="TripInvitation.invitee_user_id"
    )


class Trip(Base):
    __tablename__ = "Поездки"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String, nullable=False)

    description: Mapped[str] = mapped_column(Text, nullable=True)

    description_embedding: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-массив эмбеддинга

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Пользователи.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[User] = relationship(back_populates="trips")

    notes: Mapped[list["Note"]] = relationship(back_populates="trip", cascade="all, delete-orphan")
    invitations: Mapped[list["TripInvitation"]] = relationship(
        back_populates="trip",
        cascade="all, delete-orphan"
    )


class Note(Base):
    __tablename__ = "Заметки"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    media_type: Mapped[str | None] = mapped_column(String, nullable=True)  # "photo" или "video"
    media_file_id: Mapped[str | None] = mapped_column(String, nullable=True)

    is_ai_generated: Mapped[bool] = mapped_column(Integer, default=0)  # 0 = False, 1 = True

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Пользователи.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[User] = relationship()

    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Поездки.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip: Mapped[Trip] = relationship(back_populates="notes")


class TripInvitation(Base):
    __tablename__ = "Приглашения"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    token: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)  # UUID токен

    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Поездки.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip: Mapped[Trip] = relationship(back_populates="invitations")

    inviter_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Пользователи.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    inviter: Mapped[User] = relationship(
        back_populates="invitations",
        foreign_keys=[inviter_user_id]
    )

    invitee_user_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("Пользователи.user_id", ondelete="CASCADE"),
        nullable=True,
    )
    invitee: Mapped[User | None] = relationship(
        back_populates="accepted_invitations",
        foreign_keys=[invitee_user_id]
    )

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # Права администратора

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Checklist(Base):
    __tablename__ = "Чек листы"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    title: Mapped[str] = mapped_column(String, nullable=False)

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Пользователи.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    user: Mapped[User] = relationship()

    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Поездки.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip: Mapped[Trip] = relationship()

    items: Mapped[list["ChecklistItem"]] = relationship(
        back_populates="checklist",
        cascade="all, delete-orphan"
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ChecklistItem(Base):
    __tablename__ = "Задачи чек листа"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    order: Mapped[int] = mapped_column(Integer, default=0)  # Порядок задачи в списке

    checklist_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Чек листы.id", ondelete="CASCADE"),
        nullable=False,
    )
    checklist: Mapped[Checklist] = relationship(back_populates="items")

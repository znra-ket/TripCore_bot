from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "Пользователи"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    username: Mapped[str] = mapped_column(String, nullable=False)

    trips: Mapped[list["Trip"]] = relationship(back_populates="user")


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


class Note(Base):
    __tablename__ = "Заметки"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)

    media_type: Mapped[str | None] = mapped_column(String, nullable=True)  # "photo" или "video"
    media_file_id: Mapped[str | None] = mapped_column(String, nullable=True)

    is_ai_generated: Mapped[bool] = mapped_column(Integer, default=0)  # 0 = False, 1 = True

    trip_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Поездки.id", ondelete="CASCADE"),
        nullable=False,
    )
    trip: Mapped[Trip] = relationship(back_populates="notes")

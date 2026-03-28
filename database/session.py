from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from database.models import Base

_engine = None
_session_maker = None

def init_db() -> None:
    """Инициализация базы данных."""
    global _engine, _session_maker

    _engine = create_engine(DATABASE_URL)
    _session_maker = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)


def close(session: Session) -> None:
    """Закрытие конкретной сессии."""
    session.close()


def close_all() -> None:
    """Закрытие всех соединений при завершении работы бота."""
    global _engine, _session_maker

    if _session_maker is not None:
        _session_maker.close_all()
    if _engine is not None:
        _engine.dispose()


def get_session() -> Session:
    """Создание новой сессии для каждого запроса."""
    if _session_maker is None:
        raise RuntimeError("БД не инициализирована. Вызовите init_db()")
    return _session_maker()
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from database.models import Base

_engine = None
_session_maker = None
_session: Session | None = None


def init_db() -> None:
    """Инициализация базы данных: создание движка, сессии и таблиц."""
    global _engine, _session_maker, _session
    
    _engine = create_engine(DATABASE_URL)
    _session_maker = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)
    _session = _session_maker()


def close() -> None:
    """Закрытие сессии и движка."""
    global _session, _engine
    
    if _session:
        _session.close()
        _session = None
    
    if _engine:
        _engine.dispose()
        _engine = None


def get_session() -> Session:
    """Получение текущей сессии."""
    if _session is None:
        raise RuntimeError("Сессия не инициализирована. Вызовите init_db()")
    return _session

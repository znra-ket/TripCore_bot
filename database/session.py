from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import DATABASE_URL
from database.models import Base

_engine = None
_session_maker = None
_session: Session | None = None


def close() -> None:
    """Закрытие сессии и движка."""
    global _session, _engine
    
    if _session:
        _session.close()
        _session = None
    
    if _engine:
        _engine.dispose()
        _engine = None

def init_db() -> None:
    """Инициализация базы данных."""
    global _engine, _session_maker
    
    _engine = create_engine(DATABASE_URL)
    _session_maker = sessionmaker(bind=_engine)
    Base.metadata.create_all(bind=_engine)

def get_session() -> Session:
    """Создание новой сессии для каждого запроса."""
    if _session_maker is None:
        raise RuntimeError("БД не инициализирована. Вызовите init_db()")
    return _session_maker()

from sqlalchemy.orm import Session

from database.repo import UserRepo
from database.models import User


class UserService:
    """Сервис для работы с пользователями."""

    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepo(session)

    def create(self, user_id: int, username: str) -> User:
        """Создание нового пользователя."""
        return self.user_repo.create(user_id, username)

    def get_or_create(self, user_id: int, username: str) -> User:
        """Получение или создание пользователя."""
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            user = self.user_repo.create(user_id, username)
        return user

    def get_by_id(self, user_id: int) -> User | None:
        """Получение пользователя по ID."""
        return self.user_repo.get_by_id(user_id)

    def get_by_username(self, username: str) -> User | None:
        """Получение пользователя по username."""
        return self.user_repo.get_by_username(username)

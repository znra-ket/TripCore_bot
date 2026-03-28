from sqlalchemy.orm import Session

from database.repo import TripRepo
from database.models import Trip


class TripService:
    """Сервис для работы с поездками."""

    def __init__(self, session: Session):
        self.session = session
        self.trip_repo = TripRepo(session)

    def create(self, user_id: int, title: str, description: str | None = None) -> Trip:
        """Создание новой поездки."""
        return self.trip_repo.create(user_id, title, description)

    def get_by_id(self, trip_id: int) -> Trip | None:
        """Получение поездки по ID."""
        return self.trip_repo.get_by_id(trip_id)

    def get_by_user_id(self, user_id: int) -> list[Trip]:
        """Получение всех поездок пользователя."""
        return self.trip_repo.get_by_user_id(user_id)

    def update_description(self, trip_id: int, description: str, embedding: str) -> Trip | None:
        """Обновление описания и эмбеддинга поездки."""
        trip = self.get_by_id(trip_id)
        if trip:
            trip.description = description
            trip.description_embedding = embedding
            self.session.commit()
            self.session.refresh(trip)
            print(f"💾 Описание и эмбеддинг сохранены в БД для поездки {trip_id}")
            return trip
        else:
            print(f"❌ Поездка {trip_id} не найдена для обновления описания")
            return None

    def update_title(self, trip_id: int, new_title: str) -> Trip | None:
        """Обновление названия поездки."""
        trip = self.trip_repo.update_title(trip_id, new_title)
        if trip:
            print(f"💾 Название поездки {trip_id} обновлено на '{new_title}'")
        return trip

    def delete_trip(self, trip_id: int) -> bool:
        """Удаление поездки."""
        result = self.trip_repo.delete(trip_id)
        if result:
            print(f"💾 Поездка {trip_id} удалена")
        return result

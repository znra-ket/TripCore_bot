import json
import math
from sqlalchemy.orm import Session

from database.repo import TripRepo
from database.models import Trip


class SimilarTripService:
    """Сервис для поиска похожих поездок на основе эмбеддингов."""

    def __init__(self, session: Session):
        self.session = session
        self.trip_repo = TripRepo(session)

    def _cosine_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Вычисление косинусного сходства между двумя эмбеддингами.
        
        :return: значение от 0 до 1, где 1 - идентичные векторы
        """
        if not embedding1 or not embedding2:
            return 0.0
        
        # Скалярное произведение
        dot_product = sum(a * b for a, b in zip(embedding1, embedding2))
        
        # Нормы векторов
        norm1 = math.sqrt(sum(a * a for a in embedding1))
        norm2 = math.sqrt(sum(b * b for b in embedding2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)

    def _parse_embedding(self, embedding_json: str) -> list[float]:
        """Парсинг JSON-строки эмбеддинга в список float."""
        try:
            return json.loads(embedding_json)
        except (json.JSONDecodeError, TypeError):
            return []

    def find_similar_trips(self, trip_id: int, limit: int = 5) -> list[tuple[Trip, float]]:
        """
        Поиск похожих поездок на основе эмбеддинга.
        
        :param trip_id: ID поездки пользователя
        :param limit: Максимальное количество похожих поездок (до 5)
        :return: Список кортежей (Trip, similarity) отсортированный по убыванию сходства
        """
        # Получаем целевую поездку
        target_trip = self.trip_repo.get_by_id(trip_id)
        if not target_trip or not target_trip.description_embedding:
            return []

        target_embedding = self._parse_embedding(target_trip.description_embedding)
        if not target_embedding:
            return []

        # Получаем все поездки с эмбеддингом (кроме поездок текущего пользователя)
        all_trips = self.trip_repo.get_all_with_embedding()
        
        # Фильтруем поездки того же пользователя и саму целевую поездку
        other_trips = [
            trip for trip in all_trips 
            if trip.user_id != target_trip.user_id and trip.id != trip_id
        ]

        # Вычисляем сходство для каждой поездки
        similarities = []
        for trip in other_trips:
            trip_embedding = self._parse_embedding(trip.description_embedding)
            if trip_embedding:
                similarity = self._cosine_similarity(target_embedding, trip_embedding)
                if similarity > 0.3:  # Порог минимального сходства (30%)
                    similarities.append((trip, similarity * 100))  # Конвертируем в проценты

        # Сортируем по убыванию сходства и ограничиваем результат
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:limit]

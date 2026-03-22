from sqlalchemy.orm import Session

from database.repo import NoteRepo, TripRepo
from database.models import Note
from service.agent_serv import AgentService
from service.trip_serv import TripService


class NoteService:
    """Сервис для работы с заметками."""

    def __init__(self, session: Session):
        self.session = session
        self.note_repo = NoteRepo(session)
        self.trip_repo = TripRepo(session)

    def create(
        self,
        trip_id: int,
        text: str,
        media_type: str | None = None,
        media_file_id: str | None = None,
        is_ai_generated: bool = False,
    ) -> Note:
        """Создание новой заметки."""
        trip = self.trip_repo.get_by_id(trip_id)
        if trip is None:
            raise ValueError(f"Поездка с ID {trip_id} не найдена")
        
        note = self.note_repo.create(
            trip_id=trip_id,
            text=text,
            media_type=media_type,
            media_file_id=media_file_id,
            is_ai_generated=is_ai_generated,
        )
        
        # Генерируем описание поездки на основе всех заметок
        self._regenerate_trip_description(trip_id)
        
        return note

    def _regenerate_trip_description(self, trip_id: int) -> None:
        """Генерация и сохранение описания поездки на основе заметок."""
        try:
            agent_service = AgentService(self.session)
            trip_service = TripService(self.session)

            description, embedding = agent_service.generate_trip_description(trip_id)

            if description:
                # Сохраняем описание даже если эмбеддинг не сгенерировался
                trip_service.update_description(trip_id, description, embedding)
                if embedding:
                    print(f"✅ Описание и эмбеддинг для поездки {trip_id} сохранены в БД")
                else:
                    print(f"✅ Описание для поездки {trip_id} сохранено в БД (без эмбеддинга)")
            else:
                print(f"⚠️ Не удалось сгенерировать описание для поездки {trip_id} (лимит или ошибка)")
        except Exception as e:
            print(f"❌ Ошибка при генерации описания для поездки {trip_id}: {e}")

    def get_by_id(self, note_id: int) -> Note | None:
        """Получение заметки по ID."""
        return self.note_repo.get_by_id(note_id)

    def get_by_trip_id(self, trip_id: int) -> list[Note]:
        """Получение всех заметок поездки."""
        return self.note_repo.get_by_trip_id(trip_id)

    def delete(self, note_id: int) -> bool:
        """Удаление заметки по ID."""
        note = self.get_by_id(note_id)
        trip_id = note.trip_id if note else None
        
        result = self.note_repo.delete(note_id)
        
        # После удаления заметки перегенерируем описание поездки
        if trip_id and result:
            self._regenerate_trip_description(trip_id)
        
        return result

    def mark_as_ai_generated(self, note_id: int) -> Note | None:
        """Отметить заметку как созданную ИИ."""
        note = self.get_by_id(note_id)
        if note:
            note.is_ai_generated = True
            self.session.commit()
            self.session.refresh(note)
        return note

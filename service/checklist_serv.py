from sqlalchemy.orm import Session

from database.repo import ChecklistRepo, ChecklistItemRepo
from database.models import Checklist, ChecklistItem


class ChecklistService:
    """Сервис для работы с чек-листами."""

    def __init__(self, session: Session):
        self.session = session
        self.checklist_repo = ChecklistRepo(session)
        self.item_repo = ChecklistItemRepo(session)

    def create_checklist(self, user_id: int, trip_id: int, title: str) -> Checklist:
        """Создание нового чек-листа."""
        return self.checklist_repo.create(user_id, trip_id, title)

    def get_checklist_by_id(self, checklist_id: int) -> Checklist | None:
        """Получение чек-листа по ID."""
        return self.checklist_repo.get_by_id(checklist_id)

    def get_checklists_by_user_id(self, user_id: int) -> list[Checklist]:
        """Получение всех чек-листов пользователя."""
        return self.checklist_repo.get_by_user_id(user_id)

    def get_checklists_by_trip_id(self, trip_id: int) -> list[Checklist]:
        """Получение всех чек-листов поездки."""
        return self.checklist_repo.get_by_trip_id(trip_id)

    def delete_checklist(self, checklist_id: int) -> bool:
        """Удаление чек-листа."""
        return self.checklist_repo.delete(checklist_id)

    def add_item(self, checklist_id: int, text: str) -> ChecklistItem:
        """Добавление новой задачи в чек-лист."""
        # Получаем текущий максимальный order
        items = self.item_repo.get_by_checklist_id(checklist_id)
        order = len(items)  # Новая задача будет последней
        return self.item_repo.create(checklist_id, text, order)

    def get_items_by_checklist_id(self, checklist_id: int) -> list[ChecklistItem]:
        """Получение всех задач чек-листа."""
        return self.item_repo.get_by_checklist_id(checklist_id)

    def get_incomplete_items(self, checklist_id: int) -> list[ChecklistItem]:
        """Получение невыполненных задач."""
        return self.item_repo.get_incomplete_by_checklist_id(checklist_id)

    def complete_item(self, item_id: int) -> ChecklistItem | None:
        """
        Отметка задачи как выполненной.
        Если все задачи выполнены - удаляет чек-лист.
        """
        item = self.item_repo.mark_completed(item_id)
        if item:
            # Проверяем, все ли задачи выполнены
            checklist_id = item.checklist_id
            items = self.get_items_by_checklist_id(checklist_id)
            all_completed = all(i.is_completed for i in items)

            if all_completed and len(items) > 0:
                # Все задачи выполнены - удаляем чек-лист
                self.delete_checklist(checklist_id)
                return None  # Возвращаем None, так как чек-лист удалён

        return item

    def delete_item(self, item_id: int) -> bool:
        """Удаление задачи."""
        return self.item_repo.delete(item_id)

    def is_checklist_owner(self, checklist_id: int, user_id: int) -> bool:
        """Проверка, является ли пользователь владельцем чек-листа."""
        checklist = self.get_checklist_by_id(checklist_id)
        return checklist is not None and checklist.user_id == user_id

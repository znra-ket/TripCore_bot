import uuid

from sqlalchemy.orm import Session

from database.repo import TripInvitationRepo, TripRepo, UserRepo
from database.models import Trip, TripInvitation, User


class InvitationService:
    """Сервис для работы с приглашениями в поездки."""

    def __init__(self, session: Session):
        self.session = session
        self.invitation_repo = TripInvitationRepo(session)
        self.trip_repo = TripRepo(session)
        self.user_repo = UserRepo(session)

    def create_invitation(self, trip_id: int, inviter_user_id: int) -> str:
        """
        Создание нового приглашения в поездку.

        :return: UUID токен приглашения
        """
        trip = self.trip_repo.get_by_id(trip_id)
        if trip is None:
            raise ValueError(f"Поездка с ID {trip_id} не найдена")

        if trip.user_id != inviter_user_id:
            raise ValueError(f"Пользователь {inviter_user_id} не является владельцем поездки {trip_id}")

        token = str(uuid.uuid4())
        self.invitation_repo.create(
            trip_id=trip_id,
            inviter_user_id=inviter_user_id,
            token=token
        )

        return token

    def get_invitation_by_token(self, token: str) -> TripInvitation | None:
        """Получение приглашения по токену."""
        return self.invitation_repo.get_by_token_safe(token)

    def accept_invitation(self, token: str, invitee_user_id: int) -> TripInvitation | None:
        """
        Принятие приглашения пользователем.

        :return: приглашение или None, если не найдено
        """
        invitation = self.get_invitation_by_token(token)
        if invitation is None:
            return None

        # Если уже принято этим пользователем
        if invitation.invitee_user_id == invitee_user_id:
            return invitation

        # Принимаем приглашение
        return self.invitation_repo.accept(invitation, invitee_user_id)

    def has_access_to_trip(self, user_id: int, trip_id: int) -> bool:
        """
        Проверка, есть ли у пользователя доступ к поездке.

        Доступ есть, если:
        - Пользователь является владельцем поездки
        - Пользователь принял приглашение в эту поездку
        """
        trip = self.trip_repo.get_by_id(trip_id)
        if trip is None:
            return False

        # Владелец всегда имеет доступ
        if trip.user_id == user_id:
            return True

        # Проверяем, есть ли принятое приглашение
        invitation = self.invitation_repo.get_by_user_and_trip(user_id, trip_id)
        return invitation is not None

    def get_trip_accessible_by_user(self, user_id: int) -> list[Trip]:
        """
        Получение всех поездок, доступных пользователю.

        Включает:
        - Личные поездки пользователя
        - Поездки, куда пользователя пригласили
        """
        from sqlalchemy import select

        print(f"🔍 Получение поездок для пользователя {user_id}")

        # Личные поездки
        personal_trips = self.trip_repo.get_by_user_id(user_id)
        print(f"📋 Личные поездки: {len(personal_trips)}")

        # Поездки по приглашениям
        stmt = select(TripInvitation).where(TripInvitation.invitee_user_id == user_id)
        invitations = self.session.scalars(stmt).all()
        print(f"📋 Приглашения (invitee_user_id={user_id}): {len(invitations)}")
        for inv in invitations:
            print(f"   - trip_id={inv.trip_id}, token={inv.token}")

        invited_trip_ids = [inv.trip_id for inv in invitations]

        if not invited_trip_ids:
            return personal_trips

        stmt = select(Trip).where(Trip.id.in_(invited_trip_ids))
        invited_trips = [
            trip for trip in self.session.scalars(stmt).all()
            if trip.user_id != user_id  # Исключаем личные поездки (они уже добавлены)
        ]
        print(f"📋 Поездки по приглашениям: {len(invited_trips)}")

        result = personal_trips + invited_trips
        print(f"📋 Всего поездок: {len(result)}")
        return result

    def get_users_with_access(self, trip_id: int) -> list[tuple[int, str | None, str | None, bool, bool]]:
        """
        Получение всех пользователей, имеющих доступ к поездке.

        :return: Список кортежей (user_id, username, first_name, is_owner, is_admin), отсортированный по username
        """
        trip = self.trip_repo.get_by_id(trip_id)
        if trip is None:
            return []

        # Владелец поездки
        owner = (trip.user_id, trip.user.username if trip.user else None, trip.user.first_name if trip.user else None, True, False)

        # Приглашённые пользователи
        invitations = self.invitation_repo.get_by_trip(trip_id)
        invited_users = []

        for inv in invitations:
            if inv.invitee_user_id:  # Только принятые приглашения
                user = self.user_repo.get_by_id(inv.invitee_user_id)
                username = user.username if user else None
                first_name = user.first_name if user else None
                invited_users.append((inv.invitee_user_id, username, first_name, False, inv.is_admin))

        # Сортировка приглашённых по username (алфавит)
        invited_users.sort(key=lambda x: x[1] or "")

        # Владелец всегда первый, затем приглашённые по алфавиту
        return [owner] + invited_users

    def revoke_access(self, trip_id: int, user_id: int) -> bool:
        """
        Отозвать доступ пользователя к поездке.

        :param trip_id: ID поездки
        :param user_id: ID пользователя
        :return: True, если доступ успешно отозван
        """
        trip = self.trip_repo.get_by_id(trip_id)
        if trip is None:
            return False

        # Нельзя удалить владельца
        if trip.user_id == user_id:
            return False

        # Найти приглашение
        invitation = self.invitation_repo.get_by_user_and_trip(user_id, trip_id)
        if invitation:
            return self.invitation_repo.delete_by_id(invitation.id)

        return False

    def is_owner(self, user_id: int, trip_id: int) -> bool:
        """
        Проверка, является ли пользователь владельцем поездки.

        :return: True, если пользователь является создателем поездки
        """
        trip = self.trip_repo.get_by_id(trip_id)
        return trip is not None and trip.user_id == user_id

    def is_admin(self, user_id: int, trip_id: int) -> bool:
        """
        Проверка, является ли пользователь администратором поездки.

        :return: True, если пользователь имеет права администратора
        """
        # Владелец всегда имеет права администратора
        if self.is_owner(user_id, trip_id):
            return True

        # Проверяем роль администратора в приглашении
        invitation = self.invitation_repo.get_by_user_and_trip_with_role(user_id, trip_id)
        return invitation is not None and invitation.is_admin

    def can_delete_note(self, user_id: int, trip_id: int, note_owner_id: int) -> bool:
        """
        Проверка права на удаление заметки.

        :param user_id: ID пользователя, который хочет удалить
        :param trip_id: ID поездки
        :param note_owner_id: ID владельца заметки
        :return: True, если пользователь может удалить заметку
        """
        # Владелец поездки может удалять любые заметки
        if self.is_owner(user_id, trip_id):
            return True

        # Администратор может удалять любые заметки
        if self.is_admin(user_id, trip_id):
            return True

        # Пользователь может удалять только свои заметки
        return user_id == note_owner_id

    def can_edit_note(self, user_id: int, trip_id: int, note_owner_id: int) -> bool:
        """
        Проверка права на редактирование заметки.

        :param user_id: ID пользователя, который хочет редактировать
        :param trip_id: ID поездки
        :param note_owner_id: ID владельца заметки
        :return: True, если пользователь может редактировать заметку
        """
        # Владелец поездки может редактировать любые заметки
        if self.is_owner(user_id, trip_id):
            return True

        # Пользователь может редактировать только свои заметки (администраторы не могут редактировать чужие)
        return user_id == note_owner_id

    def can_delete_user(self, deleter_user_id: int, trip_id: int, target_user_id: int) -> bool:
        """
        Проверка права на удаление пользователя из поездки.

        :param deleter_user_id: ID пользователя, который хочет удалить
        :param trip_id: ID поездки
        :param target_user_id: ID пользователя, которого хотят удалить
        :return: True, если пользователь может удалить другого пользователя
        """
        # Только владелец и администратор могут удалять пользователей
        if not (self.is_owner(deleter_user_id, trip_id) or self.is_admin(deleter_user_id, trip_id)):
            return False

        # Нельзя удалить владельца
        if self.is_owner(target_user_id, trip_id):
            return False

        # Администратор не может удалять других администраторов и владельца
        target_invitation = self.invitation_repo.get_by_user_and_trip_with_role(target_user_id, trip_id)
        if target_invitation and target_invitation.is_admin:
            return False

        return True

    def can_invite_users(self, user_id: int, trip_id: int) -> bool:
        """
        Проверка права на приглашение пользователей.

        :return: True, если пользователь может приглашать других
        """
        # Владелец и администратор могут приглашать
        return self.is_owner(user_id, trip_id) or self.is_admin(user_id, trip_id)

    def make_admin(self, trip_id: int, target_user_id: int, admin_user_id: int) -> bool:
        """
        Назначить пользователя администратором.

        :param trip_id: ID поездки
        :param target_user_id: ID пользователя, которого назначают админом
        :param admin_user_id: ID пользователя, который назначает (должен быть владельцем)
        :return: True, если успешно назначен
        """
        # Только владелец может назначать администраторов
        if not self.is_owner(admin_user_id, trip_id):
            return False

        # Нельзя назначить самого себя (уже владелец)
        if target_user_id == admin_user_id:
            return False

        # Найти приглашение
        invitation = self.invitation_repo.get_by_user_and_trip_with_role(target_user_id, trip_id)
        if invitation is None:
            return False

        # Установить роль администратора
        self.invitation_repo.set_admin_role(invitation, True)
        return True

    def get_user_trip_role(self, user_id: int, trip_id: int) -> str:
        """
        Получить роль пользователя в поездке.

        :return: "owner", "admin", или "member"
        """
        if self.is_owner(user_id, trip_id):
            return "owner"
        if self.is_admin(user_id, trip_id):
            return "admin"
        return "member"

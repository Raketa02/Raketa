from app.modules.auth.domain.ports import PasswordHasher
from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.domain.errors import EmailAlreadyRegistered, NicknameAlreadyTaken
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Nickname,
    RawPassword,
)
from app.infrastructure.database.unit_of_work import UnitOfWork
from app.shared.ids import new_uuid


class RegisterUser:
    """Create a new user with a hashed password.

    Reads twice (email + nickname) before insert to surface a domain-specific
    conflict instead of relying on a DB unique-constraint violation.
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        uow: UnitOfWork,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._uow = uow

    async def execute(self, command: RegisterUserCommand) -> User:
        email = Email(command.email)
        nickname = Nickname(command.nickname)
        raw_password = RawPassword(command.password)

        if await self._users.get_by_email(email.value):
            raise EmailAlreadyRegistered()
        if await self._users.get_by_nickname(nickname.value):
            raise NicknameAlreadyTaken()

        user = User(
            id=new_uuid(),
            email=email,
            nickname=nickname,
            password_hash=HashedPassword(self._hasher.hash(raw_password.value)),
            authority=Authority.USER,
            is_admin=False,
            is_active=True,
        )
        user = await self._users.add(user)
        await self._uow.commit()
        return user

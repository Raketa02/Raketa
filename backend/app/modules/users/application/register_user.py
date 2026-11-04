from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.kernel import Clock
from app.modules.auth.domain.ports import PasswordHasher
from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.application.user_stream import USER_AGGREGATE
from app.modules.users.domain.errors import EmailAlreadyRegistered
from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    AdultAttestation,
    Email,
    HashedPassword,
    RawPassword,
)
from app.shared.ids import new_uuid


class RegisterUser:
    """Open an account with a hashed password — **credentials only**.

    Reads the email before insert to surface a domain-specific conflict instead
    of relying on a DB unique-constraint violation. The nickname's read moved to
    the act that carries it, the naming (``docs/adr/0199`` §3): a fresh account
    has no nickname.

    **The attestation is refused before the read.** It is built alongside the
    other value objects, above the lookup, so a caller who answered nothing is
    told so without learning which emails are taken.
    """

    def __init__(
        self,
        users: UserRepository,
        event_store: DomainEventStore,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._users = users
        self._event_store = event_store
        self._hasher = hasher
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: RegisterUserCommand) -> User:
        email = Email(command.email)
        raw_password = RawPassword(command.password)
        attestation = AdultAttestation(command.adult_attested)

        if await self._users.get_by_email(email.value):
            raise EmailAlreadyRegistered()

        user = User.register(
            user_id=new_uuid(),
            email=email,
            password_hash=HashedPassword(self._hasher.hash(raw_password.value)),
            attestation=attestation,
            occurred_at=self._clock.now(),
        )
        pending_events = user.pull_events()
        if not pending_events:
            raise RuntimeError("user registration produced no domain event")
        registered_event = pending_events[0]
        if not isinstance(registered_event, UserRegistered):
            raise RuntimeError("user registration must start with UserRegistered")

        await self._event_store.append(
            aggregate_type=USER_AGGREGATE,
            aggregate_id=user.id,
            expected_version=0,
            events=pending_events,
        )
        persisted_user = await self._users.project_registered(registered_event)
        await self._events.publish_many(pending_events)
        await self._uow.commit()
        return persisted_user

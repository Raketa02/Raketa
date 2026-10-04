from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.auth.domain.ports import PasswordHasher
from app.modules.clubs.application.club_details import details_from
from app.modules.clubs.application.commands import SignUpClubCommand
from app.modules.clubs.domain.club import Club
from app.modules.clubs.domain.club_account import ClubAccount
from app.modules.clubs.domain.errors import ClubEmailAlreadyRegistered
from app.modules.clubs.domain.ports import ClubAccountRepository, ClubRepository
from app.modules.users.domain.errors import EmailInvalid, PasswordTooWeak
from app.modules.users.domain.value_objects import Email, HashedPassword, RawPassword
from app.shared.ids import new_uuid


class SignUpClub:
    """A club signs up, and its account is opened in the same act.

    **One transaction for both** (``docs/adr/0182`` §4): a club with no way to
    sign in, or an account with no club, is a state nobody could repair from the
    website. There is no verification step and no per-club URL.

    **Every field is refused before the email is looked up**, as ``RegisterUser``
    refuses the attestation first: a caller whose form is wrong is told so
    without learning which emails are taken. The lookup is among club accounts
    only — the same address may be an unrelated player's.
    """

    def __init__(
        self,
        *,
        clubs: ClubRepository,
        accounts: ClubAccountRepository,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._accounts = accounts
        self._hasher = hasher
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SignUpClubCommand) -> Club:
        details = details_from(command.details)
        try:
            email = Email(command.email)
        except ValueError:
            raise EmailInvalid() from None
        try:
            password = RawPassword(command.password)
        except ValueError:
            raise PasswordTooWeak() from None

        if await self._accounts.get_by_email(email) is not None:
            raise ClubEmailAlreadyRegistered()

        now = self._clock.now()
        club = Club.register(club_id=new_uuid(), details=details, occurred_at=now)
        account = ClubAccount.open(
            account_id=new_uuid(),
            club_id=club.id,
            email=email,
            password_hash=HashedPassword(self._hasher.hash(password.value)),
            occurred_at=now,
        )
        await self._clubs.save(club)
        await self._accounts.save(account)
        await self._uow.commit()
        return club

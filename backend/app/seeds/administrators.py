"""The administrators: Ogrody 33 names three people — one who is new to Raketa,
one who already plays, and one who has not answered yet (``docs/adr/0184``).

**A seeded administrator is an invitation somebody took up**
(``docs/adr/0029``): every one goes through ``InviteAdministrator``, the use case
the club website's *Send invitation* runs, and then through the way that person
would get in — ``SetInvitationPassword`` by the link for the new person, which
opens her account under the name the club typed, and ``AcceptInvitation`` in
the app for the player. So each has a stream, a row, a mail-queue email that
lands in the local inbox, and a credential in the table its link is checked
against. Nothing here opens a table.

**The one thing the seed supplies is the randomness a link is minted from**, as
it supplies the clock and a photograph's verdict: the new person's link is in
an email, and a seed reads no email — so the credential's secrets are drawn
through a stand-in that remembers what it drew, and the link the run sets the
password with is the one the email carries.

**The three are arranged for the screens the later tickets draw.**

- ``administrator-only@raketa.example`` — *Marta Wójcik* — is an account an
  invitation opened and nothing else: no nickname, no player name, no Adult
  attestation, no player profile. She signs in with the seed password and lands
  in the administrator area; the club website draws *Reset password* on her row.
- ``rated-in-every-sport`` — typed by the club as *Tomek Kowal* — already
  played, and accepted in the app. His row has no
  *Reset password*: his account also plays, and the players read his nickname.
- ``the-one-sport-player`` — *Ola Kamińska* to the club — has an invitation
  waiting, so signing in as them shows the invitation sheet on launch.

Each name here is **the club's, typed for an Administrator**
(``docs/adr/0199`` §4): the catalogue holds no player name.

**Re-running invites nobody twice.** An Administrator already at the club is
left exactly as the developer left it — reset, removed or accepted in a walk —
except the pending one, which is **resent once it has expired**: an invitation
that lapsed three days after the last run is not the fixture this layer
promises.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, final

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_account_holders,
    build_administrator_repository,
    build_club_account_repository,
    build_credential_secrets,
    build_domain_event_store,
    build_event_publisher,
    build_invitation_sender,
    build_one_time_credential_store,
    build_password_hasher,
    build_refresh_token_repository,
    build_token_service,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings
from app.kernel import Instant
from app.modules.administrators.application.club_administrators import (
    InviteAdministrator,
    ResendInvitation,
)
from app.modules.administrators.application.commands import (
    InviteAdministratorCommand,
    SetInvitationPasswordCommand,
)
from app.modules.administrators.application.invitations import (
    AcceptInvitation,
    SetInvitationPassword,
)
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorStanding,
)
from app.modules.auth.application.one_time_credentials import OneTimeCredentials
from app.modules.auth.application.sign_out_everywhere import SignOutEverywhere
from app.modules.auth.application.token_rotation import TokenRotator
from app.modules.auth.domain.ports import CredentialSecrets
from app.modules.administrators.domain.value_objects import Name
from app.modules.users.domain.value_objects import Email
from app.seeds.catalog import (
    RATED_IN_EVERY_SPORT,
    SEED_EMAIL_DOMAIN,
    SEED_PASSWORD,
    THE_ONE_SPORT_PLAYER,
    SeedAccount,
)
from app.seeds.clock import FixedClock
from app.seeds.clubs import SEED_CLUBS, SeedClub, desk_email

#: The club all three are named by: the one #509's official groups are at.
THE_CLUB: Final[SeedClub] = next(
    club for club in SEED_CLUBS if club.name == "Ogrody 33"
)

#: The administrator-only account, addressed on the reserved TLD like every
#: seeded account, and named as the club typed her.
ADMINISTRATOR_ONLY_EMAIL: Final = f"administrator-only@{SEED_EMAIL_DOMAIN}"
ADMINISTRATOR_ONLY_NAME: Final = "Marta Wójcik"

#: The player who also runs the club's groups, and the one still to answer.
PLAYER_AND_ADMINISTRATOR: Final[SeedAccount] = RATED_IN_EVERY_SPORT
PENDING: Final[SeedAccount] = THE_ONE_SPORT_PLAYER

#: What the club typed for each of them. **The Administrator's, never the
#: player's** (``docs/adr/0199`` §4): the seed holds no player name, so the club
#: types one here as a desk would — and *"… runs this group"* says it only for
#: an Administrator with no nickname yet.
PLAYER_AND_ADMINISTRATOR_NAME: Final = "Tomek Kowal"
PENDING_NAME: Final = "Ola Kamińska"

# Refused on import, through the domain's own value objects, as the clubs' are.
Email(ADMINISTRATOR_ONLY_EMAIL)
Name(ADMINISTRATOR_ONLY_NAME)
Name(PLAYER_AND_ADMINISTRATOR_NAME)
Name(PENDING_NAME)


@final
class _RememberedSecrets:
    """The credential mechanism's randomness, drawn from the real source and
    **remembered**, so the run holds the link the email it wrote carries."""

    def __init__(self, source: CredentialSecrets) -> None:
        self._source = source
        self.drawn: list[str] = []

    def mint(self) -> str:
        secret = self._source.mint()
        self.drawn.append(secret)
        return secret


@final
@dataclass(frozen=True, slots=True)
class SeededAdministrator:
    email: str
    name: str
    #: How they got in, as the report says it.
    way_in: str
    #: What this run did: ``invited``, ``resent`` or ``already there``.
    action: str
    standing: AdministratorStanding


@final
@dataclass(frozen=True, slots=True)
class SeededAdministrators:
    club: SeedClub
    administrators: tuple[SeededAdministrator, ...]


async def write_the_administrators(
    session_factory: async_sessionmaker[AsyncSession],
    *,
    settings: Settings,
    now: Instant,
) -> SeededAdministrators:
    """Invite the three and let each in the way they would get in.

    **After the accounts and the clubs**, which it reads: the player and the
    pending invitee are named accounts, and the club is one its desk signed up.
    """

    async with session_factory() as session:
        club_id = await _club_id(session, THE_CLUB)
        wiring = _Wiring(session, settings=settings, now=now)
        seeded = (
            await _administrator_only(wiring, club_id),
            await _player_and_administrator(wiring, club_id),
            await _pending(wiring, club_id),
        )
    return SeededAdministrators(club=THE_CLUB, administrators=seeded)


class _Wiring:
    """The use cases a request would get, over one session and a stopped
    clock — and the remembered secrets."""

    def __init__(self, session: AsyncSession, *, settings: Settings, now: Instant):
        self.now = now
        self.clock = FixedClock(at=now)
        self.secrets = _RememberedSecrets(build_credential_secrets())
        event_store = build_domain_event_store(session)
        events = build_event_publisher(session)
        hasher = build_password_hasher(settings)
        self.uow = build_unit_of_work(session)
        self.administrators = build_administrator_repository(
            session, event_store=event_store, events=events
        )
        self.accounts = build_account_holders(
            session, event_store=event_store, events=events
        )
        self.credentials = OneTimeCredentials(
            store=build_one_time_credential_store(session),
            secrets=self.secrets,
            hasher=hasher,
        )
        self.sender = build_invitation_sender(
            session, settings, accounts=self.accounts, credentials=self.credentials
        )
        tokens = build_refresh_token_repository(session)
        self.sign_out_everywhere = SignOutEverywhere(tokens=tokens, events=events)
        self.rotator = TokenRotator(
            tokens=tokens,
            jwt=build_token_service(settings, clock=self.clock),
            hasher=hasher,
            uow=self.uow,
            clock=self.clock,
            events=events,
        )
        self.hasher = hasher
        self.users = build_user_repository(session)

    def invite(self) -> InviteAdministrator:
        return InviteAdministrator(
            administrators=self.administrators,
            accounts=self.accounts,
            sender=self.sender,
            uow=self.uow,
            clock=self.clock,
        )


async def _administrator_only(wiring: _Wiring, club_id) -> SeededAdministrator:
    email = Email(ADMINISTRATOR_ONLY_EMAIL)
    found = await wiring.administrators.at_club(club_id, email)
    action = "already there"
    if found is None:
        await wiring.invite().execute(
            InviteAdministratorCommand(
                club_id=club_id, name=ADMINISTRATOR_ONLY_NAME, email=email.value
            )
        )
        (token,) = wiring.secrets.drawn[-1:]
        await SetInvitationPassword(
            credentials=wiring.credentials,
            administrators=wiring.administrators,
            accounts=wiring.accounts,
            sign_out_everywhere=wiring.sign_out_everywhere,
            hasher=wiring.hasher,
            rotator=wiring.rotator,
            clock=wiring.clock,
        ).execute(SetInvitationPasswordCommand(password=SEED_PASSWORD, token=token))
        action = "invited"
    return await _seeded(
        wiring,
        club_id,
        email=email,
        name=ADMINISTRATOR_ONLY_NAME,
        way_in="set a password by the invitation's link",
        action=action,
    )


async def _player_and_administrator(wiring: _Wiring, club_id) -> SeededAdministrator:
    account = PLAYER_AND_ADMINISTRATOR
    email = Email(account.email)
    found = await wiring.administrators.at_club(club_id, email)
    action = "already there"
    if found is None:
        user = await wiring.users.get_by_email(email.value)
        if user is None:
            raise RuntimeError(
                f"{account.slug} is not registered — the accounts layer runs first"
            )
        row = await wiring.invite().execute(
            InviteAdministratorCommand(
                club_id=club_id, name=PLAYER_AND_ADMINISTRATOR_NAME, email=email.value
            )
        )
        await AcceptInvitation(
            administrators=wiring.administrators,
            sender=wiring.sender,
            uow=wiring.uow,
            clock=wiring.clock,
        ).execute(account_id=user.id, email=email, administrator_id=row.id)
        action = "invited"
    return await _seeded(
        wiring,
        club_id,
        email=email,
        name=PLAYER_AND_ADMINISTRATOR_NAME,
        way_in="already played, and accepted in the app",
        action=action,
    )


async def _pending(wiring: _Wiring, club_id) -> SeededAdministrator:
    account = PENDING
    email = Email(account.email)
    found = await wiring.administrators.at_club(club_id, email)
    if found is None:
        await wiring.invite().execute(
            InviteAdministratorCommand(
                club_id=club_id, name=PENDING_NAME, email=email.value
            )
        )
        action = "invited"
    elif found.standing(now=wiring.now) is AdministratorStanding.EXPIRED:
        await ResendInvitation(
            administrators=wiring.administrators,
            accounts=wiring.accounts,
            sender=wiring.sender,
            uow=wiring.uow,
            clock=wiring.clock,
        ).execute(club_id=club_id, administrator_id=found.id)
        action = "resent"
    else:
        action = "already there"
    return await _seeded(
        wiring,
        club_id,
        email=email,
        name=PENDING_NAME,
        way_in="has not answered: the invitation sheet shows on launch",
        action=action,
    )


async def _seeded(
    wiring: _Wiring, club_id, *, email: Email, name: str, way_in: str, action: str
) -> SeededAdministrator:
    administrator: Administrator | None = await wiring.administrators.at_club(
        club_id, email
    )
    if administrator is None:
        raise RuntimeError(f"{email.value} was invited and has no Administrator")
    return SeededAdministrator(
        email=email.value,
        name=name,
        way_in=way_in,
        action=action,
        standing=administrator.standing(now=wiring.now),
    )


async def _club_id(session: AsyncSession, club: SeedClub):
    """The club its desk signed up, found by the desk's address."""

    accounts = build_club_account_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    account = await accounts.get_by_email(Email(desk_email(club)))
    if account is None:
        raise RuntimeError(
            f"{club.name} has not signed up — the clubs layer runs first"
        )
    return account.club_id


def administrator_lines(seeded: SeededAdministrators) -> list[str]:
    """The report's section: who runs the club's groups, and how they got in."""

    lines = [
        f"Administrators — {len(seeded.administrators)} named by "
        f"{seeded.club.name} ({desk_email(seeded.club)}); each signs in with the "
        f"seed password:"
    ]
    for entry in seeded.administrators:
        lines.append(
            f"  {entry.name} · {entry.email} · {entry.standing.value.lower()} · "
            f"{entry.way_in} · {entry.action}"
        )
    return lines

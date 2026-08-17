"""Execute the catalog through the use cases, and report what it did.

Every write here goes through a use case assembled from
``app.bootstrap.composition``. Nothing in this module opens a table. That is what
makes a seeded aggregate a real one: the event stream, the outbox row and the
projection are written by the same code a request writes them with, in the same
transaction, so a seeded assessment replays exactly as a played one does.

**Re-running leaves the same state rather than duplicating or failing.** The two
steps get there differently, and the difference is worth knowing:

- Registration is a read before a write. ``RegisterUser`` refuses a second
  registration for an address (``EmailAlreadyRegistered``), so the account is
  looked up through the user repository first and the registration is skipped
  when it is there. Two seed runs *racing* each other would still lose one to
  the unique constraint — which is the right outcome for a developer command,
  and not a case worth writing code for.
- Starting an assessment needs nothing here at all: ``CreateAssessment`` is
  already idempotent per player and sport, and hands back the open run.

**A seeded account's id is not fixed, its address is.** ``RegisterUser`` mints
the user id itself, which is right — an id chosen by a caller is an id the write
path does not own — so re-seeding a *fresh* database yields a different uuid.
Everything downstream is derived from it, so the run and the rating that follow
the account are stable relative to it. What is promised, and what a developer
signs in with, is the address.

The events this writes land on the outbox and are delivered by the API's worker
the next time it polls, exactly as a request's are. Seeding does not deliver
them itself: a seed run is not an event-delivery worker, and having two would be
two things that can disagree about what has been delivered.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_assessment_engine,
    build_assessment_repository,
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_password_hasher,
    build_skill_rating_repository,
    build_unit_of_work,
    build_user_repository,
)
from app.core.config import Settings, get_settings
from app.infrastructure.database.engine import create_engine
from app.modules.rating.application.commands import CreateAssessmentCommand
from app.modules.rating.application.create_assessment import CreateAssessment
from app.modules.rating.domain.ids import PlayerId
from app.modules.users.application.commands import RegisterUserCommand
from app.modules.users.application.register_user import RegisterUser
from app.seeds.catalog import ACCOUNTS, SEED_PASSWORD, SeedAccount
from app.seeds.guard import refuse_unless_seedable


@dataclass(frozen=True)
class SeededAccount:
    """What one account is, after the run — and what this run had to create.

    The two flags are about *this run*, not about the account, which is why they
    are here and not on ``SeedAccount``. They are what makes a second run
    legible: an account that reports neither is one the seed found already in
    the state it wanted.
    """

    account: SeedAccount
    player_id: UUID
    assessment_id: UUID
    registered: bool
    assessment_started: bool

    @property
    def already_present(self) -> bool:
        return not (self.registered or self.assessment_started)


async def seed(session: AsyncSession) -> tuple[SeededAccount, ...]:
    """Bring every account in the catalog into the state it names.

    Takes a session rather than opening one, so the API test suite can drive
    this against its own fixture database instead of standing up a second one.
    ``run`` below is what opens a session for a real command.
    """

    return tuple([await _seed_account(session, account) for account in ACCOUNTS])


async def _seed_account(session: AsyncSession, account: SeedAccount) -> SeededAccount:
    player_id, registered = await _ensure_registered(session, account)
    assessment_id, started = await _ensure_assessment_open(
        session, player_id, account
    )
    return SeededAccount(
        account=account,
        player_id=player_id,
        assessment_id=assessment_id,
        registered=registered,
        assessment_started=started,
    )


async def _ensure_registered(
    session: AsyncSession, account: SeedAccount
) -> tuple[UUID, bool]:
    users = build_user_repository(session)

    existing = await users.get_by_email(account.email)
    if existing is not None:
        return existing.id, False

    register = RegisterUser(
        users=users,
        event_store=build_domain_event_store(session),
        hasher=build_password_hasher(),
        uow=build_unit_of_work(session),
        clock=build_clock(),
        events=build_event_publisher(session),
    )
    user = await register.execute(
        RegisterUserCommand(
            email=account.email,
            nickname=account.nickname,
            password=SEED_PASSWORD,
        )
    )
    return user.id, True


async def _ensure_assessment_open(
    session: AsyncSession, player_id: UUID, account: SeedAccount
) -> tuple[UUID, bool]:
    # The store and the publisher are built once and handed to both
    # repositories, which is what a caller outside a request has to do
    # deliberately — under FastAPI the sharing comes free from per-request
    # dependency caching.
    event_store = build_domain_event_store(session)
    events = build_event_publisher(session)

    create = CreateAssessment(
        engine=build_assessment_engine(),
        assessments=build_assessment_repository(event_store=event_store, events=events),
        ratings=build_skill_rating_repository(event_store=event_store, events=events),
        uow=build_unit_of_work(session),
        clock=build_clock(),
    )
    start = await create.execute(
        CreateAssessmentCommand(
            player_id=PlayerId(player_id),
            sport=account.sport,
        )
    )
    return start.step.assessment_id, start.created


async def run(settings: Settings | None = None) -> tuple[SeededAccount, ...]:
    """Open a connection of this command's own, seed, and close it.

    The guard is re-checked against the settings actually used. Importing this
    package already checked the process's, and this is the same question asked of
    the object that decides which database is about to be written to — a caller
    that constructs its own settings does not get to skip it.

    The engine is created and disposed here rather than taken from
    ``init_engine``: a seed run is not the API process, and an engine it owns
    outright is one it can close on the way out.
    """

    settings = settings or get_settings()
    refuse_unless_seedable(settings)

    engine = create_engine(settings)
    try:
        session_factory = async_sessionmaker(
            engine, expire_on_commit=False, autoflush=False
        )
        async with session_factory() as session:
            return await seed(session)
    finally:
        await engine.dispose()


def report(seeded: tuple[SeededAccount, ...]) -> list[str]:
    """The run, as lines a developer reads — address, password, state, id."""

    lines = [
        f"Seeded {len(seeded)} account(s). Password for all of them: "
        f"{SEED_PASSWORD}",
        "",
    ]
    for entry in seeded:
        state = "already present" if entry.already_present else "created"
        lines.append(f"  {entry.account.email}  [{state}]")
        lines.append(f"      {entry.account.description}")
        lines.append(
            f"      player {entry.player_id} · "
            f"{entry.account.sport.value} assessment {entry.assessment_id}"
        )
    return lines

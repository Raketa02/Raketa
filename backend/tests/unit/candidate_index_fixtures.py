"""A log to tail, and the machinery to tail it. Shared by three test modules.

The tail reader, the snapshot source and ``rebuild == tail`` all need the same
two things — a way to append a real event to a real ``event_store``, and a reader
wired the way the composition root wires one. Written once here, because three
copies of *how an event gets into the log* is three places for a test to be
testing a fixture rather than the projection.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.events import build_event_runtime
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Instant
from app.core.config import get_settings
from app.modules.matchmaking.infrastructure.candidate_index_tail import (
    CandidateIndexTail,
)
from app.modules.matchmaking.infrastructure.snapshot_horizon import NoSnapshotHorizon
from app.modules.auth.domain.events import RefreshTokenIssued, RefreshTokenRotated
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    GenderChanged,
    GenderPreferenceChanged,
    IntroChanged,
    IntroWritten,
    LocationChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.rating.domain.events import RatingInitialised
from app.shared.domain import DomainEvent

START = datetime(2026, 8, 27, 9, 0, tzinfo=timezone.utc)


class TickingClock:
    """A clock that moves a second per read, so two ticks are distinguishable."""

    def __init__(self, start: datetime = START) -> None:
        self._now = start

    def now(self) -> Instant:
        self._now = self._now + timedelta(seconds=1)
        return Instant(self._now)


def build_tail(
    *, clock: TickingClock | None = None, batch_size: int | None = None
) -> CandidateIndexTail:
    """A reader wired as the composition root wires one, minus the session.

    ``batch_size`` is a parameter here because **the schedule is the variable**
    the ``rebuild == tail`` property is stated over: a rebuild differs from a tail
    only in how much of the log it swallows per pass.
    """

    runtime = build_event_runtime()
    return CandidateIndexTail(
        codec=runtime.codec,
        catalog=runtime.catalog,
        horizon=NoSnapshotHorizon(),
        clock=clock or TickingClock(),
        batch_size=(
            batch_size
            if batch_size is not None
            else get_settings().CANDIDATE_INDEX_BATCH_SIZE
        ),
    )


async def append(
    session_factory: async_sessionmaker[AsyncSession],
    event: DomainEvent,
    *,
    aggregate_type: str = "PlayerProfile",
    aggregate_id: UUID | None = None,
    sequence_no: int | None = None,
    version: int = 1,
) -> int:
    """Put one event in the log and answer the position it took.

    ``sequence_no`` is settable so a test can leave a **hole**, which is the one
    thing the log's own identity column will never do on request. ``version`` is
    settable so a second event can land on the **same** stream — the store keys
    ``(aggregate, version)`` unique, so two events filed under one id at
    version 1 are a constraint violation and not a stream.
    """

    runtime = build_event_runtime()
    encoded = runtime.codec.encode(event)
    async with session_factory() as session:
        async with session.begin():
            row = EventStoreORM(
                id=uuid4(),
                aggregate_type=aggregate_type,
                aggregate_id=aggregate_id or uuid4(),
                version=version,
                event_type=encoded.event_type,
                schema_version=encoded.schema_version,
                payload=encoded.payload,
                occurred_at=event.occurred_at,
                created_at=event.occurred_at,
            )
            if sequence_no is not None:
                row.sequence_no = sequence_no
            session.add(row)
        return row.sequence_no


def profile_created(player_id: UUID, *, at: datetime = START) -> PlayerProfileCreated:
    return PlayerProfileCreated(
        player_id=player_id,
        social_tags=("competitive_edge",),
        photo_ids=("a-photo",),
        availability=("1:MORNING",),
        latitude=52.23,
        longitude=21.01,
        search_radius_km=12,
        idempotency_key=f"key-{player_id}",
        occurred_at=at,
        gender="FEMALE",
        gender_preference="ANY",
    )


def opt_in(player_id: UUID, *, at: datetime = START) -> ProposalsOptInAnswered:
    return ProposalsOptInAnswered(player_id, True, "v1", "ONBOARDING", at)


def rating_initialised(
    player_id: UUID, *, sport: str = "PADEL", at: datetime = START
) -> RatingInitialised:
    return RatingInitialised(
        rating_id=uuid4(),
        player_id=player_id,
        sport=sport,
        mu=2.71,
        sigma=0.34,
        confidence=62,
        range_low=2.4,
        range_high=3.0,
        band_name="Improver",
        band_lower=2.5,
        band_upper=3.0,
        status="INITIAL_ESTIMATE",
        engine_version="v3",
        source_assessment_id=uuid4(),
        occurred_at=at,
    )


def intent_declared(
    player_id: UUID, *, sport: str = "PADEL", intent: str = "COMPETITIVE"
) -> PlayIntentDeclared:
    return PlayIntentDeclared(player_id, sport, intent, "ONBOARDING", START)


#: One instance of **every** contract the index projects.
#:
#: A list rather than a fixture per test, because two things walk it: the
#: schema check that every column a movement names exists, and any future check
#: that wants to drive the whole vocabulary through the fold at once. It is kept
#: honest by ``PROJECTED_CONTRACTS`` — a contract added there with no instance
#: here would leave that column unwalked.
_SOMEBODY = UUID("11111111-1111-1111-1111-111111111111")

ONE_OF_EACH_PROJECTED_CONTRACT: tuple[DomainEvent, ...] = (
    profile_created(_SOMEBODY),
    SocialTagsChanged(_SOMEBODY, ("social_first",), START),
    AvailabilityChanged(_SOMEBODY, ("3:EVENING",), START),
    LocationChanged(_SOMEBODY, 52.23, 21.01, START),
    SearchRadiusChanged(_SOMEBODY, 25, START),
    GenderChanged(_SOMEBODY, "NON_BINARY", START),
    GenderPreferenceChanged(_SOMEBODY, "SAME_GENDER_ONLY", START),
    IntroWritten(_SOMEBODY, "Moved from Wrocław in May.", START),
    IntroChanged(_SOMEBODY, "Will travel for a hard game.", START),
    opt_in(_SOMEBODY),
    rating_initialised(_SOMEBODY),
    intent_declared(_SOMEBODY),
    RefreshTokenIssued(_SOMEBODY, _SOMEBODY, "jti", START, START, "player_app"),
    RefreshTokenRotated(
        _SOMEBODY, _SOMEBODY, "old", _SOMEBODY, "new", START, "player_app"
    ),
)

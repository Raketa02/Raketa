"""The register of what ``player_record`` asks for, and who answers it.

**The fifth register, and the second of the *consumer* kind.**
``matcher_demands.py`` holds the ports the matcher declares of contexts it does
not write; ``games_demands.py``, ``rating_demands.py`` and
``player_score_demands.py`` each hold what one **provider** publishes outward.
This one is the matcher's kind: a context that writes nothing and asks four
questions of five others. Rows of the two kinds in one list would make every
exhaustiveness assertion a claim about something else, and the first person to
add a row would have to guess which.

**One port here has three implementations, and that is the shape rather than an
accident.** ``PriorDisclosure`` is *where has this reader already been shown this
person*, and the platform answers it in three places — a search of theirs
returned them, they are both seated in a live challenge, they were on a court
together. A fourth surface that introduces one player to another satisfies the
same demand with a fourth row, and this context never learns what it is. The
suite runs **each** of them against the demand, which is what makes *no adapter
signs half a contract* true of a port with more than one signatory.

**A row carries a builder over a session**, not an instance, so the suite cannot
quietly excuse the implementations with a database behind them — which here is
four of the six.

**A port with nothing registered is a red build**, asserted against
``PLAYER_RECORD_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.bootstrap.composition import (
    build_account_hold_query,
    build_account_status_query,
    build_block_query,
    build_candidate_source,
    build_challenge_disclosure,
    build_domain_event_store,
    build_event_publisher,
    build_game_disclosure,
    build_photo_storage,
    build_player_profile_repository,
    build_record_gates,
    build_record_photo_link,
    build_search_disclosure,
    build_subject_identity_source,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.matchmaking.application.fail_closed_gates import FailClosedGates
from app.modules.player_record.domain.ports import (
    PLAYER_RECORD_DEMANDS,
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    SubjectIdentitySource,
)


def _identity_source(session: AsyncSession) -> SubjectIdentitySource:
    """The identity source, over the object store this process is configured for.

    The store is read from settings here rather than taken as an argument,
    because a register row is a builder over a session and nothing else — the
    same reason every other row in every other register looks the way it does.
    Constructing it opens no connection, and the demand run against this row is
    about a player with no photograph, so nothing in the suite reaches a bucket.
    """

    return build_subject_identity_source(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
        storage=build_photo_storage(get_settings()),
    )


def _photo_link(session: AsyncSession) -> RecordPhotoLink:
    """The photo link, which needs no session and takes one anyway.

    Signing is a signature over a request that is never sent, so this row runs
    with no object store up — which is the acceptance criterion for every suite
    in this repository, not a convenience.
    """

    settings = get_settings()
    return build_record_photo_link(
        storage=build_photo_storage(settings), settings=settings
    )


def _record_gates(session: AsyncSession) -> RecordGates:
    """The four fail-closed gates and the reader's hold, over an empty index.

    **The candidate source is the process's and not the request's**
    (``docs/adr/0112``), and a register row holds only a session — so this one
    takes the process-level builder and never refreshes what it hands back, which
    is a source answering an empty container for every partition. That is exactly
    the state the demand about this port is written around: *a subject with no row
    in the partition asked about is not admitted*, because a gate that cannot be
    evaluated excludes. The factory handed to it is unbound deliberately — a demand
    that refreshed this index would fail loudly here rather than quietly testing
    something else.
    """

    return build_record_gates(
        gates=FailClosedGates(
            profiles=build_player_profile_repository(
                event_store=build_domain_event_store(session),
                events=build_event_publisher(session),
            ),
            candidates=build_candidate_source(
                session_factory=async_sessionmaker()
            ),
            blocks=build_block_query(session),
            holds=build_account_hold_query(session),
            account_status=build_account_status_query(session),
        ),
        holds=build_account_hold_query(session),
    )


PLAYER_RECORD_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=SubjectIdentitySource,
        name="ProfileAndAccountIdentity",
        build=_identity_source,
    ),
    RegisteredImplementation(
        port=RecordPhotoLink,
        name="PresignedRecordPhoto",
        build=_photo_link,
    ),
    RegisteredImplementation(
        port=PriorDisclosure,
        name="SearchesThatShowedThem",
        build=build_search_disclosure,
    ),
    RegisteredImplementation(
        port=PriorDisclosure,
        name="ChallengesTheyShare",
        build=build_challenge_disclosure,
    ),
    RegisteredImplementation(
        port=PriorDisclosure,
        name="GamesTheyPlayed",
        build=build_game_disclosure,
    ),
    RegisteredImplementation(
        port=RecordGates,
        name="LiveRecordGates",
        build=_record_gates,
    ),
)


P = TypeVar("P")


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PLAYER_RECORD_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PLAYER_RECORD_DEMANDS",
    "PLAYER_RECORD_IMPLEMENTATIONS",
    "implementations_of",
]

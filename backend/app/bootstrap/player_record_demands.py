"""The register of what ``player_record`` asks for, and who answers it.

**The fifth register, and the second of the *consumer* kind.**
``matcher_demands.py`` holds the ports the matcher declares of contexts it does
not write; ``games_demands.py``, ``rating_demands.py`` and
``player_score_demands.py`` each hold what one **provider** publishes outward.
This one is the matcher's kind: a context that writes nothing and asks ten
questions of eight others. Rows of the two kinds in one list would make every
exhaustiveness assertion a claim about something else, and the first person to
add a row would have to guess which.

**One port here has three implementations, and that is the shape rather than an
accident.** ``PriorDisclosure`` is *has this reader already been shown this
person*, and the platform answers it in three places — they were on a court
together, they are both in a group, the reader runs a group the subject is in
(#575). The suite runs **each** of them against the demand, which is what makes
*no adapter signs half a contract* true of a port with more than one signatory.

**A row carries a builder over a session**, not an instance, so the suite cannot
quietly excuse the implementations with a database behind them — which here is
every row but one. The exception is the photo link, which signs a request that is
never sent and takes a session it does not use, so that a register row stays *a
builder over a session* and nothing else.

**A port with nothing registered is a red build**, asserted against
``PLAYER_RECORD_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.composition import (
    build_subject_form,
    build_subject_ratings,
    build_account_gates,
    build_account_hold_query,
    build_account_status_query,
    build_block_query,
    build_blocks_by_the_reader,
    build_domain_event_store,
    build_event_publisher,
    build_game_disclosure,
    build_group_disclosure,
    build_photo_storage,
    build_record_gates,
    build_record_photo_link,
    build_reliability_filters,
    build_runner_disclosure,
    build_subject_identity_source,
    build_subject_reliability,
    build_subject_sportsmanship,
    build_subject_variety,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.player_record.domain.ports import (
    PLAYER_RECORD_DEMANDS,
    BlocksByTheReader,
    PriorDisclosure,
    RecordGates,
    RecordPhotoLink,
    ReliabilityFilters,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
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
    """The two gates about accounts and the reader's hold, over a session."""

    holds = build_account_hold_query(session)
    return build_record_gates(
        accounts=build_account_gates(
            holds=holds, account_status=build_account_status_query(session)
        ),
        holds=holds,
    )


def _own_blocks(session: AsyncSession) -> BlocksByTheReader:
    """The reader's own block, over the one ``BlockQuery`` a session reads."""

    return build_blocks_by_the_reader(build_block_query(session))


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
        name="GamesTheyPlayed",
        build=build_game_disclosure,
    ),
    RegisteredImplementation(
        port=PriorDisclosure,
        name="GroupsTheyShare",
        build=build_group_disclosure,
    ),
    RegisteredImplementation(
        port=PriorDisclosure,
        name="GroupsTheReaderRuns",
        build=build_runner_disclosure,
    ),
    RegisteredImplementation(
        port=RecordGates,
        name="LiveRecordGates",
        build=_record_gates,
    ),
    RegisteredImplementation(
        port=BlocksByTheReader,
        name="OwnBlocksOfTheReader",
        build=_own_blocks,
    ),
    RegisteredImplementation(
        port=SubjectRatings,
        name="RatingSubjectRatings",
        build=build_subject_ratings,
    ),
    RegisteredImplementation(
        port=SubjectForm,
        name="GamesSubjectForm",
        build=build_subject_form,
    ),
    RegisteredImplementation(
        port=SubjectReliability,
        name="ScoreSubjectReliability",
        build=build_subject_reliability,
    ),
    RegisteredImplementation(
        port=ReliabilityFilters,
        name="FiltersInTheGroups",
        build=build_reliability_filters,
    ),
    RegisteredImplementation(
        port=SubjectVariety,
        name="GamesSubjectVariety",
        build=build_subject_variety,
    ),
    RegisteredImplementation(
        port=SubjectSportsmanship,
        name="PublishedSubjectSportsmanship",
        build=build_subject_sportsmanship,
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

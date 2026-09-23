"""Request-scoped declarations for the player record.

*When* each adapter is built and how long it lives, never *what* — every concrete
class comes from ``app.bootstrap.composition``, and
``tests/unit/test_composition_root.py`` fails this file if it imports one.

**The two use cases are declared apart, and the difference is the point.**
``ReadOwnRecord`` names no gate machinery at all, so the route for your own sheet
does not depend on the candidate index being loaded in this process — the gates
bind it once per evaluation and refuse the whole read when there is none, which
is right for a sheet about a stranger and absurd for the one screen that tells a
player how they appear. A single factory with a branch inside it would have made
that a runtime accident instead of a wiring decision.

**The four fail-closed gates are taken from ``matchmaking``'s own declaration**
rather than assembled again here. That factory is where every surface showing one
player to another gets them, and a surface deciding for itself where a gate comes
from is how one of them ends up wired to a different answer.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import (
    ClockDep,
    DbSession,
    DomainEventStoreDep,
    EventPublisherDep,
    SettingsDep,
)
from app.bootstrap.composition import (
    build_challenge_disclosure,
    build_game_disclosure,
    build_record_gates,
    build_record_photo_link,
    build_search_disclosure,
    build_subject_form,
    build_subject_identity_source,
    build_subject_ratings,
    build_subject_reliability,
    build_subject_sportsmanship,
    build_subject_variety,
)
from app.modules.matchmaking.presentation.dependencies import (
    AccountHoldQueryDep,
    FailClosedGatesDep,
)
from app.modules.player_profile.presentation.dependencies import PhotoStorageDep
from app.modules.player_record.application.admission import RecordAdmission
from app.modules.player_record.application.read_player_record import (
    ReadOwnRecord,
    ReadPlayerRecord,
)
from app.modules.player_record.domain.ports import (
    RecordPhotoLink,
    SubjectForm,
    SubjectIdentitySource,
    SubjectRatings,
    SubjectReliability,
    SubjectSportsmanship,
    SubjectVariety,
)


def get_subject_identity_source(
    db: DbSession,
    event_store: DomainEventStoreDep,
    events: EventPublisherDep,
    storage: PhotoStorageDep,
) -> SubjectIdentitySource:
    return build_subject_identity_source(
        session=db, event_store=event_store, events=events, storage=storage
    )


SubjectIdentitySourceDep = Annotated[
    SubjectIdentitySource, Depends(get_subject_identity_source)
]


def get_record_photo_link(
    storage: PhotoStorageDep, settings: SettingsDep
) -> RecordPhotoLink:
    return build_record_photo_link(storage=storage, settings=settings)


RecordPhotoLinkDep = Annotated[RecordPhotoLink, Depends(get_record_photo_link)]


def get_subject_ratings(db: DbSession) -> SubjectRatings:
    return build_subject_ratings(db)


SubjectRatingsDep = Annotated[SubjectRatings, Depends(get_subject_ratings)]


def get_subject_form(db: DbSession) -> SubjectForm:
    return build_subject_form(db)


SubjectFormDep = Annotated[SubjectForm, Depends(get_subject_form)]


def get_subject_reliability(db: DbSession) -> SubjectReliability:
    return build_subject_reliability(db)


SubjectReliabilityDep = Annotated[
    SubjectReliability, Depends(get_subject_reliability)
]


def get_subject_variety(db: DbSession) -> SubjectVariety:
    return build_subject_variety(db)


SubjectVarietyDep = Annotated[SubjectVariety, Depends(get_subject_variety)]


def get_subject_sportsmanship(db: DbSession) -> SubjectSportsmanship:
    """What other players said. **One adapter, and it serves both routes.**

    Both use cases below take the same collaborator and put it the same one
    question, whoever is reading (``docs/adr/0179`` §5). Two adapters here would
    be two answers to *whose sheet is this*, and the one the wiring gave would
    win over the one the record states.
    """

    return build_subject_sportsmanship(db)


SubjectSportsmanshipDep = Annotated[
    SubjectSportsmanship, Depends(get_subject_sportsmanship)
]


def get_record_admission(
    db: DbSession,
    gates: FailClosedGatesDep,
    holds: AccountHoldQueryDep,
) -> RecordAdmission:
    """The three strands and the four gates, assembled per request.

    The strands are listed **cheapest first**, which is the order they are read
    in: a search record is one indexed query, and the two directories fold
    streams. It changes no answer — the partitions are unioned before any gate
    runs — and it is what a reader who arrived from the shortlist pays.
    """

    return RecordAdmission(
        disclosures=(
            build_search_disclosure(db),
            build_challenge_disclosure(db),
            build_game_disclosure(db),
        ),
        gates=build_record_gates(gates=gates, holds=holds),
    )


RecordAdmissionDep = Annotated[RecordAdmission, Depends(get_record_admission)]


def get_read_player_record(
    admission: RecordAdmissionDep,
    identities: SubjectIdentitySourceDep,
    photos: RecordPhotoLinkDep,
    ratings: SubjectRatingsDep,
    form: SubjectFormDep,
    reliability: SubjectReliabilityDep,
    variety: SubjectVarietyDep,
    sportsmanship: SubjectSportsmanshipDep,
    clock: ClockDep,
) -> ReadPlayerRecord:
    return ReadPlayerRecord(
        admission=admission,
        identities=identities,
        photos=photos,
        ratings=ratings,
        form=form,
        reliability=reliability,
        variety=variety,
        sportsmanship=sportsmanship,
        clock=clock,
    )


ReadPlayerRecordDep = Annotated[ReadPlayerRecord, Depends(get_read_player_record)]


def get_read_own_record(
    identities: SubjectIdentitySourceDep,
    photos: RecordPhotoLinkDep,
    ratings: SubjectRatingsDep,
    form: SubjectFormDep,
    reliability: SubjectReliabilityDep,
    variety: SubjectVarietyDep,
    sportsmanship: SubjectSportsmanshipDep,
    clock: ClockDep,
) -> ReadOwnRecord:
    """Your own record — **and still not one of these is a gate.**

    Six readers and a clock now, and the property that matters is unchanged:
    nothing here binds the candidate index, so the one screen that tells a player
    how they appear cannot be taken down by the machinery that gates somebody
    else's sheet. The reliability read is the one that makes that worth the
    wiring: the pill is the number deciding who this player is offered to, and a
    penalty nobody can look up is a penalty nobody can fix.

    **The sportsmanship reader is the same object the other route gets**, and
    it is put the same question: the figure and its count cross to the subject
    as to anybody (``docs/adr/0179`` §5), so there is nothing narrower for this
    route to ask.
    """

    return ReadOwnRecord(
        identities=identities,
        photos=photos,
        ratings=ratings,
        form=form,
        reliability=reliability,
        variety=variety,
        sportsmanship=sportsmanship,
        clock=clock,
    )


ReadOwnRecordDep = Annotated[ReadOwnRecord, Depends(get_read_own_record)]

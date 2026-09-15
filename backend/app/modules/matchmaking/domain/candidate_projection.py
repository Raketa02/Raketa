"""One stored event in, what it moves in the candidate index out.

**A pure function of the event alone**, and that is the whole reason
``rebuild == tail`` is a property rather than a hope (``docs/adr/0110``). Every
contract the index reads carries its *whole new value* — a tag list, a grid, an
area, a Level — never a delta, so nothing here has to read the row it is about to
move. A projection that needed the prior row would be one whose answer depended
on the order two readers happened to run in, and replaying the log from zero
would be a different computation from tailing it.

**Two shapes move, because two things are keyed differently.** The facts a player
changes about themselves are about *the player* — tags, grid, area, radius,
gender, the session refresh — and the facts a search reads are about
``(player, sport)`` — the Level, the Play intent. Denormalising the first onto the
second would mean a profile edit had to know which sports the player is rated in,
which is a fact this fold is deliberately not allowed to look up.

**The list of what is consumed is data** (``PROJECTED_CONTRACTS``) rather than
something a reader has to collect by scanning the dispatch below, so *a contract
the index reads that nothing here projects* is a question a test can ask. That
failure arrives by omission — a column that silently stops moving — which is
exactly the kind nobody notices.

**What is absent is absent on purpose.** ``player_profile.photos_changed`` is not
here: the player card is assembled outside the engine (``docs/adr/0107``), so no
photo fact reaches the index at all. ``player_profile.intro_written`` **is**
here, and it is the one text fact the index holds: a line a player wrote about
themselves, projected like the tags so the card is assembled from the row
(``docs/adr/0170`` §3), and read by nothing in the scorer — ``fence.py`` copies
it onto no ``ScorableCandidate``, and the scorer's own fence refuses the word.
``users`` is not here either: account state is not a fact a player changes about
themselves — an administrator may change it — and a stale *active* column would
make staleness cost **safety**, which is the one thing ``docs/adr/0111``'s
invariant exists to prevent. Gate 8 reads it live (``docs/adr/0124``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Type, final
from uuid import UUID

from app.modules.auth.domain.events import RefreshTokenIssued, RefreshTokenRotated
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    GenderChanged,
    GenderPreferenceChanged,
    IntroWritten,
    LocationChanged,
    PlayerProfileCreated,
    PlayIntentDeclared,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.rating.domain.events import RatingInitialised
from app.shared.domain import DomainEvent


@final
@dataclass(frozen=True, slots=True)
class PlayerFactsMoved:
    """What one event changed about a player, whatever sports they play.

    ``changes`` is a *partial* record — only the fields the event carries — so an
    event that says nothing about an area leaves the area alone. That is what
    makes each contract's row in the spec's table readable off the dispatch below
    rather than off a constructor with twelve arguments, eleven of them repeating
    what was already there.
    """

    player_id: UUID
    changes: Mapping[str, object]


@final
@dataclass(frozen=True, slots=True)
class CandidateRowMoved:
    """What one event changed about a ``(player, sport)`` pair.

    The sport is the machine code the event already carries. It is never a set
    and never *all sports*: a Level and a Play intent are declared per sport, and
    that is what makes *neither transfers between sports* structural.
    """

    player_id: UUID
    sport: str
    changes: Mapping[str, object]


#: What one event moved. Two variants and never a third — a movement that
#: belonged to neither key would be a fact with no home in the index.
Movement = PlayerFactsMoved | CandidateRowMoved


def project(event: DomainEvent) -> tuple[Movement, ...]:
    """What this event moves in the index. Empty for a contract it does not read.

    Empty rather than an error, because the tail reader walks *the whole log* and
    most of it is somebody else's. A contract this projection is supposed to read
    going missing is caught by ``PROJECTED_CONTRACTS`` below, not by raising here
    on every rating question ever asked.
    """

    match event:
        case PlayerProfileCreated():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={
                        # The newcomer window is clocked from here — the last
                        # step of onboarding and the moment a player becomes
                        # searchable. A date, never a flag: a stored
                        # `is_newcomer` boolean goes stale hourly and a date
                        # never does (`the-newcomer-path.md` §1).
                        "profile_created_at": event.occurred_at,
                        "social_tags": event.social_tags,
                        "tags_updated_at": event.occurred_at,
                        "availability": event.availability,
                        "grid_updated_at": event.occurred_at,
                        **_area(event.latitude, event.longitude),
                        "search_radius_km": event.search_radius_km,
                        # `None` is *nobody was asked*, and it travels as
                        # itself. Backfilling it to `PREFER_NOT_TO_SAY` would
                        # invent the one thing a self-declaration must never be.
                        "gender": event.gender,
                        "gender_preference": event.gender_preference,
                    },
                ),
            )
        case SocialTagsChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={
                        "social_tags": event.social_tags,
                        "tags_updated_at": event.occurred_at,
                    },
                ),
            )
        case AvailabilityChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={
                        "availability": event.availability,
                        "grid_updated_at": event.occurred_at,
                    },
                ),
            )
        case LocationChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes=_area(event.latitude, event.longitude),
                ),
            )
        case SearchRadiusChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={"search_radius_km": event.search_radius_km},
                ),
            )
        case GenderChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id, changes={"gender": event.gender}
                ),
            )
        case GenderPreferenceChanged():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={"gender_preference": event.gender_preference},
                ),
            )
        case ProposalsOptInAnswered():
            return (
                PlayerFactsMoved(
                    player_id=event.player_id,
                    changes={"proposals_opt_in": event.accepted},
                ),
            )
        case IntroWritten():
            # The line and **no moment beside it**: nothing reads when it was
            # written, and a stamp would be activity recency by another door
            # (`docs/adr/0107` §3, which stands).
            return (
                PlayerFactsMoved(
                    player_id=event.player_id, changes={"intro": event.intro}
                ),
            )
        case RatingInitialised():
            return (
                CandidateRowMoved(
                    player_id=event.player_id,
                    sport=event.sport,
                    changes={
                        "mu": event.mu,
                        "sigma": event.sigma,
                        "confidence": event.confidence,
                        # The likely range travels **as published** — the
                        # event has carried it all along, and the alternative
                        # would put the engine's rounding rule in every
                        # consumer that ever draws it.
                        "range_low": event.range_low,
                        "range_high": event.range_high,
                        # `band`, not `band_name`: the index row carries no
                        # field whose name reads as a person's, which is what
                        # `tests/unit/test_candidate_row_fence.py` walks for.
                        "band": event.band_name,
                        "band_lower": event.band_lower,
                        "band_upper": event.band_upper,
                        "rating_status": event.status,
                        "calibration_priority": event.calibration_priority,
                    },
                ),
            )
        case PlayIntentDeclared():
            return (
                CandidateRowMoved(
                    player_id=event.player_id,
                    sport=event.sport,
                    changes={"declared_intent": event.intent},
                ),
            )
        case RefreshTokenIssued() | RefreshTokenRotated():
            # The only activity signal this platform contains. It means *last
            # session refresh* and therefore resolves days rather than hours
            # (`docs/adr/0111`), which is true precisely because these two are
            # the only events that move it — a revoked token is a sign-out and
            # is deliberately not one of them.
            return (
                PlayerFactsMoved(
                    player_id=event.user_id,
                    changes={"last_active_at": event.occurred_at},
                ),
            )
        case _:
            return ()


def _area(latitude: float, longitude: float) -> Mapping[str, object]:
    """The coarse area a pair of degrees falls in, re-coarsened on the way in.

    The events already carry a coarse pair — ``LocationArea.around`` discards the
    precise fix at the boundary and there is no version of the stream that holds
    one — so this is a no-op today. It is here because *the index holds no precise
    location* is a claim this file is one of two places able to break, and
    re-coarsening something already coarse costs one rounding per location change.
    """

    area = LocationArea.around(latitude, longitude)
    return {"area_latitude": area.latitude, "area_longitude": area.longitude}


#: Every durable contract this projection reads. **Declared, not derived.**
#:
#: Two lists that check each other, in the idiom ``MATCHER_DEMANDS`` established
#: beside ``FAIL_POSTURE``: deriving this from the dispatch above would make
#: forgetting a contract invisible rather than red, and the failure this guards is
#: a column that quietly stops moving — the kind nobody sees until a shortlist is
#: built from a fact that was true in March.
PROJECTED_CONTRACTS: tuple[Type[DomainEvent], ...] = (
    PlayerProfileCreated,
    SocialTagsChanged,
    AvailabilityChanged,
    LocationChanged,
    SearchRadiusChanged,
    GenderChanged,
    GenderPreferenceChanged,
    ProposalsOptInAnswered,
    IntroWritten,
    PlayIntentDeclared,
    RatingInitialised,
    RefreshTokenIssued,
    RefreshTokenRotated,
)

"""The PlayerProfile aggregate — event-sourced, keyed on the player alone.

**The first aggregate in the racket-sport domain that is not per sport.** A Skill
rating is per ``(player, sport)`` because skill is; tags, photos, a week, a
location and a consent are facts about a person (``docs/adr/0089``). Resisting
the pull toward a sport dimension here is deliberate, and ADR-0090 depends on the
cardinality: *does a Player profile exist* is a per-player question with a
per-player answer, and it is what onboarding's second part is checkpointed on.

**Creation is two events, not one.** ``PlayerProfileCreated`` carries the five
preferences; ``ProposalsOptInAnswered`` carries the consent. They are appended
together, in one transaction, and a profile cannot be created without both —
``create`` takes the opt-in as a required argument and there is no way to reach
the created state with it absent. The split is what makes the consent history one
sequence with no special first case.

**A preference transition that changes nothing records nothing.** Setting the
radius to the value it already holds leaves the stream alone, which is what keeps
an idempotent client retry from growing a stream by an event that says a player
did not do anything. The consent transition is the deliberate exception, and
``answer_proposals_opt_in`` says why.

**Snapshotting is not built, and this is the aggregate that will need it.** An
assessment is under ten events and then finished; a profile is written every time
someone adjusts their week, for years. ADR-0089 records that as a known cost
rather than an oversight — building it before a profile exists would be guessing
at the shape.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Final, Iterable, Sequence
from uuid import UUID

from app.kernel import Instant, instant
from app.modules.player_profile.domain.availability import AvailabilityGrid
from app.modules.player_profile.domain.consent import ConsentSurface, ProposalsOptIn
from app.modules.player_profile.domain.errors import (
    DuplicatePhoto,
    TooManyPhotos,
)
from app.modules.player_profile.domain.events import (
    AvailabilityChanged,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    ProposalsOptInAnswered,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.search_radius import SearchRadius
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: How many photos a profile may hold. The product's number
#: (``../../../../CONTEXT.md`` — *Profile photo*: up to three, or none), checked
#: on the commit rather than on the upload, because uploading is not attaching.
MAX_PROFILE_PHOTOS: Final = 3


def photo_order(photo_ids: Iterable[UUID]) -> tuple[UUID, ...]:
    """The photo list as a profile may hold it, or a refusal saying why not.

    **Order is preserved, never sorted.** The first photo is the one a player
    card shows, so the sequence the client sent *is* the answer — which is the
    opposite of how a tag selection and an availability grid are treated, and
    the reason is that neither of those has a first element that means anything.
    """

    ordered = tuple(photo_ids)
    if len(set(ordered)) != len(ordered):
        raise DuplicatePhoto()
    if len(ordered) > MAX_PROFILE_PHOTOS:
        raise TooManyPhotos()
    return ordered


@dataclass
class PlayerProfile:
    """One player's answers, rebuilt by folding their stream.

    ``id`` is the player id: the stream is keyed on the player and only the
    player, so the aggregate has no identity of its own to carry
    (``domain/ids.py``).
    """

    player_id: UUID
    social_tags: SocialTagSelection
    photo_ids: tuple[UUID, ...]
    availability: AvailabilityGrid
    location: LocationArea
    search_radius: SearchRadius
    #: The latest answer. Never ``None`` on a created profile — ``create``
    #: requires one — but the field is optional because ``_empty`` exists before
    #: any event has been applied.
    proposals_opt_in: ProposalsOptIn | None
    #: What the creating commit was made under. Read by the use case to tell a
    #: retry of that commit from a second, different one.
    idempotency_key: str
    created_at: Instant
    updated_at: Instant
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @property
    def id(self) -> UUID:
        """The stream id, which is the player id. See ``domain/ids.py``."""

        return self.player_id

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "PlayerProfile":
        profile = cls._empty()
        for event in events:
            profile._apply(event)
        return profile

    @classmethod
    def _empty(cls) -> "PlayerProfile":
        profile = cls.__new__(cls)
        profile.version = 0
        profile.proposals_opt_in = None
        profile._events = EventRecorder()
        return profile

    @classmethod
    def create(
        cls,
        *,
        player_id: UUID,
        social_tags: SocialTagSelection,
        photo_ids: Sequence[UUID],
        availability: AvailabilityGrid,
        location: LocationArea,
        search_radius: SearchRadius,
        proposals_opt_in_accepted: bool,
        consent_copy_version: str,
        consent_surface: ConsentSurface,
        idempotency_key: str,
        occurred_at: Instant,
    ) -> "PlayerProfile":
        """The one commit that ends onboarding's second part.

        Every argument is a value object that has already refused what it
        refuses — the count of tags, the radius against its bounds, the
        coarsening of the location — so nothing is re-checked here except what is
        genuinely about the *profile* rather than about one of its answers: the
        photo list's length and its uniqueness.

        The opt-in arrives as its three primitive facts rather than as a
        ``ProposalsOptIn``, because the moment is the event's ``occurred_at`` and
        assembling the record here is what guarantees the two cannot disagree.
        """

        ordered_photos = photo_order(photo_ids)

        profile = cls._empty()
        profile._record_that(
            PlayerProfileCreated(
                player_id=player_id,
                social_tags=social_tags.ids,
                photo_ids=tuple(str(photo_id) for photo_id in ordered_photos),
                availability=availability.codes,
                latitude=location.latitude,
                longitude=location.longitude,
                search_radius_km=search_radius.kilometres,
                idempotency_key=idempotency_key,
                occurred_at=occurred_at,
            )
        )
        # Appended by the creating commit exactly as a later change appends it,
        # which is the whole of what "no special first case" buys.
        profile._record_that(
            ProposalsOptInAnswered(
                player_id=player_id,
                accepted=proposals_opt_in_accepted,
                copy_version=consent_copy_version,
                surface=consent_surface.value,
                occurred_at=occurred_at,
            )
        )
        return profile

    # ------------------------------------------------------------------
    # Later changes, from the profile screen
    # ------------------------------------------------------------------

    def change_social_tags(
        self, selection: SocialTagSelection, *, occurred_at: Instant
    ) -> None:
        if selection == self.social_tags:
            return
        self._record_that(
            SocialTagsChanged(
                player_id=self.player_id,
                social_tags=selection.ids,
                occurred_at=occurred_at,
            )
        )

    def change_photos(
        self, photo_ids: Sequence[UUID], *, occurred_at: Instant
    ) -> None:
        ordered = photo_order(photo_ids)
        if ordered == self.photo_ids:
            return
        self._record_that(
            PhotosChanged(
                player_id=self.player_id,
                photo_ids=tuple(str(photo_id) for photo_id in ordered),
                occurred_at=occurred_at,
            )
        )

    def change_availability(
        self, grid: AvailabilityGrid, *, occurred_at: Instant
    ) -> None:
        if grid == self.availability:
            return
        self._record_that(
            AvailabilityChanged(
                player_id=self.player_id,
                availability=grid.codes,
                occurred_at=occurred_at,
            )
        )

    def change_location(self, area: LocationArea, *, occurred_at: Instant) -> None:
        if area == self.location:
            return
        self._record_that(
            LocationChanged(
                player_id=self.player_id,
                latitude=area.latitude,
                longitude=area.longitude,
                occurred_at=occurred_at,
            )
        )

    def change_search_radius(
        self, radius: SearchRadius, *, occurred_at: Instant
    ) -> None:
        if radius == self.search_radius:
            return
        self._record_that(
            SearchRadiusChanged(
                player_id=self.player_id,
                search_radius_km=radius.kilometres,
                occurred_at=occurred_at,
            )
        )

    def answer_proposals_opt_in(
        self,
        *,
        accepted: bool,
        copy_version: str,
        surface: ConsentSurface,
        occurred_at: Instant,
    ) -> None:
        """Record an answer to the proposals question — **always**.

        The one transition here that is not a no-op when nothing changed, and
        the departure is the point of the aggregate. *The player was asked
        again, against these words, on this surface, and answered the same way*
        is a fact about consent; a log that collapsed it could not later say
        which wording a standing yes was given against. Consent is evidenced,
        not asserted (``../../../../CONTEXT.md``).
        """

        self._record_that(
            ProposalsOptInAnswered(
                player_id=self.player_id,
                accepted=accepted,
                copy_version=copy_version,
                surface=surface.value,
                occurred_at=occurred_at,
            )
        )

    # ------------------------------------------------------------------
    # Replay
    # ------------------------------------------------------------------

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, PlayerProfileCreated):
            self.player_id = event.player_id
            self.social_tags = SocialTagSelection.from_ids(event.social_tags)
            self.photo_ids = tuple(UUID(value) for value in event.photo_ids)
            self.availability = AvailabilityGrid.from_codes(event.availability)
            self.location = LocationArea(
                latitude=event.latitude, longitude=event.longitude
            )
            self.search_radius = SearchRadius(kilometres=event.search_radius_km)
            self.idempotency_key = event.idempotency_key
            self.created_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        if isinstance(event, SocialTagsChanged):
            self.social_tags = SocialTagSelection.from_ids(event.social_tags)
            self._touch(event.occurred_at)
            return
        if isinstance(event, PhotosChanged):
            self.photo_ids = tuple(UUID(value) for value in event.photo_ids)
            self._touch(event.occurred_at)
            return
        if isinstance(event, AvailabilityChanged):
            self.availability = AvailabilityGrid.from_codes(event.availability)
            self._touch(event.occurred_at)
            return
        if isinstance(event, LocationChanged):
            self.location = LocationArea(
                latitude=event.latitude, longitude=event.longitude
            )
            self._touch(event.occurred_at)
            return
        if isinstance(event, SearchRadiusChanged):
            self.search_radius = SearchRadius(kilometres=event.search_radius_km)
            self._touch(event.occurred_at)
            return
        if isinstance(event, ProposalsOptInAnswered):
            # The *latest* answer is the state; every answer is the history, and
            # the history is the stream. Nothing here accumulates a list — a
            # reader that wants the sequence replays this event type.
            self.proposals_opt_in = ProposalsOptIn(
                accepted=event.accepted,
                copy_version=event.copy_version,
                surface=ConsentSurface(event.surface),
                answered_at=instant(event.occurred_at),
            )
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported player profile event {event!r}")

    def _touch(self, occurred_at: datetime) -> None:
        self.updated_at = instant(occurred_at)
        self.version += 1

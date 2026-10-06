"""The PlayerProfile aggregate — event-sourced, keyed on the player alone.

**The first aggregate in the racket-sport domain that is not per sport.** A Skill
rating is per ``(player, sport)`` because skill is; tags, photos, a week, a
location are facts about a person (``docs/adr/0089``). Resisting
the pull toward a sport dimension here is deliberate, and ADR-0090 depends on the
cardinality: *does a Player profile exist* is a per-player question with a
per-player answer, and it is what onboarding's second part is checkpointed on.

**Creation is one event — and a second where the player wrote a line.**
``PlayerProfileCreated`` carries the preferences. ``IntroWritten`` follows it,
in the same transaction, **only when there is a line** (``docs/adr/0170``): the
intro is optional, a blank leaves nothing behind, and the creating event does
not grow a field for it. The search radius and the proposals opt-in were asked
here too, and went with the ranking that read them (#581).

**A transition that changes nothing records nothing.** Setting the week to the
week it already holds leaves the stream alone, which is what keeps an
idempotent client retry from growing a stream by an event that says a player
did not do anything.

**The write path refuses; the fold accepts.** ``_apply`` rebuilds every value
through a ``recorded`` constructor that does *not* re-check the served bounds,
and the transitions above build through the checking ones. That asymmetry is
load-bearing: the tag floor and ceiling and the intro's cap are documented as
numbers product may edit, and a fold that could refuse a recorded fact would
make lowering any of them retroactively un-rehydrate the profiles outside the
new range — first visible as ``GET /users/me`` failing for players who had done
nothing wrong. A stream is a record of what happened, and replaying it may not
second-guess it.

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
from app.modules.player_profile.domain.errors import (
    DuplicatePhoto,
    TooManyPhotos,
)
from app.modules.player_profile.domain.events import (
    GenderChanged,
    GenderPreferenceChanged,
    IntroChanged,
    IntroWritten,
    LocationChanged,
    PhotosChanged,
    PlayerProfileCreated,
    SocialTagsChanged,
    WeeklyHoursSet,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.intro import Intro
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.social_tags import SocialTagSelection
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: How many photos a profile may hold. The product's number
#: (``../../../../CONTEXT.md`` — *Profile photo*: up to three, or none), checked
#: on the commit rather than on the upload, because uploading is not attaching.
MAX_PROFILE_PHOTOS: Final = 3


def photo_order(photo_ids: Iterable[UUID]) -> tuple[UUID, ...]:
    """The photo list as a profile may hold it; raises if it is not one.

    **Order is preserved, never sorted.** The first photo is the one a player
    card shows, so the sequence the client sent *is* the answer — which is the
    opposite of how a tag selection and a week of hours are treated, and
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
    weekly_hours: WeeklyHours
    location: LocationArea
    #: The player's own answer to the gender question (``docs/adr/0096``).
    #:
    #: ``None`` is **not** an answer and is unreachable through ``create``: it
    #: is a profile committed before anybody was asked, and the only way to hold
    #: one is to replay such a stream. It is never read as
    #: ``PREFER_NOT_TO_SAY``, which is a player's own choice — a gate that
    #: cannot be evaluated excludes rather than guesses
    #: (``../../../../CONTEXT.md``, via ADR-0095), and that rule is the reason
    #: the absence is kept distinguishable instead of being folded away here.
    gender: Gender | None
    #: Who this player is willing to be matched with. Optional and defaulting to
    #: ``ANY``, so unlike ``gender`` there is nothing for its absence to mean.
    gender_preference: GenderPreference
    #: The line the player wrote about themselves, or ``None`` where they wrote
    #: none (``docs/adr/0170``). **An absence and never an empty intro**: a
    #: player who skipped has no line, and a stream with no ``IntroWritten``
    #: folds to exactly that.
    intro: Intro | None
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
        profile.intro = None
        profile._events = EventRecorder()
        return profile

    @classmethod
    def create(
        cls,
        *,
        player_id: UUID,
        social_tags: SocialTagSelection,
        photo_ids: Sequence[UUID],
        weekly_hours: WeeklyHours,
        location: LocationArea,
        gender: Gender,
        gender_preference: GenderPreference = DEFAULT_GENDER_PREFERENCE,
        idempotency_key: str,
        occurred_at: Instant,
        intro: Intro | None = None,
    ) -> "PlayerProfile":
        """The one commit that ends onboarding's second part.

        Every argument is a value object that has already refused what it
        refuses — the count of tags, the floor of the week, the coarsening of
        the location — so nothing is re-checked here except what is genuinely
        about the *profile* rather than about one of its answers: the photo
        list's length and its uniqueness.

        **``gender`` is required and ``gender_preference`` is not**, and the
        asymmetry is ADR-0096's: the answer about oneself is asked once, here,
        with ``PREFER_NOT_TO_SAY`` a first-class choice — because optional
        collection silently shrinks the constrained pool at exactly the moment
        the pool is smallest — while a preference over others defaults to
        ``ANY``, which is what *no constraint* already means. Requiring it is
        enforced by the type: there is no value of ``Gender`` that means
        *unanswered*, so there is no branch here to forget.

        **``intro`` is optional and its absence records nothing.** It arrives
        already fenced — ``Intro.written`` refused contact and the shape before
        the commit reached here — and it is its own event, appended after the
        creating one (``docs/adr/0170``).
        """

        ordered_photos = photo_order(photo_ids)

        profile = cls._empty()
        profile._record_that(
            PlayerProfileCreated(
                player_id=player_id,
                social_tags=social_tags.ids,
                photo_ids=tuple(str(photo_id) for photo_id in ordered_photos),
                weekly_hours=weekly_hours.codes,
                latitude=location.latitude,
                longitude=location.longitude,
                idempotency_key=idempotency_key,
                occurred_at=occurred_at,
                gender=gender.value,
                gender_preference=gender_preference.value,
            )
        )
        if intro is not None:
            # Only when there is a line. A blank leaves nothing behind, so a
            # stream with no `IntroWritten` is the ordinary shape and not a
            # profile with a gap in it.
            profile._record_that(
                IntroWritten(
                    player_id=player_id, intro=intro.text, occurred_at=occurred_at
                )
            )
        return profile

    # ------------------------------------------------------------------
    # Later changes, from the profile screen — one unkeyed PUT per transition
    # below: the You tab's (docs/adr/0179 §8), the Play screens' for the week,
    # and the cold start's for the location (docs/adr/0174 §6)
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

    def change_photos(self, photo_ids: Sequence[UUID], *, occurred_at: Instant) -> None:
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

    def set_weekly_hours(self, week: WeeklyHours, *, occurred_at: Instant) -> None:
        if week == self.weekly_hours:
            return
        self._record_that(
            WeeklyHoursSet(
                player_id=self.player_id,
                weekly_hours=week.codes,
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

    def change_intro(self, intro: Intro | None, *, occurred_at: Instant) -> None:
        """Replace the line the player wrote — or withdraw it.

        ``docs/adr/0179`` §6: the edit ADR-0170 §5 deferred to the day the
        intro, the tags and the photos are edited together. The line arrives
        already fenced — ``Intro.written`` refused contact and the shape before
        it got here, exactly as it does for the commit — and ``None`` is the
        withdrawal: recorded, and the profile folds to none.

        The no-op rule holds on both sides of the absence: the line already
        held records nothing, and withdrawing a line that was never written
        records nothing either.
        """

        if intro == self.intro:
            return
        self._record_that(
            IntroChanged(
                player_id=self.player_id,
                intro=None if intro is None else intro.text,
                occurred_at=occurred_at,
            )
        )

    def change_gender(self, gender: Gender, *, occurred_at: Instant) -> None:
        """Record a new answer to the gender question.

        Gender is *"self-declared, freely changed"* (``docs/adr/0096``), so this
        exists from the day the field does rather than being a later addition —
        a value a player may not correct is a value the platform has ruled on,
        which is the one thing this field is not.

        A no-op when nothing moved, like every preference beside it. A profile
        replayed from a stream older than the field holds ``None``, and
        answering it for the first time is therefore a change and records one.
        """

        if gender == self.gender:
            return
        self._record_that(
            GenderChanged(
                player_id=self.player_id,
                gender=gender.value,
                occurred_at=occurred_at,
            )
        )

    def change_gender_preference(
        self, preference: GenderPreference, *, occurred_at: Instant
    ) -> None:
        """Record a new durable answer to *who am I willing to play with*.

        **Durable, never per game**, because the gate it feeds is mutual: it is
        evaluated against this player when somebody else's game is being made
        and this player is not present, which a setting made at the moment could
        not bind at all.
        """

        if preference == self.gender_preference:
            return
        self._record_that(
            GenderPreferenceChanged(
                player_id=self.player_id,
                gender_preference=preference.value,
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
            self.social_tags = SocialTagSelection.recorded(event.social_tags)
            self.photo_ids = tuple(UUID(value) for value in event.photo_ids)
            self.weekly_hours = WeeklyHours.from_codes(event.weekly_hours)
            self.location = LocationArea(
                latitude=event.latitude, longitude=event.longitude
            )
            # Absent stays absent. A stream written before the question existed
            # decodes with ``gender`` unset, and folding that into a value would
            # make the profile claim an answer nobody gave.
            self.gender = Gender(event.gender) if event.gender is not None else None
            self.gender_preference = GenderPreference(event.gender_preference)
            self.idempotency_key = event.idempotency_key
            self.created_at = instant(event.occurred_at)
            self._touch(event.occurred_at)
            return
        if isinstance(event, SocialTagsChanged):
            self.social_tags = SocialTagSelection.recorded(event.social_tags)
            self._touch(event.occurred_at)
            return
        if isinstance(event, PhotosChanged):
            self.photo_ids = tuple(UUID(value) for value in event.photo_ids)
            self._touch(event.occurred_at)
            return
        if isinstance(event, WeeklyHoursSet):
            self.weekly_hours = WeeklyHours.from_codes(event.weekly_hours)
            self._touch(event.occurred_at)
            return
        if isinstance(event, LocationChanged):
            self.location = LocationArea(
                latitude=event.latitude, longitude=event.longitude
            )
            self._touch(event.occurred_at)
            return
        if isinstance(event, GenderChanged):
            self.gender = Gender(event.gender)
            self._touch(event.occurred_at)
            return
        if isinstance(event, GenderPreferenceChanged):
            self.gender_preference = GenderPreference(event.gender_preference)
            self._touch(event.occurred_at)
            return
        if isinstance(event, IntroWritten):
            # Recorded, never re-checked: the cap and the fence bound the write.
            self.intro = Intro.recorded(event.intro)
            self._touch(event.occurred_at)
            return
        if isinstance(event, IntroChanged):
            # The latest of either event is the line; `None` is the withdrawal
            # and folds to the absence a skipped step leaves.
            self.intro = None if event.intro is None else Intro.recorded(event.intro)
            self._touch(event.occurred_at)
            return
        raise TypeError(f"Unsupported player profile event {event!r}")

    def _touch(self, occurred_at: datetime) -> None:
        self.updated_at = instant(occurred_at)
        self.version += 1

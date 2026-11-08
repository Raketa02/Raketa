"""The Player profile context's domain events — two streams, and what each carries.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a tag as its ``str`` id, a photo as its ``str``
uuid, an hour of the week as its code, a location as two floats, a gender and an
intent as their machine codes. Nothing here holds a value object, and nothing
here holds display text.

Twelve events. Eleven belong to the profile's own stream, keyed on the player,
and they fall into three kinds; the twelfth belongs to a **second aggregate** in
this context and is kept here because a context's durable names have one home.

**One creation.** ``PlayerProfileCreated`` is the single commit that ends
onboarding's second part, carrying every preference at once (``docs/adr/0089``).
It also carries the **idempotency key** the commit was made under — which is what
lets the same request arriving twice be recognised as the same request without a
table beside the stream to keep in step with it. The key is evidence about a
*write*, not about the player, and it is on the creating event only.

**Eight preference changes**, for the profile screen that edits the same values
later: tags, photos, weekly hours, location, gender and gender preference — and
two the creating event never carried: the reliability filter (#661), which
every profile starts with off, and *Show me in General* (#772), which every
profile starts with on. Each
carries the whole new value rather than a delta, because a preference is small,
replay stays a fold, and *what was it before* is answered by the event before it.

**One line the player wrote, and its later edits.** ``IntroWritten`` carries
the intro (``docs/adr/0170``) — text a person typed, already fenced at the write,
so what is stored is what a card shows. It is appended by the creating commit
**only when a line is present**: a blank leaves nothing behind, and
``PlayerProfileCreated`` deliberately does not grow a field for it, because an
optional field most streams lack is what an upcaster is later written for. A
stream with no ``IntroWritten`` folds to *no intro*. ``IntroChanged`` is the You
tab's edit of the same line (``docs/adr/0179`` §6) — the whole new value, or
``None`` for a withdrawal — and the fold keeps the latest of either.

**One declaration, on its own stream.** ``PlayIntentDeclared`` is keyed
``(player, sport)`` and is not a fact about the profile at all
(``docs/adr/0094``) — see ``play_intent_declaration.py``. It is registered under
``player_profile.play_intent_declared`` because the aggregate lives in this
context, and it is the reason this module's first line no longer says *one
stream*.

**The radius and the suggestions answer are gone** (#581). *How far will you
travel* and *may we suggest games?* were read by the "who fits whom" ranking
alone, and it went in #580. ``player_profile.search_radius_changed`` and
``player_profile.proposals_opt_in_answered`` are no longer registered, and
``PlayerProfileCreated`` lost ``search_radius_km`` — which is why it is at
version 3.

**Appending an optional field to an event that already has rows does not need
a new version.** ``PlayerProfileCreated`` gained ``gender`` and
``gender_preference`` after profiles existed, and both are declared last, with
defaults, so a row written before the question existed still decodes into this
class — the pattern ``UserRegistered.adult_attested`` and
``AssessmentCompleted`` already follow. The two are not symmetrical about what
their absence *means*, and each says so on its own field.

**Changing what a field holds does, and so does removing one.**
``player_profile.created`` is at version 3. Version 1 carried ``availability``,
a week of mornings, afternoons and evenings; ``docs/adr/0189`` §5 made the week
hours, and the field became ``weekly_hours`` — version 2. Version 2 carried
``search_radius_km``, and #581 removed it — version 3. Neither older version is
readable, deliberately: no environment but ``local`` has ever run, its database
is disposable and is reset with the change, and a row written under an old
shape is a decoding error rather than a profile folded wrongly. The two appended fields
keep their defaults, and what their absence would mean, though no version 3 row
lacks them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.player_profile.domain.gender import DEFAULT_GENDER_PREFERENCE


@dataclass(frozen=True)
class PlayerProfileCreated:
    """Every preference from onboarding's second part, in one event."""

    player_id: UUID
    social_tags: tuple[str, ...]
    photo_ids: tuple[str, ...]
    #: The hours of the week as ``WeeklyHour.code`` writes them — ``"2:19"``.
    #: Never empty on a commit written today: the floor refuses it
    #: (``docs/adr/0102``), and a blank week met anyway is *absent*.
    weekly_hours: tuple[str, ...]
    latitude: float
    longitude: float
    #: What the client called this commit. Recorded so a retry of the same
    #: request is answerable from the stream itself.
    idempotency_key: str
    occurred_at: datetime
    #: The player's own answer, as a ``Gender`` code (``docs/adr/0096``).
    #:
    #: **Required at profile creation, and yet nullable here — the two are not
    #: in conflict.** ``None`` is a profile committed before anybody was asked,
    #: and it says only that. It is emphatically **not** a quieter
    #: ``PREFER_NOT_TO_SAY``: that value is an answer a player chose, and
    #: backfilling absence to it would invent the one thing a self-declaration
    #: must never be invented. Nothing on the write path can produce ``None`` —
    #: ``PlayerProfile.create`` requires a ``Gender`` — so it is reachable only
    #: by replaying history, which is exactly what it is for. No backfill.
    gender: str | None = None
    #: Who this player is willing to be matched with, as a ``GenderPreference``
    #: code. Unlike ``gender`` this has a real default and its absence is not a
    #: separate fact: the preference is optional and a player who has never
    #: expressed one holds ``ANY`` (``docs/adr/0096`` §2), so a row written
    #: before the field existed decodes to the same thing an unconstrained
    #: player answers today.
    gender_preference: str = DEFAULT_GENDER_PREFERENCE.value

    def __post_init__(self) -> None:
        _retuple(self, "social_tags", "photo_ids", "weekly_hours")


@dataclass(frozen=True)
class SocialTagsChanged:
    player_id: UUID
    social_tags: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "social_tags")


@dataclass(frozen=True)
class PhotosChanged:
    """The whole photo list, in its new order.

    Order is meaning here: the first photo is the one a player card shows, so
    re-ordering three photos is a change even though the set is the same.
    """

    player_id: UUID
    photo_ids: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "photo_ids")


@dataclass(frozen=True)
class WeeklyHoursSet:
    """The whole week, as it now stands — the You tab's *Save your week*.

    ``WeeklyHoursSet`` rather than ``…Changed`` because the mechanics name it so
    (``docs/specs/games-and-fill-in/the-screens.md`` C1); it replaced
    ``player_profile.availability_changed``, whose week was mornings, afternoons
    and evenings. Empty is a legal value here and only here: a player may clear
    their week after committing, and it then reads as *absent* (ADR-0102).
    """

    player_id: UUID
    weekly_hours: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "weekly_hours")


@dataclass(frozen=True)
class LocationChanged:
    """The coarse area, and only ever the coarse area.

    The precise fix that produced it never reaches an event — it is discarded at
    the boundary by ``LocationArea.around``, so there is no version of this
    stream from which one could be recovered.
    """

    player_id: UUID
    latitude: float
    longitude: float
    occurred_at: datetime


@dataclass(frozen=True)
class GenderChanged:
    """A new answer to the gender question — *"self-declared, freely changed"*.

    Its own event rather than a re-issued ``PlayerProfileCreated``, for the
    reason every preference change here has one: the creating event is also the
    idempotency record of a commit that happens once, and a player editing an
    answer years later is not making that commit again.

    A preference, so it obeys the preference rule: a transition to the value
    already held records nothing.
    """

    player_id: UUID
    gender: str
    occurred_at: datetime


@dataclass(frozen=True)
class GenderPreferenceChanged:
    """A new durable answer to *who am I willing to be matched with*.

    **Durable, and it has effects the player must be told about at the moment of
    setting** — narrowing makes them invisible to the excluded side entirely,
    including to searchers who asked for anybody (``docs/adr/0096`` §3). This
    event records the change; the sentence is the client's, chosen from a reason
    code (``docs/adr/0022``). Learning it from silence is not acceptable, and
    nothing here can enforce that — which is why it is written down here.

    **Seats already accepted are facts, not candidates.** Changing a preference
    changes future searches and never retroactively evicts somebody who has
    already said yes, so nothing downstream of this event may treat it as a
    reason to undo an agreement.
    """

    player_id: UUID
    gender_preference: str
    occurred_at: datetime


@dataclass(frozen=True)
class ReliabilityMinimumSet:
    """A new durable answer to *whom will I share a court with*, by reliability:
    *at least Medium*, *at least High*, or ``None`` — the filter off
    (``docs/adr/0195`` §6, #661).

    **A preference beside the gender preference, and read the same way**: the
    pair rule asks it of every pair it would seat, both ways, whenever somebody
    else's game is being made — which a setting made at the moment could not
    bind. ``minimum`` is a ``ReliabilityBand`` code, the engine's spelling.

    **Yeses already given stand.** It acts on what is dealt and joined from then
    on: nothing downstream of this event takes a yes back or touches a booked
    game, unlike a block.
    """

    player_id: UUID
    minimum: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class RankingVisibilitySet:
    """*Show me in General*, turned: ``SHOWN`` or ``HIDDEN``, a
    ``RankingVisibility`` code (``docs/adr/0203`` §7, #772).

    **A fact about the player, never about a row**: the creating event carries
    no field for it, because every profile starts shown, and a stream with none
    of these folds to ``SHOWN``. The Rankings context follows it through the
    outbox into its projection, for every sport — one the player has no result
    in yet included.

    **What it stops is new**: a request already made through the ranking stays
    open, and a record already drawn stays drawn (the mechanics §18).
    """

    player_id: UUID
    visibility: str
    occurred_at: datetime


@dataclass(frozen=True)
class IntroWritten:
    """The player's own line, as the fence admitted it.

    **The first of two events on this stream that carry text a person typed**,
    and the reason it may is that the text was refused or admitted *before* it
    got here (``domain/intro.py``): a phone number, an email, a URL or a handle
    never reaches a stream. The commit appends it after the two creating events
    and only when a line was written. **It stays the commit's**: the edit is
    ``IntroChanged`` below (``docs/adr/0179`` §6), and the fold keeps the latest
    of either.

    Trimmed, never lowercased, never translated: the line crosses to a card and
    a record verbatim, and it is never scored.
    """

    player_id: UUID
    intro: str
    occurred_at: datetime


@dataclass(frozen=True)
class IntroChanged:
    """The line as it now stands — or none, where it was withdrawn.

    The You tab's edit (``docs/adr/0179`` §6), which is the day ADR-0170 §5
    deferred the edit to: the intro, the tags and the photos became editable
    together. Its own event rather than ``IntroWritten`` told again, because
    the two say different things — a line was *written* at the commit, and a
    line was *changed* afterwards, which includes being taken back — and a
    withdrawal is the one shape the commit's event cannot carry, since a blank
    at the commit leaves nothing behind.

    ``intro`` is the whole new value, the way every preference change here
    carries one, and ``None`` is **the withdrawal**: the stream records that
    the line was taken back, and the profile folds to the same absence a player
    who skipped the step has. Fenced exactly as the commit fences
    (``domain/intro.py``), so what is stored is what a card shows. A
    preference: the line already held records nothing, and neither does
    withdrawing a line that was never written.
    """

    player_id: UUID
    intro: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class PlayIntentDeclared:
    """What kind of game this player wants, in **one** sport.

    The only event on the ``PlayIntentDeclaration`` stream, and the only event in
    this module that is not about the profile. It carries the pair its stream is
    keyed on — ``player_id`` and ``sport`` — and **not** the stream id itself:
    that id is a pure function of the pair (``ids.py``), so carrying it would be
    a second copy of one fact and a second place for it to disagree.

    ``surface`` is a ``PlayIntentSurface`` code. It is client-asserted, and it
    is safe to be because nothing branches on it (``docs/adr/0094``).

    A **preference**, so a declaration of the value already held records
    nothing: re-declaring the same value says nothing that the previous event
    did not already say.
    """

    player_id: UUID
    #: The sport, as ``Sport.value``. Never a set and never a mapping: one
    #: declaration is about one sport, which is what makes *intent does not
    #: transfer between sports* structural rather than remembered.
    sport: str
    intent: str
    surface: str
    occurred_at: datetime


def _retuple(event: object, *fields: str) -> None:
    """Force a collection field to a tuple, on the way in and out of storage.

    The codec encodes a tuple as a JSON array and decodes it back as a ``list``,
    so without this an event that has been through the store is unequal to the
    event that was appended — and a replay would fold lists where the first pass
    folded tuples. Frozen dataclasses are assigned through ``object`` for the
    same reason ``__post_init__`` normalisation always is.
    """

    for field in fields:
        object.__setattr__(event, field, tuple(getattr(event, field)))

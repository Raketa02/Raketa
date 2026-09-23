"""The Player profile context's domain events — two streams, and what each carries.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a tag as its ``str`` id, a photo as its ``str``
uuid, an availability slot as its code, a location as two floats, a gender and an
intent as their machine codes. Nothing here holds a value object, and nothing
here holds display text.

Twelve events. Eleven belong to the profile's own stream, keyed on the player,
and they fall into four kinds; the twelfth belongs to a **second aggregate** in
this context and is kept here because a context's durable names have one home.

**One creation.** ``PlayerProfileCreated`` is the single commit that ends
onboarding's second part, carrying every preference at once (``docs/adr/0089``).
It also carries the **idempotency key** the commit was made under — which is what
lets the same request arriving twice be recognised as the same request without a
table beside the stream to keep in step with it. The key is evidence about a
*write*, not about the player, and it is on the creating event only.

**Seven preference changes**, for the profile screen that edits the same values
later: tags, photos, availability, location, radius, gender and gender
preference. Each carries the whole new value rather than a delta, because a
preference is small, replay stays a fold, and *what was it before* is answered by
the event before it.

**One consent answer.** ``ProposalsOptInAnswered`` carries the answer, the copy
version shown and the surface — and its own ``occurred_at`` is the moment. It is
appended by the creating commit **as well as** by every later change, so the
consent history is one sequence with no special first case: a reader that wants
every answer a player ever gave replays this one event type and needs to know
nothing about how the profile began.

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

**Adding a field to ``ProposalsOptInAnswered`` means a new catalog version.**
Events are a published contract, and this is the event most likely to be asked to
carry more later — a jurisdiction, a policy id, the surface's own version. The
existing rows must keep decoding, which is what the version is for.

**Appending an optional field to an event that already has rows does not.**
``PlayerProfileCreated`` gained ``gender`` and ``gender_preference`` after
profiles existed, and both are declared last, with defaults, so a row written
before the question existed still decodes into this class — the pattern
``UserRegistered.adult_attested`` and ``AssessmentCompleted`` already follow. The
durable name stays ``player_profile.created`` / v1. The two are not symmetrical
about what their absence *means*, and each says so on its own field.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.modules.player_profile.domain.gender import DEFAULT_GENDER_PREFERENCE


@dataclass(frozen=True)
class PlayerProfileCreated:
    """Every preference from onboarding's second part, in one event.

    The opt-in is **not** here: it arrives as its own
    ``ProposalsOptInAnswered`` appended immediately after, in the same
    transaction. That is deliberate and is what "one sequence with no special
    first case" means — the alternative puts the first consent answer in a
    different shape from every one that follows it, and every reader of the
    consent history then has two shapes to handle forever.
    """

    player_id: UUID
    social_tags: tuple[str, ...]
    photo_ids: tuple[str, ...]
    #: Availability slots as ``AvailabilitySlot.code`` writes them. Empty is a
    #: real answer — *no preference* — and never an absent one.
    availability: tuple[str, ...]
    latitude: float
    longitude: float
    search_radius_km: int
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
        _retuple(self, "social_tags", "photo_ids", "availability")


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
class AvailabilityChanged:
    player_id: UUID
    availability: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "availability")


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
class SearchRadiusChanged:
    player_id: UUID
    search_radius_km: int
    occurred_at: datetime


@dataclass(frozen=True)
class GenderChanged:
    """A new answer to the gender question — *"self-declared, freely changed"*.

    Its own event rather than a re-issued ``PlayerProfileCreated``, for the
    reason every preference change here has one: the creating event is also the
    idempotency record of a commit that happens once, and a player editing an
    answer years later is not making that commit again.

    A preference and not a consent, so it obeys the preference rule: a
    transition to the value already held records nothing. There is no wording to
    evidence a gender against and no question of *which words did they answer* —
    which is precisely the thing ``ProposalsOptInAnswered`` is the exception for.
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
    (``domain/intro.py``), so what is stored is what a card shows. A preference
    and not a consent: the line already held records nothing, and neither does
    withdrawing a line that was never written.
    """

    player_id: UUID
    intro: str | None
    occurred_at: datetime


@dataclass(frozen=True)
class ProposalsOptInAnswered:
    """One answer to the proposals question, with what makes it evidence.

    ``occurred_at`` is the moment, carried the way every event carries its
    moment rather than as a second field somebody has to keep in step with it.
    ``copy_version`` identifies the words shown — never the words themselves,
    because freezing copy in history is how a wording change becomes a
    migration.

    **Recorded every time it is answered, including when the answer has not
    changed.** That is the one place this stream departs from the preference
    events above, which are no-ops when nothing moved: *the player was asked
    again, against these words, and said yes again* is a fact about consent, and
    a consent log that drops re-affirmations cannot evidence one.
    """

    player_id: UUID
    accepted: bool
    copy_version: str
    surface: str
    occurred_at: datetime


@dataclass(frozen=True)
class PlayIntentDeclared:
    """What kind of game this player wants, in **one** sport.

    The only event on the ``PlayIntentDeclaration`` stream, and the only event in
    this module that is not about the profile. It carries the pair its stream is
    keyed on — ``player_id`` and ``sport`` — and **not** the stream id itself:
    that id is a pure function of the pair (``ids.py``), so carrying it would be
    a second copy of one fact and a second place for it to disagree.

    ``surface`` is a ``PlayIntentSurface`` code, following ``ConsentSurface``'s
    precedent in this same context. It is client-asserted, and it is safe to be
    because nothing branches on it (``docs/adr/0094``).

    A **preference**, so a declaration of the value already held records
    nothing. That is deliberately the opposite of ``ProposalsOptInAnswered``,
    which is beside it in this module: there is no wording to evidence an intent
    against, so re-declaring the same value evidences nothing that the previous
    event did not already say.
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

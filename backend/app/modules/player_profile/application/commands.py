"""Commands into the Player profile context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.kernel import Sport
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)


@dataclass(frozen=True, slots=True)
class UploadPhotoCommand:
    """One photo, from one player.

    ``declared_media_type`` is what the *client* said the bytes are. It is
    checked against the accepted list and then never trusted again — the
    transcoder decides what the bytes actually are, and a mislabelled file is
    refused by the decoder rather than stored under a lie.
    """

    owner_id: UUID
    data: bytes
    declared_media_type: str


@dataclass(frozen=True, slots=True)
class GetPhotoCommand:
    """Read access to one photo, asked for by the player who owns it."""

    owner_id: UUID
    photo_id: UUID


@dataclass(frozen=True, slots=True)
class CommitPlayerProfileCommand:
    """Every answer from onboarding's second part, in one command.

    **Primitives from the boundary, not domain value objects**
    (``backend/CONTEXT.md`` — *Command*). Weekly hours arrive as
    ``(iso weekday, hour)`` pairs and the domain is what turns them into
    hours, so nothing in ``presentation/`` builds a value object.

    The tag ids stay strings on purpose: it is what lets the *domain* refuse an
    id outside the vocabulary, with the code a client branches on, instead of a
    schema layer refusing it as a shapeless 422.

    ``idempotency_key`` is what the client called this commit. The same key twice
    is the same commit — one profile, one answer — which is why a double-tapped
    confirm on a slow connection costs nothing (``docs/adr/0089``).

    ``gender`` and ``gender_preference`` are enums: each is a closed set the
    boundary *selects from* rather than constructs — the same shape
    ``CreateAssessmentCommand`` carries ``Sport`` in — so there is nothing for
    the domain to refuse that the type has not already refused. Neither is a
    string — unlike a tag id, whose vocabulary is *served* and can therefore
    disagree with what a client holds. **``gender`` has no ``None``**: it has
    ``PREFER_NOT_TO_SAY`` — a real answer — so there is no unanswered state to
    model and nothing to refuse at this layer (``docs/adr/0096``).

    **``intro`` is optional, and it is a string here and not an ``Intro``** for
    the tag ids' reason: the fence — the cap, the line breaks, the contact rule
    — is the domain's, and it is the domain that refuses with the code and the
    reason a client branches on (``docs/adr/0170`` §2). ``None`` and a
    whitespace-only string are both *skipped*, and the domain says so.
    """

    player_id: UUID
    idempotency_key: str
    social_tag_ids: Sequence[str]
    photo_ids: Sequence[UUID]
    #: ``(iso weekday 1–7, hour 7–22)`` — one pair per hour the player ticked.
    weekly_hours: Sequence[tuple[int, int]]
    latitude: float
    longitude: float
    gender: Gender
    gender_preference: GenderPreference
    #: One line about themselves, or nothing. Fenced by the domain, never here.
    intro: str | None = None


@dataclass(frozen=True, slots=True)
class SetWeeklyHoursCommand:
    """A player's weekly hours, replaced whole.

    **Primitives from the boundary**, exactly as the commit carries them, so the
    two write paths hand the domain the same shape and the week is built in one
    place. There is no *clear my week* flag: an empty sequence **is** a cleared
    week, and it is a legal value here where it is refused at the commit — the
    floor binds the answer a player is asked for rather than every later edit of
    it (``domain/weekly_hours.py``).
    """

    player_id: UUID
    #: ``(iso weekday 1–7, hour 7–22)`` — one pair per hour still ticked.
    weekly_hours: Sequence[tuple[int, int]]


@dataclass(frozen=True, slots=True)
class ChangeLocationCommand:
    """The phone's fix, on a cold start (``docs/adr/0174`` §6).

    The **precise fix**, as the device gave it and as the commit carries it —
    two floats and not a ``LocationArea`` — because the coarsening is the
    domain's job and it happens exactly once, on the way in
    (``domain/location.py``). Nothing above the use case ever holds the cell,
    and nothing below it ever holds the fix.
    """

    player_id: UUID
    latitude: float
    longitude: float


@dataclass(frozen=True, slots=True)
class DeclarePlayIntentCommand:
    """What kind of game this player wants, in one sport.

    Three enums and no string: ``Sport``, ``PlayIntent`` and
    ``PlayIntentSurface`` are all closed sets the boundary *selects from* rather
    than constructs, which is ``Gender``'s shape in this same context.
    None of them is served, so a client cannot hold a different version of any.

    ``surface`` is **required and client-asserted**. The client is the only party
    that knows which screen a declaration was made on, and nothing branches on
    the answer (``docs/adr/0094``) — which is exactly the condition under which a
    self-reported field is safe to keep. A default would be this layer guessing
    on the client's behalf and recording the guess as evidence.
    """

    player_id: UUID
    sport: Sport
    intent: PlayIntent
    surface: PlayIntentSurface


@dataclass(frozen=True, slots=True)
class ChangeSocialTagsCommand:
    """A player's Social tags, replaced whole (``docs/adr/0179`` §8).

    The ids stay strings for the commit's reason: it is what lets the *domain*
    refuse an id outside the served vocabulary and a count outside the served
    bounds, with the codes a client branches on, rather than a schema layer
    refusing them as a shapeless 422. The You tab's picker is the onboarding
    step reused whole, so the numbers it disables on are the numbers this is
    re-checked against — and a control is not a validation.
    """

    player_id: UUID
    social_tag_ids: Sequence[str]


@dataclass(frozen=True, slots=True)
class ChangePhotosCommand:
    """A player's photographs, replaced whole and **in order**
    (``docs/adr/0179`` §8).

    The sequence the client sent *is* the answer — the first is the one a
    player card shows — and an empty sequence is a real one: a profile may hold
    no photograph, and the poster returns. Each id is checked to exist and to
    be the caller's, against the same port the upload used, exactly as the
    commit checks it.
    """

    player_id: UUID
    photo_ids: Sequence[UUID]


@dataclass(frozen=True, slots=True)
class ChangeIntroCommand:
    """The line a player wrote about themselves, replaced — or withdrawn
    (``docs/adr/0179`` §6).

    A string and not an ``Intro``, for the commit's reason: the fence — the
    cap, the line breaks, the contact rule — is the domain's, and it is the
    domain that refuses with the code and the reason a client branches on.
    ``None`` and a whitespace-only string are both **the withdrawal**, as at
    the commit both are *skipped*: the stream records that the line was taken
    back and the profile folds to none.
    """

    player_id: UUID
    intro: str | None


@dataclass(frozen=True, slots=True)
class ChangeGenderCommand:
    """A new answer to the gender question — *self-declared, freely changed*
    (``docs/adr/0096``, ``docs/adr/0179`` §8).

    An enum, as the commit carries it: a closed set the boundary *selects from*
    rather than constructs, so there is nothing for the domain to refuse that
    the type has not already refused.
    """

    player_id: UUID
    gender: Gender


@dataclass(frozen=True, slots=True)
class ChangeGenderPreferenceCommand:
    """A new durable answer to *who am I willing to play with*
    (``docs/adr/0096`` §3, ``docs/adr/0179`` §8).

    An enum for ``ChangeGenderCommand``'s reason. What narrowing it *does* — it
    makes this player invisible to the excluded side entirely, searchers who
    asked for anybody included — is the client's to say at the moment of
    setting, and the aggregate's event says so.
    """

    player_id: UUID
    gender_preference: GenderPreference

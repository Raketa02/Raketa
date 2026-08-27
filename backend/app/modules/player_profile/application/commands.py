"""Commands into the Player profile context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.modules.player_profile.domain.consent import ConsentSurface
from app.modules.player_profile.domain.gender import Gender, GenderPreference


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
    (``backend/CONTEXT.md`` — *Command*). Availability arrives as
    ``(iso weekday, part of day)`` pairs and the domain is what turns them into
    slots, so nothing in ``presentation/`` builds a value object. The one enum is
    ``ConsentSurface``, which is a closed set the boundary *selects from* rather
    than constructs — the same shape ``CreateAssessmentCommand`` carries
    ``Sport`` in.

    The tag ids stay strings and the radius stays an ``int`` on purpose: it is
    what lets the *domain* refuse an id outside the vocabulary and a radius
    outside the served bounds, with the codes a client branches on, instead of a
    schema layer refusing them as a shapeless 422.

    ``proposals_opt_in`` is ``bool | None`` and the ``None`` is load-bearing.
    Unanswered is neither yes nor no, so a client that has not asked the question
    sends null and is refused; typing it as a required ``bool`` would push that
    refusal into schema validation and lose the code that says *ask the
    question*.

    ``idempotency_key`` is what the client called this commit. The same key twice
    is the same commit — one profile, one answer — which is why a double-tapped
    confirm on a slow connection costs nothing (``docs/adr/0089``).

    ``gender`` and ``gender_preference`` are the second and third enums, and they
    are enums here for ``ConsentSurface``'s reason: each is a closed set the
    boundary *selects from* rather than constructs, so there is nothing for the
    domain to refuse that the type has not already refused. Neither is a string —
    unlike a tag id, whose vocabulary is *served* and can therefore disagree with
    what a client holds.

    **``gender`` has no ``None`` and that is the difference from
    ``proposals_opt_in``.** Both questions are required, and they are required
    differently: the opt-in has a nullable type because *unanswered* is a third
    state a client can legitimately be in and must be refused with a code that
    says *ask the question*. Gender has ``PREFER_NOT_TO_SAY`` — a real answer to
    the same effect — so there is no unanswered state to model and nothing to
    refuse at this layer (``docs/adr/0096``).
    """

    player_id: UUID
    idempotency_key: str
    social_tag_ids: Sequence[str]
    photo_ids: Sequence[UUID]
    #: ``(iso weekday 1–7, part of day)`` — one pair per cell the player ticked.
    availability: Sequence[tuple[int, str]]
    latitude: float
    longitude: float
    search_radius_km: int
    gender: Gender
    gender_preference: GenderPreference
    proposals_opt_in: bool | None
    consent_copy_version: str
    consent_surface: ConsentSurface

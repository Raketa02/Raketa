"""Commands into the Player profile context."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.modules.player_profile.domain.availability import AvailabilitySlot
from app.modules.player_profile.domain.consent import ConsentSurface


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

    **Mostly primitives, deliberately.** The tag ids arrive as strings and the
    radius as an ``int`` so that the *domain* refuses an id outside the
    vocabulary and a radius outside the served bounds — with the codes a client
    branches on — rather than a schema layer refusing them as a shapeless 422.
    Availability is the exception: a day of the week and a part of the day carry
    no served vocabulary and nothing to disagree with, so the boundary builds the
    slots and this command holds them.

    ``proposals_opt_in`` is ``bool | None`` and the ``None`` is load-bearing.
    Unanswered is neither yes nor no, so a client that has not asked the question
    sends null and is refused; typing it as a required ``bool`` would push that
    refusal into schema validation and lose the code that says *ask the
    question*.

    ``idempotency_key`` is what the client called this commit. The same key twice
    is the same commit — one profile, one answer — which is why a double-tapped
    confirm on a slow connection costs nothing (``docs/adr/0089``).
    """

    player_id: UUID
    idempotency_key: str
    social_tag_ids: Sequence[str]
    photo_ids: Sequence[UUID]
    availability: Sequence[AvailabilitySlot]
    latitude: float
    longitude: float
    search_radius_km: int
    proposals_opt_in: bool | None
    consent_copy_version: str
    consent_surface: ConsentSurface

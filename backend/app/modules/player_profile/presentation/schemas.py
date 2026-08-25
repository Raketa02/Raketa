"""Wire schemas for the Player profile context.

Ids and grouping cross the wire; the human-readable label of a tag does not. The
backend emits machine codes and never display text (``docs/adr/0022``), so a
client renders ``STAYS_FOR_A_DRINK`` in its own copy, in its own language.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.player_profile.domain.photos import PresignedPhoto
from app.modules.player_profile.domain.search_radius import SearchRadiusBounds
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
)


class SocialTagResource(BaseModel):
    """One tag, as an id and nothing else — for now.

    An object rather than a bare string deliberately: retiring a tag is
    anticipated (an id is honoured forever and hidden from the picker), and a
    tag that carries a field one day is an addition here, where an array of
    strings would have to change element type — which breaks a shipped client.
    """

    id: SocialTag = Field(..., description="Permanent id, persisted on profiles")


class SocialTagGroupResource(BaseModel):
    """One of the three groups, with its tags in the order they are rendered."""

    group: SocialTagGroup
    tags: list[SocialTagResource]

    @classmethod
    def from_group(
        cls, group: SocialTagGroup, tags: tuple[SocialTag, ...]
    ) -> "SocialTagGroupResource":
        return cls(group=group, tags=[SocialTagResource(id=tag) for tag in tags])


class SearchRadiusBoundsResource(BaseModel):
    """The range a Search radius may take, in whole kilometres.

    The unit is in every field name on purpose: a bare ``minimum`` is one
    refactor away from being read as metres.
    """

    minimum_km: int = Field(..., description="Smallest radius a player may hold")
    maximum_km: int = Field(..., description="Largest radius a player may hold")
    step_km: int = Field(..., description="Granularity — whole kilometres")
    default_km: int = Field(..., description="What the control opens at")

    @classmethod
    def from_bounds(cls, bounds: SearchRadiusBounds) -> "SearchRadiusBoundsResource":
        return cls(
            minimum_km=bounds.minimum_km,
            maximum_km=bounds.maximum_km,
            step_km=bounds.step_km,
            default_km=bounds.default_km,
        )


class PlayerProfileOptionsResponse(BaseModel):
    """Everything a client needs to *render* the profile steps, in one round trip.

    Two facts rather than one endpoint each, because they are the same kind of
    thing — closed, read-only, and needed by the same part of onboarding at the
    same moment.
    """

    social_tag_groups: list[SocialTagGroupResource]
    search_radius: SearchRadiusBoundsResource

    @classmethod
    def from_domain(cls, bounds: SearchRadiusBounds) -> "PlayerProfileOptionsResponse":
        return cls(
            social_tag_groups=[
                SocialTagGroupResource.from_group(group, tags)
                for group, tags in SOCIAL_TAG_VOCABULARY.items()
            ],
            search_radius=SearchRadiusBoundsResource.from_bounds(bounds),
        )


class PhotoResponse(BaseModel):
    """One photo: the id a profile commit will carry, and a URL that reads it.

    The same shape from the upload and from the read, so a client renders a tile
    it has just filled and a tile it is restoring with one code path.

    **The URL is not an identifier and must not be stored as one.** It carries a
    signature and stops working at ``expires_at``; the id is what is permanent.
    """

    photo_id: UUID = Field(
        ..., description="Permanent id — what the profile commit carries"
    )
    url: str = Field(
        ...,
        description=(
            "Short-lived signed URL that reads this photo. Not a stable address: "
            "it is signed for one player, for one window, and there is no public "
            "bucket behind it."
        ),
    )
    expires_at: datetime = Field(
        ...,
        description=(
            "When the URL stops working. Ask for the photo again to get another; "
            "there is no way to extend one."
        ),
    )

    @classmethod
    def from_domain(cls, photo_id: UUID, presigned: PresignedPhoto) -> "PhotoResponse":
        return cls(
            photo_id=photo_id,
            url=presigned.url,
            expires_at=presigned.expires_at,
        )

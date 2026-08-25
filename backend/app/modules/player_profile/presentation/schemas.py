"""Wire schemas for the Player profile context.

Ids and grouping cross the wire; the human-readable label of a tag does not. The
backend emits machine codes and never display text (``docs/adr/0022``), so a
client renders ``STAYS_FOR_A_DRINK`` in its own copy, in its own language.

**The commit's request types are deliberately loose where the domain is strict.**
A tag arrives as a ``str`` and a radius as an ``int``, not as an enum and a
bounded integer, so that an id outside the vocabulary or a radius outside the
served range is refused by the *domain* — with a code a client can branch on and
act from — rather than by schema validation, which can only say that some field
somewhere was wrong. What is constrained here is what has no served vocabulary
to disagree with: a weekday is 1–7 because that is what a weekday is.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import invariant, iso_weekday
from app.modules.player_profile.domain.availability import (
    DAYS_IN_THE_GRID,
    AvailabilityGrid,
    AvailabilitySlot,
    DayPart,
)
from app.modules.player_profile.domain.consent import (
    MAX_COPY_VERSION_LENGTH,
    ConsentSurface,
    ProposalsOptIn,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.photos import PresignedPhoto
from app.modules.player_profile.domain.profile import (
    MAX_PROFILE_PHOTOS,
    PlayerProfile,
)
from app.modules.player_profile.domain.search_radius import SearchRadiusBounds
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
    SocialTagSelectionBounds,
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


class SocialTagSelectionBoundsResource(BaseModel):
    """How many Social tags a selection must hold to be one.

    The unit is in both field names for the reason it is on the radius bounds:
    a bare ``minimum`` beside a list of eighteen tags reads as a count of
    something, and which something is exactly what a client would guess wrong.
    """

    minimum_tags: int = Field(
        ..., description="Fewest tags a player may hold — the picker's floor"
    )
    maximum_tags: int = Field(
        ..., description="Most tags a player may hold — the picker's ceiling"
    )

    @classmethod
    def from_bounds(
        cls, bounds: SocialTagSelectionBounds
    ) -> "SocialTagSelectionBoundsResource":
        return cls(
            minimum_tags=bounds.minimum_tags,
            maximum_tags=bounds.maximum_tags,
        )


class PlayerProfileOptionsResponse(BaseModel):
    """Everything a client needs to *render* the profile steps, in one round trip.

    A handful of facts rather than one endpoint each, because they are the same
    kind of thing — closed, read-only, and needed by the same part of onboarding
    at the same moment.

    **Fields are only ever added.** A shipped mobile app parses this document for
    months after it stops being built, so a new field goes on the end and the
    ones already here keep their names and their types.
    """

    social_tag_groups: list[SocialTagGroupResource]
    search_radius: SearchRadiusBoundsResource
    social_tag_selection: SocialTagSelectionBoundsResource

    @classmethod
    def from_domain(
        cls,
        radius_bounds: SearchRadiusBounds,
        tag_selection_bounds: SocialTagSelectionBounds,
    ) -> "PlayerProfileOptionsResponse":
        return cls(
            social_tag_groups=[
                SocialTagGroupResource.from_group(group, tags)
                for group, tags in SOCIAL_TAG_VOCABULARY.items()
            ],
            search_radius=SearchRadiusBoundsResource.from_bounds(radius_bounds),
            social_tag_selection=SocialTagSelectionBoundsResource.from_bounds(
                tag_selection_bounds
            ),
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


class AvailabilitySlotResource(BaseModel):
    """One ticked cell of the availability grid.

    Two named fields rather than the single joined code the event stream stores.
    The stream's code is a *storage* encoding chosen so a replay folds strings;
    this is a contract a client renders a grid from, and a client that had to
    split ``"3:EVENING"`` would be parsing our persistence format.
    """

    day: int = Field(
        ...,
        ge=1,
        le=DAYS_IN_THE_GRID,
        description="ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.",
    )
    part: DayPart = Field(..., description="Which part of that day")

    def to_domain(self) -> AvailabilitySlot:
        return AvailabilitySlot(day=iso_weekday(self.day), part=self.part)

    @classmethod
    def from_domain(cls, slot: AvailabilitySlot) -> "AvailabilitySlotResource":
        return cls(day=int(slot.day), part=slot.part)


class LocationAreaResource(BaseModel):
    """Where a player plays.

    **What is sent and what is kept are not the same number.** A client sends the
    fix its device gave it; the platform rounds to roughly a kilometre before
    anything is recorded, and it is the rounded pair that comes back here. The
    precise fix is never stored and never shareable
    (``../../../../CONTEXT.md`` — *Location area*).
    """

    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

    @classmethod
    def from_domain(cls, area: LocationArea) -> "LocationAreaResource":
        return cls(latitude=area.latitude, longitude=area.longitude)


class ProposalsOptInRequest(BaseModel):
    """The answer to the proposals question, and the words it was given against.

    ``accepted`` is **nullable and required**, which is the shape of a question
    that has no default. Null means *not answered* and is refused by the commit
    with ``proposals_opt_in_not_answered``; it is not a quiet ``false``, because
    a recorded refusal and an unanswered question are different facts and only
    one of them is consent (``../../../../CONTEXT.md`` — *Skipping is not
    consent*).

    ``copy_version`` identifies the exact wording the player was shown. It is
    required because consent gathered against one sentence is not consent to a
    different one, and a consent record that cannot name its words cannot
    evidence anything.
    """

    accepted: bool | None = Field(
        ...,
        description=(
            "The player's answer. `null` means the question was not answered, "
            "which is refused — it is never read as `false`."
        ),
    )
    copy_version: str = Field(
        ...,
        min_length=1,
        max_length=MAX_COPY_VERSION_LENGTH,
        description=(
            "Identifier of the exact copy the player was shown. Not the copy "
            "itself — the words are the client's and are never stored here."
        ),
    )


class CommitPlayerProfileRequest(BaseModel):
    """Every answer from onboarding's second part, in one body.

    Photos and availability default to empty because both are legitimately
    blank: a player may hold no photos, and **a blank week means "no preference"
    and never "leave me out"**. Nothing else has a default — a location, a
    radius, a tag selection and an answer to the proposals question are all
    things this request must actually carry.
    """

    social_tag_ids: list[str] = Field(
        ...,
        description=(
            "The tag ids this player picked, as served by "
            "`GET /player-profile/options`. The count is re-checked against the "
            "served floor and ceiling, and an id this platform does not serve is "
            "refused with `unknown_social_tag`."
        ),
    )
    photo_ids: list[UUID] = Field(
        default_factory=list,
        description=(
            f"Ids returned by `POST /photos`, in the order the player arranged "
            f"them — the first is the one a player card shows. At most "
            f"{MAX_PROFILE_PHOTOS}; an empty list is valid. Every id is checked "
            f"to exist and to belong to this player."
        ),
    )
    availability: list[AvailabilitySlotResource] = Field(
        default_factory=list,
        description=(
            "The cells of the week this player ticked. **An empty list is a "
            "valid answer** and means no preference — it is never read as "
            "unavailable. Repeated cells are collapsed."
        ),
    )
    location: LocationAreaResource
    search_radius_km: int = Field(
        ...,
        description=(
            "Whole kilometres, re-checked against the range and step served by "
            "`GET /player-profile/options`."
        ),
    )
    proposals_opt_in: ProposalsOptInRequest

    def availability_slots(self) -> list[AvailabilitySlot]:
        return [slot.to_domain() for slot in self.availability]


class ProposalsOptInResponse(BaseModel):
    """The standing answer, and the evidence recorded with it.

    This is the *current* answer. The **history** — every answer this player ever
    gave, against which words and on which surface — is the stream, and nothing
    serves it yet because nothing has asked for it.
    """

    accepted: bool
    copy_version: str = Field(..., description="The copy this answer was given against")
    surface: ConsentSurface = Field(..., description="Where it was answered")
    answered_at: datetime = Field(..., description="When it was answered")

    @classmethod
    def from_domain(cls, opt_in: ProposalsOptIn) -> "ProposalsOptInResponse":
        return cls(
            accepted=opt_in.accepted,
            copy_version=opt_in.copy_version,
            surface=opt_in.surface,
            answered_at=opt_in.answered_at,
        )


class PlayerProfileResponse(BaseModel):
    """A player's profile as it now stands.

    The same body whether the commit created the profile or replayed an earlier
    one, so a client that only wants its profile needs no branch on the status.

    **Fields are only ever added.** A shipped mobile app parses this document for
    months after it stops being built.
    """

    player_id: UUID
    social_tag_ids: list[SocialTag]
    photo_ids: list[UUID]
    availability: list[AvailabilitySlotResource]
    location: LocationAreaResource
    search_radius_km: int
    proposals_opt_in: ProposalsOptInResponse
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "PlayerProfileResponse":
        # A created profile always carries an answer — `PlayerProfile.create`
        # appends `ProposalsOptInAnswered` with the creating event and there is
        # no path to the created state without it. If that ever stops being true
        # this raises here rather than serving a profile with a hole where the
        # consent record should be.
        opt_in = invariant(
            profile.proposals_opt_in,
            f"a committed profile with no opt-in answer: {profile.player_id}",
        )
        return cls(
            player_id=profile.player_id,
            social_tag_ids=list(profile.social_tags.tags),
            photo_ids=list(profile.photo_ids),
            availability=_grid_resource(profile.availability),
            location=LocationAreaResource.from_domain(profile.location),
            search_radius_km=profile.search_radius.kilometres,
            proposals_opt_in=ProposalsOptInResponse.from_domain(opt_in),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


def _grid_resource(grid: AvailabilityGrid) -> list[AvailabilitySlotResource]:
    return [AvailabilitySlotResource.from_domain(slot) for slot in grid.slots]

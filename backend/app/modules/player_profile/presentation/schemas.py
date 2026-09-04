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
to disagree with: a weekday is 1–7 because that is what a weekday is, and
``Gender`` and ``GenderPreference`` are closed sets fixed by ``docs/adr/0096``
that no endpoint publishes and no client can hold a different version of.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport, invariant
from app.modules.player_profile.application.read_player_profile import (
    PlayerProfileSurface,
)
from app.modules.player_profile.domain.availability import (
    DAYS_IN_THE_GRID,
    AvailabilityGrid,
    DayPart,
)
from app.modules.player_profile.domain.consent import (
    MAX_COPY_VERSION_LENGTH,
    ConsentSurface,
    ProposalsOptIn,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.play_intent import (
    PlayIntent,
    PlayIntentSurface,
)
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)
from app.modules.player_profile.domain.photos import (
    PhotoReviewDecision,
    PresignedPhoto,
)
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

    ## The verdict crosses; the evidence does not

    ``review`` is the on-court check's conclusion and it is a **code**, never a
    sentence: the backend emits codes and the client owns the words
    (``docs/adr/0022``). ``review-note`` — the model, the prompt-set fingerprint
    and the raw similarity vector — stays on the object. It is evidence for us
    rather than a fact about the player, and a confidence score on the wire is an
    invitation to a client that renders one.

    **The upload carries it and the read does not**, which is why the field is
    optional and why ``null`` is not ``allowed``. Two reasons, and neither is
    that the read is harder. A warning belongs to the moment a player *chose* a
    photograph; a tile being restored is a photograph they already kept, and
    saying it again is a screen re-litigating a decision the player made. And the
    read would have to pay for it: ``GET /photos/{id}`` proves existence and signs
    a URL, and no part of it looks at what the store holds beside the bytes — the
    verdict is user metadata, which every S3-compatible store answers with a
    request per object. So the shape stays one shape and the tile stays one code
    path, exactly as the paragraph above promises; what differs is whether this
    response has anything to say about the check.

    **The upload can also carry nothing, and that is not the read's ``null``**
    (``docs/adr/0138``). A reviewer that could not be asked concludes nothing, so
    an outage answers ``null`` here rather than ``allowed``: fail-open used to
    spell *nothing to warn about* with the only word it had, and that word now
    means *checked and passed* somewhere else — on a player card, to somebody who
    is not this photograph's owner. Both absences reach a client as *say
    nothing*, which is what makes the collapse safe on this route and the
    distinction load-bearing on the other one.
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

    review: PhotoReviewDecision | None = Field(
        default=None,
        description=(
            "What the on-court check concluded about this photo, or `null` "
            "where this response carries no verdict.\n\n"
            "**`null` is not `allowed`, and it means two different things on "
            "the two routes.** On the upload it is *the reviewer could not be "
            "asked* — our outage, and never a statement about the photograph. "
            "On the read it is *this route does not carry one*, which it never "
            "does. A client that has not been told anything must warn about "
            "nothing, and both readings collapse to that.\n\n"
            "**A warning and nothing else.** `flagged` does not refuse, delete "
            "or hold back a photo: it is stored, it keeps its id, and a profile "
            "commit takes it like any other. The check is wrong sometimes, and "
            "the cost of being wrong is a sentence rather than a signup.\n\n"
            "A code, not copy — the words belong to the client."
        ),
    )

    @classmethod
    def from_domain(
        cls,
        photo_id: UUID,
        presigned: PresignedPhoto,
        *,
        review: PhotoReviewDecision | None = None,
    ) -> "PhotoResponse":
        """The two routes call this differently, and that is the contract.

        The upload passes what the reviewer concluded; the read passes nothing,
        because it has not asked. Defaulting rather than requiring the argument
        would make *no verdict* the thing a caller forgets rather than the thing
        it decides — so the read states its ``None`` by omission at exactly one
        call site, and the class docstring says why.
        """

        return cls(
            photo_id=photo_id,
            url=presigned.url,
            expires_at=presigned.expires_at,
            review=review,
        )


class AvailabilitySlotResource(BaseModel):
    """One ticked cell of the availability grid.

    Two named fields rather than the single joined code the event stream stores.
    The stream's code is a *storage* encoding chosen so a replay folds strings;
    this is a contract a client renders a grid from, and a client that had to
    split ``"3:EVENING"`` would be parsing our persistence format.

    **Every cell, and there is no exception.** The rule was twice read as
    covering only the cells a player *chose* — the one a times rung offers
    (#283), and the week a raised ``KEEP_THESE_TIMES`` quotes back (#286) — on
    the argument that a payload handed back is not a resource. Both crossed as
    codes, and in both cases a client ended up splitting one. What decides this
    is not whose value it is but **what is done with it**: a cell that gets
    drawn on the seven-by-three grid crosses in these two fields, and the engine
    holding it as a code is a fact about the engine. This side of the boundary
    owns the encoding, so this side is where it is read.
    """

    day: int = Field(
        ...,
        ge=1,
        le=DAYS_IN_THE_GRID,
        description="ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.",
    )
    part: DayPart = Field(..., description="Which part of that day")

    def as_cell(self) -> tuple[int, str]:
        """The pair a command carries. **Not a domain value object** — building
        one is the domain's job, not the boundary's (``backend/CONTEXT.md``)."""

        return self.day, self.part.value

    @classmethod
    def from_cell(cls, cell: tuple[int, str]) -> "AvailabilitySlotResource":
        day, part = cell
        return cls(day=day, part=DayPart(part))


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

    **Photos are the only field with a default**, because holding none is a
    legitimate answer to *add some photos*. Everything else is something this
    request must actually carry — a location, a radius, a tag selection, an
    answer to the proposals question, and **a week with something ticked in it**
    (``docs/adr/0102``).

    The week's *floor* is not spelled here, and that is the same decision the tag
    selection's is: an empty list passes this schema and is refused by the domain
    with ``availability_grid_empty``, so the client gets a code it can branch on
    and a recovery it can offer, rather than a 422 that can only say some field
    somewhere was wrong.
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
        ...,
        description=(
            "The cells of the week this player ticked. **At least one of the "
            "twenty-one** — an empty list is refused with "
            "`availability_grid_empty`. The minimum is exactly one and is not "
            "served: it is fixed, so a client holds it as a constant. Repeated "
            "cells are collapsed, and the floor is counted after that."
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
    gender: Gender = Field(
        ...,
        description=(
            "The player's own answer, asked once. Required — `PREFER_NOT_TO_SAY` "
            "is a first-class answer and is what a player who does not want to "
            "say sends; there is no way to send nothing. It matches only "
            "unconstrained searches, which costs its holder reach, and the "
            "client is what says so at the moment of asking."
        ),
    )
    gender_preference: GenderPreference = Field(
        default=DEFAULT_GENDER_PREFERENCE,
        description=(
            "Who this player is willing to be matched with. Optional, and "
            "`ANY` when it is not sent.\n\n"
            "**It is mutual and durable.** It governs what reaches this player "
            "as well as what this player sees, so narrowing it makes them "
            "invisible to the excluded side entirely — including to searchers "
            "who asked for anybody. The client must say so at the moment of "
            "setting; learning it from silence is not acceptable. A single "
            "search may narrow this further and nothing may widen past it."
        ),
    )

    def availability_cells(self) -> list[tuple[int, str]]:
        return [slot.as_cell() for slot in self.availability]


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

    **No gender value comes back out**, and that is a rule rather than an
    oversight (``docs/adr/0096`` §6): a preference crosses the wire *in*, on a
    search; no response shape carries a gender out and no card renders one.
    This body is only ever the caller's own profile, so nothing here would leak
    a third party's answer — the field is left off anyway, because the moment
    one response shape carries it, *which* shapes may is a judgement call made
    per endpoint instead of a line nobody has to re-argue. Nothing reads it back
    today: onboarding sends it once, and there is no profile editor. When one
    exists, adding it here is an addition to this document and ADR-0096's
    ticket's to make.

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
    return [AvailabilitySlotResource.from_cell(cell) for cell in grid.cells]


class PlayerProfileReadResponse(BaseModel):
    """The profile facts the Play screens read, in one round trip.

    **Three facts and not the whole profile**, and the two absences are
    different absences:

    A **standing refusal.** ``gender`` and ``gender_preference`` never come back
    out of this API — the commit route already promises it (``docs/adr/0096``
    §6) and this route does not weaken it.

    A **deferral.** Social tags, photos and the location area are not refused;
    they are **not served yet**, and this is the route they land on when *You* is
    built rather than a route that acquires a sibling. The one worth naming is
    **photos**: a profile may legally hold none, so an absent ``photo_ids`` is
    the single deferral a client could read as *you have none* — which is exactly
    the vanished-row lie ADR-0109 exists to prevent, arriving through the field
    nobody would check. Tags and a location are required at commit, so their
    absence cannot be mistaken for an answer.

    It is prose rather than a machine-readable ``withheld`` list: ADR-0130
    already struck ADR-0109's *and why* half, and a list here would be a field
    whose only reader is a human, on a route where no client ever counted a row
    that could go missing.

    **No ``player_id``.** The resource is ``/players/me``, so the caller is the
    bearer token and echoing it back would be a fourth fact on a body scoped to
    three. ``GET /users/me`` is where an id comes from.

    **Fields are only ever added.** A shipped mobile app parses this document for
    months after it stops being built.
    """

    availability: list[AvailabilitySlotResource] = Field(
        ...,
        description=(
            "The cells of the week this player has ticked, in the platform's "
            "own reading order. **An empty list is a real answer** — a player "
            "may clear their week — and it means *we do not know when they "
            "play*, never *never*."
        ),
    )
    search_radius_km: int = Field(
        ..., description="Whole kilometres. What the search screen's slider opens at."
    )
    play_intents: dict[Sport, PlayIntent] = Field(
        ...,
        description=(
            "What this player declared, per sport. **Only sports they have "
            "declared in appear** — an undeclared sport is absent and is never "
            "a `null` value, because there is no unanswered Play intent "
            "(`NO_PREFERENCE` is an explicit answer).\n\n"
            "*Rated but not yet declared* is a set difference the client "
            "computes against `GET /ratings`, which it is already fetching to "
            "build the sport chips. A search by a player with no declaration "
            "for that sport is refused with `play_intent_not_declared`, so this "
            "is what lets a client open the one-tap interstitial before the "
            "refusal rather than after it."
        ),
    )

    @classmethod
    def from_domain(cls, surface: PlayerProfileSurface) -> "PlayerProfileReadResponse":
        return cls(
            availability=_grid_resource(surface.profile.availability),
            search_radius_km=surface.profile.search_radius.kilometres,
            play_intents=dict(surface.play_intents),
        )


class ChangeAvailabilityRequest(BaseModel):
    """The week, replaced whole.

    **No floor, and that is the difference from the commit.** An empty list is a
    cleared week and is recorded; ``availability_grid_empty`` refuses the answer
    a player is *asked for* at the end of onboarding, not every later edit of it.

    Repeated cells are collapsed rather than refused, and the response carries
    the grid as it was stored — so a client that sent the same cell twice, or
    sent the week in its own order, can see what the profile now holds.
    """

    availability: list[AvailabilitySlotResource] = Field(
        ...,
        description=(
            "Every cell still ticked. **The list is the week** — what is absent "
            "is unticked — and an empty list clears it, which is a legal value "
            "rather than a refusal."
        ),
    )

    def availability_cells(self) -> list[tuple[int, str]]:
        return [slot.as_cell() for slot in self.availability]


class AvailabilityResponse(BaseModel):
    """The week as the profile now holds it.

    A body rather than a ``204`` because the value stored is not always the
    value sent: repeated cells are collapsed and the order is the platform's
    reading order, so a client that kept what it sent would hold a week the
    profile does not.
    """

    availability: list[AvailabilitySlotResource]

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "AvailabilityResponse":
        return cls(availability=_grid_resource(profile.availability))


class ChangeSearchRadiusRequest(BaseModel):
    """The Search radius, replaced whole."""

    search_radius_km: int = Field(
        ...,
        description=(
            "Whole kilometres, re-checked against the range and step served by "
            "`GET /player-profile/options`. Refused with "
            "`search_radius_out_of_bounds` — a disabled slider is not a "
            "validation."
        ),
    )


class SearchRadiusResponse(BaseModel):
    """The radius as the profile now holds it."""

    search_radius_km: int

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "SearchRadiusResponse":
        return cls(search_radius_km=profile.search_radius.kilometres)


class DeclarePlayIntentRequest(BaseModel):
    """What kind of game this player wants in one sport, and where they said so.

    The sport is the path, because it is half the resource's identity: the
    resource is *one player's intent in one sport* (``docs/adr/0094``).
    """

    intent: PlayIntent = Field(
        ...,
        description=(
            "The declaration. `NO_PREFERENCE` is an **explicit answer** and not "
            "an absence — the matcher must be able to tell *either suits me* "
            "from *I never opened that screen*, and nobody is ever backfilled "
            "to it. There is no null."
        ),
    )
    surface: PlayIntentSurface = Field(
        ...,
        description=(
            "Which screen this was declared on. Required, because the client is "
            "the only party that knows — and safe to take its word for, because "
            "nothing branches on it: it is context recorded beside the fact, "
            "never a thing a decision reads."
        ),
    )


class PlayIntentDeclarationResponse(BaseModel):
    """The standing declaration for one player in one sport.

    The **surface is not served back**. It is recorded beside the fact for us,
    and a response that carried it would invite a client to render *where you
    last said this*, which is a fact about the app and not about the player.
    """

    sport: Sport
    intent: PlayIntent

    @classmethod
    def from_domain(
        cls, declaration: PlayIntentDeclaration
    ) -> "PlayIntentDeclarationResponse":
        return cls(sport=declaration.sport, intent=declaration.intent)

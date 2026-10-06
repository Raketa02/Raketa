"""Wire schemas for the Player profile context.

Ids and grouping cross the wire; the human-readable label of a tag does not. The
backend emits machine codes and never display text (``docs/adr/0022``), so a
client renders ``STAYS_FOR_A_DRINK`` in its own copy, in its own language.

**The commit's request types are deliberately loose where the domain is strict.**
A tag arrives as a ``str``, not as an enum, so that an id outside the vocabulary
is refused by the *domain* — with a code a client can branch on and
act from — rather than by schema validation, which can only say that some field
somewhere was wrong. What is constrained here is what has no served vocabulary
to disagree with: a weekday is 1–7 because that is what a weekday is, and
``Gender`` and ``GenderPreference`` are closed sets fixed by ``docs/adr/0096``
that no client can hold a different version of — published on exactly one
route, the owner's own profile read (``docs/adr/0179`` §4), and no other.

**An omitted field is not a null one** on the profile read. ``OMITTED`` fields
are absent from the JSON, and the difference is the contract's own: *absent*
means the field does not apply to this profile — no intro was written, nobody
looked at this photograph, the gender question did not exist when this profile
was committed — and ``null`` would mean it applies and the answer is a measured
nothing. Nothing on that read is ever nulled.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.kernel import Sport
from app.modules.player_profile.application.read_player_profile import (
    PlayerProfileSurface,
)
from app.modules.player_profile.domain.gender import (
    DEFAULT_GENDER_PREFERENCE,
    Gender,
    GenderPreference,
)
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS
from app.modules.player_profile.domain.location import (
    MAXIMUM_LATITUDE,
    MAXIMUM_LONGITUDE,
    MINIMUM_LATITUDE,
    MINIMUM_LONGITUDE,
    LocationArea,
)
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
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_VOCABULARY,
    SocialTag,
    SocialTagGroup,
    SocialTagSelectionBounds,
)
from app.modules.player_profile.domain.weekly_hours import (
    DAYS_IN_THE_GRID,
    FIRST_HOUR,
    LAST_HOUR,
    WeeklyHours,
)

#: The default that spells **omitted** — the same sentinel the shortlist's and
#: the record's schemas use, spelled here rather than imported for the reason
#: each of them spells its own: a context declares its own presentation
#: vocabulary, and it is one line.
#:
#: A field carrying it is not in the schema's ``required`` list, so it generates
#: as ``field?: T``, and the profile read is declared
#: ``response_model_exclude_unset=True`` so it is genuinely absent from the JSON
#: rather than present as ``null``. It is typed ``Any`` so the field keeps its
#: own non-nullable type: a field annotated ``T | None`` *and* defaulted would
#: generate as ``field?: T | null`` and say neither thing.
OMITTED: Any = None


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


class SocialTagSelectionBoundsResource(BaseModel):
    """How many Social tags a selection must hold to be one.

    The unit is in both field names: a bare ``minimum`` beside a list of
    nineteen tags reads as a count of something, and which something is exactly
    what a client would guess wrong.
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
    ones already here keep their names and their types. ``search_radius`` is the
    one removal, with the radius itself (#581), made while no build had shipped
    anywhere but ``local``.
    """

    social_tag_groups: list[SocialTagGroupResource]
    social_tag_selection: SocialTagSelectionBoundsResource

    @classmethod
    def from_domain(
        cls,
        tag_selection_bounds: SocialTagSelectionBounds,
    ) -> "PlayerProfileOptionsResponse":
        return cls(
            social_tag_groups=[
                SocialTagGroupResource.from_group(group, tags)
                for group, tags in SOCIAL_TAG_VOCABULARY.items()
            ],
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
    response has anything to say about the check. Where the owner reads what
    **stands** beside each of their photographs is the profile read's ``photos``
    list (`ProfilePhotoResource`, ``docs/adr/0179`` §8) — the one screen whose
    question is the check's answer, paying that request for at most three
    objects rather than per tile.

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


class WeeklyHourResource(BaseModel):
    """One ticked hour of the week — a day, and the hour its cell starts at.

    Two named fields rather than the single joined code the event stream stores.
    The stream's code is a *storage* encoding chosen so a replay folds strings;
    this is a contract a client renders a grid from, and a client that had to
    split ``"3:19"`` would be parsing our persistence format.

    **Every cell, and there is no exception.** The rule was twice read as
    covering only the cells a player *chose* — the one a times rung offers
    (#283), and the week a raised ``KEEP_THESE_TIMES`` quotes back (#286) — on
    the argument that a payload handed back is not a resource. Both crossed as
    codes, and in both cases a client ended up splitting one. What decides this
    is not whose value it is but **what is done with it**: a cell that gets
    drawn on the seven-by-sixteen grid crosses in these two fields, and the engine
    holding it as a code is a fact about the engine. This side of the boundary
    owns the encoding, so this side is where it is read.
    """

    day: int = Field(
        ...,
        ge=1,
        le=DAYS_IN_THE_GRID,
        description="ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.",
    )
    hour: int = Field(
        ...,
        ge=FIRST_HOUR,
        le=LAST_HOUR,
        description=(
            "The hour the cell starts at, wall clock — 19 is 19:00 to 20:00. The "
            "week runs 07:00 to 23:00, so the first cell is 7 and the last is 22."
        ),
    )

    def as_cell(self) -> tuple[int, int]:
        """The pair a command carries. **Not a domain value object** — building
        one is the domain's job, not the boundary's (``backend/CONTEXT.md``)."""

        return self.day, self.hour

    @classmethod
    def from_cell(cls, cell: tuple[int, int]) -> "WeeklyHourResource":
        day, hour = cell
        return cls(day=day, hour=hour)


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


class CommitPlayerProfileRequest(BaseModel):
    """Every answer from onboarding's second part, in one body.

    **Photos and the intro are the fields with a default**, because holding no
    photograph is a legitimate answer to *add some photos* and writing nothing
    is a legitimate answer to *say it in your own words* (``docs/adr/0170``).
    Everything else is something this request must actually carry — a
    location, a tag selection, a gender answer, and **a week with something
    ticked in it** (``docs/adr/0102``).

    The week's *floor* is not spelled here, and that is the same decision the tag
    selection's is: an empty list passes this schema and is refused by the domain
    with ``weekly_hours_empty``, so the client gets a code it can branch on
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
    weekly_hours: list[WeeklyHourResource] = Field(
        ...,
        description=(
            "The hours of the week this player ticked. **At least one of the "
            "112** — an empty list is refused with `weekly_hours_empty`. The "
            "minimum is exactly one and is not served: it is fixed, so a client "
            "holds it as a constant. Repeated hours are collapsed, and the floor "
            "is counted after that."
        ),
    )
    location: LocationAreaResource
    gender: Gender = Field(
        ...,
        description=(
            "The player's own answer, asked once. Required — `PREFER_NOT_TO_SAY` "
            "is a first-class answer and is what a player who does not want to "
            "say sends; there is no way to send nothing. It matches only "
            "unconstrained preferences, which costs its holder reach, and the "
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
    intro: str | None = Field(
        default=None,
        # **No `max_length` here, deliberately** — the same decision the tag
        # selection makes. A schema cap would refuse a 101-character line as a
        # shapeless 422; the domain refuses it as `intro_not_admitted` with
        # `reason: too_long`, which is the code a client branches on.
        description=(
            "One line about yourself — your **intro** — or nothing. Optional: "
            "a player who skips the step sends nothing (or `null`, or "
            "whitespace, which is the same), and has no intro rather than an "
            f"empty one.\n\n"
            f"Trimmed, then held to **at most {INTRO_MAX_CHARACTERS} "
            "characters** and **one line**, in any language. Refused with "
            "`intro_not_admitted` and one coarse `details.reason` — "
            "`too_long`, `multiline`, or `contains_contact` for a phone "
            "number, an email, a URL or bare domain, or an `@handle` — so the "
            "client can say what to change without the server explaining what "
            "it matched. Nothing else is read.\n\n"
            "Edited later from the You tab through `PUT /players/me/intro`, "
            "with the tags and the photos it sits between (ADR-0179 §6). It "
            "crosses on the player card and on the record, and this response "
            "does not echo it."
        ),
    )

    def weekly_hours_cells(self) -> list[tuple[int, int]]:
        return [hour.as_cell() for hour in self.weekly_hours]


class PlayerProfileResponse(BaseModel):
    """A player's profile as it now stands.

    The same body whether the commit created the profile or replayed an earlier
    one, so a client that only wants its profile needs no branch on the status.

    **No gender value comes back out of this body**, and that is a rule rather
    than an oversight (``docs/adr/0096`` §6): a preference crosses the wire
    *in*, on a write; no response that describes one player to another carries
    a gender out and no card renders one. This body is only ever the caller's
    own profile, so nothing here would leak a third party's answer — the field
    is left off anyway, because *which* shapes may carry it is a line rather
    than a judgement made per endpoint, and the line is **exactly one shape**:
    the owner's own read, ``PlayerProfileReadResponse`` (``docs/adr/0179`` §4).
    The profile editor that reads it back is the You tab, and it reads that
    route; the commit's answer stays what it was.

    **Fields are only ever added.** A shipped mobile app parses this document for
    months after it stops being built. ``weekly_hours`` is the one replacement,
    of the part-of-day ``availability`` it succeeded (``docs/adr/0189`` §5), and
    ``search_radius_km`` and ``proposals_opt_in`` the two removals (#581), each
    made while no build had shipped anywhere but ``local``.
    """

    player_id: UUID
    social_tag_ids: list[SocialTag]
    photo_ids: list[UUID]
    weekly_hours: list[WeeklyHourResource]
    location: LocationAreaResource
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "PlayerProfileResponse":
        return cls(
            player_id=profile.player_id,
            social_tag_ids=list(profile.social_tags.tags),
            photo_ids=list(profile.photo_ids),
            weekly_hours=_weekly_hours_resource(profile.weekly_hours),
            location=LocationAreaResource.from_domain(profile.location),
            created_at=profile.created_at,
            updated_at=profile.updated_at,
        )


def _weekly_hours_resource(week: WeeklyHours) -> list[WeeklyHourResource]:
    return [WeeklyHourResource.from_cell(cell) for cell in week.cells]


class ProfilePhotoResource(BaseModel):
    """One of the owner's photographs, and what the on-court check said about it.

    **The same words as ``PhotoResponse``** — ``photo_id`` and ``review``, the
    same code under the same name — so a client keys a tile from this list and
    from ``GET /photos/{id}`` by one id and reads one vocabulary, even though the
    two shapes spell *no verdict* differently (there ``null``, here omitted).
    What differs is which route carries the verdict: the upload says it at
    the moment the photograph was chosen (``docs/adr/0133``), the per-photo read
    says nothing, and this list says what **stands** — because the You tab's
    photos row is the one screen whose question is *what did the check conclude
    about mine*, and a warning a player was shown once at upload has to be
    findable again on the screen that lets them change the answer.

    Three answers and only two values (``docs/adr/0138``): ``allowed``,
    ``flagged``, and **omitted** for *nobody looked*. Omitted is not
    ``allowed`` — a photograph that arrived while the reviewer was unreachable,
    or before the check existed, has had nothing concluded about it, and a
    client that drew a tick on the absence would be claiming a check happened.
    ``flagged`` blocks nothing: the photo is stored, it is shown, and the check
    is wrong sometimes.
    """

    photo_id: UUID = Field(
        ..., description="Permanent id — what a photos write carries"
    )
    review: PhotoReviewDecision = Field(
        default=OMITTED,
        description=(
            "What the on-court check concluded about this photograph, or "
            "**omitted** where nobody looked.\n\n"
            "**Omitted is not `allowed`.** Three answers, not two: checked and "
            "passed, checked and flagged, and *nobody looked* — a photo that "
            "arrived while the reviewer could not be reached, or before the "
            "check existed. This is the owner's own reading of the verdict the "
            "upload showed them once; `GET /photos/{id}` deliberately carries "
            "none. `flagged` blocks nothing — the photo is stored and shown, "
            "and the check is wrong sometimes. The evidence behind the verdict "
            "never crosses on any route."
        ),
    )


class PlayerProfileReadResponse(BaseModel):
    """Every fact a player declared, in one round trip — what the Play screens
    read and, since ``docs/adr/0179``, what the You tab draws its rows from.

    **The gender and the preference are served here, and on no other shape.**
    ADR-0096 §6's *no response shape carries a gender value out* is about
    responses that describe one player to another, and its walk still refuses
    both words on every one of those. A player reading their own answer on a
    route scoped to ``me`` is not what that rule protects, and a screen that
    asks *who should we match you with* with nothing pre-selected is a screen a
    player cannot trust (``docs/adr/0179`` §4). ``gender`` is **omitted** on a
    profile committed before the question existed — never ``PREFER_NOT_TO_SAY``,
    which is an answer a player gives.

    **The one thing still withheld is the location area**, and nothing stands
    in for it: a profile cannot be committed without an area, so a
    ``has_location`` could never be false, and a branch nobody can take is a
    branch nobody tests.

    Absence has one spelling here and it is **omission** (``OMITTED``): an intro
    never written, a photograph nobody looked at, a gender never asked. The one
    absence that is served rather than omitted is **an empty ``photos`` list**,
    because a profile may legally hold none and that is a real answer.

    **No ``player_id``.** The resource is ``/players/me``, so the caller is the
    bearer token and echoing it back would say nothing. ``GET /users/me`` is
    where an id comes from.

    **Fields are only ever added.** A shipped mobile app parses this document for
    months after it stops being built. ``weekly_hours`` is the one replacement,
    of the part-of-day ``availability`` it succeeded (``docs/adr/0189`` §5), and
    ``search_radius_km`` and ``proposals_opt_in`` the two removals (#581), each
    made while no build had shipped anywhere but ``local``.
    """

    weekly_hours: list[WeeklyHourResource] = Field(
        ...,
        description=(
            "The hours of the week this player has ticked, in the platform's "
            "own reading order — day, then hour. **An empty list is a real "
            "answer** — a player may clear their week — and it means *we do not "
            "know when they play*, never *never*."
        ),
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
            "build the sport chips, and it is what lets a client open the "
            "one-tap interstitial for a sport still undeclared."
        ),
    )
    social_tags: list[SocialTag] = Field(
        ...,
        description=(
            "The Social tag ids this player holds, **in the vocabulary's "
            "order** whatever order the picker sent them in. Required at "
            "commit, so never empty and never absent."
        ),
    )
    photos: list[ProfilePhotoResource] = Field(
        ...,
        description=(
            "The photographs, **in the player's order** — the first is the "
            "profile photo — each with the verdict its uploader is owed. "
            "**An empty list is a real answer**: a profile may hold none, and "
            "the client draws the generated court poster."
        ),
    )
    intro: str = Field(
        default=OMITTED,
        # No `max_length`: the cap binds the write and not the read. A line the
        # profile holds was admitted when it was written, and a response schema
        # that refused it after the cap moved would take the tab down for a
        # fact the platform recorded.
        description=(
            "The line this player wrote about themselves, as recorded, or "
            "**omitted** where none was written. Never an empty string "
            "(`docs/adr/0170`)."
        ),
    )
    gender: Gender = Field(
        default=OMITTED,
        description=(
            "The owner's own answer to the gender question. **Served here and "
            "on no other response shape** (`docs/adr/0179` §4) — what one "
            "player is told about another never carries it.\n\n"
            "**Omitted** on a profile committed before the question existed, "
            "and never read as `PREFER_NOT_TO_SAY`, which is an answer a "
            "player gives: a client pre-selects nothing rather than something."
        ),
    )
    gender_preference: GenderPreference = Field(
        ...,
        description=(
            "Who the owner is willing to be matched with — their own setting, "
            "served here and on no other response shape (`docs/adr/0179` §4). "
            "Always present: it defaults to `ANY` at commit, so there is "
            "nothing for its absence to mean."
        ),
    )

    @classmethod
    def from_domain(cls, surface: PlayerProfileSurface) -> "PlayerProfileReadResponse":
        profile = surface.profile
        fields: dict[str, Any] = {
            "weekly_hours": _weekly_hours_resource(profile.weekly_hours),
            "play_intents": dict(surface.play_intents),
            "social_tags": list(profile.social_tags.tags),
            "photos": [
                _profile_photo(photo_id, surface.photo_verdicts.get(photo_id))
                for photo_id in profile.photo_ids
            ],
            "gender_preference": profile.gender_preference,
        }
        if profile.intro is not None:
            # Omitted where nothing was written, never `""` (`docs/adr/0170`).
            fields["intro"] = profile.intro.text
        if profile.gender is not None:
            # Absent stays absent: a stream from before the question folds to
            # `None`, and serving a value would claim an answer nobody gave.
            fields["gender"] = profile.gender
        return cls.model_validate(fields)


def _profile_photo(
    photo_id: UUID, review: PhotoReviewDecision | None
) -> ProfilePhotoResource:
    # `review` is left **unset** rather than passed as `None`, which is what
    # `response_model_exclude_unset=True` reads as *omit*.
    fields: dict[str, Any] = {"photo_id": photo_id}
    if review is not None:
        fields["review"] = review
    return ProfilePhotoResource.model_validate(fields)


class SetWeeklyHoursRequest(BaseModel):
    """The weekly hours, replaced whole — *Save your week*.

    **No floor, and that is the difference from the commit.** An empty list is a
    cleared week and is recorded; ``weekly_hours_empty`` refuses the answer a
    player is *asked for* at the end of onboarding, not every later edit of it.

    Repeated hours are collapsed rather than refused, and the response carries
    the week as it was stored — so a client that sent the same hour twice, or
    sent the week in its own order, can see what the profile now holds.
    """

    weekly_hours: list[WeeklyHourResource] = Field(
        ...,
        description=(
            "Every hour still ticked. **The list is the week** — what is absent "
            "is unticked — and an empty list clears it, which is a legal value "
            "rather than a refusal."
        ),
    )

    def weekly_hours_cells(self) -> list[tuple[int, int]]:
        return [hour.as_cell() for hour in self.weekly_hours]


class WeeklyHoursResponse(BaseModel):
    """The weekly hours as the profile now holds them.

    A body rather than a ``204`` because the value stored is not always the
    value sent: repeated hours are collapsed and the order is the platform's
    reading order, so a client that kept what it sent would hold a week the
    profile does not.
    """

    weekly_hours: list[WeeklyHourResource]

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "WeeklyHoursResponse":
        return cls(weekly_hours=_weekly_hours_resource(profile.weekly_hours))


class ChangeLocationRequest(BaseModel):
    """The phone's fix, on a cold start.

    **What is sent is never what is kept.** The client sends the fix its device
    gave it, with the accuracy onboarding used; the platform rounds it to the
    cell about a kilometre across before anything is recorded, exactly as the
    commit does, and a fix that rounds to the cell already stored records
    nothing (``docs/adr/0174`` §6). Nothing comes back: no route on this
    surface serves the area yet — the profile read grows the field when *You*
    is built — and a silent write on every launch is not the one to start.

    The bounds are the world's, as they are on the commit's ``location`` —
    read from the value object rather than spelled again. A fix outside them
    is a broken reading and not a place, refused at the boundary rather than
    rounded into a cell at the pole.
    """

    latitude: float = Field(..., ge=MINIMUM_LATITUDE, le=MAXIMUM_LATITUDE)
    longitude: float = Field(..., ge=MINIMUM_LONGITUDE, le=MAXIMUM_LONGITUDE)


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


class ChangeSocialTagsRequest(BaseModel):
    """The Social tags, replaced whole (``docs/adr/0179`` §8).

    Strings rather than an enum, as the commit carries them: an id outside the
    served vocabulary is refused by the domain with ``unknown_social_tag``, a
    count outside the served bounds with ``social_tag_selection_out_of_bounds``,
    and the client gets a code it can act on rather than a 422.
    """

    social_tags: list[str] = Field(
        ...,
        description=(
            "Every tag this player now holds, as ids served by "
            "`GET /player-profile/options`. **The list is the selection** — what "
            "is absent is dropped. Re-checked against the served vocabulary and "
            "the served floor and ceiling exactly as the commit re-checks them; "
            "the same id twice is refused with `duplicate_social_tag`."
        ),
    )


class SocialTagsResponse(BaseModel):
    """The tags as the profile now holds them — in the vocabulary's order.

    A body rather than a ``204`` for the week's reason: the order stored is the
    platform's and not the picker's, so a client that kept what it sent would
    hold a selection in an order the profile does not.
    """

    social_tags: list[SocialTag] = Field(
        ..., description="In the vocabulary's order, whatever order was sent."
    )

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "SocialTagsResponse":
        return cls(social_tags=list(profile.social_tags.tags))


class ChangePhotosRequest(BaseModel):
    """The photographs, replaced whole and **in order** (``docs/adr/0179`` §8).

    An empty list is a legal value and clears: a profile may hold none, and the
    poster returns. There is no *clear my photos* flag for the week's reason —
    the list is the answer.
    """

    photo_ids: list[UUID] = Field(
        ...,
        description=(
            f"Ids returned by `POST /photos`, in the order the player arranged "
            f"them — the first is the one a player card shows. At most "
            f"{MAX_PROFILE_PHOTOS}; **an empty list is valid and clears**. Every "
            f"id is checked to exist and to belong to this player, exactly as the "
            f"commit checks it, and the same id twice is refused with "
            f"`duplicate_photo`."
        ),
    )


class PhotosResponse(BaseModel):
    """The photographs as the profile now holds them, in their order.

    Ids and nothing else: the verdict beside each is the profile read's to
    serve (`ProfilePhotoResource`), paid for once there rather than on every
    rearrangement here.
    """

    photo_ids: list[UUID]

    @classmethod
    def from_domain(cls, profile: PlayerProfile) -> "PhotosResponse":
        return cls(photo_ids=list(profile.photo_ids))


class ChangeIntroRequest(BaseModel):
    """The line, replaced — or withdrawn (``docs/adr/0179`` §6).

    **The field is required and nullable**, which is the shape of a value whose
    absence is a real act: ``null`` withdraws the line, and ``{}`` is a 422 so
    that a client which forgot the field cannot be clearing lines. No
    ``max_length``, for the commit's reason: the cap is the domain's, and the
    domain refuses with `intro_not_admitted` and `reason: too_long`, which is
    the code a client branches on.

    **Nothing comes back.** The intro reaches the card, the record and its
    author's own profile read and nowhere else — a sweep in ``tests/unit/
    test_intro.py`` holds the contract to those three shapes — and a response
    that echoed the trimmed line would be a fourth. The author reads it back
    from the profile read, as the two gender writes are read back.
    """

    intro: str | None = Field(
        ...,
        description=(
            "The new line, or `null` to withdraw it. Trimmed, then held to "
            f"**at most {INTRO_MAX_CHARACTERS} characters** and **one line** — "
            "the commit's fence exactly, with the commit's codes: "
            "`intro_not_admitted` and one coarse `details.reason`, `too_long`, "
            "`multiline`, or `contains_contact` for a phone number, an email, a "
            "URL or bare domain, or an `@handle`. Whitespace is `null`: a line "
            "with nothing in it is withdrawn, never stored empty."
        ),
    )


class ChangeGenderRequest(BaseModel):
    """A new answer to the gender question — *self-declared, freely changed*."""

    gender: Gender = Field(
        ...,
        description=(
            "The player's own answer. `PREFER_NOT_TO_SAY` is a first-class "
            "answer; it matches only unconstrained preferences, which costs its "
            "holder reach, and the client is what says so at the moment of "
            "asking (`docs/adr/0096`)."
        ),
    )


class ChangeGenderPreferenceRequest(BaseModel):
    """A new durable answer to *who am I willing to play with*."""

    gender_preference: GenderPreference = Field(
        ...,
        description=(
            "Who this player is willing to be matched with.\n\n"
            "**It is mutual and durable.** Narrowing it makes them invisible to "
            "the excluded side entirely — including to searchers who asked for "
            "anybody — and the client must say so at the moment of setting; "
            "learning it from silence is not acceptable. Seats already accepted "
            "are facts, not candidates: nothing already agreed is undone."
        ),
    )

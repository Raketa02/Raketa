"""The profile surface reads and writes: one read, one `PUT` per fact.

A player edits two facts here that a Play screen once edited — the weekly hours
and the per-sport Play intent — and the second is ADR-0094's
`PUT /api/v1/play-intents/{sport}`, next door. The search screen these routes
were first written for, and the prompts it raised (`KEEP_THESE_TIMES`,
`KEEP_THIS_RADIUS`), went with the searches (#579); the search radius went with
the ranking that read it (#581). The You tab edits the same facts through the
same writes.

**One `PUT` per fact, unkeyed, and deliberately not a `PATCH`.** Three arguments
converge and the third is decisive:

1. **The shape is already fixed** for the third changeable fact in this same
   context — ADR-0094's unkeyed `PUT`, where *"the resource is one player's
   intent in one sport, the same request twice lands the same state, and the
   no-op rule means the second appends nothing."* Two write shapes in one context
   is the thing worth avoiding.
2. **Each fact is changed by exactly one write.** The weekly hours by one, the
   tags by another. A partial update would exist to serve a caller that does
   not exist.
3. **`null` versus absent is fatal on the week specifically.** A blank week is a
   **legal value** — `set_weekly_hours` accepts one deliberately — so
   `PATCH {"weekly_hours": null}` would mean both *leave my week alone* and
   *clear my week*, and the second is a real thing a player does. This is not a
   general dislike of `PATCH`; it is that this field has a legal empty value and
   the ambiguity therefore bites.

**No `Idempotency-Key`.** `profile_routes.py` argues one for the **creating**
commit — *"the request a player makes once, at the end of six steps, on whatever
connection they have"* — and a `PUT` that lands the same state twice has nothing
to deduplicate.

**The read is the You tab's too, and it grew rather than acquiring a sibling**
(``docs/adr/0179`` §8). It was scoped to what the Play screens edit and promised
that the deferred facts — tags, photos, the intro — would land on
this same route when *You* was built, and that is what happened: one read now
carries every fact a player declared, and the tab draws every row's live line
from it. Two of them are served to the owner and to nobody else — the gender and
the preference, the one shape ADR-0096 §6's fence admits (ADR-0179 §4), and the
contract walk asserts it is the only one.

**And the five writes those rows need are here, on this surface's argument**
(ADR-0179 §8): the tags, the photos, the intro, the gender and the preference —
one unkeyed `PUT` per fact, each the aggregate's own transition, so that every
transition under *Later changes, from the profile screen* now has the route it
was written for. Three of them ADR-0170
§5 held back until they could ship together — the intro, the tags and the
photos, so that no field is editable while the two beside it are frozen — and
this is that day. Each answers **the fact as stored** where that differs from
what was sent (the tags in the vocabulary's order) and the photos with their ids
in order; **the two gender writes and the intro's
answer `204`**, because *served on one route and no other* (§4) and *the card,
the record and its author* (ADR-0170 §3) are sentences about response shapes,
and a write must not become one more. The refusals are the commit's, under the
commit's codes: a control is not a validation, and the picker on the tab is the
onboarding step reused whole.

**The location is the exception, and it is not You's — it is the cold start's**
(``docs/adr/0174`` §6). No screen edits it and no prompt asks for it: the client
re-reads the phone's position on every cold start and on return from the
background after more than a day, and puts it here silently. It is an unkeyed
`PUT` for the others' reason, and the same-cell no-op is what makes a write on
every launch free. It answers `204` and no body, and **the read
does not serve the area either, nor a flag for it**: a profile cannot be
committed without one, so `has_location` could never be false, and the tab
branches on the phone's permission state instead.

**And the reliability filter is written here too** (``docs/adr/0195`` §6,
#661): a preference beside the gender preference, a clause of the same pair
rule, so the same aggregate holds it. It answers `204` like the preference, and
is read back on the player's own record, beside how many players in their groups
it hides — never on the profile read.

**And *Show me to new people*** (``docs/adr/0204`` §2, #791): the switch on
*On your card*, `PUT /players/me/show-me-to-new-people`, `{on}`, `204`. Unlike
the filter it **is** read back on the profile read, as `show_me_to_new_people`,
because the You tab draws its row from that read.
"""

from __future__ import annotations

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.player_profile.application.commands import (
    ChangeGenderCommand,
    ChangeGenderPreferenceCommand,
    ChangeIntroCommand,
    ChangeLocationCommand,
    ChangePhotosCommand,
    ChangeSocialTagsCommand,
    SetShowMeToNewPeopleCommand,
    SetReliabilityMinimumCommand,
    SetWeeklyHoursCommand,
)
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS
from app.modules.player_profile.presentation.dependencies import (
    ChangeGenderDep,
    ChangeGenderPreferenceDep,
    ChangeIntroDep,
    ChangeLocationDep,
    ChangePhotosDep,
    ChangeSocialTagsDep,
    ReadPlayerProfileDep,
    SetShowMeToNewPeopleDep,
    SetReliabilityMinimumDep,
    SetWeeklyHoursDep,
)
from app.modules.player_profile.presentation.schemas import (
    ChangeGenderPreferenceRequest,
    ChangeGenderRequest,
    ChangeIntroRequest,
    ChangeLocationRequest,
    ChangePhotosRequest,
    ChangeSocialTagsRequest,
    PhotosResponse,
    PlayerProfileReadResponse,
    SetShowMeToNewPeopleRequest,
    SetReliabilityFilterRequest,
    SetWeeklyHoursRequest,
    SocialTagsResponse,
    WeeklyHoursResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/players/me", tags=["player-profile"])

_NO_PROFILE = {
    "model": ErrorResponse,
    "description": (
        "`player_profile_not_found` — this player has not finished onboarding's "
        "second part. The recovery is that part, which `GET /users/me` already "
        "sends a cold launch into."
    ),
}

#: Every write here appends to the profile's stream, so every one can lose a
#: version race — the same 409 the creating commit documents, on the same
#: aggregate. Stated here rather than left to be discovered, because a status a
#: route can return and the contract does not list is a branch no generated
#: client has.
_LOST_THE_RACE = {
    "model": ErrorResponse,
    "description": (
        "`concurrent_modification` — two writes reached this player's profile "
        "and this one lost. Retry: the retry reads the winner, and lands the "
        "same state or nothing."
    ),
}


@router.get(
    "/profile",
    response_model=PlayerProfileReadResponse,
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: _NO_PROFILE},
    summary="Every fact this player declared — what the Play screens and You read",
    description=(
        "One read for everything a player declared, across the two aggregates "
        "that own it: the week and the per-sport Play intent the Play screens "
        "edit, and — since the *You* tab — the tags, the photos with their "
        "verdicts, the intro, and the owner's own gender and preference. The "
        "one fact a Play screen still needs from elsewhere — **which sports "
        "am I rated in** — is `GET /api/v1/ratings` and is not re-served "
        "here.\n\n"
        "**`play_intents` holds only what was declared.** An undeclared sport is "
        "absent, never `null`: `NO_PREFERENCE` is an explicit answer, so there "
        "is no unanswered value to send. *Rated but undeclared* is a set "
        "difference against `GET /ratings`, and it is what a client uses to open "
        "the declaration interstitial for a sport still undeclared.\n\n"
        "**An empty `weekly_hours` is a real answer.** A player may clear their "
        "week; it means *we do not know when they play* and never *never*. "
        "**An empty `photos` list is one too**: a profile may hold none.\n\n"
        "**Absent means omitted, never `null`.** `intro` is omitted where no "
        "line was written; a photo's `review` is omitted where nobody looked — "
        "which is not `allowed`; `gender` is omitted on a profile committed "
        "before the question existed — which is not `PREFER_NOT_TO_SAY`.\n\n"
        "## Who is told what\n\n"
        "**`gender` and `gender_preference` are withheld from everybody but "
        "their owner.** No response that describes one player to another "
        "carries either — not a card, not a record, not a seat — and that "
        "walk is asserted over the whole emitted contract. This route is the "
        "one shape that carries them, to the person who set them, so the "
        "screen that asks *who should we match you with* can open on the "
        "answer already given (`docs/adr/0179` §4).\n\n"
        "**The location area is not served, and neither is a flag for it.** "
        "A profile cannot be committed without an area, so `has_location` "
        "could never be false; the tab branches on the phone's permission "
        "state, which is the device's."
    ),
)
async def read_player_profile(
    user: CurrentUserDep,
    use_case: ReadPlayerProfileDep,
) -> PlayerProfileReadResponse:
    return PlayerProfileReadResponse.from_domain(await use_case.execute(user.id))


@router.put(
    "/weekly-hours",
    response_model=WeeklyHoursResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's weekly hours — Save your week",
    description=(
        "The whole week, every time — the list **is** the week, and what is "
        "absent from it is unticked. An hour is a day and the hour its cell "
        "starts at, 7 to 22: the week runs 07:00 to 23:00. Unkeyed and safe to "
        "send twice: the same week twice lands the same state, and a transition "
        "that changes nothing records nothing.\n\n"
        "**An empty list is a legal value and clears the week.** The floor of "
        "one ticked hour binds the *commit*, which is the answer a player is "
        "asked for at the end of onboarding, and not every later edit of it. A "
        "cleared week is read as *absent* by the matcher, never as a zero — "
        "silence is never scored (`docs/adr/0102`).\n\n"
        "Repeated hours are collapsed and the response carries the week as "
        "stored, in the platform's reading order — so a client can see what the "
        "profile now holds rather than assuming it kept what was sent.\n\n"
        "It replaced `PUT /players/me/availability`, whose week was mornings, "
        "afternoons and evenings (`docs/adr/0189` §5)."
    ),
)
async def set_weekly_hours(
    payload: SetWeeklyHoursRequest,
    user: CurrentUserDep,
    use_case: SetWeeklyHoursDep,
) -> WeeklyHoursResponse:
    profile = await use_case.execute(
        SetWeeklyHoursCommand(
            player_id=user.id,
            weekly_hours=payload.weekly_hours_cells(),
        )
    )
    return WeeklyHoursResponse.from_domain(profile)


@router.put(
    "/location",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`location_club_unknown` — the club picked in place of a "
                "reading is no club in Rakieta (`details.field` `club_id`). "
                "Nothing moves."
            ),
        },
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary=(
        "Move this player's Location area to where the phone is — or to a "
        "club picked in its place"
    ),
    description=(
        "**The cold start's write.** The client re-reads the "
        "phone's position on every cold start and on return from the "
        "background after more than 24 hours — never merely on foreground — "
        "with the accuracy onboarding used, and puts it here silently. A "
        "revoked permission sends nothing: the stored area stays.\n\n"
        "**Or a club, from *You › Where you play*** (`docs/adr/0200` §10). A "
        "player who refused the phone's location sends a `club_id` in place of "
        "the reading — exactly one of the two, never both — and the club's "
        "point, rounded to the cell, is their area. The phone never needs the "
        "club's coordinates. Nothing records which it was, so the next reading "
        "in another cell replaces a club-picked area.\n\n"
        "**What is sent is never what is kept.** The fix — or the club's "
        "point — is rounded to the "
        "cell about a kilometre across before anything is recorded, exactly as "
        "the profile commit rounds it, so the precise fix never reaches the "
        "platform's records. A move that rounds to the cell already stored "
        "records nothing and still answers `204` — which is what makes a write "
        "on every launch free, and why there is no `Idempotency-Key`.\n\n"
        "**Nothing else moves.** A trip is a trip: whatever reads the area "
        "reads the new cell — and nothing is reset. "
        "`204` and no body: no route on this surface serves the area yet, and "
        "a silent write on every launch is not the one to start."
    ),
)
async def change_location(
    payload: ChangeLocationRequest,
    user: CurrentUserDep,
    use_case: ChangeLocationDep,
) -> None:
    await use_case.execute(
        ChangeLocationCommand(player_id=user.id, location=payload.as_source())
    )


@router.put(
    "/social-tags",
    response_model=SocialTagsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`unknown_social_tag` — an id this platform does not serve; "
                "re-read `GET /player-profile/options`.\n\n"
                "`social_tag_selection_out_of_bounds` — too few or too many "
                "tags for the served floor and ceiling.\n\n"
                "`duplicate_social_tag` — the same tag id arrived twice.\n\n"
                "The commit's three refusals under the commit's codes: the "
                "picker on the tab is the onboarding step reused, and a "
                "control is not a validation."
            ),
        },
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's Social tags",
    description=(
        "The whole selection, every time — the list **is** the selection, and "
        "what is absent from it is dropped. Unkeyed and safe to send twice: "
        "the same selection twice lands the same state, and a transition that "
        "changes nothing records nothing.\n\n"
        "**Re-validated exactly as the commit re-validates** — against the "
        "served vocabulary and the served floor and ceiling — so the tab's "
        "picker and onboarding's cannot disagree about what a selection may "
        "be (`docs/adr/0179` §6).\n\n"
        "The response carries the tags **in the vocabulary's order**, which is "
        "what the profile read serves and what a card draws, so a client can "
        "see what the profile now holds rather than assuming it kept the order "
        "it sent. The next read of their record shows the new tags."
    ),
)
async def change_social_tags(
    payload: ChangeSocialTagsRequest,
    user: CurrentUserDep,
    use_case: ChangeSocialTagsDep,
) -> SocialTagsResponse:
    profile = await use_case.execute(
        ChangeSocialTagsCommand(player_id=user.id, social_tag_ids=payload.social_tags)
    )
    return SocialTagsResponse.from_domain(profile)


@router.put(
    "/photos",
    response_model=PhotosResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`too_many_photos` / `duplicate_photo` — the list is not one a "
                "profile may hold."
            ),
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ErrorResponse,
            "description": (
                "`player_profile_not_found` — this player has not finished "
                "onboarding's second part.\n\n"
                "`photo_not_found` — a photo id that does not exist, or belongs "
                "to another player. The two answer the same way deliberately, "
                "and it is the commit's check through the commit's port."
            ),
        },
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's photographs, in order",
    description=(
        "The whole list, every time, **in the order the player arranged it** — "
        "the first is the one a player card shows, so promoting the second "
        "photograph is a change even though the set is the same. Unkeyed and "
        "safe to send twice: the same order twice records nothing.\n\n"
        "**An empty list is a legal value and clears.** A profile may hold no "
        "photograph; the poster returns on the card, and the photographs let "
        "go of become what the uncommitted-photo sweep collects.\n\n"
        "**Photos write on every change** (`docs/adr/0179`): a player "
        "rearranging three photographs sends three of these, each idempotent, "
        "and the last one is the state — the row is the truth and a draft of it "
        "would be a second one. The verdict beside each photograph is the "
        "profile read's to serve, not this response's."
    ),
)
async def change_photos(
    payload: ChangePhotosRequest,
    user: CurrentUserDep,
    use_case: ChangePhotosDep,
) -> PhotosResponse:
    profile = await use_case.execute(
        ChangePhotosCommand(player_id=user.id, photo_ids=payload.photo_ids)
    )
    return PhotosResponse.from_domain(profile)


@router.put(
    "/intro",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`intro_not_admitted` — the line is not one the platform "
                "admits, with one coarse `details.reason`: `too_long` (over "
                f"{INTRO_MAX_CHARACTERS} characters after trimming), "
                "`multiline` (a line break), or `contains_contact` (a phone "
                "number, an email, a URL or bare domain, or an `@handle`). The "
                "commit's fence exactly; "
                "refused before anything is stored, and the server never says "
                "what it matched."
            ),
        },
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Replace this player's intro — or withdraw it",
    description=(
        "**The day ADR-0170 §5 deferred to** (`docs/adr/0179` §6): the intro "
        "becomes editable with the tags and the photos, as one piece of work. "
        "The line is trimmed and fenced exactly as the commit fences it, and "
        "the fence is contact — nothing else is read.\n\n"
        "**`null` withdraws the line.** The stream records that it was taken "
        "back and the profile folds to none — the same absence a player who "
        "skipped the step has, which the profile read spells by omission. "
        "Whitespace is `null`. The field is required, so `{}` is a 422: "
        "withdrawing has to be said.\n\n"
        "**`204` and no body.** The intro reaches the card, the record and its "
        "author's own profile read and nowhere else (`docs/adr/0170` §3), and "
        "the write does not become a fourth shape: read the line as stored — "
        "trimmed — back from `GET /players/me/profile`, as the two gender "
        "writes are read back.\n\n"
        "Unkeyed and safe to send twice: the same line twice records nothing, "
        "and so does withdrawing a line that was never written. The next read "
        "of their record shows the new line — or none."
    ),
)
async def change_intro(
    payload: ChangeIntroRequest,
    user: CurrentUserDep,
    use_case: ChangeIntroDep,
) -> None:
    await use_case.execute(ChangeIntroCommand(player_id=user.id, intro=payload.intro))


@router.put(
    "/gender",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Correct this player's answer to the gender question",
    description=(
        "*Self-declared, freely changed* (`docs/adr/0096`): a value a player "
        "may not correct is a value the platform has ruled on, which is the "
        "one thing this field is not. Unkeyed; an unchanged value records "
        "nothing, and a first answer on a profile committed before the "
        "question existed is a change and records one.\n\n"
        "**`204` and no body, deliberately.** The owner's own profile read is "
        "the one response shape that carries a gender value out "
        "(`docs/adr/0179` §4), and the contract walk holds it to being the "
        "only one; the write answers nothing rather than becoming a second. "
        "Read the answer back from `GET /players/me/profile`.\n\n"
        "The mutual gate reads the new answer live, the next time the proposer, "
        "the fill or a rescue asks it of a pair."
    ),
)
async def change_gender(
    payload: ChangeGenderRequest,
    user: CurrentUserDep,
    use_case: ChangeGenderDep,
) -> None:
    await use_case.execute(
        ChangeGenderCommand(player_id=user.id, gender=payload.gender)
    )


@router.put(
    "/gender-preference",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Change who this player is willing to play with",
    description=(
        "A new durable answer to *who am I willing to play with* "
        "(`docs/adr/0096` §3). Unkeyed; an unchanged value records "
        "nothing.\n\n"
        "**It is mutual and durable, and narrowing it has an effect the "
        "player must be told about at the moment of setting**: they become "
        "kept off courts with the excluded side entirely — including with "
        "players who asked for anybody. The client says so from a reason code; "
        "learning it "
        "from silence is not acceptable. Seats already accepted are facts, not "
        "candidates: nothing already agreed is undone.\n\n"
        "**`204` and no body**, for the gender write's reason: the setting is "
        "served on the owner's profile read and on no other shape "
        "(`docs/adr/0179` §4). It is read live, in both directions, the next "
        "time the proposer, the fill or a rescue asks it of a pair."
    ),
)
async def change_gender_preference(
    payload: ChangeGenderPreferenceRequest,
    user: CurrentUserDep,
    use_case: ChangeGenderPreferenceDep,
) -> None:
    await use_case.execute(
        ChangeGenderPreferenceCommand(
            player_id=user.id, gender_preference=payload.gender_preference
        )
    )


@router.put(
    "/reliability-filter",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Play only with players of at least High or Medium reliability",
    description=(
        "The Player reliability screen's switch (`docs/adr/0195` §6, #661): "
        "*Play only with players of at least High reliability*, *at least "
        "Medium*, or off. Unkeyed; an unchanged value records nothing.\n\n"
        "**One more clause of the pair rule, asked both ways and from then on**: "
        "a pair is unfit when either player's minimum is above the other's band, "
        "and **New passes every minimum** — on the deal, the deck, posts, *Seat "
        "open* and Fill in, and the details. **Yeses already given stand**, a "
        "player who drops below it keeps theirs, and booked games never "
        "change.\n\n"
        "**`204` and no body**: the setting is read back on `GET "
        "/players/me/record`, with how many players in this player's groups it "
        "hides."
    ),
)
async def set_reliability_filter(
    payload: SetReliabilityFilterRequest,
    user: CurrentUserDep,
    use_case: SetReliabilityMinimumDep,
) -> None:
    await use_case.execute(
        SetReliabilityMinimumCommand(player_id=user.id, minimum=payload.minimum)
    )


@router.put(
    "/show-me-to-new-people",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: _NO_PROFILE,
        status.HTTP_409_CONFLICT: _LOST_THE_RACE,
    },
    summary="Show me to new people",
    description=(
        "The switch on *On your card* (`docs/adr/0204` §2): *Players you don't "
        "share a group or a game with can find you on Home, open your record "
        "and send you a request.* On by default; written at once, with no "
        "Save; an unchanged value records nothing.\n\n"
        "**Off**: anybody you share no group, no game and no friendship with "
        "reads your record as *not available* and can't send you a request — "
        "from the next tap, with nothing to wait for. Your place in the ranking "
        "never moves, a request already sent stays open, and you still see "
        "everybody and may ask anybody yourself.\n\n"
        "**`204` and no body**: the switch is read back on "
        "`GET /players/me/profile`, as `show_me_to_new_people`."
    ),
)
async def set_show_me_to_new_people(
    payload: SetShowMeToNewPeopleRequest,
    user: CurrentUserDep,
    use_case: SetShowMeToNewPeopleDep,
) -> None:
    await use_case.execute(
        SetShowMeToNewPeopleCommand(player_id=user.id, on=payload.on)
    )

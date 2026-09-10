"""The five plan routes: read yours, set each of the three slots, and agree it.

**One route per slot, because ADR-0144 has three events** and *setting a slot and
moving one are the same event told with two sentences*. A single
``PUT /plans/{game_id}`` carrying a partial body would collapse three facts into
one write and make the room's three lines a thing the server had to infer from
which keys were present.

**``PUT``, because a slot is a value that is set rather than a thing that
happens.** The same value twice lands the same state and records nothing, which
is what the verb already promises. **The lock takes the same verb for the same
promise about an act**: locking a plan that is already locked lands the same
state and records nothing (``docs/adr/0155``).

**There is no route that creates a plan and none that destroys one.** A plan is
born by being used — the first slot write is its birth — and it is never unmade:
there is no cancellation, because ``games`` opens one game per arrangement for
ever and nobody turning up is a game that ghosts rather than a plan that was
withdrawn.

**The lock is an act, and it freezes nothing** (``docs/adr/0155``). ADR-0144
refused it because the only thing it did — ownership, and a booking — was out of
scope; it has a destination now, and the destination is a **system line in the
room**, so every member sees that the plan was agreed rather than merely
completed. What it is not: it is not the slot count under another name, it does
not freeze a slot, and there is no route that undoes it. Any member may still
move any slot afterwards, and each move writes its own line as it always did.

**There is no per-game plan read.** ``GET /plans`` is the only one, and it is a
list beside ``GET /games`` rather than a field on it: the plan cannot ride on
``GameSchema`` without ``games`` importing the Plan, and a per-game read would be
an N+1 across the whole of Now (``docs/adr/0148`` §7).
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.plans.application.commands import (
    LockThePlanCommand,
    ReadPlansCommand,
    SetDayCommand,
    SetHourCommand,
    SetPlaceCommand,
)
from app.modules.plans.domain.plan import Plan
from app.modules.plans.domain.slots import as_wall_time
from app.modules.plans.presentation.dependencies import (
    LockThePlanDep,
    ReadPlansDep,
    SetDayDep,
    SetHourDep,
    SetPlaceDep,
)
from app.modules.plans.presentation.schemas import (
    PlanListResponse,
    PlanSchema,
    SetDayRequest,
    SetHourRequest,
    SetPlaceRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/plans", tags=["plans"])

#: `plan_is_history`, spelled once because three of the four write routes have to
#: say it **inside a 409 that also carries something else** — a moment that has
#: gone, for two of the slots, and a plan that is not complete, for the lock. A
#: response code carries one description and a client reads it whole, so the two
#: cannot be two entries — one would silently overwrite the other, and the
#: refusal that disappeared would be the one nothing in the contract mentioned.
_THE_GAME_IS_OVER = (
    "`plan_is_history` — the game left its entry window, so its slots are "
    "frozen. **That is the only thing that freezes them, and locking is not "
    "it**: a locked plan is still fully editable by any member. Once *we "
    "played* can no longer be said, the plan is a note about an evening that "
    "is over."
)

#: What every write here refuses, and it is the same list on all four because
#: the refusals are about **the game** rather than about what was sent — the
#: port's one question, and the hold. The lock takes it whole: *a hold refuses a
#: lock exactly as it refuses a slot write*, because both write a line other
#: people read.
_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`account_held` — your account is under a live hold. **A hold stops "
            "you writing anywhere another player sees it, and never stops you "
            "reading**: `GET /plans` stays open to you, because a hold must not "
            "erase an arrangement other people are already inside."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": (
            "`plan_not_found` — **one code for two cases**: there is no game "
            "with that id, or there is one and you were not on its court. They "
            "are not told apart on purpose, because a 403 would answer *is this "
            "id real* about four strangers' evening."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": _THE_GAME_IS_OVER,
    },
}

#: The 409 the **two slots that can name a moment** answer with, and it carries
#: both codes rather than one. It replaces `_REFUSALS`' 409 outright — a mapping
#: has one entry per status — so `plan_is_history` is repeated here rather than
#: assumed: a description that said *everything above* would be pointing at an
#: entry this one had just overwritten.
#:
#: **The place route may not advertise the second code.** A note about a venue
#: names no instant, so it is a refusal that route cannot return and a client
#: branch that would never be reached.
_A_MOMENT_THAT_HAS_GONE: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            _THE_GAME_IS_OVER
            + "\n\n"
            + "`that_moment_has_already_passed` — the day and the hour together "
            "name a moment that has gone. **Raised when the second of the two is "
            "filled, in either order**, and it names neither: the platform has "
            "no opinion about which one is wrong, so change whichever you meant."
        ),
    },
}

#: The 409 the **lock** answers with, and like `_A_MOMENT_THAT_HAS_GONE` it
#: carries both codes rather than one. A mapping has one entry per status, so
#: `plan_is_history` is repeated here rather than assumed — one of the two would
#: otherwise silently overwrite the other, and the refusal that disappeared would
#: be the one nothing in the contract mentioned.
#:
#: **The two are the same status for opposite reasons**: one is a plan there is
#: nothing left to agree about, the other a plan there is not yet enough to agree
#: on. Both are the state of the plan rather than anything that was sent, which
#: is why neither is a `400`.
_A_PLAN_THAT_CANNOT_BE_AGREED: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            _THE_GAME_IS_OVER
            + "\n\n"
            + "`the_plan_is_not_complete` — a slot is still empty. **A refusal "
            "and not a silent `200`**, which is deliberately the opposite shape "
            "from locking a plan that is already locked: a no-op here would "
            "leave you believing you had agreed one. It is a conflict rather "
            "than a `400` because the request carried nothing at all — what is "
            "wrong is the state of the plan."
        ),
    },
}


@router.get(
    "",
    response_model=PlanListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "Every plan for the games you are on the court of, newest "
                "arrangement first."
            )
        },
    },
    summary="Your plans",
    description=(
        "**A plan is one game's, and this is the only plan read.** Join it "
        "against `GET /games` by `game_id` — the plan is not a field on a game, "
        "because a game is a record of an evening and a plan is an agreement "
        "about a future, and the two contexts do not read each other.\n\n"
        "**A game with nothing agreed is absent from this list.** *No plan* is "
        "what it draws, and it is one spelling: a plan is born by being used, so "
        "there is no empty row for a game nobody has arranged anything on "
        "yet.\n\n"
        "**There is no `read_at` here, deliberately.** A plan folds nothing "
        "against the clock — its day and hour are wall-clock facts, drawn "
        "literally and never counted down — so there is no instant for it to "
        "have been folded against. Fold the card against `GET /games`' "
        "`read_at`, which keeps every clock on that screen the same one.\n\n"
        "**`agreed_point` is derived and sent**: the agreed instant when the day "
        "and the hour are both recorded, the start of the following local day "
        "when only the day is, and `null` when no day is."
    ),
)
async def read_plans(
    user: CurrentUserDep,
    use_case: ReadPlansDep,
) -> PlanListResponse:
    found = await use_case.execute(ReadPlansCommand(reader_id=user.id))
    return PlanListResponse(plans=[_plan(one) for one in found])


@router.put(
    "/{game_id}/place",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The plan as it now stands."},
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`the_place_is_empty` — nothing but whitespace. **A slot is "
                "never emptied**, so a blank value is not a way of clearing "
                "one.\n\n"
                "`the_place_is_too_long` — past the cap. **Refused, never "
                "truncated.**"
            ),
        },
        **_REFUSALS,
    },
    summary="Set where you are meeting",
    description=(
        "**Any member may fill or change any slot, any number of times.** There "
        "is no lock and no rate limit — every change writes a system line naming "
        "who and what, and **the line is the friction**.\n\n"
        "**Writing the value already there records nothing and answers `200`.** "
        "Without that the room fills with *Tomek set the place* three times "
        "over.\n\n"
        "**This is a note and never a court.** No id, no lookup, no "
        "autocomplete, no reuse, no geocode — and nothing anywhere reads it. One "
        "club will be spelled four ways and nothing will notice, which is what "
        "refusing a venue record costs."
    ),
)
async def set_place(
    game_id: UUID,
    payload: SetPlaceRequest,
    user: CurrentUserDep,
    use_case: SetPlaceDep,
) -> PlanSchema:
    return _plan(
        await use_case.execute(
            SetPlaceCommand(
                game_id=game_id, player_id=user.id, place=payload.place
            )
        )
    )


@router.put(
    "/{game_id}/day",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The plan as it now stands."},
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`the_day_is_past_the_horizon` — past this game's planning "
                "window. The days a client offers are clamped to the same bound "
                "and shrink as the week runs out; **inside the entry grace there "
                "is no day left to set at all**, and the only act remaining is "
                "*We played*."
            ),
        },
        **_REFUSALS,
        **_A_MOMENT_THAT_HAS_GONE,
    },
    summary="Set the day you are playing",
    description=(
        "**A local day in the platform's one zone**, so one arrangement reads "
        "the same on every phone in it.\n\n"
        "**Clamped to the game's own horizon**, which is what keeps a plan from "
        "naming a day on which *we played* can no longer be said — and what "
        "leaves every plannable day at least twenty-four hours to say it.\n\n"
        "**Writing the day already there records nothing and answers `200`.**"
    ),
)
async def set_day(
    game_id: UUID,
    payload: SetDayRequest,
    user: CurrentUserDep,
    use_case: SetDayDep,
) -> PlanSchema:
    return _plan(
        await use_case.execute(
            SetDayCommand(game_id=game_id, player_id=user.id, day=payload.day)
        )
    )


@router.put(
    "/{game_id}/hour",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The plan as it now stands."},
        status.HTTP_400_BAD_REQUEST: {
            "model": ErrorResponse,
            "description": (
                "`the_hour_is_not_offered` — outside the grid, between two of "
                "its steps, or carrying seconds. **Bounded chips the platform "
                "offered, never a free instant**: the grid a client draws is a "
                "convention, and this refusal is what makes it true."
            ),
        },
        **_REFUSALS,
        **_A_MOMENT_THAT_HAS_GONE,
    },
    summary="Set the time you are playing",
    description=(
        "**The hour is the agreement, not a guess at a booking.** Nothing on "
        "this platform will ever hold a court, so nothing can ever contradict "
        "it — there is no un-agreeing to fear, only re-agreeing, and any member "
        "may do that at any time.\n\n"
        "**Thirty-minute steps between 06:00 and 23:00, validated here.**\n\n"
        "**Writing the hour already there records nothing and answers `200`.**"
    ),
)
async def set_hour(
    game_id: UUID,
    payload: SetHourRequest,
    user: CurrentUserDep,
    use_case: SetHourDep,
) -> PlanSchema:
    return _plan(
        await use_case.execute(
            SetHourCommand(game_id=game_id, player_id=user.id, hour=payload.hour)
        )
    )


@router.put(
    "/{game_id}/lock",
    response_model=PlanSchema,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"description": "The plan as it now stands."},
        **_REFUSALS,
        **_A_PLAN_THAT_CANNOT_BE_AGREED,
    },
    summary="Agree the plan",
    description=(
        "**We are agreed.** Any member may lock, once all three slots are "
        "set — and locking is an **act** rather than a fourth slot: a complete "
        "plan is one everybody *could* agree, and this says somebody did. It "
        "writes a system line into the room, which is the whole of what it "
        "does.\n\n"
        "**It takes no body.** The value is the three slots and they are already "
        "recorded; sending one back would be the second place that fact is "
        "true.\n\n"
        "**A locked plan is not a frozen one.** Any member may still move any "
        "slot afterwards, the plan stays locked, and every move writes its own "
        "line — there is no un-agreeing to fear, only re-agreeing. **The game "
        "leaving its entry window is still the only thing that freezes a "
        "slot.**\n\n"
        "**There is no unlock**, for the same reason a slot is never emptied: "
        "the lock is a thing that happened.\n\n"
        "**Locking a plan that is already locked answers `200` and records "
        "nothing**, and the first lock's `locked_at` is the one that stands."
    ),
)
async def lock_the_plan(
    game_id: UUID,
    user: CurrentUserDep,
    use_case: LockThePlanDep,
) -> PlanSchema:
    return _plan(
        await use_case.execute(
            LockThePlanCommand(game_id=game_id, player_id=user.id)
        )
    )


def _plan(plan: Plan) -> PlanSchema:
    """One plan, as its own court reads it.

    **Nothing is re-gated against who is asking.** The four fail-closed gates
    decided who may be introduced, and everybody who can reach a plan was on a
    court somebody already agreed to be on.

    The hour crosses as a clock face and is stored as a minute of the local day;
    the conversion is the domain's own inverse, so the wire and the room's system
    line cannot come to two spellings of 18:00.
    """

    return PlanSchema(
        game_id=plan.game_id,
        place=plan.place.value if plan.place is not None else None,
        day=plan.day,
        hour=as_wall_time(plan.hour) if plan.hour is not None else None,
        agreed_point=plan.agreed_point,
        locked_at=plan.locked_at,
    )

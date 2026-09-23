"""The two sportsmanship routes: which cards are waiting, and answering one.

**There is no route that reads a rating back.** Not the subject's, not the
rater's own, not as a list, not as a count, not as *you rated Karol four stars in
August*. The average and the number of people behind it reach a reader on the
player record; the answers themselves reach nobody, and there is no shape on this
surface they could arrive in.

**There is no route that amends one.** Submitting closes the card, and a blank
stays blank for ever — including the card where everything was left blank, which
is an explicit *I am not rating anyone* and is an answer like any other.

**There is no penalty behind any of this.** Ignoring the card costs nothing:
there is no strand for rating, nothing is recorded about the omission, and the
card simply expires.

**Nothing is re-gated against anybody.** The four fail-closed gates decide who
may be *introduced*, and an evening you were both at is not an introduction —
``docs/adr/0095`` §7 settled that a block is forward-looking and does not reach
into a game already agreed. There is a second reason here that is this route's
own: a block that stopped somebody rating you would make blocking the way to
dodge a bad rating, and everybody who had just played badly would reach for it.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, status

from app.core.exception_handlers import ErrorResponse
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import StarsGiven
from app.modules.sportsmanship.presentation.dependencies import (
    AnswerTheCardDep,
    ReadTheOpenCardsDep,
)
from app.modules.sportsmanship.presentation.schemas import (
    AnswerTheCardRequest,
    OpenCardSchema,
    OpenCardsResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/sportsmanship", tags=["sportsmanship"])

_REFUSALS: dict[int | str, dict[str, Any]] = {
    status.HTTP_400_BAD_REQUEST: {
        "model": ErrorResponse,
        "description": (
            "`they_were_not_on_this_court` — stars for somebody who was not "
            "there, **including yourself**. You rate everybody else on the "
            "court and nobody else.\n\n"
            "`you_rated_the_same_person_twice` — one card carries one answer "
            "about each player. Refused rather than collapsed, because "
            "collapsing means the platform picking which of your two opinions "
            "to keep.\n\n"
            "`stars_are_one_to_five` — whole stars, one to five. There is no "
            "zero and there are no halves."
        ),
    },
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`this_game_is_not_yours_to_rate` — no settled game of **yours** "
            "has that id. **One code for three cases** — it does not exist, you "
            "did not play in it, or its result has not settled — because they "
            "have one remedy and separating them would answer *is this id real* "
            "about four strangers' evening."
        ),
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`you_have_already_rated_this_game` — the card is closed. It closed "
            "when you answered it, whatever you put on it, and there is no way "
            "to reopen it."
        ),
    },
}


@router.get(
    "",
    response_model=OpenCardsResponse,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "description": (
                "The courts still waiting for your stars, **soonest to expire "
                "first**. An empty list is the ordinary answer."
            )
        },
    },
    summary="Cards waiting for your stars",
    description=(
        "**A card appears the day after the game and stays for seven days.** "
        "Not on the evening itself — an answer given ten minutes after losing "
        "badly is not the answer this is for — and not for ever, because a card "
        "nobody is obliged to answer can only accumulate.\n\n"
        "**A game is on this list only once it is over**: the score is agreed, "
        "or both sides put one up and neither gave way. A game nobody ever said "
        "was played never appears at all — there is nobody to rate for an "
        "evening that did not happen.\n\n"
        "**Answering removes it, whatever you put on it.** Submitting closes the "
        "card for ever, including the card you answered with everybody left "
        "blank.\n\n"
        "**Absence is the only reason given.** A game not yet a day old, one "
        "whose week has run out and one you have already answered are all simply "
        "not here — and none of them is something to draw differently.\n\n"
        "**Ids only.** Join `game_id` against `/api/v1/games` for the names, "
        "the sport and the date; `players` is everybody else who was on that "
        "court, in the line-up's own order.\n\n"
        "**Ignoring all of this costs nothing.** There is no strand for rating, "
        "no penalty, and nothing is recorded about a card that expired."
    ),
)
async def read_the_open_cards(
    user: CurrentUserDep,
    use_case: ReadTheOpenCardsDep,
) -> OpenCardsResponse:
    return OpenCardsResponse(
        cards=[
            OpenCardSchema(game_id=court.game_id, players=list(court.others))
            for court in await use_case.execute(user.id)
        ]
    )


@router.post(
    "/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": (
                "Answered, and the card is closed. **Nothing is returned, and "
                "nothing ever will be** — there is no route through which an "
                "individual rating reaches anybody, including the person who "
                "gave it and the person it is about."
            )
        },
        **_REFUSALS,
    },
    summary="Rate the players you played",
    description=(
        "**Everybody from one game, answered together.** In doubles that is "
        "three people — both opponents *and* your partner, because the person "
        "who saw you play closest was on your own side of the net. In singles "
        "it is the one opponent.\n\n"
        "**Anybody may be left blank**: leave them out of `ratings`. Sending an "
        "empty `ratings` answers the card without rating anybody, which is an "
        "answer and closes it.\n\n"
        "**Submitting closes it for ever.** A second request is refused, a blank "
        "stays blank, and there is no correction path — so ask before you send.\n\n"
        "**Only your most recent rating of a given person counts.** Rating "
        "somebody again after another game replaces what you said last time "
        "rather than adding to it, so partners who play every week cannot "
        "inflate each other by volume.\n\n"
        "**A low rating feeds the average and nothing else.** It does not pass, "
        "hide or block, and it will not stop you being matched with that person "
        "again. `POST /api/v1/passes` and `POST /api/v1/blocks` are the controls "
        "that do those things, and both are meant to be deliberate.\n\n"
        "**Nobody is told, and no individual answer is ever shown to anybody.** "
        "What reaches every reader — the person you rated included — is an "
        "average out of five beside how many different people it rests on, "
        "over their fifty most recent raters (ADR-0179 §5)."
    ),
)
async def answer_the_card(
    game_id: UUID,
    payload: AnswerTheCardRequest,
    user: CurrentUserDep,
    use_case: AnswerTheCardDep,
) -> None:
    await use_case.execute(
        AnswerTheCardCommand(
            game_id=game_id,
            rater_id=user.id,
            # The domain value object is constructed here rather than in the use
            # case, which is where the range refusal fires. It is still the
            # domain's rule doing the refusing — there is one copy of it, and
            # the wire deliberately declares a plain integer so there cannot be
            # a second.
            given=tuple(
                StarsGiven(subject_id=one.player_id, stars=one.stars)
                for one in payload.ratings
            ),
        )
    )

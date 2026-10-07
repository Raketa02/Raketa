"""Situations: one press sets the stage for one mechanic, and the rows play it
out (``docs/adr/0194`` §4; #590 builds the first two).

**A situation goes through the same use cases a request runs** — the proposer
the job runs, the yes a phone's swipe runs — so it can never leave a state the
app could not reach. **The server's clock is never moved**: everything here
happens at the real *now*, and a situation that needs history writes it on the
seed's backdated clock (the later ones, #591–#593). **It obeys the rules**:
pressed twice it may meet *games per week* or *one game per hour*, and the
answer is the domain's refusal; a fresh store is ``make down-v && make up &&
make seed``.

1. **Fresh deal** — the proposer, now, for the group: what the sweep would deal
   it on its next run, dealt at once.
2. **Needs her yes · Instant club** — a game the protagonist's yes fills: a card
   of hers at a club that books at once, which her deck shows — one with
   ``TIME_TO_ANSWER`` left before its book-by where there is one — and enough of
   the people dealt it beside her In — three in padel — that hers is the last. When
   no card of hers can be, the proposer deals first, as *Fresh deal* does; when
   none can be still, the situation says so rather than inventing one.

**The protagonist is the phone**: the account the tester holds, never acted as
— but a seed account all the same, since it is her deck the situation shapes.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from app.api.dependencies import ClockDep, UserRepositoryDep
from app.api.dev.accounts import holds_a_seed_account, refuse_unless_a_seed_account
from app.api.dev.board import PersonRef, the_group
from app.api.dev.dependencies import (
    ClubTermsDep,
    PlayerNamesDep,
    ProposeGamesDep,
    SavedMethodsDep,
)
from app.core.exception_handlers import ErrorResponse
from app.kernel import Instant, Sport, hours, instant, invariant
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.groups.presentation.dependencies import GroupDirectoryDep
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.domain.ports import (
    ClubTerms,
    ProposalDirectory,
    ProposalRepository,
    SavedMethods,
)
from app.modules.proposals.domain.proposal import Proposal
from app.modules.proposals.presentation.dependencies import (
    ProposalClubNamesDep,
    ProposalDirectoryDep,
    ProposalRepositoryDep,
    ReadGroupDeckDep,
    SayYesDep,
)
from app.modules.users.domain.ports import UserRepository
from app.shared.domain.errors import ConflictError

router = APIRouter(prefix="/situations", tags=["dev"])

#: How long before its book-by a card a situation leaves needing her yes should
#: still be — enough to pick the phone up and say it. A card with less is taken
#: only when no other can be, and the situation says when her yes is due.
TIME_TO_ANSWER = timedelta(hours=2)


class SituationUnavailable(ConflictError):
    """The situation cannot be set up in this store as it stands — said in
    words, because nothing here invents a game the app would not have made."""

    code = "situation_unavailable"


# --------------------------------------------------------------------------- #
# The wire
# --------------------------------------------------------------------------- #


class FreshDealRequest(BaseModel):
    group_id: UUID


class ProposedSchema(BaseModel):
    """What the proposer's run did, as the job counts it."""

    made: int = Field(description="Picks it made.")
    dealt: int = Field(description="Versions it dealt on games already filling.")
    lost: int = Field(description="Cards it found had lost their court hour.")
    redealt: int = Field(description="Turned-down games whose people it re-dealt.")
    refused: int = Field(description="Acts the world had moved past.")


class FreshDealResponse(BaseModel):
    proposed: ProposedSchema
    says: str = Field(description="What happened, for the tester.")


class NeedsHerYesRequest(BaseModel):
    group_id: UUID
    sport: Sport
    protagonist_id: UUID = Field(
        description="Whose phone it is — the yes the game is left needing."
    )


class NeedsHerYesResponse(BaseModel):
    game_id: UUID = Field(description="The game her yes fills.")
    starts_at: datetime
    book_by: datetime = Field(description="When her yes is due by.")
    club_name: str | None
    people_in: list[PersonRef] = Field(
        description="Everybody In now, in yes order — she is not."
    )
    says: str = Field(description="What happened, for the tester.")


_REFUSED: dict[int | str, dict[str, Any]] = {
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": (
            "`not_a_seed_account` — the protagonist, or somebody the situation "
            "would act as, is not an account the seed created."
        ),
    },
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "`group_not_found` — no such group.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": (
            "`situation_unavailable` — it cannot be set up in this store, and "
            "why. Any other code is a use case's own refusal, in its own words."
        ),
    },
}


# --------------------------------------------------------------------------- #
# The card a situation leaves needing her, found per request
# --------------------------------------------------------------------------- #


class CardFinder:
    """The soonest card of hers a situation can leave needing only her yes."""

    def __init__(
        self,
        *,
        directory: ProposalDirectory,
        proposals: ProposalRepository,
        terms: ClubTerms,
        saved: SavedMethods,
        deck: ReadGroupDeck,
        users: UserRepository,
    ) -> None:
        self._directory = directory
        self._proposals = proposals
        self._terms = terms
        self._saved = saved
        self._deck = deck
        self._users = users

    async def reload(self, proposal_id: UUID) -> Proposal:
        return invariant(
            await self._proposals.load(proposal_id),
            f"{proposal_id} went missing mid-situation",
        )

    async def find(
        self, her: UUID, group_id: UUID, sport: Sport, *, now: Instant
    ) -> tuple[Proposal, Sequence[UUID]] | None:
        """The game, and who beside her says yes on it — in the order they were
        dealt: the soonest card with ``TIME_TO_ANSWER`` left before its book-by,
        or else the soonest at all. ``None`` when no card of hers can be."""

        soonest: tuple[Proposal, Sequence[UUID]] | None = None
        for proposal_id in await self._directory.filling_in(group_id, now=now):
            game = await self._proposals.load(proposal_id)
            if game is None or game.sport is not sport:
                continue
            others = await self._yeses_it_needs(her, game, now=now)
            if others is None:
                continue
            if game.book_by >= now + TIME_TO_ANSWER:
                return game, others
            soonest = soonest or (game, others)
        return soonest

    async def _yeses_it_needs(
        self, her: UUID, game: Proposal, *, now: Instant
    ) -> Sequence[UUID] | None:
        version = game.version_of(her)
        if version is None or not game.may_say_yes(her, at=now):
            return None
        terms = (await self._terms.of([game.club_id], now=now)).get(game.club_id)
        if terms is None or terms.confirms_each_game:
            return None
        if not await self._deck.shows(her, game, now=now):
            return None
        needed = game.open_seats - 1
        beside_her = [
            player
            for player in version.players
            if player != her
            and player not in game.yeses
            and game.may_say_yes(player, at=now)
        ]
        able = [
            player
            for player in beside_her
            if await holds_a_seed_account(self._users, player)
            and await self._saved.saved_for(player)
        ]
        return able[:needed] if len(able) >= needed else None


def get_card_finder(
    directory: ProposalDirectoryDep,
    proposals: ProposalRepositoryDep,
    terms: ClubTermsDep,
    saved: SavedMethodsDep,
    deck: ReadGroupDeckDep,
    users: UserRepositoryDep,
) -> CardFinder:
    return CardFinder(
        directory=directory,
        proposals=proposals,
        terms=terms,
        saved=saved,
        deck=deck,
        users=users,
    )


CardFinderDep = Annotated[CardFinder, Depends(get_card_finder)]


# --------------------------------------------------------------------------- #
# 1 · Fresh deal
# --------------------------------------------------------------------------- #


@router.post(
    "/fresh-deal",
    response_model=FreshDealResponse,
    responses=_REFUSED,
    summary="Situation 1 · Fresh deal",
    description=(
        "Runs the proposer now for the group — the job's own use case, over "
        "every sport the group plays, at the real now."
    ),
)
async def fresh_deal(
    body: FreshDealRequest, groups: GroupDirectoryDep, proposer: ProposeGamesDep
) -> FreshDealResponse:
    await the_group(groups, body.group_id)
    proposed = await proposer.execute(body.group_id)
    return FreshDealResponse(
        proposed=ProposedSchema(
            made=proposed.made,
            dealt=proposed.dealt,
            lost=proposed.lost,
            redealt=proposed.redealt,
            refused=proposed.refused,
        ),
        says=(
            f"The proposer made {proposed.made} pick(s) and dealt {proposed.dealt} "
            f"version(s); {proposed.lost} card(s) had lost their court hour."
        ),
    )


# --------------------------------------------------------------------------- #
# 2 · Needs her yes · Instant club
# --------------------------------------------------------------------------- #


@router.post(
    "/needs-her-yes-instant-club",
    response_model=NeedsHerYesResponse,
    responses=_REFUSED,
    summary="Situation 2 · Needs her yes, Instant club",
    description=(
        "Leaves a game needing only the protagonist's yes, at a club that books "
        "at once: the soonest card of hers in the group and sport that her deck "
        f"shows — one with {TIME_TO_ANSWER // hours(1)} hours left before its "
        "book-by, where there is one — with enough of the people dealt it beside "
        "her saying yes — each "
        "through the yes their own phone runs. Her yes then fills it: a charge, "
        "*It's a game!*, then Home. With no such card, the proposer deals first."
    ),
)
async def needs_her_yes_instant_club(
    body: NeedsHerYesRequest,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    finder: CardFinderDep,
    proposer: ProposeGamesDep,
    say: SayYesDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> NeedsHerYesResponse:
    listing = await the_group(groups, body.group_id)
    her = body.protagonist_id
    await refuse_unless_a_seed_account(users, her)
    if her not in listing.members:
        raise SituationUnavailable(f"The protagonist is not in {listing.name.value}.")

    now = instant(clock.now())
    found = await finder.find(her, body.group_id, body.sport, now=now)
    if found is None:
        await proposer.execute(body.group_id)
        now = instant(clock.now())
        found = await finder.find(her, body.group_id, body.sport, now=now)
    if found is None:
        raise SituationUnavailable(
            f"No {body.sport.value.lower()} card of hers in "
            f"{listing.name.value} can be left needing only her yes at a club "
            f"that books at once — not even after a fresh deal: none her deck "
            f"shows has enough people dealt it beside her who are seed accounts "
            f"with a card saved."
        )

    game, others = found
    for player in others:
        await say.execute(
            AnswerProposalCommand(proposal_id=game.proposal_id, player_id=player)
        )

    game = await finder.reload(game.proposal_id)
    named = await names.names_of([her, *game.yeses])
    club = (await clubs.names_of([game.club_id])).get(game.club_id)
    hour = game.start.astimezone(CLUB_ZONE)
    due = game.book_by.astimezone(CLUB_ZONE)
    minutes = int((game.book_by - now).total_seconds() // 60)
    return NeedsHerYesResponse(
        game_id=game.proposal_id,
        starts_at=game.start,
        book_by=game.book_by,
        club_name=club,
        people_in=[
            PersonRef(player_id=player, name=named.get(player)) for player in game.yeses
        ],
        says=(
            f"{named.get(her, 'Her')}'s yes fills {hour:%a %d %b %H:%M} at "
            f"{club or 'the club'}: {len(game.yeses)} In, "
            f"{game.open_seats} seat open — book by {due:%H:%M} "
            f"({minutes // 60} h {minutes % 60:02d} min)."
        ),
    )

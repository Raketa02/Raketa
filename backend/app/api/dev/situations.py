"""Situations: one press sets the stage for one mechanic, and the rows play it
out (``docs/adr/0194`` §4; #590 builds the first two, #591 three more).

**A situation goes through the same use cases a request runs** — the proposer
the job runs, the yes a phone's swipe runs, the seed's own building blocks — so
it can never leave a state the app could not reach. **The server's clock is
never moved**: everything here happens at the real *now*, and a situation that
needs history writes it on the seed's backdated clock (``FixedClock``) — the
pick made, and everybody's yes said, as if earlier. **It obeys the rules**:
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
3. **Needs her yes · On request club** — the same at a club that confirms each
   game, so her yes asks the club and the club row answers it. **Or, given
   minutes, the club asked already**: her game at the soonest hour an On request
   club of the group's sells, made and said yes to by her and three of the group
   — hers last — on a clock backdated so that the club's time to confirm runs out
   that many minutes from now. The request is the event counted from, so the
   event is what moves; *Run it now* on the club's answer window then calls it
   off once it is due, and not before.
4. **Card declines at the fill** — situation 2, with her saved card set to
   decline: her yes fills the game and her share is refused, so nobody pays and
   her payment waits for her — which the bank confirms from the payment
   provider's controls, and her phone's *Confirm* then books.
11. **Check-in at the club** — her game at the soonest hour today that has not
    begun, at a club of the group's that books at once: made and filled by her
    and three of the group on a clock backdated past the club's minimum notice,
    when the hour was still on sale. Her phone shows her code on the game's day;
    a club that checks nobody in is switched to *We check players in*, as its
    desk would, and the situation says so.

**The protagonist is the phone**: the account the tester holds, never acted as
— but a seed account all the same, since it is her deck the situation shapes.
**A situation that writes history writes hers too**, as the seed does: her yes
said as if earlier is the past, never a press of hers now.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Collection, Sequence
from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ClockDep, DbSession, SettingsDep, UserRepositoryDep
from app.api.dev.accounts import holds_a_seed_account, refuse_unless_a_seed_account
from app.api.dev.board import PersonRef, the_group
from app.api.dev.dependencies import (
    ClubTermsDep,
    CourtHoursDep,
    PlayerNamesDep,
    PoolsDep,
    ProposeGamesDep,
    SavedMethodsDep,
    WherePoolsPlayDep,
)
from app.api.dev.board import CardOutcome
from app.api.dev.club import is_a_seed_club
from app.api.dev.provider import NoSavedCard, TheFakeDep, steer
from app.core.config import Settings
from app.core.exception_handlers import ErrorResponse
from app.kernel import SPORT_SPECS, Clock, Instant, Sport, instant, invariant
from app.modules.clubs.application.commands import SaveRaketaSettingsCommand
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.court_hours import CLUB_ZONE, local_day
from app.modules.clubs.domain.raketa_terms import TIME_TO_CONFIRM_MINUTES
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.clubs.presentation.dependencies import (
    ClubAccountRepositoryDep,
    ClubCourtsRepositoryDep,
    SaveRaketaSettingsDep,
)
from app.modules.groups.domain.ports import GroupDirectory, GroupListing
from app.modules.groups.presentation.dependencies import GroupDirectoryDep
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.presentation.dependencies import (
    PaymentMethodRepositoryDep,
    PaymentProviderDep,
)
from app.modules.proposals.application.answers import SayYes, YesAnswer
from app.modules.proposals.application.commands import AnswerProposalCommand
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.domain.deck import DECK_HORIZON, GAME_LENGTH
from app.modules.proposals.domain.ports import (
    BookedGames,
    ClubNames,
    ClubTerms,
    CourtHours,
    PlayerNames,
    Pools,
    ProposalDirectory,
    ProposalRepository,
    SavedMethods,
    WherePoolsPlay,
)
from app.modules.proposals.domain.proposal import Proposal
from app.modules.proposals.domain.proposer import CourtHourOnSale
from app.modules.proposals.presentation.dependencies import (
    BookedGamesDep,
    ProposalClubNamesDep,
    ProposalDirectoryDep,
    ProposalRepositoryDep,
    ReadGroupDeckDep,
    SayYesDep,
)
from app.modules.users.domain.ports import UserRepository
from app.seeds.bookings import all_say_yes
from app.seeds.clock import FixedClock
from app.seeds.proposals import GAMES_KIND
from app.shared.domain.errors import ConflictError

router = APIRouter(prefix="/situations", tags=["dev"])

#: How long before its book-by a card a situation leaves needing her yes should
#: still be — enough to pick the phone up and say it. A card with less is taken
#: only when no other can be, and the situation says when her yes is due.
TIME_TO_ANSWER = timedelta(hours=2)

#: How much earlier than the club's minimum notice *Check-in at the club* writes
#: its game's history: the hour was on sale then, with time to fill it.
BEFORE_THE_NOTICE = timedelta(hours=1)


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


class HerSituationRequest(BaseModel):
    """A situation set up around the protagonist, in a group and a sport."""

    group_id: UUID
    sport: Sport
    protagonist_id: UUID = Field(
        description="Whose phone it is — the protagonist the situation is for."
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


class OnRequestRequest(HerSituationRequest):
    answer_due_in_minutes: int | None = Field(
        default=None,
        ge=1,
        le=TIME_TO_CONFIRM_MINUTES[1],
        description=(
            "Ask the club already, as if her yes had been said earlier, so that "
            "its answer is due this many minutes from now. A club's own time to "
            "confirm is the most it can be: asked for more, the club is asked "
            "now and `answer_by` says when. Left out, her yes is left for the "
            "phone."
        ),
    )


class OnRequestResponse(BaseModel):
    game_id: UUID
    starts_at: datetime
    book_by: datetime
    club_name: str | None
    people_in: list[PersonRef] = Field(description="Everybody In now, in yes order.")
    answer_by: datetime | None = Field(
        description=(
            "When the club's answer is due, once it was asked; `null` while her "
            "yes is left for the phone."
        )
    )
    says: str = Field(description="What happened, for the tester.")


class CheckInAtTheClubResponse(BaseModel):
    game_id: UUID
    starts_at: datetime
    club_id: UUID = Field(description="The club the club row acts as.")
    club_name: str | None
    people: list[PersonRef] = Field(description="Everybody on it, in yes order.")
    check_in_switched_on: bool = Field(
        description=(
            "The club checked nobody in, and its *We check players in* was "
            "switched on as its desk would."
        )
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
        self,
        her: UUID,
        group_id: UUID,
        sport: Sport,
        *,
        on_request: bool,
        now: Instant,
    ) -> tuple[Proposal, Sequence[UUID]] | None:
        """The game, and who beside her says yes on it — in the order they were
        dealt: the soonest card at a club that confirms each game or not, as
        asked, with ``TIME_TO_ANSWER`` left before its book-by, or else the
        soonest at all. ``None`` when no card of hers can be."""

        soonest: tuple[Proposal, Sequence[UUID]] | None = None
        for proposal_id in await self._directory.filling_in(group_id, now=now):
            game = await self._proposals.load(proposal_id)
            if game is None or game.sport is not sport:
                continue
            others = await self._yeses_it_needs(
                her, game, on_request=on_request, now=now
            )
            if others is None:
                continue
            if game.book_by >= now + TIME_TO_ANSWER:
                return game, others
            soonest = soonest or (game, others)
        return soonest

    async def _yeses_it_needs(
        self, her: UUID, game: Proposal, *, on_request: bool, now: Instant
    ) -> Sequence[UUID] | None:
        version = game.version_of(her)
        if version is None or not game.may_say_yes(her, at=now):
            return None
        terms = (await self._terms.of([game.club_id], now=now)).get(game.club_id)
        if terms is None or terms.confirms_each_game is not on_request:
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
# An hour, and three beside her — for a game a situation makes itself
# --------------------------------------------------------------------------- #


class HourFinder:
    """The soonest hour a club of the group's sells at which she and three of
    the group can all be booked, and those three — for a situation that makes
    its game itself, as the seed does, rather than finding a card."""

    def __init__(
        self,
        *,
        pools: Pools,
        where: WherePoolsPlay,
        terms: ClubTerms,
        court_hours: CourtHours,
        booked: BookedGames,
        saved: SavedMethods,
        users: UserRepository,
        accounts: ClubAccountRepository,
    ) -> None:
        self._pools = pools
        self._where = where
        self._terms = terms
        self._court_hours = court_hours
        self._booked = booked
        self._saved = saved
        self._users = users
        self._accounts = accounts

    async def clubs(
        self, group_id: UUID, *, on_request: bool, now: Instant
    ) -> Sequence[UUID]:
        """The clubs the seed signed up that the group plays at and that sell
        now — confirming each game, or booking at once, as asked — home first.
        A situation that makes a game at a club asks its desk, or acts as it."""

        pool = await self._pools.find(group_id)
        where = None if pool is None else await self._where.of(pool, now=now)
        if where is None:
            return ()
        terms = await self._terms.of(where.home_first, now=now)
        return [
            club_id
            for club_id in where.home_first
            if club_id in terms
            and terms[club_id].confirms_each_game is on_request
            and await is_a_seed_club(self._accounts, club_id)
        ]

    async def hour_and_three(
        self,
        her: UUID,
        listing: GroupListing,
        club_id: UUID,
        sport: Sport,
        *,
        on_sale_at: Instant,
        start: Instant,
        end: Instant,
    ) -> tuple[CourtHourOnSale, Sequence[UUID]] | None:
        """The soonest hour beginning after ``start``, until ``end``, the club
        sold at ``on_sale_at`` — taking new cards — with her and enough of the
        group free then: seed accounts with a card saved, in the order they
        joined."""

        needed = SPORT_SPECS[sport].players - 1
        beside_her = [
            member
            for member in listing.members
            if member != her
            and await holds_a_seed_account(self._users, member)
            and await self._saved.saved_for(member)
        ]
        busy = {
            player: await self._booked.starts_of(
                player, start=start - GAME_LENGTH, end=end + GAME_LENGTH
            )
            for player in (her, *beside_her)
        }
        on_sale = await self._court_hours.on_sale(
            [club_id], start=start, end=end, now=on_sale_at
        )
        for hour in sorted(on_sale, key=lambda one: one.start):
            if (
                hour.sport is not sport
                or not hour.taking_new_cards
                or hour.start <= start
            ):
                continue
            if _busy(busy[her], hour.start):
                continue
            free = [p for p in beside_her if not _busy(busy[p], hour.start)]
            if len(free) >= needed:
                return hour, free[:needed]
        return None


def _busy(booked: Collection[Instant], start: Instant) -> bool:
    return any(abs(start - game) < GAME_LENGTH for game in booked)


def get_hour_finder(
    pools: PoolsDep,
    where: WherePoolsPlayDep,
    terms: ClubTermsDep,
    court_hours: CourtHoursDep,
    booked: BookedGamesDep,
    saved: SavedMethodsDep,
    users: UserRepositoryDep,
    accounts: ClubAccountRepositoryDep,
) -> HourFinder:
    return HourFinder(
        pools=pools,
        where=where,
        terms=terms,
        court_hours=court_hours,
        booked=booked,
        saved=saved,
        users=users,
        accounts=accounts,
    )


HourFinderDep = Annotated[HourFinder, Depends(get_hour_finder)]


class HerGameEarlier:
    """Her game at an hour, made and said yes to by three of the group and her
    — hers last — on a clock stopped earlier: the seed's own building block,
    over this request's session and the provider it moves money through."""

    def __init__(
        self, *, db: AsyncSession, settings: Settings, provider: PaymentProvider
    ) -> None:
        self._db = db
        self._settings = settings
        self._provider = provider

    async def write(
        self,
        body: HerSituationRequest,
        club_id: UUID,
        hour: CourtHourOnSale,
        three: Sequence[UUID],
        *,
        at: Instant,
    ) -> YesAnswer | None:
        """Her yes's answer — the last."""

        return await all_say_yes(
            self._db,
            settings=self._settings,
            clock=FixedClock(at=at),
            provider=self._provider,
            pool_id=body.group_id,
            club_id=club_id,
            start=hour.start,
            players=(*three, body.protagonist_id),
            sport=body.sport,
            kind=GAMES_KIND,
        )


def get_her_game_earlier(
    db: DbSession, settings: SettingsDep, provider: PaymentProviderDep
) -> HerGameEarlier:
    return HerGameEarlier(db=db, settings=settings, provider=provider)


HerGameEarlierDep = Annotated[HerGameEarlier, Depends(get_her_game_earlier)]


async def her_group(
    groups: GroupDirectory, users: UserRepository, group_id: UUID, her: UUID
) -> GroupListing:
    """The group, once the protagonist is a seed account in it."""

    listing = await the_group(groups, group_id)
    await refuse_unless_a_seed_account(users, her)
    if her not in listing.members:
        raise SituationUnavailable(f"The protagonist is not in {listing.name.value}.")
    return listing


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
# 2 · Needs her yes · Instant club — and 3 and 4, which are it elsewhere
# --------------------------------------------------------------------------- #


class NeedsHerYes:
    """A card of hers left needing only her yes — the work of situations 2, 3
    and 4, built per request."""

    def __init__(
        self,
        *,
        groups: GroupDirectory,
        users: UserRepository,
        finder: CardFinder,
        proposer: ProposeGames,
        say: SayYes,
        names: PlayerNames,
        clubs: ClubNames,
        clock: Clock,
    ) -> None:
        self._groups = groups
        self._users = users
        self._finder = finder
        self._proposer = proposer
        self._say = say
        self._names = names
        self._clubs = clubs
        self._clock = clock

    async def set_up(
        self, body: HerSituationRequest, *, on_request: bool
    ) -> NeedsHerYesResponse:
        listing = await her_group(
            self._groups, self._users, body.group_id, body.protagonist_id
        )
        her = body.protagonist_id
        now = instant(self._clock.now())
        found = await self._finder.find(
            her, body.group_id, body.sport, on_request=on_request, now=now
        )
        if found is None:
            await self._proposer.execute(body.group_id)
            now = instant(self._clock.now())
            found = await self._finder.find(
                her, body.group_id, body.sport, on_request=on_request, now=now
            )
        if found is None:
            raise SituationUnavailable(
                f"No {body.sport.value.lower()} card of hers in "
                f"{listing.name.value} can be left needing only her yes at a club "
                f"that {'confirms each game' if on_request else 'books at once'} — "
                f"not even after a fresh deal: none her deck shows has enough "
                f"people dealt it beside her who are seed accounts with a card "
                f"saved."
            )

        game, others = found
        for player in others:
            await self._say.execute(
                AnswerProposalCommand(proposal_id=game.proposal_id, player_id=player)
            )

        game = await self._finder.reload(game.proposal_id)
        named = await self._names.names_of([her, *game.yeses])
        club = (await self._clubs.names_of([game.club_id])).get(game.club_id)
        minutes = int((game.book_by - now).total_seconds() // 60)
        return NeedsHerYesResponse(
            game_id=game.proposal_id,
            starts_at=game.start,
            book_by=game.book_by,
            club_name=club,
            people_in=[
                PersonRef(player_id=player, name=named.get(player))
                for player in game.yeses
            ],
            says=(
                f"{named.get(her, 'Her')}'s yes fills {_when(game.start)} at "
                f"{club or 'the club'}: {len(game.yeses)} In, "
                f"{game.open_seats} seat open — book by "
                f"{game.book_by.astimezone(CLUB_ZONE):%H:%M} "
                f"({minutes // 60} h {minutes % 60:02d} min)."
            ),
        )


def _when(start: Instant) -> str:
    return f"{start.astimezone(CLUB_ZONE):%a %d %b %H:%M}"


def get_needs_her_yes(
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    finder: CardFinderDep,
    proposer: ProposeGamesDep,
    say: SayYesDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> NeedsHerYes:
    return NeedsHerYes(
        groups=groups,
        users=users,
        finder=finder,
        proposer=proposer,
        say=say,
        names=names,
        clubs=clubs,
        clock=clock,
    )


NeedsHerYesDep = Annotated[NeedsHerYes, Depends(get_needs_her_yes)]


@router.post(
    "/needs-her-yes-instant-club",
    response_model=NeedsHerYesResponse,
    responses=_REFUSED,
    summary="Situation 2 · Needs her yes, Instant club",
    description=(
        "Leaves a game needing only the protagonist's yes, at a club that books "
        "at once: the soonest card of hers in the group and sport that her deck "
        f"shows — one with {TIME_TO_ANSWER // timedelta(hours=1)} hours left "
        "before its book-by, where there is one — with enough of the people dealt "
        "it beside "
        "her saying yes — each "
        "through the yes their own phone runs. Her yes then fills it: a charge, "
        "*It's a game!*, then Home. With no such card, the proposer deals first."
    ),
)
async def needs_her_yes_instant_club(
    body: HerSituationRequest, needs_her_yes: NeedsHerYesDep
) -> NeedsHerYesResponse:
    return await needs_her_yes.set_up(body, on_request=False)


# --------------------------------------------------------------------------- #
# 3 · Needs her yes · On request club
# --------------------------------------------------------------------------- #


@router.post(
    "/needs-her-yes-on-request-club",
    response_model=OnRequestResponse,
    responses=_REFUSED,
    summary="Situation 3 · Needs her yes, On request club",
    description=(
        "Situation 2 at a club that confirms each game: her yes asks the club, "
        "and the club row accepts or refuses — or the club's time to confirm "
        "runs out. **With `answer_due_in_minutes`, the club is asked already**: "
        "her game at the soonest hour an On request club of the group's sells, "
        "made and said yes to by her and three of the group — hers last — as "
        "if earlier, so the answer is due that many minutes from now (or, past "
        "the club's own time to confirm, that long from now); then *Run it now* "
        "on the club's answer window calls it off once it is due."
    ),
)
async def needs_her_yes_on_request_club(
    body: OnRequestRequest,
    needs_her_yes: NeedsHerYesDep,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    hours_finder: HourFinderDep,
    club_courts: ClubCourtsRepositoryDep,
    earlier: HerGameEarlierDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
    finder: CardFinderDep,
) -> OnRequestResponse:
    if body.answer_due_in_minutes is None:
        found = await needs_her_yes.set_up(body, on_request=True)
        return OnRequestResponse(
            **found.model_dump(exclude={"says"}),
            answer_by=None,
            says=f"{found.says} Her yes asks the club.",
        )

    her = body.protagonist_id
    listing = await her_group(groups, users, body.group_id, her)
    now = instant(clock.now())
    due_in = timedelta(minutes=body.answer_due_in_minutes)
    for club_id in await hours_finder.clubs(body.group_id, on_request=True, now=now):
        to_confirm = timedelta(
            minutes=(await club_courts.load(club_id)).settings.time_to_confirm_minutes
        )
        asked_at = instant(now - max(to_confirm - due_in, timedelta()))
        found_hour = await hours_finder.hour_and_three(
            her,
            listing,
            club_id,
            body.sport,
            on_sale_at=asked_at,
            start=asked_at,
            end=asked_at + DECK_HORIZON,
        )
        if found_hour is None:
            continue
        hour, three = found_hour
        asked = _asked(
            await earlier.write(body, club_id, hour, three, at=asked_at), hour
        )
        game = await finder.reload(asked.proposal_id)
        named = await names.names_of(game.yeses)
        club = (await clubs.names_of([club_id])).get(club_id)
        answer_by = invariant(asked.waiting_until, "asked, with no answer due")
        left_minutes = max(int((answer_by - now).total_seconds() // 60), 0)
        return OnRequestResponse(
            game_id=game.proposal_id,
            starts_at=game.start,
            book_by=game.book_by,
            club_name=club,
            people_in=[
                PersonRef(player_id=player, name=named.get(player))
                for player in game.yeses
            ],
            answer_by=answer_by,
            says=(
                f"{club or 'The club'} was asked for {_when(game.start)} at "
                f"{asked_at.astimezone(CLUB_ZONE):%H:%M}: its answer is due by "
                f"{answer_by.astimezone(CLUB_ZONE):%H:%M} ({left_minutes} min). "
                f"Accept or refuse from the club row, or let it run out and press "
                f"*Run it now*."
            ),
        )
    raise SituationUnavailable(
        f"No On request club {listing.name.value} plays at sells a "
        f"{body.sport.value.lower()} hour she and three of the group — seed "
        f"accounts with a card saved — are all free for."
    )


def _asked(answer: YesAnswer | None, hour: CourtHourOnSale) -> YesAnswer:
    """The last yes's answer, once it asked the club — or what it did instead."""

    if answer is None or answer.waiting_until is None:
        raise SituationUnavailable(
            f"Everybody's yes on {_when(hour.start)} did not ask the club: {answer!r}."
        )
    return answer


# --------------------------------------------------------------------------- #
# 4 · Card declines at the fill
# --------------------------------------------------------------------------- #


@router.post(
    "/card-declines-at-the-fill",
    response_model=NeedsHerYesResponse,
    responses=_REFUSED,
    summary="Situation 4 · Card declines at the fill",
    description=(
        "Situation 2, with her saved card set to decline: her yes fills the "
        "game and her share is refused, so nobody pays and the game is filling "
        "again. The recovery: *Bank confirms* on her charge, then *Confirm* on "
        "her phone books it."
    ),
)
async def card_declines_at_the_fill(
    body: HerSituationRequest,
    needs_her_yes: NeedsHerYesDep,
    users: UserRepositoryDep,
    fake: TheFakeDep,
    methods: PaymentMethodRepositoryDep,
) -> NeedsHerYesResponse:
    # Refused before anybody says yes, so a press that cannot steer her card
    # leaves no game half set up.
    await refuse_unless_a_seed_account(users, body.protagonist_id)
    if (await methods.load(body.protagonist_id)).method is None:
        raise NoSavedCard()
    found = await needs_her_yes.set_up(body, on_request=False)
    card = await steer(fake, methods, body.protagonist_id, CardOutcome.DECLINES)
    return found.model_copy(
        update={
            "says": (
                f"{found.says} Her {card.brand} •••• {card.last_four} declines: "
                f"her yes will be refused."
            )
        }
    )


# --------------------------------------------------------------------------- #
# 11 · Check-in at the club
# --------------------------------------------------------------------------- #


@router.post(
    "/check-in-at-the-club",
    response_model=CheckInAtTheClubResponse,
    responses=_REFUSED,
    summary="Situation 11 · Check-in at the club",
    description=(
        "Her game at the soonest hour today that has not begun, at a club of "
        "the group's that books at once — made and filled by her and three of "
        "the group as if earlier, when the hour was still on sale. Her phone "
        "shows her check-in code today, and the club checks players in: a club "
        "that did not is switched to *We check players in*, as its desk would."
    ),
)
async def check_in_at_the_club(
    body: HerSituationRequest,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    hours_finder: HourFinderDep,
    club_courts: ClubCourtsRepositoryDep,
    save_settings: SaveRaketaSettingsDep,
    earlier: HerGameEarlierDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> CheckInAtTheClubResponse:
    her = body.protagonist_id
    listing = await her_group(groups, users, body.group_id, her)
    now = instant(clock.now())
    for club_id in await hours_finder.clubs(body.group_id, on_request=False, now=now):
        courts = await club_courts.load(club_id)
        filled_at = instant(
            now
            - timedelta(hours=courts.settings.minimum_notice_hours)
            - BEFORE_THE_NOTICE
        )
        found_hour = await hours_finder.hour_and_three(
            her,
            listing,
            club_id,
            body.sport,
            on_sale_at=filled_at,
            start=now,
            end=now + timedelta(days=1),
        )
        if found_hour is None or local_day(found_hour[0].start) != local_day(now):
            continue
        hour, three = found_hour
        answer = await earlier.write(body, club_id, hour, three, at=filled_at)
        if answer is None or answer.booked is None:
            raise SituationUnavailable(
                f"Everybody's yes on {_when(hour.start)} did not book it: {answer!r}."
            )
        switched_on = not courts.settings.check_in
        if switched_on:
            await save_settings.execute(_checking_players_in(club_id, courts))
        people = (*three, her)
        named = await names.names_of(people)
        club = (await clubs.names_of([club_id])).get(club_id)
        return CheckInAtTheClubResponse(
            game_id=answer.proposal_id,
            starts_at=hour.start,
            club_id=club_id,
            club_name=club,
            people=[PersonRef(player_id=p, name=named.get(p)) for p in people],
            check_in_switched_on=switched_on,
            says=(
                f"Booked {_when(hour.start)} at {club or 'the club'}: her phone "
                f"shows her code today."
                + (
                    " The club checked nobody in — *We check players in* is on now."
                    if switched_on
                    else ""
                )
            ),
        )
    raise SituationUnavailable(
        f"No club {listing.name.value} plays at that books at once sells a "
        f"{body.sport.value.lower()} hour later today she and three of the group "
        f"— seed accounts with a card saved — are all free for."
    )


def _checking_players_in(
    club_id: UUID, courts: ClubCourts
) -> SaveRaketaSettingsCommand:
    """The desk's settings form as it stands, with *We check players in* on."""

    kept = courts.settings
    return SaveRaketaSettingsCommand(
        club_id=club_id,
        release_lead_days=kept.release_lead_days,
        cut_off_hours=kept.cut_off_hours,
        minimum_notice_hours=kept.minimum_notice_hours,
        time_to_confirm_minutes=kept.time_to_confirm_minutes,
        other_clubs_courts=kept.other_clubs_courts.offered,
        other_clubs_within_km=kept.other_clubs_courts.within_km,
        check_in=True,
        paused=courts.paused,
    )

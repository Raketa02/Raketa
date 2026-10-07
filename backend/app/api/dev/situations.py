"""Situations: one press sets the stage for one mechanic, and the rows play it
out (``docs/adr/0194`` §4; #590 builds the first two, #591 three more, #592
three whose moment is a clock).

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
5. **About to expire** — a card of hers nobody has answered, at the hour whose
   book-by is the next full hour the rules allow: the soonest book-by of an
   hour a club of the group's sells, she and three of the group are free for,
   in a week her deck still shows — dealt as the dealer deals a pick, now.
7. **Empty seat at the cut-off** — her game booked at the hour whose cut-off is
   the next full hour the rules allow, at a club of the group's that books at
   once: filled by her and three of the group as if earlier, when the hour was
   on sale, and left by one of the three just now — so a seat is open since
   before the cut-off, the leaver refunded less the fee and the seat offered.
11. **Check-in at the club** — her game at the soonest hour today that has not
    begun, at a club of the group's that books at once: made and filled by her
    and three of the group on a clock backdated past the club's minimum notice,
    when the hour was still on sale. Her phone shows her code on the game's day;
    a club that checks nobody in is switched to *We check players in*, as its
    desk would, and the situation says so.
12. **Club day close** — the last closed club day's played games, at a club of
    the group's that books at once and has had no day close for it yet: up to
    two, each a game's worth of the group — never her, and nobody on both —
    booked inside that day, on a clock backdated to it, and played. Running
    the day close then pays the club for them and emails its desk the day's
    new bookings.

**A moment fixed to the hour lands on the next full hour the rules allow, and
says so** (situations 5 and 7): *fires at 15:00 · 40 min*. Book-bys and
cut-offs are whole hours before games that start on the hour, so the soonest
one is whichever the club sells first — **at least ``TIME_TO_WATCH`` off**, so
there is time to pick the phone up before it fires.

**The protagonist is the phone**: the account the tester holds, never acted as
— but a seed account all the same, since it is her deck the situation shapes.
**A situation that writes history writes hers too**, as the seed does: her yes
said as if earlier is the past, never a press of hers now.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Collection, Sequence
from datetime import date, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field

from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ClockDep, DbSession, SettingsDep, UserRepositoryDep
from app.api.dev.accounts import holds_a_seed_account, refuse_unless_a_seed_account
from app.api.dev.board import PersonRef, fires_at, the_group
from app.api.dev.dependencies import (
    ClubPayoutRepositoryDep,
    ClubTermsDep,
    CourtHoursDep,
    MakeProposalDep,
    SummaryRepositoryDep,
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
from app.kernel import (
    SPORT_SPECS,
    Clock,
    Instant,
    Sport,
    hours,
    instant,
    invariant,
    shifted,
)
from app.modules.bookings.domain.summary import summary_id_for
from app.modules.clubs.application.commands import SaveRaketaSettingsCommand
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.court_hours import (
    CLUB_ZONE,
    DAY_CLOSES,
    day_closes_at,
    last_closed_day,
    local_day,
)
from app.modules.clubs.domain.raketa_terms import TIME_TO_CONFIRM_MINUTES
from app.modules.clubs.domain.ports import ClubAccountRepository
from app.modules.clubs.presentation.dependencies import (
    ClubAccountRepositoryDep,
    ClubCourtsRepositoryDep,
    SaveRaketaSettingsDep,
)
from app.modules.groups.domain.ports import GroupDirectory, GroupListing
from app.modules.groups.presentation.dependencies import GroupDirectoryDep
from app.modules.payments.domain.club_payout import payout_id_for
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.presentation.dependencies import (
    PaymentMethodRepositoryDep,
    PaymentProviderDep,
)
from app.modules.proposals.application.answers import SayYes, YesAnswer
from app.modules.proposals.application.commands import (
    AnswerProposalCommand,
    LeaveTheGameCommand,
    MakeProposalCommand,
)
from app.modules.proposals.application.group_deck import ReadGroupDeck
from app.modules.proposals.application.propose_games import ProposeGames
from app.modules.proposals.domain.deck import DECK_HORIZON, GAME_LENGTH, week_of
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
from app.modules.proposals.domain.proposal import Origin, Proposal
from app.modules.proposals.domain.proposer import CourtHourOnSale
from app.modules.proposals.presentation.dependencies import (
    BookedGamesDep,
    LeaveTheGameDep,
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

#: How much earlier than the club's minimum notice a situation that books its
#: own game writes its history: the hour was on sale then, with time to fill it.
BEFORE_THE_NOTICE = timedelta(hours=1)

#: How far off at least a moment a situation lands on the hour is — a book-by,
#: a cut-off — so the tester can pick the phone up before it fires. Not a rule
#: of the games: the next full hour is the soonest *the rules* allow, and this
#: only skips one too close to watch.
TIME_TO_WATCH = timedelta(minutes=5)

#: How many games *Club day close* plays in the closed day — nobody on two of
#: them, so nobody's week takes two.
DAY_CLOSE_GAMES = 2


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


class AboutToExpireResponse(BaseModel):
    game_id: UUID
    starts_at: datetime
    book_by: datetime = Field(
        description="When it goes: the next full hour a book-by can fall on."
    )
    club_name: str | None
    dealt: list[PersonRef] = Field(
        description="Who it was dealt to, her first. Nobody has answered."
    )
    says: str = Field(description="What happened, and when it fires.")


class EmptySeatResponse(BaseModel):
    game_id: UUID
    starts_at: datetime
    cut_off: datetime = Field(
        description="The next full hour a cut-off can fall on — the booking's own."
    )
    club_id: UUID = Field(description="The club the club row acts as.")
    club_name: str | None
    people_in: list[PersonRef] = Field(description="Everybody still on it, her last.")
    left: PersonRef = Field(description="Who left, just now, before the cut-off.")
    says: str = Field(description="What happened, and when it fires.")


class ClubDayCloseRequest(BaseModel):
    group_id: UUID
    sport: Sport
    protagonist_id: UUID | None = Field(
        default=None,
        description=(
            "Whose phone it is — **kept off** the games, so her week stays as the "
            "phone has it."
        ),
    )


class DayCloseGame(BaseModel):
    game_id: UUID
    starts_at: datetime
    booked_at: datetime = Field(description="Inside the day, after the close before.")
    people: list[PersonRef]


class ClubDayCloseResponse(BaseModel):
    club_id: UUID = Field(description="The club the club row acts as.")
    club_name: str | None
    day: date = Field(description="The last club day closed — whose close is run.")
    closed_at: datetime = Field(
        description=f"When that day closed: {DAY_CLOSES}:00 in Kraków."
    )
    games: list[DayCloseGame] = Field(description="Played that day, soonest first.")
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
        self, group_id: UUID, *, on_request: bool | None, now: Instant
    ) -> Sequence[UUID]:
        """The clubs the seed signed up that the group plays at and that sell
        now — confirming each game, or booking at once, as asked, or either
        for ``None`` — home first. A situation that makes a game at a club asks
        its desk, or acts as it."""

        pool = await self._pools.find(group_id)
        where = None if pool is None else await self._where.of(pool, now=now)
        if where is None:
            return ()
        terms = await self._terms.of(where.home_first, now=now)
        return [
            club_id
            for club_id in where.home_first
            if club_id in terms
            and (on_request is None or terms[club_id].confirms_each_game is on_request)
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
        """The soonest of ``hours_free`` with her, and the first of the group
        free then who make it a game with her."""

        for hour, free in await self.hours_free(
            listing,
            club_id,
            sport,
            her=her,
            on_sale_at=on_sale_at,
            start=start,
            end=end,
        ):
            return hour, free[: SPORT_SPECS[sport].players - 1]
        return None

    async def hours_free(
        self,
        listing: GroupListing,
        club_id: UUID,
        sport: Sport,
        *,
        her: UUID | None,
        leaving_out: Collection[UUID] = (),
        on_sale_at: Instant,
        start: Instant,
        end: Instant,
    ) -> list[tuple[CourtHourOnSale, Sequence[UUID]]]:
        """Every hour beginning after ``start``, until ``end``, the club sold
        at ``on_sale_at`` — taking new cards — soonest first, that she is free
        for when she is named, each with everybody else of the group free then:
        seed accounts with a card saved, in the order they joined, never one
        ``leaving_out`` names. An hour too few are free for to make a game is
        left out."""

        needed = SPORT_SPECS[sport].players - (0 if her is None else 1)
        others = [
            member
            for member in listing.members
            if member != her
            and member not in leaving_out
            and await holds_a_seed_account(self._users, member)
            and await self._saved.saved_for(member)
        ]
        busy = {
            player: await self._booked.starts_of(
                player, start=start - GAME_LENGTH, end=end + GAME_LENGTH
            )
            for player in (*(() if her is None else (her,)), *others)
        }
        on_sale = await self._court_hours.on_sale(
            [club_id], start=start, end=end, now=on_sale_at
        )
        found: list[tuple[CourtHourOnSale, Sequence[UUID]]] = []
        for hour in sorted(on_sale, key=lambda one: one.start):
            if (
                hour.sport is not sport
                or not hour.taking_new_cards
                or hour.start <= start
            ):
                continue
            if her is not None and _busy(busy[her], hour.start):
                continue
            free = [p for p in others if not _busy(busy[p], hour.start)]
            if len(free) >= needed:
                found.append((hour, free))
        return found


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


class EarlierYeses:
    """A game at an hour, made and said yes to by everybody on it in turn — her
    last, where she is on it — on a clock stopped earlier: the seed's own
    building block (``all_say_yes``), over this request's session and the
    provider it moves money through."""

    def __init__(
        self, *, db: AsyncSession, settings: Settings, provider: PaymentProvider
    ) -> None:
        self._db = db
        self._settings = settings
        self._provider = provider

    async def all_say_yes(
        self,
        *,
        group_id: UUID,
        sport: Sport,
        club_id: UUID,
        hour: CourtHourOnSale,
        players: Sequence[UUID],
        at: Instant,
    ) -> YesAnswer | None:
        """The last yes's answer."""

        return await all_say_yes(
            self._db,
            settings=self._settings,
            clock=FixedClock(at=at),
            provider=self._provider,
            pool_id=group_id,
            club_id=club_id,
            start=hour.start,
            players=tuple(players),
            sport=sport,
            kind=GAMES_KIND,
        )


def get_earlier_yeses(
    db: DbSession, settings: SettingsDep, provider: PaymentProviderDep
) -> EarlierYeses:
    return EarlierYeses(db=db, settings=settings, provider=provider)


EarlierYesesDep = Annotated[EarlierYeses, Depends(get_earlier_yeses)]


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
                f"{game.open_seats} seat open — its book-by "
                f"{fires_at(game.book_by, now=now)}."
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
    earlier: EarlierYesesDep,
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
            await earlier.all_say_yes(
                group_id=body.group_id,
                sport=body.sport,
                club_id=club_id,
                hour=hour,
                players=(*three, her),
                at=asked_at,
            ),
            hour,
        )
        game = await finder.reload(asked.proposal_id)
        named = await names.names_of(game.yeses)
        club = (await clubs.names_of([club_id])).get(club_id)
        answer_by = invariant(asked.waiting_until, "asked, with no answer due")
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
                f"{asked_at.astimezone(CLUB_ZONE):%H:%M}: its answer window "
                f"{fires_at(answer_by, now=now)}. "
                f"Accept or refuse from the club row, or let it run out and press "
                f"*Run it now*."
            ),
        )
    raise SituationUnavailable(
        f"No On request club {listing.name.value} plays at sells a "
        f"{body.sport.value.lower()} hour she and three of the group — seed "
        f"accounts with a card saved — are all free for."
    )


def _booked(answer: YesAnswer | None, hour: CourtHourOnSale) -> YesAnswer:
    """The last yes's answer, once it booked the game — or what it did instead."""

    if answer is None or answer.booked is None:
        raise SituationUnavailable(
            f"Everybody's yes on {_when(hour.start)} did not book it: {answer!r}."
        )
    return answer


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
# 5 · About to expire
# --------------------------------------------------------------------------- #


@router.post(
    "/about-to-expire",
    response_model=AboutToExpireResponse,
    responses=_REFUSED,
    summary="Situation 5 · About to expire",
    description=(
        "Deals her a card nobody has answered, at the hour whose book-by is the "
        "next full hour the rules allow — the soonest book-by of an hour a club "
        "of the group's sells, she and three of the group are free for, in a "
        "week her deck still shows, at least "
        f"{TIME_TO_WATCH // timedelta(minutes=1)} minutes off. It goes from her "
        "deck then, and *Run it now* on the book-by sweep records it."
    ),
)
async def about_to_expire(
    body: HerSituationRequest,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    pools: PoolsDep,
    hours_finder: HourFinderDep,
    deck: ReadGroupDeckDep,
    make: MakeProposalDep,
    finder: CardFinderDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> AboutToExpireResponse:
    her = body.protagonist_id
    listing = await her_group(groups, users, body.group_id, her)
    now = instant(clock.now())
    pool = await pools.find(body.group_id)
    if pool is None:
        raise SituationUnavailable(f"{listing.name.value} deals no games.")
    # Her own filters, as her deck reads them: the kinds she plays, and the
    # weeks her games per week has filled.
    hers = await deck.deal_to(her, pool, body.sport, [], now=now)
    if not hers.shown:
        raise SituationUnavailable(
            f"She plays no kind of {body.sport.value.lower()} her deck would show."
        )
    kind = GAMES_KIND if GAMES_KIND in hers.shown else hers.shown[0]
    full = {week.starts_on for week in hers.capped}

    soonest: tuple[CourtHourOnSale, Sequence[UUID]] | None = None
    for club_id in await hours_finder.clubs(body.group_id, on_request=None, now=now):
        # Hours soonest first, so each club's first is its soonest book-by.
        first = next(
            (
                (hour, free)
                for hour, free in await hours_finder.hours_free(
                    listing,
                    club_id,
                    body.sport,
                    her=her,
                    on_sale_at=now,
                    start=now,
                    end=now + DECK_HORIZON,
                )
                if hour.book_by >= now + TIME_TO_WATCH
                and week_of(hour.start) not in full
            ),
            None,
        )
        if first is not None and (
            soonest is None or first[0].book_by < soonest[0].book_by
        ):
            soonest = first
    if soonest is None:
        raise SituationUnavailable(
            f"No club {listing.name.value} plays at sells a "
            f"{body.sport.value.lower()} hour she and three of the group — seed "
            f"accounts with a card saved — are all free for, in a week her deck "
            f"still shows."
        )

    hour, free = soonest
    dealt = (her, *free[: SPORT_SPECS[body.sport].players - 1])
    game = await finder.reload(
        await make.execute(
            MakeProposalCommand(
                pool_id=body.group_id,
                origin=Origin.PICK,
                poster_id=None,
                sport=body.sport,
                kind=kind,
                club_id=hour.club_id,
                start=hour.start,
                versions=[list(dealt)],
            )
        )
    )
    if not await deck.shows(her, game, now=now):
        raise SituationUnavailable(
            f"The card for {_when(game.start)} was dealt, and her deck does not "
            f"show it — her Games & money, or somebody on it she no longer fits."
        )
    named = await names.names_of(dealt)
    club = (await clubs.names_of([game.club_id])).get(game.club_id)
    return AboutToExpireResponse(
        game_id=game.proposal_id,
        starts_at=game.start,
        book_by=game.book_by,
        club_name=club,
        dealt=[PersonRef(player_id=player, name=named.get(player)) for player in dealt],
        says=(
            f"A card of hers for {_when(game.start)} at {club or 'the club'}, "
            f"nobody's answer on it. Its book-by {fires_at(game.book_by, now=now)}: "
            f"then it is gone from her deck, and *Run it now* on the book-by "
            f"sweep records it."
        ),
    )


# --------------------------------------------------------------------------- #
# 7 · Empty seat at the cut-off
# --------------------------------------------------------------------------- #


@router.post(
    "/empty-seat-at-the-cut-off",
    response_model=EmptySeatResponse,
    responses=_REFUSED,
    summary="Situation 7 · Empty seat at the cut-off",
    description=(
        "Books her game at the hour whose cut-off is the next full hour the "
        "rules allow, at a club of the group's that books at once — filled by "
        "her and three of the group as if earlier, when the hour was on sale — "
        "and one of the three leaves it now, through the leave their phone "
        "runs: a seat open since before the cut-off. Still open at the cut-off, "
        "*Run it now* on the cut-off calls the game off and refunds everybody "
        "in full; taken first, the game plays."
    ),
)
async def empty_seat_at_the_cut_off(
    body: HerSituationRequest,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    users: UserRepositoryDep,
    hours_finder: HourFinderDep,
    club_courts: ClubCourtsRepositoryDep,
    earlier: EarlierYesesDep,
    leave: LeaveTheGameDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> EmptySeatResponse:
    her = body.protagonist_id
    listing = await her_group(groups, users, body.group_id, her)
    now = instant(clock.now())

    soonest: tuple[Instant, CourtHourOnSale, Sequence[UUID], Instant] | None = None
    for club_id in await hours_finder.clubs(body.group_id, on_request=False, now=now):
        settings = (await club_courts.load(club_id)).settings
        filled_at = instant(
            now - timedelta(hours=settings.minimum_notice_hours) - BEFORE_THE_NOTICE
        )
        first = next(
            (
                (cut_off, hour, free)
                for hour, free in await hours_finder.hours_free(
                    listing,
                    club_id,
                    body.sport,
                    her=her,
                    on_sale_at=filled_at,
                    start=now,
                    end=filled_at + DECK_HORIZON,
                )
                if (cut_off := shifted(hour.start, hours(-settings.cut_off_hours)))
                >= now + TIME_TO_WATCH
            ),
            None,
        )
        if first is not None and (soonest is None or first[0] < soonest[0]):
            soonest = (*first, filled_at)
    if soonest is None:
        raise SituationUnavailable(
            f"No club {listing.name.value} plays at that books at once sells a "
            f"{body.sport.value.lower()} hour she and three of the group — seed "
            f"accounts with a card saved — are all free for."
        )

    cut_off, hour, free, filled_at = soonest
    three = free[: SPORT_SPECS[body.sport].players - 1]
    answer = _booked(
        await earlier.all_say_yes(
            group_id=body.group_id,
            sport=body.sport,
            club_id=hour.club_id,
            hour=hour,
            players=(*three, her),
            at=filled_at,
        ),
        hour,
    )
    leaver, *staying = three
    await leave.execute(
        LeaveTheGameCommand(booking_id=answer.proposal_id, player_id=leaver)
    )
    named = await names.names_of((*three, her))
    club = (await clubs.names_of([hour.club_id])).get(hour.club_id)
    return EmptySeatResponse(
        game_id=answer.proposal_id,
        starts_at=hour.start,
        cut_off=cut_off,
        club_id=hour.club_id,
        club_name=club,
        people_in=[
            PersonRef(player_id=player, name=named.get(player))
            for player in (*staying, her)
        ],
        left=PersonRef(player_id=leaver, name=named.get(leaver)),
        says=(
            f"Her game {_when(hour.start)} at {club or 'the club'}, booked earlier; "
            f"{named.get(leaver, 'one of the three')} left it just now — a seat is "
            f"open, their share refunded less the card fee, the seat offered to "
            f"the group's best fits. The cut-off {fires_at(cut_off, now=now)}: a "
            f"seat still open then calls the game off and refunds everybody in "
            f"full."
        ),
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
    earlier: EarlierYesesDep,
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
        answer = _booked(
            await earlier.all_say_yes(
                group_id=body.group_id,
                sport=body.sport,
                club_id=club_id,
                hour=hour,
                players=(*three, her),
                at=filled_at,
            ),
            hour,
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


# --------------------------------------------------------------------------- #
# 12 · Club day close
# --------------------------------------------------------------------------- #


@router.post(
    "/club-day-close",
    response_model=ClubDayCloseResponse,
    responses=_REFUSED,
    summary="Situation 12 · Club day close",
    description=(
        "Writes the last closed club day's played games — yesterday's, or "
        f"today's from {DAY_CLOSES}:00 — at a club of the group's that books at "
        "once and has had no day close for it yet: up to "
        f"{DAY_CLOSE_GAMES}, each a game's worth of the group, never the "
        "protagonist, booked inside that day on a clock backdated to it. Once "
        "the outbox has captured the shares, *Run it now* on club payouts pays "
        "the club for them, and on the new bookings summary emails its desk "
        "the day's bookings."
    ),
)
async def club_day_close(
    body: ClubDayCloseRequest,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    hours_finder: HourFinderDep,
    club_courts: ClubCourtsRepositoryDep,
    earlier: EarlierYesesDep,
    payouts: ClubPayoutRepositoryDep,
    summaries: SummaryRepositoryDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
) -> ClubDayCloseResponse:
    listing = await the_group(groups, body.group_id)
    now = instant(clock.now())
    day = last_closed_day(now)
    # The day's bookings are those made from the close before it.
    opens = day_closes_at(day - timedelta(days=1))
    closes = day_closes_at(day)
    players = SPORT_SPECS[body.sport].players
    kept_off = () if body.protagonist_id is None else (body.protagonist_id,)

    closed_out: list[UUID] = []
    for club_id in await hours_finder.clubs(body.group_id, on_request=False, now=now):
        if (
            await payouts.load(payout_id_for(club_id, day)) is not None
            or await summaries.load(summary_id_for(club_id, day)) is not None
        ):
            # Games written into a day already closed out wait for tonight's.
            closed_out.append(club_id)
            continue
        notice = timedelta(
            hours=(await club_courts.load(club_id)).settings.minimum_notice_hours
        )
        seated: set[UUID] = set()
        played: list[tuple[CourtHourOnSale, Sequence[UUID], Instant, UUID]] = []
        for hour, free in await hours_finder.hours_free(
            listing,
            club_id,
            body.sport,
            her=None,
            leaving_out=kept_off,
            on_sale_at=opens,
            start=opens,
            end=closes,
        ):
            on_it = [player for player in free if player not in seated][:players]
            if len(on_it) < players:
                continue
            filled_at = max(opens, instant(hour.start - notice - BEFORE_THE_NOTICE))
            answer = _booked(
                await earlier.all_say_yes(
                    group_id=body.group_id,
                    sport=body.sport,
                    club_id=club_id,
                    hour=hour,
                    players=on_it,
                    at=filled_at,
                ),
                hour,
            )
            seated.update(on_it)
            played.append((hour, on_it, filled_at, answer.proposal_id))
            if len(played) == DAY_CLOSE_GAMES:
                break
        if not played:
            continue
        named = await names.names_of(seated)
        club = (await clubs.names_of([club_id])).get(club_id)
        return ClubDayCloseResponse(
            club_id=club_id,
            club_name=club,
            day=day,
            closed_at=closes,
            games=[
                DayCloseGame(
                    game_id=game_id,
                    starts_at=hour.start,
                    booked_at=filled_at,
                    people=[PersonRef(player_id=p, name=named.get(p)) for p in on_it],
                )
                for hour, on_it, filled_at, game_id in played
            ],
            says=(
                f"{len(played)} game(s) at {club or 'the club'} on {day:%a %d %b}, "
                f"booked that day and played — the day closed at "
                f"{closes.astimezone(CLUB_ZONE):%H:%M}. Once the outbox has "
                f"captured the shares, *Run it now* on club payouts pays the club "
                f"for them, and on the new bookings summary emails its desk — or "
                f"each job's own next tick does."
            ),
        )

    named_clubs = await clubs.names_of(closed_out)
    closed = ", ".join(named_clubs.get(club_id, "a club") for club_id in closed_out)
    raise SituationUnavailable(
        f"{closed} had its day close for {day:%a %d %b} already — paid for it, or "
        f"its desk told — so games written into it would wait for tonight's."
        if closed_out
        else f"No club {listing.name.value} plays at that books at once sold a "
        f"{body.sport.value.lower()} hour on {day:%a %d %b} that a game's worth of the "
        f"group — seed accounts with a card saved, never her — were all free for."
    )

"""What the console shows: the groups to pick, and a group's board — a row per
seeded member with the cards they were dealt (``docs/adr/0194`` §2; #590).

**A read, recorded nowhere**, against one instant. Its two queries are the dev
surface's own (``routes.py`` says why), and every aggregate it shows is loaded
through the context's own repository, taken as a request dependency — so what a
row says is what the stream says, folded the way the context folds it.

**A row is somebody the console may act as.** A member the seed did not create
has no row — they are counted, so the tester knows the group has them — and the
board never lists a button the console would refuse. **A row's cards are the
games still filling that are anything to them**: dealt, In, or answered — with
their answer, and who is In — so the tester can see what each person can press.
Which press a phone would *offer* is the player's details' question
(``GET /proposals/{id}``); the console offers all three, and the use case says
what a person's own button would have said.

**And what the club row and the payment provider need** (#591): each row's
saved card and what the provider will do with its next payment — read off the
process's fake, the one the console steers, and ``null`` where the provider is
not it — and each booked seat's check-in code, as the phone shows it and the
desk would type it.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ClockDep, DbSession, UserRepositoryDep
from app.api.dev.accounts import seed_accounts_only
from app.api.dev.dependencies import (
    BookingRepositoryDep,
    CheckInCodesDep,
    ClubTermsDep,
    DeckPeopleDep,
    PlayerNamesDep,
)
from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, hours, instant, shifted
from app.modules.bookings.domain.booking import (
    Booking,
    BookingState,
    CalledOff,
    CancelReason,
)
from app.modules.bookings.domain.ports import BookingRepository, CheckInCodes
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import GroupDirectory, GroupListing
from app.modules.groups.presentation.dependencies import GroupDirectoryDep
from app.modules.payments.domain.entered_cards import CardBehaviour
from app.modules.payments.domain.ports import (
    PaymentMethodRepository,
    SeatChargeRepository,
)
from app.modules.payments.domain.provider import PaymentProvider
from app.modules.payments.domain.seat_charge import (
    FailureReason,
    SeatCharge,
    SeatChargeStatus,
)
from app.modules.payments.infrastructure.fake_payments import FakePayments
from app.modules.payments.presentation.dependencies import (
    PaymentMethodRepositoryDep,
    PaymentProviderDep,
    SeatChargeRepositoryDep,
)
from app.modules.proposals.application.proposal_details import ReadProposalDetails
from app.modules.proposals.domain.deck import SellingTerms, Sides
from app.modules.proposals.domain.errors import ProposalNotFound
from app.modules.proposals.domain.ports import ClubNames, ClubTerms, PlayerNames
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing
from app.modules.proposals.infrastructure.proposal_models import ProposalORM
from app.modules.proposals.presentation.dependencies import (
    ProposalClubNamesDep,
    ProposalRepositoryDep,
    ReadProposalDetailsDep,
)
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from app.seeds.catalog import THE_POPULATED_PLAYER

router = APIRouter(prefix="/groups", tags=["dev"])

#: How far back the board looks for a group's games: a game that started
#: within it is still shown, so one that has just been played is there to read.
LOOK_BACK = timedelta(days=1)


class CardOutcome(StrEnum):
    """What a saved card does with the next payment asked of it — what the
    payment provider's controls set (``provider.py``)."""

    #: Every payment goes through.
    SUCCEEDS = "SUCCEEDS"
    #: Every payment is declined.
    DECLINES = "DECLINES"
    #: The bank wants the player there to check every payment (3-D Secure).
    ASKS_FOR_VERIFICATION = "ASKS_FOR_VERIFICATION"


#: The test card each outcome makes a saved card behave as — what the controls
#: set, and read back the other way for a row.
CARD_BEHAVIOURS: Mapping[CardOutcome, CardBehaviour] = MappingProxyType(
    {
        CardOutcome.SUCCEEDS: CardBehaviour.SUCCEEDS,
        CardOutcome.DECLINES: CardBehaviour.DECLINES_PAYMENTS,
        CardOutcome.ASKS_FOR_VERIFICATION: CardBehaviour.CHECKED_EVERY_TIME,
    }
)


def outcome_of(behaviour: CardBehaviour) -> CardOutcome:
    """What a saved card does with a payment. A card the bank checked once,
    when it was saved, pays off-session; one it refused was never saved."""

    return next(
        (outcome for outcome, b in CARD_BEHAVIOURS.items() if b is behaviour),
        CardOutcome.SUCCEEDS,
    )


def steerable(provider: PaymentProvider) -> FakePayments | None:
    """The provider, when it is the in-process fake the console steers."""

    return provider if isinstance(provider, FakePayments) else None


# --------------------------------------------------------------------------- #
# The wire
# --------------------------------------------------------------------------- #


class PersonRef(BaseModel):
    player_id: UUID
    name: str | None = Field(
        description="Their Name; `null` for an account never named."
    )


class ConsoleGroup(BaseModel):
    group_id: UUID
    name: str
    club_name: str | None = Field(description="Its home club's name.")
    seed_members: int = Field(
        description="Members the console may act as — each is a row."
    )
    other_members: int = Field(
        description=(
            "Members the seed did not create: no row, since the console refuses "
            "to act as them."
        )
    )
    holds_the_protagonist: bool = Field(
        description="The seed's protagonist is a member — where the page opens."
    )


class GroupsResponse(BaseModel):
    protagonist: PersonRef | None = Field(
        description=(
            "The seed's default protagonist — the account the phone is signed in "
            "as while a QA plan is walked. `null` in a store the seed never ran "
            "in."
        )
    )
    sports: list[Sport] = Field(description="What a board may be read for.")
    groups: list[ConsoleGroup] = Field(
        description=(
            "Every group with a member the console may act as, by name. A group "
            "of nobody the seed created is not here."
        )
    )


class RowAnswer(StrEnum):
    """Where a person stands on a card, as its stream leaves it."""

    #: Dealt it, and not answered.
    DEALT = "DEALT"
    IN = "IN"
    SAID_NO = "SAID_NO"
    #: Took their yes back, and has not said it again.
    WITHDREW = "WITHDREW"
    #: The last yes reopened their seat — a payment that could not be held, or
    #: somebody In they no longer fit.
    REOPENED = "REOPENED"
    #: Another booking holds their week.
    PAUSED = "PAUSED"


class RowCard(BaseModel):
    proposal_id: UUID
    starts_at: datetime
    kind: SearchMode
    answer: RowAnswer
    open_seats: int
    people_in: list[PersonRef] = Field(description="Everybody In, in yes order.")


class CardOnFilePane(BaseModel):
    brand: str
    last_four: str
    outcome: CardOutcome | None = Field(
        description=(
            "What the provider does with the next payment on it; `null` where "
            "the provider is not the fake the console steers."
        )
    )


class PersonRow(BaseModel):
    player_id: UUID = Field(description="What a press on this row names.")
    email: str
    name: str | None
    photo_url: str | None = Field(
        description="A short-lived link to their face; `null` for none."
    )
    level: float | None = Field(
        description="Their published Level in the board's sport; `null` unrated."
    )
    card: CardOnFilePane | None = Field(
        description="Their saved card; `null` with none saved."
    )
    cards: list[RowCard] = Field(
        description=(
            "Every game in the group and sport still filling that is anything to "
            "them — dealt, In or answered — soonest first."
        )
    )


class ClubPane(BaseModel):
    club_id: UUID
    name: str | None
    confirms_each_game: bool | None = Field(
        description=(
            "`true` at an On request club, `false` at an Instant one; `null` for a "
            "club no longer selling through Raketa."
        )
    )


class VersionPerson(BaseModel):
    player_id: UUID
    name: str | None
    answer: RowAnswer


class VersionPane(BaseModel):
    number: int
    people: list[VersionPerson] = Field(description="Who it named, in dealt order.")


class SidesPane(BaseModel):
    first: list[PersonRef]
    second: list[PersonRef]


class DeparturePane(BaseModel):
    player: PersonRef
    side: str
    at: datetime
    rescued_by: PersonRef | None = Field(
        description="Who took the seat; `null` while it is open."
    )


class SeatCodePane(BaseModel):
    player: PersonRef
    short_code: str = Field(
        description=(
            "What the desk types — the phone shows it on the game's day. The "
            "club row's *Check in* sends it."
        )
    )


class BookingPane(BaseModel):
    state: BookingState
    court_name: str
    cut_off: datetime
    answer_by: datetime | None = Field(
        description="When the club's answer is due, on a booking put to it."
    )
    booked_at: datetime | None
    called_off: CalledOff | None
    cancel_reason: CancelReason | None
    departures: list[DeparturePane]
    checked_in: list[PersonRef]
    codes: list[SeatCodePane] = Field(
        description="Each seated player's check-in code, the first side first."
    )


class RefundPane(BaseModel):
    decided_at: datetime | None
    withholds_fee: bool = Field(description="Whether the card fee is kept back.")
    given_back_grosze: int = Field(
        description=(
            "What the provider gave back once it has; until then what was decided."
        )
    )
    fee_withheld_grosze: int | None = Field(
        description="The fee the provider kept; `null` until it has answered."
    )
    given_at: datetime | None = Field(
        description="When the provider gave it; `null` while it is on its way."
    )


class ChargePane(BaseModel):
    charge_id: UUID
    player: PersonRef
    amount_grosze: int
    status: SeatChargeStatus
    failure: FailureReason | None
    payment_id: str | None = Field(
        description="The payment at the provider; `null` if it was never asked."
    )
    opened_at: datetime
    taken_at: datetime | None
    refund: RefundPane | None


class GamePane(BaseModel):
    """One game, from its first card to its court: everything a tester checks
    the money and the people against."""

    game_id: UUID = Field(
        description="The proposal — and its booking's id, once it has one."
    )
    origin: Origin
    kind: SearchMode
    poster: PersonRef | None
    club: ClubPane
    starts_at: datetime = Field(description="The court hour.")
    book_by: datetime
    cut_off: datetime | None = Field(
        description=(
            "The booking's own once it has one; until then the club's cut-off as "
            "its settings stand. `null` for a club no longer selling."
        )
    )
    standing: Standing
    waiting_for_the_club: bool
    share_grosze: int
    seats: int
    open_seats: int
    people_in: list[PersonRef] = Field(description="Everybody In, in yes order.")
    versions: list[VersionPane]
    sides: SidesPane | None = Field(
        description=(
            "The booking's, once it has one; on a game still filling, as the "
            "people In stand on it now. `null` with nobody In."
        )
    )
    booking: BookingPane | None
    charges: list[ChargePane] = Field(description="Every one, oldest first.")


class PaymentsPane(BaseModel):
    steerable: bool = Field(
        description=(
            "The provider is the in-process fake, so the payment provider's "
            "controls steer it."
        )
    )
    refunds_wait: bool | None = Field(
        description=(
            "Every refund waits until it is delivered from the console; `null` "
            "where the provider is not the fake."
        )
    )


class BoardResponse(BaseModel):
    group: ConsoleGroup
    sport: Sport
    read_at: datetime = Field(description="The instant every row was read at.")
    payments: PaymentsPane
    people: list[PersonRow] = Field(
        description="A row per member the console may act as, in join order."
    )
    games: list[GamePane] = Field(
        description=(
            f"Every game in the group and sport whose hour began less than "
            f"{LOOK_BACK // timedelta(hours=1)} hours ago — filling, booked or over — "
            f"soonest first."
        )
    )


_NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "`group_not_found` — no such group.",
    }
}


# --------------------------------------------------------------------------- #
# The panes' reader, built per request
# --------------------------------------------------------------------------- #


class GamePanes:
    """Every game's pane, read once for the board: the booking and the charges
    of each, through their contexts' own repositories, and one question each
    for the names, the clubs and their terms. On a game still filling with
    somebody In, the sides are the player's own details read as the first of
    them — the evenest arrangement the engine forecasts, as their card draws it."""

    def __init__(
        self,
        *,
        bookings: BookingRepository,
        charges: SeatChargeRepository,
        names: PlayerNames,
        clubs: ClubNames,
        terms: ClubTerms,
        details: ReadProposalDetails,
        codes: CheckInCodes,
    ) -> None:
        self._bookings = bookings
        self._charges = charges
        self._names = names
        self._clubs = clubs
        self._terms = terms
        self._details = details
        self._codes = codes

    async def read(self, games: Sequence[Proposal], *, now: Instant) -> "_Folded":
        bookings: dict[UUID, Booking] = {}
        charges: dict[UUID, Sequence[SeatCharge]] = {}
        sides: dict[UUID, Sides] = {}
        for game in games:
            booking = await self._bookings.load(game.proposal_id)
            if booking is not None:
                bookings[game.proposal_id] = booking
            charges[game.proposal_id] = await self._charges.of_game(game.proposal_id)
            if (
                booking is None
                and game.yeses
                and game.standing_at(now) is Standing.FILLING
            ):
                try:
                    read = await self._details.execute(game.proposal_id, game.yeses[0])
                except ProposalNotFound:
                    continue
                sides[game.proposal_id] = read.sides

        club_ids = {game.club_id for game in games}
        return _Folded(
            now=now,
            names=await self._names.names_of(_everybody_on(games, bookings, charges)),
            clubs=await self._clubs.names_of(club_ids),
            terms=await self._terms.of(club_ids, now=now),
            bookings=bookings,
            charges=charges,
            sides=sides,
            codes=self._codes,
        )


def get_game_panes(
    bookings: BookingRepositoryDep,
    charges: SeatChargeRepositoryDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
    terms: ClubTermsDep,
    details: ReadProposalDetailsDep,
    codes: CheckInCodesDep,
) -> GamePanes:
    return GamePanes(
        bookings=bookings,
        charges=charges,
        names=names,
        clubs=clubs,
        terms=terms,
        details=details,
        codes=codes,
    )


GamePanesDep = Annotated[GamePanes, Depends(get_game_panes)]


# --------------------------------------------------------------------------- #
# The routes
# --------------------------------------------------------------------------- #


@router.get(
    "",
    response_model=GroupsResponse,
    summary="The groups to pick",
)
async def read_groups(
    db: DbSession,
    groups: GroupDirectoryDep,
    clubs: ProposalClubNamesDep,
    users: UserRepositoryDep,
) -> GroupsResponse:
    listings = await groups.listings(await groups.every())
    seed = await _seed_accounts_among(
        db, {member for listing in listings.values() for member in listing.members}
    )
    names = await clubs.names_of(
        {listing.home_club_id for listing in listings.values()}
    )
    protagonist = await the_protagonist(users)
    listed = [
        _console_group(listing, seed, names, protagonist)
        for listing in listings.values()
        if any(member in seed for member in listing.members)
    ]
    return GroupsResponse(
        protagonist=None
        if protagonist is None
        else PersonRef(
            player_id=protagonist.id,
            name=None if protagonist.name is None else protagonist.name.value,
        ),
        sports=list(Sport),
        groups=sorted(listed, key=lambda group: (group.name, group.group_id)),
    )


@router.get(
    "/{group_id}",
    response_model=BoardResponse,
    responses=_NOT_FOUND,
    summary="A group's board",
    description=(
        "A row per member the console may act as, with the cards they were "
        "dealt in the sport, and a state pane per game. Nothing is recorded."
    ),
)
async def read_board(
    group_id: UUID,
    sport: Sport,
    db: DbSession,
    clock: ClockDep,
    groups: GroupDirectoryDep,
    clubs: ProposalClubNamesDep,
    proposals: ProposalRepositoryDep,
    people: DeckPeopleDep,
    users: UserRepositoryDep,
    panes: GamePanesDep,
    methods: PaymentMethodRepositoryDep,
    provider: PaymentProviderDep,
) -> BoardResponse:
    now = instant(clock.now())
    listing = await the_group(groups, group_id)
    seed = await _seed_accounts_among(db, listing.members)
    club = await clubs.names_of([listing.home_club_id])

    games = [
        proposal
        for proposal_id in await _games_in(db, group_id, sport=sport, now=now)
        if (proposal := await proposals.load(proposal_id)) is not None
    ]
    filling = [game for game in games if game.standing_at(now) is Standing.FILLING]
    folded = await panes.read(games, now=now)

    rows_of = [member for member in listing.members if member in seed]
    drawn = await people.people(rows_of, sport=sport)
    fake = steerable(provider)
    cards = await _cards_of(methods, fake, rows_of)
    return BoardResponse(
        group=_console_group(listing, seed, club, await the_protagonist(users)),
        sport=sport,
        read_at=now,
        payments=PaymentsPane(
            steerable=fake is not None,
            refunds_wait=None if fake is None else fake.refunds_wait,
        ),
        people=[
            PersonRow(
                player_id=player,
                email=seed[player],
                name=drawn[player].name,
                photo_url=drawn[player].photo_url,
                level=drawn[player].level,
                card=cards.get(player),
                cards=[
                    _card(game, player, folded.names)
                    for game in filling
                    if game.is_on_it(player)
                ],
            )
            for player in rows_of
        ],
        games=[folded.pane(game) for game in games],
    )


async def the_group(groups: GroupDirectory, group_id: UUID) -> GroupListing:
    """The group a press names, or ``group_not_found``."""

    listing = (await groups.listings([group_id])).get(group_id)
    if listing is None:
        raise GroupNotFound()
    return listing


async def the_protagonist(users: UserRepository) -> User | None:
    """The seed's default protagonist — ``None`` in a store the seed never ran
    in."""

    return await users.get_by_email(THE_POPULATED_PLAYER.email)


# --------------------------------------------------------------------------- #
# Reads
# --------------------------------------------------------------------------- #


async def _seed_accounts_among(
    db: AsyncSession, player_ids: Collection[UUID]
) -> dict[UUID, str]:
    """Which of these are seed accounts — each with its address."""

    if not player_ids:
        return {}
    rows = await db.execute(
        select(UserORM.id, UserORM.email).where(
            UserORM.id.in_(player_ids), seed_accounts_only()
        )
    )
    return {row.id: row.email for row in rows}


async def _cards_of(
    methods: PaymentMethodRepository,
    fake: FakePayments | None,
    player_ids: Sequence[UUID],
) -> dict[UUID, CardOnFilePane]:
    """Each of these players' saved card — and, from the fake, what it does."""

    cards: dict[UUID, CardOnFilePane] = {}
    for player in player_ids:
        saved = (await methods.load(player)).method
        if saved is None:
            continue
        cards[player] = CardOnFilePane(
            brand=saved.brand,
            last_four=saved.last_four,
            outcome=None
            if fake is None
            else outcome_of(fake.card_behaviour_of(saved.method_id)),
        )
    return cards


async def _games_in(
    db: AsyncSession, pool_id: UUID, *, sport: Sport, now: Instant
) -> Sequence[UUID]:
    """Every game in the pool and sport whose hour began no earlier than
    ``LOOK_BACK`` ago, soonest first — filling or not."""

    rows = await db.execute(
        select(ProposalORM.id)
        .where(
            ProposalORM.pool_id == pool_id,
            ProposalORM.sport == sport.value,
            ProposalORM.start >= now - LOOK_BACK,
        )
        .order_by(ProposalORM.start, ProposalORM.id)
    )
    return list(rows.scalars())


# --------------------------------------------------------------------------- #
# Folding
# --------------------------------------------------------------------------- #


def _console_group(
    listing: GroupListing,
    seed: Collection[UUID],
    clubs: Mapping[UUID, str],
    protagonist: User | None,
) -> ConsoleGroup:
    acting = sum(1 for member in listing.members if member in seed)
    return ConsoleGroup(
        group_id=listing.id,
        name=listing.name.value,
        club_name=clubs.get(listing.home_club_id),
        seed_members=acting,
        other_members=len(listing.members) - acting,
        holds_the_protagonist=protagonist is not None
        and protagonist.id in listing.members,
    )


def _answer(game: Proposal, player: UUID) -> RowAnswer:
    if player in game.yeses:
        return RowAnswer.IN
    if player in game.declined:
        return RowAnswer.SAID_NO
    if player in game.paused:
        return RowAnswer.PAUSED
    if player in game.reopened:
        return RowAnswer.REOPENED
    if player in game.withdrawn:
        return RowAnswer.WITHDREW
    return RowAnswer.DEALT


def _card(game: Proposal, player: UUID, names: Mapping[UUID, str]) -> RowCard:
    return RowCard(
        proposal_id=game.proposal_id,
        starts_at=game.start,
        kind=game.kind,
        answer=_answer(game, player),
        open_seats=game.open_seats,
        people_in=[PersonRef(player_id=one, name=names.get(one)) for one in game.yeses],
    )


def _everybody_on(
    games: Sequence[Proposal],
    bookings: Mapping[UUID, Booking],
    charges: Mapping[UUID, Sequence[SeatCharge]],
) -> set[UUID]:
    """Everybody a pane names, for one question about their names."""

    on_games = {
        player
        for game in games
        for player in (
            *game.yeses,
            *(one for version in game.versions for one in version.players),
            *((game.poster_id,) if game.poster_id is not None else ()),
        )
    }
    on_bookings = {
        player
        for booking in bookings.values()
        for player in (
            *booking.first_side,
            *booking.second_side,
            *(departure.player_id for departure in booking.departures),
            *(
                departure.rescued_by
                for departure in booking.departures
                if departure.rescued_by is not None
            ),
        )
    }
    charged = {charge.player_id for each in charges.values() for charge in each}
    return on_games | on_bookings | charged


class _Folded:
    """The panes' reads, folded into a pane per game."""

    def __init__(
        self,
        *,
        now: Instant,
        names: Mapping[UUID, str],
        clubs: Mapping[UUID, str],
        terms: Mapping[UUID, SellingTerms],
        bookings: Mapping[UUID, Booking],
        charges: Mapping[UUID, Sequence[SeatCharge]],
        sides: Mapping[UUID, Sides],
        codes: CheckInCodes,
    ) -> None:
        self.names = names
        self._now = now
        self._clubs = clubs
        self._terms = terms
        self._bookings = bookings
        self._charges = charges
        self._sides = sides
        self._codes = codes

    def pane(self, game: Proposal) -> GamePane:
        booking = self._bookings.get(game.proposal_id)
        terms = self._terms.get(game.club_id)
        if booking is not None:
            cut_off: Instant | None = booking.cut_off
            sides: SidesPane | None = SidesPane(
                first=self._refs(booking.first_side),
                second=self._refs(booking.second_side),
            )
        else:
            cut_off = (
                None
                if terms is None
                else shifted(game.start, hours(-terms.cut_off_hours))
            )
            drawn = self._sides.get(game.proposal_id)
            sides = (
                None
                if drawn is None
                else SidesPane(
                    first=self._refs(drawn.yours), second=self._refs(drawn.theirs)
                )
            )
        return GamePane(
            game_id=game.proposal_id,
            origin=game.origin,
            kind=game.kind,
            poster=None if game.poster_id is None else self._ref(game.poster_id),
            club=ClubPane(
                club_id=game.club_id,
                name=self._clubs.get(game.club_id),
                confirms_each_game=None if terms is None else terms.confirms_each_game,
            ),
            starts_at=game.start,
            book_by=game.book_by,
            cut_off=cut_off,
            standing=game.standing_at(self._now),
            waiting_for_the_club=game.waiting_for_the_club,
            share_grosze=game.share_grosze,
            seats=game.seats,
            open_seats=game.open_seats,
            people_in=self._refs(game.yeses),
            versions=[
                VersionPane(
                    number=version.number,
                    people=[
                        VersionPerson(
                            player_id=player,
                            name=self.names.get(player),
                            answer=_answer(game, player),
                        )
                        for player in version.players
                    ],
                )
                for version in game.versions
            ],
            sides=sides,
            booking=None if booking is None else self._booking(booking),
            charges=[
                self._charge(charge)
                for charge in self._charges.get(game.proposal_id, ())
            ],
        )

    def _ref(self, player: UUID) -> PersonRef:
        return PersonRef(player_id=player, name=self.names.get(player))

    def _refs(self, players: Sequence[UUID]) -> list[PersonRef]:
        return [self._ref(player) for player in players]

    def _booking(self, booking: Booking) -> BookingPane:
        return BookingPane(
            state=booking.state,
            court_name=booking.court.name,
            cut_off=booking.cut_off,
            answer_by=booking.answer_by,
            booked_at=booking.booked_at,
            called_off=booking.called_off,
            cancel_reason=booking.cancel_reason,
            departures=[
                DeparturePane(
                    player=self._ref(departure.player_id),
                    side=departure.side,
                    at=departure.at,
                    rescued_by=None
                    if departure.rescued_by is None
                    else self._ref(departure.rescued_by),
                )
                for departure in booking.departures
            ],
            checked_in=self._refs(list(booking.checked_in)),
            codes=[
                SeatCodePane(
                    player=self._ref(player),
                    short_code=self._codes.code_for(
                        booking.booking_id, player
                    ).short_code,
                )
                for player in booking.players
            ],
        )

    def _charge(self, charge: SeatCharge) -> ChargePane:
        given = charge.refund_given
        return ChargePane(
            charge_id=charge.charge_id,
            player=self._ref(charge.player_id),
            amount_grosze=charge.amount_grosze,
            status=charge.status,
            failure=charge.failure,
            payment_id=charge.payment_id,
            opened_at=charge.opened_at,
            taken_at=charge.taken_at,
            refund=None
            if charge.refund_withholds_fee is None
            else RefundPane(
                decided_at=charge.refund_decided_at,
                withholds_fee=charge.refund_withholds_fee,
                given_back_grosze=charge.given_back_grosze,
                fee_withheld_grosze=None
                if given is None
                else given.fee_withheld_grosze,
                given_at=None if given is None else given.at,
            ),
        )

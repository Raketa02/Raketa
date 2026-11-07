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

**And what the payment provider needs** (#591): each row's saved card and what
the provider will do with its next payment — read off the process's fake, the
one the console steers, and ``null`` where the provider is not it.

**And a countdown on every pending moment** (#592): each moment still ahead on
a game that a timed rule acts at — its book-by, a payment due, its cut-off,
the close of its club day, the moment a stated score confirms — with the job
whose *Run it now* acts at it (``jobs.py``), so the tester presses at the right
time. A moment past is not counted down: the press acts on it now, and the next
refresh drops it.

**And what the rest of a row's buttons act on** (#593): the booked games they
hold a seat on — *Leave the game*, then the score and the attendance taps, named by
the Game each booking opened, whose record the pane shows — the group's rescues
they hold no seat on, each read through the rule *Fill in* and the deck read
(``RescueOffers``) for whether it is offered to them and dealt to them, and the
posts still filling they were never dealt, which a *Join* answers. As with the
cards, the console offers each press and the use case says what their own
button would have.
"""

from __future__ import annotations

import app.api.dev.refusal  # noqa: F401 — refuses first; see refusal.py

import math
from collections.abc import Collection, Mapping, Sequence
from datetime import datetime, timedelta
from enum import StrEnum
from types import MappingProxyType
from typing import Annotated, Any, NamedTuple
from uuid import UUID

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import ClockDep, DbSession, UserRepositoryDep
from app.api.dev.accounts import seed_accounts_only
from app.api.dev.dependencies import (
    ReaderRelationsDep,
    BookingRepositoryDep,
    ClubTermsDep,
    DeckPeopleDep,
    PlayerNamesDep,
    PoolsDep,
    RescueOffersDep,
)
from app.bootstrap.jobs import (
    CLUB_PAYOUTS_JOB,
    CUT_OFF_JOB,
    HOLDING_JOB,
    HOW_DID_IT_GO_JOB,
    NEW_BOOKINGS_SUMMARY_JOB,
    PROPOSAL_EXPIRY_JOB,
    RATING_CATCH_UP_JOB,
    TIME_TO_PAY_JOB,
)
from app.core.exception_handlers import ErrorResponse
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, hours, instant, shifted
from app.modules.bookings.domain.booking import (
    Answer,
    Booking,
    BookingState,
    CalledOff,
    CancelReason,
    Emptied,
)
from app.modules.bookings.domain.ports import BookingRepository
from app.modules.bookings.infrastructure.booking_models import BookingORM
from app.modules.clubs.domain.court_hours import CLUB_ZONE, day_close_after, local_day
from app.modules.games.domain.attendance import AttendanceState
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.results import Score
from app.modules.games.domain.standing import GameStanding, settled_at
from app.modules.games.domain.windows import (
    A_BOOKED_GAME,
    ENTRY_GRACE,
    PROPOSAL_WINDOW,
    hour_ends_at,
    late_claim_closes_at,
    proposal_closes_at,
    tap_window_closes_at,
)
from app.modules.games.presentation.dependencies import GameRepositoryDep
from app.modules.groups.domain.errors import GroupNotFound
from app.modules.groups.domain.ports import GroupDirectory, GroupListing
from app.modules.groups.presentation.dependencies import GroupDirectoryDep
from app.modules.payments.domain.entered_cards import CardBehaviour, CardKind
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
from app.modules.proposals.application.rescues import RescueOffers
from app.modules.proposals.domain.deck import SellingTerms, Sides
from app.modules.proposals.domain.errors import ProposalNotFound
from app.modules.proposals.domain.home import BookedGame
from app.modules.proposals.domain.ports import (
    ClubNames,
    ClubTerms,
    PlayerNames,
    Pools,
)
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
#: within it is still shown, so one that has just been played is there to read
#: — for as long as its result can still move (#593): its hour, the day to say
#: *we played*, and the day a score entered at the last of it waits for an
#: answer.
LOOK_BACK = A_BOOKED_GAME + ENTRY_GRACE + PROPOSAL_WINDOW


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


class CardNetwork(StrEnum):
    """The network a saved card holds a share on — which says how long a hold
    made without its player lasts at the provider (ADR-0190's 2026-10-10
    amendment): 4 days 18 hours on a Visa, 7 days on a Mastercard. Spelled as
    the provider names a brand."""

    VISA = "visa"
    MASTERCARD = "mastercard"


def network_of(brand: str) -> CardNetwork:
    """The network a card's brand holds on; any other is held as a Visa, the
    shortest window — as the fake holds it."""

    return CardNetwork.MASTERCARD if brand == "mastercard" else CardNetwork.VISA


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


class Moment(StrEnum):
    """A moment ahead on a game that a timed rule acts at — what a countdown
    counts down to, in the order a game meets them."""

    #: A card still filling is over at its book-by.
    BOOK_BY = "BOOK_BY"
    #: A refused share's time to pay ends (#625) — or, before the
    #: cut-off, its time to fix the card (#638), at the fill or at its holding
    #: (#639).
    PAYMENT_DUE = "PAYMENT_DUE"
    #: A share the fill only checked is held again: four days before the
    #: cut-off (#639).
    HOLDING = "HOLDING"
    #: Leaving stops being free: a full game's held shares are taken, and a
    #: seat still open calls the game off with every hold let go (#637).
    CUT_OFF = "CUT_OFF"
    #: A counted booked game's hour ends with nobody having put a score up:
    #: all four are asked *How did it go?* (#663).
    HOUR_ENDS = "HOUR_ENDS"
    #: The close of the club day it was booked in: its desk is emailed it among
    #: the day's new bookings.
    NEW_BOOKINGS_SUMMARY = "NEW_BOOKINGS_SUMMARY"
    #: The close of the club day it is played on: the club is paid for it.
    CLUB_PAYOUT = "CLUB_PAYOUT"
    #: A score stated on a counted game becomes final on its day of silence —
    #: two naming the same winner, on the later one's — and the rating catch-up
    #: moves the Levels. An agreement settles at once and waits on no moment.
    RESULT_CONFIRMS = "RESULT_CONFIRMS"


class MomentRule(NamedTuple):
    """The job whose *Run it now* acts at a moment, and what it does then."""

    job: str
    says: str


MOMENT_RULES: Mapping[Moment, MomentRule] = MappingProxyType(
    {
        Moment.BOOK_BY: MomentRule(
            PROPOSAL_EXPIRY_JOB,
            "Unfilled by then, the card is gone from every deck; the book-by "
            "sweep records it.",
        ),
        Moment.PAYMENT_DUE: MomentRule(
            TIME_TO_PAY_JOB,
            "Not fixed or paid by then, the payer's seat reopens for everybody "
            "and the holds the others kept are let go; a seat kept for a "
            "refused rescuer is offered to everybody again.",
        ),
        Moment.HOLDING: MomentRule(
            HOLDING_JOB,
            "The shares the fill only checked are held on their cards again, "
            "to stay until the cut-off; a card refused then gets thirty minutes "
            "to be fixed, the game still booked.",
        ),
        Moment.CUT_OFF: MomentRule(
            CUT_OFF_JOB,
            "Leaving stops being free: a full game has every held share taken, "
            "and a seat still open then calls the game off with every hold let "
            "go — nobody pays.",
        ),
        Moment.HOUR_ENDS: MomentRule(
            HOW_DID_IT_GO_JOB,
            "The hour ends: all four are asked How did it go? — unless a score "
            "is up by then, or somebody didn't come.",
        ),
        Moment.NEW_BOOKINGS_SUMMARY: MomentRule(
            NEW_BOOKINGS_SUMMARY_JOB,
            "The club's day closes: its desk is emailed this among the day's new "
            "bookings.",
        ),
        Moment.CLUB_PAYOUT: MomentRule(
            CLUB_PAYOUTS_JOB,
            "The club's day closes: it is paid what this game left it, once the "
            "money is settled.",
        ),
        Moment.RESULT_CONFIRMS: MomentRule(
            RATING_CATCH_UP_JOB,
            "Unless somebody answers first, the score is final by silence — with "
            "two scores naming the same winner, the closer one — and the rating "
            "catch-up moves the Levels. *That's right* settles it at once, and "
            "the outbox moves the Levels then.",
        ),
    }
)


def fires_at(at: Instant, *, now: Instant) -> str:
    """*fires at 15:00 · 40 min*: when a moment fires, on the clubs' clock —
    with the day, where it is not today — and how long until then, rounded up
    to the minute."""

    local = at.astimezone(CLUB_ZONE)
    when = (
        f"{local:%H:%M}"
        if local_day(at) == local_day(now)
        else f"{local:%a %d %b %H:%M}"
    )
    minutes = max(math.ceil((at - now).total_seconds() / 60), 0)
    left = (
        f"{minutes} min"
        if minutes < 120
        else f"{minutes // 60} h {minutes % 60:02d} min"
    )
    return f"fires at {when} · {left}"


# --------------------------------------------------------------------------- #
# The wire
# --------------------------------------------------------------------------- #


class PersonRef(BaseModel):
    player_id: UUID
    nickname: str | None = Field(
        description="Their nickname; `null` for an account with none."
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

    #: A post still filling they were never dealt: *Join* is a yes on it, which
    #: says whether they may.
    NOT_DEALT = "NOT_DEALT"
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


class RowBooked(BaseModel):
    """A booked game they hold a seat on — what *Leave the game*, a score and
    the attendance taps act on."""

    booking_id: UUID = Field(
        description=(
            "The booking — its game's pane's `game_id`, and what *Leave the game* "
            "names."
        )
    )
    game_id: UUID | None = Field(
        description=(
            "The Game it opened — what a score, an agreement and an attendance "
            "tap name. `null` on a game that waited for a payment and has no "
            "booking."
        )
    )
    starts_at: datetime
    state: BookingState
    standing: GameStanding | None = Field(
        description="What its Game is at `read_at`; `null` with no Game."
    )


class RowRescue(BaseModel):
    """A rescue in the group they hold no seat on — what *Take the seat* and
    *No* act on."""

    booking_id: UUID
    starts_at: datetime
    kind: SearchMode
    open_seats: int
    people_on: list[PersonRef] = Field(description="Everybody on it, side A first.")
    offered: bool = Field(
        description=(
            "On their *Fill in*: they fit everybody on it and are free for it — "
            "*Take the seat* is open to them."
        )
    )
    dealt: bool = Field(
        description="A *Seat open* card in their deck: one of its best fits."
    )
    said_no: bool = Field(description="They said no to its card.")


class RowFriendsSeat(BaseModel):
    person: PersonRef
    #: ``IN``, ``WAITING``, ``DECLINED`` or ``RAN_OUT`` — the last read off
    #: the clock too — or, nobody's since (#752), ``LEFT`` and ``SEAT_OPEN``.
    state: str
    #: An empty seat's name — what *Invite a friend* and *Open to the group*
    #: press on (#752); ``None`` on a seat somebody holds or is held for.
    seat_of: UUID | None = None
    #: Every friend invited into this empty seat, still to answer.
    invited: list[PersonRef] = Field(default_factory=list)


class RowFriendsGame(BaseModel):
    """A friends game in the group they sent, are In on or are invited to —
    what *Accept*, *Not this time* and *Call it off* act on (#751)."""

    booking_id: UUID
    starts_at: datetime
    kind: SearchMode
    pay_mode: str = Field(description="`SPLIT_THE_COST` or `WHOLE_COURT`.")
    sender: PersonRef
    state: BookingState
    seats: list[RowFriendsSeat] = Field(description="The sender's first.")
    you_are_the_sender: bool
    invited_until: datetime | None = Field(
        description="Their own invitation's end, while it waits on them."
    )
    cut_off: datetime


class CardOnFilePane(BaseModel):
    brand: str
    last_four: str
    outcome: CardOutcome | None = Field(
        description=(
            "What the provider does with the next payment on it; `null` where "
            "the provider is not the fake the console steers."
        )
    )
    kind: CardKind | None = Field(
        description=(
            "Which kind of card the provider takes it for, and so the fee it "
            "keeps when the share is taken; `null` where the provider is not "
            "the fake."
        )
    )
    network: CardNetwork | None = Field(
        description=(
            "The network the provider holds a share on, and so how long the "
            "hold lasts; `null` where the provider is not the fake."
        )
    )


class PersonRow(BaseModel):
    player_id: UUID = Field(description="What a press on this row names.")
    email: str
    nickname: str | None
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
            "them — dealt, In or answered — and every post still filling they "
            "were never dealt (`NOT_DEALT`), soonest first."
        )
    )
    booked: list[RowBooked] = Field(
        description=(
            "Every game on the board they hold a seat on, booked or put to its "
            "club, soonest first."
        )
    )
    rescues: list[RowRescue] = Field(
        description=(
            "Every rescue in the group and sport with a seat to take now that "
            "they hold no seat on, soonest first."
        )
    )
    friends_games: list[RowFriendsGame] = Field(
        default_factory=list,
        description=(
            "Every friends game in the group and sport they sent, are In on or "
            "are invited to, soonest first (#751)."
        ),
    )
    friends: list[PersonRef] = Field(
        default_factory=list,
        description=(
            "Their friends among the board's rows — whom *Send a friends game* "
            "seats beside them, in the board's order (#751)."
        ),
    )


class ClubPane(BaseModel):
    club_id: UUID
    name: str | None


class VersionPerson(BaseModel):
    player_id: UUID
    nickname: str | None
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


class BookingPane(BaseModel):
    state: BookingState
    court_name: str
    #: The court's kind, which a move keeps (#671).
    indoor: bool
    cut_off: datetime
    booked_at: datetime
    called_off: CalledOff | None
    cancel_reason: CancelReason | None
    departures: list[DeparturePane]


class ScorePane(BaseModel):
    """A score on the table."""

    side: GameSide = Field(description="Whose score it is.")
    by: PersonRef
    sets: str = Field(description="Side A's games first in each set: *6–4 6–3*.")
    at: datetime
    answer_by: datetime = Field(
        description="When the other side's silence agrees with it."
    )


class AttendancePane(BaseModel):
    """Somebody tapped *isn't here yet* (#657), and what became of it at
    `read_at` — the player's own read of it (`GameSchema.attendance`)."""

    player: PersonRef
    state: AttendanceState
    noted_at: datetime
    arrive_by: datetime = Field(description="The tap window's end, 30 min in.")
    arrived_at: datetime | None
    claim_by: datetime = Field(
        description="The end of the day for *I was there* and its confirmation."
    )
    claimed_at: datetime | None
    confirmed_at: datetime | None


class ResultPane(BaseModel):
    """The Game a booking opened: whether it was played, and what was said
    about it."""

    game_id: UUID = Field(
        description=(
            "The Game's own id — what a score, an agreement and an attendance "
            "tap name; "
            "not the pane's `game_id`, which is the proposal's and the "
            "booking's."
        )
    )
    standing: GameStanding
    counted: bool = Field(description="A competitive game: a result moves Levels.")
    entry_closes_at: datetime = Field(
        description="When *we played* stops being sayable."
    )
    scores: list[ScorePane] = Field(
        description="Every score on the table, side A's first — two disagree."
    )
    agreed_by: PersonRef | None = Field(
        description=(
            "Who said *That's right* to the other side's score — which settled "
            "it at once (#654). `null` on a result silence settled."
        )
    )
    confirmed: str | None = Field(description="The agreed score, once final.")
    attendance: list[AttendancePane] = Field(
        description="Everybody tapped *isn't here yet*; empty on an ordinary game."
    )


class RefundPane(BaseModel):
    decided_at: datetime | None
    withholds_fee: bool = Field(
        description="Whether the fee kept on the payment is kept back."
    )
    given_back_grosze: int | None = Field(
        description=(
            "What the provider gave back once it has; until then what was "
            "decided — `null` while that waits on a fee not yet known (#641)."
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
    held_until: datetime | None = Field(
        description=(
            "The cut-off a share held for the booked game is taken at (#637) — "
            "`HELD` until then, let go (`RELEASING`, `CANCELLED`) by a leave, a "
            "game short at it or the club's cancel before it. `null` for a "
            "share never held for the game."
        )
    )
    taken_at: datetime | None
    refund: RefundPane | None


class MomentPane(BaseModel):
    """A pending moment, and the *Run it now* that acts at it."""

    moment: Moment
    at: datetime = Field(description="When it fires — the countdown's end.")
    job: str = Field(
        description="The job that acts at it: `POST /dev/jobs/{job}` once it is due."
    )
    says: str = Field(description="What happens then, for the tester.")


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
    result: ResultPane | None = Field(
        description="The Game its booking opened; `null` until it has one."
    )
    charges: list[ChargePane] = Field(description="Every one, oldest first.")
    moments: list[MomentPane] = Field(
        description=(
            "Every moment still ahead at `read_at` that a timed rule acts at, "
            "soonest first — each a countdown. A moment past is not listed: its "
            "job acts on it at the next press or tick."
        )
    )


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
    """Every game's pane, read once for the board: the booking, the Game it
    opened and the charges of each, through their contexts' own repositories,
    and one question each for the names, the clubs and their terms. On a game
    still filling with somebody In, the sides are the player's own details read
    as the first of them — the evenest arrangement the engine forecasts, as
    their card draws it."""

    def __init__(
        self,
        *,
        bookings: BookingRepository,
        games: GameRepository,
        charges: SeatChargeRepository,
        names: PlayerNames,
        clubs: ClubNames,
        terms: ClubTerms,
        details: ReadProposalDetails,
    ) -> None:
        self._bookings = bookings
        self._games = games
        self._charges = charges
        self._names = names
        self._clubs = clubs
        self._terms = terms
        self._details = details

    async def read(self, games: Sequence[Proposal], *, now: Instant) -> "_Folded":
        bookings: dict[UUID, Booking] = {}
        played: dict[UUID, Game] = {}
        charges: dict[UUID, Sequence[SeatCharge]] = {}
        sides: dict[UUID, Sides] = {}
        for game in games:
            booking = await self._bookings.load(game.proposal_id)
            if booking is not None:
                bookings[game.proposal_id] = booking
                opened = (
                    None
                    if booking.game_id is None
                    else await self._games.load(booking.game_id)
                )
                if opened is not None:
                    played[game.proposal_id] = opened
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
            played=played,
            charges=charges,
            sides=sides,
        )


def get_game_panes(
    bookings: BookingRepositoryDep,
    games: GameRepositoryDep,
    charges: SeatChargeRepositoryDep,
    names: PlayerNamesDep,
    clubs: ProposalClubNamesDep,
    terms: ClubTermsDep,
    details: ReadProposalDetailsDep,
) -> GamePanes:
    return GamePanes(
        bookings=bookings,
        games=games,
        charges=charges,
        names=names,
        clubs=clubs,
        terms=terms,
        details=details,
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
            nickname=(
                None if protagonist.nickname is None else protagonist.nickname.value
            ),
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
    offers: RescueOffersDep,
    pools: PoolsDep,
    bookings: BookingRepositoryDep,
    relations: ReaderRelationsDep,
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
    rescues = _rescues_of(
        await read_rescues(offers, pools, group_id, sport=sport, now=now),
        rows_of,
        folded.names,
    )
    friends_games = [
        booking
        for booking_id in await _friends_games_in(db, group_id, sport=sport, now=now)
        if (booking := await bookings.load(booking_id)) is not None
    ]
    named: dict[UUID, str] = {}
    for player in rows_of:
        nickname = drawn[player].nickname
        if nickname is not None:
            named[player] = nickname
    friends_of: dict[UUID, list[UUID]] = {}
    for player in rows_of:
        theirs = set(await relations.friends_among(player, rows_of))
        friends_of[player] = [friend for friend in rows_of if friend in theirs]
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
                nickname=drawn[player].nickname,
                photo_url=drawn[player].photo_url,
                level=drawn[player].level,
                card=cards.get(player),
                cards=[
                    _card(game, player, folded.names)
                    for game in filling
                    if game.is_on_it(player) or game.origin is Origin.POST
                ],
                booked=folded.booked_by(player),
                rescues=rescues.get(player, []),
                friends_games=[
                    _friends_game(game, player, named, now=now)
                    for game in friends_games
                    if player in game.players or game.invitation_of(player) is not None
                ],
                friends=[
                    PersonRef(player_id=friend, nickname=named.get(friend))
                    for friend in friends_of[player]
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
            kind=None if fake is None else fake.card_kind_of(saved.method_id),
            network=None
            if fake is None
            else network_of(fake.card_network_of(saved.method_id)),
        )
    return cards


class RescueRead(NamedTuple):
    """A rescue with a seat to take, and who it is open to."""

    game: BookedGame
    #: Every member it is offered to — on their *Fill in* — in the group's
    #: order.
    offered: tuple[UUID, ...]
    #: Its best fits: a *Seat open* card in their deck.
    best_fits: frozenset[UUID]


async def read_rescues(
    offers: RescueOffers,
    pools: Pools,
    group_id: UUID,
    *,
    sport: Sport,
    now: Instant,
) -> list[RescueRead]:
    """The group's rescues in the sport with a seat to take now, soonest
    first, each read over every member as *Fill in* and the deck read it —
    one pair rule per kind, never one per game (``RescueOffers``)."""

    games = await offers.in_pool(group_id, sport=sport, now=now)
    pool = await pools.find(group_id)
    if not games or pool is None:
        return []
    everybody = await offers.candidates(
        await pools.members_of(pool), sport=sport, games=games, now=now
    )
    offered = await offers.offered(games, everybody, sport=sport, now=now)
    read: list[RescueRead] = []
    for game in games:
        # A no is the seat dealt to the next best fit: whoever said one holds
        # no place among them, as the deck reads it.
        fits = await offers.best_fits(
            game,
            [p for p in offered[game.booking_id] if p not in game.said_no],
            sport=sport,
        )
        read.append(RescueRead(game, offered[game.booking_id], fits.players))
    return read


def _rescues_of(
    rescues: Sequence[RescueRead],
    rows_of: Sequence[UUID],
    names: Mapping[UUID, str],
) -> dict[UUID, list[RowRescue]]:
    """Each row's rescues: every one they hold no seat on."""

    rows: dict[UUID, list[RowRescue]] = {}
    for rescue in rescues:
        for player in rows_of:
            if player in rescue.game.players:
                continue
            rows.setdefault(player, []).append(
                _rescue(
                    rescue.game,
                    names,
                    offered=player in rescue.offered,
                    dealt=player in rescue.best_fits,
                    said_no=player in rescue.game.said_no,
                )
            )
    return rows


def _rescue(
    game: BookedGame,
    names: Mapping[UUID, str],
    *,
    offered: bool,
    dealt: bool,
    said_no: bool,
) -> RowRescue:
    return RowRescue(
        booking_id=game.booking_id,
        starts_at=game.start,
        kind=game.kind,
        open_seats=game.open_seats,
        people_on=[
            PersonRef(player_id=player, nickname=names.get(player))
            for player in game.players
        ],
        offered=offered,
        dealt=dealt,
        said_no=said_no,
    )


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


async def _friends_games_in(
    db: AsyncSession, pool_id: UUID, *, sport: Sport, now: Instant
) -> Sequence[UUID]:
    """Every friends game in the pool and sport whose hour began no earlier
    than ``LOOK_BACK`` ago, soonest first (#751)."""

    rows = await db.execute(
        select(BookingORM.id)
        .where(
            BookingORM.pool_id == pool_id,
            BookingORM.sport == sport.value,
            BookingORM.sender_id.is_not(None),
            BookingORM.start >= now - LOOK_BACK,
        )
        .order_by(BookingORM.start, BookingORM.id)
    )
    return list(rows.scalars())


def _friends_game(
    booking: Booking, reader: UUID, names: Mapping[UUID, str], *, now: Instant
) -> RowFriendsGame:
    assert booking.sender is not None and booking.pay_mode is not None

    def ref(player: UUID) -> PersonRef:
        return PersonRef(player_id=player, nickname=names.get(player))

    def state_of(answer: Answer, until: Instant) -> str:
        if answer is Answer.WAITING and now >= until:
            return Answer.RAN_OUT.value
        return "IN" if answer is Answer.ACCEPTED else answer.value

    def invited_into(seat_of: UUID) -> list[PersonRef]:
        return [
            ref(seat.player_id)
            for seat in booking.invited
            if seat.seat_of == seat_of and seat.waiting_at(now)
        ]

    invited = booking.invitation_of(reader)
    return RowFriendsGame(
        booking_id=booking.booking_id,
        starts_at=booking.start,
        kind=booking.kind,
        pay_mode=booking.pay_mode.value,
        sender=ref(booking.sender),
        state=booking.state,
        seats=[
            # Everybody In, the sender first; then each seat the card still
            # holds for its friend; then each seat nobody holds (#752).
            *(
                RowFriendsSeat(person=ref(player), state="IN")
                for player in sorted(
                    booking.players, key=lambda one: one != booking.sender
                )
            ),
            *(
                RowFriendsSeat(
                    person=ref(seat.player_id),
                    state=state_of(seat.answer, seat.until),
                    seat_of=seat.player_id if now >= seat.until else None,
                )
                for seat in booking.invited
                if seat.seat_of is None and seat.answer is Answer.WAITING
            ),
            *(
                RowFriendsSeat(
                    person=ref(empty.seat_of),
                    state={
                        Emptied.DECLINED: Answer.DECLINED.value,
                        Emptied.RAN_OUT: Answer.RAN_OUT.value,
                        Emptied.LEFT: "LEFT",
                    }[empty.how],
                    seat_of=empty.seat_of,
                    invited=invited_into(empty.seat_of),
                )
                for empty in booking.empty
            ),
            *(
                RowFriendsSeat(
                    person=ref(left.player_id),
                    state="SEAT_OPEN",
                    seat_of=left.player_id,
                    invited=invited_into(left.player_id),
                )
                for left in booking.open_departures
            ),
        ],
        you_are_the_sender=booking.sender == reader,
        invited_until=invited.until
        if invited is not None and invited.waiting_at(now) and booking.is_booked
        else None,
        cut_off=booking.cut_off,
    )


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
    if not game.is_on_it(player):
        return RowAnswer.NOT_DEALT
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
        people_in=[
            PersonRef(player_id=one, nickname=names.get(one)) for one in game.yeses
        ],
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
        played: Mapping[UUID, Game],
        charges: Mapping[UUID, Sequence[SeatCharge]],
        sides: Mapping[UUID, Sides],
    ) -> None:
        self.names = names
        self._now = now
        self._clubs = clubs
        self._terms = terms
        self._bookings = bookings
        self._played = played
        self._charges = charges
        self._sides = sides

    def booked_by(self, player: UUID) -> list[RowBooked]:
        """Every game on the board this player holds a seat on, soonest first
        — the bookings are read in the games' order."""

        return [
            RowBooked(
                booking_id=booking.booking_id,
                game_id=booking.game_id,
                starts_at=booking.start,
                state=booking.state,
                standing=None if played is None else played.standing_at(self._now),
            )
            for proposal_id, booking in self._bookings.items()
            if player in booking.players
            for played in (self._played.get(proposal_id),)
        ]

    def pane(self, game: Proposal) -> GamePane:
        booking = self._bookings.get(game.proposal_id)
        played = self._played.get(game.proposal_id)
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
            club=ClubPane(club_id=game.club_id, name=self._clubs.get(game.club_id)),
            starts_at=game.start,
            book_by=game.book_by,
            cut_off=cut_off,
            standing=game.standing_at(self._now),
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
                            nickname=self.names.get(player),
                            answer=_answer(game, player),
                        )
                        for player in version.players
                    ],
                )
                for version in game.versions
            ],
            sides=sides,
            booking=None if booking is None else self._booking(booking),
            result=None if played is None else self._result(played),
            charges=[
                self._charge(charge)
                for charge in self._charges.get(game.proposal_id, ())
            ],
            moments=self._moments(game, booking, played),
        )

    def _moments(
        self, game: Proposal, booking: Booking | None, played: Game | None
    ) -> list[MomentPane]:
        """Each moment the game's record still has ahead of it."""

        ahead: list[tuple[Moment, Instant]] = []
        if game.standing_at(self._now) is Standing.FILLING:
            ahead.append((Moment.BOOK_BY, game.book_by))
        if game.ending is None and game.pay_by is not None:
            ahead.append((Moment.PAYMENT_DUE, game.pay_by))
        checked = [
            charge.hold_at
            for charge in self._charges.get(game.proposal_id, ())
            if charge.status is SeatChargeStatus.CHECKED and charge.hold_at is not None
        ]
        if checked:
            ahead.append((Moment.HOLDING, min(checked)))
        if booking is not None and booking.cards_to_fix:
            # A refused holding's time to fix the card (#639).
            ahead.append(
                (
                    Moment.PAYMENT_DUE,
                    min(to_fix.until for to_fix in booking.cards_to_fix.values()),
                )
            )
        kept = [] if booking is None else list(booking.kept_until.values())
        if any(until > self._now for until in kept):
            # A seat kept for a refused rescuer (#640), its time still running.
            ahead.append(
                (Moment.PAYMENT_DUE, min(until for until in kept if until > self._now))
            )
        if booking is not None:
            if booking.is_booked:
                ahead.append((Moment.CUT_OFF, booking.cut_off))
            # Whatever it came to since: the summary marks a game called off,
            # and the payout nets what one gave back.
            ahead.append(
                (Moment.NEW_BOOKINGS_SUMMARY, day_close_after(booking.booked_at))
            )
            ahead.append((Moment.CLUB_PAYOUT, day_close_after(booking.start)))
        if (
            played is not None
            and played.kind is GameKind.COUNTED
            and played.starts_at is not None
            and played.standing_at(self._now) is GameStanding.AWAITING_ENTRY
        ):
            # Nobody has put a score up yet: they are asked for it at the
            # hour's end (#663).
            ahead.append((Moment.HOUR_ENDS, hour_ends_at(played.starts_at)))
        if (
            played is not None
            and played.kind is GameKind.COUNTED
            and played.standing_at(self._now) is GameStanding.AWAITING_ANSWER
        ):
            # The Game's own answer to *when does this become final*: the lone
            # score's day, or the later score's when two name the same winner —
            # none when two name different winners, which ends disputed and
            # moves no Level (#654).
            confirms = settled_at(
                kind=played.kind,
                proposals=played.proposals,
                acceptance=played.acceptance,
            )
            if confirms is not None:
                ahead.append((Moment.RESULT_CONFIRMS, confirms))
        order = list(Moment)
        return [
            MomentPane(
                moment=moment,
                at=at,
                job=MOMENT_RULES[moment].job,
                says=MOMENT_RULES[moment].says,
            )
            for moment, at in sorted(
                ahead, key=lambda one: (one[1], order.index(one[0]))
            )
            if at > self._now
        ]

    def _ref(self, player: UUID) -> PersonRef:
        return PersonRef(player_id=player, nickname=self.names.get(player))

    def _refs(self, players: Sequence[UUID]) -> list[PersonRef]:
        return [self._ref(player) for player in players]

    def _booking(self, booking: Booking) -> BookingPane:
        return BookingPane(
            state=booking.state,
            court_name=booking.court.name,
            indoor=booking.court.indoor,
            cut_off=booking.cut_off,
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
        )

    def _result(self, played: Game) -> ResultPane:
        standing = played.standing_at(self._now)
        # The argument is on the table only while it is one, as the player's
        # own read of the game has it (``GameSchema.of``). An agreement is never
        # on it: *That's right* settles the game at once (#654), so who said it
        # is read off a confirmed game, beside the score it agreed with.
        arguing = standing is GameStanding.AWAITING_ANSWER
        agreement = played.settled_by_agreement_at(self._now)
        confirmed = played.confirmed_score_at(self._now)
        return ResultPane(
            game_id=played.id,
            standing=standing,
            counted=played.kind is GameKind.COUNTED,
            entry_closes_at=played.entry_closes_at,
            scores=[
                ScorePane(
                    side=proposal.side,
                    by=self._ref(proposal.by),
                    sets=sets_of(proposal.score),
                    at=proposal.at,
                    answer_by=proposal_closes_at(proposal.at),
                )
                for proposal in (played.standing_proposals() if arguing else ())
            ],
            agreed_by=None if agreement is None else self._ref(agreement.by),
            confirmed=None if confirmed is None else sets_of(confirmed),
            attendance=self._attendance(played),
        )

    def _attendance(self, played: Game) -> list[AttendancePane]:
        starts_at = played.starts_at
        if starts_at is None:
            return []
        return [
            AttendancePane(
                player=self._ref(player),
                state=state,
                noted_at=played.attendance[player].noted_at,
                arrive_by=tap_window_closes_at(starts_at),
                arrived_at=played.attendance[player].arrived_at,
                claim_by=late_claim_closes_at(starts_at),
                claimed_at=played.attendance[player].claimed_at,
                confirmed_at=played.attendance[player].confirmed_at,
            )
            for player, state in played.attendance_at(self._now).items()
        ]

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
            held_until=charge.held_until,
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


def sets_of(score: Score) -> str:
    """*6–4 6–3* — side A's games first in each set, as the score is held."""

    return " ".join(f"{one.a}–{one.b}" for one in score.sets)

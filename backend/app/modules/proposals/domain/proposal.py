"""The Proposal aggregate — event-sourced, one stream per proposed game.

A game that is still filling (``docs/adr/0189`` §5; the mechanics §5–§7): a pool,
a sport, a kind, a court hour at a club, the share fixed on it, the versions it
was dealt in, the yeses, and the book-by. Four rules shape it.

**Yeses are the game's, never a version's.** A version is only *who was shown
it*: the people In, and the names dealt for the seats still open. A yes on any
version counts toward the one game, so three versions with one yes each are a
game three people are In on (§7). The set of people In is the one fact every
later ticket reads.

**A version names people for the open seats and nobody twice.** At most three
versions, each person in one, never more names than seats still open, and never
somebody already on the game — In, dealt, or gone. **A seat a no left is dealt
again into the version it was on** — to at most three next best fits per open
seat (§6.2) — so re-dealing never spends a version. Breaking any of those is the
dealer's bug, so it is an ``invariant``; whether the people named *fit* each
other is a question about live facts, asked by the application before it deals.

**A no is final; a withdrawn yes is not.** A card swiped left never comes back
(§5.3) and the player is *declined* for good. A yes taken back is free (§6.5)
and is no verdict on the card: the player is *withdrawn*, their seat is open,
and while the game fills they may say yes again. Somebody In leaves by
withdrawing, never by a no.

**The book-by is the only deadline, and it is read off the clock.** A proposal
is *expired* from its book-by on whether or not anything has recorded it, so
every act asks ``standing_at`` with the caller's instant; ``expire`` writes the
record for whoever sweeps. A post whose poster withdrew with nobody else In is
*withdrawn*. A card whose last court at its club and hour went has *lost its
court hour* — read off the club, not the clock, so it is recorded by the
proposer that reads the club (#540).

**A post is for somebody** (#546): its *Who* and the range of the others'
Levels travel on ``ProposalMade``, so every fit it is ever dealt to is held to
the same two — and a member it was never dealt to may **join** it from the slot
sheet, which is their yes. Only a post: a pick is the engine's four, dealt by
name.

**Filled is the last yes booking it** (#541): every seat's share was taken and a
Booking opened under this proposal's id. When a share could not be held,
nobody paid, the game did not fill, and that player's **seat reopened** — open
again until they confirm the payment, or somebody else takes it. And a
player whose games per week another game just booked has their other yeses
that week **paused**: not counted, and **resumed** when their week has room again
— a game of theirs called off, or left (#544).

**No club confirms a game** (``docs/adr/0196`` §1): the last yes books it at
every club, so a full game never waits for a club's answer, and On request's
*turned down* ending is removed with it (#669).

**A booked game its club cancels is owed a new card** (#547): the proposal
still filled — the booking says it was cancelled, and why — but the people
still in when the club cancelled are dealt a new card first, until the proposer
deals it (``Redealt``). **That card is the owed card** (#673): it is born
knowing whom it is owed to (``owed_card_for``), which is what puts it first in
their decks.

**A refused share waits for its player: time to pay** (#625, #626; the
mechanics §12.2, Q109). When a share is refused as the game fills, nobody pays,
and the player **stays In, their seat held for them alone** for thirty minutes,
never past the book-by: nobody else is
dealt it or may take it, since the game is still full. *The reopening waits*:
paid in time, the game books on the holds the others kept; out of time, their
seat **reopens** (``TimeToPayRanOut``), as a refused share's always did. A seat
somebody else opens meanwhile falls the game back to filling while the payer's
time runs on — told as ``FellBackToFilling``.
**Before the club's cut-off it is time to fix the card** (#638; Q113): nothing
is taken then, only held, so the player is not asked to pay — the same thirty
minutes, never past the cut-off either; from the cut-off on, where money is
taken at once, it stays time to pay (``TimeTo``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Collection, Iterable, Sequence
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, instant, invariant
from app.modules.proposals.domain.errors import (
    ProposalAlreadyAnswered,
    ProposalIsFull,
    ProposalIsOver,
    ProposalNotFound,
)
from app.modules.proposals.domain.events import (
    ClubCancelled,
    CourtHourLost,
    FellBackToFilling,
    NoSaid,
    ProposalExpired,
    ProposalFilled,
    ProposalMade,
    ProposalWithdrawn,
    Redealt,
    SeatReopened,
    TimeToPayGiven,
    TimeToPayMet,
    TimeToPayRanOut,
    VersionDealt,
    YesPaused,
    YesResumed,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.limits import (
    NEXT_BEST_FITS_PER_SEAT,
    TIME_TO_PAY,
    VERSIONS_PER_PROPOSAL,
)
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.post import LevelRange, PostedFor, Who
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


class Origin(StrEnum):
    """Who proposed the game (the mechanics §8.1)."""

    #: The engine built it: a *Picked for you* card.
    PICK = "PICK"
    #: A member posted it: a *Challenge* card to everybody else.
    POST = "POST"


class Ending(StrEnum):
    """How a proposal stopped filling, as its stream records it."""

    #: The last yes booked it (#541).
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"
    COURT_HOUR_LOST = "COURT_HOUR_LOST"


class ReopenReason(StrEnum):
    """Why the last yes could not count somebody's yes, and reopened their seat."""

    #: Their share could not be held: the bank wants them to confirm it.
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    #: Their share could not be held: the bank refused it.
    DECLINED = "DECLINED"
    #: Their card's brand changed since they accepted the terms.
    TERMS_NEEDED = "TERMS_NEEDED"
    #: They have no method to charge.
    NO_METHOD = "NO_METHOD"
    #: They and somebody In may no longer share a court (§7).
    NO_LONGER_FITS = "NO_LONGER_FITS"


class Standing(StrEnum):
    """Where a proposal stands at an instant — derived, never stored."""

    FILLING = "FILLING"
    FILLED = "FILLED"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"
    COURT_HOUR_LOST = "COURT_HOUR_LOST"


@dataclass(frozen=True, slots=True)
class Reopened:
    """Why the last yes reopened somebody's seat, and the refused payment they
    may confirm — ``None`` where nothing was asked of the provider."""

    reason: ReopenReason
    seat_charge_id: UUID | None

    @property
    def payment_to_confirm(self) -> UUID | None:
        """The payment confirming which is their yes again (§12.2)."""

        return _to_confirm(self.reason, self.seat_charge_id)


def _to_confirm(reason: ReopenReason, seat_charge_id: UUID | None) -> UUID | None:
    """A refused payment its player confirms in the app — the bank's check, or
    a decline confirmed with another card; nothing for a refusal the provider
    was never asked about, nor a seat reopened because two no longer fit."""

    return (
        seat_charge_id
        if reason in (ReopenReason.AUTHENTICATION_REQUIRED, ReopenReason.DECLINED)
        else None
    )


#: The refusals a share's player is given time to pay after (Q109) — every
#: refusal of their payment; a seat reopened because two players no longer fit
#: is no payment of theirs.
PAYMENT_REFUSALS = frozenset(
    {
        ReopenReason.AUTHENTICATION_REQUIRED,
        ReopenReason.DECLINED,
        ReopenReason.TERMS_NEEDED,
        ReopenReason.NO_METHOD,
    }
)


class TimeTo(StrEnum):
    """What a refused share's thirty minutes are for (#638; the mechanics
    §12.2, Q113) — one machinery, two names, decided by the club's cut-off."""

    #: **Time to fix the card**: refused before the cut-off, where nothing is
    #: taken, only held — so nothing is paid in it; the player confirms with
    #: their bank or changes card, and the same hold runs again. Never past the
    #: cut-off.
    FIX_THE_CARD = "FIX_THE_CARD"
    #: **Time to pay**: refused from the cut-off on, where the money is taken
    #: at once.
    PAY = "PAY"

    @classmethod
    def at(cls, now: Instant, *, cut_off: Instant) -> "TimeTo":
        """What a share refused at ``now`` is given time for."""

        return cls.FIX_THE_CARD if now < cut_off else cls.PAY


@dataclass(frozen=True, slots=True)
class Paying:
    """A player In whose share was refused, and their **time to pay**: why it
    was refused, the refused payment, and until when the seat is theirs alone
    (#625, Q109) — and what the time is for (#638)."""

    reason: ReopenReason
    seat_charge_id: UUID
    until: Instant
    #: To fix the card, before the cut-off — or to pay, from it on (#638).
    time_to: TimeTo = TimeTo.PAY

    def __post_init__(self) -> None:
        invariant(
            self.reason in PAYMENT_REFUSALS, f"time to pay after {self.reason}"
        )

    @property
    def payment_to_confirm(self) -> UUID | None:
        """The payment confirming which pays in time — ``None`` where they
        accept the terms again, or save a method, and say yes again."""

        return _to_confirm(self.reason, self.seat_charge_id)


@dataclass(frozen=True, slots=True)
class DealtVersion:
    """One view of the game: the people named on it for the seats that were
    open when it was dealt, then the next best fits dealt into it for the seats
    its noes left — ``players[:first_named]`` and the rest."""

    number: int
    players: tuple[UUID, ...]
    #: How many it named when it was dealt — the seats it was dealt for.
    first_named: int


@dataclass
class Proposal:
    """One proposed game, as its stream leaves it."""

    proposal_id: UUID
    pool: Pool
    origin: Origin
    poster_id: UUID | None
    sport: Sport
    kind: SearchMode
    club_id: UUID
    start: Instant
    share_grosze: int
    book_by: Instant
    made_at: Instant
    #: Who a post is for — ``None`` on a pick, and on a post made before posts
    #: had a *Who*, which is for anybody.
    posted_for: PostedFor | None = None
    #: Whom this is **the owed card** for (#673): the people still in on a game
    #: its club cancelled — first in each one's deck. Empty on any other card.
    owed_card_for: tuple[UUID, ...] = ()
    versions: tuple[DealtVersion, ...] = ()
    #: Everybody In, in the order they said yes.
    yeses: tuple[UUID, ...] = ()
    #: Everybody who said no, in the order they did — for good.
    declined: tuple[UUID, ...] = ()
    #: Everybody who took their yes back and has not said it again.
    withdrawn: tuple[UUID, ...] = ()
    #: Everybody whose seat the last yes reopened, and who has not said yes
    #: again — each with why, and the refused payment they may confirm.
    reopened: dict[UUID, Reopened] = field(default_factory=dict)
    #: Everybody whose yes another game's booking paused, and has not said it
    #: again.
    paused: tuple[UUID, ...] = ()
    ending: Ending | None = None
    #: The people still in on a game its club cancelled have been dealt a new
    #: card first.
    redealt: bool = False
    #: Everybody still in when the club cancelled the booked game (#547) —
    #: ``None`` on a game no club cancelled.
    cancelled_for: tuple[UUID, ...] | None = None
    #: The player whose own act filled the booked game (Q102) — ``None`` until
    #: it is booked, and when a paused yes coming back did.
    filled_by: UUID | None = None
    #: Everybody In whose share was refused and whose time to pay runs (#625).
    paying: dict[UUID, Paying] = field(default_factory=dict)
    #: When the game first waited for a payment as it filled — it has no
    #: booking until it books, and is on its players' Home from then on
    #: (#625). ``None`` on every other game.
    payment_awaited_at: Instant | None = None
    #: When a full game waiting for a payment last went back to filling: a
    #: seat opened, or the time to pay ran out (#625) — ``None`` on any other.
    fell_back_at: Instant | None = None
    #: The last time to pay ran out at or after the book-by: the game cannot
    #: fill again — called off, a payment that did not come in time.
    ran_out_for_good: bool = False
    #: The game booked the moment a payment it waited for came in (#625): the
    #: four were told *It's a game!* already, so its booking is told as
    #: *booked · you paid*, never twice (Q110).
    booked_on_a_payment: bool = False
    #: Everybody In who paid in time while a seat was open, and the payment
    #: they confirmed — held for the fill, as any confirmed payment is.
    paid_in_time: dict[UUID, UUID] = field(default_factory=dict)
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def make(
        cls,
        *,
        proposal_id: UUID,
        pool: Pool,
        origin: Origin,
        poster_id: UUID | None,
        sport: Sport,
        kind: SearchMode,
        club_id: UUID,
        start: Instant,
        share_grosze: int,
        book_by: Instant,
        at: Instant,
        posted_for: PostedFor | None = None,
        owed_card_for: Sequence[UUID] = (),
    ) -> "Proposal":
        """A game proposed at a court hour. **A post is its poster's yes**, so
        it is born with them In. ``owed_card_for`` makes it the owed card for
        those people (#673) — only ever the engine's pick."""

        invariant(
            (origin is Origin.POST) == (poster_id is not None),
            f"a {origin} names a poster exactly when it is a post: {poster_id}",
        )
        invariant(
            origin is Origin.POST or posted_for is None,
            f"a pick is for nobody in particular: {posted_for}",
        )
        invariant(
            origin is Origin.PICK or not owed_card_for,
            f"a post is nobody's owed card: {owed_card_for}",
        )
        invariant(share_grosze > 0, f"a share of {share_grosze} grosze")
        invariant(
            at < book_by <= start,
            f"made at {at}, book by {book_by}, starting {start}",
        )
        made = ProposalMade(
            proposal_id=proposal_id,
            pool_id=pool.id,
            pool_kind=pool.kind.value,
            origin=origin.value,
            poster_id=poster_id,
            sport=sport.value,
            kind=kind.value,
            club_id=club_id,
            start=start,
            share_grosze=share_grosze,
            book_by=book_by,
            occurred_at=at,
            who=None if posted_for is None else posted_for.who.value,
            level_low=None if posted_for is None else posted_for.levels.low,
            level_high=None if posted_for is None else posted_for.levels.high,
            owed_card_for=tuple(owed_card_for),
        )
        proposal = cls._born(made)
        proposal._events.record(made)
        if poster_id is not None:
            proposal._record_that(
                YesSaid(proposal_id=proposal_id, player_id=poster_id, occurred_at=at)
            )
        return proposal

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Proposal":
        history = iter(events)
        made = next(history)
        invariant(isinstance(made, ProposalMade), f"a proposal stream opens {made!r}")
        assert isinstance(made, ProposalMade)
        proposal = cls._born(made)
        for event in history:
            proposal._apply(event)
        return proposal

    @classmethod
    def _born(cls, made: ProposalMade) -> "Proposal":
        return cls(
            proposal_id=made.proposal_id,
            pool=Pool(id=made.pool_id, kind=PoolKind(made.pool_kind)),
            origin=Origin(made.origin),
            poster_id=made.poster_id,
            sport=Sport(made.sport),
            kind=SearchMode(made.kind),
            club_id=made.club_id,
            start=instant(made.start),
            share_grosze=made.share_grosze,
            book_by=instant(made.book_by),
            made_at=instant(made.occurred_at),
            posted_for=_posted_for(made),
            owed_card_for=made.owed_card_for,
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ------------------------------------------------------------------ reads

    @property
    def seats(self) -> int:
        """Four for padel and badminton, two for tennis and squash."""

        return SPORT_SPECS[self.sport].players

    @property
    def seats_per_side(self) -> int:
        """Two in doubles, one in singles."""

        return self.seats // 2

    @property
    def open_seats(self) -> int:
        """Seats nobody is In on yet. Nought is a game every seat said yes to,
        which the fill turns into a booking (#541)."""

        return self.seats - len(self.yeses)

    @property
    def who(self) -> Who | None:
        """Who a post is for — ``None`` on a pick and on a post for anybody."""

        return None if self.posted_for is None else self.posted_for.who

    @property
    def poster_withdrew(self) -> bool:
        """A post whose poster is no longer In — *the group challenged you*
        (the mechanics §8.1)."""

        return self.poster_id is not None and self.poster_id not in self.yeses

    @property
    def waiting_for_a_payment(self) -> bool:
        """Every seat is In and a refused share's time to pay runs: the game
        waits for that payment, nobody else may take the seat, and paying in
        time books it (#625; Q111)."""

        return self.ending is None and self.open_seats == 0 and bool(self.paying)

    @property
    def payments_due(self) -> dict[UUID, Instant]:
        """Each player whose refused share the game waits for, and when their
        time to pay ends."""

        return {player: paying.until for player, paying in self.paying.items()}

    @property
    def pay_by(self) -> Instant | None:
        """When the payment the game waits for is due — the earliest, if more
        than one is awaited; ``None`` while none is."""

        return min(self.payments_due.values(), default=None)

    @property
    def fixing(self) -> frozenset[UUID]:
        """Those of the payers whose time is to fix the card (#638)."""

        return frozenset(
            player
            for player, paying in self.paying.items()
            if paying.time_to is TimeTo.FIX_THE_CARD
        )

    @property
    def time_to(self) -> TimeTo | None:
        """What the time of the payment due at ``pay_by`` is for — to fix the
        card, or to pay (#638); ``None`` while none is awaited. Everybody's at
        once is the same: a time to fix ends by the cut-off, and a payment is
        refused after it only on its own payer's act, which runs out first."""

        due = min(self.paying.values(), key=lambda one: one.until, default=None)
        return None if due is None else due.time_to

    def time_to_pay_ends(self, now: Instant, *, cut_off: Instant) -> Instant | None:
        """When a share refused at ``now`` has to be paid by (Q109): thirty
        minutes from now, **never past the book-by** — and, before the club's
        ``cut_off``, where it is time to fix the card, never past the cut-off
        either (#638). ``None`` when no time is left, the book-by having come.
        A payer refused again keeps the time they had (``give_time_to_pay``):
        it never moves."""

        ends = min(instant(now + TIME_TO_PAY), self.book_by)
        if TimeTo.at(now, cut_off=cut_off) is TimeTo.FIX_THE_CARD:
            ends = min(ends, cut_off)
        return ends if now < ends else None

    @property
    def owes_a_new_card(self) -> bool:
        """Its club cancelled it once booked (#547), and the people it owes
        have not been dealt a new card first yet."""

        return self.cancelled_for is not None and not self.redealt

    @property
    def owed_to(self) -> tuple[UUID, ...]:
        """Who a new card is dealt to first: everybody still in when the club
        cancelled the booked game — a leaver is not — and otherwise the people
        In, as a game that lost its court hour has them."""

        return self.yeses if self.cancelled_for is None else self.cancelled_for

    def standing_at(self, now: Instant) -> Standing:
        if self.ending is not None:
            return Standing(self.ending.value)
        if now >= self.book_by:
            return Standing.EXPIRED
        return Standing.FILLING

    def version_of(self, player_id: UUID) -> DealtVersion | None:
        """The version this player was dealt, if they were dealt one."""

        return next(
            (version for version in self.versions if player_id in version.players),
            None,
        )

    def is_on_it(self, player_id: UUID) -> bool:
        """Whether this game is anything to this player: dealt to them, said
        yes to by them, or answered by them."""

        return (
            player_id in self.yeses
            or player_id in self.declined
            or player_id in self.withdrawn
            or player_id in self.reopened
            or player_id in self.paused
            or self.version_of(player_id) is not None
        )

    # ------------------------------------------------------------------- acts

    def deal(
        self, players: Sequence[UUID], *, at: Instant, into: int | None = None
    ) -> DealtVersion:
        """Deal ``players`` the game: as a new version, naming them for the
        seats still open, or ``into`` an existing one — the next best fits for
        the seats its noes left. Whether they fit the people already In, and
        each other, is the caller's question, asked before this."""

        self._refuse_unless_filling(at)
        named = tuple(players)
        invariant(len(named) > 0, f"nobody named on {self.proposal_id}")
        invariant(len(set(named)) == len(named), f"somebody named twice: {named}")
        invariant(
            not any(self.is_on_it(player) for player in named),
            f"somebody in {named} is already on {self.proposal_id}",
        )
        if into is None:
            invariant(
                len(self.versions) < VERSIONS_PER_PROPOSAL,
                f"a {len(self.versions) + 1}th version of {self.proposal_id}",
            )
            invariant(
                len(named) <= self.open_seats,
                f"{len(named)} named for {self.open_seats} open seats",
            )
            number = len(self.versions) + 1
        else:
            invariant(
                1 <= into <= len(self.versions),
                f"no version {into} of {self.proposal_id}",
            )
            invariant(
                len(named) <= NEXT_BEST_FITS_PER_SEAT * self.open_seats,
                f"{len(named)} next best fits for {self.open_seats} open seats",
            )
            number = into
        self._record_that(
            VersionDealt(
                proposal_id=self.proposal_id,
                number=number,
                player_ids=named,
                occurred_at=at,
            )
        )
        return self.versions[number - 1]

    def may_say_yes(self, player_id: UUID, *, at: Instant) -> bool:
        """Whether a yes from this player would be recorded — ``False`` for one
        already In, which a repeated tap is — refusing what this game itself
        refuses. What the player's account and the people In have to say about
        it is the caller's."""

        self._refuse_a_stranger(player_id)
        return self._may_take_a_seat(player_id, at=at)

    def say_yes(self, player_id: UUID, *, at: Instant) -> None:
        if self.may_say_yes(player_id, at=at):
            self._record_a_yes(player_id, at=at)

    def may_join(self, player_id: UUID, *, at: Instant) -> bool:
        """Whether a member's *I'm in* from the slot sheet would be recorded
        (#546; the mechanics §9.1 step 6, Q79) — ``False`` for one already In.
        **Only a post is joined**: a pick is dealt to the people it names, and
        anybody else is a stranger to it. Whether the member may be on it —
        the pool, the post's *Who* and range, the people In — is the
        caller's."""

        if self.origin is not Origin.POST:
            self._refuse_a_stranger(player_id)
        return self._may_take_a_seat(player_id, at=at)

    def join(self, player_id: UUID, *, at: Instant) -> None:
        """A member's yes on a post they may never have been dealt — a yes
        like any other, In on the one game with no version of their own."""

        if self.may_join(player_id, at=at):
            self._record_a_yes(player_id, at=at)

    def say_no(self, player_id: UUID, *, at: Instant) -> None:
        """A swipe left. A second one records nothing."""

        self._refuse_a_stranger(player_id)
        self._refuse_unless_filling(at)
        if player_id in self.declined:
            return
        if player_id in self.yeses:
            raise ProposalAlreadyAnswered()
        self._record_that(
            NoSaid(proposal_id=self.proposal_id, player_id=player_id, occurred_at=at)
        )

    def withdraw_yes(self, player_id: UUID, *, at: Instant, own: bool = True) -> None:
        """The player takes their yes back. Withdrawing a yes they never said,
        or already took back, records nothing. **A poster withdrawing with
        nobody else In ends the post**; with others In the game carries on
        without them (the mechanics §9.3). ``own`` is false where it is not
        their act — another game booked their hour — which nobody is told
        by name (Q104)."""

        self._refuse_a_stranger(player_id)
        self._refuse_unless_filling(at)
        if player_id not in self.yeses:
            return
        waited = self.waiting_for_a_payment
        self._record_that(
            YesWithdrawn(
                proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
            )
        )
        self._fell_back_if(waited, player_id, left=own, at=at)
        if player_id == self.poster_id and not self.yeses:
            self._record_that(
                ProposalWithdrawn(
                    proposal_id=self.proposal_id,
                    withdrawn_by=player_id,
                    occurred_at=at,
                )
            )

    def withdraw_paused_yes(self, player_id: UUID, *, at: Instant) -> bool:
        """Take back a yes another booking paused — the ordinary
        ``YesWithdrawn``, so it never comes back when the player's week frees.
        **Only a block asks this** (``docs/adr/0193`` §4): a paused yes is still
        the blocker's, and nothing may reappear on their behalf. Answers whether
        anything was recorded — nothing for a yes that is not paused, or a game
        no longer filling."""

        if self.standing_at(at) is not Standing.FILLING or player_id not in self.paused:
            return False
        self._record_that(
            YesWithdrawn(
                proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
            )
        )
        return True

    def fill(
        self,
        *,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        by: UUID | None,
        at: Instant,
    ) -> None:
        """**The last yes booked it**: every seat was taken, and these are the
        sides the people In were drawn on. Called by the fill once the money
        is held — never before. ``by`` is the player whose own act filled it,
        or ``None`` when no player's did (a resumed yes)."""

        self._refuse_unless_filling(at)
        invariant(self.open_seats == 0, f"filling {self.proposal_id} with seats open")
        invariant(
            sorted((*first_side, *second_side)) == sorted(self.yeses),
            f"sides {first_side} {second_side} for the people In {self.yeses}",
        )
        self._record_that(
            ProposalFilled(
                proposal_id=self.proposal_id,
                first_side=first_side,
                second_side=second_side,
                occurred_at=at,
                filled_by=by,
            )
        )

    def reopen_seat(
        self,
        player_id: UUID,
        *,
        reason: ReopenReason,
        seat_charge_id: UUID | None,
        at: Instant,
    ) -> None:
        """The last yes could not count this player's: their seat is open
        again."""

        invariant(
            player_id in self.yeses, f"{player_id} is not In on {self.proposal_id}"
        )
        waited = self.waiting_for_a_payment
        self._record_that(
            SeatReopened(
                proposal_id=self.proposal_id,
                player_id=player_id,
                seat_charge_id=seat_charge_id,
                reason=reason.value,
                occurred_at=at,
            )
        )
        self._fell_back_if(waited, player_id, left=False, at=at)

    def give_time_to_pay(
        self,
        player_id: UUID,
        *,
        reason: ReopenReason,
        seat_charge_id: UUID,
        until: Instant,
        time_to: TimeTo,
        filled_by: UUID | None,
        at: Instant,
    ) -> None:
        """This player's share of the full game was refused as it filled:
        **their seat is held for them alone** until ``until`` (#625; Q109), to
        fix the card or to pay (``time_to``, #638). A player refused again
        keeps the time they had, and what it is for: it never moves. Whether any
        time is left is the caller's question, asked of ``time_to_pay_ends``."""

        invariant(
            self.ending is None and self.open_seats == 0,
            f"{self.proposal_id} gives time to pay while not full",
        )
        invariant(
            player_id in self.yeses, f"{player_id} is not In on {self.proposal_id}"
        )
        invariant(reason in PAYMENT_REFUSALS, f"time to pay after {reason}")
        already = self.paying.get(player_id)
        ends = already.until if already is not None else until
        invariant(at < ends, f"{player_id} given until {ends} at {at}")
        self._record_that(
            TimeToPayGiven(
                proposal_id=self.proposal_id,
                player_id=player_id,
                seat_charge_id=seat_charge_id,
                reason=reason.value,
                until=ends,
                occurred_at=at,
                filled_by=filled_by,
                time_to=(time_to if already is None else already.time_to).value,
            )
        )

    def time_to_pay_met(self, player_id: UUID, *, at: Instant) -> None:
        """This player paid in time, and the game cannot book on it yet: a
        seat opened while it waited. They are In with their payment held."""

        invariant(
            player_id in self.paying and player_id in self.yeses,
            f"{player_id} has no time to pay on {self.proposal_id}",
        )
        self._record_that(
            TimeToPayMet(
                proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
            )
        )

    def run_out_of_time(self, *, at: Instant) -> tuple[UUID, ...]:
        """Every payer whose time to pay is up at ``at``: **their seat reopens**
        (Q109) — offered to others, theirs to take back while it is free.
        Answers whose; nothing on a game that ended, or whose times still run.
        Past the book-by too, as long as nothing recorded its end: the time to
        pay never outlasts it, and is what ends it."""

        if self.ending is not None:
            return ()
        lapsed = tuple(
            player
            for player in self.yeses
            if player in self.paying and self.paying[player].until <= at
        )
        if lapsed:
            self._record_that(
                TimeToPayRanOut(
                    proposal_id=self.proposal_id,
                    player_ids=lapsed,
                    occurred_at=at,
                    fixing=tuple(player for player in lapsed if player in self.fixing),
                )
            )
        return lapsed

    def pause_yes(self, player_id: UUID, *, at: Instant) -> bool:
        """This player's games per week are booked for this game's week: their
        yes stops counting. Answers whether anything was recorded — nothing for
        a player not In, or a game no longer filling."""

        if self.standing_at(at) is not Standing.FILLING or player_id not in self.yeses:
            return False
        waited = self.waiting_for_a_payment
        self._record_that(
            YesPaused(proposal_id=self.proposal_id, player_id=player_id, occurred_at=at)
        )
        self._fell_back_if(waited, player_id, left=False, at=at)
        return True

    def resume_yes(self, player_id: UUID, *, at: Instant) -> bool:
        """This player's week has room again: their paused yes counts once more
        (#544). Answers whether anything was recorded — nothing for a player
        whose yes is not paused, a game no longer filling, or one with no seat
        left for it: somebody took it while the yes was paused. Whether their
        week has room, and whether they may still be In, is the caller's."""

        if (
            player_id not in self.paused
            or self.standing_at(at) is not Standing.FILLING
            or self.open_seats == 0
        ):
            return False
        self._record_that(
            YesResumed(
                proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
            )
        )
        return True

    def expire(self, *, now: Instant) -> bool:
        """Record that the book-by passed with the game unfilled. Answers
        whether anything was recorded: nothing before the book-by, and nothing
        on a proposal that already ended."""

        if self.standing_at(now) is not Standing.EXPIRED or self.ending is not None:
            return False
        self._record_that(
            ProposalExpired(proposal_id=self.proposal_id, occurred_at=now)
        )
        return True

    def club_cancelled(self, player_ids: tuple[UUID, ...], *, at: Instant) -> None:
        """The club cancelled the booked game this proposal filled, with these
        players still in: they are owed a new card first (#547)."""

        invariant(
            self.ending is Ending.FILLED and self.cancelled_for is None,
            f"{self.proposal_id} is cancelled by its club from {self.ending}, "
            f"cancelled before for {self.cancelled_for}",
        )
        self._record_that(
            ClubCancelled(
                proposal_id=self.proposal_id, player_ids=player_ids, occurred_at=at
            )
        )

    def redeal(self, *, card_id: UUID, named: Collection[UUID], at: Instant) -> bool:
        """Record that the people In were dealt a new card first: ``card_id``,
        naming ``named`` — those of them it names, and maybe best fits beside
        them. Answers whether anything was recorded: nothing on a game that
        owes nothing."""

        if not self.owes_a_new_card:
            return False
        self._record_that(
            Redealt(
                proposal_id=self.proposal_id,
                occurred_at=at,
                card_id=card_id,
                player_ids=tuple(p for p in self.owed_to if p in named),
            )
        )
        return True

    def lose_court_hour(self, *, at: Instant) -> bool:
        """Record that the last court at the card's club and hour went. Answers
        whether anything was recorded: nothing on a proposal no longer filling
        at ``at`` — one past its book-by has expired, whether or not the sweep
        noticed. **The people In stay on the record**: they are who the
        proposer deals a new card first (the mechanics §5.2)."""

        if self.standing_at(at) is not Standing.FILLING:
            return False
        self._record_that(
            CourtHourLost(proposal_id=self.proposal_id, occurred_at=at)
        )
        return True

    # ------------------------------------------------------------------- fold

    def _fell_back_if(
        self, waited: bool, player_id: UUID, *, left: bool, at: Instant
    ) -> None:
        """A seat opened on a full game that waited for a payment: it is
        filling again (Q104, Q106)."""

        if waited and not self.waiting_for_a_payment:
            self._record_that(
                FellBackToFilling(
                    proposal_id=self.proposal_id,
                    player_ids=(player_id,),
                    occurred_at=at,
                    left=(player_id,) if left else (),
                )
            )

    def _a_seat_opened(self, player_id: UUID) -> None:
        """Somebody In is In no longer: their own time to pay — or the payment
        they made in it — goes with them."""

        self.paying.pop(player_id, None)
        self.paid_in_time.pop(player_id, None)

    def _may_take_a_seat(self, player_id: UUID, *, at: Instant) -> bool:
        """What this game refuses of any yes: it is over, the player said no,
        or every seat is In. ``False`` for somebody already In."""

        self._refuse_unless_filling(at)
        if player_id in self.yeses:
            return False
        if player_id in self.declined:
            raise ProposalAlreadyAnswered()
        if self.open_seats == 0:
            raise ProposalIsFull()
        return True

    def _record_a_yes(self, player_id: UUID, *, at: Instant) -> None:
        self._record_that(
            YesSaid(proposal_id=self.proposal_id, player_id=player_id, occurred_at=at)
        )

    def _refuse_a_stranger(self, player_id: UUID) -> None:
        if not self.is_on_it(player_id):
            raise ProposalNotFound()

    def _refuse_unless_filling(self, at: Instant) -> None:
        standing = self.standing_at(at)
        if standing is not Standing.FILLING:
            raise ProposalIsOver(standing=standing.value)

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, VersionDealt):
            if event.number <= len(self.versions):
                dealt_into = self.versions[event.number - 1]
                self.versions = tuple(
                    DealtVersion(
                        number=version.number,
                        players=(*version.players, *event.player_ids),
                        first_named=version.first_named,
                    )
                    if version is dealt_into
                    else version
                    for version in self.versions
                )
            else:
                self.versions = (
                    *self.versions,
                    DealtVersion(
                        number=event.number,
                        players=tuple(event.player_ids),
                        first_named=len(event.player_ids),
                    ),
                )
        elif isinstance(event, YesSaid):
            self.yeses = (*self.yeses, event.player_id)
            self.withdrawn = tuple(
                player for player in self.withdrawn if player != event.player_id
            )
            self.reopened.pop(event.player_id, None)
            self.paused = tuple(
                player for player in self.paused if player != event.player_id
            )
        elif isinstance(event, NoSaid):
            self.declined = (*self.declined, event.player_id)
            self.withdrawn = tuple(
                player for player in self.withdrawn if player != event.player_id
            )
        elif isinstance(event, YesWithdrawn):
            # A paused yes is withdrawn only by a block (`withdraw_paused_yes`).
            if event.player_id in self.yeses:
                self._a_seat_opened(event.player_id)
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.paused = tuple(
                player for player in self.paused if player != event.player_id
            )
            self.withdrawn = (*self.withdrawn, event.player_id)
        elif isinstance(event, SeatReopened):
            self._a_seat_opened(event.player_id)
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.reopened[event.player_id] = Reopened(
                reason=ReopenReason(event.reason),
                seat_charge_id=event.seat_charge_id,
            )
        elif isinstance(event, YesPaused):
            self._a_seat_opened(event.player_id)
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.paused = (*self.paused, event.player_id)
        elif isinstance(event, TimeToPayGiven):
            self.paying[event.player_id] = Paying(
                reason=ReopenReason(event.reason),
                seat_charge_id=event.seat_charge_id,
                until=instant(event.until),
                time_to=TimeTo(event.time_to),
            )
            if self.payment_awaited_at is None:
                self.payment_awaited_at = instant(event.occurred_at)
        elif isinstance(event, TimeToPayMet):
            met = self.paying.pop(event.player_id, None)
            if met is not None:
                self.paid_in_time[event.player_id] = met.seat_charge_id
        elif isinstance(event, TimeToPayRanOut):
            for player in event.player_ids:
                paying = self.paying.pop(player)
                self.yeses = tuple(p for p in self.yeses if p != player)
                self.reopened[player] = Reopened(
                    reason=paying.reason, seat_charge_id=paying.seat_charge_id
                )
            at = instant(event.occurred_at)
            self.fell_back_at = at
            self.ran_out_for_good = at >= self.book_by
        elif isinstance(event, FellBackToFilling):
            self.fell_back_at = instant(event.occurred_at)
        elif isinstance(event, YesResumed):
            self.yeses = (*self.yeses, event.player_id)
            self.paused = tuple(
                player for player in self.paused if player != event.player_id
            )
        elif isinstance(event, ProposalFilled):
            self.ending = Ending.FILLED
            self.filled_by = event.filled_by
            self.booked_on_a_payment = bool(self.paying)
            self.paying = {}
            self.paid_in_time = {}
        elif isinstance(event, ProposalWithdrawn):
            self.ending = Ending.WITHDRAWN
        elif isinstance(event, ProposalExpired):
            self.ending = Ending.EXPIRED
        elif isinstance(event, CourtHourLost):
            self.ending = Ending.COURT_HOUR_LOST
        elif isinstance(event, Redealt):
            self.redealt = True
        elif isinstance(event, ClubCancelled):
            self.cancelled_for = tuple(event.player_ids)
        else:
            raise TypeError(f"Unsupported proposal event {event!r}")
        self.version += 1


def _posted_for(made: ProposalMade) -> PostedFor | None:
    """Who a post is for, as its first event recorded it — ``None`` on a pick
    and on a post made before posts had a *Who*."""

    if made.who is None:
        return None
    invariant(
        made.level_low is not None and made.level_high is not None,
        f"a post for {made.who} with no level range: {made.proposal_id}",
    )
    assert made.level_low is not None and made.level_high is not None
    return PostedFor(
        who=Who(made.who),
        levels=LevelRange(low=made.level_low, high=made.level_high),
    )

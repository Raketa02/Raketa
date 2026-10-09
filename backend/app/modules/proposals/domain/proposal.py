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

**A full game still filling is waiting for its club** (#543): only an On request
club leaves one so, and while it waits **its book-by no longer reads** — the
game filled in time, and the club's time to confirm may run past the book-by,
never past the start. Its club's yes fills it; its no, or no answer, **turns it
down**: over, nobody paid, and the people In owed a new card first, until the
proposer deals it (``Redealt``). A seat opening while it waits — a yes taken
back, paused or reopened — leaves it filling again, the book-by reading again.

**A booked game its club cancels is owed a new card too** (#547): the
proposal still filled — the booking says it was cancelled, and why — but the
people still in when the club cancelled are dealt a new card first, as a
turned-down game's are, and never at that club and hour.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable, Sequence
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
    NoSaid,
    ProposalExpired,
    ProposalFilled,
    ProposalMade,
    ProposalWithdrawn,
    Redealt,
    SeatReopened,
    TurnedDown,
    VersionDealt,
    YesPaused,
    YesResumed,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.limits import (
    NEXT_BEST_FITS_PER_SEAT,
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
    #: Its On request club refused it, or did not answer in time (#543).
    TURNED_DOWN = "TURNED_DOWN"


class ClubAnswer(StrEnum):
    """How an On request club turned a full game down (the mechanics §16.8)."""

    REFUSED = "REFUSED"
    NO_ANSWER = "NO_ANSWER"


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
    TURNED_DOWN = "TURNED_DOWN"


@dataclass(frozen=True, slots=True)
class Reopened:
    """Why the last yes reopened somebody's seat, and the refused payment they
    may confirm — ``None`` where nothing was asked of the provider."""

    reason: ReopenReason
    seat_charge_id: UUID | None

    @property
    def payment_to_confirm(self) -> UUID | None:
        """The payment confirming which is their yes again (§12.2)."""

        return (
            self.seat_charge_id
            if self.reason
            in (ReopenReason.AUTHENTICATION_REQUIRED, ReopenReason.DECLINED)
            else None
        )


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
    #: The people In on a game its club turned down have been dealt a new card
    #: first.
    redealt: bool = False
    #: Everybody still in when the club cancelled the booked game (#547) —
    #: ``None`` on a game no club cancelled.
    cancelled_for: tuple[UUID, ...] | None = None
    #: The player whose own act filled the booked game (Q102) — ``None`` until
    #: it is booked, and when the club's yes or a paused yes coming back did.
    filled_by: UUID | None = None
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
    ) -> "Proposal":
        """A game proposed at a court hour. **A post is its poster's yes**, so
        it is born with them In."""

        invariant(
            (origin is Origin.POST) == (poster_id is not None),
            f"a {origin} names a poster exactly when it is a post: {poster_id}",
        )
        invariant(
            origin is Origin.POST or posted_for is None,
            f"a pick is for nobody in particular: {posted_for}",
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
    def waiting_for_the_club(self) -> bool:
        """Every seat is In and the game has not ended: its On request club has
        it, and has not answered (#543). Only such a club leaves a full game
        filling — any other books it, or reopens a seat, in the same act."""

        return self.ending is None and self.open_seats == 0

    @property
    def owes_a_new_card(self) -> bool:
        """Its club turned it down — or cancelled it once booked (#547) — and
        the people it owes have not been dealt a new card first yet."""

        owed = self.ending is Ending.TURNED_DOWN or self.cancelled_for is not None
        return owed and not self.redealt

    @property
    def owed_to(self) -> tuple[UUID, ...]:
        """Who a new card is dealt to first: everybody still in when the club
        cancelled the booked game — a leaver is not — and otherwise the people
        In, as a turned-down game and one that lost its court hour have them."""

        return self.yeses if self.cancelled_for is None else self.cancelled_for

    def standing_at(self, now: Instant) -> Standing:
        if self.ending is not None:
            return Standing(self.ending.value)
        # A full game filled in time: its club's answer is its deadline now.
        if now >= self.book_by and not self.waiting_for_the_club:
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

    def withdraw_yes(self, player_id: UUID, *, at: Instant) -> None:
        """The player takes their yes back. Withdrawing a yes they never said,
        or already took back, records nothing. **A poster withdrawing with
        nobody else In ends the post**; with others In the game carries on
        without them (the mechanics §9.3)."""

        self._refuse_a_stranger(player_id)
        self._refuse_unless_filling(at)
        if player_id not in self.yeses:
            return
        self._record_that(
            YesWithdrawn(
                proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
            )
        )
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
        or ``None`` when no player's did (the club's yes, a resumed yes)."""

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
        self._record_that(
            SeatReopened(
                proposal_id=self.proposal_id,
                player_id=player_id,
                seat_charge_id=seat_charge_id,
                reason=reason.value,
                occurred_at=at,
            )
        )

    def pause_yes(self, player_id: UUID, *, at: Instant) -> bool:
        """This player's games per week are booked for this game's week: their
        yes stops counting. Answers whether anything was recorded — nothing for
        a player not In, or a game no longer filling."""

        if self.standing_at(at) is not Standing.FILLING or player_id not in self.yeses:
            return False
        self._record_that(
            YesPaused(proposal_id=self.proposal_id, player_id=player_id, occurred_at=at)
        )
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

    def turn_down(self, answer: ClubAnswer, *, at: Instant) -> None:
        """Its On request club refused it, or did not answer in time. **The
        people In stay on the record**: they are who the proposer deals a new
        card first."""

        invariant(
            self.waiting_for_the_club,
            f"{self.proposal_id} is turned down while not waiting for its club",
        )
        self._record_that(
            TurnedDown(
                proposal_id=self.proposal_id, answer=answer.value, occurred_at=at
            )
        )

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

    def redeal(self, *, at: Instant) -> bool:
        """Record that the people In were dealt a new card first. Answers whether
        anything was recorded: nothing on a game that owes nothing."""

        if not self.owes_a_new_card:
            return False
        self._record_that(Redealt(proposal_id=self.proposal_id, occurred_at=at))
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
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.paused = tuple(
                player for player in self.paused if player != event.player_id
            )
            self.withdrawn = (*self.withdrawn, event.player_id)
        elif isinstance(event, SeatReopened):
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.reopened[event.player_id] = Reopened(
                reason=ReopenReason(event.reason),
                seat_charge_id=event.seat_charge_id,
            )
        elif isinstance(event, YesPaused):
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.paused = (*self.paused, event.player_id)
        elif isinstance(event, YesResumed):
            self.yeses = (*self.yeses, event.player_id)
            self.paused = tuple(
                player for player in self.paused if player != event.player_id
            )
        elif isinstance(event, ProposalFilled):
            self.ending = Ending.FILLED
            self.filled_by = event.filled_by
        elif isinstance(event, ProposalWithdrawn):
            self.ending = Ending.WITHDRAWN
        elif isinstance(event, ProposalExpired):
            self.ending = Ending.EXPIRED
        elif isinstance(event, CourtHourLost):
            self.ending = Ending.COURT_HOUR_LOST
        elif isinstance(event, TurnedDown):
            self.ending = Ending.TURNED_DOWN
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

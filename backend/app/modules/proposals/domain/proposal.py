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
proposer that reads the club (#540). *Filled* arrives with the fill (#541).
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
    CourtHourLost,
    NoSaid,
    ProposalExpired,
    ProposalMade,
    ProposalWithdrawn,
    VersionDealt,
    YesSaid,
    YesWithdrawn,
)
from app.modules.proposals.domain.limits import (
    NEXT_BEST_FITS_PER_SEAT,
    VERSIONS_PER_PROPOSAL,
)
from app.modules.proposals.domain.pool import Pool, PoolKind
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

    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"
    COURT_HOUR_LOST = "COURT_HOUR_LOST"


class Standing(StrEnum):
    """Where a proposal stands at an instant — derived, never stored."""

    FILLING = "FILLING"
    EXPIRED = "EXPIRED"
    WITHDRAWN = "WITHDRAWN"
    COURT_HOUR_LOST = "COURT_HOUR_LOST"


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
    versions: tuple[DealtVersion, ...] = ()
    #: Everybody In, in the order they said yes.
    yeses: tuple[UUID, ...] = ()
    #: Everybody who said no, in the order they did — for good.
    declined: tuple[UUID, ...] = ()
    #: Everybody who took their yes back and has not said it again.
    withdrawn: tuple[UUID, ...] = ()
    ending: Ending | None = None
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
    ) -> "Proposal":
        """A game proposed at a court hour. **A post is its poster's yes**, so
        it is born with them In."""

        invariant(
            (origin is Origin.POST) == (poster_id is not None),
            f"a {origin} names a poster exactly when it is a post: {poster_id}",
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
    def poster_withdrew(self) -> bool:
        """A post whose poster is no longer In — *the group challenged you*
        (the mechanics §8.1)."""

        return self.poster_id is not None and self.poster_id not in self.yeses

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
        self._refuse_unless_filling(at)
        if player_id in self.yeses:
            return False
        if player_id in self.declined:
            raise ProposalAlreadyAnswered()
        if self.open_seats == 0:
            raise ProposalIsFull()
        return True

    def say_yes(self, player_id: UUID, *, at: Instant) -> None:
        if self.may_say_yes(player_id, at=at):
            self._record_that(
                YesSaid(
                    proposal_id=self.proposal_id, player_id=player_id, occurred_at=at
                )
            )

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

    def expire(self, *, now: Instant) -> bool:
        """Record that the book-by passed with the game unfilled. Answers
        whether anything was recorded: nothing before the book-by, and nothing
        on a proposal that already ended."""

        if self.ending is not None or now < self.book_by:
            return False
        self._record_that(
            ProposalExpired(proposal_id=self.proposal_id, occurred_at=now)
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
        elif isinstance(event, NoSaid):
            self.declined = (*self.declined, event.player_id)
            self.withdrawn = tuple(
                player for player in self.withdrawn if player != event.player_id
            )
        elif isinstance(event, YesWithdrawn):
            self.yeses = tuple(
                player for player in self.yeses if player != event.player_id
            )
            self.withdrawn = (*self.withdrawn, event.player_id)
        elif isinstance(event, ProposalWithdrawn):
            self.ending = Ending.WITHDRAWN
        elif isinstance(event, ProposalExpired):
            self.ending = Ending.EXPIRED
        elif isinstance(event, CourtHourLost):
            self.ending = Ending.COURT_HOUR_LOST
        else:
            raise TypeError(f"Unsupported proposal event {event!r}")
        self.version += 1

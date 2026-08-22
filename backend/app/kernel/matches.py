"""The facts the resolution ladder reads, and the five deadlines it reads them against.

This is **not the Matches aggregate** and must not become one. It is the closed
set of facts one pure function needs in order to say what a match is doing —
the same relationship ``MatchSnapshot`` has to a match in
``app/engines/matchmaking.py``, and the narrow input contract
``docs/adr/0022-kernel-negative-space-and-constant-homes.md`` asks for in place
of an aggregate shape. Matches (``Raketa02/Raketa#66``) owns the record, its
version, its outbox and its events; it publishes *this* to be resolved.

**No player identity crosses.** A seat says whether it is taken and whether it is
paid, and the viewer says whether the seat is hers. Nothing in the ladder needs
to know *who*, so nothing here holds an id — which is also why the kernel does
not mint a second spelling of the engines' ``PlayerRef``.

**Every threshold is an instant, and every comparison is against an instant.**
The source specification computes a fractional ``left = (start - now) / HOUR``
and warns twice not to round it; comparing instants removes the question. It
also removes the sub-minute hole a whole-minute subtraction would open: at
``start - 12h - 30s`` a floored minute count reads 719 and lapses a hold that
has not lapsed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import final

from app.kernel.invariants import invariant
from app.kernel.money import SOLD_FORMATS
from app.kernel.sports import SPORT_SPECS, Sport
from app.kernel.time import Instant, Minutes, hours, minutes, shifted

#: The commitment floor: whatever a club's own cancellation window says, a match
#: commits no later than twelve hours before it is played. `commit` is the
#: **earlier** of the two, so the club's window can only ever move it forwards.
_COMMITMENT_BACKSTOP = hours(12)

#: The rescue window opens here — six hours out for a two-player sport, four for
#: a four-player one. A singles court that loses its opponent loses the whole
#: game, so it starts looking sooner.
_RESCUE_SINGLES = hours(6)
_RESCUE_DOUBLES = hours(4)

#: The checkpoint: two hours out, the last moment anything about the roster can
#: change. It cannot be switched off by a club.
_CHECKPOINT = hours(2)

#: A full match becomes *ready to play* — and the door code is worth showing —
#: fifteen minutes before the start.
_DOOR_CODE_LEAD = minutes(15)

#: How long after the last point a score may still be entered. Twenty-four hours,
#: not the prototype's thirty minutes: ADR-0048 permits entry *"for 24 hours after
#: the match ends"* and ADR-0049 says outright *"with the deadline now 24 hours"*.
#: The thirty minutes survive as the moment the card **asks** — a nudge while both
#: sides are still at the club — and never as a bar (``Raketa02/Raketa#79``).
_RESULT_WINDOW = hours(24)

#: How long a hole left by a departure keeps the match in the recovery group
#: before the card goes back to describing an ordinary forming match.
_VACANCY_DECAY = hours(24)

#: The tolerance that separates *committed at the deadline* from *committed on
#: the spot*: a match whose last seat was paid after the deadline had already
#: passed commits the moment it fills, and says so.
_LATE_FILL_TOLERANCE = minutes(1)

# Every one of these is private, and each has a function below that answers the
# question it exists for. A constant re-exported is an invitation to compute
# `start - 15min` somewhere else, and two computations of one threshold is the
# failure this layer exists to make unreachable — the same argument
# `docs/adr/0022-kernel-negative-space-and-constant-homes.md` makes about second
# implementations. The hold ladder's own two tiers live with the hold ladder,
# for the same reason.


class MatchKind(str, Enum):
    """Whether the court was bought by the marketplace or by one player."""

    OPEN = "open"
    PRIVATE = "private"


class PayModel(str, Enum):
    """How a private court is paid for.

    ``SOLO`` is an ordinary court booking: the owner pays the whole thing and
    whoever turns up owes nothing. ``SPLIT`` divides it among the seats, and the
    owner carries every share nobody has paid yet
    (``docs/adr/0045-the-owners-guarantee-is-the-whole-court-and-never-shrinks.md``).
    An open match has no pay model of its own — every seat is sold — so the
    field is read only under ``MatchKind.PRIVATE``.
    """

    SOLO = "solo"
    SPLIT = "split"


class OfferKind(str, Enum):
    """How a seat reached this viewer, when one has.

    Two wordings, because they are two different claims
    (``docs/adr/0072-two-sentences-are-two-situations-and-a-leaver-is-a-third-audience.md``):
    ``EXCLUSIVE`` genuinely holds the seat for one person, and ``OPEN`` is a
    race nobody has won yet. Only one of them ships in v1 — the invitation
    ladder is one open call at every distance
    (``docs/adr/0061-the-invitation-ladder-is-an-order-and-one-open-call.md``) —
    and the other is here because the ladder must be able to say the sentence
    the moment an exclusive offer exists, not a release later.
    """

    EXCLUSIVE = "exclusive"
    OPEN = "open"


@final
@dataclass(frozen=True)
class Seat:
    """One seat: whether somebody holds it, and whether they have paid for it.

    The two are not one fact. A seat held under an invitation and not yet paid
    is the whole of ``formingHeld``, and counting it as filled would tell four
    people a match is complete when a seat may still lapse
    (``Raketa02/Raketa#74``).

    A paid seat with nobody on it is a caller's bug rather than a state, and it
    is refused here so that the count downstream cannot be quietly wrong.
    """

    taken: bool = False
    paid: bool = False

    def __post_init__(self) -> None:
        invariant(
            self.taken or not self.paid,
            "a paid seat with nobody on it",
        )


@final
@dataclass(frozen=True)
class Vacancy:
    """A hole a departure left, for as long as it is unfilled.

    A vacancy and the departure that caused it are independent facts
    (``docs/adr/0033-settlement-and-occupancy-are-independent.md``): the ladder
    reads *is there a hole in this match*, and the leaver's card reads what her
    own departure settled at. Only open vacancies reach the ladder — one that
    has been refilled is not a hole — which is what stops a refilled match being
    pinned in a recovery state for ever, the defect the prototype shipped.

    ``vacated_at`` is the only field the ladder reads. The seat, the player, the
    amount and the outcome belong to the departure record (``Raketa02/Raketa#67``).
    """

    vacated_at: Instant


@final
@dataclass(frozen=True)
class Viewer:
    """One player's relationship to one match — the whole of what a rung may read.

    Three rungs of seventeen read this, and every other audience difference is
    rendering downstream of the resolver
    (``docs/adr/0040-one-ladder-resolves-a-situation.md``,
    ``docs/adr/0072-...``). In particular a **leaver is not here**: her card is
    the match's card rendered for somebody who used to hold a seat, and the
    situation it renders is the match's own.

    Resolving with no viewer at all is the same function with the parameter
    absent, never a second derivation — so there is nothing for a consistency
    suite to catch between the absolute answer and the viewer's.
    """

    holds_seat: bool = False
    on_standby: bool = False
    offer: OfferKind | None = None


@final
@dataclass(frozen=True)
class HoldPolicy:
    """The four fields of a club's policy that the hold ladder actually reads.

    ``ClubPolicy`` is eight fields versioned as one row
    (``docs/adr/0078-club-policy-is-eight-fields-and-two-of-them-ship-dark.md``);
    the other four — ``rebookingCredit``, ``freeCancelHours``, ``turnaroundMin``
    and ``countsCash`` — are read by money, by reservations and by nobody, and
    naming them here would be the aggregate shape this module refuses to be.

    ``max_hold_age`` is ``None`` when the club caps nothing, and **zero means
    the club does not hold speculatively at all** — not *everything is instantly
    stale*, which is the same behaviour told as a lie. There is no platform
    floor under it.
    """

    #: The club's cancellation window. `commit` is the earlier of `start - this`
    #: and the twelve-hour backstop.
    window: Minutes = hours(24)

    #: How long before the start a match stops accepting anybody.
    join_cut: Minutes = minutes(30)

    #: How long a speculative hold may sit before the club takes the court back.
    #: Measured from `held_since`, never from the match's creation
    #: (``docs/adr/0031-hold-ladder-is-a-floor-at-a-level-of-certainty.md``).
    max_hold_age: Minutes | None = None

    #: Whether the club publishes a demand model, which is what lets it extend a
    #: hold the ladder has already lapsed.
    prob_hold: bool = False

    def __post_init__(self) -> None:
        invariant(self.window > 0, f"club cancellation window: {self.window}")
        invariant(self.join_cut >= 0, f"club join cutoff: {self.join_cut}")
        invariant(
            self.max_hold_age is None or self.max_hold_age >= 0,
            f"club maximum hold age: {self.max_hold_age}",
        )


@final
@dataclass(frozen=True)
class MatchRecord:
    """Every stored fact the ladder and the wake function read, and no other.

    Grouped the way ``docs/adr/0034-matches-is-a-record-and-keeps-no-history.md``
    groups them, by the question *may a reader derive this*. Nothing derived is
    stored: ``filled``, ``is_full``, whether a court is held and the situation
    itself are all computed here, every time, from these facts and the clock.
    """

    sport: Sport
    """Which sport, and therefore how many players the court is sold for."""

    start: Instant
    """When the match is played. **Mutable** — a consented shift moves it, and
    every deadline moves with it, because all five are relative to this."""

    duration: Minutes
    """How long the court is booked for; `match_end` is `start + duration`."""

    created: Instant
    """When the match was posted. Read for one thing only: whether it was born
    after its own commitment deadline, which is a different sentence from a
    deadline that has since passed."""

    seats: tuple[Seat, ...]
    """Exactly as many seats as the sport is sold for, in a fixed order."""

    policy: HoldPolicy = field(default_factory=HoldPolicy)
    """The club's policy **as it stood when this record was assembled**. Policy
    is versioned whole (ADR-0078), so resolving which row applies happens once,
    outside, and the answer travels with the record."""

    kind: MatchKind = MatchKind.OPEN
    pay_model: PayModel = PayModel.SPLIT
    """How a private court is paid for. Not read unless `kind` is `PRIVATE`."""

    open_seats: int = 0
    """How many of a private court's seats have been opened to the marketplace.
    Opening one takes unanimous consent from everybody already paid (ADR-0030);
    inviting a named person takes none and opens nothing."""

    held_since: Instant | None = None
    """When the hold being aged was granted, or `None` if none ever was.

    A new stored fact, and it cannot be reconstructed: nothing in the history
    distinguishes *the hold was granted at T* from *the second seat was paid at
    T* once a seat has been vacated and refilled (ADR-0031).

    **It outlives the reclaim that ends it**, so it is not on its own the answer
    to *is a court being kept aside* — `keeping_a_court` reads it with
    `released_at` beside it. The club's cap is measured from this instant, and a
    reclaim that cleared it would reset the clock that had just fired."""

    released_at: Instant | None = None
    """When the court went back on sale, and therefore that it has. A receipt —
    the notification was sent — and never the answer to *should a court be held*,
    which is the ladder's."""

    committed_at: Instant | None = None
    """When the match bound everybody to it. Irreversible, and **not derivable**:
    commitment needs the deadline passed *and* the match full, so a re-derivation
    would release three people the moment a fourth left."""

    open_vacancies: tuple[Vacancy, ...] = ()
    """Holes left by departures, while they are still holes."""

    transferring: bool = False
    """A leaver has named somebody to take the seat and the handover is running."""

    court_locked: bool = False
    """The club has committed a court by hand, outside the ladder."""

    club_extended: bool = False
    """The club has published an extension of a hold the ladder has lapsed."""

    inventory_lost: bool = False
    """The last court in the category was sold to somebody else."""

    club_cancelled: bool = False
    weather: bool = False
    form_cancelled: bool = False
    checkpoint_cancelled: bool = False

    no_show: bool = False
    """Somebody who paid did not turn up."""

    score_proposed: bool = False
    """A score is on the table awaiting an answer."""

    result_agreed: bool = False
    """A score has settled, by agreement or by silence."""

    def __post_init__(self) -> None:
        players = SPORT_SPECS[self.sport].players
        invariant(
            len(self.seats) == players,
            f"{self.sport.value} sold in {len(self.seats)} seats, not {players}",
        )
        invariant(
            players in SOLD_FORMATS,
            f"a sport sold in {players} seats",
        )
        invariant(self.duration > 0, f"match duration: {self.duration}")
        invariant(
            0 <= self.open_seats <= players,
            f"{self.open_seats} seats opened of {players}",
        )
        # A hole is a seat nobody is on. More vacancies than empty seats is the
        # degenerate input the prototype produced by never clearing `vacated` —
        # a card reading "3 of 4 · the seat stays funded" over a complete four —
        # and it is refused at the door rather than resolved into a lying card.
        invariant(
            len(self.open_vacancies) <= players - sum(1 for s in self.seats if s.taken),
            f"{len(self.open_vacancies)} open vacancies with "
            f"{sum(1 for s in self.seats if s.taken)} of {players} seats taken",
        )


@final
@dataclass(frozen=True)
class Deadlines:
    """The five instants every downstream rule compares the clock against.

    Pure in the record and free of the clock: a deadline is a property of the
    match, and the question *has it passed* belongs to whoever holds a now.
    """

    commit: Instant
    rescue: Instant
    check: Instant
    join_cut: Instant
    play: Instant
    singles: bool


def seat_count(record: MatchRecord) -> int:
    """How many players the court is sold for."""

    return len(record.seats)


def filled(record: MatchRecord) -> int:
    """Seats **paid for**, which is the only count that means anything.

    Counting people who said yes rather than people who paid is how a match
    reads full while a seat may still lapse (``Raketa02/Raketa#74``).
    """

    return sum(1 for seat in record.seats if seat.taken and seat.paid)


def held_unpaid(record: MatchRecord) -> int:
    """Seats somebody holds and nobody has paid for — its own number, always."""

    return sum(1 for seat in record.seats if seat.taken and not seat.paid)


def is_full(record: MatchRecord) -> bool:
    """Every seat taken and paid."""

    return all(seat.taken and seat.paid for seat in record.seats)


def _is_singles(record: MatchRecord) -> bool:
    """Whether the sport is played by two, which is a fact about the sport.

    Read off the registry rather than off the seat count so that a record whose
    seats disagree with its sport is caught by the record's own invariant rather
    than silently changing the rescue window.
    """

    return SPORT_SPECS[record.sport].players == 2


def match_end(record: MatchRecord) -> Instant:
    """When the court booking ends — the moment a result becomes askable."""

    return shifted(record.start, record.duration)


def result_window(record: MatchRecord) -> Instant:
    """When a score can no longer be entered: past this, a match nobody agreed on
    is an evening rather than evidence (ADR-0048, ADR-0049).

    **How long a card is kept afterwards is not here.** A card lives twenty-four
    hours from the moment it *closed*, which is a fact about a settlement or a
    cancellation and not about when the match would have ended
    (``Raketa02/Raketa#74``) — so the record the ladder reads cannot say it, and
    the kernel does not pretend to. It is also not a boundary any rung reads.
    """

    return shifted(match_end(record), _RESULT_WINDOW)


def is_terminal(record: MatchRecord) -> bool:
    """Whether nothing further can happen to this match.

    The four cancellations and nothing else. A played match is **not** terminal:
    `needsResult → confirmResult → completed` still moves, and the card still
    leaves Now on its own clock.
    """

    return (
        record.inventory_lost
        or record.club_cancelled
        or record.weather
        or record.form_cancelled
        or record.checkpoint_cancelled
    )


def court_named_at(start: Instant) -> Instant:
    """When the specific court stops being ours and becomes the player's to know.

    The same fifteen minutes as the door code, from the same constant and
    computed once, because they are one moment seen from two contexts: a match
    becomes *ready to play* and a reservation names its court. ADR-0035 fixes
    the second — *"`courtAssigned`, fifteen minutes before play, is the only
    state that names a specific court"* — and everywhere earlier the card says
    the **category**, because the court is assigned and may be reassigned.

    Takes a start rather than a record, because Courts has no ``MatchRecord`` to
    hand: a club's own block on a Tuesday morning is a reservation with a start
    and no match behind it at all. That is also why this is the function and
    ``door_code_at`` is the wrapper, rather than the other way round.
    """

    return shifted(start, _before(_DOOR_CODE_LEAD))


def door_code_at(record: MatchRecord) -> Instant:
    """When a full match becomes *ready to play*, fifteen minutes before it."""

    return court_named_at(record.start)


def vacancy_expires_at(record: MatchRecord) -> Instant | None:
    """When the newest open hole stops describing the match, if there is one.

    The **most recent** vacancy rather than the oldest, and the difference is
    the whole reason the twenty-four hours exist: two departures, one thirty
    hours ago and one an hour ago, is a match that lost a player an hour ago.

    This is the mechanism the documents promised and never had. Without it a
    flag set on a departure and never cleared pins a match in a recovery state
    for ever — including one that has since refilled.
    """

    if not record.open_vacancies:
        return None
    newest = max(vacancy.vacated_at for vacancy in record.open_vacancies)
    return shifted(newest, _VACANCY_DECAY)


def deadlines(record: MatchRecord) -> Deadlines:
    """The five deadlines, every one of them relative to `start`.

    `commit` is the **earlier** of the club's cancellation window and the
    platform's twelve-hour backstop, so a club may bring commitment forward and
    never push it back. At a twelve-hour club the two coincide exactly, and the
    commitment and the two-seat hold lapse fire in the same instant — a
    coincidence any suite exercising only a twenty-four-hour club never sees.
    """

    by_window = shifted(record.start, _before(record.policy.window))
    by_backstop = shifted(record.start, _before(_COMMITMENT_BACKSTOP))
    singles = _is_singles(record)
    return Deadlines(
        commit=min(by_window, by_backstop),
        rescue=shifted(
            record.start, _before(_RESCUE_SINGLES if singles else _RESCUE_DOUBLES)
        ),
        check=shifted(record.start, _before(_CHECKPOINT)),
        join_cut=shifted(record.start, _before(record.policy.join_cut)),
        play=record.start,
        singles=singles,
    )


def committed_on_fill(record: MatchRecord) -> bool:
    """Whether the match committed *because it filled*, past its own deadline.

    A minute of tolerance, so that a match which filled a moment before the
    deadline and committed a moment after it is not described as having raced.
    """

    if record.committed_at is None:
        return False
    return record.committed_at > shifted(deadlines(record).commit, _LATE_FILL_TOLERANCE)


def born_late(record: MatchRecord) -> bool:
    """Whether the match was posted after its own commitment deadline.

    Such a match never had a commitment window: it commits the moment it fills,
    and telling its creator *the deadline has passed* would read as a warning
    about something she did on purpose.
    """

    return record.created >= deadlines(record).commit


def _before(span: Minutes) -> Minutes:
    """`span` as an offset backwards, for `shifted`."""

    return minutes(-span)
